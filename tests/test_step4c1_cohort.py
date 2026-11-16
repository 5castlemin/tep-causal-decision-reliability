from __future__ import annotations

import multiprocessing
from pathlib import Path
import tempfile
import unittest

import numpy as np

from research.budget_aware_refinement.step4c1_cohort import (
    CohortRegistry, RegistryConflict, run_cohort, sha256,
)
from research.budget_aware_refinement.step4b4_mock_runner import _event, append_event, SimulatedProcessStop
from research.budget_aware_refinement.step4c1_pipeline import execution_binding, PIPELINE_STAGES


def _write_complete_fixture_ledger(proposal, ledger, delta, signature):
    _,cfg_sha,input_sha=execution_binding(proposal,delta)
    run_id=f"step4c1:{proposal['cohort']}:{proposal['proposal_id']}:attempt-{proposal['attempt']}"
    rng_key=f"{proposal['cohort']}:{proposal['master_seed']}:{proposal['proposal_id']}:{proposal['attempt']}"
    for stage in PIPELINE_STAGES:
        output={"equation_signature_sha256":signature} if stage == "scm" else {}
        if stage == "composite":
            output={"status":"OK","complete":True,"gt_evaluation_performed":True}
        append_event(ledger,_event(run_id,f"stage:{stage}",rng_key=rng_key,
            config_sha256=cfg_sha,input_sha256=input_sha,scm_id=proposal["scm_id"],
            cohort=proposal["cohort"],status="OK",elapsed_seconds=.01,output=output),max_bytes=100000)
    append_event(ledger,_event(run_id,"terminal",rng_key=rng_key,config_sha256=cfg_sha,
        input_sha256=input_sha,scm_id=proposal["scm_id"],cohort=proposal["cohort"],
        status="OK",completed_stages=list(PIPELINE_STAGES)),max_bytes=100000)


def _register_concurrently(args):
    db_path, proposal = args
    reg = CohortRegistry(Path(db_path))
    return reg.admit(proposal, "unbound", Path(db_path).with_suffix(".jsonl"))["scm_id"]


class Step4C1CohortTests(unittest.TestCase):
    def _proposal(self, pid, *, accepted=True, scm_id=None, equation=None, topology="same-topology"):
        return {"cohort": "development", "master_seed": 73, "proposal_id": pid,
                "attempt": 0, "accepted": accepted, "scm_id": scm_id if accepted else None,
                "topology_hash": topology, "template": "chain_mediation", "node_count": 6,
                "post_eligibility_rng_seeds": {"coefficient": int(pid.rsplit("-",1)[-1]) if pid[-1].isdigit() else 2},
                "equation_signature_sha256": equation,
                "reason": None if accepted else "fixed_fixture_ineligible"}

    def test_registry_idempotency_delta_balance_and_signature_duplicate(self):
        with tempfile.TemporaryDirectory() as td:
            registry = CohortRegistry(Path(td) / "admission.sqlite")
            rejected = self._proposal("development-proposal-0", accepted=False)
            registry.record_rejection(rejected, "cfg")
            p1 = self._proposal("development-proposal-1", scm_id="dev-scm-1")
            first = registry.admit(p1, "unbound", Path(td)/"1.jsonl")
            self.assertEqual(first["delta"], 1)
            replay = registry.admit(p1, "unbound", Path(td)/"1.jsonl")
            self.assertTrue(replay["replayed"])
            self.assertEqual(replay["delta"], 1)
            registry.bind_equation_signature("development", p1["proposal_id"], 0, "eq-one")
            p2 = self._proposal("development-proposal-2", scm_id="dev-scm-2", topology="same-topology")
            second = registry.admit(p2, "unbound", Path(td)/"2.jsonl")
            self.assertEqual(second["delta"], -1)
            registry.bind_equation_signature("development", p2["proposal_id"], 0, "eq-two")
            p3 = self._proposal("development-proposal-3", scm_id="dev-scm-3")
            registry.admit(p3, "unbound", Path(td)/"3.jsonl")
            with self.assertRaises(RegistryConflict):
                registry.bind_equation_signature("development", p3["proposal_id"], 0, "eq-one")
            changed = dict(p1, topology_hash="changed")
            with self.assertRaises(RegistryConflict):
                registry.admit(changed, "unbound", Path(td)/"1.jsonl")
            with self.assertRaises(RegistryConflict):
                registry.admit(p1, "different-config", Path(td)/"1.jsonl")
            counts = registry.counts("development")
            self.assertEqual(counts["topology_proposals"], 4)
            self.assertEqual(counts["q_common_structurally_eligible"], 3)
            self.assertEqual(counts["delta_counts"], {"-1": 1, "1": 2})
            confirmation=dict(p1,cohort="confirmation",proposal_id="confirmation-proposal-0",
                scm_id="rep-scm-0")
            confirm=registry.admit(confirmation,"unbound",Path(td)/"confirm.jsonl")
            self.assertEqual(confirm["delta"],1)

    def test_single_proposal_runner_requires_explicit_delta(self):
        from research.budget_aware_refinement.step4c1_pipeline import run_eligible_proposal
        from research.budget_aware_refinement.step4c1_proposal import build_structural_proposal
        with tempfile.TemporaryDirectory() as td:
            proposal=build_structural_proposal(cohort="development",master_seed=101,
                proposal_id="f5",attempt=0)
            self.assertTrue(proposal["accepted"])
            with self.assertRaises(ValueError):
                run_eligible_proposal(proposal,Path(td)/"ledger.jsonl")

    def test_same_topology_different_equations_are_allowed(self):
        with tempfile.TemporaryDirectory() as td:
            reg = CohortRegistry(Path(td)/"r.sqlite")
            for i in range(2):
                proposal = self._proposal(f"development-proposal-{i}", scm_id=f"dev-scm-{i}")
                reg.admit(proposal, "unbound", Path(td)/f"{i}.jsonl")
                reg.bind_equation_signature("development", proposal["proposal_id"], 0, f"eq-{i}")
            self.assertEqual(reg.counts("development")["scm_generation_success"], 2)

    def test_two_processes_cannot_double_admit_same_proposal(self):
        with tempfile.TemporaryDirectory() as td:
            db = str(Path(td)/"r.sqlite")
            proposal = self._proposal("development-proposal-5", scm_id="dev-scm-5")
            ctx = multiprocessing.get_context("spawn")
            with ctx.Pool(2) as pool:
                results = pool.map(_register_concurrently, [(db,proposal),(db,proposal)])
            self.assertEqual(results, ["dev-scm-5","dev-scm-5"])
            self.assertEqual(CohortRegistry(Path(db)).counts("development")["registry_accepted"], 1)

    def test_cohort_resumes_admission_and_does_not_replace_pipeline_failure(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            registry = CohortRegistry(root/"registry.sqlite")
            calls = {"runner": 0}
            def builder(*,cohort,master_seed,proposal_id,attempt):
                number = int(proposal_id.rsplit("-",1)[-1])
                accepted = number >= 2
                return {"cohort":cohort,"master_seed":master_seed,"proposal_id":proposal_id,
                        "attempt":attempt,"accepted":accepted,
                        "scm_id":f"dev-scm-{number}" if accepted else None,
                        "topology_hash":f"top-{number}","template":"chain_mediation","node_count":6,
                        "post_eligibility_rng_seeds":{"coefficient":number},
                        "reason":None if accepted else "fixture_structure_ineligible"}
            def runner(proposal, ledger, delta):
                calls["runner"] += 1
                if calls["runner"] == 1:
                    raise SimulatedProcessStop()
                _write_complete_fixture_ledger(proposal,ledger,delta,f"eq-{proposal['proposal_id']}")
                return {"status":"OK"}
            with self.assertRaises(SimulatedProcessStop):
                run_cohort(cohort="development",master_seed=9,registry=registry,
                    ledger_dir=root/"ledgers",proposal_builder=builder,proposal_runner=runner,
                    target_eligible=2,proposal_cap=5)
            self.assertEqual(registry.counts("development")["registry_accepted"],1)
            result = run_cohort(cohort="development",master_seed=9,registry=registry,
                ledger_dir=root/"ledgers",proposal_builder=builder,proposal_runner=runner,
                target_eligible=2,proposal_cap=5)
            self.assertEqual(result["counts"]["topology_proposals"],4)
            self.assertEqual(result["counts"]["registry_accepted"],2)
            self.assertEqual(result["counts"]["three_type_evaluation_complete"],2)
            self.assertEqual(result["counts"]["delta_counts"],{"-1":1,"1":1})
            self.assertEqual(result["shortfall_eligible"],0)
            with self.assertRaises(RegistryConflict):
                run_cohort(cohort="development",master_seed=10,registry=registry,
                    ledger_dir=root/"ledgers",proposal_builder=builder,proposal_runner=runner,
                    target_eligible=2,proposal_cap=5)

    def test_pipeline_failure_is_retained_and_does_not_trigger_replacement(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); registry=CohortRegistry(root/"r.sqlite")
            seen=[]
            def builder(*,cohort,master_seed,proposal_id,attempt):
                number=int(proposal_id.rsplit("-",1)[-1])
                accepted=number==0
                return {"cohort":cohort,"master_seed":master_seed,"proposal_id":proposal_id,
                    "attempt":attempt,"accepted":accepted,"scm_id":"dev-scm-0" if accepted else None,
                    "topology_hash":f"top-{number}","template":"chain_mediation","node_count":6,
                    "post_eligibility_rng_seeds":{"coefficient":number},
                    "reason":None if accepted else "fixture_structure_ineligible"}
            def runner(proposal,ledger,delta):
                seen.append(proposal["proposal_id"])
                return {"status":"GT_EVAL_FAIL"}
            result=run_cohort(cohort="development",master_seed=1,registry=registry,
                ledger_dir=root/"ledgers",proposal_builder=builder,proposal_runner=runner,
                target_eligible=1,proposal_cap=4)
            self.assertEqual(seen,["development-proposal-000000"])
            self.assertEqual(result["counts"]["registry_accepted"],1)
            self.assertEqual(result["counts"]["missing_or_failed"],1)
            self.assertEqual(result["counts"]["composite_available"],0)
            self.assertEqual(result["counts"]["topology_proposals"],1)

    def test_cap_shortfall_preserves_all_rejected_proposals(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); registry=CohortRegistry(root/"r.sqlite")
            def builder(*,cohort,master_seed,proposal_id,attempt):
                number=int(proposal_id.rsplit("-",1)[-1])
                return {"cohort":cohort,"master_seed":master_seed,"proposal_id":proposal_id,
                    "attempt":attempt,"accepted":False,"scm_id":None,
                    "topology_hash":f"top-{number}","reason":"fixed_ineligible"}
            result=run_cohort(cohort="development",master_seed=1,registry=registry,
                ledger_dir=root/"ledgers",proposal_builder=builder,
                target_eligible=1,proposal_cap=2)
            self.assertTrue(result["cap_reached"])
            self.assertEqual(result["shortfall_eligible"],1)
            self.assertEqual(result["counts"]["topology_proposals"],2)
            self.assertEqual(result["counts"]["q_common_structurally_eligible"],0)

    def test_terminal_ledger_before_registry_update_is_reconciled_without_rerun(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); registry=CohortRegistry(root/"r.sqlite"); attempts=[]
            def builder(*,cohort,master_seed,proposal_id,attempt):
                return {"cohort":cohort,"master_seed":master_seed,"proposal_id":proposal_id,
                    "attempt":attempt,"accepted":True,"scm_id":"dev-scm-0",
                    "topology_hash":"top-0","template":"chain_mediation","node_count":6,
                    "post_eligibility_rng_seeds":{"coefficient":0}}
            def runner(proposal,ledger,delta):
                attempts.append(proposal["proposal_id"])
                _write_complete_fixture_ledger(proposal,ledger,delta,"unique-eq")
                raise SimulatedProcessStop()
            with self.assertRaises(SimulatedProcessStop):
                run_cohort(cohort="development",master_seed=1,registry=registry,
                    ledger_dir=root/"ledgers",proposal_builder=builder,proposal_runner=runner,
                    target_eligible=1,proposal_cap=2)
            def must_not_rerun(*args):
                self.fail("terminal successful ledger must reconcile without re-execution")
            result=run_cohort(cohort="development",master_seed=1,registry=registry,
                ledger_dir=root/"ledgers",proposal_builder=builder,proposal_runner=must_not_rerun,
                target_eligible=1,proposal_cap=2)
            self.assertEqual(attempts,["development-proposal-000000"])
            self.assertEqual(result["counts"]["composite_available"],1)

    def test_real_pipeline_fixture_resumes_through_cohort_orchestrator(self):
        from research.budget_aware_refinement.step4c1_pipeline import run_eligible_proposal
        from research.budget_aware_refinement.step4c1_proposal import build_structural_proposal
        from research.budget_aware_refinement.step4c1_scm import _topological_order
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); registry=CohortRegistry(root/"r.sqlite"); stopped={"once":False}
            def builder(**kwargs):
                return build_structural_proposal(**kwargs)
            def fixture(proposal):
                nodes,edges=proposal["nodes"],proposal["topology_edges"]
                truth={"nodes":nodes,"topological_order":list(_topological_order(nodes,edges)),
                    "edges":edges,"coefficients":{f"{a}->{b}":.5 for a,b in edges},
                    "noise":{"family":"fixed-cohort-test-double",
                        "means":{node:0.0 for node in nodes},"sd":{node:1.0 for node in nodes}}}
                seed=int(proposal["post_eligibility_rng_seeds"]["observational_sample"])
                noise=np.random.default_rng(seed).normal(size=(512,len(nodes)))
                return {"truth_spec":truth,"exogenous_noise":noise}
            def binding(proposal,delta):
                from research.budget_aware_refinement.step4c1_pipeline import execution_binding
                return execution_binding(proposal,delta,fixture(proposal))
            def runner(proposal,ledger,delta):
                should_stop=not stopped["once"]
                def hook(stage):
                    if should_stop and stage=="scm":
                        stopped["once"]=True
                        raise SimulatedProcessStop()
                return run_eligible_proposal(proposal,ledger,delta=delta,
                    isolate_stages=False,max_rss_bytes=None,_fixture_payload=fixture(proposal),
                    checkpoint_hook=hook if should_stop else None)
            args=dict(cohort="development",master_seed=101,registry=registry,
                ledger_dir=root/"ledgers",proposal_builder=builder,proposal_runner=runner,
                execution_binding_fn=binding,target_eligible=1,proposal_cap=5)
            with self.assertRaises(SimulatedProcessStop):
                run_cohort(**args)
            self.assertEqual(registry.counts("development")["registry_accepted"],1)
            result=run_cohort(**args)
            self.assertEqual(result["counts"]["three_type_evaluation_complete"],1)
            self.assertEqual(result["counts"]["shared_observation_generation_success"],1)
            self.assertEqual(result["counts"]["composite_available"],1)


if __name__ == "__main__":
    unittest.main()

"""Single-proposal production pipeline for Step 4C-1.

The entry point processes one already-eligible proposal. It does not create a
development/replication cohort or batch, and must not be used for Step 5.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import sys
from typing import Mapping

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from .step3_adapter import K, prepare as step3_prepare
from .graph_adapter import run_graph_stage
from .step4b4_mock_runner import StageFailure, recover_jsonl, run_pipeline
from .step4c1_evaluation import evaluate_prepared_pair, aggregate_scm_type_results
from .step4c1_gt import analytic_response
from .step4c1_scm import (generate_observations, generate_scm_parameters,
                          scm_signature, simulate_from_exogenous_noise)
from .step4_rng import RNGKey, RNG_PROTOCOL_VERSION, derive_seed
from .step4b2_population import competition_recipes
from .step4b_task_budget import classify_task_pairs
from .step4_topology_generator import is_dag
from .step4b4_failure_rules import fallback_rule
from src.integrated_pilot import fit_model
from src.decision_mvp import static_mean_response

TYPES = ("FN", "FP", "REV")
PIPELINE_STAGES = ("proposal", "scm", "observations", "error_graphs",
                   "policy_graphs", "recommendations", "gt_evaluation", "composite")
ACTIVE_BUDGET = 1
ACTIVE_GAMMA = 1
ACTIVE_DELTA = 1


class _PolicyFailure(RuntimeError):
    def __init__(self, status: str, reason: str):
        self.status = status
        super().__init__(reason)


def _fallback_selection(request: Mapping[str, object], data: np.ndarray, delta: int) -> dict | None:
    """Create the shared-grid k=0 intention-to-handle fallback if inputs allow."""
    nodes = tuple(request["node_ids"])
    action_idx, target_idx = nodes.index(request["action"]), nodes.index(request["target"])
    mean, sd = data.mean(axis=0), data.std(axis=0, ddof=1)
    if not np.isfinite(data).all() or not np.isfinite(sd).all() or (sd <= 0).any():
        return None
    candidates = [{"k": float(k), "action": float(mean[action_idx] + k * sd[action_idx])}
                  for k in K]
    return {"action": request["action"], "target_node": request["target"],
            "target": float(mean[target_idx] + delta * sd[target_idx]),
            "sd_y": float(sd[target_idx]), "candidates": candidates, "selected_k": 0.0,
            "fallback": True, "fallback_k": 0.0}


def _run_recommendation(request: dict, policy_id: str, data: np.ndarray,
                        nodes: tuple[str, ...], delta: int, graph: dict) -> dict:
    full_request = {**request, "policy_id": policy_id}
    def guarded_fit(*args, **kwargs):
        try:
            return fit_model(*args, **kwargs)
        except Exception as exc:
            raise _PolicyFailure("RIDGE_FAIL", f"{type(exc).__name__}:{str(exc)[:200]}") from exc

    try:
        graph_again, selection = step3_prepare(full_request, data, list(nodes), list(nodes), delta,
                                               guarded_fit, static_mean_response,
                                               graph_result=graph)
        return {"status": "OK", "reason": None, "selection": selection,
                "final_graph": graph_again["final_graph"], "edit_sequence": graph_again["edit_sequence"],
                "fallback_used": False}
    except _PolicyFailure as exc:
        status, reason = exc.status, str(exc)
    except Exception as exc:
        status, reason = "RECOMMEND_FAIL", f"{type(exc).__name__}:{str(exc)[:200]}"
    fallback_decision = fallback_rule(status, training_valid=True, truth_valid=True,
                                      k0_in_common_action_grid=0.0 in K)
    fallback = _fallback_selection(request, data, delta) if fallback_decision["fallback"] else None
    if fallback is not None:
        return {"status": status, "reason": reason, "selection": fallback,
                "final_graph": graph["final_graph"], "edit_sequence": graph["edit_sequence"],
                "fallback_used": True, "original_failure_preserved": True}
    return {"status": status, "reason": reason, "selection": None,
            "final_graph": graph["final_graph"], "edit_sequence": graph["edit_sequence"],
            "fallback_used": False}


def _canonical_json(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False).encode("ascii")


def _eligible_proposal(*, cohort, master_seed, proposal_id, attempt, template=None, node_count=None):
    from .step4c1_proposal import build_structural_proposal
    return build_structural_proposal(cohort=cohort, master_seed=master_seed,
        proposal_id=proposal_id, attempt=attempt, template=template, node_count=node_count)


@dataclass(frozen=True)
class ProductionStage:
    name: str
    ledger: str
    run_id: str
    scm_id: str
    cohort: str
    config_sha256: str
    input_sha256: str
    proposal: dict
    delta: int = ACTIVE_DELTA
    fixture_payload: dict | None = None

    def _prior(self, name: str) -> dict:
        for row in recover_jsonl(Path(self.ledger)):
            if (row.get("run_id") == self.run_id and row.get("event") == f"stage:{name}"
                    and row.get("status") == "OK" and row.get("scm_id") == self.scm_id
                    and row.get("cohort") == self.cohort
                    and row.get("config_sha256") == self.config_sha256
                    and row.get("input_sha256") == self.input_sha256):
                return row["output"]
        raise StageFailure("CHECKPOINT_MISSING", f"missing bound prerequisite stage {name}")

    def __call__(self):
        if self.name == "proposal":
            return self.proposal
        proposal = self._prior("proposal")
        if not proposal.get("accepted") or proposal.get("scm_id") != self.scm_id:
            raise StageFailure("STRUCTURE_INELIGIBLE", "Q-common eligibility failed before SCM ID assignment")
        nodes = tuple(proposal["nodes"])
        truth_edges = tuple(tuple(edge) for edge in proposal["topology_edges"])
        if self.name == "scm":
            try:
                if self.fixture_payload is not None:
                    truth = self.fixture_payload["truth_spec"]
                    if (tuple(truth.get("nodes", ())) != nodes
                            or tuple(map(tuple, truth.get("edges", ()))) != truth_edges):
                        raise ValueError("fixed fixture truth does not match accepted topology")
                    generated = {"truth_spec": truth,
                            "equation_signature_sha256": scm_signature(truth),
                            "coefficient_stream": "fixed_explicit_test_fixture",
                            "noise_parameter_stream": "fixed_explicit_test_fixture",
                            "fixture_only": True, "outcome_selection": False}
                else:
                    generated = generate_scm_parameters(proposal)
                for row in recover_jsonl(Path(self.ledger)):
                    if (row.get("event") == "stage:scm" and row.get("status") == "OK"
                            and row.get("scm_id") != self.scm_id
                            and row.get("output", {}).get("equation_signature_sha256")
                            == generated["equation_signature_sha256"]):
                        raise StageFailure("DUPLICATE_SCM", "equation signature already belongs to another SCM ID")
                return generated
            except StageFailure:
                raise
            except Exception as exc:
                raise StageFailure("SCM_GEN_FAIL", f"{type(exc).__name__}:{str(exc)[:240]}") from exc
        if self.name == "observations":
            try:
                scm = self._prior("scm")
                if self.fixture_payload is not None:
                    return simulate_from_exogenous_noise(
                        scm["truth_spec"], self.fixture_payload["exogenous_noise"],
                        source="fixed_explicit_test_fixture")
                return generate_observations(proposal, scm)
            except FloatingPointError as exc:
                raise StageFailure("NONFINITE", str(exc)) from exc
            except Exception as exc:
                raise StageFailure("DATA_FAIL", f"{type(exc).__name__}:{str(exc)[:240]}") from exc
        observations = self._prior("observations")
        matrix = np.asarray(observations["rows"], dtype=np.float64)
        if self.name == "error_graphs":
            output = {}
            for kind in TYPES:
                recipe = proposal.get("error_recipes", {}).get(kind)
                if not recipe:
                    raise StageFailure("ERROR_INJECTION_FAIL", f"missing preselected {kind} recipe")
                initial = tuple(tuple(edge) for edge in recipe["initial_edges"])
                if not is_dag(nodes, initial):
                    raise StageFailure("ERROR_INJECTION_FAIL", f"initial {kind} graph is cyclic")
                classified = competition_recipes(nodes, truth_edges, proposal["action"], proposal["target"], kind)
                if not any(set(r["initial_edges"]) == set(initial) for r in classified):
                    raise StageFailure("ERROR_INJECTION_FAIL", f"{kind} recipe no longer matches Q-common contract")
                output[kind] = {"initial_edges": [list(e) for e in sorted(initial)],
                                "errors": recipe["errors"], "initial_dag_valid": True}
            return output
        errors = self._prior("error_graphs")
        if self.name == "policy_graphs":
            seed = derive_seed(RNGKey(RNG_PROTOCOL_VERSION, self.cohort, proposal["master_seed"],
                self.scm_id, proposal["template"], proposal["node_count"], proposal["attempt"],
                "policy_schedule"))
            all_results = {}
            for kind in TYPES:
                request = {"node_ids": list(nodes), "initial_edges": errors[kind]["initial_edges"],
                           "reference_edges": [list(e) for e in truth_edges],
                           "allowed_types": [kind], "budget": ACTIVE_BUDGET,
                           "gamma": ACTIVE_GAMMA, "action": proposal["action"],
                           "target": proposal["target"], "seed": seed,
                           "schedule_seed": seed, "graph_id": f"{self.scm_id}-{kind}"}
                try:
                    global_graph = run_graph_stage({**request, "policy_id": f"G-{kind}"})
                    focused_graph = run_graph_stage({**request, "policy_id": f"T-{kind}"})
                except Exception as exc:
                    raise StageFailure("POLICY_GRAPH_FAIL", f"{type(exc).__name__}:{str(exc)[:200]}") from exc
                all_results[kind] = {"request": request,
                    "global_graph": global_graph, "task_focused_graph": focused_graph,
                    "same_initial_graph": global_graph["initial_graph"] == focused_graph["initial_graph"],
                    "same_policy_schedule_seed": global_graph["schedule_seed"] == focused_graph["schedule_seed"]}
            return all_results
        policy_graphs = self._prior("policy_graphs")
        if self.name == "recommendations":
            all_results = {}
            for kind in TYPES:
                graph_pair = policy_graphs[kind]
                request = graph_pair["request"]
                g = _run_recommendation(request, f"G-{kind}", matrix, nodes, self.delta,
                                        graph_pair["global_graph"])
                t = _run_recommendation(request, f"T-{kind}", matrix, nodes, self.delta,
                                        graph_pair["task_focused_graph"])
                all_results[kind] = {"global_final_graph": g["final_graph"],
                    "task_focused_final_graph": t["final_graph"],
                    "global_selection": g["selection"], "task_focused_selection": t["selection"],
                    "global_status": g["status"], "task_focused_status": t["status"],
                    "global_failure_reason": g["reason"], "task_focused_failure_reason": t["reason"],
                    "global_fallback_used": g["fallback_used"], "task_focused_fallback_used": t["fallback_used"],
                    "global_edit_sequence": g.get("edit_sequence"),
                    "task_focused_edit_sequence": t.get("edit_sequence"),
                    "training_data_sha256": observations["data_sha256"],
                    "same_data_for_pair": True}
                if g["selection"] is None or t["selection"] is None:
                    failed = g if g["selection"] is None else t
                    raise StageFailure(failed["status"],
                        f"{kind} recommendation unavailable after fallback check: {failed['reason']}")
            return all_results
        recommendations = self._prior("recommendations")
        if self.name == "gt_evaluation":
            scm = self._prior("scm")
            truth = scm["truth_spec"]
            results = {}
            for kind in TYPES:
                prep = recommendations[kind]
                if prep["global_selection"] is None or prep["task_focused_selection"] is None:
                    results[kind] = {"paired_status": "INCOMPLETE", "difference": None,
                        "global_regret": None, "task_focused_regret": None,
                        "global_recommendation_status": prep["global_status"],
                        "task_recommendation_status": prep["task_focused_status"],
                        "global_fallback_used": prep["global_fallback_used"],
                        "task_fallback_used": prep["task_focused_fallback_used"],
                        "gt_evaluation_performed": False}
                    continue
                pair = evaluate_prepared_pair(prep, truth_spec=truth, analytic_response=analytic_response)
                if pair["paired_status"] != "OK":
                    statuses = (pair["global"].get("status"), pair["task_focused"].get("status"))
                    failure_status = "NUMERIC_UNSTABLE" if "NUMERIC_UNSTABLE" in statuses else "GT_EVAL_FAIL"
                    raise StageFailure(failure_status, f"{kind} paired GT evaluation incomplete: {statuses}")
                results[kind] = {"paired_status": pair["paired_status"],
                    "global_regret": pair["global"].get("regret"),
                    "task_focused_regret": pair["task_focused"].get("regret"),
                    "difference": pair["difference"], "global": pair["global"],
                    "task_focused": pair["task_focused"],
                    "global_recommendation_status": prep["global_status"],
                    "task_recommendation_status": prep["task_focused_status"],
                    "global_fallback_used": prep["global_fallback_used"],
                    "task_fallback_used": prep["task_focused_fallback_used"],
                    "gt_evaluation_performed": True}
            return results
        if self.name == "composite":
            scm = self._prior("scm")
            results = self._prior("gt_evaluation")
            composite = aggregate_scm_type_results(results)
            return {**composite, "scm_id": self.scm_id,
                    "equation_signature_sha256": scm["equation_signature_sha256"],
                    "observational_data_sha256": observations["data_sha256"],
                    "types_complete": set(results) == set(TYPES),
                    "gt_evaluation_performed": all(r["gt_evaluation_performed"] for r in results.values())}
        raise ValueError(f"unknown production stage {self.name}")


def prepare_single_candidate(*, cohort: str, master_seed: int, proposal_id: str,
                             attempt: int, template: str | None = None,
                             node_count: int | None = None) -> dict:
    """Create one outcome-blind proposal; assign an SCM ID only if eligible."""
    return _eligible_proposal(cohort=cohort, master_seed=master_seed, proposal_id=proposal_id,
                              attempt=attempt, template=template, node_count=node_count)


def run_eligible_proposal(proposal: Mapping[str, object], ledger: Path, *, delta: int = ACTIVE_DELTA,
                          isolate_stages: bool = True, max_wall_seconds: float = 1800,
                          max_unit_seconds: float = 2, max_rss_bytes: int | None = 512 * 1024 * 1024,
                          max_ledger_bytes: int = 100 * 1024 * 1024,
                          checkpoint_hook=None, _fixture_payload: dict | None = None) -> dict:
    """Run one already-Q-common-eligible candidate through all production stages.

    This function does not loop over candidates or cohorts. Structural rejections
    are returned before an SCM ID, coefficient, noise or sample is assigned.
    """
    if not proposal.get("accepted"):
        return {"status": "STRUCTURE_INELIGIBLE", "proposal_id": proposal.get("proposal_id"),
                "reason": proposal.get("reason"), "scm_id": None}
    scm_id = proposal.get("scm_id")
    cohort = proposal.get("cohort")
    if not scm_id or cohort not in {"development", "confirmation"}:
        raise ValueError("eligible proposal must have a cohort-scoped SCM ID")
    if type(delta) is not int or delta not in (-1, 1):
        raise ValueError("delta must be the prespecified +/-1 target direction")
    if _fixture_payload is not None and cohort != "development":
        raise ValueError("fixed pipeline fixtures cannot use the replication namespace")
    config = {"protocol": "step4c1-linear-scm-v1", "budget": ACTIVE_BUDGET,
              "gamma": ACTIVE_GAMMA, "delta": delta, "n_observations": 512,
              "coefficient_abs_range": [0.25, 0.8], "sign_probability": "1/2 each",
              "noise_family": "independent Gaussian, mean 0",
              "noise_sd_range": [0.8, 1.2], "types": TYPES}
    config_sha = hashlib.sha256(_canonical_json(config)).hexdigest()
    input_payload = {"proposal": dict(proposal)}
    if _fixture_payload is not None:
        input_payload["fixed_fixture"] = {
            "truth_spec": _fixture_payload["truth_spec"],
            "exogenous_noise_sha256": hashlib.sha256(
                np.asarray(_fixture_payload["exogenous_noise"], dtype=np.float64).tobytes()).hexdigest()}
        config["fixed_fixture_only"] = True
        config_sha = hashlib.sha256(_canonical_json(config)).hexdigest()
    input_sha = hashlib.sha256(_canonical_json(input_payload)).hexdigest()
    run_id = f"step4c1:{cohort}:{proposal['proposal_id']}:attempt-{proposal['attempt']}"
    stages = {name: ProductionStage(name, str(ledger), run_id, scm_id, cohort,
        config_sha, input_sha, dict(proposal), delta, _fixture_payload) for name in PIPELINE_STAGES}
    return run_pipeline(run_id, ledger, stages,
        rng_key=f"{proposal['cohort']}:{proposal['master_seed']}:{proposal['proposal_id']}:{proposal['attempt']}",
        config=config, input_sha256=input_sha, scm_id=scm_id, cohort=cohort,
        max_wall_seconds=max_wall_seconds, max_unit_seconds=max_unit_seconds,
        max_rss_bytes=max_rss_bytes, max_ledger_bytes=max_ledger_bytes,
        isolate_stages=isolate_stages, checkpoint_hook=checkpoint_hook)

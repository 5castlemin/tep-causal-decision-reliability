"""Approval-gated Research C proposal assembly and cohort orchestration.

TEST_ONLY proposals remain explicitly excluded from study denominators.
Research proposals use the existing outcome-blind topology/task, SCM,
observation, G0 and evaluation components only after runner approval.
"""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np

from research.budget_aware_refinement.step4c1_proposal import build_structural_proposal
from research.budget_aware_refinement.step4c1_scm import (
    generate_observations, generate_scm_parameters,
)

from . import policy_engine as pe
from .cohort_ledger_test_only import _subseed
from .cohort_runner import (run_approved_research_cohort, run_proposal_stage,
                            run_test_only_cohort)
from .execution_limits import ResourceLimits
from .e2e_fixture import FixtureInput
from .g0_candidate import corrupt_graph_candidate


@dataclass(frozen=True)
class _TestOnlyGeneratedFactory:
    proposal: dict
    test_master_seed: int
    outer_scm_id: str

    def __call__(self):
        proposal = self.proposal
        scm = generate_scm_parameters(proposal)
        observations = generate_observations(proposal, scm)
        truth = pe.state(proposal["topology_edges"])
        generator_scm_id = proposal["scm_id"]
        g0_seed = _subseed(self.test_master_seed, "TEST_ONLY", self.outer_scm_id, "g0")
        corruption = corrupt_graph_candidate(
            truth, nodes=proposal["nodes"], action=proposal["action"],
            target=proposal["target"], master_seed=g0_seed,
            task_id=f"TEST_ONLY:{proposal['proposal_id']}")
        initial = pe.state(corruption["initial_graph"]["edges"],
                           unresolved=corruption["initial_graph"]["unresolved"])
        fixture = FixtureInput(
            truth_spec=scm["truth_spec"], initial_graph=initial,
            observations=np.asarray(observations["rows"], dtype=np.float64),
            action=proposal["action"], target=proposal["target"],
            delta=1, test_only=True)
        metadata = {
            "classification": "TEST_ONLY_GENERATED_PROPOSAL",
            "proposal_id": proposal["proposal_id"], "scm_id": self.outer_scm_id,
            "proposal_generator_scm_id": generator_scm_id,
            "proposal_cohort_namespace": proposal["cohort"],
            "topology_hash": proposal["topology_hash"],
            "template": proposal["template"], "node_count": proposal["node_count"],
            "task": {"action": proposal["action"], "target": proposal["target"]},
            "equation_signature_sha256": scm["equation_signature_sha256"],
            "observation_data_sha256": observations["data_sha256"],
            "observation_rows": observations["n_rows"],
            "g0_seed": g0_seed, "g0_generation": corruption,
            "study_sample": False,
        }
        return fixture, metadata


@dataclass(frozen=True)
class _ResearchGeneratedFactory:
    """Outcome-blind SCM/G0 factory used only after the runner approval gate."""
    proposal: dict
    master_seed: int
    scm_id: str
    cohort_namespace: str
    delta: int

    def __call__(self):
        proposal = self.proposal
        scm = generate_scm_parameters(proposal)
        observations = generate_observations(proposal, scm)
        truth = pe.state(proposal["topology_edges"])
        g0_seed = _subseed(self.master_seed, self.cohort_namespace, self.scm_id, "g0")
        corruption = corrupt_graph_candidate(
            truth, nodes=proposal["nodes"], action=proposal["action"],
            target=proposal["target"], master_seed=g0_seed,
            task_id=f"{self.cohort_namespace}:{proposal['proposal_id']}")
        initial = pe.state(corruption["initial_graph"]["edges"],
                           unresolved=corruption["initial_graph"]["unresolved"])
        fixture = FixtureInput(
            truth_spec=scm["truth_spec"], initial_graph=initial,
            observations=np.asarray(observations["rows"], dtype=np.float64),
            action=proposal["action"], target=proposal["target"],
            delta=self.delta, test_only=False)
        metadata = {
            "classification": "RESEARCH_C_GENERATED_PROPOSAL",
            "proposal_id": proposal["proposal_id"], "scm_id": self.scm_id,
            "proposal_generator_scm_id": proposal["scm_id"],
            "cohort_namespace": self.cohort_namespace,
            "topology_hash": proposal["topology_hash"],
            "template": proposal["template"], "node_count": proposal["node_count"],
            "task": {"action": proposal["action"], "target": proposal["target"]},
            "equation_signature_sha256": scm["equation_signature_sha256"],
            "observation_data_sha256": observations["data_sha256"],
            "observation_rows": observations["n_rows"],
            "g0_seed": g0_seed, "g0_generation": corruption,
            "study_sample": True,
        }
        return fixture, metadata


def _test_only_factory(proposal: dict, test_master_seed: int, outer_scm_id: str):
    """Return a picklable deterministic data factory for an isolated worker."""
    return _TestOnlyGeneratedFactory(proposal, test_master_seed, outer_scm_id)


def run_cohort_orchestration(output_root, *, mode: str, run_id: str,
                             master_seed: int, fixtures: dict,
                             proposal_outcomes: list[dict] | None = None,
                             budgets=(0, 1, 2, 3, 4),
                             resource_limits: ResourceLimits | None = None,
                             proposal_active_seconds: float = 0.0,
                             _authorization=None) -> dict:
    """Shared durable execution dispatch; production mode requires gate capability.

    TEST_ONLY callers may use this core for deterministic orchestration tests.
    No test-only override is accepted by the production CLI.
    """
    if mode == "TEST_ONLY":
        if proposal_active_seconds != 0:
            raise ValueError("proposal_active_seconds is reserved for approved research runs")
        if (resource_limits is not None
                and resource_limits.classification != "TEST_ONLY_RESOURCE_ENVELOPE"):
            raise PermissionError("TEST_ONLY orchestration requires TEST_ONLY resource limits")
        return run_test_only_cohort(
            output_root, run_id=run_id, master_seed=master_seed,
            fixtures=fixtures, budgets=budgets,
            proposal_outcomes=proposal_outcomes, resource_limits=resource_limits)
    if mode == "RESEARCH":
        from .e2e_fixture import _RESEARCH_EXECUTION_CAPABILITY
        if _authorization is not _RESEARCH_EXECUTION_CAPABILITY:
            raise PermissionError("research orchestration requires validated runner capability")
        if resource_limits is None:
            raise PermissionError("research orchestration requires an approved resource profile")
        return run_approved_research_cohort(
            output_root, run_id=run_id, master_seed=master_seed,
            fixtures=fixtures, budgets=budgets, proposal_outcomes=proposal_outcomes,
            resource_limits=resource_limits,
            proposal_active_seconds=proposal_active_seconds,
            _authorization=_authorization)
    raise ValueError("mode must be TEST_ONLY or RESEARCH")


def run_test_only_proposal_cohort(output_root, *, run_id: str,
                                  master_seed: int,
                                  proposal_specs: Sequence[dict],
                                  budgets=(0, 1, 2, 3, 4),
                                  resource_limits: ResourceLimits | None = None,
                                  after_claim_hook=None,
                                  before_commit_hook=None) -> dict:
    """Run generator-to-regret E2E on named test proposals only.

    Each spec has proposal_id, attempt, template, and node_count. The existing
    proposal builder uses its development RNG namespace internally, but every
    record and output is labelled TEST_ONLY, names are required to use the
    ``test-only-`` prefix, and no resulting SCM enters a study denominator.
    """
    if type(master_seed) is not int or master_seed < 0:
        raise ValueError("TEST_ONLY master_seed must be a nonnegative integer")
    if not proposal_specs:
        raise ValueError("at least one explicitly named TEST_ONLY proposal is required")

    outcomes = []
    admitted = {}
    for spec in proposal_specs:
        proposal_id = spec.get("proposal_id")
        if not isinstance(proposal_id, str) or not proposal_id.startswith("test-only-"):
            raise PermissionError("proposal IDs must use the TEST_ONLY namespace")
        proposal = build_structural_proposal(
            cohort="development", master_seed=master_seed,
            proposal_id=proposal_id, attempt=spec["attempt"],
            template=spec["template"], node_count=spec["node_count"])
        accepted = bool(proposal["accepted"])
        # Step 4's proposal helper also computes legacy Q-recipe examples;
        # Research C G0 is generated independently below and those recipes
        # are intentionally excluded from this audit record.
        record = {k: v for k, v in proposal.items() if k != "error_recipes"}
        record.update({"status": "ADMITTED" if accepted else "STRUCTURALLY_INELIGIBLE",
                       "test_only": True,
                       "legacy_q_error_recipes_used": False})
        if accepted:
            outer_scm_id = f"test-only-scm-{proposal_id.removeprefix('test-only-')}"
            record["proposal_generator_scm_id"] = proposal["scm_id"]
            record["scm_id"] = outer_scm_id
            record["ledger_scm_id"] = outer_scm_id
            admitted[outer_scm_id] = {
                "factory": _test_only_factory(proposal, master_seed, outer_scm_id),
                "apply_g0_generator": False,
            }
        else:
            record["ledger_scm_id"] = None
        outcomes.append(record)

    if after_claim_hook is not None or before_commit_hook is not None:
        # Process-kill hooks remain confined to the dedicated low-level TEST_ONLY
        # ledger API; they are not part of either orchestration mode.
        result = run_test_only_cohort(
            output_root, run_id=run_id, master_seed=master_seed,
            fixtures=admitted, budgets=budgets, proposal_outcomes=outcomes,
            resource_limits=resource_limits,
            after_claim_hook=after_claim_hook, before_commit_hook=before_commit_hook)
    else:
        result = run_cohort_orchestration(
            output_root, mode="TEST_ONLY", run_id=run_id, master_seed=master_seed,
            fixtures=admitted, budgets=budgets, proposal_outcomes=outcomes,
            resource_limits=resource_limits)
    result["pipeline"] = {
        "classification": "TEST_ONLY_NOT_RESEARCH_COHORT",
        "stages": ["proposal", "strict_q_common", "scm_parameters",
                   "shared_observations", "g0_corruption", "17_policy_e2e",
                   "analytic_gt_evaluation", "regret"],
        "research_execution_authorized": False,
    }
    return result


def build_approved_research_inputs(*, cohort_type: str, master_seed: int,
                                   target_admissions: int, proposal_cap: int,
                                   proposal_builder=build_structural_proposal):
    """Build deterministic proposal records/factories without executing them.

    This function is called only after the runner validates the signed
    configuration and manifest. Attempt and admission denominators are
    distinct; no outcome or regret is inspected while selecting admissions.
    """
    from research.budget_aware_refinement.step4c1_proposal import ATTEMPT_CAPS

    cohort = {"development": "development",
              "independent_evaluation": "confirmation"}.get(cohort_type)
    if cohort is None:
        raise ValueError("unsupported approved cohort type")
    if type(target_admissions) is not int or target_admissions <= 0:
        raise ValueError("target_admissions must be a positive integer")
    if type(proposal_cap) is not int or not target_admissions <= proposal_cap <= ATTEMPT_CAPS[cohort]:
        raise ValueError("proposal_cap must cover the target and stay within the generator cap")
    if type(master_seed) is not int or master_seed < 0:
        raise ValueError("master_seed must be a nonnegative integer")

    proposals = []
    for attempt in range(proposal_cap):
        proposal_id = f"{cohort}-proposal-{attempt + 1:06d}"
        proposals.append(proposal_builder(cohort=cohort, master_seed=master_seed,
                                           proposal_id=proposal_id, attempt=attempt))
        if sum(bool(p["accepted"]) for p in proposals) >= target_admissions:
            break
    return assemble_approved_research_inputs(
        proposals, cohort_type=cohort_type, master_seed=master_seed,
        target_admissions=target_admissions, proposal_cap=proposal_cap)


def assemble_approved_research_inputs(proposals: Sequence[dict], *, cohort_type: str,
                                      master_seed: int, target_admissions: int,
                                      proposal_cap: int):
    """Create factories only from already checkpointed, deterministic proposals."""
    cohort = {"development": "development",
              "independent_evaluation": "confirmation"}.get(cohort_type)
    if cohort is None:
        raise ValueError("unsupported approved cohort type")
    outcomes, admitted = [], {}
    admission_ordinal = 0
    for proposal in proposals:
        proposal_id = proposal.get("proposal_id")
        if (proposal.get("cohort") != cohort or not isinstance(proposal_id, str)
                or proposal.get("attempt") != len(outcomes)):
            raise ValueError("checkpointed proposal sequence/cohort binding is invalid")
        accepted = bool(proposal["accepted"])
        record = {k: v for k, v in proposal.items() if k != "error_recipes"}
        if accepted and admission_ordinal < target_admissions:
            delta = 1 if admission_ordinal % 2 == 0 else -1
            scm_id = proposal["scm_id"]
            record.update({"status": "ADMITTED", "admission_ordinal": admission_ordinal,
                           "delta": delta, "study_sample": True})
            admitted[scm_id] = {
                "factory": _ResearchGeneratedFactory(
                    proposal, master_seed, scm_id, cohort, delta),
                "apply_g0_generator": False,
            }
            admission_ordinal += 1
        else:
            record.update({"status": "STRUCTURALLY_INELIGIBLE" if not accepted
                           else "ELIGIBLE_AFTER_TARGET", "study_sample": False})
        record["ledger_scm_id"] = proposal.get("scm_id") if accepted and admission_ordinal <= target_admissions else None
        outcomes.append(record)
        if admission_ordinal >= target_admissions:
            break
    return {"cohort": cohort, "proposal_outcomes": outcomes,
            "admitted_factories": admitted, "target_admissions": target_admissions,
            "proposal_cap": proposal_cap,
            "shortfall": max(0, target_admissions - len(admitted))}


def run_approved_research_proposal_cohort(output_root, *, run_id: str,
                                          cohort_type: str, master_seed: int,
                                          target_admissions: int, proposal_cap: int,
                                          budgets=(0, 1, 2, 3, 4),
                                          resource_limits: ResourceLimits,
                                          _authorization=None) -> dict:
    """Run the shared proposal-to-ledger path after runner approval validation."""
    from .e2e_fixture import _RESEARCH_EXECUTION_CAPABILITY
    if _authorization is not _RESEARCH_EXECUTION_CAPABILITY:
        raise PermissionError("research proposals require validated runner capability")
    stage = run_proposal_stage(
        output_root, run_id=run_id, cohort_type=cohort_type,
        master_seed=master_seed, target_admissions=target_admissions,
        proposal_cap=proposal_cap, resource_limits=resource_limits,
        _authorization=_authorization)
    if not stage["proposal_stage_complete"]:
        return {"run_id": run_id, "cohort_type": cohort_type,
                "proposal_stage": stage, "admitted_scm_count": 0,
                "completed_scm_count": 0, "all_scm_complete": False,
                "all_target_admissions_completed": False,
                "classification": "RESEARCH_COHORT_INCOMPLETE",
                "reason": "proposal generation/checkpoint did not complete; no SCM admitted"}
    built = assemble_approved_research_inputs(
        stage["proposals"], cohort_type=cohort_type, master_seed=master_seed,
        target_admissions=target_admissions, proposal_cap=proposal_cap)
    result = run_cohort_orchestration(
        output_root, mode="RESEARCH", run_id=run_id, master_seed=master_seed,
        fixtures=built["admitted_factories"], budgets=budgets,
        proposal_outcomes=built["proposal_outcomes"],
        resource_limits=resource_limits,
        proposal_active_seconds=stage["proposal_active_seconds"],
        _authorization=_authorization)
    result["target_admissions"] = target_admissions
    result["proposal_cap"] = proposal_cap
    result["shortfall"] = built["shortfall"]
    result["proposal_stage"] = {key: stage[key] for key in (
        "proposal_stage_status", "proposal_count", "eligible_count", "shortfall",
        "proposal_active_seconds", "config_sha256", "stop_reason", "database_path")}
    result["all_target_admissions_completed"] = (
        built["shortfall"] == 0 and result["completed_scm_count"] == target_admissions)
    result["pipeline"] = {"stages": ["configuration_and_manifest_gate", "topology_proposal",
        "strict_indirect_only_eligibility", "scm_admission", "scm_parameters",
        "shared_observations", "g0_corruption", "17_policy_e2e", "analytic_gt_evaluation",
        "regret", "checksum_ledger"], "cohort_namespace": built["cohort"],
        "regret_used_for_admission": False}
    return result

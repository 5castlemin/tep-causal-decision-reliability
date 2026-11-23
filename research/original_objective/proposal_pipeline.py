"""Approval-gated Research C proposal assembly; TEST_ONLY bridge for validation.

The adapter reuses the existing outcome-blind topology/task proposal, SCM and
observation generators, G0 corruption, and single-SCM E2E evaluator. Generated
examples exposed here are explicitly TEST_ONLY and never constitute a study
cohort. Research execution is still blocked by runner approval and safety gates.
"""
from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import numpy as np

from research.budget_aware_refinement.step4c1_proposal import build_structural_proposal
from research.budget_aware_refinement.step4c1_scm import (
    generate_observations, generate_scm_parameters,
)

from . import policy_engine as pe
from .cohort_ledger_test_only import _subseed
from .cohort_runner import run_test_only_cohort
from .e2e_fixture import FixtureInput
from .g0_candidate import corrupt_graph_candidate


def _test_only_factory(proposal: dict, test_master_seed: int, outer_scm_id: str):
    """Return deterministic data factory for one admitted proposal."""
    def factory():
        scm = generate_scm_parameters(proposal)
        observations = generate_observations(proposal, scm)
        truth = pe.state(proposal["topology_edges"])
        generator_scm_id = proposal["scm_id"]
        g0_seed = _subseed(test_master_seed, "TEST_ONLY", outer_scm_id, "g0")
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
            "proposal_id": proposal["proposal_id"], "scm_id": outer_scm_id,
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
    return factory


def run_test_only_proposal_cohort(output_root, *, run_id: str,
                                  master_seed: int,
                                  proposal_specs: Sequence[dict],
                                  budgets=(0, 1, 2, 3, 4),
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

    result = run_test_only_cohort(
        output_root, run_id=run_id, master_seed=master_seed,
        fixtures=admitted, budgets=budgets, proposal_outcomes=outcomes,
        after_claim_hook=after_claim_hook, before_commit_hook=before_commit_hook)
    result["pipeline"] = {
        "classification": "TEST_ONLY_NOT_RESEARCH_COHORT",
        "stages": ["proposal", "strict_q_common", "scm_parameters",
                   "shared_observations", "g0_corruption", "17_policy_e2e",
                   "analytic_gt_evaluation", "regret"],
        "research_execution_authorized": False,
    }
    return result

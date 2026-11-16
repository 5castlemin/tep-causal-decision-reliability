"""Outcome-blind P-stratum and Q-common structural proposal interface.

Only proposal/topology/task/error structure is constructed here. SCM parameters,
noise and observations are intentionally delegated to the unfinished frozen
specification contract and are never drawn by this module.
"""
from __future__ import annotations

from hashlib import sha256
import json
import random

from .step4_rng import RNGKey, RNG_PROTOCOL_VERSION, STREAMS, derive_seed
from .step4_topology_generator import TEMPLATES, generate_topology, is_dag, directed_paths
from .step4b_task_budget import graph_hash, relabel_roles, role_nodes, select_task_pair
from .step4b2_population import competition_recipes, select_q_recipe

NODE_COUNTS = tuple(range(6, 11))
STRATA = tuple((template, n) for template in TEMPLATES for n in NODE_COUNTS)
ATTEMPT_CAPS = {"development": 362, "confirmation": 1036}
ELIGIBLE_TARGETS = {"development": 64, "confirmation": 200}


def proposal_stratum(*, cohort: str, master_seed: int, proposal_id: str) -> tuple[str, int]:
    """Uniform 1/20 stratum assignment with rejection sampling (no modulo bias)."""
    if cohort not in {"development", "confirmation"} or type(master_seed) is not int or master_seed < 0:
        raise ValueError("invalid proposal cohort or master seed")
    if not proposal_id:
        raise ValueError("proposal ID is required")
    limit = (1 << 256) - ((1 << 256) % len(STRATA))
    counter = 0
    while True:
        payload = f"step4c1-stratum-v1|{cohort}|{master_seed}|{proposal_id}|{counter}".encode()
        value = int.from_bytes(sha256(payload).digest(), "big")
        if value < limit:
            return STRATA[value % len(STRATA)]
        counter += 1


def _seed(cohort, master_seed, proposal_id, template, node_count, attempt, stream, substream=""):
    candidate_namespace = "dev-proposal-" if cohort == "development" else "rep-proposal-"
    key = RNGKey(RNG_PROTOCOL_VERSION, cohort, master_seed,
                 f"{candidate_namespace}{proposal_id}", template, node_count,
                 attempt, stream, substream=substream)
    return derive_seed(key)


def q_common_eligibility(nodes, truth_edges, action: str, target: str) -> dict:
    """Assess Q-common only from topology/task and two-correction structure."""
    nodes, truth_edges = tuple(nodes), frozenset(map(tuple, truth_edges))
    paths = directed_paths(nodes, truth_edges, action, target)
    if not is_dag(nodes, truth_edges):
        return {"eligible": False, "reason": "invalid_gt_dag", "recipe_counts": {}}
    if not any(len(path) >= 3 for path in paths):
        return {"eligible": False, "reason": "task_not_indirect_only", "recipe_counts": {}}
    recipes = {kind: competition_recipes(nodes, truth_edges, action, target, kind)
               for kind in ("FN", "FP", "REV")}
    counts = {kind: len(rows) for kind, rows in recipes.items()}
    eligible = all(counts[kind] > 0 for kind in ("FN", "FP", "REV"))
    return {"eligible": eligible,
            "reason": None if eligible else "missing_same_type_two_candidate_support",
            "recipe_counts": counts,
            "task_paths": [list(path) for path in paths],
            "recipes": recipes if eligible else {}}


def build_structural_proposal(*, cohort: str, master_seed: int,
                              proposal_id: str, attempt: int,
                              template: str | None = None,
                              node_count: int | None = None) -> dict:
    """Generate one outcome-blind topology proposal; never sample an SCM.

    A caller may supply a preassigned P stratum. Otherwise, the proposal ID
    maps to a fixed-probability stratum. Rejected proposals have no SCM ID and
    are not replaced inside this function.
    """
    if cohort not in {"development", "confirmation"}:
        raise ValueError("cohort must be development or confirmation")
    if type(attempt) is not int or not 0 <= attempt < ATTEMPT_CAPS[cohort]:
        raise ValueError("candidate attempt is outside the fixed cohort cap")
    if (template is None) != (node_count is None):
        raise ValueError("template and node_count must be assigned together")
    if template is None:
        template, node_count = proposal_stratum(cohort=cohort, master_seed=master_seed,
                                                proposal_id=proposal_id)
    if (template, node_count) not in STRATA:
        raise ValueError("stratum is outside the active 20-cell P population")
    topology_seed = _seed(cohort, master_seed, proposal_id, template, node_count, attempt, "topology")
    relabel_seed = _seed(cohort, master_seed, proposal_id, template, node_count, attempt, "node_relabeling")
    task_seed = _seed(cohort, master_seed, proposal_id, template, node_count, attempt, "task_selection")
    topology = generate_topology(node_count, template, topology_seed)
    nodes, truth_edges, roles, mapping = relabel_roles(template, topology.nodes,
                                                        topology.edges, relabel_seed)
    scaffold_roles = role_nodes(template, topology.nodes)
    preferred = ((mapping[scaffold_roles["action"]], mapping[scaffold_roles["target"]])
                 if template == "observed_common_cause" else None)
    tasks = select_task_pair(nodes, truth_edges, task_seed, preferred)
    task = next((pair for kind, pair in tasks["selected"] if kind == "indirect"), None)
    base = {"proposal_id": proposal_id, "cohort": cohort, "attempt": attempt,
            "template": template, "node_count": node_count,
            "topology_hash": graph_hash(nodes, truth_edges),
            "topology_edges": [list(edge) for edge in sorted(truth_edges)],
            "role_map": roles, "task_candidate_counts": tasks["candidate_counts"],
            "task_failures": tasks["failures"], "outcomes_used": False,
            "coefficient_or_data_drawn": False}
    if task is None:
        return {**base, "accepted": False, "reason": tasks["failures"].get("indirect", "no_indirect_task"),
                "scm_id": None}
    action, target = task
    support = q_common_eligibility(nodes, truth_edges, action, target)
    if not support["eligible"]:
        return {**base, "accepted": False, "reason": support["reason"],
                "action": action, "target": target, "scm_id": None,
                "q_recipe_counts": support["recipe_counts"]}
    scm_prefix = "dev-scm-" if cohort == "development" else "rep-scm-"
    scm_id = f"{scm_prefix}{proposal_id}"
    error_recipes = {}
    for kind in ("FN", "FP", "REV"):
        seed = _seed(cohort, master_seed, proposal_id, template, node_count,
                     attempt, "error_injection", kind)
        selected = select_q_recipe(support["recipes"][kind], seed)
        error_recipes[kind] = {"initial_edges": [list(edge) for edge in sorted(selected["initial_edges"])],
                               "errors": [list(error) for error in selected["errors"]],
                               "recipe_count": support["recipe_counts"][kind]}
    scm_streams = {
        stream: _seed(cohort, master_seed, scm_id, template, node_count, attempt, stream)
        for stream in ("coefficient", "exogenous_noise", "observational_sample")
    }
    return {**base, "accepted": True, "reason": None, "scm_id": scm_id,
            "action": action, "target": target, "q_recipe_counts": support["recipe_counts"],
            "error_recipes": error_recipes,
            "post_eligibility_rng_seeds": scm_streams,
            "scm_generated": False}

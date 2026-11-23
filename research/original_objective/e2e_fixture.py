"""Shared graph-repair -> fit -> action -> analytic-truth evaluation core.

Ordinary callers can execute TEST_ONLY fixtures. The approved runner supplies
a process-local capability before non-fixture inputs can use this same core.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import sys
from typing import Mapping
from itertools import combinations

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
for _path in (ROOT, ROOT / "src"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from research.budget_aware_refinement.step3_adapter import K, prepare, evaluate
from research.budget_aware_refinement.step4c1_gt import analytic_response
from integrated_pilot import fit_model
from decision_mvp import static_mean_response

from . import policy_engine as pe
from .unresolved_abstention import encode_residual_unresolved_abstention

# Runner supplies this process-local capability only after validating the
# approved configuration and manifest. It is not exposed by the CLI.
_RESEARCH_EXECUTION_CAPABILITY = object()


class _FixtureStageError(RuntimeError):
    def __init__(self, status, reason):
        self.status = status
        super().__init__(reason)


@dataclass(frozen=True)
class FixtureInput:
    truth_spec: Mapping[str, object]
    initial_graph: Mapping[tuple[str, str], tuple[str, str] | str]
    observations: np.ndarray
    action: str
    target: str
    delta: int = 1
    test_only: bool = True


def _digest(value) -> str:
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                              ensure_ascii=True, allow_nan=False).encode()).hexdigest()


def _policy_graph_result(result: Mapping[str, object], nodes) -> dict:
    structural = pe.state(result["final_edges"], unresolved=result["final_unresolved"])
    encoding = encode_residual_unresolved_abstention(structural, nodes=nodes)
    return {"final_graph": encoding["learner_dag_edges"], "edit_sequence": result["edits"],
            "learner_graph_sha256": encoding["learner_dag_sha256"],
            "structural_graph_sha256": encoding["structural_graph_sha256"],
            "abstention_encoding": encoding}


def run_fixed_fixture(fixture: FixtureInput, *, budgets=(0, 1, 2, 3, 4),
                      config: pe.Config = pe.Config(), _authorization=None) -> dict:
    """Run the shared policy/fit/evaluation core for fixture or authorized study input."""
    if fixture.test_only is not True and _authorization is not _RESEARCH_EXECUTION_CAPABILITY:
        raise PermissionError("non-fixture evaluation requires the approved runner capability")
    status_ok = "TEST_ONLY_OK" if fixture.test_only else "RESEARCH_OK"
    mode = "TEST_ONLY" if fixture.test_only else "RESEARCH"
    nodes = tuple(fixture.truth_spec.get("nodes", ()))
    truth_edges = [tuple(edge) for edge in fixture.truth_spec.get("edges", ())]
    truth = pe.state(truth_edges)
    if set(nodes) != set(fixture.truth_spec.get("topological_order", ())):
        raise ValueError("invalid fixture truth node order")
    if set(fixture.initial_graph) and not set(fixture.initial_graph) <= {
        pe.pair(a, b) for i, a in enumerate(nodes) for b in nodes[i+1:]
    }:
        raise ValueError("fixture graph contains an unknown node pair")
    data = np.asarray(fixture.observations, dtype=np.float64)
    if data.ndim != 2 or data.shape[1] != len(nodes) or not np.isfinite(data).all():
        raise ValueError("invalid fixed observation matrix")
    if len(data) < 2 or np.any(data.std(axis=0, ddof=1) <= 0):
        raise ValueError("fixture observations require positive sample variance")
    if fixture.delta not in (-1, 1):
        raise ValueError("invalid delta")
    if fixture.action not in nodes or fixture.target not in nodes:
        raise ValueError("unknown task node")

    input_hash = sha256(data.tobytes(order="C")).hexdigest()
    graph_cache = {}
    rows = []
    for budget in budgets:
        if type(budget) is not int or budget < 0:
            raise ValueError("fixture budgets must be nonnegative integers")
        policies = []
        initial_stats = pe.metrics(truth, fixture.initial_graph, fixture.action,
                                   fixture.target, config)
        initial_error_count = sum(sum(row.values()) for row in initial_stats["counts"].values())
        all_candidates = pe.candidates(truth, fixture.initial_graph, fixture.action,
                                       fixture.target, config)
        structural_runs = [(pe.run(truth, fixture.initial_graph, fixture.action,
                                   fixture.target, budget, subset, config), False)
                           for subset in pe.catalog()]
        canonical = pe.run(truth, fixture.initial_graph, fixture.action,
                           fixture.target, budget, pe.METRICS, config, canonical=True)
        structural_runs.append((canonical, True))
        for structural, is_canonical in structural_runs:
            structural_subset = (pe.METRICS if is_canonical else
                                 tuple(structural["policy_id"].split("+"))
                                 if structural["policy_id"] != "S0" else ())
            eligible_candidates = [e for e in all_candidates
                                   if is_canonical or e.metric in structural_subset]
            candidate_counts_by_metric = {m: sum(e.metric == m for e in eligible_candidates)
                                          for m in pe.METRICS}
            selected_counts_by_metric = {m: sum(row["metric"] == m for row in structural["edits"])
                                         for m in pe.METRICS}
            entry = {"policy_id": structural["policy_id"], "budget": budget,
                     "status": "OK", "failure_reason": None,
                     "initial_error_count": initial_error_count,
                     "repair_candidate_count": len(eligible_candidates),
                     "repair_candidate_counts_by_metric": candidate_counts_by_metric,
                     "selected_edit_counts_by_metric": selected_counts_by_metric,
                     "candidate_status": ("NO_EDIT_POLICY" if not structural_subset and not is_canonical else
                                          "NO_INITIAL_ERRORS" if initial_error_count == 0 else
                                          "NO_ELIGIBLE_REPAIR_CANDIDATES" if not eligible_candidates else
                                          "REPAIR_CANDIDATES_AVAILABLE"),
                     "initial_graph_sha256": structural["initial_hash"],
                     "final_graph_sha256": structural["final_hash"],
                     "edit_log": structural["edits"], "total_edit_cost": structural["total_cost"],
                     "unused_budget": structural["unused_budget"],
                     "stop_reason": structural["stop_reason"],
                     "structural_P_S": structural["P_S"], "structural_P_all": structural["P_all"],
                     "final_error_counts": structural["final_counts"],
                     "learner_graph_sha256": None, "structural_graph_sha256": structural["final_hash"],
                     "unresolved_abstention": None,
                     "evaluation_status": "NOT_EVALUATED", "evaluation": None,
                     "test_only": fixture.test_only}
            try:
                graph = _policy_graph_result(structural, nodes)
                entry["learner_graph_sha256"] = graph["learner_graph_sha256"]
                entry["structural_graph_sha256"] = graph["structural_graph_sha256"]
                entry["unresolved_abstention"] = graph["abstention_encoding"]
            except ValueError as exc:
                entry["status"] = "GRAPH_INPUT_UNSUPPORTED"
                entry["failure_reason"] = str(exc)
                entry["evaluation_status"] = "NOT_EVALUATED"
                policies.append(entry)
                continue
            try:
                cache_key = _digest({"learner_dag": graph["final_graph"], "data": input_hash,
                                     "nodes": nodes, "action": fixture.action,
                                     "target": fixture.target, "delta": fixture.delta,
                                     "candidate_grid": K, "fit": "ridge-alpha-1-v1",
                                     "unresolved_encoding": "abstain-v1"})
                if cache_key not in graph_cache:
                    request = {"node_ids": list(nodes), "action": fixture.action,
                               "target": fixture.target}
                    def guarded_fit(*args, **kwargs):
                        try:
                            return fit_model(*args, **kwargs)
                        except Exception as exc:
                            raise _FixtureStageError("MODEL_FIT_FAILURE", str(exc)) from exc
                    def guarded_response(*args, **kwargs):
                        try:
                            return static_mean_response(*args, **kwargs)
                        except Exception as exc:
                            raise _FixtureStageError("RECOMMENDATION_FAILURE", str(exc)) from exc
                    _, selection = prepare(request, data, list(nodes), list(nodes), fixture.delta,
                                           guarded_fit, guarded_response, graph_result=graph)
                    graph_cache[cache_key] = selection
                selection = graph_cache[cache_key]
            except Exception as exc:
                entry["status"] = (exc.status if isinstance(exc, _FixtureStageError)
                                   else "FIXTURE_INPUT_OR_FIT_FAILURE")
                entry["failure_reason"] = f"{type(exc).__name__}:{str(exc)}"
                entry["evaluation_status"] = "NOT_EVALUATED"
                policies.append(entry)
                continue
            # The learner receives only data, graph and task. Truth becomes
            # visible to the evaluator only after selection is frozen.
            try:
                evaluation = evaluate(selection, fixture.truth_spec, analytic_response)
                entry["evaluation_status"] = status_ok
                entry["evaluation"] = {**evaluation, "selected_k": selection["selected_k"],
                                       "selected_action": next(r["action"] for r in selection["candidates"]
                                                                if r["k"] == selection["selected_k"]),
                                       "predicted_losses": {str(r["k"]): r["predicted_loss"]
                                                            for r in selection["candidates"]},
                                       "truth_rows": evaluation["truth"],
                                       "gt_selected_loss": next(r["loss"] for r in evaluation["truth"]
                                                                 if r["k"] == selection["selected_k"]),
                                       "gt_best_loss": min(r["loss"] for r in evaluation["truth"]),
                                       "decision_margin": _decision_margin(selection["candidates"])}
                entry["model_cache_key"] = cache_key
                entry["training_data_sha256"] = input_hash
                entry["fit_graph_sha256"] = graph["learner_graph_sha256"]
            except Exception as exc:
                entry["status"] = "GT_EVALUATION_FAILURE"
                entry["failure_reason"] = f"{type(exc).__name__}:{str(exc)}"
                entry["evaluation_status"] = "NOT_EVALUATED"
            policies.append(entry)
        s0 = next(p for p in policies if p["policy_id"] == "S0")
        for policy in policies:
            policy["same_graph_as_S0"] = policy["final_graph_sha256"] == s0["final_graph_sha256"]
            if (policy["evaluation_status"] == status_ok
                    and s0["evaluation_status"] == status_ok):
                policy["same_action_as_S0"] = (
                    policy["evaluation"]["selected_action"], policy["evaluation"]["selected_k"]
                ) == (s0["evaluation"]["selected_action"], s0["evaluation"]["selected_k"])
                policy["same_regret_as_S0"] = abs(policy["evaluation"]["regret"]-
                                                  s0["evaluation"]["regret"]) <= 1e-12
                policy["regret_change_from_S0"] = policy["evaluation"]["regret"] - s0["evaluation"]["regret"]
            else:
                policy["same_action_as_S0"] = None
                policy["same_regret_as_S0"] = None
                policy["regret_change_from_S0"] = None
        pairwise = _policy_comparison_diagnostics(policies, initial_error_count, mode=mode)
        # Remove the internal tuples from the output, retaining all per-policy
        # failures. S0 and policies are repeated observations within one fixture.
        rows.append({"budget": budget, "policies": policies,
                     "distinct_successful_graphs": len({p["final_graph_sha256"] for p in policies
                                                        if p["status"] == "OK"}),
                     "policy_vector_status": "COMPLETE" if all(
                         p["evaluation_status"] == status_ok for p in policies) else "INCOMPLETE",
                     "expected_policy_count": len(policies),
                     "evaluable_policy_count": sum(p["evaluation_status"] == status_ok for p in policies),
                     "common_policy_comparison_allowed": all(
                         p["evaluation_status"] == status_ok for p in policies),
                     "policy_comparison_diagnostics": pairwise,
                     "test_only": fixture.test_only})
    _check_equal_action_regret(rows)
    return {"status": mode, "test_only": fixture.test_only,
            "research_cohort_generated": not fixture.test_only,
            "regret_research_result": not fixture.test_only,
            "input": {"truth_graph_sha256": pe.graph_hash(truth),
                      "initial_graph_sha256": pe.graph_hash(fixture.initial_graph),
                      "observations_sha256": input_hash, "nodes": list(nodes),
                      "action": fixture.action, "target": fixture.target,
                      "delta": fixture.delta},
            "model_cache_entries": len(graph_cache), "budgets": rows}


def _decision_margin(candidates):
    values = sorted(float(row["predicted_loss"]) for row in candidates)
    return values[1] - values[0] if len(values) >= 2 else None


def _policy_comparison_diagnostics(policies, initial_error_count, *, mode="TEST_ONLY"):
    graph_pairs = len(list(combinations(policies, 2)))
    same_graph_pairs = 0
    action_pairs = same_action = regret_pairs = regret_ties = 0
    reasons = {"no_repairable_errors": 0, "same_graph": 0,
               "different_graph_same_action": 0, "different_action_same_gt_loss": 0,
               "different_action_different_gt_loss": 0, "not_comparable_failure": 0}
    for left, right in combinations(policies, 2):
        same_graph = left["final_graph_sha256"] == right["final_graph_sha256"]
        if same_graph:
            same_graph_pairs += 1
        if left["evaluation_status"] not in {"TEST_ONLY_OK", "RESEARCH_OK"} \
                or right["evaluation_status"] not in {"TEST_ONLY_OK", "RESEARCH_OK"}:
            reasons["not_comparable_failure"] += 1
            continue
        action_pairs += 1
        left_eval, right_eval = left["evaluation"], right["evaluation"]
        same_act = (left_eval["selected_action"], left_eval["selected_k"]) == (
            right_eval["selected_action"], right_eval["selected_k"])
        if same_act:
            same_action += 1
        else:
            equal_loss = abs(left_eval["gt_selected_loss"] - right_eval["gt_selected_loss"]) <= 1e-12
        regret_pairs += 1
        if abs(left_eval["regret"] - right_eval["regret"]) <= 1e-12:
            regret_ties += 1
        if initial_error_count == 0 or (left["repair_candidate_count"] == 0
                                        and right["repair_candidate_count"] == 0):
            reasons["no_repairable_errors"] += 1
        elif same_graph:
            reasons["same_graph"] += 1
        elif same_act:
            reasons["different_graph_same_action"] += 1
        elif equal_loss:
            reasons["different_action_same_gt_loss"] += 1
        else:
            reasons["different_action_different_gt_loss"] += 1
    return {"pair_count": graph_pairs, "same_final_graph_pairs": same_graph_pairs,
            "same_final_graph_rate": same_graph_pairs / graph_pairs if graph_pairs else None,
            "action_comparable_pairs": action_pairs, "same_action_pairs": same_action,
            "same_action_rate": same_action / action_pairs if action_pairs else None,
            "regret_comparable_pairs": regret_pairs, "regret_tie_pairs": regret_ties,
            "regret_tie_rate": regret_ties / regret_pairs if regret_pairs else None,
            "tie_cause_categories": reasons,
            "classification_status": ("TEST_ONLY_DIAGNOSTIC_NOT_STUDY_ESTIMATE"
                                       if mode == "TEST_ONLY" else "RESEARCH_COHORT_DIAGNOSTIC")}


def _check_equal_action_regret(rows):
    for budget in rows:
        seen = {}
        for policy in budget["policies"]:
            if policy["evaluation_status"] not in {"TEST_ONLY_OK", "RESEARCH_OK"}:
                continue
            result = policy["evaluation"]
            action_key = (result["selected_action"], result["selected_k"])
            regret = result["regret"]
            if action_key in seen and not np.isclose(seen[action_key], regret, rtol=0, atol=1e-12):
                raise AssertionError("same selected action in same GT must have equal regret")
            seen[action_key] = regret


def run_research_cohort(*_args, **_kwargs):
    """Fail-closed placeholder until approval, preregistration and runner exist."""
    raise PermissionError("RESEARCH_C_COHORT_BLOCKED: contract is not approved/preregistered")

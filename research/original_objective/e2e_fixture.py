"""TEST_ONLY graph-repair -> fit -> action -> analytic-truth fixture bridge.

No cohort loop or study sampling is exposed here. Research runs require a
separate approved, preregistered runner and are deliberately rejected below.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import sys
from typing import Mapping

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


def _policy_graph_result(result: Mapping[str, object]) -> dict:
    if result["final_unresolved"]:
        raise ValueError("UNRESOLVED_GRAPH_UNSUPPORTED_BY_LINEAR_FIT_ADAPTER")
    return {"final_graph": result["final_edges"], "edit_sequence": result["edits"]}


def run_fixed_fixture(fixture: FixtureInput, *, budgets=(0, 1, 2, 3, 4),
                      config: pe.Config = pe.Config()) -> dict:
    """Execute only explicit test fixture inputs and mark all truth losses TEST_ONLY."""
    if fixture.test_only is not True:
        raise PermissionError("research cohort execution is not authorized by this fixture API")
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
            entry = {"policy_id": structural["policy_id"], "budget": budget,
                     "status": "OK", "failure_reason": None,
                     "initial_error_count": initial_error_count,
                     "repair_candidate_count": len(eligible_candidates),
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
                     "evaluation_status": "NOT_EVALUATED", "evaluation": None,
                     "test_only": True}
            try:
                graph = _policy_graph_result(structural)
            except ValueError as exc:
                entry["status"] = "GRAPH_INPUT_UNSUPPORTED"
                entry["failure_reason"] = str(exc)
                entry["evaluation_status"] = "NOT_EVALUATED"
                policies.append(entry)
                continue
            try:
                cache_key = _digest({"graph": graph["final_graph"], "data": input_hash,
                                     "nodes": nodes, "action": fixture.action,
                                     "target": fixture.target, "delta": fixture.delta,
                                     "candidate_grid": K, "fit": "ridge-alpha-1-v1"})
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
                entry["evaluation_status"] = "TEST_ONLY_OK"
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
                entry["fit_graph_sha256"] = structural["final_hash"]
            except Exception as exc:
                entry["status"] = "GT_EVALUATION_FAILURE"
                entry["failure_reason"] = f"{type(exc).__name__}:{str(exc)}"
                entry["evaluation_status"] = "NOT_EVALUATED"
            policies.append(entry)
        s0 = next(p for p in policies if p["policy_id"] == "S0")
        for policy in policies:
            policy["same_graph_as_S0"] = policy["final_graph_sha256"] == s0["final_graph_sha256"]
            if (policy["evaluation_status"] == "TEST_ONLY_OK"
                    and s0["evaluation_status"] == "TEST_ONLY_OK"):
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
        # Remove the internal tuples from the output, retaining all per-policy
        # failures. S0 and policies are repeated observations within one fixture.
        rows.append({"budget": budget, "policies": policies,
                     "distinct_successful_graphs": len({p["final_graph_sha256"] for p in policies
                                                        if p["status"] == "OK"}),
                     "test_only": True})
    _check_equal_action_regret(rows)
    return {"status": "TEST_ONLY", "test_only": True,
            "research_cohort_generated": False, "regret_research_result": False,
            "input": {"truth_graph_sha256": pe.graph_hash(truth),
                      "initial_graph_sha256": pe.graph_hash(fixture.initial_graph),
                      "observations_sha256": input_hash, "nodes": list(nodes),
                      "action": fixture.action, "target": fixture.target,
                      "delta": fixture.delta},
            "model_cache_entries": len(graph_cache), "budgets": rows}


def _decision_margin(candidates):
    values = sorted(float(row["predicted_loss"]) for row in candidates)
    return values[1] - values[0] if len(values) >= 2 else None


def _check_equal_action_regret(rows):
    for budget in rows:
        seen = {}
        for policy in budget["policies"]:
            if policy["evaluation_status"] != "TEST_ONLY_OK":
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

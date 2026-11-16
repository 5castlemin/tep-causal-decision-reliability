"""Step 4 paired recommendation and separate truth evaluation adapter.

This connects the existing Step 3 adapter to the active Step 4 policy pair.
It does not generate SCMs or observational data.
"""
from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping

from .step3_adapter import evaluate as step3_evaluate, prepare as step3_prepare
from .step4b4_failure_rules import scm_composite


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _request_without_policy(request: Mapping[str, object]) -> dict:
    return {k: v for k, v in request.items() if k != "policy_id"}


def _validated_regret(selection, truth_spec, analytic_response):
    try:
        result = step3_evaluate(selection, truth_spec, analytic_response)
    except (ValueError, OverflowError, ArithmeticError) as exc:
        return {"status": "GT_EVAL_FAIL", "reason": f"{type(exc).__name__}:{str(exc)[:200]}", "regret": None}
    raw = float(result["regret"])
    if not math.isfinite(raw):
        return {"status": "GT_EVAL_FAIL", "reason": "nonfinite_regret", "regret": None}
    losses = [float(row["loss"]) for row in result["truth"]]
    scale = max([1.0, *map(abs, losses)])
    tolerance = 64.0 * math.ulp(scale)
    if raw < -tolerance:
        return {"status": "NUMERIC_UNSTABLE", "reason": "negative_regret_beyond_roundoff",
                "regret": None, "raw_regret": raw}
    if raw < 0.0:
        result["raw_regret"] = raw
        result["regret"] = 0.0
        result["roundoff_correction"] = "negative_within_64_ulp_clamped_to_zero"
    return {"status": "OK", **result}


def evaluate_frozen_pair(*, global_selection, task_focused_selection,
                         truth_spec, analytic_response) -> dict:
    """Evaluate two already-frozen recommendations under one truth contract."""
    shared = ("action", "target_node", "target", "sd_y")
    if any(global_selection.get(key) != task_focused_selection.get(key) for key in shared):
        raise ValueError("paired selections must share action, target and scale")
    g_candidates, t_candidates = global_selection.get("candidates"), task_focused_selection.get("candidates")
    def candidate_signature(rows):
        return [(row.get("k"), row.get("action")) for row in rows]
    if not isinstance(g_candidates, list) or candidate_signature(g_candidates) != candidate_signature(t_candidates):
        raise ValueError("paired selections must use identical intervention candidates")
    # Both selections have been frozen before either truth call happens.
    global_result = _validated_regret(global_selection, truth_spec, analytic_response)
    focused_result = _validated_regret(task_focused_selection, truth_spec, analytic_response)
    result = {"global": global_result, "task_focused": focused_result}
    if global_result["status"] != "OK" or focused_result["status"] != "OK":
        result.update(paired_status="INCOMPLETE", difference=None)
        return result
    difference = global_result["regret"] - focused_result["regret"]
    if not math.isfinite(difference):
        result.update(paired_status="NONFINITE", difference=None)
    else:
        result.update(paired_status="OK", difference=difference)
    return result


def evaluate_policy_pair(*, request: Mapping[str, object], global_policy_id: str,
                         task_focused_policy_id: str, data, columns: list[str],
                         schema: list[str], delta: int, truth_spec,
                         fit_model, response, analytic_response) -> dict:
    """Prepare both recommendations on shared data, then evaluate both via GT.

    The two request mappings must differ only by policy ID. No truth evaluator
    or truth result is passed into either call to the Step 3 learner adapter.
    """
    if not global_policy_id.startswith("G-") or not task_focused_policy_id.startswith("T-"):
        raise ValueError("policy IDs must identify Global and Task-Focused explicitly")
    if global_policy_id[2:] != task_focused_policy_id[2:]:
        raise ValueError("paired policies must use the same allowed error-type schedule")
    global_request = dict(request, policy_id=global_policy_id)
    focused_request = dict(request, policy_id=task_focused_policy_id)
    if _canonical(_request_without_policy(global_request)) != _canonical(_request_without_policy(focused_request)):
        raise ValueError("paired policy requests differ outside policy ID")
    schema_hash = hashlib.sha256(_canonical(schema)).hexdigest()
    data_hash = hashlib.sha256(data.tobytes() if hasattr(data, "tobytes") else _canonical(data)).hexdigest()
    global_graph, global_selection = step3_prepare(global_request, data, columns, schema, delta, fit_model, response)
    focused_graph, focused_selection = step3_prepare(focused_request, data, columns, schema, delta, fit_model, response)
    # Freeze both recommendations before either GT evaluation is invoked.
    truth_pair = evaluate_frozen_pair(global_selection=global_selection,
                                      task_focused_selection=focused_selection,
                                      truth_spec=truth_spec, analytic_response=analytic_response)
    common = {"schema_sha256": schema_hash, "training_data_sha256": data_hash,
              "request_sha256": hashlib.sha256(_canonical(_request_without_policy(request))).hexdigest(),
              "global_final_graph": global_graph["final_graph"],
              "task_focused_final_graph": focused_graph["final_graph"],
              "global_selection": global_selection, "task_focused_selection": focused_selection,
              "global": truth_pair["global"], "task_focused": truth_pair["task_focused"],
              "paired_status": truth_pair["paired_status"], "difference": truth_pair["difference"]}
    return common


def aggregate_scm_type_results(type_rows: Mapping[str, Mapping[str, object]]) -> dict:
    """Apply the shared mock/production validator to the complete FN/FP/REV vector."""
    required = ("FN", "FP", "REV")
    if set(type_rows) != set(required):
        return {"complete": False, "status": "INCOMPLETE", "D_i": None,
                "reason": "missing_or_extra_type"}
    differences = {}
    for kind in required:
        row = type_rows[kind]
        if row.get("paired_status") != "OK":
            return {"complete": False, "status": "INCOMPLETE", "D_i": None,
                    "reason": f"incomplete_{kind}"}
        differences[kind] = row["difference"]
    return scm_composite(differences)

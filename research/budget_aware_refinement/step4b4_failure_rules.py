"""Executable mock of Step 4B-4 status, fallback and stop decisions."""
from __future__ import annotations

NORMAL_STATUSES = frozenset({"OK", "NO_CANDIDATE", "UNUSED_BUDGET", "CYCLE_REJECT"})
STRUCTURAL_STATUSES = frozenset({"STRUCTURE_INELIGIBLE", "TOPOLOGY_FAIL", "TASK_FAIL"})
COMPUTE_STATUSES = frozenset({"DATA_FAIL", "RIDGE_FAIL", "RECOMMEND_FAIL", "GT_EVAL_FAIL",
                              "NONFINITE", "TIMEOUT", "IO_FAIL", "SYSTEM_FAIL"})


def classify_status(status: str) -> str:
    if status in NORMAL_STATUSES:
        return "normal_result"
    if status in STRUCTURAL_STATUSES:
        return "pre_scm_structural_rejection"
    if status in COMPUTE_STATUSES:
        return "analysis_failure"
    raise ValueError(f"unknown status: {status}")


def fallback_rule(status: str, *, training_valid: bool, truth_valid: bool,
                  k0_in_common_action_grid: bool) -> dict:
    """Fallback only learner/recommendation failure with valid shared inputs."""
    category = classify_status(status)
    if status not in {"RIDGE_FAIL", "RECOMMEND_FAIL"}:
        return {"fallback": False, "primary_value_available": status in NORMAL_STATUSES,
                "reason": "not_a_fallback_eligible_failure", "original_status": status,
                "analysis_category": category}
    if training_valid and truth_valid and k0_in_common_action_grid:
        return {"fallback": True, "fallback_k": 0.0,
                "primary_value_available": True,
                "reason": "valid_k0_intention_to_handle_fallback",
                "original_status": status, "analysis_category": category}
    return {"fallback": False, "primary_value_available": False,
            "reason": "fallback_inputs_or_common_k0_invalid",
            "original_status": status, "analysis_category": category}


def infra_retry_rule(status: str, prior_attempts: int) -> dict:
    """At most one same-key retry for explicitly transient IO/system faults."""
    if prior_attempts < 1:
        raise ValueError("prior_attempts must be positive")
    retryable = status in {"IO_FAIL", "SYSTEM_FAIL"}
    retry = retryable and prior_attempts == 1
    return {"retry": retry, "same_input_and_rng_key": retry,
            "reason": "one_transient_infrastructure_retry" if retry else "retain_failure_no_retry",
            "attempts_after_decision": prior_attempts + int(retry)}


def scm_composite(type_differences: dict[str, float | None]) -> dict:
    """Shared production/mock equal-type SCM validator; never imputes missing values."""
    required = ("FN", "FP", "REV")
    if set(type_differences) != set(required):
        raise ValueError("expected exactly FN, FP, REV")
    if any(type_differences[k] is None for k in required):
        return {"complete": False, "status": "INCOMPLETE", "D_i": None,
                "reason": "incomplete_type_vector_no_complete_case_average"}
    import math
    import numbers
    raw = [type_differences[k] for k in required]
    if any(not isinstance(value, numbers.Real) or isinstance(value, bool) for value in raw):
        return {"complete": False, "status": "NONFINITE", "D_i": None,
                "reason": "invalid_type_difference"}
    values = [float(value) for value in raw]
    if any(not math.isfinite(x) for x in values):
        return {"complete": False, "status": "NONFINITE", "D_i": None,
                "reason": "nonfinite_type_difference"}
    mean = math.fsum(values) / 3.0
    if not math.isfinite(mean):
        return {"complete": False, "status": "NONFINITE", "D_i": None,
                "reason": "nonfinite_composite"}
    return {"complete": True, "status": "OK", "D_i": mean,
            "type_differences": values, "reason": None}


def confirmation_action(*, q_eligible_target: int, q_eligible_observed: int,
                        candidate_attempts: int, attempt_cap: int,
                        missing_primary_scm_rows: int) -> dict:
    """Do not weaken the target after a cap or compute failure."""
    if min(q_eligible_target, q_eligible_observed, candidate_attempts, attempt_cap,
           missing_primary_scm_rows) < 0:
        raise ValueError("counts must be nonnegative")
    if candidate_attempts > attempt_cap:
        raise ValueError("attempt cap exceeded")
    if q_eligible_observed < q_eligible_target:
        return {"inferential_start": False, "state": "shortfall",
                "reason": "finite_candidate_pool_below_eligible_target"}
    if missing_primary_scm_rows:
        return {"inferential_start": False, "state": "inconclusive",
                "reason": "primary_scm_vector_incomplete"}
    return {"inferential_start": True, "state": "ready", "reason": None}


def probability_complete(n_scm: int, per_event_missing_rate: float,
                        events_per_scm: int = 1) -> float:
    """MCAR illustration only; assumes independent event-level missingness."""
    if type(n_scm) is not int or n_scm < 1 or type(events_per_scm) is not int or events_per_scm < 1:
        raise ValueError("sample size and events_per_scm must be positive integers")
    if not 0 <= per_event_missing_rate <= 1:
        raise ValueError("missing rate must be in [0,1]")
    return (1.0 - per_event_missing_rate) ** (n_scm * events_per_scm)

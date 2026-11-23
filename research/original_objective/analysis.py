"""SCM-level analyses for completed Research C cohort ledgers.

This module contains analysis-only calculations. It does not generate SCMs,
fit models, alter ledgers, or choose policies from outcome data.
"""
from __future__ import annotations

import math
import random
import statistics

HELDOUT_BOOTSTRAP_SEED = 2026112302
HELDOUT_BOOTSTRAP_REPLICATES = 10_000


def validate_heldout_bootstrap_contract(seed: int, replicates: int) -> None:
    """Reject analysis settings that differ from the user-approved lock."""
    if seed != HELDOUT_BOOTSTRAP_SEED:
        raise ValueError("bootstrap seed differs from the approved Held-out analysis lock")
    if replicates != HELDOUT_BOOTSTRAP_REPLICATES:
        raise ValueError("bootstrap replicate count differs from the approved Held-out analysis lock")


def sign_counts(values: list[float]) -> dict[str, int]:
    return {"improve": sum(value > 0 for value in values),
            "worsen": sum(value < 0 for value in values),
            "tie": sum(value == 0 for value in values)}


def p1_delta(s0_regret: float | None, full_greedy_regret: float | None) -> float | None:
    """Return the approved P1 difference, preserving incomplete pairs as missing."""
    if s0_regret is None or full_greedy_regret is None:
        return None
    return float(s0_regret) - float(full_greedy_regret)


def m4_secondary_delta(full_greedy_regret: float | None, m4_regret: float | None) -> float | None:
    """Return Development-selected comparison, positive when M4 regret is lower."""
    if full_greedy_regret is None or m4_regret is None:
        return None
    return float(full_greedy_regret) - float(m4_regret)


def percentile_linear(sorted_values: list[float], probability: float) -> float:
    """Linear interpolation at (n-1)*p, matching NumPy's default method."""
    if not sorted_values or not 0 <= probability <= 1:
        raise ValueError("nonempty values and probability in [0,1] are required")
    position = (len(sorted_values) - 1) * probability
    lo = math.floor(position)
    hi = math.ceil(position)
    if lo == hi:
        return sorted_values[lo]
    weight = position - lo
    return sorted_values[lo] * (1 - weight) + sorted_values[hi] * weight


def paired_bootstrap_mean(values: list[float], *, seed: int,
                          replicates: int = 10_000) -> dict:
    """Resample whole SCM-level deltas with replacement using CPython MT19937."""
    if not values:
        raise ValueError("at least one complete SCM pair is required")
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative integer")
    if type(replicates) is not int or replicates < 1:
        raise ValueError("replicates must be a positive integer")
    rng = random.Random(seed)
    n = len(values)
    means = []
    for _ in range(replicates):
        means.append(sum(values[rng.randrange(n)] for _ in range(n)) / n)
    ordered = sorted(means)
    return {"method": "SCM-level paired percentile bootstrap; linear quantiles",
            "rng": "CPython random.Random MT19937", "seed": seed,
            "replicates": replicates, "resampling_unit": "SCM",
            "resample_size": n, "lower": percentile_linear(ordered, 0.025),
            "upper": percentile_linear(ordered, 0.975),
            "bootstrap_mean_of_means": statistics.mean(means)}


def _student_t_cdf_positive(x: float, df: int) -> float:
    """Simpson integration of the Student-t density on [0,x]."""
    if x < 0 or df < 1:
        raise ValueError("x must be nonnegative and df positive")
    n = 8192
    h = x / n
    scale = math.gamma((df + 1) / 2) / (
        math.sqrt(df * math.pi) * math.gamma(df / 2))

    def density(value: float) -> float:
        return scale * (1 + value * value / df) ** (-(df + 1) / 2)

    total = density(0) + density(x)
    total += 4 * sum(density(i * h) for i in range(1, n, 2))
    total += 2 * sum(density(i * h) for i in range(2, n, 2))
    return 0.5 + total * h / 3


def _student_t_quantile(probability: float, df: int) -> float:
    if not 0.5 < probability < 1:
        raise ValueError("probability must be between 0.5 and 1")
    low, high = 0.0, 10.0
    for _ in range(60):
        mid = (low + high) / 2
        if _student_t_cdf_positive(mid, df) < probability:
            low = mid
        else:
            high = mid
    return (low + high) / 2


def paired_t_summary(values: list[float], confidence: float = 0.95) -> dict:
    """Mean, sample SD, and two-sided Student-t interval on SCM-level deltas."""
    if len(values) < 2:
        raise ValueError("at least two complete SCM pairs are required")
    if not 0 < confidence < 1:
        raise ValueError("confidence must be between 0 and 1")
    n = len(values)
    mean = statistics.mean(values)
    sd = statistics.stdev(values)
    se = sd / math.sqrt(n)
    critical = _student_t_quantile((1 + confidence) / 2, n - 1)
    return {"n_pairs": n, "df": n - 1, "mean": mean, "median": statistics.median(values),
            "sample_sd": sd, "standard_error": se, "confidence": confidence,
            "critical_t": critical, "lower": mean - critical * se,
            "upper": mean + critical * se,
            "method": "two-sided paired-t interval on SCM-level paired differences"}


def paired_summary(values: list[float]) -> dict:
    if not values:
        raise ValueError("at least one complete SCM pair is required")
    return {"n_pairs": len(values), "mean": statistics.mean(values),
            "median": statistics.median(values),
            "sample_sd": statistics.stdev(values) if len(values) > 1 else None,
            "sign_counts": sign_counts(values)}

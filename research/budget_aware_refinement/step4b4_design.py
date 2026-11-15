"""Small, dependency-light helpers for Step 4B-4 design calibration.

These functions operate on structural acceptance counts or paired summary
vectors. They do not generate SCMs, observations, effects, or regret.
"""
from __future__ import annotations

from math import exp, lgamma, log, sqrt


def _beta_continued_fraction(a: float, b: float, x: float) -> float:
    max_iter, epsilon, floor = 300, 3e-14, 1e-300
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < floor:
        d = floor
    d = 1.0 / d
    h = d
    for m in range(1, max_iter + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < floor:
            d = floor
        c = 1.0 + aa / c
        if abs(c) < floor:
            c = floor
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < floor:
            d = floor
        c = 1.0 + aa / c
        if abs(c) < floor:
            c = floor
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < epsilon:
            return h
    raise ArithmeticError("incomplete beta continued fraction did not converge")


def regularized_beta(x: float, a: float, b: float) -> float:
    if not (a > 0 and b > 0 and 0 <= x <= 1):
        raise ValueError("invalid incomplete beta arguments")
    if x in (0.0, 1.0):
        return x
    front = exp(lgamma(a + b) - lgamma(a) - lgamma(b)
                + a * log(x) + b * log1p_neg(x))
    if x < (a + 1.0) / (a + b + 2.0):
        return front * _beta_continued_fraction(a, b, x) / a
    return 1.0 - front * _beta_continued_fraction(b, a, 1.0 - x) / b


def log1p_neg(x: float) -> float:
    # Keep the implementation standard-library-only and stable near one.
    from math import log1p
    return log1p(-x)


def beta_quantile(probability: float, a: float, b: float) -> float:
    if not 0.0 < probability < 1.0:
        raise ValueError("probability must be in (0, 1)")
    lo, hi = 0.0, 1.0
    for _ in range(90):
        mid = (lo + hi) / 2.0
        if regularized_beta(mid, a, b) < probability:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def clopper_pearson(successes: int, trials: int, alpha: float = 0.05) -> tuple[float, float]:
    """Two-sided exact binomial interval; failures stay in the denominator."""
    if type(successes) is not int or type(trials) is not int or not 0 <= successes <= trials:
        raise ValueError("invalid binomial counts")
    if trials < 1 or not 0 < alpha < 1:
        raise ValueError("invalid trial count or alpha")
    lower = 0.0 if successes == 0 else beta_quantile(alpha / 2.0, successes,
                                                      trials - successes + 1)
    upper = 1.0 if successes == trials else beta_quantile(1.0 - alpha / 2.0,
                                                            successes + 1,
                                                            trials - successes)
    return lower, upper


def binomial_probability_at_least(target: int, trials: int, probability: float) -> float:
    """Exact P[Binomial(trials, probability) >= target] by lower-tail sum."""
    if type(target) is not int or type(trials) is not int or target < 0 or trials < 0:
        raise ValueError("invalid target/trials")
    if not 0 <= probability <= 1:
        raise ValueError("invalid probability")
    if target == 0:
        return 1.0
    if target > trials or probability == 0:
        return 0.0
    if probability == 1:
        return 1.0
    term = (1.0 - probability) ** trials
    cdf = term
    for k in range(0, target - 1):
        term *= ((trials - k) / (k + 1)) * probability / (1.0 - probability)
        cdf += term
    return max(0.0, min(1.0, 1.0 - cdf))


def minimum_attempt_cap(target_eligible: int, probability: float,
                        conditional_yield_probability: float = 0.95) -> tuple[int, float]:
    """Smallest fixed candidate pool meeting a conditional yield probability."""
    if target_eligible < 1 or not 0 < conditional_yield_probability < 1:
        raise ValueError("invalid target or yield probability")
    if not 0 < probability <= 1:
        raise ValueError("probability must be in (0, 1]")
    lo, hi = target_eligible - 1, max(target_eligible, 1)
    while binomial_probability_at_least(target_eligible, hi, probability) < conditional_yield_probability:
        hi *= 2
    while lo + 1 < hi:
        mid = (lo + hi) // 2
        if binomial_probability_at_least(target_eligible, mid, probability) >= conditional_yield_probability:
            hi = mid
        else:
            lo = mid
    return hi, binomial_probability_at_least(target_eligible, hi, probability)


def student_t_critical(two_sided_alpha: float, degrees_freedom: int) -> float:
    """Two-sided Student t critical value using the regularized beta identity."""
    if not 0 < two_sided_alpha < 1 or degrees_freedom < 1:
        raise ValueError("invalid alpha or degrees of freedom")
    df = float(degrees_freedom)
    lo, hi = 0.0, 1.0
    def upper_tail(t_value: float) -> float:
        x = df / (df + t_value * t_value)
        return 0.5 * regularized_beta(x, df / 2.0, 0.5)
    while upper_tail(hi) > two_sided_alpha / 2.0:
        hi *= 2.0
    for _ in range(80):
        mid = (lo + hi) / 2.0
        if upper_tail(mid) > two_sided_alpha / 2.0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def paired_t_interval(values, alpha: float = 0.05) -> tuple[float, float]:
    """SCM-level paired mean CI; caller supplies exactly one value per SCM."""
    x = [float(value) for value in values]
    if len(x) < 2 or any(not __import__("math").isfinite(value) for value in x):
        raise ValueError("paired differences must be a finite 1-D vector with n>=2")
    mean = sum(x) / len(x)
    variance = sum((value - mean) ** 2 for value in x) / (len(x) - 1)
    se = sqrt(variance / len(x))
    crit = student_t_critical(alpha, len(x) - 1)
    return mean - crit * se, mean + crit * se


def paired_t_reject(values, alpha: float = 0.05) -> bool:
    lower, upper = paired_t_interval(values, alpha)
    return lower > 0.0 or upper < 0.0


def scm_bootstrap_interval(values, *, replicates: int = 20_000, seed: int = 440041,
                           alpha: float = 0.05) -> tuple[float, float]:
    """Percentile sensitivity CI resampling SCM rows, never nested cells."""
    import numpy as np
    x = np.asarray(values, dtype=float)
    if x.ndim != 1 or x.size < 2 or not np.isfinite(x).all():
        raise ValueError("paired differences must be a finite 1-D vector with n>=2")
    if type(replicates) is not int or replicates < 1 or type(seed) is not int:
        raise ValueError("invalid bootstrap settings")
    rng = np.random.default_rng(seed)
    means = np.empty(replicates, dtype=float)
    chunk = max(1, min(replicates, 1_000_000 // x.size))
    offset = 0
    while offset < replicates:
        count = min(chunk, replicates - offset)
        indices = rng.integers(0, x.size, size=(count, x.size))
        means[offset:offset + count] = x[indices].mean(axis=1)
        offset += count
    return tuple(map(float, np.quantile(means, [alpha / 2.0, 1.0 - alpha / 2.0])))

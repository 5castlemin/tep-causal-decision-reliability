"""Outcome-free calibration on SCM-level paired-difference distributions.

The simulated values are abstract statistical draws, not SCM outcomes or
Decision Regret observations.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

import numpy as np

from .step4b4_design import student_t_critical

HERE = Path(__file__).parent
OUTPUT = HERE / "step4b4_statistical_calibration_v1.json"
SEED = 4042026
N_GRID = (34, 64, 100, 200)
REPLICATES = 20_000
ALPHA = 0.05
MEAN_TARGET = 0.10
BOOTSTRAP_N = 200
BOOTSTRAP_OUTER = 2000
BOOTSTRAP_INNER = 499
SCENARIOS = ("normal", "zero_heavy_symmetric", "zero_heavy_skewed",
             "rare_symmetric_extremes", "degenerate_zero")
SETTINGS = {
    "protocol": "STEP4B4_ABSTRACT_PAIRED_DIFFERENCE_CALIBRATION_V1",
    "seed": SEED, "n_grid": N_GRID, "replicates_per_scenario_n": REPLICATES,
    "two_sided_alpha": ALPHA, "shifted_mean": MEAN_TARGET,
    "scenarios": SCENARIOS,
    "primary_candidate": "two-sided SCM-level paired t test and t-based 95% CI",
    "bootstrap_sensitivity": {"n": BOOTSTRAP_N, "outer_replicates": BOOTSTRAP_OUTER,
                              "inner_resamples": BOOTSTRAP_INNER,
                              "method": "SCM-row percentile bootstrap CI"},
    "no_scm_or_regret_draws": True,
}
SETTINGS_SHA256 = sha256(json.dumps(SETTINGS, sort_keys=True, separators=(",", ":"),
                                   default=list).encode()).hexdigest()


def _draw(name, rng, shape):
    if name == "normal":
        return rng.normal(size=shape)
    u = rng.random(shape)
    x = np.zeros(shape, dtype=float)
    if name == "zero_heavy_symmetric":
        x[u < 0.10] = -np.sqrt(5.0)
        x[(u >= 0.10) & (u < 0.20)] = np.sqrt(5.0)
    elif name == "zero_heavy_skewed":
        positive = np.sqrt(1.0 / 0.9)
        x[u < 0.01] = -9.0 * positive
        x[(u >= 0.90) & (u < 0.99)] = positive
    elif name == "rare_symmetric_extremes":
        x[u < 0.005] = -10.0
        x[(u >= 0.005) & (u < 0.010)] = 10.0
    elif name == "degenerate_zero":
        pass
    else:
        raise ValueError(f"unknown scenario: {name}")
    return x


def _summarize_t(values, critical):
    n = values.shape[1]
    means = values.mean(axis=1)
    sd = values.std(axis=1, ddof=1)
    se = sd / np.sqrt(n)
    t_stat = np.divide(means, se, out=np.zeros_like(means), where=se > 0)
    reject = np.abs(t_stat) > critical
    low, high = means - critical * se, means + critical * se
    return {"rejection_rate": float(reject.mean()),
            "ci_coverage": float(((low <= 0.0) & (high >= 0.0)).mean()),
            "zero_sample_sd_rate": float((sd == 0).mean()),
            "mcse_rejection": float(np.sqrt(reject.mean() * (1 - reject.mean()) / len(reject))),
            "mean_estimate_sd": float(means.std(ddof=1))}


def _bootstrap_coverage(name, rng):
    n, outer, inner = BOOTSTRAP_N, BOOTSTRAP_OUTER, BOOTSTRAP_INNER
    critical = student_t_critical(ALPHA, n - 1)
    cover_t = cover_boot = 0
    degenerate_boot = 0
    for _ in range(outer):
        x = _draw(name, rng, (n,))
        sd = float(x.std(ddof=1))
        mean = float(x.mean())
        half = critical * sd / np.sqrt(n)
        cover_t += (mean - half <= 0.0 <= mean + half)
        indices = rng.integers(0, n, size=(inner, n))
        means = x[indices].mean(axis=1)
        lo, hi = np.quantile(means, [ALPHA / 2.0, 1.0 - ALPHA / 2.0])
        cover_boot += (lo <= 0.0 <= hi)
        degenerate_boot += (lo == hi)
    return {"n": n, "outer_replicates": outer, "bootstrap_resamples": inner,
            "t_ci_coverage": cover_t / outer,
            "percentile_bootstrap_coverage": cover_boot / outer,
            "bootstrap_degenerate_interval_rate": degenerate_boot / outer,
            "coverage_mcse_max": float(np.sqrt(0.25 / outer))}


def run():
    rng = np.random.default_rng(SEED)
    results = {}
    for scenario in SCENARIOS:
        by_n = {}
        for n in N_GRID:
            critical = student_t_critical(ALPHA, n - 1)
            null = _draw(scenario, rng, (REPLICATES, n))
            alt = null + MEAN_TARGET
            null_result = _summarize_t(null, critical)
            alt_result = _summarize_t(alt, critical)
            by_n[str(n)] = {"critical_value": critical,
                            "type1_and_null_ci_coverage": null_result,
                            "power_at_mean_0_10": alt_result["rejection_rate"],
                            "alt_ci_coverage_at_mean_0_10": alt_result["ci_coverage"],
                            "alt_zero_sample_sd_rate": alt_result["zero_sample_sd_rate"]}
        results[scenario] = by_n
    bootstrap = {name: _bootstrap_coverage(name, rng) for name in
                 ("normal", "zero_heavy_symmetric", "zero_heavy_skewed",
                  "rare_symmetric_extremes", "degenerate_zero")}
    return {"settings": SETTINGS, "settings_sha256": SETTINGS_SHA256,
            "results": results, "bootstrap_sensitivity_n200": bootstrap,
            "interpretation_limits": [
                "Monte Carlo distributions are abstract paired differences, not SCM outcomes.",
                "The t test estimates a mean but finite-sample calibration may fail under rare extremes and mass at zero.",
                "Rejecting mean zero does not establish a mean improvement exceeding 0.10.",
                "A topology-pilot SD is unavailable; simulated power is scenario-based, not guaranteed study power.",
            ]}


def main():
    result = run()
    text = json.dumps(result, sort_keys=True, indent=2, allow_nan=False)
    OUTPUT.write_text(text + "\n", encoding="utf-8")
    print(json.dumps({"settings_sha256": result["settings_sha256"],
                      "output": str(OUTPUT.name),
                      "n200_normal_type1": result["results"]["normal"]["200"]["type1_and_null_ci_coverage"]["rejection_rate"],
                      "n200_normal_power_at_0_10": result["results"]["normal"]["200"]["power_at_mean_0_10"]}, indent=2))


if __name__ == "__main__":
    main()

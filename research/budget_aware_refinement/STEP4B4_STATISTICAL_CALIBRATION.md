> **Historical v1 note:** `alt_ci_coverage_at_mean_0_10` in the v1 JSON incorrectly measures whether zero is inside the alternative CI. It is not coverage of the true mean 0.10. v1 raw is preserved; corrected coverage and numerical handling are in [v2](STEP4B4_STATISTICAL_CALIBRATION_V2.md).

# Step 4B-4 statistical calibration

Status: **IN_PROGRESS; no primary test/CI selected**. The runner generates abstract paired-difference distributions only; these are not SCMs, outcomes or regret. Settings SHA-256: `8b3d40f8274624926777b2e5060230ed9a113cd994382bcec7723d10d6dab662`. 20,000 Monte Carlo repetitions per scenario and n in {34,64,100,200}; two-sided alpha=.05; mean shift=.10.

At n=200, paired t rejection/type-I and corresponding null CI coverage were: Normal .048/.952; zero-heavy symmetric .049/.951; zero-heavy skewed .136/.864; rare symmetric extremes .013/.987; all-zero 0/1.00. For mean shift .10, power was approximately .293 (normal), .293 (zero-heavy symmetric), .409 (skewed), .264 (rare extremes), and 0 (degenerate). These distributions have variance standardized to about one except the degenerate case.

SCM-row percentile bootstrap sensitivity at n=200 used 2,000 outer samples × 499 resamples. Coverage: normal .9445; zero-heavy symmetric .9485; skewed .8545; rare extremes .9910; degenerate 1.00 with 100% degenerate interval. Monte Carlo standard error is at most .0112. Thus neither paired t nor percentile bootstrap has acceptable calibration across the deliberately stressed skewed scenario. A high rejection rate in the shifted skewed scenario does not repair its inflated type-I error.

Conclusion: do not freeze paired t or percentile bootstrap as the primary inference. Exact sign-flip would require a symmetry condition not established for the mean estimand. A robust/ studentized alternative requires new outcome-free calibration under explicitly justified distributions and Step 4C review. The observed calibration is a blocker, not a post-hoc reason to change the estimand.

The .10 threshold remains a proposed minimum meaningful difference on standardized mean-response squared-loss scale; it is not a 10% manufacturing cost reduction or an externally validated utility threshold. A test against zero and evidence that the effect exceeds .10 are different claims. For one H2 primary contrast alpha=.05 would not require Holm; type-specific analyses and matched Random comparisons remain secondary, with multiplicity treatment specified before final freeze.

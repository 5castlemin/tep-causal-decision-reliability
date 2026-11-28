# Research S3 corrected deep-analysis results

**Classification:** post-hoc exploratory; original Research C cohorts reused. Correction contract lock commit: `b832001c701f8183cb7ddb53ba02950785a36a9a`. Executed analysis source revision: `616ec21499eb4cd4b43139423240cd380a643d86`. No new SCM/G0/independent observations/intervention rows were generated.

## B=2 baselines and policy comparisons

| Cohort | Policy | Mean regret | Mean edits | Action-change rate vs S0 |
|---|---|---:|---:|---:|
| C_DEVELOPMENT | S0 | 0.100852 | 0.000000 | 0.000000 |
| C_DEVELOPMENT | FULL_GREEDY | 0.025641 | 1.453125 | 0.234375 |
| C_DEVELOPMENT | CANONICAL_ORACLE | 0.056047 | 1.453125 | 0.156250 |
| C_DEVELOPMENT | M4_ORIGINAL | 0.002928 | 0.656250 | 0.281250 |
| C_DEVELOPMENT | M4_FN_FIRST | 0.002560 | 0.656250 | 0.265625 |
| C_DEVELOPMENT | M4_FP_FIRST | 0.002928 | 0.656250 | 0.281250 |
| C_DEVELOPMENT | M4_REV_FIRST | 0.002928 | 0.656250 | 0.281250 |
| C_DEVELOPMENT | M4_UNRES_FIRST | 0.002928 | 0.656250 | 0.281250 |
| C_DEVELOPMENT | M4_RANDOM_EXPECTATION | 0.002805 | 0.656250 | 0.276042 |
| C_HELDOUT | S0 | 0.093439 | 0.000000 | 0.000000 |
| C_HELDOUT | FULL_GREEDY | 0.018603 | 1.435000 | 0.230000 |
| C_HELDOUT | CANONICAL_ORACLE | 0.055398 | 1.435000 | 0.190000 |
| C_HELDOUT | M4_ORIGINAL | 0.003988 | 0.695000 | 0.255000 |
| C_HELDOUT | M4_FN_FIRST | 0.003717 | 0.695000 | 0.260000 |
| C_HELDOUT | M4_FP_FIRST | 0.006841 | 0.695000 | 0.260000 |
| C_HELDOUT | M4_REV_FIRST | 0.003988 | 0.695000 | 0.255000 |
| C_HELDOUT | M4_UNRES_FIRST | 0.004639 | 0.695000 | 0.250000 |
| C_HELDOUT | M4_RANDOM_EXPECTATION | 0.006994 | 0.695000 | 0.252500 |

Random-M4 is an exact expectation over uniform sequential legal choices; its action-change column is the expected probability of changing the S0 action, not the action-change rate of a single realized trajectory.

## Corrected 63-subset Greedy replay

All 63 nonempty T1–T6 subsets were recomputed at B=1–4 in Development (64) and Held-out (200). Cohort policy aggregates, paired intervals, and candidate summaries are in `tables/correction_v1/`. The 63-way observed minima are descriptive and must not be treated as selected confirmatory policies.

| Cohort | B | Policy | Mean regret | Mean edits |
|---|---:|---|---:|---:|
| C_DEVELOPMENT | 1 | S0 | 0.100852 | 0.000000 |
| C_DEVELOPMENT | 1 | FULL_GREEDY | 0.054209 | 0.890625 |
| C_DEVELOPMENT | 1 | CANONICAL_ORACLE | 0.093793 | 0.890625 |
| C_DEVELOPMENT | 1 | M4_ORIGINAL | 0.023753 | 0.484375 |
| C_DEVELOPMENT | 1 | M4_FN_FIRST | 0.006315 | 0.484375 |
| C_DEVELOPMENT | 1 | M4_FP_FIRST | 0.029833 | 0.484375 |
| C_DEVELOPMENT | 1 | M4_REV_FIRST | 0.023753 | 0.484375 |
| C_DEVELOPMENT | 1 | M4_UNRES_FIRST | 0.028031 | 0.484375 |
| C_DEVELOPMENT | 1 | M4_RANDOM_EXPECTATION | 0.024821 | 0.484375 |
| C_DEVELOPMENT | 1 | T3 | 0.002560 | 0.484375 |
| C_DEVELOPMENT | 1 | T1+T2+T3+T4+T5+T6 | 0.002560 | 0.484375 |
| C_DEVELOPMENT | 2 | S0 | 0.100852 | 0.000000 |
| C_DEVELOPMENT | 2 | FULL_GREEDY | 0.025641 | 1.453125 |
| C_DEVELOPMENT | 2 | CANONICAL_ORACLE | 0.056047 | 1.453125 |
| C_DEVELOPMENT | 2 | M4_ORIGINAL | 0.002928 | 0.656250 |
| C_DEVELOPMENT | 2 | M4_FN_FIRST | 0.002560 | 0.656250 |
| C_DEVELOPMENT | 2 | M4_FP_FIRST | 0.002928 | 0.656250 |
| C_DEVELOPMENT | 2 | M4_REV_FIRST | 0.002928 | 0.656250 |
| C_DEVELOPMENT | 2 | M4_UNRES_FIRST | 0.002928 | 0.656250 |
| C_DEVELOPMENT | 2 | M4_RANDOM_EXPECTATION | 0.002805 | 0.656250 |
| C_DEVELOPMENT | 2 | T3 | 0.002560 | 0.656250 |
| C_DEVELOPMENT | 2 | T1+T2+T3+T4+T5+T6 | 0.002560 | 0.656250 |
| C_DEVELOPMENT | 3 | S0 | 0.100852 | 0.000000 |
| C_DEVELOPMENT | 3 | FULL_GREEDY | 0.002560 | 1.812500 |
| C_DEVELOPMENT | 3 | CANONICAL_ORACLE | 0.025265 | 1.812500 |
| C_DEVELOPMENT | 3 | M4_ORIGINAL | 0.002560 | 0.703125 |
| C_DEVELOPMENT | 3 | M4_FN_FIRST | 0.002560 | 0.703125 |
| C_DEVELOPMENT | 3 | M4_FP_FIRST | 0.002560 | 0.703125 |
| C_DEVELOPMENT | 3 | M4_REV_FIRST | 0.002560 | 0.703125 |
| C_DEVELOPMENT | 3 | M4_UNRES_FIRST | 0.002560 | 0.703125 |
| C_DEVELOPMENT | 3 | T3 | 0.002560 | 0.703125 |
| C_DEVELOPMENT | 3 | T1+T2+T3+T4+T5+T6 | 0.002560 | 0.703125 |
| C_DEVELOPMENT | 4 | S0 | 0.100852 | 0.000000 |
| C_DEVELOPMENT | 4 | FULL_GREEDY | 0.002560 | 1.968750 |
| C_DEVELOPMENT | 4 | CANONICAL_ORACLE | 0.011762 | 1.968750 |
| C_DEVELOPMENT | 4 | M4_ORIGINAL | 0.002560 | 0.718750 |
| C_DEVELOPMENT | 4 | M4_FN_FIRST | 0.002560 | 0.718750 |
| C_DEVELOPMENT | 4 | M4_FP_FIRST | 0.002560 | 0.718750 |
| C_DEVELOPMENT | 4 | M4_REV_FIRST | 0.002560 | 0.718750 |
| C_DEVELOPMENT | 4 | M4_UNRES_FIRST | 0.002560 | 0.718750 |
| C_DEVELOPMENT | 4 | T3 | 0.002560 | 0.718750 |
| C_DEVELOPMENT | 4 | T1+T2+T3+T4+T5+T6 | 0.002560 | 0.718750 |
| C_HELDOUT | 1 | S0 | 0.093439 | 0.000000 |
| C_HELDOUT | 1 | FULL_GREEDY | 0.046053 | 0.830000 |
| C_HELDOUT | 1 | CANONICAL_ORACLE | 0.078560 | 0.830000 |
| C_HELDOUT | 1 | M4_ORIGINAL | 0.029327 | 0.515000 |
| C_HELDOUT | 1 | M4_FN_FIRST | 0.030670 | 0.515000 |
| C_HELDOUT | 1 | M4_FP_FIRST | 0.035619 | 0.515000 |
| C_HELDOUT | 1 | M4_REV_FIRST | 0.029327 | 0.515000 |
| C_HELDOUT | 1 | M4_UNRES_FIRST | 0.033478 | 0.515000 |
| C_HELDOUT | 1 | M4_RANDOM_EXPECTATION | 0.030072 | 0.515000 |
| C_HELDOUT | 1 | T3 | 0.022611 | 0.515000 |
| C_HELDOUT | 1 | T1+T2+T3+T4+T5+T6 | 0.021573 | 0.515000 |
| C_HELDOUT | 2 | S0 | 0.093439 | 0.000000 |
| C_HELDOUT | 2 | FULL_GREEDY | 0.018603 | 1.435000 |
| C_HELDOUT | 2 | CANONICAL_ORACLE | 0.055398 | 1.435000 |
| C_HELDOUT | 2 | M4_ORIGINAL | 0.003988 | 0.695000 |
| C_HELDOUT | 2 | M4_FN_FIRST | 0.003717 | 0.695000 |
| C_HELDOUT | 2 | M4_FP_FIRST | 0.006841 | 0.695000 |
| C_HELDOUT | 2 | M4_REV_FIRST | 0.003988 | 0.695000 |
| C_HELDOUT | 2 | M4_UNRES_FIRST | 0.004639 | 0.695000 |
| C_HELDOUT | 2 | M4_RANDOM_EXPECTATION | 0.006994 | 0.695000 |
| C_HELDOUT | 2 | T3 | 0.002790 | 0.695000 |
| C_HELDOUT | 2 | T1+T2+T3+T4+T5+T6 | 0.003717 | 0.695000 |
| C_HELDOUT | 3 | S0 | 0.093439 | 0.000000 |
| C_HELDOUT | 3 | FULL_GREEDY | 0.008167 | 1.790000 |
| C_HELDOUT | 3 | CANONICAL_ORACLE | 0.041039 | 1.790000 |
| C_HELDOUT | 3 | M4_ORIGINAL | 0.001435 | 0.760000 |
| C_HELDOUT | 3 | M4_FN_FIRST | 0.001435 | 0.760000 |
| C_HELDOUT | 3 | M4_FP_FIRST | 0.001435 | 0.760000 |
| C_HELDOUT | 3 | M4_REV_FIRST | 0.001435 | 0.760000 |
| C_HELDOUT | 3 | M4_UNRES_FIRST | 0.001435 | 0.760000 |
| C_HELDOUT | 3 | T3 | 0.001299 | 0.760000 |
| C_HELDOUT | 3 | T1+T2+T3+T4+T5+T6 | 0.001299 | 0.760000 |
| C_HELDOUT | 4 | S0 | 0.093439 | 0.000000 |
| C_HELDOUT | 4 | FULL_GREEDY | 0.000964 | 2.005000 |
| C_HELDOUT | 4 | CANONICAL_ORACLE | 0.018932 | 2.005000 |
| C_HELDOUT | 4 | M4_ORIGINAL | 0.001435 | 0.780000 |
| C_HELDOUT | 4 | M4_FN_FIRST | 0.001299 | 0.780000 |
| C_HELDOUT | 4 | M4_FP_FIRST | 0.001435 | 0.780000 |
| C_HELDOUT | 4 | M4_REV_FIRST | 0.001435 | 0.780000 |
| C_HELDOUT | 4 | M4_UNRES_FIRST | 0.001435 | 0.780000 |
| C_HELDOUT | 4 | T3 | 0.001299 | 0.780000 |
| C_HELDOUT | 4 | T1+T2+T3+T4+T5+T6 | 0.001299 | 0.780000 |

Corrected lookahead evaluated all 63 subsets at B=2. Only one Held-out contrast had a nonzero point estimate:

| Cohort | Lookahead − Greedy | Mean difference | 95% pointwise interval | Better/worse/tie |
|---|---|---:|---:|---:|
| C_HELDOUT | T4+T6_LOOKAHEAD2 - T4+T6_GREEDY2 | -0.002180 | [-0.006540, 0.000000] | 1/0/199 |

This contrast is driven by one changed unit among 200 Held-out SCMs; no broad lookahead advantage is established. Fallback counts are recorded separately for each metric set in the corrected summary JSON and are not hard-coded to zero.

## Individual feasible M4 edits

The following are mean SCM-level regret reductions after each initially feasible M4 edit, grouped by error class and task-structure role. Positive values mean improvement; negative values mean harm. Candidate rows are clustered within SCM before averaging; the bootstrap interval resamples SCMs. Sparse cells should be read cautiously.

| Cohort | Error | Role | Candidate edits | SCMs | Mean regret reduction | 95% SCM-cluster interval |
|---|---|---|---:|---:|---:|---:|
| C_DEVELOPMENT | FN | path_and_backdoor | 1 | 1 | 0.590383 | [0.590383, 0.590383] |
| C_DEVELOPMENT | FN | path | 9 | 9 | 0.277498 | [0.114191, 0.452009] |
| C_DEVELOPMENT | FN | backdoor | 3 | 3 | 0.000000 | [0.000000, 0.000000] |
| C_DEVELOPMENT | FP | other_task_fp | 8 | 7 | 0.060405 | [-0.010090, 0.191305] |
| C_DEVELOPMENT | REV | path | 11 | 11 | 0.165728 | [0.082703, 0.248295] |
| C_DEVELOPMENT | UNRES | path | 8 | 6 | 0.200486 | [0.011717, 0.455112] |
| C_DEVELOPMENT | UNRES | backdoor | 6 | 5 | 0.000000 | [0.000000, 0.000000] |
| C_HELDOUT | FN | path_and_backdoor | 4 | 4 | 0.084697 | [0.000000, 0.254091] |
| C_HELDOUT | FN | path | 43 | 39 | 0.195117 | [0.121275, 0.273851] |
| C_HELDOUT | FN | backdoor | 6 | 6 | 0.072670 | [0.000000, 0.218011] |
| C_HELDOUT | FP | other_task_fp | 20 | 17 | -0.018297 | [-0.089481, 0.049865] |
| C_HELDOUT | REV | path_and_backdoor | 2 | 2 | 0.000000 | [0.000000, 0.000000] |
| C_HELDOUT | REV | path | 18 | 17 | 0.159040 | [0.052577, 0.293581] |
| C_HELDOUT | REV | backdoor | 11 | 11 | -0.002479 | [-0.007436, 0.000000] |
| C_HELDOUT | UNRES | path_and_backdoor | 2 | 2 | 0.000000 | [0.000000, 0.000000] |
| C_HELDOUT | UNRES | path | 39 | 36 | 0.176855 | [0.102870, 0.255535] |
| C_HELDOUT | UNRES | backdoor | 12 | 10 | 0.000000 | [0.000000, 0.000000] |

The number of SCMs with at least two initially legal M4 edits was 11/64 Development and 35/200 Held-out. T1/T2 score every eligible pair in the fixed task-zone universe, whereas realized M4 edits are restricted to the initial reference-relative error candidate pool; metric-gain ranking therefore evaluates how scores rank feasible edits, not all possible graph changes.

## Metric gain versus realized edit value

Per-SCM rankings compare structural score gain with realized one-edit regret gain. Candidate count, per-SCM pairwise rank accuracy, within-SCM Spearman, tied-best hit rate, positive-score/worsened-regret counts are in `tables/correction_v1/corrected_s3_metric_gain_validation.csv`.

| Cohort | Metric | SCMs with ≥2 candidates | Candidate count | Pairwise rank accuracy | Mean within-SCM Spearman* | Best-candidate hit rate | Positive-score/worsened candidates |
|---|---|---:|---:|---:|---:|
| C_DEVELOPMENT | T1 | 11 | 26 | 0.5 | 0.0 | 0.8181818181818182 | 1 |
| C_DEVELOPMENT | T2 | 11 | 26 | 0.7857142857142857 | 0.9665063509461096 | 1.0 | 2 |
| C_DEVELOPMENT | T3 | 11 | 26 | 0.9285714285714286 | 1.0 | 1.0 | 1 |
| C_DEVELOPMENT | T4 | 11 | 26 | 0.9285714285714286 | 1.0 | 1.0 | 1 |
| C_DEVELOPMENT | T5 | 11 | 26 | 0.8571428571428571 | 0.9732050807568877 | 1.0 | 1 |
| C_DEVELOPMENT | T6 | 11 | 26 | 0.21428571428571427 | -0.9999999999999999 | 0.6363636363636364 | 0 |
| C_DEVELOPMENT | M4 | 11 | 26 | 0.6071428571428571 | 0.25 | 0.8181818181818182 |  |
| C_HELDOUT | T1 | 35 | 89 | 0.5182291666666666 | 0.04569532006777814 | 0.8857142857142857 | 3 |
| C_HELDOUT | T2 | 35 | 89 | 0.5052083333333334 | 0.040681563845057514 | 0.9142857142857143 | 4 |
| C_HELDOUT | T3 | 35 | 89 | 0.7213541666666666 | 0.6945705769029127 | 1.0 | 1 |
| C_HELDOUT | T4 | 35 | 89 | 0.90625 | 0.9285714285714286 | 1.0 | 0 |
| C_HELDOUT | T5 | 35 | 89 | 0.8229166666666666 | 0.7088999065674341 | 0.9714285714285714 | 0 |
| C_HELDOUT | T6 | 35 | 89 | 0.30729166666666663 | -0.7708333333333334 | 0.8285714285714286 | 1 |
| C_HELDOUT | M4 | 35 | 89 | 0.4947916666666667 | 0.0036361151007631076 | 0.8285714285714286 |  |

\*Spearman is averaged only over SCMs where both score and utility vary; the table's SCM count is the multi-candidate count, not the Spearman-defined denominator. Hit rate allows ties among best observed candidates. These are descriptive, not out-of-sample ranking validation. Several candidate gains are zero under T1/T4/T6 despite nonzero regret changes; graph-score gain is not decision gain.

## Metric complementarity

A descriptive all-subset marginal contribution table is supplied at `tables/correction_v1/descriptive_metric_marginal_contributions.csv`. It averages the difference in cohort mean regret between each nonempty subset and the same subset with one metric removed, stratified by parent subset size and budget. It has no unit-level bootstrap interval and changes the equal-weight average when a metric is added; it is not a causal marginal effect. Pairwise trajectory identity, full factorial uncertainty, and exhaustive ranking overlap were not completed.

## Not completed

- Deterministic baselines (S0, Full Greedy, Canonical Oracle, and four M4 error-type-first variants) were recomputed from the original cohorts. Exact Random-M4 sequence expectation was computed at B=1 and B=2; it is an expectation over legal choices, not a deterministic trajectory.
- Ex-post best feasible M4 edit and complete two-edit interaction benchmark were not executed.
- Gamma objective sensitivity was not run.
- Holm-adjusted inference was not calculated; intervals are pointwise.
- Research D unit-level extension remains unavailable.

See the separate not-run documents. The corrected S3 Gate is therefore **partial with documented limitations**; it does not authorize or claim an independently confirmed policy winner.

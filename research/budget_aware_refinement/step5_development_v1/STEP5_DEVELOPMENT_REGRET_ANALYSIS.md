# Step 5 Development Regret Analysis

## Analysis contract

This is a descriptive analysis of the 64 admitted development SCMs. For each SCM, the analysis formed `D_i,type = Regret_Global - Regret_TaskFocused`, then averaged FN, FP and REV with equal weight. The independent unit remains the SCM; the three error types are repeated observations within it. No confirmatory test, equivalence claim, or population guarantee is reported. Step 6 was not run.

## SCM-level paired result

| Statistic | Value |
|---|---:|
| Complete SCMs | 64 |
| Mean `D_i` | 0.0146605 |
| Median | 0 |
| Sample SD | 0.0621579 |
| Q1 / Q3 (linear) | 0 / 0 |
| Minimum / maximum | -0.0006981 / 0.4195602 |
| Positive / negative / zero | 6 / 1 / 57 |

Positive values indicate lower regret for Task-Focused under the defined sign convention. The distribution is zero-heavy and the mean is influenced by a few nonzero cases; this is descriptive, not evidence of confirmed superiority.

## Error-type results

| Type | Mean difference | Median | SD | Positive / negative / zero |
|---|---:|---:|---:|---:|
| FN | 0.0058258 | 0 | 0.0434724 | 2 / 1 / 61 |
| FP | 0 | 0 | 0 | 0 / 0 / 64 |
| REV | 0.0381557 | 0 | 0.1717861 | 5 / 0 / 59 |

Global mean regret by type was FN 0.0083625, FP 0.0010743 and REV 0.0406924. Task-Focused mean regret was FN 0.0025367, FP 0.0010743 and REV 0.0025367. FP paired regrets were identical in all 64 SCMs. These type summaries are not independent samples.

## Policy outputs and composition

The policies selected the same action in all 64 SCMs for each error type. Final graphs matched in 46/64 FN (71.9%), 33/64 FP (51.6%), and 38/64 REV (59.4%) pairs. Selected `k` matched in 61/64 FN, 64/64 FP, and 59/64 REV. Thus different final graphs often still corresponded to the same selected action; graph difference alone did not imply a regret difference.

Delta groups had 32 SCMs each: mean `D_i` was 0.0041646 for `+1` and 0.0251563 for `-1`. Template counts were chain 17, fork 5, multiple directed paths 32, and observed common cause 10. The maximum `D_i` was 0.4195602 (proposal 000059; multiple directed paths, 8 nodes, delta -1); its difference came from REV only. The minimum was -0.0006981 (proposal 000210; multiple directed paths, 6 nodes, delta -1).

Subgroup counts are small and uneven, especially fork (n=5). Delta/template contrasts are exploratory descriptions and must not be used to revise the frozen design or initiate selective resampling.

## Limits

- Development cohort only; no independent replication.
- Option B: descriptive estimation, no confirmatory superiority/equivalence claim.
- Zero-heavy paired differences and a small number of nonzero cases limit interpretation of the mean.
- No causal claim about real DAT manufacturing processes follows from this synthetic SCM development cohort.
- Raw observations/equations remain in the dedicated run root; this report does not copy them into the repository.

Machine-readable detail: `STEP5_DEVELOPMENT_ANALYSIS_SUMMARY.json`; per-SCM paired values: `STEP5_DEVELOPMENT_SCM_SUMMARY.csv`.

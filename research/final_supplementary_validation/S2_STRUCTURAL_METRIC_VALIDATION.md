# S2 — Structural metric validation

## Analysis unit and uncertainty

There were 23,760 saved policy-budget graph rows and 1,333 unique `(SCM, structural graph hash)` rows (336 Development; 997 Held-out). Duplicates were checked for identical task, learner input, recommendation, and regret before collapsing. Correlation intervals resample SCM clusters, preserve within-SCM dependence, and are pointwise; graph rows and within-SCM pairs are not independent samples.

## Held-out metric association with regret

| Metric | SCM-balanced Spearman | 95% SCM-cluster interval |
|---|---:|---:|
| directed_f1 | -0.387 | [-0.454, -0.316] |
| directed_shd | +0.333 | [+0.260, +0.403] |
| task_error_rate | +0.710 | [+0.643, +0.768] |
| xy_path | -0.924 | [-0.972, -0.866] |
| abs_signed_total_effect_slope_error | +0.025 | [-0.078, +0.134] |

Task-related error rate and X→Y path presence show stronger association with decision regret than global directed F1/SHD in these stored C graphs. Absolute effect-magnitude error has no clear association (the interval includes zero in both cohorts). This is cohort- and task-specific, not a universal ranking of graph metrics. In same-SCM groups with identical SHD or skeleton F1, regret can still vary materially, showing that aggregate structure scores do not uniquely determine downstream performance.

## Predictive validation

| Feature model | Held-out SCM-balanced MAE | OOS R² | Unique Held-out graphs |
|---|---:|---:|---:|
| B_original | 0.06966 | 0.123 | 200 |
| E_nested | 0.06153 | 0.242 | 200 |
| F_nested | 0.03768 | 0.544 | 200 |

Historical B and E were not nested. This corrected post-hoc comparison refits `B_original`, `E_nested = B_original + task features`, and `F_nested = E_nested + X→Y path` from the same saved graph features with the same Development grouped folds, SCM weighting, alpha candidates, and preprocessing. Results and common-index paired intervals are in `outputs/s2_nested_model_validation.csv` and `outputs/s2_nested_prediction_bootstrap.csv`. No held-out tuning or data generation occurred; historical non-nested B/E results remain separate.

## Zero-regret classification (secondary)

| Feature model | Brier | AUROC | Weighted Average Precision (AP) | Positive-regret graphs / rows |
|---|---:|---:|---:|---:|
| B_GENERAL_STRUCTURE | 0.1138 | 0.856 | 0.481 | 227/997 |
| E_GENERAL_PLUS_TASK | 0.0833 | 0.905 | 0.650 | 227/997 |
| F_STRUCTURE_PLUS_PATH | 0.0224 | 0.961 | 0.941 | 227/997 |

Held-out folds were not used to choose features or alpha; alpha was selected using grouped Development CV. Classification is post-hoc and SCM-balanced. The target is whether stored graph regret exceeds `1e-12`; it is not an independent outcome. The reported PR metric is weighted Average Precision: tied score blocks are processed together. It is not trapezoidal PR-AUC.

## Metric limits

Directed F1, SHD and frozen task-zone supports answer different structural questions. Unresolved edges are not silently treated as directed. SID/AID were not computed because a verified compatible implementation and fixture were unavailable. No claim that one score is a universally optimal structural metric is supported.

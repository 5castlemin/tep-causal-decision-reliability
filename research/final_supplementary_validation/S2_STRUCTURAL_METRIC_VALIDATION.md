# S2 — Structural metric validation

## Analysis unit and uncertainty

There were 23,760 saved policy-budget graph rows and 1,333 unique `(SCM, structural graph hash)` rows (336 Development; 997 Held-out). Duplicates were checked for identical task, learner input, recommendation, and regret before collapsing. Correlation intervals resample SCM clusters, preserve within-SCM dependence, and are pointwise; graph rows and within-SCM pairs are not independent samples.

## Held-out metric association with regret

| Metric | SCM-balanced Spearman | 95% SCM-cluster interval |
|---|---:|---:|
| directed_f1 | -0.387 | [-0.456, -0.315] |
| directed_shd | +0.333 | [+0.262, +0.400] |
| task_error_rate | +0.710 | [+0.644, +0.769] |
| xy_path | -0.924 | [-0.972, -0.865] |
| abs_effect_magnitude_error | +0.025 | [-0.078, +0.132] |

Task-related error rate and X→Y path presence show stronger association with decision regret than global directed F1/SHD in these stored C graphs. Absolute effect-magnitude error has no clear association (the interval includes zero in both cohorts). This is cohort- and task-specific, not a universal ranking of graph metrics. In same-SCM groups with identical SHD or skeleton F1, regret can still vary materially, showing that aggregate structure scores do not uniquely determine downstream performance.

## Predictive validation

| Feature model | Held-out SCM-balanced MAE | OOS R² | Unique Held-out graphs |
|---|---:|---:|---:|
| A_NULL | 0.08802 | -0.000 | 997 |
| B_GENERAL_STRUCTURE | 0.06966 | 0.123 | 997 |
| C_OFF_TASK | 0.08826 | -0.001 | 997 |
| D_TASK_RELATED | 0.05763 | 0.301 | 997 |
| E_GENERAL_PLUS_TASK | 0.06047 | 0.284 | 997 |
| F_STRUCTURE_PLUS_PATH | 0.03749 | 0.548 | 997 |
| G_ORACLE_EFFECT_DIAGNOSTICS | 0.03769 | 0.706 | 997 |

Task-only D has lower Held-out MAE than general-plus-task E (.05763 vs .06047), so task and general features are not simply additive. Adding the X→Y path indicator in F lowers MAE further to .03749. G includes oracle effect diagnostics and is non-deployable; it improves R² but does not improve MAE over F. These regressions predict observed historical regret from saved graph-level features; they do not validate a deployable causal repair policy.

## Zero-regret classification (secondary)

| Feature model | Brier | AUROC | PR-AUC | Positive-regret graphs / rows |
|---|---:|---:|---:|---:|
| B_GENERAL_STRUCTURE | 0.1138 | 0.856 | 0.482 | 227/997 |
| E_GENERAL_PLUS_TASK | 0.0833 | 0.905 | 0.651 | 227/997 |
| F_STRUCTURE_PLUS_PATH | 0.0224 | 0.961 | 0.941 | 227/997 |

Held-out folds were not used to choose features or alpha; alpha was selected using grouped Development CV. Classification is post-hoc and SCM-balanced. The target is whether stored graph regret exceeds `1e-12`; it is not an independent outcome.

## Metric limits

Directed F1, SHD and frozen task-zone supports answer different structural questions. Unresolved edges are not silently treated as directed. SID/AID were not computed because a verified compatible implementation and fixture were unavailable. No claim that one score is a universally optimal structural metric is supported.

# S6-2 — B=1 Policy Comparison

All estimates below are post-hoc replays of the same saved initially feasible M4 candidate table. Regret changes are relative to S0; negative values mean lower regret than S0. Paired contrasts use left minus right; negative favors the left policy.

| Cohort | Policy | Mean regret reduction vs S0 | Mean edit count |
|---|---|---:|---:|
| Development, 80 SCM | Frozen M4 | 0.01763 | 0.600 |
| Development, 80 SCM | Development type-ranked M4 | 0.02159 | 0.600 |
| Development, 80 SCM | T5-guided M4 | 0.02159 | 0.600 |
| Development, 80 SCM | Ex-post single-edit regret oracle | 0.04415 | 0.600 |
| Replication, 160 SCM | Frozen M4 | 0.04765 | 0.606 |
| Replication, 160 SCM | Development type-ranked M4 | 0.04985 | 0.606 |
| Replication, 160 SCM | T5-guided M4 | 0.05631 | 0.606 |
| Replication, 160 SCM | Ex-post single-edit regret oracle | 0.07355 | 0.606 |

| Replication paired contrast, B=1 | Mean left−right | Pointwise 95% SCM bootstrap interval | Better / worse / tie |
|---|---:|---:|---:|
| Type-ranked M4 − Frozen M4 | −0.002204 | [−0.009283, 0.003368] | 1 / 0 / 159 |
| T5-guided M4 − Frozen M4 | −0.008664 | [−0.020484, 0.000005] | 4 / 1 / 155 |
| Type-ranked M4 − T5-guided M4 | +0.006460 | [−0.001180, 0.017319] | 0 / 3 / 157 |
| Frozen M4 − ex-post regret oracle | +0.025910 | [+0.010203, 0.044858] | 1 / 11 / 148 |

The type-ranked policy's observed difference from Frozen M4 is small and uncertain. The T5 point estimate is more favorable but its interval includes zero; the original S4 frozen primary remains unchanged. The ex-post oracle is outcome privileged and not deployable. At B=1, M4 and type-ranked M4 selected the same exact edit on 151/160 replication SCMs (including 63 common no-ops); M4 and T5 did so on 148/160. Agreement is descriptive, not evidence of equivalence.

Source: [`policy_budget_aggregates.csv`](outputs/saved_candidates_v4/policy_budget_aggregates.csv), [`paired_policy_contrasts.csv`](outputs/saved_candidates_v4/paired_policy_contrasts.csv), [`policy_redundancy.csv`](outputs/saved_candidates_v4/policy_redundancy.csv).

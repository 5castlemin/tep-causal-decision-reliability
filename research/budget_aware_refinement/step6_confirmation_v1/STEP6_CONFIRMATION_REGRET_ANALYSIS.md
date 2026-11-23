# Step 6 Confirmation-Namespace Descriptive Regret Analysis

## Estimand and interpretation

For each complete SCM, `D_i,type = Regret_Global,type - Regret_TaskFocused,type`; `D_i` is the equal-weight average of FN, FP, and REV differences. Positive values favor lower Task-Focused regret; negative values favor lower Global regret. SCM is the independent unit. Error types are repeated observations within SCM. This is a held-out descriptive replication under Option B, not a confirmatory superiority/equivalence test.

## SCM-level result

| Statistic | Value |
|---|---:|
| Complete SCMs | 200 / 200 admitted |
| Mean `D_i` | 0.0200725 |
| Median | 0 |
| Sample SD | 0.0824273 |
| Q1 / Q3 (linear) | 0 / 0 |
| Minimum / maximum | -0.1447869 / 0.6097471 |
| Positive / negative / zero | 25 / 8 / 167 |

The mean is positive, but 83.5% of SCM-level values are exactly zero and 33 are nonzero. It is therefore a sparse, heterogeneous descriptive mean, not a broad claim that Task-Focused improves every or most SCMs. Type means are not independent samples.

## Error types and policy regrets

| Type | `D` mean (Global − Task-Focused regret) | Global regret mean | Task-Focused regret mean | Positive / negative / zero `D` |
|---|---:|---:|---:|---:|
| FN | 0.0307732 | 0.0493737 | 0.0186005 | 12 / 2 / 186 |
| FP | 0.0021787 | 0.0108991 | 0.0087204 | 3 / 0 / 197 |
| REV | 0.0272656 | 0.0419844 | 0.0147188 | 17 / 8 / 175 |

The equally weighted averages of the type means are consistent with the SCM-level mean. FP differences are almost always zero. REV has both positive and negative cases; it is not uniformly favorable to either policy.

## Policy output agreement

| Type | Same final graph | Same action | Same selected `k` |
|---|---:|---:|---:|
| FN | 124/200 (62.0%) | 200/200 | 186/200 |
| FP | 91/200 (45.5%) | 200/200 | 197/200 |
| REV | 107/200 (53.5%) | 200/200 | 175/200 |

The policies selected the same action in every paired case, while selected `k` and final graphs sometimes differed. Different final graphs do not by themselves imply a different selected action or a regret difference.

## Delta and template summaries

Delta allocation was balanced: 100 SCMs each. Mean `D_i` was 0.0210997 for `+1` and 0.0190453 for `-1`. Template summaries were:

| Template | n | Mean `D_i` | Positive / negative / zero |
|---|---:|---:|---:|
| Chain / mediation | 49 | 0.0067301 | 3 / 3 / 43 |
| Fork / branch | 28 | 0.0018254 | 2 / 2 / 24 |
| Multiple directed paths | 88 | 0.0338076 | 16 / 2 / 70 |
| Observed common cause | 35 | 0.0188156 | 4 / 1 / 30 |

These are descriptive subgroups, not powered comparisons. The cohort's observed template counts reflect the frozen P proposal distribution conditioned on strict Q-common eligibility; no post hoc reweighting was applied.

## Extreme-value sensitivity (pre-specified)

The largest `D_i` was 0.6097471. Removing it gives mean 0.0171093. Removing the two largest values (0.6097471 and 0.5710779) gives mean 0.0143115. The largest case contributes 15.2% and the two largest together 29.4% of the summed `D_i`. The full-cohort mean remains the reported primary descriptive quantity; these diagnostics do not replace it.

The largest positive cases are concentrated in FN and/or REV. The most negative case was `D_i=-0.1447869` (REV difference -0.4343607); it is retained. Full per-SCM values and top/bottom cases are in `STEP6_CONFIRMATION_ANALYSIS_SUMMARY.json` and `STEP6_CONFIRMATION_SCM_SUMMARY.csv`.

## Limits

- No confirmatory p-value, superiority, equivalence, or industrial benefit claim is made.
- The zero-heavy distribution means subgroup averages can be sensitive to a small number of nonzero cases.
- This synthetic SCM cohort does not validate interventions on real DAT manufacturing processes.
- Step 6 did not authorize any changes to the frozen policy, weights, population, budget, or outcome.

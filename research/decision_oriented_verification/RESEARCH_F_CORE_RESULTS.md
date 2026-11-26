# Research F-Lite core results

## Design and analysis unit

Post-hoc policy evaluation on Research C Development 64 SCM and Held-out 200 SCM, separately. Main policy is `DECISION_WEIGHTED_VERIFICATION`; budget B=4 was fixed before evaluation. Outcome is C's analytic Decision Regret. The confidence intervals below are SCM-level paired percentile bootstrap intervals (10,000 resamples) for comparator minus proposed policy; positive values favor the proposed policy. They are exploratory, pointwise comparisons.

## B=4 results

| Cohort | Policy | Mean regret | Mean queries | Mean edits | Mean remaining errors | Action change |
|---|---|---:|---:|---:|---:|---:|
| Development | S0 | 0.100852 | 0 | 0 | 2.141 | 0.000 |
| Development | Random verification | 0.086433 | 4 | 0.301 | 1.839 | 0.266 |
| Development | Fit-based | 0.006710 | 4 | 1.875 | 0.266 | 0.250 |
| Development | Suspicion-only | 0.006710 | 4 | 1.797 | 0.344 | 0.250 |
| Development | Decision-impact-only | 0.002560 | 4 | 0.422 | 1.719 | 0.266 |
| Development | Decision-weighted | 0.002560 | 4 | 0.422 | 1.719 | 0.266 |
| Development | Oracle-assisted M4 | 0.002560 | — | 0.422 | 1.719 | 0.266 |
| Development | Graph-free association | 0.029390 | 0 | 0 | n/a | 0.266 |
| Held-out | S0 | 0.093439 | 0 | 0 | 2.170 | 0.000 |
| Held-out | Random verification | 0.081223 | 4 | 0.305 | 1.865 | 0.270 |
| Held-out | Fit-based | 0.003770 | 4 | 1.905 | 0.265 | 0.250 |
| Held-out | Suspicion-only | 0.006061 | 4 | 1.885 | 0.285 | 0.245 |
| Held-out | Decision-impact-only | 0.017270 | 4 | 0.425 | 1.745 | 0.190 |
| Held-out | Decision-weighted | 0.016281 | 4 | 0.450 | 1.720 | 0.200 |
| Held-out | Oracle-assisted M4 | 0.001435 | — | 0.780 | 1.390 | 0.265 |
| Held-out | Graph-free association | 0.038725 | 0 | 0 | n/a | 0.320 |

Source: `outputs/c_development_aggregate.csv`, `outputs/c_heldout_aggregate.csv`; exact detail remains in the private unit-level artifact audit. Graph-free `remaining errors` is not a repair quantity and is intentionally n/a here.

## Held-out B=4 paired contrasts

| Comparator − Decision-weighted | Mean difference | 95% paired CI | Comparator better / proposed better / tie |
|---|---:|---:|---:|
| Random | +0.064942 | [0.045436, 0.086207] | 7 / 48 / 145 |
| Fit-based | −0.012511 | [−0.023669, −0.003856] | 10 / 0 / 190 |
| Suspicion-only | −0.010220 | [−0.019854, −0.002602] | 9 / 0 / 191 |
| Decision-impact-only | +0.000988 | [0, 0.002881] | 0 / 2 / 198 |
| Oracle M4 | −0.014846 (aggregate difference) | not in saved primary contrast set | see aggregate; non-blind reference-assisted |

Interpretation: the combined heuristic is better than random on this reused cohort, substantially worse than fit-based and suspicion-only on Held-out, and nearly indistinguishable from decision-impact-only for most SCMs. This is not evidence that multiplying the two scores adds value. Development shows extensive ties and does not establish superiority over simpler policies.

## Cohort contrast

The development and Held-out outcomes differ: decision-weighted equals impact-only at B=4 in Development, but performs worse than fit-based and suspicion-only in Held-out. This is a useful robustness warning, not an independent confirmatory replication. Existing C Held-out outcomes were already known when F was designed.

Development B=4 paired contrasts were: Random minus proposed +0.083874 (95% [0.046167, 0.127312], 18 proposed-better / 0 comparator-better / 46 ties); Fit-based and Suspicion-only each +0.004150 (95% [0, 0.012449], 1 / 0 / 63); Impact-only exactly tied across all 64 SCMs. These are pointwise intervals, not simultaneous confidence intervals.

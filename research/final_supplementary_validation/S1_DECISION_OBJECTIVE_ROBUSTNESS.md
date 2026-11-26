# S1 — Decision-objective robustness

## Design

Post-hoc re-analysis of Research C only. It changes the target-tracking objective by adding `gamma × k²` to squared standardized target loss, with `gamma ∈ {0,.05,.2,.5,1}`, and varies the training-derived target by `delta ∈ {-.25,+.25}` SD. Action grid and per-SCM scale are held fixed. This is a robustness analysis, not a new confirmatory test; gamma is a dimensionless preference penalty, not measured operating cost.

## Primary condition

Original target, `gamma=.2`, `B=2`; intervals are paired SCM percentile-bootstrap pointwise 95% intervals (10,000 common-index resamples). Table entries are `Regret(A)-Regret(B)`, so negative favors the first named policy.

| Cohort | Contrast | Mean difference | 95% interval | Better / worse / tie |
|---|---|---:|---:|---:|
| C_DEVELOPMENT | FullGreedy-S0 | -0.00797 | [-0.02294, +0.00296] | 3/1/60 |
| C_DEVELOPMENT | M4-FullGreedy | -0.00849 | [-0.02191, +0.00235] | 4/2/58 |
| C_DEVELOPMENT | M4-S0 | -0.01646 | [-0.03567, -0.00052] | 6/2/56 |
| C_HELDOUT | FullGreedy-S0 | -0.01188 | [-0.02066, -0.00428] | 11/2/187 |
| C_HELDOUT | M4-FullGreedy | -0.01883 | [-0.02919, -0.00936] | 17/1/182 |
| C_HELDOUT | M4-S0 | -0.03071 | [-0.04404, -0.01885] | 27/2/171 |

Held-out, the primary direction remains favorable to Full Greedy versus S0 (difference −.01188) and M4 versus Full Greedy (−.01883). Development point estimates have the same direction, but the Full Greedy–S0 and M4–Full Greedy intervals include zero. M4–S0 is negative in both cohorts. These exploratory intervals do not alter the frozen Research C primary or M4's Development-selected secondary status.

## Objective support

Held-out analytic-GT optimum category by original target:

| gamma | endpoint | zero action | nonzero interior |
|---:|---:|---:|---:|
| 0 | 100.0% | 0.0% | 0.0% |
| 0.05 | 93.0% | 2.0% | 5.0% |
| 0.2 | 58.5% | 9.0% | 32.5% |
| 0.5 | 0.0% | 26.5% | 73.5% |
| 1 | 0.0% | 68.5% | 31.5% |

At gamma 0, all SCMs select endpoints, reproducing the boundary-action limitation. Positive penalty creates interior and zero-action optima, but does not do so uniformly: at gamma .2, 9% choose zero and 32.5% choose nonzero interior; at gamma .5, 73.5% choose nonzero interior and 26.5% choose zero. Under target offsets ±.25 and gamma .2, most Held-out optima are zero. Thus the robustness check broadens objective support in some conditions while preserving strong target dependence.

## Mechanism diagnostics

At gamma .2/B2, Held-out total-effect sign accuracy is .725 for S0, .870 for Full Greedy, .970 for M4, .955 for M2+M4, and .970 for Adaptive M4. Mean absolute magnitude errors are .1823, .1758, .1685, and .1704 respectively for S0, Full Greedy, M4, and M2+M4. Sign accuracy is a post-hoc diagnostic and zero effects form a separate category. It is not a causal mediation analysis.

See `outputs/s1_aggregate.csv`, `outputs/s1_primary_contrasts.csv`, and `outputs/s1_optimum_distribution.csv`.

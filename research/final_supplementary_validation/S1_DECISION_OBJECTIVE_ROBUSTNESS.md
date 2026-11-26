# S1 — Decision-objective robustness

## Design

Post-hoc re-analysis of Research C only. It changes the target-tracking objective by adding `gamma × k²` to squared standardized target loss, with `gamma ∈ {0,.05,.2,.5,1}`, and varies the training-derived target by `delta ∈ {-.25,+.25}` SD. Action grid and per-SCM scale are held fixed. This is a robustness analysis, not a new confirmatory test; gamma is a dimensionless preference penalty, not measured operating cost.

## Primary condition

Original target, `gamma=.2`, `B=2`; intervals are paired SCM percentile-bootstrap pointwise 95% intervals (10,000 common-index resamples). Table entries are `Regret(A)-Regret(B)`, so negative favors the first named policy.

| Cohort | Contrast | Mean difference | 95% interval | Better / worse / tie |
|---|---|---:|---:|---:|
| C_DEVELOPMENT | FullGreedy-S0 | -0.01133 | [-0.02796, +0.00218] | 5/2/57 |
| C_DEVELOPMENT | M4-FullGreedy | -0.00513 | [-0.01674, +0.00291] | 2/1/61 |
| C_DEVELOPMENT | M4-S0 | -0.01646 | [-0.03569, -0.00059] | 6/2/56 |
| C_DEVELOPMENT | CanonicalOracle-S0 | -0.00797 | [-0.02294, +0.00296] | 3/1/60 |
| C_DEVELOPMENT | M4-CanonicalOracle | -0.00849 | [-0.02192, +0.00266] | 4/2/58 |
| C_HELDOUT | FullGreedy-S0 | -0.02572 | [-0.03798, -0.01463] | 22/2/176 |
| C_HELDOUT | M4-FullGreedy | -0.00498 | [-0.01077, -0.00038] | 6/1/193 |
| C_HELDOUT | M4-S0 | -0.03071 | [-0.04385, -0.01865] | 27/2/171 |
| C_HELDOUT | CanonicalOracle-S0 | -0.01188 | [-0.02093, -0.00424] | 11/2/187 |
| C_HELDOUT | M4-CanonicalOracle | -0.01883 | [-0.02931, -0.00964] | 17/1/182 |

The corrected Full Greedy contrast uses policy ID `M1+M2+M3+M4`; `CANONICAL_ORACLE` is a distinct structural-only diagnostic. Held-out Full Greedy−S0 is -0.02572 (-0.03798, -0.01463); M4−Full Greedy is -0.00498 (-0.01077, -0.00038). The earlier contrast used Canonical Oracle under the Full Greedy label; the original contract snapshot is retained and this correction is separately versioned. These exploratory intervals do not alter the frozen Research C primary or M4's Development-selected secondary status.

## Objective support

Original target, Held-out mean regret at B=2:

| gamma | S0 | Full Greedy | M4 | M2+M4 |
|---:|---:|---:|---:|---:|
| 0 | 0.09343898 | 0.01860262 | 0.00398775 | 0.01267397 |
| 0.05 | 0.10301599 | 0.04686117 | 0.03476873 | 0.04043910 |
| 0.2 | 0.11795863 | 0.09223511 | 0.08725290 | 0.09031225 |
| 0.5 | 0.08546025 | 0.08216346 | 0.08359752 | 0.08359752 |
| 1 | 0.02836961 | 0.02836961 | 0.02836961 | 0.02836961 |

The named Full Greedy column is policy `M1+M2+M3+M4`; Canonical Oracle is a different diagnostic policy.

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

At gamma .2/B2, corrected Held-out total-effect sign accuracy is S0 0.725, Full Greedy 0.945, M4 0.970, M2+M4 0.955, and Adaptive M4 0.970. The stored `abs_effect_magnitude_error` is `abs(estimated_slope - true_slope)`, an absolute signed-total-effect slope error, not `abs(abs(estimated_slope)-abs(true_slope))`; numeric values are preserved under this corrected label. Sign accuracy keeps zero effects separate. The unit table contains slope but not intercept estimates, and per-action predictions were not saved, so intercept-error and oracle intercept/slope substitution diagnostics could not be run.

For Full Greedy, sign was correct but the canonical grid action was wrong in 171/200 Held-out SCMs; only 2/65 nonzero-interior-optimum SCMs had the canonical action match. The reference-graph learner's mean absolute signed slope error was .16799 (Held-out) and .15283 (Development); its optimum-action agreement was 99% at gamma=0 and 11% at gamma=.2 in Held-out. Intercept error cannot be computed because intercept values were not saved. Multiple-optimum agreement is not separately available in the local optimum artifact; these rates use the saved canonical optimum action.

See `outputs/s1_corrected_primary_contrasts.csv`, `outputs/s1_corrected_objective_policy_summary.csv`, `outputs/s1_corrected_effect_diagnostics.csv`, and `outputs/s1_optimum_distribution.csv`. The earlier `s1_primary_contrasts.csv` is retained as a historical, superseded output.

# Research E Final Extension — Saved-Result Budget Analysis

Classification: post-hoc decision-economic analysis. Source commit for the preserved S4/S5 results: `0c9236d7f8981d879d1fd47b517ef5dc0c19a7b1`. Analysis script and fixed input digests are recorded in `RESEARCH_E_EXTENSION_EXECUTION_LOCK.json` and `outputs/final_extension_v1/execution_manifest.json`.

## Scope actually completed

The extension re-aggregated 16,560 saved unit-policy-budget rows: S4 Development (80 SCMs), S4 independently seeded replication (160 SCMs), and S5 (200 G0 corruption draws conditional on one DRF DGP). It created no SCM, G0, observation, DRF fit, or intervention response. S4 regret and S5 bias-corrected tracking loss remain in separate scales and cohorts. The original Research E C Development/Held-out extension through B=9 remains available in the pre-existing artifacts and is cited separately; the new S4/S5 saved rows cover B=0–4 only. B=5–9 for S4 and S5 were not generated or inferred in this closeout.

## Selected results

| Cohort / unit | Policy and budget | Mean loss | Mean edits | Interpretation |
|---|---|---:|---:|---|
| S4 Development, 80 SCM | S0, any B | 0.050777 | 0 | Baseline |
| S4 Development, 80 SCM | M4, B=2 | 0.009218 | 0.888 | Lower regret than S0 in this cohort |
| S4 Development, 80 SCM | M4, B=4 | 0.003325 | 1.050 | Observed saved endpoint |
| S4 Development, 80 SCM | Full Greedy, B=4 | 0.003325 | 2.225 | Same displayed mean, more edits |
| S4 Replication, 160 SCM | S0, any B | 0.086462 | 0 | Baseline |
| S4 Replication, 160 SCM | M4, B=2 | 0.020615 | 0.863 | Lower regret than S0 in this cohort |
| S4 Replication, 160 SCM | M4, B=4 | 0.011129 | 0.988 | Observed saved endpoint |
| S4 Replication, 160 SCM | Full Greedy, B=4 | 0.012598 | 2.363 | Higher displayed regret and more edits than M4 |
| S4 Development, 80 SCM | T5-guided M4, B=2 | 0.006627 | 0.888 | Post-hoc selected-metric policy |
| S4 Development, 80 SCM | Full T1–T6, B=2 | 0.003325 | 0.888 | Descriptive; no new confirmatory selection |
| S4 Replication, 160 SCM | T5-guided M4, B=2 | 0.017357 | 0.863 | Post-hoc secondary budget |
| S4 Replication, 160 SCM | Full T1–T6, B=2 | 0.016706 | 0.863 | Descriptive; no new confirmatory selection |
| S5, 200 G0 draws | S0, B=2 | 0.875236 | 0 | Conditional tracking loss |
| S5, 200 G0 draws | M4, B=2 | 0.868384 | 0.295 | Loss reduction 0.006852; uncertainty depends on source |
| S5, 200 G0 draws | Graph-free association, B=2 | 0.867868 | 0 edge edits | Slightly lower mean than M4; model development cost omitted |

The full policy-by-budget values are in `outputs/final_extension_v1/budget_policy_aggregate.csv`. The extension re-aggregates 16,560 nonduplicated saved rows; the duplicate explicit B=1 T5 alias was excluded in favor of the canonical T5 subset record. The existing S4 replication primary remains T5-guided M4 minus Frozen M4 at B=1: mean `−0.0086644`, pointwise 95% SCM bootstrap interval `[−0.020391, 0]` in its frozen report, 4/1/155 better/worse/ties. The rerun descriptive common-resample table is separate and does not replace that record.

## Interpretation

The saved S4 curves show gains at some budget increments and plateaus or reversals at others. For example, Development M4 regret rises from 0.009218 at B=2 to 0.015830 at B=3, then falls to 0.003325 at B=4. This is a cohort mean and does not imply every SCM follows that path. In the S5 saved range, M4 and T5-guided M4 are identical in mean loss and mean edit count from B=1 onward; the S5 report records no first-edit disagreements. There is no evidence here for T5's additional value in this external cohort.

The S5 primary B=2 contrast remains `loss(S0) − loss(M4) = +0.00685175`: its G0-only interval excludes zero, while the action-MC-only and two-source intervals include zero. The new E aggregation's paired bootstrap resamples G0 units against a fixed shared action-loss table; it is not a two-source interval and does not supersede those intervals.

## Limits and stopping

All costs count atomic graph edits only. They exclude model fitting, expert review, validation, risk, time and money. Pareto sets, lambda switches and selected policies are in-sample descriptive optimization. λ is hypothetical loss per edit, not an economic price. Pointwise intervals do not provide simultaneous coverage. The S4 independent replication is specific to its Q-common-admitted strict-indirect SCM population. The S5 units are correlated in origin through a single fitted DGP and fixed training frame, and are not 200 independent SCMs.

S4/S5 B=5–9 extension is `NOT_RUN`: the saved sealed recommendation/evaluation records cover only B=0–4. We did not reuse evaluator outputs as recommendation inputs or extrapolate candidate exhaustion. This is a scope limitation, not a negative result. No S4/S5 lower-budget conclusion is promoted to a new confirmatory claim.

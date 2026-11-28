# S4 Minimal Reconstruction — Development Results

Run: `s4-minimal-development-20261128-v1`  
Execution code revision: `f60f50f0d6f11cc2b8135607e7ddf99a7e19d730`  
Status: completed, post-hoc development evidence

## Generation and information boundary

The locked run admitted 80 SCMs from the existing outcome-blind Q-common strict-indirect proposal population, generated 40,960 observational rows and 80 analysis G0s, and evaluated 11,360 policy-budget rows. It screened 327 proposals and sealed a 367-row recommendation manifest before querying the analytic true-SCM evaluator. No intervention-response rows were sampled. Private unit data, recommendation records and evaluator rows are stored outside Git; the repository contains aggregate outputs only.

This is a reconstructed development cohort, not a recovery of the unavailable other-PC Unified S4 records, not the lost S4-3 confirmation, and not an unconditional sample from the Research C proposal population.

## Repair opportunity

The initial DAG-feasible M4 candidate count was 0 for 32 SCMs, 1 for 25, 2 for 14, 3 for 6, and 4 for 3. The mean was 1.0375 and 23/80 SCMs had at least two candidates. This cohort therefore provides limited evidence about choosing among multiple initial repairs; dynamic candidate changes after edits remain part of the private unit records.

## Paired contrasts

Contrasts use a common SCM bootstrap index array within this report (10,000 percentile replicates). Negative differences favor the left policy. These are pointwise, exploratory intervals.

| Contrast | Mean difference | 95% interval | Left better / worse / tie |
|---|---:|---:|---:|
| T5-guided M4 − Frozen M4, B=1 | −0.003967 | [−0.010221, 0.000000] | 2 / 0 / 78 |
| Full T1–T6 − Frozen M4, B=1 | −0.003967 | [−0.010221, 0.000000] | 2 / 0 / 78 |
| Frozen M4 − S0, B=2 | −0.041559 | [−0.073662, −0.014576] | 10 / 1 / 69 |
| Full Greedy − S0, B=2 | −0.021311 | [−0.049566, 0.004861] | 7 / 2 / 71 |

T5 and Full T selected the same B=1 graph and action for every development SCM in this cohort. T5 versus M4 differs on only two SCMs, so this development result does not establish a general T5 advantage. B=2 M4 and Full Greedy contrasts against S0 are descriptive, after-development comparisons and do not change any frozen Research C primary result.

## Reproducibility artifacts

Aggregate files are in `outputs/development_v1/`. The private archive is `C:\DAT_RESEARCH\archives\research-s4-s5\s4-development-s4-minimal-development-20261128-v1.zip`, SHA-256 `e661150559f0e94dab658f339a4568bfb1d0e0325bb8716047c7b45aa42da358`. This is a same-device archive; no off-device backup has been completed. Raw private records are not committed.

## Scope not completed by this run

The run does not estimate gamma 0.2/0.5 objectives, matched corruption effects, or direct outside-task edit values. It does not finish the metric-selection analysis by itself. Those are separate post-hoc analyses and must be completed only from eligible stored inputs; absence of a relevant unit-level input is reported as not estimable, never inferred from aggregate tables.

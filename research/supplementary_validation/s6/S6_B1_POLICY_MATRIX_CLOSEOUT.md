# S6 B=1 Policy Matrix Closeout

**Status:** `POST_HOC_RETROSPECTIVE_REAGGREGATION_COMPLETE_WITH_LIMITATIONS`\
**Data:** saved S4 Development (80 SCM) and independent replication (160 SCM) candidate-level artifacts only. No SCM, G0, observations, or intervention responses were generated. Candidate rows are clustered within SCM.\
**Runtime:** approximately 5 seconds for the v6 aggregate replay; no evaluator was called.

## Methods and integrity

The locked candidate/input SHA-256 values were verified before replay. v6 uses the same legal M4 candidate set for every policy, B=1, T-score positivity gate, frozen-M4 fallback, M4 secondary tie-break (including negative M4 gains among tied positive T gains), canonical pair/operation ordering, and recorded edit counts. Random-M4 is an exact expectation over legal candidate choices. The ex-post single-edit oracle uses realized regret and is a privileged diagnostic, not an implementable policy. The first v5 replay was superseded because its secondary tie-break incorrectly applied a positivity gate; v5 is retained as superseded and is not analyzed as a result.

The six stored Frozen M4, Type-ranked M4, and T5 cohort summaries exactly match the earlier v4 saved replay within 1e-12 (observed maximum absolute difference 0). Thus existing S6 Frozen M4 and T5 replay results are preserved.

## B=1 outcomes

Mean regret is reported both as the absolute cohort mean and as reduction from S0. In replication, mean absolute regret was .038817 for Frozen M4, .036613 for Development-selected Type-ranked M4, .030152 for T5, .031391 for Full T, and .012907 for the ex-post oracle. Their mean regret reductions from S0 were .047645, .049849, .056310, .055071, and .073555 respectively. Mean edit count was .60625 for every ordinary policy; the ex-post oracle averaged .20 because it can choose no edit when no candidate has positive realized benefit.

| Replication comparison vs Frozen M4 | Mean paired regret difference (left − M4) | SCM bootstrap 95% pointwise interval | Better / worse / tie | Holm-adjusted paired-t p |
|---|---:|---:|---:|---:|
| FN-first | +.001197 | [−.009156, .012490] | 3 / 3 / 154 | 1.000 |
| FP-first | +.005023 | [−.007580, .018430] | 2 / 4 / 154 | 1.000 |
| REV-first | .000000 | [.000000, .000000] | 0 / 0 / 160 | 1.000 |
| UNRES-first | −.002099 | [−.009206, .002908] | 1 / 1 / 158 | 1.000 |
| Development type-ranked | −.002204 | [−.009283, .003545] | 2 / 1 / 157 | 1.000 |
| T1 | +.003190 | [−.012291, .019173] | 5 / 6 / 149 | 1.000 |
| T2 | −.003888 | [−.010157, .000000] | 2 / 0 / 158 | 1.000 |
| T3 | −.004538 | [−.014100, .004836] | 3 / 1 / 156 | 1.000 |
| T4 | −.005045 | [−.016400, .004836] | 3 / 1 / 156 | 1.000 |
| T5 | −.008664 | [−.020398, .000000] | 4 / 1 / 155 | 1.000 |
| T6 | +.003030 | [.000000, .009089] | 0 / 1 / 159 | 1.000 |
| Full T1–T6 | −.007426 | [−.019693, .002789] | 4 / 1 / 155 | 1.000 |
| Random-M4 expectation | −.001246 | [−.012022, .009838] | 9 / 8 / 143 | 1.000 |
| Ex-post single-edit oracle | −.025910 | [−.044657, −.010495] | 10 / 0 / 150 | .054 |

Intervals are 10,000-replicate SCM-level paired bootstrap percentile intervals, pointwise, using common resampling indices across contrasts. Holm adjustment covers the 14 replication comparisons against Frozen M4; paired-t p-values are descriptive under the usual independent-SCM and approximately normal paired-difference assumptions. The oracle unadjusted paired-t p=.00384 is not significant after Holm (adjusted p=.0537). No ordinary structural policy establishes superiority after this multiplicity procedure. The many exact ties mean absence of significance is not equivalence.

## Incremental feature check

A fixed-alpha, deterministic five-fold SCM-grouped Ridge diagnostic used the 83 candidate rows in the 48 Development SCMs that had eligible candidates. SCM-balanced MAE was .11963 for Model A (M4 gain, candidate count, operation indicators), .11977 after adding error type (Model B), and .12487 after adding T1–T6 gains (Model C). These small, post-hoc predictive diagnostics do not show incremental predictive improvement from the added features; they are not policy-effect estimates and do not justify broad generalization. No replication data were used for feature selection or tuning.

## Interpretation

Candidate-level T scores change selected edits and some sample means, but replication intervals are wide relative to observed differences, with 143–159 of 160 SCMs tied for most comparisons. T5 has the most favorable non-oracle point estimate among these policies in this cohort, but superiority is not established. The development-selected type ranking also does not establish an independent benefit. The ex-post benchmark’s apparent advantage is outcome privileged. These results are post-hoc and conditional on saved S4 cohorts and their candidate availability.

Machine-readable tables: [`outputs/saved_candidates_v6/policy_aggregates.csv`](outputs/saved_candidates_v6/policy_aggregates.csv), [`paired_vs_frozen_m4.csv`](outputs/saved_candidates_v6/paired_vs_frozen_m4.csv), [`nested_grouped_ridge_cv_development.csv`](outputs/saved_candidates_v6/nested_grouped_ridge_cv_development.csv), and [`execution_manifest.json`](outputs/saved_candidates_v6/execution_manifest.json).

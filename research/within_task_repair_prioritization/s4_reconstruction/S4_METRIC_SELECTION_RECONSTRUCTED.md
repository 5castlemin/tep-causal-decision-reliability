# S4-M Metric Selection Reconstruction

This is a retrospective SCM-clustered ranking diagnostic on saved initial DAG-legal M4 candidate rows. It is not a new cohort, not the unavailable other-PC development run, and not confirmatory evidence. Candidate rows are nested within SCM; only SCMs with at least two saved initial candidates enter candidate-choice summaries. Results do not represent all possible edits or dynamic candidate states.

| Cohort | SCMs | Multi-candidate SCMs | T5 selected gain (95% cluster bootstrap interval) | Mean ex-post gap | Strict best hit | Pairwise ranking accuracy |
|---|---:|---:|---:|---:|---:|---:|
| Historical pilot | 64 | 38 | .08185 [.01380, .16186] | .04157 | .921 | .769 |
| Reconstructed development | 80 | 23 | −.00157 [−.08507, .08418] | .07846 | .913 | .558 |
| New replication | 160 | 41 | .09052 [.01280, .17532] | .06730 | .829 | .676 |

The development T5-selected edit had negative mean observed regret gain despite a high strict-hit rate; that combination reflects a highly tied/zero-mass outcome and the strict-best definition. It cautions against interpreting a hit rate alone as utility. T3 had stronger within-SCM ranking association in development (Spearman .829 versus .101 for T5), while in confirmation T3+T4 had higher selected gain (.09766) and ranking measures than T5. These are outcome-informed retrospective comparisons among 63 combinations; the best-performing subset is selected on the same data and is optimistic.

The corrected selector applies T-score per edit cost first, then M4 gain per cost within a floating-point tolerance of 1e−12, then canonical pair/operation order. When all T gains fail the positive threshold it falls back to M4; fallback frequency is retained per policy. The analysis computes 189 cohort-by-subset aggregate rows with 10,000 SCM resamples; private SCM-level rows are not published. Full aggregate output and input digests are in `outputs/metric_selection_v1/`.

Conclusion: candidate-level actual repair value varies within SCM, but these saved candidate cohorts do not identify a universally best task metric. T5 remains a replication candidate selected in earlier development history, not an established optimal ranking rule.

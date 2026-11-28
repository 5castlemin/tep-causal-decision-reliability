# Analysis lock and chronology

This file is an audit record, not a preregistration. The first S3 exploratory run occurred before source code, all tie/fallback rules and an immutable analysis revision had been committed. This timing cannot be repaired retrospectively. Accordingly every S3 policy comparison and interval is exploratory/post-hoc; none is confirmatory.

The subsequent scope was expanded uniformly to all 63 one-step metric subsets (B=1–4) and a fixed set of 13 two-step lookahead subsets (B=2) chosen from the user-specified priority order, without selecting based on favorable outcomes.

Bootstrap: 10,000 SCM-cluster paired resamples, cohort-specific, fixed seeds 2026112701 (policy contrasts) and 2026112702 (candidate-role summaries). Intervals are pointwise percentile intervals and are not simultaneous. There is no new independent cohort. Holm-adjusted inference was not calculated; multiplicity is handled by explicitly exploratory interpretation rather than significance claims.

Inputs, definitions, code and aggregate output hashes are recorded in `RESEARCH_S3_INTEGRITY_AUDIT.md`.
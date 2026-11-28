# Research S3 — Within-task causal graph repair prioritization

**Classification:** post-hoc exploratory extension.
**Gate:** `S3_GREEDY_AND_LOOKAHEAD_COMPLETED_WITH_LIMITATIONS`.

## Question
Among reference-defined M4 task-zone errors, do structural metrics distinguish which single repair or short repair sequence improves the frozen Research C decision task? This is a retrospective analysis of the already observed Development (64 SCM) and Held-out (200 SCM) cohorts. It is not confirmatory and does not change Research C.

## Frozen inputs
The four original SQLite files matched the prior verified SHA-256 values; exact values and recheck method are in `RESEARCH_S3_INTEGRITY_AUDIT.md`. Deterministic restoration reproduced the stored truth, observation, task and initial graph bindings. No new SCM, G0, independently drawn observations or interventions were generated. Original observations were reconstructed in memory for learner evaluation and discarded.

## Scope actually executed
- 63 nonempty equal-weight combinations of T1–T6; B=1–4; 264 original SCMs.
- Individual feasible M4 edit diagnostic and SCM-cluster bootstrap summaries by error type/structural role.
- 13 two-step lookahead combinations at B=2: six singleton metrics, all six metrics, and six prelisted metric pairs.
- Common-index 10,000-resample paired intervals for the specified principal comparisons.

## Deviations and status
The first exploratory calculation happened before the analysis code/definitions were committed. All S3 estimates therefore remain post-hoc even though later code was hash-recorded. Only 13 of 63 possible lookahead combinations were executed. Exhaustive two-edit interaction classification, full 63-combination lookahead, all metric-gain ranking diagnostics, gamma objective sensitivity, and final full D reanalysis were not completed. Research D raw unit-level materials were unavailable in the designated store; no replacement samples were made. Details are in `RESEARCH_S3_FINAL_REPORT_KO.md`.

Definitions and scoring rules are in `RESEARCH_S3_METRIC_DEFINITIONS.md`; policy procedure in `RESEARCH_S3_POLICY_CATALOG.md`.
# S3 completion and proposed S4

This directory records a post-hoc completion analysis of the existing Research C cohorts and a design-only proposal for a future independent S4 study. No new SCM, G0, observational sample, or intervention response was generated.

## Public and private artifacts

- `tables/completion_v3/` contains aggregate-only outputs. They do not contain SCM identifiers or unit-level records.
- `outputs_v13/` and `outputs_completion_v1/` are local, ignored private intermediate outputs. They must not be committed or redistributed.
- `run_s3_completion.py` deterministically reconstructs existing Research C inputs and asserts their source digests; it is not a new-cohort generator.
- `finalize_saved_s3.py` aggregates already saved private output. The v3 tables are the publication-facing summaries.

The analysis is post-hoc and exploratory. It does not change Research C's frozen primary or upgrade S3 to confirmatory evidence. S4 is proposed only; it was not run.

# Corrected S3 results — versioned reanalysis

The historical first-run report remains available but is superseded for implementation-specific S3 values by `RESEARCH_S3_CORRECTION_AUDIT.md` and `RESEARCH_S3_DEEP_ANALYSIS_RESULTS.md`. Corrected summary gate: `S3_CORRECTION_RECOMPUTED_WITH_LIMITATIONS`. It is still post-hoc exploratory.

## Paired baselines

M4 minus exact Random-M4 sequence expectation:

| Cohort | Mean difference | 95% pointwise SCM bootstrap | Better/worse/tie |
|---|---:|---:|---:|
| C_DEVELOPMENT | -0.001068 | [-0.019703, 0.019316] | 5/2/57 |
| C_HELDOUT | -0.000745 | [-0.010052, 0.008663] | 7/9/184 |

All 63 metric subsets and 63 lookahead subsets were recomputed. The corrected run also recomputed frozen baselines, error-type-first strategies, and exact uniform Random-M4 expectations at B=1 and B=2. Baseline and opportunity summaries are included in the corrected tables. The corrected artifact directory is `tables/correction_v1/`. No public table contains SCM-keyed rows. The S3 result remains exploratory and does not establish a policy winner.

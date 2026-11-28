# S6-1 — M4 Single-Edit Value by Error Type

Analysis uses saved one-edit M4 candidate records; candidate edits are nested within SCMs and are not independent observations. Positive values mean the saved single repair reduced regret; negative values mean it increased regret. SCM-balanced means first average candidates within an SCM and then average supported SCMs.

| Cohort | Type | Candidate edits | SCM support | SCM-balanced mean reduction | SCM-clustered pointwise 95% interval |
|---|---|---:|---:|---:|---:|
| Development, 80 SCM | FN | 29 | 23 | 0.04243 | [0.00000, 0.10767] |
| Development, 80 SCM | FP | 17 | 15 | −0.04568 | [−0.12778, 0.00457] |
| Development, 80 SCM | REV | 12 | 11 | 0.07417 | [0.00000, 0.18927] |
| Development, 80 SCM | UNRES | 25 | 21 | 0.02772 | [−0.02489, 0.09016] |
| Replication, 160 SCM | FN | 47 | 41 | 0.08915 | [0.03491, 0.15449] |
| Replication, 160 SCM | FP | 29 | 24 | −0.03782 | [−0.10056, 0.00297] |
| Replication, 160 SCM | REV | 40 | 39 | 0.11401 | [0.04119, 0.19209] |
| Replication, 160 SCM | UNRES | 42 | 34 | 0.04956 | [0.00027, 0.10336] |

REV had the largest point estimate in both cohorts; FP had a negative point estimate. These are descriptive associations among the saved legal M4 edits, not randomized error-type effects. Within-SCM type contrasts have sparse overlap: only 4–10 SCMs support each paired type comparison in the replication cohort. Their intervals are wide and pointwise. An absent error type, an infeasible edit, and a legal edit with zero observed value are distinct cases.

Source: [`error_type_summary.csv`](outputs/saved_candidates_v4/error_type_summary.csv), [`within_scm_type_contrasts.csv`](outputs/saved_candidates_v4/within_scm_type_contrasts.csv); raw SCM-level data remain private.

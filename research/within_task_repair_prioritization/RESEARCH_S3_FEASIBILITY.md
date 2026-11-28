# S3 feasibility

The source SQLite hashes matched the previously audited values before and after analysis. The existing R/C proposal and original cohort ledgers were opened read-only. Deterministic restoration matched the stored truth/observation/task/G0 bindings and replayed S0, M4 and Full Greedy B=0–4 graph hashes/edit logs; B=0 and B=2 action/regret checks also matched.

| Cohort | n | At least 1 legal M4 candidate | At least 2 legal M4 candidates | T3 first edit differs from M4 among comparable eligible SCMs | Six-metric first edit differs |
|---|---:|---:|---:|---:|---:|
| Development | 64 | 31 | 11 | 4/31 | 3/31 |
| Held-out | 200 | 103 | 35 | 16/103 | 15/103 |

Both opportunity thresholds were met. Counts are operational feasibility evidence, not power calculations. First-edit differences establish that new structural rankings can select differently, not that they generalize or improve performance. S3 is retrospective because Held-out results had already been seen.

Research D’s aggregate audit is available, but no G0-level recommendations or response vectors were found in the designated local store. D extensions were not run.
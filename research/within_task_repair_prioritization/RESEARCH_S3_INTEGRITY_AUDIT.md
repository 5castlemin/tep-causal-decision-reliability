# S3 integrity audit

## Sources

| File | SHA-256 |
|---|---|
| Development cohort DB | `dd4264d5085adbabe9510bf99b564ec6c2b33e35d4eeb346a079cc4ccfb9b716` |
| Development proposal DB | `1d00d1790788c342e15a81a0c405768e5e2a3e46ee75c57c0bbe34f8c0fcb584` |
| Held-out cohort DB | `37b3c265ecb65b09a97eda91d29411844c3a3851c9fbff6cfa06445f919a3eba` |
| Held-out proposal DB | `59f1abcf5661a5b3d0658d0db0f7e6afe601ebd09997035228df0716800538d6` |

All four hashes matched before and after analysis. Databases were opened with SQLite read-only URI and `query_only=ON`. Deterministic truth/observation reconstruction matched stored input bindings and initial graph hash; S0/M4/Full Greedy B0–4 graph/edit replay matched, with B0/B2 action and regret checked against stored evaluations. No source SQLite writes occurred.

The runtime reconstructed 264 original observation matrices in memory to restore bindings and calculate existing-task learner predictions, then discarded them. No new SCM/G0 cohort or independently seeded observation/intervention sample was generated. Publicly committed tables contain cohort-level aggregates only; no SCM IDs, row-level outcomes or private source data.

The S3 implementation was not committed before first exploratory computation, so the output is not reproducible under a prospectively frozen S3 execution revision. All results are explicitly post-hoc. Current S3 run time was about 68 seconds for calculation after import; no process-tree memory profiler was active, so memory is not verified. CI cannot access private source DBs or reproduce the local analysis.
# E-2 — Input provenance and exact restoration audit

## Original source files

| Cohort | Source | SHA-256 | SQLite integrity | Rows |
|---|---|---|---|---:|
| C Development | original cohort DB | `dd4264d5085adbabe9510bf99b564ec6c2b33e35d4eeb346a079cc4ccfb9b716` | `ok`, all completed | 64 |
| C Development | proposal-stage DB | `1d00d1790788c342e15a81a0c405768e5e2a3e46ee75c57c0bbe34f8c0fcb584` | read-only source | 64 admitted matches |
| C Held-out | original cohort DB | `37b3c265ecb65b09a97eda91d29411844c3a3851c9fbff6cfa06445f919a3eba` | `ok`, all completed | 200 |
| C Held-out | proposal-stage DB | `59f1abcf5661a5b3d0658d0db0f7e6afe601ebd09997035228df0716800538d6` | read-only source | 200 admitted matches |

No WAL or SHM sidecar was present at the inspected source locations. Cohort and proposal databases were opened via SQLite `mode=ro` with `query_only=ON`. No source database was modified.

## Exact reconstruction

The original accepted proposal row and fixed cohort/master seed were matched by SCM ID. Existing deterministic SCM parameter and observation generators were invoked in memory only. For each of 264 SCMs the restored truth-spec digest, 512-row numeric observation digest, task action/target and initial structural graph hash matched its original Ledger binding. The complete B0–4 outcome replay then matched each original graph hash, edit log (canonical JSON comparison), recommended action and analytic regret for all 22,440 SCM×policy×budget rows.

This was a hash-identical restoration of already admitted SCM inputs. It did not add a cohort member, draw another seed, or produce a new independent SCM. The 512-row matrices were not written to public files. The standalone extension runner calls deterministic source generators and public pure repair/learner/evaluator functions; it does not call or bypass the guarded approved Research C cohort runner or its internal execution capability.

## Research D availability

The local D final audit record hash is `6fa458199ea814a61248a1088bbe5a3b96a586916516c02a1dd6b54c0331292b`. It passed its 27 recorded checks and includes 85 aggregate policy-budget rows, five action summary rows, response-vector hash strings and independent-analysis outcomes, but no response vectors or per-G0 recommendation records. A targeted search of the designated local Research D store found no `.npy`, `.npz`, `.parquet`, `.csv`, `.sqlite` or `.db` evaluation artifact outside runtime/venv directories. The raw D records were not regenerated or substituted. D extensions requiring paired G0-level outcomes were not run.

This availability search is limited to the named local Research D store; it does not claim the raw artifacts do not exist elsewhere.

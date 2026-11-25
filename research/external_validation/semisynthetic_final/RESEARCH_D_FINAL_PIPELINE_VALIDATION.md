# Research D final pipeline validation

**Final gate:** `EXTERNAL_FINAL_EVALUATION_VERIFIED`
**Execution source revision:** `a6d751e3f157fca63a93931d62b9f7a9318c6cb5` (tree `fa1aaf635518e6d7a1f292f410185d220ccacc99`)
**Run:** `rd-external-final-20261125-01`

## Contract and source binding

The final run lock bound the exact pinned causalAssembly source and sample/reference hashes, Station1 graph and node order, fixed 512-row learner frame, task/actions/target/scale, 200 G0 IDs, all 17 policies and five budgets, evaluator row counts, bootstrap contract, runtime fingerprint, code byte hashes, and output location before evaluation. The recommendation manifest was content-hash locked before the evaluator was invoked. All 17,000 recommendations were replay-checked against the unchanged policy engine; task-zone and off-task edit counts were added from that deterministic replay.

The recommendation worker received the observational training frame and graph/task inputs. It did not receive the fitted DRF or intervention response data. The evaluator ran as a separate process, re-fit the pinned DGP, verified the locked recommendations, and sampled only the five fixed actions. This is process separation and input separation, not an OS sandbox.

## Preflight and execution

- Exact external sample, reference and source commit checks passed; causalAssembly imported from the pinned source worktree.
- Fixed training CSV raw SHA-256 `dfc77931debb528db05defaf8302198048a04337d2d20a95ab51e5b1685a7094` and numeric SHA-256 `bcca5e56b01dd8cc59d227272906fcee6f9160897e9be2179bd9751619b4bc39` passed. No new training rows were generated.
- Runtime matched Python `3.11.15`, NumPy `2.2.6`, pandas `2.3.1`, NetworkX `3.4.2`, R `4.5.3`, R `drf` `1.3.1`, rpy2 `3.6.2`, and causalAssembly `1.2.1`.
- DRF fit diagnostic matched `11f3a13511bfcf405c8ab167aced154a01fd068711a1fee06fca89e6362856f1` over 16 rows. This diagnostic is not proof that the full fitted generator is identical.
- Final G0 IDs were `703001–703200`; the scanned prior-record set showed zero seed collisions.
- Recommendation rows: 17000; action response rows: 12500; sampling parallelism: 1; evaluator sampling time: 238.182 s.
- All vectors were finite, schema-checked, exact hard-do values were applied, and each vector was saved once outside the repository with a SHA-256. No prior response rows were reused.

## Errors and environment notes

An initial dry-run attempt lacked `R_LIBS_USER` and stopped before sampling; no final rows were created. Repeating the preflight with the already documented isolated `R-library` path passed. Windows printed pre-existing `sh`, ABI-mode fallback, and locale warnings; the pinned R fit and sampler completed with exit code 0 and the expected diagnostic.

The local default Python full-suite attempt used incompatible NumPy/pandas/NetworkX versions and also surfaced the already documented Windows CRLF raw-ledger hash mismatch. No frozen file or validation rule was changed. GitHub Actions on the pushed immutable source revision passed the full suite: **399 tests, 398 passed, 1 skipped**, plus all repository validators.

## Hash record

- Run lock: `8cc953098352ae8ff97ffc6618cd5353ee6565a9d8300b3143b0b45d08acdda2`
- Recommendations raw bytes: `20453dc69698ce21fb7aa0d32eac242301bc816486540e13ca677a6df63cc738`
- Execution manifest: `9ae374e873d6dec68a0ad7bd396506483c6c447a42053a9bce97a5cbb5fd8eed`
- Evaluation response manifest: `136c5d97bfad66ecf3e95f0afd1023d730df33841ab6997f6ec18c4b0f50291f`
- Independent analysis: `2cdb1e3585c95cc3d373d4113017ca2f84c46e4003d62a0ba25439d3c0346e1a`
- Separate artifact audit: `09b6c54710b49005fb49fb2ca26792be07443a4d0b8762ad9cf8a8de71096be3`

Raw run lock, recommendation rows, learner frame, fitted object and response vectors remain in the ignored external data area; they are not in Git.

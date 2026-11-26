# Research F-Lite execution and audit log

## Core F-2

- Actual scientific runner commit: `9155b8c63b64548a88b2c1f5f98032288dbbafed`; tree: `a7d25dfd5df045129e6d73568bcb242ab6f23ad6`; see `execution_lock.json`.
- Source cohort/proposal database hashes are bound in that lock and independently rechecked before use.
- A pre-lock Development technical smoke queried one SCM four times, did not call the evaluator, and persisted no artifact.
- First full attempt built 64 Development recommendations then failed before evaluation because Graph-free selection reused an old policy view. No output was produced for that attempt. Correction: commit `9155b8c`; the same inputs and seeds were then used.
- Successful core evaluation completed both cohorts and saved locked recommendation/evaluator files. Its terminal summary failed after the cohort artifacts were written because a local variable shadowed the run-lock object. Later correction was summary-only; the scientific execution source remains the lock-bound commit above.
- Read-only audit found 12,480 Development and 39,000 Held-out recommendations, and the same number of evaluator rows. Query-score replay confirmed all 4,224 selected queries were the score maximum under the deterministic tie-break.
- The stored query-score replay artifact has SHA-256 `e624e3ca365e37155455062b7c323769fc939b3c875bddf09e3e6ff243e6bd92`; it remains local-only.

## Optional expert-noise F-3

- Initial code commit: `7d3c782`; technical import-path error occurred before `main()` and generated zero research samples.
- Corrected runner commit: `9b8b0f8`; original lock: `noise_sensitivity_lock.json`.
- Development attempt persisted 8,192 recommendations and 8,192 evaluator trajectories. It then failed in summary aggregation because the evaluator history schema had no `correct` field. No file was overwritten; the output pair was hash-checked and reused read-only.
- Recovery runner commit: `68afbd0`; continuation lock: `noise_sensitivity_recovery_lock.json`. Development aggregation reconstructs correctness by comparing saved answer pairs with the restored truth and does not resample Development. Held-out uses the original locked accuracy/repeat/pair seed derivation.
- Both technical failures and the recovered Development run are retained; neither is hidden as a clean first-pass execution.

## Resource measurement

The core and F-3 scripts run as a local Python process without child workers. F-3 polls process RSS and wall time after each SCM and has locked caps of 4 GiB and 7,200 seconds. This is process RSS, not a kernel job-object measurement of an arbitrary process tree. Do not claim a stronger system-wide memory guarantee. Historical attempts without a contemporaneous measurement are not assigned invented resource figures.

## Data and interpretation boundary

Original C SQLite files and per-SCM data remain outside Git. Public cohort aggregates and hash summaries are derived from the locked evaluation artifacts. Results are conditional on the reused C SCM cohorts and the C regret contract; they are not a newly sampled confirmatory study.

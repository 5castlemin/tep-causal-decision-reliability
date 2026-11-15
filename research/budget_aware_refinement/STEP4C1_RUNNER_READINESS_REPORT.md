# Step 4C-1 Runner Readiness Report

## Decision

**IN_PROGRESS; not production-ready.** The integration mock is restart-safe and process-isolated. Production SCM generation and GT evaluation are absent, so this is not a production study runner and cannot satisfy Step 4C-1 DONE or Step 4 freeze.

## Restart defect and repair

The former integration pipeline retained graph edges and the fitted model only in closure memory, while the ledger skipped completed stages. A fresh process therefore resumed at Fit without graph state or at Recommend without a model. The replacement stages restore verified JSON outputs from the ledger. The fitted model is JSON-compatible; recommendation uses that persisted model and fixed fixture input. Tests terminate a real runner process after Graph, Fit, and Recommend checkpoints, resume in a fresh process, and compare the final ledger SHA-256 with uninterrupted execution. All three comparisons pass.

This is deterministic mock recomputation/restoration, not a new SCM draw.

## Integrity and result validation

Each event is canonicalized and hashed; output payloads have their own digest. Recovery rejects a complete tampered event and removes only an incomplete final line. A run ID is bound to RNG key, config SHA-256, and input SHA-256. Stage order, duplicate stages, and terminal placement are checked. Regret aggregation accepts finite signed values including zero; NaN, infinities, strings, overflowed differences, failed policies, or any missing FN/FP/REV value produce an incomplete result, never zero imputation.

## Isolation and resource behavior

Stages can run in a spawned child process. Unit timeout terminates then kills the child if needed; abnormal exit and stage exceptions are separately recorded. RSS sampling includes process working set on Windows and resident pages on Linux, including native allocations. RSS enforcement is sampled, kill-on-observation with possible overshoot, not a strict OS memory limit. Total wall time is checked at stage boundaries, not preemptively. Ledger writes are fsynced and bounded before append; a terminal record is reserved where possible. These implementation differences and limitations remain a freeze gate for production operation.

## Implemented scope

Mock-validated: Graph→existing Ridge fit→recommendation→truth test double; deterministic restart; event/output integrity; resource failure fixtures; composite result validation.

Not implemented: production proposal/stratum and Q-common runner, cohort ID allocator, SCM coefficient/noise/observation generation, production GT evaluation, study-scale checkpoint scheduling, or end-to-end resource enforcement. The truth test double explicitly returns `evaluation_performed=false`, `effect=null`, and `regret=null`.

## Research contract

Active terms are recorded in `STEP4_CURRENT_ACTIVE_CONTRACT.md`: P|Q-common, indirect-only, B=1, gamma=1, Global vs Task-Focused, FN/FP/REV equal weights, SCM-level mean paired difference, dev target 64, replication target 200, attempt caps 362/1,036, Option B (estimate and sensitivity reporting; no confirmatory superiority claim). Step 4 remains IN_PROGRESS / NOT FROZEN.

Historical P/B4 protocol and preregistration text are superseded proposals, retained as history. No Step 5 or confirmation SCM work was performed.

## Verification

Local Python 3.14 targeted runner suite: 19 tests passed after remediation. Full local discovery: 225 tests, 224 passed; one existing exact-float failure in `test_diverse_structure_pilot.test_actual_saved_experiment`. `scripts/check_research_state.py`, `scripts/check_research_docs.py --base origin/main`, and `git diff --check` pass. Windows `scripts/check_asset_manifest.py` fails on its config hash under this checkout; it is not reported as a pass. No frozen graph asset paths changed. The previous HEAD's Python 3.11 Actions passed; a new HEAD requires its own CI run before that result applies.

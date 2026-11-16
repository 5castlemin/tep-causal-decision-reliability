# Step 4C-2 Final Freeze Audit — IN_PROGRESS / NOT FROZEN

Date: 2026-11-16. This is an implementation/readiness audit using deterministic fixed fixtures only. No development or replication cohort, study SCM, or research Decision Regret experiment was generated.

## Active contract

`STEP4_CURRENT_ACTIVE_CONTRACT.md` remains the current authority: P conditioned on strict Q-common; indirect-only; B=1, gamma=1; Task-Focused vs ID-ordered Global; FN/FP/REV equally weighted within SCM; SCM is the independent unit; delta alternates by admitted ordinal separately per cohort; targets are 64/200 admissions with proposal caps 386/1,104; Option B descriptive estimation with no confirmatory superiority claim. Historical P/B4 proposals, structural feasibility matrices, and fixed-fixture software tests are not study results.

## P0 fixes and evidence

### Proposal-generation errors

The cohort orchestrator now accepts only explicit structural rejection reasons. Expected task-generation and Q-common rejection reasons retain their separate proposal-failure or structural-rejection categories. An unexpected exception, malformed record, unrecognized rejection reason, or replay binding mismatch is persisted as `GENERATOR_ERROR` (or a failed row with the same fatal prefix for an already-admitted proposal) and halts the cohort at that proposal. Restart re-raises the persisted fatal error instead of advancing to another proposal. This does not alter the Q eligibility rule or the proposal denominator; it prevents software faults from entering the structural-yield denominator.

Regression coverage includes `IndexError`, `KeyError`, `RuntimeError`, malformed records, unknown rejection reason, and invalid admitted-proposal replay. The strict task builder's fallback reason was aligned to `no_indirect_only_task`.

### Cohort storage accounting

`max_ledger_bytes` remains an individual JSONL bound (default 100 MiB). The optional `CohortStorageMonitor` separately totals every non-symlink file below an explicitly dedicated cohort root, including SQLite database/WAL, ledgers, checkpoints and other run artifacts; it checks filesystem free space before writes, reserves space for a failure terminal event, and re-evaluates usage on restart. A storage contract is included in the cohort settings hash. Attempts to put the registry or ledger outside the managed root fail before execution.

The monitor is opt-in and is exercised with small-cap fixtures, including a normal `DISK_CAP` terminal record. Its SQLite write preflight uses a 16 KiB reserve. This is a conservative preflight, not an OS-enforced filesystem quota; concurrent external writers and filesystem/SQLite journal growth can overshoot. Therefore no whole-cohort byte cap is frozen from these tests.

## Fixed-fixture resource qualification

Run: `python -m research.budget_aware_refinement.run_step4c2_resource_qualification` under Python 3.11.15 with pinned requirements. The harness reused one deterministic explicit-coefficient/mock-noise fixture at each node count for three repetitions; it ran the production pipeline including shared 512-row input, all three error versions, paired policies, Ridge recommendation, analytic truth evaluation, composite validation, JSONL, and completed-ledger replay. It separately timed SQLite admission plus equation-signature binding. No metric values (including regret) are included in the resource JSON.

| Nodes | Full fixed-fixture path median (s) | p95/max (s) | Resume median (s) | Ledger median/max (bytes) | Registry admission/signature median (s) |
|---:|---:|---:|---:|---:|---:|
| 6 | 0.1438 | 0.1528 / 0.1528 | 0.0041 | 91,422 / 91,442 | 0.0094 |
| 7 | 0.1695 | 0.1772 / 0.1772 | 0.0050 | 102,233 / 102,237 | 0.0080 |
| 8 | 0.1968 | 0.2011 / 0.2011 | 0.0050 | 113,237 / 113,243 | 0.0078 |
| 9 | 0.2337 | 0.2370 / 0.2370 | 0.0055 | 124,777 / 124,780 | 0.0086 |
| 10 | 0.2776 | 0.3145 / 0.3145 | 0.0062 | 136,392 / 136,394 | 0.0085 |

The v1 resource JSON records per-node fixture topology hashes, run counts, process RSS snapshots, and linear 64/200 extrapolations. It labels `independent_scm_n=0`, `study_cohort_generated=false`, and `decision_regret_analysis=false`. Replays left terminal result hashes and ledger bytes unchanged. Process working-set snapshots were 66,478,080 bytes before and 74,510,336 bytes after the harness. These are not stage-peak measurements or native-memory attribution. The 3-run nearest-rank p95 is descriptive and not a tail bound.

At the largest fixture ledger size, a simple 200-row multiplication is about 27.3 MB before registry, failure/event overhead, or other artifacts. This supports a *candidate* whole-cohort 100 MiB cap with emergency reserve as a testable operating proposal, not a guarantee. The individual-ledger 100 MiB setting and a whole-cohort cap are distinct. No full 64/200 workflow or external disk-pressure test was performed; do not call either limit a frozen production guarantee.

## Freeze decision

Status remains **IN_PROGRESS**. The P0 classification and accounting code is covered by fixed-cap tests, but final freeze is not justified because:

- Linux/Python 3.11 CI and current-HEAD Self-Review remain required after the final commit.
- The cohort-wide storage monitor has no proven bound against SQLite/WAL growth or external concurrent writes; it is not a filesystem quota.
- Resource data consists of three repeated runs per node count on deterministic fixtures; it does not qualify study-scale tails, native peak RSS, failure-log maxima, or cross-platform execution.
- No final immutable code/settings/environment manifest is generated until the exact reviewed commit and runtime are known. Candidate hash scope must include generator, eligibility, SCM, error injection, policy, Ridge/recommendation, GT, failure rules, cohort/registry/runner, statistics/reporting contract, active settings, and pinned environment. Content hashes and commit/tree IDs must be recorded separately to avoid self-reference.
- The historical preregistration contains superseded P/B4 proposals. The active-contract document identifies them as superseded, but final cross-document/version stamping and freeze manifest review remain for Step 4C-2.

Thus Step 4C-2 is **IN_PROGRESS**, Step 4 remains **IN_PROGRESS / NOT FROZEN**, and Step 5 development SCM execution is not ready. No `STEP4_FROZEN_PROTOCOL.md` is created.

## Verification

The resource table is regression-checked against `step4c2_resource_qualification_v1.json`. Python 3.11.15 full unittest discovery passed 257 tests locally; the 28 focused cohort/production tests passed. The normalized production-artifact manifest test passed locally. GitHub Actions run #237 initially failed that single manifest test because `.txt` was missing from the text newline-normalization suffix set; the test and manifest were corrected to normalize UTF-8 text suffixes consistently. The 39 frozen graph asset Git blobs match their expected hashes (39/39); the Windows worktree byte checker reports CRLF-only mismatches for 31 files. `scripts/check_research_state.py`, `scripts/check_research_docs.py --base origin/main`, and `git diff --check` passed. After the normalization correction, the full Python 3.11.15 suite passed again (257 tests). The corrected exact-head Linux CI and Self-Review remain pending; earlier CI runs validate only their cited commits.

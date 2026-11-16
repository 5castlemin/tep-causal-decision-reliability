# Step 4C-1 Cohort Orchestration Readiness

Status: **DONE (fixed-fixture implementation/readiness); Step 4 remains IN_PROGRESS / NOT FROZEN**. Validation uses deterministic proposal records, a SQLite registry, explicit fixed SCM equations/noise, and mock ledger events. No 64/200 SCM cohort, study observations, or Decision Regret experiment was generated.

## Active contract reconciliation

The active target-direction design remains the protocol's balanced `delta ∈ {-1,+1}` allocation. The registry assigns `+1,-1,+1,...` by zero-based admitted-SCM ordinal, independently within each cohort, only after strict Q-common eligibility. A rejection consumes no delta; replay retains the persisted value. All three error types and both policies for one SCM use the same delta. The cohort counts differ by at most one. `run_eligible_proposal` has no default delta, preventing accidental fixed-`+1` production use.

The 64/200 targets count structurally eligible proposals atomically admitted to the registry, not complete analyses. A later SCM/data/policy/GT failure remains in that admitted denominator and is never replaced. Proposal caps 386/1,104 count every topology proposal, including rejected candidates. They are finite operating limits, not yield guarantees. Counts separately report proposals, strict-Q admissions, registered SCMs, parameter/data generation (equation signature), complete three-type evaluation, failure/missing vectors and complete composites.

## Registry and recovery implementation

`step4c1_cohort.py` adds a local SQLite registry with `BEGIN IMMEDIATE`, a unique proposal/attempt key, globally unique SCM IDs, cohort-scoped alternating delta, immutable topology/RNG/config/input bindings, unique equation signatures, status transitions, and ledger paths. Same-key/same-input replay is idempotent; a changed binding is rejected. Repeated topology is allowed. Identical equation signatures under a second SCM ID are rejected, while same topology with distinct equations is allowed.

The orchestrator uses deterministic proposal IDs (`<cohort>-proposal-000000`, etc.), attempt zero for each candidate, and the existing uniform 1/20 stratum assignment. It records every rejected candidate and stops when the registry admission target or proposal cap is reached. A later failure does not trigger a replacement proposal. SQLite admission precedes pipeline execution. On restart, pending admissions are regenerated from the same cohort/master seed/proposal ID and resumed with their registered delta. Successful ledger terminal state written before the registry completion update is reconciled from its bound ledger and SCM equation signature. A completed registry row without its ledger, or mismatched hashes/bindings, is a hard integrity error.

An OS process lock serializes one cohort orchestrator; SQLite serializes admission transactions across processes. The lock is automatically released on process termination. A cohort resume does not reset its measured stage-time budget: prior durable stage times are recovered from ledgers and current invocation elapsed time is added to the optional stop check. The report separates durable stage seconds from current invocation wall time. Coordinator overhead from a process killed before it writes a stage record is not durably charged; therefore this is an operational monitor, not a hard end-to-end cohort wall-clock limit. No study-scale cohort time cap is claimed as frozen.

## Fixed-fixture checks

The new tests cover balanced delta and replay, duplicate equation rejection, same-DAG/different-equation admission, immutable binding conflict, two-process same-proposal registration, rejected proposal denominators, target/cap shortfall, post-admission interruption/restart, post-terminal/pre-registry interruption recovery, and preservation of a failed eligible SCM without silent replacement. Existing pipeline tests continue to exercise explicit fixed-equation/noise evaluation and child-process restart; these tests do not constitute study data.

Local verification on Python 3.11.15: cohort registry tests **9 passed**; full `unittest discover` **249 passed**; `scripts/check_research_state.py`, `scripts/check_research_docs.py --base origin/main`, and `git diff --check` passed. GitHub Actions run #227 passed all steps on HEAD `137c021e31d19168a11758eeeeb826cfc7077a84`, including the Linux frozen-asset check and document sync. The Windows `scripts/check_asset_manifest.py` check fails because its seven frozen JSON configs are checked out with CRLF while the recorded hashes match LF-normalized bytes and Git blobs; no frozen graph/config path was modified. A documentation/status update is now being validated on the next HEAD; Self-Review will be posted against that exact HEAD after its CI completes.

## Generator and evaluation contract

The production configuration retains the existing signed linear DAG equations: edge magnitudes Uniform[0.25,0.8], independent fair signs assigned by sorted edge IDs, independent node disturbance SD Uniform[0.8,1.2], independent centered Gaussian disturbances, and one shared 512-row observation matrix. The Gaussian disturbance family prospectively replaces the older Uniform disturbance-family proposal; no outcome/effect-based rejection is introduced. The analytic hard-do evaluator remains separate from the learner and no GT value enters eligibility, error selection, or policy ordering.

## Remaining Step 4C-2 gates

- Run and review the final Python 3.11 GitHub Actions workflow and manifest validation on the resulting HEAD.
- Freeze the precise generator/runner settings and hash scope only after code/document reconciliation in Step 4C-2.
- Qualify study-scale wall time/storage with realistic production load; current resource evidence is fixed-fixture only and RSS remains sampled kill-on-detection.
- Do not generate development or replication cohorts until the Step 4C-2 freeze.

Step 4C-1 implementation can be considered complete after the above repository checks pass; Step 4 remains **IN_PROGRESS / NOT FROZEN**.

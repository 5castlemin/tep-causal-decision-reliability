# Step 4C-1 Production Integration & Final Runner Audit

## Decision

**IN_PROGRESS; not production-ready.** The mock runner's failure recovery, execution binding, cumulative per-SCM active wall time, and process isolation are hardened. Structural proposal and paired Step 3 evaluation interfaces are implemented and fixed-fixture validated. The complete SCM generation and study runner remain unimplemented because `STEP4_SCM_GENERATION_SPEC.md` still leaves coefficient sign assignment, duplicate admission, and numerical eligibility thresholds unresolved. No new SCM, observation, GT effect, Decision Regret, or confirmation sample was generated.

## Failure ledger and restart behavior

Stage outcomes and terminal state are now distinct: only `OK` stages enter `completed_stages`; a failed stage is retained with its failure status. Requery after Ridge failure, GT evaluation failure, graph timeout, sampled RSS termination, disk cap, and wall cap returns the same terminal failure without converting it to success or replaying the failed stage. Complete event/output hashes, stage order, terminal placement, and run bindings are verified. Only an incomplete final JSONL tail is truncated; a complete damaged event is rejected.

The integrated Graph→Fit→Recommend→Truth-stub fixture is interrupted in a child process after checkpoints and resumed in a fresh process. Resumed and uninterrupted final ledgers match. The fitted model and other prerequisite outputs are restored from validated JSON outputs, not hidden process memory.

## Runtime and isolation contract

The mock runner sums active per-stage wall time for one SCM across restarts; process downtime is excluded. Unit timeout applies to a spawned child process. Disk size is checked before writes. RSS is sampled (including native process memory) and the child is terminated after an observed overage, so peak overshoot is possible. The cumulative wall cap is enforced at stage boundaries, not preemptively. There is no cohort-wide cumulative runtime cap. These controls have not been established as production study caps.

Every event binds run ID, SCM ID, cohort, config SHA-256, input SHA-256, and RNG key. Stage restoration is scoped to that complete binding. Reusing an SCM ID across run IDs in a cohort or restarting with changed inputs/config/RNG is rejected. Legacy events without digest/binding fields are not resumable under this contract; no historical ledger is rewritten.

## Structural proposal interface

`step4c1_proposal.py` implements a stable SHA-256 1/20 proposal stratum, topology and role relabeling, indirect-task selection, outcome-blind Q-common eligibility, and type-specific structural error recipes. Rejections retain their proposal denominator and receive no SCM ID. Accepted proposals receive cohort-namespaced IDs and post-eligibility stream keys. The interface deliberately stops before drawing coefficients, noise, or observations. It does not resolve the still-open generation-spec items or constitute the production SCM generator.

## Step 3 policy and truth evaluation interface

`step4c1_evaluation.py` prepares Global and Task-Focused recommendations on the same supplied training data and request, freezes both selections before invoking the separate Step 3 truth evaluator, and validates finite nonnegative regret with explicit roundoff handling. Paired requests must share task, candidate grid, scale, and type schedule. The SCM composite uses the common FN/FP/REV validator and remains missing if any type is incomplete. Tests use a fixed existing fixture/deterministic truth contract only. This is adapter validation, not a new Step 4 SCM evaluation. Truth-stub output is never treated as successful GT evaluation.

## Information and failure boundaries

GT outputs are not passed into policy preparation, task selection, topology eligibility, or error ranking. The three type versions use a shared input identity. Failed/incomplete GT evaluation is not zero-imputed; incomplete FN/FP/REV vectors have no composite. Existing fallback rules remain restricted to eligible Ridge/recommendation failure with valid shared training/truth inputs and common `k=0`; original failure status is preserved. Normal candidate exhaustion and unused budget remain valid outcomes.

## Active contract and superseded proposals

The active contract remains P conditioned on Q-common, indirect-only, B=1, gamma=1, paired Task-Focused vs ID-ordered Global, equal 1/3 type weights, SCM as independent unit, descriptive Option B, development target 64, held-out replication target 200, and candidate caps 362/1,036. Earlier P/B4 confirmatory language remains historical/superseded. Step 4 is IN_PROGRESS / NOT FROZEN.

## Step 4C-2 freeze-input proposal

For a later code/config hash manifest, include at minimum: `step4_topology_generator.py`, `step4_error_injection.py`, `step4b_task_budget.py`, `step4b2_population.py`, `step4_rng.py`, `step4c1_proposal.py`, `step4c1_evaluation.py`, `step4b4_failure_rules.py`, `step4b4_mock_runner.py`, `run_step4b4_mock_pipeline.py`, `policy_engine.py`, `step3_adapter.py`, the relevant Step 3 evaluator modules, `STEP4C1_PRODUCTION_RUNNER_CONTRACT.json`, and `STEP4_CURRENT_ACTIVE_CONTRACT.md`. This is a proposed scope only, not a freeze or hash lock.

## Verification status

Verification must be reported for the exact current HEAD after the final full suite and Python 3.11 Actions complete. Local Python 3.14 results and Windows asset-manifest behavior are not substitutes for those checks. No frozen research asset is intentionally modified; final manifest and diff checks remain required.

The repository dependency list is now pinned to NumPy 2.4.3, pandas 3.0.1 and NetworkX 3.6.1; CI targets Python 3.11. The local Python 3.11 installation is managed and has no project packages, and its isolated venv creation was blocked by the host application-control policy. Exact-head Actions is therefore required to validate the pins on Python 3.11.

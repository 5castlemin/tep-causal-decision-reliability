# Step 4 Current Active Contract

## CURRENT ACTIVE CONTRACT

Status: **NOT FROZEN**. This page is the current authority for Step 4 planning; historical proposals below remain preserved but are not active.

- Population: P conditioned on strict Q-common structural eligibility; selected task has a directed path of length ≥2 and no direct Action→Target edge.
- Budget/cost: B=1, gamma=1.
- Paired policies: Task-Focused vs ID-ordered Global, same graph, candidate set, data, and task.
- Error versions: FN, FP, REV; equal within-SCM weight 1/3.
- Independent unit: independently generated SCM; three error versions are repeated measures.
- Target direction: after strict Q-common structural eligibility and atomic registry admission, assign `delta=+1,-1,+1,...` by accepted SCM ordinal separately within development and confirmation cohorts. This deterministic alternation is outcome/GT-blind, persisted in the registry, and shared by all three error types and both paired policies. Each cohort's +1/-1 counts differ by at most one. Replays retain the original assignment.
- Targets: 64 structurally eligible, registry-admitted development SCMs and 200 structurally eligible, registry-admitted held-out replication SCMs; strict-indirect structural proposal caps 386/1,104. These are operational targets, not executed samples or yield guarantees. Later data/model/GT failures remain among admitted SCMs and are never replaced; completed three-type composite N may therefore be below target.
- Outcome: SCM-level arithmetic mean of the three paired Decision Regret differences.
- Inference: Option B. Report estimates, distributions, and sensitivity analyses; do not claim confirmatory 5% superiority.
- Resource candidates: 1,800 seconds total, 2 seconds/unit, RSS 512 MiB, ledger 100 MiB. Current mock runner can kill isolated timed-out units and monitor sampled RSS; RSS overshoot remains possible. These are not frozen production limits.

## IMPLEMENTED / MOCK-VALIDATED / NOT IMPLEMENTED

Implemented and fixed-fixture-validated: deterministic Graph→Ridge→recommendation→analytic-GT evaluation→SCM composite pipeline; durable event/output hashes; run/config/input/RNG/SCM/cohort binding; failed-stage terminal requery; cumulative active stage wall-time accounting per SCM (downtime excluded); finite-value composite checks; isolated unit timeout; and deterministic resume from durable stage outputs. A structure-only proposal interface implements uniform stratum assignment, topology/task construction, strict Q-common eligibility and error recipes. A SQLite admission registry atomically records all proposals, accepted SCM IDs, balanced delta, immutable configuration/input/RNG bindings, unique equation signatures, and status transitions. The fixed-sequence cohort orchestrator enforces target/cap stopping, counts all denominators, resumes pending admissions, and preserves eligible pipeline failures without replacement. SCM coefficient/noise/512-row observation generation is implemented and deterministic-fixture validated, but was not used to generate a study cohort. The analytic GT evaluator takes truth equations separately from the learner and has hand-calculation tests.

Not implemented or not run: execution against newly sampled study SCMs and study-scale runtime/storage qualification. Numeric rejection is limited to nonfinite values and zero sample variance; no condition-number, effect-size or outcome-based threshold is applied. No study-cohort SCM or Decision Regret experiment was generated. Cohort tests use fixed proposal sequences and deterministic runners; they are not research data. The separate truth stub still returns null outcomes and is not a successful evaluation.

Resource enforcement: spawned child unit timeout is enforced by termination; RSS uses sampled kill-on-detection and can overshoot; JSONL storage is capped before append. The 1,800-second cap accumulates active per-SCM stage wall time across restarts and excludes downtime. Cohort orchestration recovers durable stage seconds from all ledgers and combines them with current-invocation elapsed time for an optional cap; coordinator overhead from an invocation killed before a stage event is written is not persisted. No study-scale cohort cap is frozen. These are fixed-fixture runner behaviors, not frozen production resource limits.

Reproducibility runtime proposal: Python 3.11 and exact dependency pins `numpy==2.4.3`, `pandas==3.0.1`, `networkx==3.6.1`. Local Python 3.11.15 full regression passed (249 tests) on the current working tree; GitHub Actions on the final pushed HEAD remains pending. BLAS/native numerical differences can still affect exact floating-point reproduction.

## SUPERSEDED PROPOSALS

Earlier P/B=4 selected-policy vs matched-random and Path-F1 confirmatory proposals in `RESEARCH_PROTOCOL.md`, `STEP4_PREREGISTRATION.md`, and `STEP4_STATISTICAL_ANALYSIS_PLAN.md` are historical proposals. They are not the active primary question. They remain in place as an audit trail and must not be read as current instructions.

## ARCHIVED PILOTS

Step 4A and Step 4B feasibility matrices and mock ledgers are structural/software pilots only. They are not independent SCMs, confirmation data, or policy-performance evidence.

## Production sequence contract (one-proposal path implemented; cohort generation not run)

Proposal/stratum → topology → Q-common eligibility → assign cohort-scoped SCM ID and independent streams → generate one shared SCM/data input → construct FN/FP/REV versions → paired Global/Task-Focused runs → separate GT evaluator → validate all three paired differences → equal-weight SCM composite → append validated checkpoint/ledger.

GT results must not flow into topology eligibility, task selection, error injection, or policy ordering. A missing type or failed GT evaluation leaves the SCM vector incomplete; no zero imputation or silent complete-case substitution.

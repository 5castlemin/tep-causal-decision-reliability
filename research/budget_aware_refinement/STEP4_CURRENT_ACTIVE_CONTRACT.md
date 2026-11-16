# Step 4 Current Active Contract

## CURRENT ACTIVE CONTRACT

Status: **NOT FROZEN**. This page is the current authority for Step 4 planning; historical proposals below remain preserved but are not active.

- Population: P conditioned on strict Q-common structural eligibility; selected task has a directed path of length ≥2 and no direct Action→Target edge.
- Budget/cost: B=1, gamma=1.
- Paired policies: Task-Focused vs ID-ordered Global, same graph, candidate set, data, and task.
- Error versions: FN, FP, REV; equal within-SCM weight 1/3.
- Independent unit: independently generated SCM; three error versions are repeated measures.
- Targets: 64 eligible development SCM and 200 eligible held-out replication SCM; strict-indirect structural diagnostic candidate caps 386/1,104. These are planning values, not executed samples or yield guarantees.
- Outcome: SCM-level arithmetic mean of the three paired Decision Regret differences.
- Inference: Option B. Report estimates, distributions, and sensitivity analyses; do not claim confirmatory 5% superiority.
- Resource candidates: 1,800 seconds total, 2 seconds/unit, RSS 512 MiB, ledger 100 MiB. Current mock runner can kill isolated timed-out units and monitor sampled RSS; RSS overshoot remains possible. These are not frozen production limits.

## IMPLEMENTED / MOCK-VALIDATED / NOT IMPLEMENTED

Implemented and fixed-fixture-validated: deterministic Graph→Ridge→recommendation→analytic-GT evaluation→SCM composite pipeline; durable event/output hashes; run/config/input/RNG/SCM/cohort binding; failed-stage terminal requery; cumulative active stage wall-time accounting per SCM (downtime excluded); finite-value composite checks; isolated unit timeout; and deterministic resume from durable stage outputs. A structure-only proposal interface implements uniform stratum assignment, topology/task construction, strict Q-common eligibility and error recipes. SCM coefficient/noise/512-row observation generation is implemented and deterministic-fixture validated, but was not used to generate a study cohort. The analytic GT evaluator takes truth equations separately from the learner and has hand-calculation tests.

Not implemented or not run: cohort-level 64/200 orchestration, execution against newly sampled study SCMs, study-scale runtime accounting, and a durable cross-ledger duplicate/admission registry. Numeric rejection is limited to nonfinite values and zero sample variance; no condition-number, effect-size or outcome-based threshold is applied. No study-cohort SCM or Decision Regret experiment was generated. The integrated software test uses explicit fixed equations and noise; it is not research data. The separate truth stub still returns null outcomes and is not a successful evaluation.

Resource enforcement: spawned child unit timeout is enforced by termination; RSS uses sampled kill-on-detection and can overshoot; JSONL storage is capped before append. The 1,800-second cap accumulates active per-SCM stage wall time across restarts and excludes downtime. No cohort-wide elapsed-time cap is configured. These are mock-runner behaviors, not frozen production resource limits.

Reproducibility runtime proposal: Python 3.11 in CI and exact dependency pins `numpy==2.4.3`, `pandas==3.0.1`, `networkx==3.6.1`. The current local fixture runs used these dependency versions under Python 3.14; compatibility and full-suite result on the pinned Python 3.11 runtime remain gated on the new HEAD GitHub Actions run. BLAS/native numerical differences can still affect exact floating-point reproduction.

## SUPERSEDED PROPOSALS

Earlier P/B=4 selected-policy vs matched-random and Path-F1 confirmatory proposals in `RESEARCH_PROTOCOL.md`, `STEP4_PREREGISTRATION.md`, and `STEP4_STATISTICAL_ANALYSIS_PLAN.md` are historical proposals. They are not the active primary question. They remain in place as an audit trail and must not be read as current instructions.

## ARCHIVED PILOTS

Step 4A and Step 4B feasibility matrices and mock ledgers are structural/software pilots only. They are not independent SCMs, confirmation data, or policy-performance evidence.

## Production sequence contract (one-proposal path implemented; cohort generation not run)

Proposal/stratum → topology → Q-common eligibility → assign cohort-scoped SCM ID and independent streams → generate one shared SCM/data input → construct FN/FP/REV versions → paired Global/Task-Focused runs → separate GT evaluator → validate all three paired differences → equal-weight SCM composite → append validated checkpoint/ledger.

GT results must not flow into topology eligibility, task selection, error injection, or policy ordering. A missing type or failed GT evaluation leaves the SCM vector incomplete; no zero imputation or silent complete-case substitution.

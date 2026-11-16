# Step 4 Current Active Contract

## CURRENT ACTIVE CONTRACT

Status: **NOT FROZEN**. This page is the current authority for Step 4 planning; historical proposals below remain preserved but are not active.

- Population: P conditioned on Q-common structural eligibility; task is indirect-only.
- Budget/cost: B=1, gamma=1.
- Paired policies: Task-Focused vs ID-ordered Global, same graph, candidate set, data, and task.
- Error versions: FN, FP, REV; equal within-SCM weight 1/3.
- Independent unit: independently generated SCM; three error versions are repeated measures.
- Targets: 64 eligible development SCM and 200 eligible held-out replication SCM; proposal caps 362/1,036. These are design targets, not executed samples or yield guarantees.
- Outcome: SCM-level arithmetic mean of the three paired Decision Regret differences.
- Inference: Option B. Report estimates, distributions, and sensitivity analyses; do not claim confirmatory 5% superiority.
- Resource candidates: 1,800 seconds total, 2 seconds/unit, RSS 512 MiB, ledger 100 MiB. Current mock runner can kill isolated timed-out units and monitor sampled RSS; RSS overshoot remains possible. These are not frozen production limits.

## IMPLEMENTED / MOCK-VALIDATED / NOT IMPLEMENTED

Implemented and fixture-validated: deterministic mock Graph→Ridge→recommendation→truth-stub flow; durable event/output hashes; run/config/input/RNG/SCM/cohort binding; failed-stage terminal requery; cumulative active stage wall-time accounting per SCM (downtime excluded); finite-value composite checks; isolated unit timeout; and deterministic resume from durable stage outputs. A structure-only proposal interface now implements uniform stratum assignment, topology/task construction, Q-common eligibility and error recipes. A Step 3 paired recommendation/GT-evaluation adapter is validated on fixed fixtures only.

Not implemented: coefficient/noise/observation generation; production SCM construction and duplicate admission; end-to-end study orchestration; production execution against newly generated SCMs; and study-scale cohort runtime accounting. The existing generation spec leaves sign assignment, duplicate definition/admission and numeric eligibility thresholds unresolved. The GT adapter reuses Step 3 code but has only fixed-fixture validation; no real Step 4 SCM evaluation was performed. The truth stub returns `evaluation_performed=false` and null outcomes; it is not a successful evaluation.

Resource enforcement: spawned child unit timeout is enforced by termination; RSS uses sampled kill-on-detection and can overshoot; JSONL storage is capped before append. The 1,800-second cap accumulates active per-SCM stage wall time across restarts and excludes downtime. No cohort-wide elapsed-time cap is configured. These are mock-runner behaviors, not frozen production resource limits.

Reproducibility runtime proposal: Python 3.11 in CI and exact dependency pins `numpy==2.4.3`, `pandas==3.0.1`, `networkx==3.6.1`. The current local fixture runs used these dependency versions under Python 3.14; compatibility and full-suite result on the pinned Python 3.11 runtime remain gated on the new HEAD GitHub Actions run. BLAS/native numerical differences can still affect exact floating-point reproduction.

## SUPERSEDED PROPOSALS

Earlier P/B=4 selected-policy vs matched-random and Path-F1 confirmatory proposals in `RESEARCH_PROTOCOL.md`, `STEP4_PREREGISTRATION.md`, and `STEP4_STATISTICAL_ANALYSIS_PLAN.md` are historical proposals. They are not the active primary question. They remain in place as an audit trail and must not be read as current instructions.

## ARCHIVED PILOTS

Step 4A and Step 4B feasibility matrices and mock ledgers are structural/software pilots only. They are not independent SCMs, confirmation data, or policy-performance evidence.

## Production sequence contract (planned)

Proposal/stratum → topology → Q-common eligibility → assign cohort-scoped SCM ID and independent streams → generate one shared SCM/data input → construct FN/FP/REV versions → paired Global/Task-Focused runs → separate GT evaluator → validate all three paired differences → equal-weight SCM composite → append validated checkpoint/ledger.

GT results must not flow into topology eligibility, task selection, error injection, or policy ordering. A missing type or failed GT evaluation leaves the SCM vector incomplete; no zero imputation or silent complete-case substitution.

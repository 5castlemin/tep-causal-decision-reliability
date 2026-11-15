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

Implemented and fixture-validated: deterministic mock Graph→Ridge→recommendation→truth-stub flow, recoverable event ledger, event/output hashes, run/config/input/RNG binding, finite-value composite checks, process-isolated stage timeout, and deterministic resume from durable stage outputs.

Not implemented: production topology/Q-common proposal runner; independent SCM coefficient/noise/data generation; production GT evaluator; production result analysis and study-scale orchestration. The truth stub returns `evaluation_performed=false` and null outcomes; it is not a successful evaluation.

## SUPERSEDED PROPOSALS

Earlier P/B=4 selected-policy vs matched-random and Path-F1 confirmatory proposals in `RESEARCH_PROTOCOL.md`, `STEP4_PREREGISTRATION.md`, and `STEP4_STATISTICAL_ANALYSIS_PLAN.md` are historical proposals. They are not the active primary question. They remain in place as an audit trail and must not be read as current instructions.

## ARCHIVED PILOTS

Step 4A and Step 4B feasibility matrices and mock ledgers are structural/software pilots only. They are not independent SCMs, confirmation data, or policy-performance evidence.

## Production sequence contract (planned)

Proposal/stratum → topology → Q-common eligibility → assign cohort-scoped SCM ID and independent streams → generate one shared SCM/data input → construct FN/FP/REV versions → paired Global/Task-Focused runs → separate GT evaluator → validate all three paired differences → equal-weight SCM composite → append validated checkpoint/ledger.

GT results must not flow into topology eligibility, task selection, error injection, or policy ordering. A missing type or failed GT evaluation leaves the SCM vector incomplete; no zero imputation or silent complete-case substitution.

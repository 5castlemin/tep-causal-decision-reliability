# Step 4C-1 Final Production Readiness (NOT FROZEN)

Date: 2026-11-16. This report records implementation and fixed-fixture evidence only. No development/replication cohort, newly sampled research SCM, or study Decision Regret experiment was run.

## Active task and strict Q-common definition

The active task is indirect-only: at least one directed Action→Target path of length ≥2 exists, and the direct Action→Target edge is absent. Direct-only and direct-plus-indirect pairs are ineligible. The proposal selector only treats the Observed Common Cause scaffold as preferred when that pair belongs to the disjoint `indirect_only` class. Otherwise it selects from the indirect-only candidate class. Q-common then requires same-type FN, FP, and REV two-correction competition support at B=1. These checks use topology, task, and error structures only.

Fixed counterexamples are tested for (i) X→M→Y only, (ii) X→Y only, and (iii) both paths. The code distinguishes failure to have any indirect path from having a direct edge in addition to an indirect path. Indirect-only topology alone does not guarantee Q-common: all three error-type competition recipes must also exist.

## Strict-indirect yield rerun

The original Step 4B-4 compressed raw output is preserved. The new v2 rerun used the same fixed 2,000 candidate cells, 20 strata, 100 candidates per stratum, master seed 20261115, proposal identifiers, and RNG derivation. Only the task eligibility rule was corrected. No coefficient, observation, intervention, effect, or regret was generated.

- Historical accepted: 637/2,000 (31.85%).
- Strict indirect-only accepted: 595/2,000 (29.75%).
- Changed acceptances: 42, all Observed Common Cause scaffold selections that had a direct edge; strict accepted rows with a direct edge: 0.
- Strict accepted counts: Chain 107, Fork 69, Observed Common Cause 122, Multiple Directed Paths 297.
- Topology generation still has large repetition: 1,929 distinct topology hashes across 2,000 attempts. This is a proposal-yield audit, not 2,000 independent SCMs.
- Under the same conservative stratified lower-yield planning rule, caps are 386 (64 eligible target) and 1,104 (200 target). These do not guarantee attainment; the old 362/1,036 values no longer meet this rule.

Settings SHA-256: `b5fc9bb2f3767d1592aa560626c985eb7c853a4969cba2f5d5e899645564d52b`.

Compressed raw v2 SHA-256: `959078f02df14f54af5915327115bab6d78e1b19f010c285cea2eb0f9de79ae3`.

Artifact: `step4c1_indirect_only_yield_v2.json.gz`; summary: `step4c1_indirect_only_yield_v2_summary.json`. The reported caps are planning estimates from the fixed stratified pilot, not a prospective yield guarantee.

## SCM generation and numerical contract implemented

`step4c1_scm.py` implements an acyclic linear structural equation family using sorted directed edge IDs for coefficient assignment. Each edge magnitude is Uniform[0.25, 0.8] and its sign is a separate fair Bernoulli draw. Node exogenous SDs are Uniform[0.8, 1.2]; exogenous disturbances are independent Gaussian with mean zero. Parameter and observational sample streams are separate. Observations are generated in topological order, with exactly 512 rows, and the same resulting matrix is used for all three error types and both policies.

Numeric rejection currently covers invalid topology, nonfinite parameters/data, and zero sample variance. No arbitrary effect, condition-number, maximum-value, prediction, or regret threshold was added. Small and cancelling effects remain eligible. An exact equation signature distinguishes identical equations from merely repeated DAG topology; the pipeline rejects an equation signature already present in its available ledger under another SCM ID. A durable registry spanning independent ledgers/cohort storage is not implemented and must be part of Step 4C-2 before real cohort generation.

## Analytic GT and one-proposal integration

`step4c1_gt.py` computes exact intervention means by forward substitution and replaces the intervened node equation, thereby cutting incoming edges. The evaluator receives the truth specification only after both learner recommendations have been frozen. Step 4C-1 tests include a hand-computed chain plus direct path, a parent-edge intervention, cancellation to zero, and deterministic repetition.

`step4c1_pipeline.py` connects Proposal → SCM parameter draw → shared observations → error graphs → paired policy graph edits → paired Ridge recommendation → analytic GT evaluation → complete three-type SCM composite. Recommendation code receives task, graph, and observational data, not the truth specification. The pipeline requires FN/FP/REV values to be present and successful before calculating the equal-weight composite. It uses the existing eligible k=0 fallback rule and preserves the original policy failure status. Truth failures are not converted to zero.

The full path was run only against one preselected topology and explicit fixed equation/noise fixture. This is a software test double, not a generated study SCM. The truth-stub runner is not considered analytic evaluation success.

## Remaining gates and limits

- A separate child process was forcibly terminated immediately after the SCM, policy-graph, recommendation, and GT-evaluation checkpoints. Fresh processes resumed each ledger, and the terminal result SHA matched the uninterrupted fixed-fixture run in all four cases. This validates the integrated deterministic test fixture and existing durable stage outputs; it does not validate cohort-scale orchestration.
- Candidate-stage checkpoints are bound to run/SCM/cohort/config/input identities. Cross-ledger equation deduplication and a cohort-wide accepted-ID registry remain incomplete.
- Resource checks are inherited from the mock runner: unit timeout uses child termination; RSS is sampled and killed on detection with possible overshoot; ledger cap is checked before append; total active per-SCM stage wall time excludes downtime. These are not strict OS RSS limits or a cohort-wide wall-clock budget.
- Full Python 3.11 unittest discovery passed locally: 240 tests. Exact frozen-asset verification, Python 3.11 CI on this HEAD, and Self-Review are pending.
- Historical v1–v4 reports remain as evidence of superseded task definitions; the active contract and this report define the strict current task. Historical raw results are not rewritten.

Step 4C-1 remains IN_PROGRESS. Step 4 overall remains IN_PROGRESS / NOT FROZEN. Do not start Step 5 or generate the 64/200 cohorts until Step 4C-2 freezes implementation, settings, duplicate policy, durable resume, and final hash manifests.

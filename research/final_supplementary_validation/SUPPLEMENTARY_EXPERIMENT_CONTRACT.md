# Supplementary Experiment Contract

Status: `SUPPLEMENTARY_CONTRACT_AND_PROVENANCE_VERIFIED` (contract locked before this branch's cohort-level analysis).

Classification: `POST_HOC_SUPPLEMENTARY_DECISION_ROBUSTNESS_AND_METRIC_VALIDATION`. Existing Research C–F results have already been observed; this contract does not create an independent preregistered confirmation.

## Scope and units

Use only the original Research C Development (64 SCM) and Held-out (200 SCM) cohorts and their read-only cohort/proposal SQLite files. The two cohorts remain separate. All uncertainty resampling uses SCM as the unit. No new SCM, G0, observations, DRF fits, interventions, or expert responses are generated. Research D is excluded because its private unit-level response material is unavailable in this analysis checkout.

Reconstruct existing C inputs only through the documented deterministic source functions, and require exact truth-specification and observation digest matches to the original ledger before using them. Do not substitute a seed or alter an input. Preserve the original C–F contracts and outputs.

## S1: decision-objective robustness

Action grid: `K={-1,-0.5,0,0.5,1}`. Existing per-SCM training-derived action mapping, original target and scale are retained for the primary condition. For each action, the objective is `L_gamma(k)=((mu(k)-target)/scale)^2 + gamma*k^2`; the same gamma is applied to learner-predicted and analytic-GT losses. Predictions reselect the action using the existing tie-break `(loss, abs(k), k)`. Regret is selected GT grid loss minus the GT grid minimum; a negative value beyond `1e-12` is an error.

Primary exploratory comparison: original target, `gamma=0.2`, `B=2`, with S0, Canonical Oracle (the stored Full Greedy comparator), M4; report paired `Regret(A)-Regret(B)`. Secondary conditions: original target and `gamma in {0,0.05,0.2,0.5,1.0}`, plus training-derived targets `mean(Y)+delta*SD(Y)` for `delta in {-0.25,+0.25}` and the same gamma grid. Policies: all 17 stored C policies, saved Adaptive M4 trajectories, plus reference-graph and graph-free diagnostic learners. C repair trajectories remain those already saved; F query trajectories are not regenerated.

Classify GT optima as endpoint, zero, nonzero interior, or multi-optimal. Report standardized true/predicted total-effect slopes, sign accuracy (zero is a separate category), absolute magnitude error, action agreement, paired regret contrasts, and edit counts. Do not interpret gamma as measured operating cost or compare raw regret across different objective scales as if commensurate.

Use 10,000 paired SCM bootstrap replicates, common SCM indices for all policy/objective contrasts, fixed seed `2026112601`; intervals are pointwise. Gamma zero on the original target must reproduce stored C actions/regret within the existing `1e-12` regret tolerance before any gamma-positive result is accepted.

## S2: structural metric validation

Primary S2 unit is a unique `(SCM_ID, structural_graph_hash)` from the original C saved B=0–4 results, weighted so each SCM has total weight one. Deduplicate only after checking that duplicate-graph task, learner input, recommendation, and regret agree. Also report initial-G0 cross-sectional results and the secondary `(SCM_ID, learner_graph_hash)` deduplication when available. Keep unresolved adjacency distinct from directed edges.

Metrics: skeleton precision/recall/F1; directed precision/recall/F1; directed SHD with one reversal cost and one mismatch for unresolved versus a known direction; atomic errors under frozen M1–M4 accounting; task-related FN/FP/REV/UNRES counts and rates with frozen supports; X-to-Y directed path; and standardized total-effect sign/magnitude errors. Empty denominators are NA, not zero. M1–M4 scores use the frozen policy-engine definitions; no new weighted “M4 score” is introduced.

Report SCM-clustered Spearman/Kendall associations, same-SCM metric/regret contrasts, and representative cases selected by predeclared deterministic criteria (first SCM key after sorting within each category). Do not count within-SCM graph pairs as independent observations.

Predictive comparison uses Development only for grouped 5-fold CV and regularization selection (`alpha={0.01,0.1,1,10,100}`), with all rows for one SCM in one fold and equal total SCM weight. Fit Model B (general structure) versus Model E (general plus task-related frozen metric features) as the primary contrast, plus fixed Model A–G feature groups as specified in the user-approved request. Evaluate once on the existing Held-out cohort and report SCM-balanced MAE, RMSE, out-of-sample R2, Spearman, and positive-regret AUROC/PR-AUC/Brier where defined. Bootstrap Held-out SCMs 10,000 times with common paired indices. This is post-hoc evaluation on a previously observed held-out cohort, not new confirmation. Effect-error Model G is an oracle-informed diagnostic, not deployable.

SID/AID are not required for the core S2 gate. Run only if an already available, verified implementation and fixtures support the frozen graph conventions; otherwise record `SID_AID_NOT_RUN_WITH_DOCUMENTED_REASON`.

## Failure and integrity rules

Missing or mismatched source binding, incomplete/duplicate cohort keys, gamma-zero mismatch, invalid DAG, incompatible duplicate graph, fold leakage, nonfinite values, or negative regret beyond tolerance stops the affected analysis. Do not change grids, objectives, metrics, policies, exclusions, or bootstrap seed after viewing results. Preserve C–F frozen assets and original ledgers byte-for-byte.

No claim of industrial validation, measured economic savings, universal metric superiority, new confirmatory evidence, or causal effect of structural metric changes is permitted.

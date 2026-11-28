# Final Scientific Integrity Review

## S6/S7 supplementary status (2026-11-28)

S6 reaggregates saved S4 candidate results; it is post-hoc and candidate observations are clustered within SCM. Its B=1 replication comparison of T5-guided M4 with Frozen M4 was −.008664 regret (95% common-index SCM bootstrap CI [−.020398, 0]); Holm-adjusted paired-t p=1.0, so policy superiority is not established. S7 generated no persisted G0 or recommendations (0/400; 0/24,000); no evaluator ran. The run's final supervisor report is missing, so actual cap enforcement and termination/resource reason cannot be verified. Separate task-zone implementation feasibility passed without outcome data; that does not complete S7. See `research/supplementary_validation/s6/S6_B1_POLICY_MATRIX_CLOSEOUT.md` and `research/supplementary_validation/s7/S7_COMPUTATIONAL_CLOSEOUT.md`.

Date: 2026-11-28. Scope: existing published research outputs plus saved S4/S5 unit-level results for post-hoc E budget/cost aggregation. No new study data were generated.

## Evidence separation

- Research C primary remains its frozen-contract confirmatory synthetic evaluation (200 independent held-out SCMs).
- C M4 is a Development-selected secondary policy.
- C mechanism, S1/S2, S3, E and this extension are post-hoc analyses.
- S4 reconstruction: separate 80-SCM development and 160-SCM replication cohorts; the latter is a new replication under the stated Q-common-admitted strict-indirect population, not recovery of the missing other-PC run.
- S5: new conditional external semisynthetic reconstruction; 200 G0 draws conditional on one fitted DGP/training frame, not 200 independent SCMs and not exact Research D reproduction.
- Other-PC Unified S4 and historical S4-3 quantitative reports remain reported-only/unverifiable where their unit records were unavailable.

## Scope and input integrity

The extension script reads these external private unit files without copying them to Git: S4 development `policy_results_private.json` SHA-256 `e899c927ad452394f0c03af03911f77f2c8d332f4891ee24b0c0c88de7040a0f`; S4 confirmation `policy_results_private.json` SHA-256 `a9e9c6109ba0ce75974cd7be120f69cb2deae43bbfa419cc5cc1d7de2c568b0f`; S5 `unit_policy_losses_private.json` SHA-256 `6332af831d25bc487bb3026a3f506ae6a10ab8c58efb55d66f4a6224a53c7242`. These hashes and public output hashes are in [`execution_manifest.json`](research/budget_adaptive_repair/outputs/final_extension_v1/execution_manifest.json). The script and analysis limits are bound by [`RESEARCH_E_EXTENSION_EXECUTION_LOCK.json`](research/budget_adaptive_repair/RESEARCH_E_EXTENSION_EXECUTION_LOCK.json).

16,560 saved unit-policy-budget rows were summarized. The S4 cohorts remain separate. S5 remains separate and uses a G0-only paired bootstrap conditional on the existing common action-loss table; the historical S5 two-source intervals are retained and not replaced. Existing C primary/frozen inputs, historical requirements, and protected status files were not edited. S4/S5 unit rows, recommendations, training data, response vectors, fitted objects, and private archives are excluded from the public commit.

## Interpretation controls

- “Mean actual edit cost” means graph edits only. It does not mean labour time, money, verification effort, safety or total modeling cost.
- B is a maximum allowed budget, not the number of edits necessarily performed.
- Pareto dominance is based on observed cohort means and is not statistical significance.
- λ is hypothetical and lower-envelope choices are in-sample descriptive.
- Percentile intervals in the extension are pointwise. No simultaneous coverage is implied.
- C/S4 regret and S5 standardized tracking loss are not pooled.
- B=5–9 S4/S5 values are not in preserved sealed records; not run and not extrapolated.
- No graph-repair method is claimed to be universally superior to graph-free prediction.
- No real manufacturing treatment effect, deployment readiness, or safety is established.

## Verification status

The existing S4/S5 run integrity manifests and prior remote CI records remain source evidence for those studies. This extension's generated CSVs have SHA-256 entries in its execution manifest. New focused tests cover aggregation separation, marginal edit denominators, and Pareto tie retention. Final status generation, diff check, focused/full suite and remote CI are recorded in the final commit/CI record; any host-specific failure is reported rather than normalized away.

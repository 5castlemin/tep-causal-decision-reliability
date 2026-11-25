# Research D Bounded Development Pilot Results

**Status:** Completed as an authorized Development Pilot. The final external evaluation was not run. All result selection settings were fixed in the run lock before evaluator draws.

## Locked setting

- One Station1 DRF-based external semisynthetic generator, refit from the pinned public 500 × 98 semisynthetic sample and official Station1 reference DAG.
- One 512-row observational learner-training sample shared by all graph seeds, policies, and budgets.
- Task `Station1_mp_0 → Station1_mp_4`, reference path via `Station1_mp_1`; virtual benchmark hard-do only.
- Five pinned-source action quantiles: `0.000155911358968`, `0.0001724093665238`, `0.00018679686613765`, `0.00020263502221978`, `0.00022589388613683002`.
- Training-only target `15.460000542160238`, scale `1.565469292160237`.
- 32 development G0 seeds, 17 policy definitions including Canonical Oracle, budgets 0–4, and 256 evaluator rows for each of five actions.
- Evaluator output: 1,280 total interventional draws, all schema-valid and finite, exact action value in every generated row. No raw generated response frame was saved.

## Primary Development contrast

At B=2, `Δ_D = L_exp(a_S0) − L_exp(a_FullGreedy)`; positive values favor Full Greedy.

| Estimate | Result |
|---|---:|
| Mean paired bias-corrected loss contrast | +0.003338 |
| G0 seeds | 32 |
| G0 conditional SD with fixed evaluator table | 0.010874 |
| G0 seeds where Full Greedy changed the action vs S0 | 6 / 32 |
| Those changed-action cases with lower Full Greedy loss | 6 / 6 |
| Unchanged-action cases | 26 / 32 (same action, same loss) |
| Full Greedy losses worse than S0 | 0 / 32 |

The all-nonnegative pilot deltas do not establish a general guarantee. The primary's two-source uncertainty interval is much wider than the fixed-evaluator G0-only interval:

| Bootstrap view | 95% percentile interval for mean `Δ_D` |
|---|---:|
| G0-only resampling, fixed action loss table | `[0.00059, 0.00737]` |
| Action Monte Carlo resampling, fixed G0 set | `[-0.05854, 0.06344]` |
| Two-source paired G0 + within-action row resampling | `[-0.06532, 0.07547]` |

The two-source interval includes zero and is the relevant pilot indication of precision. This is not a confirmatory p-value or a confidence interval over manufacturing systems or independent SCMs.

## Action-level evaluation summaries

| Action | Evaluator mean `Y` | Sample variance | Bias-corrected target loss |
|---:|---:|---:|---:|
| 0.0001559114 | 13.9258 | 2.5160 | 0.95646 |
| 0.0001724094 | 13.8242 | 2.8905 | 1.08724 |
| 0.0001867969 | 13.9180 | 2.7736 | 0.96586 |
| 0.0002026350 | 14.0352 | 2.2380 | 0.82484 |
| 0.0002258939 | 13.8789 | 2.3578 | 1.01630 |

All five evaluation means were below the training-only target (15.4600). The target remains locked; this observed gap is recorded as a task-feasibility limitation and did not trigger a task or target change. The lowest observed action loss is a noisy finite-sample minimum and is not reported as a definitive best action or used to compute Primary absolute Regret.

## Policy and graph-free diagnostics at B=2

| Policy | Mean corrected loss | Mean unit edit count | Same recommendation as S0 | Different actions vs S0 |
|---|---:|---:|---:|---:|
| S0 | 0.96010 | 0.0000 | 100.0% | 0 / 32 |
| Full Greedy | 0.95676 | 1.1563 | 81.25% | 6 / 32 |
| M4 | 0.95676 | 0.1875 | 81.25% | 6 / 32 |
| Canonical Oracle | 0.95705 | 1.1563 | 84.38% | 5 / 32 |

M4 and Full Greedy recommended exactly the same action for all 32 G0s at B=2, so their observed paired loss contrast was zero despite different average edit costs. The graph-free observational X–Y Ridge association baseline selected action `0.000155911358968` and had corrected loss `0.95646`; it is an association baseline, not a causal estimator. Its comparatively low loss does not validate its causal interpretation.

No absolute empirical regret, final primary analysis, or policy-selection decision was made from these results. All 17 policies and all five budgets remain in `development_pilot_summary.json` and `development_policy_diagnostics.json`.

## Structural Development G0 snapshot

The fixed 32-seed development cohort had 8 no-error G0s and 7 seeds with task-zone error. It generated 49 error proposals; 7 were DAG-rejected without redraw. Accepted errors were FN=11, FP=11, REV=6, UNRES=14. Task-zone errors totaled 7 (FN=4, REV=1, UNRES=2; FP=0); off-task errors totaled 35. M1/M2/M3/M4 had nonzero error support in 7/11/14/7 seeds respectively. No seed was excluded or replaced.

## Interpretation

The pipeline can now run end to end and produces a small positive B=2 average contrast under this one fitted DRF, but evaluator Monte Carlo uncertainty is large enough that the pilot does not determine whether the mean contrast is positive. Only six G0s changed the action under Full Greedy; all 26 remaining pairs tied. M4 was not distinguished from Full Greedy by recommendation in this task at B=2. Before the post-run byte-provenance issue was detected, the pilot appeared technically ready for contract review. Because the current source digest differs from the run lock, all policy aggregates are now exploratory and the pilot is incomplete for final-contract review.


## Provenance status

A post-run source-file terminator formatting error caused the current pipeline.py byte hash to differ from the pre-run digest in development_run_lock.json. Although the executable statements were not changed and the module was repaired, exact run-to-source byte provenance is not intact. Treat all policy aggregates above as exploratory Development Pilot output; Gate G3 is DEVELOPMENT_PILOT_INCOMPLETE until a newly locked, bounded repeat is separately approved and run. No final evaluation data were generated.

# Simulated expert-noise sensitivity

## Status

The sensitivity was predeclared in `noise_sensitivity_lock.json`: response accuracy 0.9 and 0.8, 16 repeats per SCM/accuracy, B=4, and four query policies. It uses existing C Development 64 and Held-out 200 SCMs only. Query noise is deterministic under fixed pair-specific namespaces; no new SCM, G0, observational or intervention data is generated.

The first attempt completed and persisted Development recommendations/evaluator rows (8,192 each), then failed at summary aggregation because the trace schema did not contain a `correct` field. Those files were retained and read-only reaggregated by the recovery runner; no Development resampling was performed. The continuation used the same seed derivation and ran Held-out once. All 33,792 trajectories are present and hash-checked. The saved-output audit replayed query answers through the graph update rule and compared queried answers to their true pair state to classify wrong, pending, applied-wrong, and newly created relation errors. Summary and detailed paired analysis: `noise_sensitivity_summary.json`, `noise_sensitivity_audit.json`.

## Results

Mean regret (within each SCM averaged over 16 repeats; cohorts remain separate):

| Cohort | Accuracy | Random | Suspicion-only | Impact-only | Decision-weighted |
|---|---:|---:|---:|---:|---:|
| Development | 0.9 | .093387 | .020614 | .042868 | .038282 |
| Development | 0.8 | .109357 | .041393 | .062455 | .053501 |
| Held-out | 0.9 | .092546 | .021620 | .039614 | .038087 |
| Held-out | 0.8 | .095624 | .039240 | .065565 | .060056 |

Held-out paired nested SCM/repeat bootstrap, comparator regret minus decision-weighted regret (10,000 resamples; positive favors proposed):

| Accuracy | Comparator | Difference | 95% interval |
|---:|---|---:|---:|
| .9 | Random | +.054459 | [.034844, .075739] |
| .9 | Suspicion-only | −.016467 | [−.027095, −.007539] |
| .9 | Impact-only | +.001526 | [−.000336, .003754] |
| .8 | Random | +.035569 | [.017427, .055158] |
| .8 | Suspicion-only | −.020816 | [−.031251, −.011203] |
| .8 | Impact-only | +.005509 | [.001296, .010694] |

Across both simulated error rates, decision-weighted remains better than random but worse than suspicion-only on Held-out. Its difference from impact-only is small. At lower accuracy, weighted regret rises from .0381 to .0601; suspicion-only rises from .0216 to .0392. The hypothetical noise model therefore does not rescue the combined score's relative standing.

At Held-out accuracy .9, the decision-weighted policy averages .70 graph edits and .383 wrong responses per four-query trajectory; .058 wrong responses were pending when answered, .328 remained wrong in the final queried-pair state, .056 were not present as a final error, and .291 newly incorrect queried pairs remained. At .8 these are 1.020 edits, .828 wrong answers, .109 wrong answers pending at query time, .722 wrong answers reflected in the final queried-pair state, .106 not present as a final error, and .653 newly incorrect pairs. Mean final pending relations are .060 and .113 respectively. These are descriptive quantities conditional on reused SCMs and simulated categorical noise.

## Interpretation rule

Each repeated trajectory remains conditional on its original SCM. The paired bootstrap resamples SCMs and shared repeat IDs jointly, preserving same-repeat pairing across policies. The hypothetical accuracy levels are sensitivity settings, not empirical estimates of expert reliability. A difference here cannot establish performance with real experts or new causal populations.

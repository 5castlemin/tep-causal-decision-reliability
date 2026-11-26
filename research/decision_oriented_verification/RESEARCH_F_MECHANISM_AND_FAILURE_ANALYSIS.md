# Research F-Lite: mechanisms and failure modes

## Main diagnostic

At B=4 the proposed `suspicion × decision impact` heuristic is essentially identical to decision-impact-only in Development, and close to it in Held-out (mean regret 0.016281 versus 0.017270). In Held-out it is worse than fit-based (0.003770) and suspicion-only (0.006061). It therefore does not demonstrate that multiplying the two components improves query allocation.

## Error discovery is not decision value

The fit/suspicion policies discover roughly 1.9 incorrect relations per Held-out SCM at four queries and leave about 0.27–0.29 average residual errors, while decision-weighted discovers 0.45 and leaves 1.72. Yet the latter's regret is 0.0163, below random (0.0812), but above the policies that identify more errors. This shows that raw discovery counts alone are not enough to explain performance, and that the proposed decision weighting did not reliably preserve the intended advantage on Held-out.

## Reference-assisted comparison

Held-out Oracle-assisted M4 reaches 0.001435 mean regret with 0.780 edits; the proposed policy reaches 0.016281 with 0.450 edits. This contrasts a reference-informed repair policy with a reference-blind query policy and is not an equal-information policy contest. Oracle performance is a diagnostic benchmark, not a realizable blind baseline.

## Failure mechanisms and counterexamples

- A queried relation can be correct but unhelpful to the action, consuming query budget without changing the decision.
- A decision-impact score is computed from the current misspecified learner, which may fail to flag a structurally important relation if its own fitted response is misleading.
- Local Gaussian BIC can rank observational fit rather than causal truth; equivalent or weakly identified structures can remain ambiguous.
- Query answers that conflict with the current DAG are pending until compatible changes are possible; finite budget can leave them unapplied.
- In a six-node graph, a small number of queries can miss a broken task path. The proposed heuristic did not match the fit/suspicion baselines on the reused Held-out cohort.
- The graph-free association baseline is itself imperfect but has no verification/edit count; its B=4 Held-out regret is 0.038725.

The saved core audit verifies selection consistency and arithmetic but does not turn these post-hoc results into evidence from newly sampled SCMs.

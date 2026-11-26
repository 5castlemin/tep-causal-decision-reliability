# Research F-Lite critical review

## What this adds

F-Lite changes the operational question from “which known graph error should be repaired?” to “which pair should an expert verify first when the policy cannot see the reference?” It reuses C cohorts to test an interface-level query strategy and makes query count distinct from atomic graph edits.

## What it does not establish

This is post-hoc reuse of the same synthetic SCMs already used for C, not a new external or independent population. The Held-out labels and effects were already observed in prior Research C, and F was designed after C–E results. Simulated expert answers are perfect in the core analysis; optional noise is an artificial scenario, not measured expert reliability. The expert still has access to the reference. The policy's “suspicion” score is not a calibrated probability, and the impact score is model-relative rather than a causal value-of-information estimate.

## Key negative finding

Decision-weighted verification beats random querying on the reused Held-out set, but loses to fit-based and suspicion-only verification at B=4 and is nearly the same as impact-only. This is contrary to a strong claim that the combined heuristic is superior. Its proposed conceptual ingredients may still motivate future work, but the current implementation does not show incremental benefit from their product.

## Methodological limitations

- Interface separation is not operating-system isolation.
- Local BIC imposes a Gaussian score approximation on the observed data.
- Oracle M4 uses reference information and is not an apples-to-apples blind competitor.
- The graph-free association model uses a different modeling route and must remain a diagnostic baseline.
- SCM-level bootstrap intervals condition on the fixed reused cohort; they do not capture new-SCM sampling, expert-population variation, or model-training variation.
- The Development and Held-out cohorts are reported separately; they are not pooled.
- The choice of B=4 and score rule was made in a post-hoc extension after prior results were available.
- Technical attempts and the summary-stage failure are retained in the audit trail; a successful rerun is not retroactively treated as failure-free.

## Overall assessment

The evidence supports feasibility of a reference-blind *interface* and shows that query strategies can differ in this setup. It does not support superiority of the proposed combined score, realistic human-in-the-loop effectiveness, causal identification without a reference, or industrial impact. Research F-Lite is best presented as a negative/qualified exploratory prototype.

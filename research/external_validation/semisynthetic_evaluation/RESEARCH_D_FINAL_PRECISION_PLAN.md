# Research D proposed final precision plan

**Status: proposal only; not executable or approved. The authorized Development reproduction did not reach model fitting or evaluation, so this plan cannot be updated with reproduced pilot diagnostics.**

## Candidate estimand and scope

Retain the proposed primary contrast at B=2, `Δ_D = L_exp(a_S0) − L_exp(a_FullGreedy)`, conditional on one fixed Station1 reference DAG, one refit DRF DGP, one 512-row learner-training sample, and the prespecified G0 corruption distribution. This is not a physical manufacturing population estimand and 200 G0 draws would not be 200 independent SCMs.

## Existing proposal, not newly validated

The prior exploratory pilot used 256 evaluator draws per each of five actions. Its action-Monte-Carlo-only percentile interval was `[-0.058536, 0.063438]`, a half-width of about `0.061`; its two-source interval was `[-0.065322, 0.075465]`. These values belong to the historical exploratory pilot, whose raw evaluator rows were discarded. They were not reproduced here.

A two-sided 95% Monte Carlo-only half-width of `0.02` standardized target-loss units remains a candidate reporting tolerance, not a manufacturing meaningful-effect threshold. First-order `1/sqrt(n)` scaling from the historical action-MC interval suggests about `256 × (0.061/0.02)^2 ≈ 2,380` rows/action; the earlier rounded proposal of 2,500/action is therefore a planning candidate only. It has not been confirmed with a reproduced variance estimate, precision simulation, or resource-cap test.

The prior proposal of 200 final G0 seeds, 512 new training rows, five actions, 2,500 evaluator rows/action, and 10,000 bootstrap replicates remains unapproved. No final seeds, training frames, or evaluation rows were generated.

## Required before a new approval

1. Review the corrected audit-schema gate and decide whether a new single reproduction is authorized; the previous authorization's one invocation ended before any model/data generation and was not retried.
2. If separately authorized, complete one same-seed reproduction with its own run ID and immutable source lock. Only a valid reproduction can replace the historical exploratory values for planning.
3. Use a prespecified simulation based on the reproduced action-level variance and recommendation frequency weights to compare sample counts against the fixed 0.02 tolerance, while keeping G0 and evaluator Monte Carlo uncertainty separate.
4. Set wall-time and memory caps from measured batch performance before any final data generation.
5. Review whether a single fixed generator and the training-only target rule provide a useful benchmark task; do not alter target, task, actions, or Primary based on the historical pilot response means.

No final evaluation samples or seeds are approved or present.

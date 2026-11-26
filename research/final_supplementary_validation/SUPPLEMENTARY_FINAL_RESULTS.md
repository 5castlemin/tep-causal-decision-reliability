# Final supplementary results

Gate: `SUPPLEMENTARY_ANALYSIS_COMPLETED_WITH_LIMITATIONS`.

This is a post-hoc saved-data supplement and does not alter C's frozen primary. At original target, gamma=.2, B=2 Held-out, Full Greedy is `M1+M2+M3+M4` and `CANONICAL_ORACLE` is distinct. Mean regret: S0 .11795863, Full Greedy .09223511, M4 .08725290, M2+M4 .09031225, and reference-graph learner .08635285. The reference learner is a diagnostic with access to the reference DAG, not a deployable oracle. Shared-index paired SCM bootstrap pointwise intervals: Full Greedy−S0 −.02572 [-0.03798, -0.01463]; M4−Full Greedy −.00498 [-0.01077, -0.00038]. Development intervals include zero for both contrasts. At gamma=.5 Full Greedy regret .08216346 is below M4 .08359752; at gamma=1 the four repair policies all select `k=0` in 200/200 saved units. Objective dependence means M4 is not uniformly best.

`EMPTY_DAG_LEARNER` is the blank graph passed to the existing SCM learner; it is not Research F's observational association baseline. Saved F association results at gamma zero are .02939 Development/.03873 Held-out, and were not evaluated on the supplementary objective grid. S2 nested held-out MAE is .06966 (B_original), .06153 (E_nested), .03768 (F_nested); paired pointwise SCM bootstrap B−E is .00813 [0.00209, 0.01390] and E−F is .02386 [.01674,.03116].

No new data were generated. Research D is excluded for lack of private unit-level artifacts. This supplement does not supersede Research C's frozen primary, change Research D's interpretation, or establish operational benefit.

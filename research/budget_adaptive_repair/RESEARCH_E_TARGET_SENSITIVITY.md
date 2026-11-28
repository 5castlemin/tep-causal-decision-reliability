# Target sensitivity — fixed action grid, varied training target

This post-hoc analysis keeps each original C SCM's five training-derived action values and scale, while evaluating target rules `mean(Y_train)+delta×SD(Y_train)` for delta `−1, −0.5, 0, 0.5, 1`. Policies are S0, M4, M2+M4, Full Greedy and Adaptive M4 at B=1,2,4. Model predictions and analytic truth responses were recomputed from the hash-verified original inputs; no new observations were sampled.

The target can change which of the five actions is optimal. For example, in Held-out at B2 with M4, the action-grid optimum was an interior action for 92.5% of SCMs at delta 0, while it was an endpoint in the other target settings. This changes the decision problem and demonstrates target dependence; it does not show that the baseline task was invalid. Mean regret and optimal-action support by cohort/policy/budget/target are saved in the aggregate CSV.

No Research C graph-free baseline existed in the frozen study, so one was not retrofitted. Research D target sensitivity was not run because the accessible audit contained no per-G0 recommendation, training frame or raw response vector. In particular, no new D intervention sampling was performed.

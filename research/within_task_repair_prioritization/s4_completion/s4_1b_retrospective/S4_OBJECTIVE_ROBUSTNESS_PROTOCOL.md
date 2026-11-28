# S4 objective robustness protocol (proposal)

Status: `PROPOSED_NOT_RUN`. Existing S4 pilot remains gamma=0.

Reuse the same frozen SCM, G0, observational frame, action grid and base target. For each structural trajectory, independently recompute policy recommendations and true action regret under gamma=0, 0.2, and 0.5 using the already defined objective `L_gamma(k)=standardized_tracking_loss(k)+gamma*k^2`. Gamma is a hypothetical action penalty, not a monetary cost. Do not transfer Research S1 output as though it were an S4 result.

For each gamma report optimum-action location, effect-sign/magnitude diagnostics, recommendation changes, single-edit values, interactions, structural score gains, and policy/ex-post gaps. Keep structural trajectories fixed across gamma so only objective-dependent action selection and regret change. Use SCM-blocked paired differences and common bootstrap units across gamma. The minimum family and multiplicity adjustment must be frozen before a future run. Existing pilot has no saved gamma-specific recommendation/evaluator table; computing this requires deterministic learner reevaluation from saved observations and a separately committed retrospective analysis lock. This task did not execute it; no fitted model or new sample was produced.

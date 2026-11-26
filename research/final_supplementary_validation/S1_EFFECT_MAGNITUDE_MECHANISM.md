# S1 — Effect magnitude and mechanism diagnostics

The objective penalty changes which action is preferred even when the graph and learner remain fixed. In the original target condition, gamma zero reproduces the endpoint optimum for every C SCM; increasing gamma yields interior and zero-action optima. This means the original endpoint concentration is partly a property of the target-tracking setup rather than a general statement about causal decision tasks.

The prior `abs_effect_magnitude_error` field computed `abs(estimated_slope - true_slope)`, an absolute signed total-effect slope error, not pure absolute-magnitude error. Corrected summaries preserve the numeric values and rename their interpretation. Saved per-action prediction vectors were unavailable, so oracle intercept-only or slope-only substitution diagnostics were not run. These are post-hoc diagnostics, not causal mediation evidence.

The empty-DAG learner is named `EMPTY_DAG_LEARNER`; it is not the Research F observational X–Y association learner. The existing F association baseline's gamma-zero Held-out regret is {float(final_audit['saved_f_association_baseline'][1]['mean_gamma_zero_regret']):.8f}; it was not newly evaluated over S1 gamma conditions. The action penalty is an abstract sensitivity parameter, not measured cost. Raw regret across gamma or cohorts is not a common economic scale.

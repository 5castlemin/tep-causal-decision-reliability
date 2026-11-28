# S6-3 — Incremental Structural-Information Value

**Status: `NOT_RUN` for nested out-of-sample feature prediction and hybrid-policy evaluation.** The saved S4 candidate rows support descriptive B=1 comparisons for one Development-selected type ranking and the existing T5 rule, but do not provide a preregistered, leakage-safe nested model evaluation for all T1–T6. S6 did not rerun the 63-subset search, fit new candidate-value models, or develop a hybrid policy.

The replication-cohort B=1 type-ranked versus T5 contrast was `+0.006460` (left minus right; positive means type-ranked had higher regret), with pointwise SCM bootstrap interval `[−0.001180, 0.017319]`. T5-guided M4 versus Frozen M4 was `−0.008664` with interval `[−0.020484, 0.000005]` in this common-index reaggregation. Neither comparison establishes superiority. The frozen S4 report's original interval and precision decision remain authoritative for that earlier locked analysis; this S6 reaggregation is supplementary and does not overwrite it.

The small performance differences coexist with high selection overlap and a large no-op mass. Among replication SCMs, 63/160 had no initial legal M4 candidate. Conditional selection among initial candidate rows is not representative of all deployment states.

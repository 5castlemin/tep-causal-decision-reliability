# Research E — S5 External Budget Analysis

S5 extension re-aggregation uses the existing 200 G0 unit-policy losses, recommendation records and common intervention response vectors. No DRF fit or response sampling was rerun. The public S5 saved range is B=0–4; 200 units are corruption draws conditional on one Station1 semisynthetic DGP and fixed training frame, not independent SCMs.

At B=2, saved means are S0 0.875236, M4 0.868384 (0.295 mean edits), T5-guided M4 0.868384 (0.295), Full T 0.868384 (0.295), M2+M4 0.867997 (0.570), Full Greedy 0.868255 (1.090), and graph-free association 0.867868 (zero edge edits). The B=2 primary No-repair minus M4 difference is +0.00685175. Its G0-only interval is `[0.00486307, 0.00902371]`; action-MC-only and two-source intervals include zero. Thus the apparent point-estimate improvement is uncertain once action Monte Carlo variability is included.

M4 and T5 have identical B=1–4 displayed recommendations/loss summaries; S5 reports the same first edit for all 200 G0 draws. The candidate opportunity is sparse, so these results do not show that T5 adds value in this external cohort. Graph-free's mean is slightly lower than M4, but counted edge edits are not total computational/economic cost.

Higher budgets B=5–9 are `NOT_RUN` because sealed recommendation and evaluator records stop at B=4. No estimates are inferred from the observed plateau. See [`S5_EXTERNAL_PRIMARY_RESULTS.md`](../within_task_repair_prioritization/s4_reconstruction/S5_EXTERNAL_PRIMARY_RESULTS.md), [`S5_STRUCTURAL_OPPORTUNITY_RESULTS.md`](../within_task_repair_prioritization/s4_reconstruction/S5_STRUCTURAL_OPPORTUNITY_RESULTS.md), and the saved unit aggregation in `outputs/final_extension_v1/`.

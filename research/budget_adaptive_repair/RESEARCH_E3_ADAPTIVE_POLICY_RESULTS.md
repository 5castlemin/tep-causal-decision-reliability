# E-3 — Adaptive M4 exploratory analysis

`ADAPTIVE_M4_BLOCKER_AWARE` was implemented separately from the frozen policy engine. Six deterministic fixtures passed: unchanged M4 behavior absent a blocker, no task error, valid off-task FP blocker, irrelevant off-task FP, insufficient one-edit residual budget, and an outcome-free input interface.

The policy then ran on the same original C cohorts after exact-input verification. It made no blocker edits in Development. In Held-out it used two blocker edits total from B3 onward (mean 0.010 per SCM at B3–B9). At B2 it exactly reproduced the original M4 aggregate. At B3 its mean regret was 0.000964 versus M4's 0.001435 (paired difference `−0.000471`, 95% paired SCM-bootstrap interval `[−0.001414, 0.000000]`); its mean cost was 0.780 versus 1.350 for M2+M4 and 1.325 for Full Greedy. At B5 it reached 0.000828 at mean cost 0.810. These are exploratory cohort-conditioned comparisons. Paired unit-level differences and bootstrap intervals are in `e3_adaptive_paired_comparisons.csv`; no result changes an original Research C estimand.

The blocker mechanism was triggered only where one M2 off-task FP deletion unlocked a positive-gain task edit. It did not generally solve multiple-blocker planning, and it was not uniformly cheaper or better for each SCM. Edits still count as unit-cost edge changes rather than labor cost.

No corresponding Research D adaptive analysis was possible because the local D artifact lacked per-G0 recommendation rows. No D outcome or intervention was created.

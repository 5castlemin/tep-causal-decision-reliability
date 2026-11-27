# Research E — Pareto and Cost-Weighted Policy Report

For each saved cohort, candidate coordinates are mean atomic edit count and mean cohort-specific loss. Both fixed-budget and cross-budget nondominated sets retain identical-coordinate policy ties. CSV: [`pareto_frontier.csv`](outputs/final_extension_v1/pareto_frontier.csv). Candidate lower-envelope intersections and observed switches are in [`lambda_breakpoints.csv`](outputs/final_extension_v1/lambda_breakpoints.csv).

The objective is `Jλ = mean_loss + λ × mean_edit_count`. λ is a hypothetical penalty per graph edit. It does not measure money, labour, engineering time or safety. A frontier member is not necessarily statistically better, and a point can lie on a Pareto frontier without being selected by this linear objective. The lower envelope is computed on the observed sample and therefore constitutes in-sample descriptive optimization.

S5 includes graph-free association with zero counted edge edits. Its loss is slightly lower than M4 in the saved B=2 data. This comparison is conditional on an edge-edit-only cost axis and does not imply zero total model development cost. S4 has no directly comparable graph-free line in the same saved extension table. Research C, S4 analytic regret and S5 standardized tracking loss are analyzed in separate panels/cohorts and never pooled.

The inherited Research C results remain the only B=0–9 series in this final E package. The new S4 and S5 rows stop at B=4; no higher-budget policy is chosen from an inferred curve. Existing E frontier plots under `figures/` cover Research C. The new machine-readable frontier and breakpoints support additional plotting without conflating scales.

# E-1 — Pareto frontiers and hypothetical edit-cost preferences

Two frontier types are reported: within the same maximum permitted budget, and across all examined policy-budget combinations. A point is dominated if another has both no greater average edit count and no greater average regret/loss, with a strict improvement in at least one. Exact-coordinate ties are retained. C frontiers use paired SCM averages; D uses saved aggregate means only.

The cost coordinate is the number of atomic graph edits. It does not include diagnosis, engineer time, validation, safety, or implementation cost.

## Research C Held-out

The original B≤4 cross-budget observed frontier contains S0 B0, M3 B1, M4 B1–3, and M2+M4 B4 (with identical-coordinate ties preserved in the machine table). M4 provides a sharp early reduction in regret at lower mean edit counts than Full Greedy. At B4, M2+M4 reaches 0.000964 mean regret at 1.440 edits, while Full Greedy reaches the same 0.000964 at 2.005 edits; M2+M4 therefore dominates that Full Greedy point under this edit-count metric. This observed mean frontier is not a statistical dominance claim.

At B2, M4 mean regret is 0.003988 for 0.695 edits; Full Greedy is 0.018603 for 1.435 edits. In the original C Held-out Primary, Full Greedy is favored over S0, while M4 remains a Development-selected Secondary. Cost analysis does not change those inferential roles.

## Research D Final

The saved aggregate data put M4 B1, M4 B2, M2+M4 B2, and the zero-edge-edit graph-free association baseline on the observed frontier; equal-loss structure policies are dominated by the zero-edit graph-free point under the stated edge-edit-only cost. At B2, the graph-free baseline and Full Greedy both have mean loss 0.789362, but graph-free performs zero graph edits. This does not mean graph-free training has zero total economic cost, and it is not evidence that graph-free is causally equivalent.

D's graph-free point uses its saved aggregate baseline result. No unit-level frontier inclusion probability or paired uncertainty can be calculated from the accessible artifact.

## Lambda objective

For `J_lambda = mean loss + lambda × mean edits`, the common lambda grid is a sensitivity display. `lambda=0` chooses minimum observed mean loss; increasing lambda favors fewer edits. Exact pairwise intersections and supported-optimum intervals are saved in `lambda_exact_intervals.csv`. The same numeric lambda across Research C regret and Research D standardized tracking loss is not the same economic preference. A convex weighted objective can skip non-supported Pareto points; the Pareto set and lambda-optimal set need not coincide.

This is post-hoc selection on already observed cohorts, including held-out evidence. It is descriptive policy choice, not a newly validated decision rule.


## Final audit extension — C Bmax and Adaptive M4

The final closeout recomputed cross-budget and fixed-Bmax frontiers with the original 17 repair policies plus the 18th post-hoc `ADAPTIVE_M4_BLOCKER_AWARE` policy. C Held-out cross-budget mean frontier points after preserving all zero-edit ties are S0/no-edit, M3 B1, M4 B1–3, Adaptive M4 B3, and Adaptive M4 B5–9. At fixed Bmax=9, the frontier consists of S0, M3, M4 and Adaptive M4. Full Greedy is not on the observed mean frontier. C Development outputs are separately recorded. No C and D losses are pooled.

The exact lower envelope now includes transition-only breakpoint ties, including supported collinear points; pairwise intersections between candidates that are not optimal at the crossing are not presented as policy transitions. C Held-out transitions are λ≈.0045445, .0235724, .0392675, and .1287068. The exact tied candidate labels are in `research/final_integration/research_e_audit/expanded_lambda_breakpoints.csv`; region winners are in `expanded_lambda_lower_envelope.csv`. A 2,000-resample paired-unit stability table is descriptive frontier inclusion, not inferential superiority.

Research D’s graph-free point is only verified at its saved B2 aggregate: zero graph edits and the same .789362 mean loss as Full Greedy. D lacks unit-level rows here, so it is not extended over budgets.

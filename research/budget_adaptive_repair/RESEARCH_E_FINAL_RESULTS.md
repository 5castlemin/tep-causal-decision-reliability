# Research E — Final results

## Gate

`RESEARCH_E_CORE_COMPLETED_WITH_LIMITATIONS`: E-1 completed for C unit data and D saved aggregates; C E-2 exact reconstruction, B0–4 replay and B>4 downstream evaluation completed; C-only E-3 Adaptive M4 and target sensitivity completed. D unit-level extensions were not run because the accessible D audit had no per-G0 rows or response vectors. This limitation does not invalidate E-1 C results or D's existing frozen final report.

## Selected findings

1. In C Held-out, M4 mean regret fell from `0.093439` at B0 to `0.003988` at B2, `0.001435` at B3, and stayed there at B4. M2+M4 at B4 reached `0.000964` with mean cost `1.440`; Full Greedy reached the same aggregate regret with mean cost `2.005`.
2. Increasing budget was not uniformly beneficial. C Held-out M2 had negative marginal benefit at B0→1 (`−0.004823` regret units); all negative increments remain in the tables.
3. At the C cohort caps, canonical structural repair removed every initial reference discrepancy for 47/64 Development and 156/200 Held-out SCMs. Structural and policy/decision saturation differed; see terminal-feasibility diagnostics.
4. Adaptive M4 matched M4 at B2. In Held-out, limited blocker edits improved some larger-budget aggregate results, but effects are exploratory and paired per-SCM differences are retained. It is not a general-purpose planner.
5. At the target mean (`delta=0`), the target's optimum often moved to an interior action on the fixed grid; this illustrates task dependence rather than invalidating the original target.
6. D's aggregate B2 graph-free association baseline has the same loss as Full Greedy (`0.789362`) at zero graph-edit count. This is an important competing baseline, with edge-count-only cost and no unit-level reanalysis.

All primary Research C and D conclusions, contracts, and effect estimates remain as previously reported. Research E is a descriptive post-hoc extension, not a replacement primary or an independent physical validation.

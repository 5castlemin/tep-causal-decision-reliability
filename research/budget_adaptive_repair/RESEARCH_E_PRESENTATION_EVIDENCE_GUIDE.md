# Research E — presentation evidence guide

## Suggested narrative

1. Ask how a limited graph-repair budget should be allocated to improve downstream decisions.
2. Show Research C's frozen B2 Primary and clearly distinguish its 200-SCM inference from the post-hoc budget extension.
3. Show the C cost–regret curve: early gains for M4, M2+M4's later cost trade-off, and M2's negative marginal return.
4. Show the extended B5–9 curves and explain that the same original SCMs were deterministically restored and replayed, not resampled.
5. Show the decision saturation chart beside structural saturation; they need not coincide.
6. Present Adaptive M4 as a limited exploratory response to a known blocker pattern, with paired comparisons and non-universal behavior.
7. End with Research D's conditional role: a single DRF semisynthetic environment, under-missed precision goals, and a competitive graph-free baseline.

## Recommended visuals

Use SVG figures in `figures/`: `E1_policy_budget_heatmap.svg`; separate C cohort and D `E2_curves_*.svg`; `E4_pareto_*.svg`; `E7_adaptive_M4_*.svg`; `E8_target_sensitivity_*.svg`. Tables `e2_extended_marginal_benefit.csv`, `e2_extended_pareto_frontiers.csv`, `e2_saturation_diagnostics.csv`, `e3_adaptive_paired_comparisons.csv`, and `target_sensitivity_aggregate.csv` provide the numeric backing.

Every figure is exploratory and cohort-specific. Research C uses SCM-level regret; Research D uses standardized target-tracking loss. Edit count is a proxy, not money or work hours. The lambda axis is hypothetical. Do not say the D intervention was physical, that its 200 units were SCMs, that graph-free cost is zero overall, or that the new Adaptive policy is validated generally.

## Likely questions

- **Why does more budget sometimes hurt?** The selected edit sequence is heuristic and decision loss is not monotone in structural repair. The C M2 negative marginal benefit is retained.
- **Is B=7 or 9 a universal cap?** No. It is the maximum observed initial error burden in these fixed cohorts under this unit-cost candidate definition.
- **Does complete graph recovery solve all regret?** Not necessarily. The reference-graph learner is a diagnostic and still depends on finite training data, Ridge and the fixed action grid/target.
- **Does D confirm manufacturing impact?** No. It is a DRF-based semisynthetic benchmark with virtual hard-do actions and a single fitted DGP.

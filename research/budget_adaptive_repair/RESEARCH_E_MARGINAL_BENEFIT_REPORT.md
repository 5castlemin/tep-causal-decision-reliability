# Research E — Marginal Benefit and Edit-Cost Report

The saved-result extension calculates `MB(B) = mean_loss(B−1) − mean_loss(B)` and divides by the change in mean edit count only when that change is positive. If no additional mean edits occurred, benefit per edit is undefined. Positive MB means lower observed mean loss; negative MB means worsening. These are cohort-level ratios, not causal effects of individual edits.

Complete rows: [`marginal_benefit.csv`](outputs/final_extension_v1/marginal_benefit.csv). Unit-level paired bootstrap contrasts: [`paired_bootstrap_uncertainty.csv`](outputs/final_extension_v1/paired_bootstrap_uncertainty.csv). These resample whole SCM units within S4 cohorts and whole G0 draws within S5, using common indices across contrasts. S5 intervals condition on the existing action-loss table and do not include action Monte Carlo uncertainty.

The saved results demonstrate that a higher allowance does not guarantee a lower mean regret at every increment. S4 Development M4 worsens from B=2 to B=3 before improving at B=4; plateau and non-monotonicity must be reported policy by policy. The S5 saved evaluation reaches the same displayed M4/T5 loss by B=2 and adds no observed mean edit cost at B=3–4. This is an observed plateau within the saved range, not an optimal stopping theorem.

Research C's earlier B=0–9 extension and its adaptive policy remain documented in [`RESEARCH_E_FINAL_AUDIT.md`](../final_integration/RESEARCH_E_FINAL_AUDIT.md). The new S4/S5 unit records do not contain B=5–9 evaluations; no marginal values are imputed for those rows. The edit count proxy excludes actual labour and total model lifecycle cost.

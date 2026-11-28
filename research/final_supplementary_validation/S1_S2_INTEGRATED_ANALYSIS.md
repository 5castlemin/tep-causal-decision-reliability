# S1–S2 integrated analysis

Across the stored C cohorts, graph metrics tied to the task structure—especially task-zone error rate and X→Y path presence—are more strongly associated with regret than global accuracy alone. The relationship is not deterministic: graphs with the same SCM and similar aggregate score can have different policy recommendations and regrets. S1 further shows that the decision objective can change the optimal action distribution substantially.

Together these analyses support a conditional conclusion: structural quality matters through the task and objective used to make decisions. They do not show that any single structural metric causes a reduction in regret, nor that task-zone metrics dominate for other tasks. A corrected common-graph analysis uses the same B=2 graph set (84 Development graph rows/36 SCMs; 250 Held-out graph rows/121 SCMs), SCM-balanced weighting, and shared paired SCM bootstrap indices to compare correlations across original target gamma 0/.2/.5/1 and offsets ±.25 at gamma .2. Results are in `outputs/s1_s2_common_graph_objective_associations.csv`; they are descriptive and pointwise, not independent replications. Undefined correlations under constant outcomes remain NA. This does not validate S2 predictive performance under each objective.

Held-out common-graph SCM-balanced Spearman correlations (121 common SCMs, 250 graph rows; point estimates):

| Objective condition | SCMs | Directed F1 | Task error rate | X→Y path |
|---|---:|---:|---:|---:|
| Original γ=0 | 121 | -0.383 | 0.676 | -0.887 |
| Original γ=.2 | 121 | -0.062 | 0.126 | -0.209 |
| Original γ=.5 | 121 | -0.072 | 0.011 | 0.005 |
| Original γ=1 | 121 | -0.028 | -0.035 | 0.069 |
| δ=−.25, γ=.2 | 121 | -0.053 | 0.001 | 0.022 |
| δ=+.25, γ=.2 | 121 | -0.003 | -0.070 | 0.086 |

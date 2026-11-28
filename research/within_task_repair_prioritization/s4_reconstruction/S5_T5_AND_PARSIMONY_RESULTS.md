# S5 T5 and Parsimony Results

At B=1 through B=4, T5-guided M4, frozen M4, and Full T1–T6 produced identical aggregate losses and costs in this run. Their B=2 mean loss was 0.868384 and mean edits 0.295. Unit-level diagnostic shows identical first edit, final graph, and recommended action on all 200 G0 draws. T5 had only two unique strictly positive winners among the five G0 draws with at least two initially DAG-legal M4 candidates; it did not create a policy distinction at the cohort level.

At B=2, Full Greedy averaged 1.090 edits and loss 0.868255; M2+M4 averaged 0.570 edits and loss 0.867997. M2+M4 therefore had lower observed loss with fewer mean edits than Full Greedy in this fixed run, but this is exploratory and uncertainty spans shared action losses. The graph-free association baseline's loss was 0.867868 with zero counted edge edits. The edge-edit metric excludes the cost of fitting, validating, or maintaining that model.

No superiority, equivalence, or noninferiority claim is made. The full budget table is `outputs/s5_reconstruction_v1/policy_budget_aggregates.csv`.

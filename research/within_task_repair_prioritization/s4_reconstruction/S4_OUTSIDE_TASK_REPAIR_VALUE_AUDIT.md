# S4 Direct Outside-Task Repair Value Audit

See `S4_DIRECT_OFF_TASK_EDIT_DIAGNOSTIC.md` for the protocol and aggregate results. That analysis evaluates actual legal graph edits before assigning repair value; a no-op is not counted as a zero-value repair.

Across the eligible stored 64-pilot, 80-development, and 160-confirmation units, 759 direct candidate edits were evaluated; 747 were DAG-legal and 12 infeasible. Among 77 legal outside-task false-negative edits, observed regret change and recommended action did not change. This is a result for these candidate edits and tasks only, not evidence that all outside-task errors are harmless. Other outside-task false-positive edits could help or harm. The comparison is not a randomized causal effect: edit candidates differ structurally, and some comparisons do not share the same initial graph.

For each evaluated edit the private diagnostic binds the operation and pair to before/after graph hashes, feasibility, edit count, action, and regret. No raw unit records are in the public repository.

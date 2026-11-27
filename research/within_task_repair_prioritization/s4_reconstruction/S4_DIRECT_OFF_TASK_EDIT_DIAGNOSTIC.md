# Direct Single-Edit Diagnostic: Task and Outside-Task Errors

Status: retrospective replay completed using saved Development, confirmation and original-PC S4 pilot units. No SCMs, G0s, observations or intervention responses were generated.

## Method

For each saved unit, the reference-relative event list was checked against the complete `policy_engine.candidates` output. Every error correction was directly applied once, including M1/M2/M3 outside-task events that frozen M4 omits. DAG-illegal corrections were retained as infeasible and were not assigned zero value. For legal corrections, the same saved observational frame, learner, action grid, target and SCM analytic evaluator were used before and after the edit. Value is `Regret(G0) − Regret(G0 after edit)`; one edit costs one atomic graph edit. This is a one-edit what-if diagnostic, not a deployable policy evaluation or a causal effect estimate.

## Coverage and descriptive results

Across 64 historical pilot units, 80 reconstructed Development units and 160 independent confirmation units, 759 reference-relative edit candidates were directly enumerated. Of these, 747 were DAG-legal and 12 were infeasible. There were 347 task-zone and 412 outside-task candidates before the DAG check; 341 and 406 respectively were legal. Candidate edits are clustered within the same SCM/G0 and must not be treated as independent observations.

| Cohort | Role | Error | Legal edits | Mean regret reduction | Positive / negative / zero | Action changed |
|---|---|---|---:|---:|---:|---:|
| Original-PC pilot | Outside-task | FN | 14 | 0.000000 | 0 / 0 / 14 | 0.0% |
| Reconstructed development | Outside-task | FN | 21 | 0.000000 | 0 / 0 / 21 | 0.0% |
| Independent confirmation | Outside-task | FN | 42 | 0.000000 | 0 / 0 / 42 | 0.0% |
| Original-PC pilot | Outside-task | FP | 42 | −0.018081 | 0 / 1 / 41 | 2.4% |
| Reconstructed development | Outside-task | FP | 53 | 0.000000 | 0 / 0 / 53 | 0.0% |
| Independent confirmation | Outside-task | FP | 131 | +0.004984 | 2 / 0 / 129 | 1.5% |
| Original-PC pilot | Task-zone | FN | 36 | +0.031969 | 6 / 0 / 30 | 16.7% |
| Reconstructed development | Task-zone | FN | 29 | +0.056352 | 4 / 0 / 25 | 13.8% |
| Independent confirmation | Task-zone | FN | 47 | +0.086908 | 11 / 1 / 35 | 25.5% |
| Original-PC pilot | Task-zone | REV | 24 | +0.080073 | 3 / 1 / 20 | 16.7% |
| Reconstructed development | Task-zone | REV | 12 | +0.067986 | 2 / 0 / 10 | 16.7% |
| Independent confirmation | Task-zone | REV | 40 | +0.122264 | 12 / 1 / 27 | 32.5% |

Other task-zone and outside-task error-type rows, including UNRES, are preserved in `outputs/direct_edit_v1/direct_edit_aggregate.csv`.

## Interpretation

In these saved units, direct single repairs of 77 legal outside-task FN events (14 + 21 + 42) produced zero analytic-regret change and no action change; this is evidence for these exact graph/SCM/task units, not a universal zero-value result. The outside-task FP corrections were usually neutral, but include one loss-increasing historical-pilot case and two loss-reducing confirmation cases. Task-zone FN and REV corrections more often improved the decision in this sample, yet many edits remained decision-neutral, and a few worsened regret. The pattern is consistent with task relevance mattering, while showing that error type and the rest of the graph can still change the value. No confidence interval was computed over pooled candidate edits; a unit-clustered matched analysis is required for inferential claims.

The prior statement “outside-task FN repair value = 0” was not supported by the original M4 policy run, because those edits were excluded from its candidate set. This direct replay now measures the what-if value in the accessible units and keeps the scope conditional.

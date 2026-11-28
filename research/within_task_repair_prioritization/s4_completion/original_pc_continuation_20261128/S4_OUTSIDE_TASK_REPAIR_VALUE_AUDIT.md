# S4 outside-task repair-value audit

Status: `NO_DIRECT_OUTSIDE_TASK_REPAIR_VALUE_ESTIMATE`.

The saved pilot code's `feasible_m4` builder filters candidates through `s3.direct_task_edit(...)` (`run_s4_pilot.py`, candidate construction and replay paths). Thus the M4 candidate table and its recorded `regret_gain` apply to eligible direct task edits, not to arbitrary off-task corruption events. The saved corruption inputs include off-task errors, but an off-task error's presence or omission from a task-zone candidate set is not an intervention on that error and cannot be interpreted as repair value zero.

Across the accepted corruption events in the 64 saved inputs, the archived records show off-task events of several types. Those are generation records, not applied policy edits. The policy/candidate outputs do not provide a direct, independently evaluated single-edit counterfactual for each off-task event. No new single-edit replay was run in this continuation; therefore actual off-task edit pair/operation, post-edit graph, and before/after regret are not available for a claim about outside-task repair effects.

Conclusion: previous “outside-task FN value = 0” summaries must be read as no observed value in the task-filtered M4 candidate/evaluation path unless their underlying calculation establishes an actual edit. They do not establish that outside-task errors have no decision value. A valid direct diagnostic would require replaying each saved SCM/G0/observation with one explicit legal off-task edit and analytic evaluation under a separately bound retrospective analysis; this continuation did not execute that analysis.

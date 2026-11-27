# Research S4/S5 gate closeout

| Gate | Status | Evidence / limitation |
|---|---|---|
| Gate 0 — S3 preflight | `PREFLIGHT_VERIFIED_WITH_LIMITATIONS` | Existing S3 source audit and read-only SHA-256 checks on the four original C SQLite inputs; completion-v3 history remains separate. |
| Gate 1 — independent pilot | `PILOT_EXECUTED_WITH_LIMITATIONS` | 32 general and 32 structurally opportunity-rich SCMs evaluated; 142 G0 screening draws and 32,768 observations; no sampled intervention rows. |
| Gate 2 — mechanisms | `PARTIAL_MECHANISM_ANALYSIS` | Single-edit values, limited task-role labels, 63 subset policies, and feasible ordered two-edit diagnostics summarized. No matched corruptions, adequately powered mechanism model, or causal role effect. |
| Gate 3 — confirmation protocol | `PROPOSED_NOT_LOCKED_FOR_EXECUTION` | Protocol and design proposal exist; the selected policy, confirmatory contrast, precision target, and N are not frozen. No confirmation data were created. |
| Gate 4 — independent confirmation | `NOT_RUN_NOT_AUTHORIZED` | Requires a separately approved, committed scientific protocol. |
| Gate 5 — external feasibility | `BLOCKED_UNAVAILABLE_PRIVATE_UNIT_ARTIFACTS` | Research D unit-level G0/recommendation/training/response artifacts are not available in the approved local artifact root. Historical audit summary only. |
| Gate 6 — external execution | `NOT_RUN_NOT_AUTHORIZED` | No new CausalAssembly refit, G0, intervention sample, station, or dataset. |
| Gate 7 — cross-environment synthesis | `NOT_RUN` | Cannot make an S4-to-D mechanism comparison without the D unit-level artifacts and a frozen transfer analysis. Existing C/D claims retain their earlier scope. |

## Pilot execution integrity

The pilot was generated once under the committed S4 lock. A runtime dictionary-key bug stopped the first evaluator attempt after generation. A separate continuation reused the private generated inputs and locked recommendation manifest. The evaluator tables were written once; a subsequent summary field error was fixed by a summary-only continuation that verified the table hashes and did not repeat evaluation or generation. All failed attempts, commits, row counts, and checkpoints are retained outside the public repository. No generated unit was replaced.

The actual evaluator is analytic ground-truth evaluation, so “0 intervention rows” means no Monte Carlo response rows were sampled. It does not mean that no evaluation occurred.

The one local full-suite failure was a Windows checkout byte mismatch: a protected historical JSONL artifact has a Git LF blob whose hash matches the expected manifest, while the local CRLF worktree bytes do not. The frozen test was not changed. On this checkout the suite discovered 468 tests and reported one failure; this is not recorded as a passing local suite. Focused S4 tests and the public research-state check pass. CI status must be reported from the actual remote run, not inferred from local results.

## Interpretation boundary

S4 is a small, exploratory pilot in one signed-linear Gaussian generator family. The opportunity-rich cohort is selected using structure alone and estimates a conditional diagnostic quantity. The pointwise intervals are descriptive; the candidate rows and edit pairs are clustered within SCM. The observed tables are useful for feasibility and for planning, not confirmation.

S5 is not negative evidence about transfer. It is currently unassessable from the permitted local files. Research D's previously reported aggregate results remain historical and are not upgraded by this audit.

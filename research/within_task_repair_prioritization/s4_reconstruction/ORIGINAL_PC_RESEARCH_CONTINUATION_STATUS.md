# Original-PC Research Continuation Status

Status date: 2026-11-28. Branch: `research/s4-reconstruction-s5-validation`.

This continuation used the original research PC. It did not recover or claim to reproduce the missing other-PC commits `928d784`, `65e4413`, `00d20b7`, or `58d934b`. Those reports remain historical and independently unverifiable. The current branch contains the local S4 reconstruction and the new S5 run; main and PR #50 were not changed.

## Completed here

- Reused the saved S4 pilot 64 units, then performed a bounded reconstructed development cohort of 80 SCMs and a new independently seeded replication cohort of 160 SCMs.
- Ran the locked Station1 semisynthetic S5 execution with 200 graph-corruption draws, 22,000 recommendation rows, and 24,995 evaluator responses (plus one separately counted smoke response).
- Preserved training, unit records, recommendations, and response vectors outside the public repository. Public files contain aggregates and hashes only.
- The user-authorized Research E extension remains future work; this task did not perform it.

## Git and verification

Execution code revision for S5: `c571d2a58fcc09d7799eb4a8965217e7ab997401`. The retrospective S4 candidate-ranking analysis was committed separately at `22816b636ffd8857e62d517fcb3efcb148ad1b6a`; its CI run `46045720886` succeeded. Subsequent public closeout documentation and aggregate exports are recorded in later commits. No claim is made that the other-PC work has been integrated.

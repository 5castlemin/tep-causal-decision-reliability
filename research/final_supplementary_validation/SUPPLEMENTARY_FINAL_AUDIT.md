# Final supplementary audit

## Scope and gate

Read-only reanalysis of original C cohort data and saved C policy trajectories; no SCM, G0, observations, interventions, or expert responses were generated. F-Lite stored evaluation rows were not changed. Research D private unit-level materials were not available and were excluded.

## Corrections and validation

- Full Greedy is `M1+M2+M3+M4`; `CANONICAL_ORACLE` is distinct. The corrected shared-index paired contrasts are in `outputs/s1_corrected_primary_contrasts.csv`; the original incorrect comparison is retained as historical/superseded.
- The empty-DAG graph learner is labeled `EMPTY_DAG_LEARNER`, not Graph-free association. The saved Research F association baseline is reported only for gamma zero and was not reevaluated for the supplementary objective grid.
- The original S2 B/E feature comparison was not nested. Corrected B_original/E_nested/F_nested results use shared saved features and Development grouped folds, with Held-out reserved for evaluation.
- A same-graph-set objective-association reaggregation covers six prespecified saved objectives. It is SCM-balanced and uses common SCM bootstrap draws; it is descriptive and does not rerun predictive validation under each objective.
- The weighted AUROC implementation was corrected after range validation found values above 1; the corrected held-out AUROC values are B=.856, E=.905, F=.961.
- Gamma-zero reproduction and deterministic fixtures passed. AP tie-group fixtures include perfect, reversed, all-tied, nonuniform-weight, and within-tie permutation checks.
- Paired contrasts and metric associations use common SCM resamples and SCM as the independent unit; intervals are pointwise, not simultaneous.
- SID/AID remain unrun because no verified compatible implementation/fixture was available.
- All public tables are aggregate only. Unit-level S1/S2 files are gitignored and stay local.

Detailed hashes, CI counts, exact commands, and any environment caveats are recorded in the integrity manifest and the accompanying closeout.

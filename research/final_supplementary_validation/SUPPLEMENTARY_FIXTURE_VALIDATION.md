# Supplementary code and fixture validation

The new calculation paths were checked with deterministic fixtures before reading cohort results. Tests cover gamma-zero identity with target-tracking loss, positive gamma action penalty, action tie-breaking, saved-edge replay and DAG validity, distinction between directed and skeleton metrics, SCM-grouped folds, heterogeneous CSV schemas, and weighted AUROC bounds/ties.

The supplementary audit also checks that duplicate `(SCM, structural graph hash)` rows agree on learner inputs, recommendation and loss before deduplication. Gamma-zero action/regret outputs reproduce the stored Research C outputs within the original `1e-12` regret tolerance. The original stored trajectory and result tables are not rewritten.

`SID/AID` was not run: this frozen environment contained no verified implementation and compatible fixture for the exact unresolved-edge and graph conventions. No result is imputed for those metrics.

The logistic classification audit initially exposed an AUROC implementation error (values above 1). It was corrected to a weighted Mann–Whitney calculation, a perfect/reversed/tied score regression test was added, and the stored-only audit was rerun. The final AUROC values are all in `[0,1]`.

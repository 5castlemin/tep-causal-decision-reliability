# Supplementary contract correction V2

This document corrects the analysis/reporting interpretation after the saved-result audit. It does not rewrite the original contract snapshot or change any Research C frozen contract or source execution. The original `SUPPLEMENTARY_EXPERIMENT_CONTRACT.md` and `supplementary_contract.json` remain preserved as historical artifacts; their original SHA-256 values are recorded in the pre-correction integrity manifest (`2a25a73cf90d03131067d74b28b73c0642e3b58b21fdc3b79401a25be1fea8cd` and `3117ecd15a2aa111e3fd081e688e50e654b0f00ad2e5ff6fd64e4487e3b14f86`).

## Corrections

1. The S1 Full Greedy comparator is policy ID `M1+M2+M3+M4`. `CANONICAL_ORACLE` is a separate structural-only diagnostic. The historical `s1_primary_contrasts.csv` is retained and superseded by `outputs/s1_corrected_primary_contrasts.csv`; the corrected contrasts use one shared set of 10,000 SCM bootstrap indices per cohort. Intervals are pointwise paired percentile intervals, not simultaneous intervals.
2. `GRAPH_FREE` in the original S1 saved table means a blank DAG supplied to the existing graph learner. Its corrected label is `EMPTY_DAG_LEARNER`; it is not Research F's observational X–Y association learner. The saved F association baseline is reported only for the original gamma-zero objective (.02938967 Development; .03872502 Held-out) and was not newly scored over the S1 objective grid.
3. S2's original B and E feature sets were not nested. A post-hoc comparison now refits B_original, E_nested=B_original plus the existing task features, and F_nested=E_nested plus `xy_path`, using the same saved rows, Development SCM-grouped folds, weighting, alpha candidates, and preprocessing. Held-out rows are not used for tuning.
4. S2 weighted Spearman is defined as midrank transformation followed by SCM-weighted Pearson correlation. Correlation resampling shares the same cluster draws across metrics within a cohort. These intervals are pointwise.
5. Classification PR-AUC is weighted Average Precision; tied score groups are processed together. It is not trapezoidal PR-AUC. Regression fixtures cover ranking, reverse ranking, all-tied scores, nonuniform weights, and invariance to row order within ties.
6. Existing effect error field `abs_effect_magnitude_error` is `abs(estimated_slope - true_slope)`, an absolute signed total-effect slope error. Its historical values are retained with corrected interpretation.

## Scope

All additions are saved-result reaggregation, deterministic refitting of predictive models from saved feature rows, or read-only checks. No new SCM, G0, observations, interventions, or expert responses were generated. No Research C frozen policy, learner, evaluator, contract, or result was changed. Research D unit-level material was unavailable for this supplement and is not imputed.

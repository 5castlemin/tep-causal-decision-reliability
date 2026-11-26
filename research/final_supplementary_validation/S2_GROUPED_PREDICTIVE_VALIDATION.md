# S2 — Grouped predictive validation

Models were trained and regularization selected only with five-fold Development CV grouped by SCM, using equal total SCM weight. The existing Held-out cohort was then evaluated once. The B-vs-E comparison is post-hoc because the C cohorts and outcomes had already been observed when this supplement was designed.

General structure features alone (B) yield Held-out SCM-balanced MAE .06966. Task-only features (D) yield .05763. General plus task features (E) yield .06047; paired SCM bootstrap reports B–E MAE difference .00919 (95% [.00239,.01576], 110 better / 73 worse / 17 tied). Structure plus directed-path (F) yields .03749; the oracle-effect diagnostic model G yields .03769 MAE and is not deployable. Full model outputs and paired intervals are in `outputs/s2_model_validation.csv` and `outputs/s2_prediction_bootstrap.csv`.

Positive-regret classification uses logistic models with the same grouped folds. The corrected Held-out AUROC values are .856 (B), .905 (E), and .961 (F), with Brier .114, .083, and .022. These are historical post-hoc discrimination results, not prospective calibration or an operational screening guarantee. Held-out PR-AUC is prevalence-sensitive and should be interpreted alongside the SCM-balanced positive prevalence.

# Supplementary claims and evidence matrix

| Claim | Evidence | Unit / estimand | Grade | Limit / permitted wording |
|---|---|---|---|---|
| The objective changes action-optimum support. | `outputs/s1_optimum_distribution.csv` | C SCM; analytic grid optimum under fixed target/gamma | Post-hoc robustness | “In these cohorts, positive gamma produced interior/zero optima in some conditions.” Not universal. |
| At gamma .2/B2, repair policies have lower Held-out regret than S0. | `outputs/s1_primary_contrasts.csv` | Paired Held-out SCM; regret difference | Post-hoc | Report exact contrasts and intervals; does not alter C primary. |
| Task/path structure is more informative than global scores for regret here. | `outputs/s2_metric_correlations.csv`, `outputs/s2_model_validation.csv` | SCM-balanced graph association and Held-out prediction | Post-hoc metric evidence | Cohort/task conditional; not a causal metric effect. |
| Path features improve predictive MAE over general/task features. | `outputs/s2_model_validation.csv`, `outputs/s2_prediction_bootstrap.csv` | Fixed historical Held-out SCM-balanced MAE | Post-hoc | Model selection in Development; one historical Held-out evaluation. |
| Oracle-informed G is deployable. | No | N/A | Unsupported | G uses oracle effect diagnostics; do not claim deployability. |
| SID/AID establishes metric superiority. | Not computed | N/A | Unsupported | No verified compatible implementation. |
| Research D has supplementary unit-level validation here. | D private unit-level data absent | N/A | Unsupported | State the exclusion. |
| The findings establish plant-level gains or economic savings. | No physical/economic evaluation | N/A | Unsupported | Do not claim. |

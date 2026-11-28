# Research S3 metric-gain validation

This post-hoc diagnostic compares per-edit T1–T6 score gains and frozen M4 gain with realized single-edit regret reduction. Scores and outcomes are grouped within SCM first; SCMs, not candidate rows, are the reporting units. The supplied table reports SCM-balanced pairwise ranking accuracy, within-SCM Spearman when defined, best-candidate hit rate allowing ties, and counterexamples where positive structural gain coincides with worse realized regret.

Results and counts: `tables/correction_v1/corrected_s3_metric_gain_validation.csv`. No confidence intervals were computed for ranking summaries, and no held-out cohort was reserved for choosing metrics: both original Research C cohorts had already been observed. The rankings are descriptive. Discrete metrics generate many ties; Spearman denominators vary and are explicitly smaller than or equal to the multi-candidate SCM count. Ties in score count one-half in pairwise accuracy; utility-tied candidate pairs are excluded.

A structural score is not a direct estimate of the causal or decision value of an edit. Positive structural gain can co-occur with a worse decision regret, and a zero score gain can co-occur with a realized benefit. No general metric ranking is established.

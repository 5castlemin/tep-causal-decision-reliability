# Step 4B-4 readiness report

Overall: **IN_PROGRESS**. Step 4 remains **IN_PROGRESS / NOT FROZEN**. No confirmation SCMs, new SCM coefficients, observations, intervention effects or Decision Regret were generated.

## Verified evidence

- Q-common topology-only audit: 637/2000 of 2,000 attempts accepted (31.850%); exact 95% interval [29.811%, 33.942%]. Raw gzip SHA-256 `c0ce611bf7aeca025407d884111fa919175c5bd091f9d55537de022948aa406e`; settings SHA-256 `a7e44c66387ac77ca10ff344cacec2c3fbf678d04741087701c16b6d042bc414`. All rejected rows retained.
- Same-final-graph invariance test is added on the existing fixed Step 3 unit fixture: when graph, data, schema and candidate grid match, G/T/Random labels and seed do not enter model fitting or recommendation. This is a unit-fixture validation, not new research data.
- Statistical calibration artifact records paired-difference-only simulations; paired t and percentile bootstrap fail the skewed zero-heavy stress case.
- Failure/fallback executable rules preserve status and disallow incomplete type averaging.

## Contract recommendation

Use uniform-stratum rejection sampling to target P conditional on Q-common; no quotas unless inclusion weights and variance method are fixed prospectively. Equal type weights 1/3 form one SCM row; SCM is the independent unit. 64 development and 200 confirmation remain candidate eligible-SCM counts. The observed yield implies planning caps, but stratum variation and zero-yield strata prevent adopting these as fixed caps.

The proposed primary H2 contrast remains Global minus Task-Focused, B=1, gamma=1, within-type matched and averaged across FN/FP/REV. Positive favors Task-Focused. It remains planned, not statistically ready: no calibrated mean-inference method selected, no justified power/SDE-specific precision guarantee, no frozen N, and no validated compute cap.

## Open gates

1. Choose and calibrate a valid mean-estimand test and confidence interval under plausible zero-heavy/skew/extreme distributions.
2. Determine sample-size/precision using defensible variance scenarios; current n=200 power at delta=.10 is about .29 under a unit-SD normal difference and is not a guarantee.
3. Estimate Q yield with a prespecified stratum-aware method; set finite attempt caps and shortfall action.
4. Benchmark full 10-node Ridge/candidate path without creating new research observations; current local bench limited to graph-only 10-node structures plus existing fixed 3-node Step 3 fixture for Ridge.
5. Set time, memory, storage caps and prove resume/deduplication for the final runner.
6. Freeze operational missingness, infra retries, fallback, and one missing primary SCM stop rule in code and preregistration.
7. Reconcile older Step 0/Step 4 draft language and run final Python 3.11 CI, frozen assets, state consistency and Self-Review on the final HEAD.

Accordingly, this work does not meet Step 4B-4 DONE conditions and does not authorize Step 5 or confirmation generation.


## Remediation update (v2)

The original v1 alt-CI coverage field was incorrect and is superseded. v2 separately verifies alternative true-mean coverage, zero-variance behavior, the stratified yield interval and cap, missingness completion risk, 512×10 mock resources, and provisional ceilings. Paired t and bootstrap remain uncalibrated for the skew stress case; Step 4B-4 remains IN_PROGRESS. See `STEP4B4_FINAL_GATE_REVIEW.md`.


## Remediation v2 evidence

See `STEP4B4_FINAL_GATE_REVIEW.md` and the four Step4B4 v2 review documents. The v1 alternative coverage bug is corrected in v2; v1 raw is unchanged. The independent 13.4% skew Type I persists; thus Step4B4 remains open despite added stratified and 512×10 mock measurements.

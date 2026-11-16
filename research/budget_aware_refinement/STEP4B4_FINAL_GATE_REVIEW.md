# Step 4B-4 final gate review

Historical remediation review, superseded by `STEP4B4_FINAL_DECISION.md` (Option B adopted; Step 4B-4 design decision DONE, Step 4 remains IN_PROGRESS / NOT FROZEN).

**Gate: IN_PROGRESS; not READY FOR Step 4C freeze.** No Step 5 or confirmation SCM generation.

## What is evidenced

- Corrected alternative CI coverage reference: H0 true mean 0; shifted alternative true mean .10; rejection/power is a separate field. v1 JSON remains unchanged. Exact/near-degenerate cases and NumPy constant-rounding behavior have regression tests.
- Independent-seed paired-t skew calibration reproduces Type I 13.635% and 13.415%, with CI coverage 86.365% and 86.585%. This is severe-skew finite-sample calibration failure, not a t critical-value implementation error.
- Percentile and studentized bootstrap are also poorly calibrated under skew; studentized bootstrap has zero-SE/unbounded intervals for rare-loss scenarios. No mean-inference method selected.
- Stratified Q-yield estimate, conservative simultaneous exact interval, 0/1 boundary handling and future random-stratum rejection design are specified. Planning cap 362/1,036 uses explicit lower yield and conditional attainment probabilities.
- Normal-model precision/power, 0.1–2% missingness completion likelihoods, and resource measurements are available. 512×10 dummy matrix traversed existing Ridge/5-candidate recommendation path; no outcomes were evaluated.
- Failure/fallback mocks and restart deduplication mock were tested; provisional caps are stated with derivation, pending actual enforcement.

## Unresolved completion gates

1. A defensible calibrated mean test and CI for unknown/skewed/unbounded paired Regret differences. Known-variance Chebyshev and known-range Hoeffding require bounds not justified by the frozen outcome contract; they are too wide in the illustrative scenarios.
2. With n=200, normal-model two-sided power for delta .10 ranges from nearly 1 at SD .2 to .291 at SD 1. Nominal 95% CI half-width is .028/.042/.070/.098/.139 for SD .2/.3/.5/.7/1. The actual SD and tail behavior are unknown; these are not guarantees. Estimation-oriented planning should report the SCM-level interval width and uncertainty; a significance-only decision does not guarantee useful precision, and a non-significant result does not establish equivalence.

| paired-difference SD (normal model) | two-sided power for delta=.10 | nominal 95% CI half-width |
|---:|---:|---:|
| 0.2 | 1.000 | 0.028 |
| 0.3 | 0.997 | 0.042 |
| 0.5 | 0.804 | 0.070 |
| 0.7 | 0.520 | 0.098 |
| 1.0 | 0.291 | 0.139 |

3. Persistent type-cell missingness at 0.1% gives only 54.9% chance all 600 are observed under independent MCAR. Real dependence and resolution remain unknown; mock retries do not settle it.
4. The final study runner, GT evaluation, storage schema, and enforceable checkpoint/timeout/RSS/disk caps have not been implemented or stress tested. The provisional proposal is 30 min total, 2 s/unit, 512 MiB peak, 100 MiB disk; cannot claim execution readiness yet.
5. Reconcile the prior Step 0/Step 4 drafts prospectively and complete Step 4C code/config hashes and freeze validation.

## Decision

Keep Q-common/B=1/gamma=1/H2 and SCM-level D_i=(D_FN+D_FP+D_REV)/3 unchanged. Step 4B-4 remains IN_PROGRESS. Do not view confirmation data or begin Step 5. Next decision: justify a finite contrast range/variance bound from the frozen scoring contract, or explicitly retain a scientifically justified normal approximation with documented tail sensitivity, or stop confirmatory mean inference. Any route must be calibrated and frozen before confirmation.

Precision calculation settings SHA-256 `776de0f83edb53243c8b9129579f45ed5fa5a14adf9010f047cdd9c452ab545f`; artifact `step4b4_precision_v2.json`. The 0.10 standardized-loss threshold does not imply practical industrial value.

Development N=64 may inform nuisance variance and software diagnostics only. Before confirmation is opened, a prespecified precision algorithm must either approve candidate N=200 or stop/amend; no confirmation-driven increase is allowed.

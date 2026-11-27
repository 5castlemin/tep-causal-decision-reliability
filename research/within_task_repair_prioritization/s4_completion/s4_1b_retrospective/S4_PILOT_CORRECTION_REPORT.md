# S4 pilot correction report

## Provenance and checks

The private pilot run is `s4-independent-pilot-20261127-v1`, rooted at the approved local S4 artifact root. The pilot artifact manifest's 12 file entries and evaluator continuation lock's 9 checkpoint/result entries were compared byte-for-byte by SHA-256; there were no missing files or mismatches. Key bindings include:

- Inputs: `pilot_inputs_private.json` SHA-256 `34334f07b19d8b42691461e51b4865bd51878ed14f68cdf9d10dadde2bf54bf4`.
- Recommendations: `recommendation_manifest_private.json` SHA-256 `f93a560019b4c4b2d1592572d6d30fc5b91d63b099f5c9c2d00f7872dd3925cb`.
- Policy results: `policy_results_private.json` SHA-256 `347cc564358c76cc422a8e01ea001b33a7b4d7c091074a06a6ab93026cbf5904`.
- Candidate values: `candidate_values_private.json` SHA-256 `92cbe755033df446e0ea39088e24b6e4bc44ab501c60e609e6a0826df1e154fb`.
- Unit results: `unit_results_private.json` SHA-256 `ab88bab2fef3d84ffe17e4af6fff40fe857742902b0b9e5240f323ccdd604370`.

The retrospective runner additionally asserted the five input digests embedded in its committed contract before reading them. The two SHA-bound passes validate saved artifacts; they do not establish that the original S4 population rule matched Research C.

## Admission-rule correction

`RESEARCH_C_EXPERIMENT_CONTRACT_V1.md` §§29, 39 requires strict indirect-only eligibility, while Q-common support is secondary. The S4 scientific contract and `step4c1_proposal.build_structural_proposal()` use Q-common recipe support during admission. Thus “General” must be relabeled in interpretation as Q-common-conditioned. Historical lock, generated units and original public aggregates remain unchanged; no post-hoc reweighting is attempted.

## Paired-contrast direction

The stored pilot summary uses generic `better_left_count`/`worse_left_count`. For the contrast `M4_B2_minus_FULL_GREEDY_B2`, negative favors M4. Re-expressing the stored values explicitly:

| Cohort | Mean M4−Full Greedy | 95% interval | M4 better | Full Greedy better | Tie |
|---|---:|---:|---:|---:|---:|
| General | 0.000000 | [0.000000, 0.000000] | 0 | 0 | 32 |
| Opportunity-rich | −0.047459 | [−0.113196, −0.000589] | 4 | 1 | 27 |

This is a relabeling of the historical 2,000-replicate interval and counts, not a new evaluation. The B=1 and B=2 same-budget retrospective policy comparisons use 10,000 shared SCM bootstrap indices per cohort, seed `2026112702`, with pointwise percentile intervals.

## S3 diagnostic scope

The source selector in `s3_analysis.py` implements its M4 secondary tie-break. `finalize_saved_s3.py`'s saved candidate ranking report uses T score and canonical IDs without that secondary comparison. Its `tied_best_hit_rate` indicates whether the ex-post optimum is inside a score-tied set, not whether the deterministic selector chose an optimal edit. These quantities must not be conflated. No S3 cohort replay was performed for this report.

## Execution history

The first retrospective output attempt failed on heterogeneous CSV row fields before writing a complete result set; it generated no samples. The second run fixed CSV field union and same-budget pairing. A final source review then aligned the no-positive-T-gain branch with `s3_analysis.select_greedy_option()`: positive T gain is primary, M4 is the documented fallback, and no edit is selected if neither has positive gain. The final aggregate run at source commit `5dae72c34e61d89f9364c1acf8b8738ee83f7a0b` used the committed lock and saved private inputs. The cohort-policy regret aggregates were unchanged; graph/action redundancy was recomputed under the exact fallback. Earlier partial drafts are not evidence. No SCM, G0, observational sample, evaluator call or intervention response was generated in this reaggregation.

# Step 4 readiness audit — IN_PROGRESS

2026-11-10; base commit `42b7c2a0e9d6c11ed72aae4205c0bb7114221a2a`. Source: the 456 saved Step 3 supplement records; run `python -X utf8 research/budget_aware_refinement/step4_audit.py`. Recorded Windows-byte SHA-256 `67c9c6e975161b0767585396229a189dadb2ebb97c7e469293b450a7a3e1aec3` is checked; Git LF checkout is verified by reconstructing CRLF bytes. No new model or outcome was generated.

| Path | Positive regret | Recommendation changed vs no-edit | Prediction changed | Runs |
|---|---|---|---|---:|
| absent | yes | no | no | 248 |
| present | no | no | no | 114 |
| present | no | yes | yes | 94 |

All 248 without a path had constant predictions across five actions and selected k=0. No run had a path and positive regret; no other cell occurred. All results are from two dependent development structures and are not inferential frequencies. Missing FN, path loss and decision loss are confounded in these fixtures. FP=Y→A and REV=T→S are not evidence about task-relevant false or reversed relations; they do not establish that path-present effect-magnitude or sign errors are distinguishable. This is a property of these saved cases, not a theorem about all linear SCMs.

Before freezing the study, implement and validate a topology-only generator and enumerate feasible error recipes on *mock DAGs*, including task-relevant FP and REV, surviving paths, competing-sign paths, and peripheral controls. Predefine admission/failed construction denominators and avoid selection on effects or regret. Existing S1–S8/C01–C12 remain development-only.

Current blocking evidence: no verified generator or proof that the proposed quotas and retry rules are achievable without changing the target population; no measured runtime/memory bound for the required 48,720 candidate policy runs or Path-F1 implementation; 200-SCM power for 0.10 depends on an unknown between-SCM SD. Therefore the documents below are proposals, not a completed preregistration. Step 5 is not authorized by this draft. Do not inspect confirmation outcomes to resolve these gaps.

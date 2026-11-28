# S4 and S5 Closeout

Date: 2026-11-28. Branch: `research/s4-reconstruction-s5-validation`. This is a phase closeout, not the final whole-project narrative; the previously authorized Research E extension was not started.

## Study 2 — S4

The other-PC Unified S4 and S4-3 commits/private records remain unavailable and are classified as reported but not independently verifiable. On this PC, the saved 64-SCM pilot was retained, an 80-SCM reconstructed development cohort was run, and a separately seeded 160-SCM T5 replication was completed. These are distinct, post-hoc/conditional cohorts, not a restoration of the missing run.

The replication primary at B=1, gamma=0 was `T5 − M4 = −0.0086644`, paired 95% SCM interval `[−0.0203910, 0]`, with 4 better / 1 worse / 155 ties. The interval includes zero and its .010 target half-width was narrowly missed. T5 superiority and noninferiority were not established. Metric-candidate retrospective rankings varied by cohort and metric; the 63-subset best observed on the same data is exploratory and selection-optimistic. Direct outside-task edit diagnostics must not be paraphrased as evidence that unedited errors have zero value.

## Study 3 — S5

S5 used one pinned Station1 DRF semisynthetic DGP, a fixed 512-row training frame and 200 G0 corruption draws. It generated 22,000 recommendations and 24,995 intervention responses (plus one separately counted smoke response under the cap). No raw Research D vectors were recovered; S5 is a new conditional reconstruction, not exact Research D reproduction or a physical manufacturing validation.

At B=2, `loss(S0) − loss(M4) = +0.00685175` (45 better / 0 worse / 155 ties). G0-only 95% CI `[0.0048631, 0.0090237]`; action-MC interval `[−0.0088964, 0.0231993]`; two-source interval `[−0.0092609, 0.0227350]`. Only five of 200 G0s had at least two initially DAG-legal M4 candidates; T5 and M4 chose the same first edit in all 200. The mean graph-free association loss (0.867868) was slightly below M4 and involved zero edge edits, but the cost measure omits fitting and validation work.

## Scope, preservation and execution

No new experiment beyond the locked S4 reconstruction/replication and S5 run was started here. C–F historical contracts and protected assets were left untouched; raw unit records, response vectors, training data and recommendations remain outside Git. The private S5 archive is same-device only; no off-device backup is claimed. Exact source, input, response, aggregate and archive hashes are recorded in `outputs/s4_s5_integrity_manifest.json`.

S5 resource use was 373.3 seconds and 1,056,018,432 bytes peak observed process-tree RSS, within the locked 14,400-second and 4-GiB limits. The monitor was observational, not an OS sandbox.

## Verification and limitations

The focused S4/S5 tests and research-state check passed. A local full discovery run executed 477 tests: 469 passed, 3 failed, and 5 errored in the Windows environment. Failures/errors involved unavailable `jsonschema`, a frozen dependency fingerprint mismatch, protected raw-file byte differences in the Windows checkout, and a freeze test tied to the locked historical revision. These failures were not suppressed or repaired by changing frozen contracts. The frozen asset check passed in a temporary canonical-LF checkout. CI for code commit `22816b636ffd8857e62d517fcb3efcb148ad1b6a` succeeded (run `46045720886`); the final documentation commit requires its own remote CI result.

Research E extension remains outside this work. Findings are conditional on the stated synthetic/semisynthetic designs; they do not establish physical manufacturing benefit, universal T5/M4 priority, or generalization across independent external SCMs.

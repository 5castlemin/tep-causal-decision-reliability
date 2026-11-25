# Research D Development reproduction attempt

**Status: `DEVELOPMENT_PILOT_INCOMPLETE`. No reproduction data were generated.** This record documents one authorized runner invocation that stopped at a pre-fit audit-schema guard. The invocation was not repeated under the one-attempt instruction.

## Attempt record

- Run ID: `rd-development-reproduction-20261125-01`.
- Runner revision: `16445173224f405c88a32e8856435bbc4290876b`.
- Command: the bounded `run_development_pilot --mode pilot` invocation with the pinned `../assembly`, `../data`, existing outcome-blind structural preflight, original run lock, and v2 historical artifact audit. All outputs were directed to the ignored external `../data/local/research-d-semisen-reproduction-01/` directory.
- Result: exit before fitting the DRF or sampling any observations. The guard looked for the saved-artifact audit status at the document top level, while the actual schema stores it under `stored_artifact_audit.status`.
- Generated counts: 0 DRF fit samples, 0 learner-training rows, 0 recommendation rows, 0 intervention/evaluation rows, 0 G0 records, 0 bootstrap draws.
- No reproduction run lock, recommendation manifest, evaluator artifact, execution manifest, or summary was written. The external output directory remained empty.
- The historical audit itself passed; the failure was in the new runner's schema lookup. `validate_original_artifact_audit()` was corrected and covered by a regression test in commit `4007dbf5bdd4b57f7c9df413ec78243706e4a7f6`. This correction does not make the failed invocation a completed reproduction.

## Interpretation

The pilot's scientific conditions were not reached, so there are no new action responses, policy recommendations, losses, Primary/Secondary estimates, or intervals to compare. No result from the failed invocation can be described as a reproduction. The historical exploratory pilot remains separately audited for saved-row arithmetic and provenance; its raw evaluator response rows and independently reproducible bootstrap are unavailable.

Under the current authorization, the runner was not called again. A future invocation would require a new explicit authorization and a new run ID/lock, after review of the corrected pre-fit gate. Final evaluation data were not generated.

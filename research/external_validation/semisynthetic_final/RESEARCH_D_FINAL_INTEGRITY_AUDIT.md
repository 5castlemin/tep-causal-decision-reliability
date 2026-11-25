# Research D final integrity audit

**Audit status:** `PASS`; 27 independent checks passed.
**Research D execution source commit/tree:** `a6d751e3f157fca63a93931d62b9f7a9318c6cb5` / `fa1aaf635518e6d7a1f292f410185d220ccacc99`.

## Verified

- The contract, run lock, execution manifest, recommendation bytes/content, response manifest and analysis hashes agree with their bindings.
- Every listed execution file matches its locked byte SHA-256; Git HEAD and tree equal the pre-run commit/tree. The closeout/audit files were created after the final run and are not execution inputs.
- All 17,000 unique recommendation keys cover exactly 200 G0 IDs × five budgets × 17 policies; all 85 aggregate policy-budget cells were independently recalculated.
- Five 2,500-row float64 finite response vectors match the per-file SHA-256 and action order; total 12,500 rows. No action was resampled or vector overwritten.
- Independently recalculated action means, sample variances, bias-corrected losses, primary and M4 contrasts, policy-budget losses and edit costs match the saved analysis within `2e-13` numeric tolerance.
- Run lock fit diagnostic matched the predeclared 16-row digest, pinned graph has 6 nodes/7 edges, and stored node order matches fitted parent sampling order.
- Recommendation manifest was finalized and locked before evaluator-only response generation; response values were not used to change task, action set, target, scale, policies, budgets or sample sizes.
- External source/sample/reference and fixed learner-frame hashes match the approved manifest. Seed audit recorded zero collisions with scanned earlier records.
- Resource supervisor completed with no time or RSS breach; Research C contract, policies, ledgers and frozen manifests were untouched.

## Public/private artifact boundary

The repository contains only aggregate summaries, hash records, contracts, code and reports. The 1.46 MB raw run lock (including G0 records), 40 MB recommendation manifest, training CSV, fitted R/DRF object, evaluation manifest and five `.npy` response vectors remain outside Git in the ignored external data area. The response vectors are individually hash-addressed in `final_public_execution_manifest.json` and can be independently reanalyzed locally. No personal absolute paths are published.

The earlier response-blind resource benchmark completed at full synthetic dimensions; its own peak-memory counter returned zero and is explicitly marked invalid. The full supervised execution's independent process-tree RSS measurement is valid and is the basis for the resource cap result. This counter issue does not change any scientific result or the output integrity check.

## Important limitations

The full DRF fit is not proven identical by a 16-row diagnostic digest. The DRF was refit from the same pinned semisynthetic sample in the evaluator process. The actual final run was on Windows with documented R ABI/locale warnings, though it exited normally. The external psutil peak is sampled every two seconds, not a kernel-enforced address-space limit. Research D remains one conditional semisynthetic benchmark, not physical validation.

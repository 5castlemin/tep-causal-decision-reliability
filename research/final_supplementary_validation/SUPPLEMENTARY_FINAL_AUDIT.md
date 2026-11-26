# Final supplementary audit

## Scope and gate

Read-only reanalysis of original C cohort data and saved C policy trajectories; no SCM, G0, observations, interventions, or expert responses were generated. F-Lite stored evaluation rows were not changed. Research D private unit-level materials were not available and were excluded.

## Corrections and validation

- The weighted AUROC implementation was corrected after range validation found values above 1; the corrected held-out AUROC values are B=.856, E=.905, F=.961.
- Gamma-zero reproduction and deterministic fixtures passed.
- Paired contrasts and metric associations use common SCM resamples and SCM as the independent unit.
- SID/AID remain unrun because no verified compatible implementation/fixture was available.
- All public tables are aggregate only. Unit-level S1/S2 files are gitignored and stay local.
- The original C SQLite inputs still match all four locked source hashes after the audit; no ledger writes were performed.

## Local validation record

- `python -X utf8 -m unittest tests.test_supplementary_validation -v`: 8 passed.
- `python -X utf8 -m unittest discover -s tests -v`: 437 run, 435 passed, 1 failed, 1 errored. The error is the pre-existing frozen readiness test rejecting the local NumPy 2.4.6 / pandas 3.0.3 / NetworkX 3.6.1 fingerprint. The failure is a raw-byte hash mismatch for the frozen mock JSONL; its CRLF-normalized LF bytes match the expected manifest SHA-256 exactly. No protected files were changed to make either check pass.
- `scripts/check_research_state.py --write` and then without `--write`: pass.
- `scripts/check_asset_manifest.py`: local raw-byte check reports config hash mismatch for seven configs; each mismatch is Windows CRLF, and LF-normalized bytes match the frozen expected SHA-256. This is recorded as a local line-ending limitation, not a pass of the raw-byte command.
- `git diff --check`: pass.

The GitHub Actions result for the final pushed head must be reported separately. A remote CI pass does not imply the local frozen runtime was reproduced.

Detailed hashes, CI counts, exact commands, and any environment caveats are recorded in the integrity manifest and the accompanying closeout.

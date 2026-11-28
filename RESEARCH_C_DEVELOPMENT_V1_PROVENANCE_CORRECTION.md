# Research C Development v1 — G0 provenance correction record

**Classification:** `METADATA_ONLY_CONFIRMED`
**Run:** `development-20261123-seed-2026112301-v1`
**Correction version:** `research-c-g0-provenance-correction-v1`
**Prepared:** 2026-11-23 (Asia/Seoul)

## Original records retained

The G0 metadata lives inside each SCM result row at `fixture_metadata.g0_generation`; there is no standalone G0 file. The containing, unmodified cohort database is:

`C:\DAT_RESEARCH\research-c\development\development-20261123-seed-2026112301-v1\research_c_cohort.sqlite`

Original database SHA-256: `dd4264d5085adbabe9510bf99b564ec6c2b33e35d4eeb346a079cc4ccfb9b716` (21,344,256 bytes). SQLite integrity passed, no foreign-key issues were found, and all 64 SCM result row checksums verified. The corresponding proposal-stage database is `C:\DAT_RESEARCH\research-c\development\development-20261123-seed-2026112301-v1\research_c_proposal_stage.sqlite`, SHA-256 `1d00d1790788c342e15a81a0c405768e5e2a3e46ee75c57c0bbe34f8c0fcb584` (200,704 bytes); its SQLite integrity and proposal checksums also passed.

Per-SCM result checksum, G0 payload digest, and E2E input digest are preserved in the separate read-only audit snapshot `C:\DAT_RESEARCH\research-c\audits\development-v1-audit-v7.json`. The audit JSON file-byte SHA-256 is `a3285992c36aa046666a008e98c8016cf9e2715423cc06707c58f86c51872ee6`; its embedded canonical audit payload SHA-256 is `72a5a8c2ed6deb9f902324ef43631746b644194b9f95b92a20c18a5951b8bc31`. The read-only audit script SHA-256 is `84e55a5896ec81789d212c35c97bfff68261afe8d1f40d315169c1a08b245506`. These are audit references, not changes to the original rows.

## Corrected interpretation

All 64 G0 records contain these helper labels:

- `contract_status=PROPOSED_NOT_APPROVED`
- `test_or_cohort_use=not_authorized`

They are stale, hard-coded descriptive fields emitted by `g0_candidate.corrupt_graph_candidate`; they were not read by admission, policy scoring, SCM fitting, action recommendation, or the GT evaluator. The helper’s actual configured values in all 64 records were q=0.15, r=0.05, and conditional FN/REV/UNRES shares of 1/3 each, with zero redraws. The approval configuration and Manifest identify the Development cohort, approved status, master seed, proposal cap, runtime, resources, source commit/tree, and code hashes. The run’s code map matches the Manifest.

The research factory generated SCM parameters and observations, then called the outcome-blind G0 helper with the truth DAG, task, and dedicated G0 RNG seed. The helper does not receive coefficients, observations, intervention losses, or Regret. The approved Manifest binds `g0_candidate.py` at SHA-256 `b09a23176cb949c4f4755dbf3ac9b799621edb9f62f976be2f926aea3b0e9c1c`. The approval Gate was checked before proposal generation; it uses the approved configuration and Manifest and does not interpret these helper-level labels as authorization fields.

## Use in later analysis

Interpret the two fields only as stale labels. For authorization and provenance, use the run-bound approved config and Manifest above, together with the per-SCM seeds, graph/G0 digests, checksummed result rows, and their matching source commit/tree. Do not describe these legacy labels as the run’s actual approval state.

This correction is a separate annotation. It does not rewrite, normalize, or replace any raw G0 metadata or database row. No result was regenerated. The audit did not find evidence that the labels changed data generation or evaluation, so the preserved Development results may be used conditionally as exploratory results under their actual run provenance. Held-out remains blocked until the analysis bundle is locked and separately authorized.

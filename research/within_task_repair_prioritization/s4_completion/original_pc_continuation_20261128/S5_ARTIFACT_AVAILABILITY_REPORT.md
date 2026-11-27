# S5 artifact availability report — original PC

Status: `BLOCKED_UNAVAILABLE_PRIVATE_UNIT_ARTIFACTS_AND_RUNTIME` (2026-11-28).

## Existing Research D run

Public provenance identifies `rd-external-final-20261125-01`, execution commit `a6d751e3f157fca63a93931d62b9f7a9318c6cb5`, run-lock SHA-256 `8cc953098352ae8ff97ffc6618cd5353ee6565a9d8300b3143b0b45d08acdda2`, recommendation raw SHA-256 `20453dc69698ce21fb7aa0d32eac242301bc816486540e13ca677a6df63cc738`, training numeric digest `bcca5e56b01dd8cc59d227272906fcee6f9160897e9be2179bd9751619b4bc39`, training CSV SHA-256 `dfc77931debb528db05defaf8302198048a04337d2d20a95ab51e5b1685a7094`, and action-vector hashes listed in `research/external_validation/semisynthetic_final/final_public_execution_manifest.json`.

These are expected historical identities, not hashes of locally present files. In the approved local root the approved local Research D artifact root, the only file is `final-reaudit-20261126.json`, SHA-256 `6fa458199ea814a61248a1088bbe5a3b96a586916516c02a1dd6b54c0331292b`. Its recorded checks concern a prior audit. It does not include the training frame, G0 records, recommendation records, DRF object, response vectors, final run lock or private evaluation manifest. No unit-level replay is currently possible.

## Reconstruction path assessment

The exact pinned source/data configuration is documented publicly (causalAssembly 1.2.1, commit `8da3729e6383f0e1cbe7740bb6ab7ac4977ac7f9`, Station1). However the observed environment lacks R/Rscript, `rpy2`, and the historical numerical package fingerprint. The required DRF runtime is therefore not executable in this checkout. No setup/install, download, refit or sampling was attempted, consistent with avoiding repeated environment restoration. S5 cannot be classified as run or as a historical reproduction.

No final/evaluation seeds or response data were generated. A new reconstruction, if later enabled, must use a new run ID, a pre-outcome lock and the approved caps, and be called a new conditional semisynthetic evaluation rather than exact reproduction of the historical D run.

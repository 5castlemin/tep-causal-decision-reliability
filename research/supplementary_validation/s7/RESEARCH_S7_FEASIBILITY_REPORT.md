# Research S7 — Feasibility Gate

**Feasibility state:** `S7_ENVIRONMENT_ELIGIBLE_WITH_LIMITATIONS`
**Decision:** proceed with the locked two-station-task evaluation, conditional on one full causalAssembly DRF over the official joint assembly-line DAG.

## Verified source and data

The local causalAssembly checkout is at pinned commit `8da3729e6383f0e1cbe7740bb6ab7ac4977ac7f9` (version 1.2.1; AGPL-3.0 source license). The official raw reference file SHA-256 is `f015fbe1a1955446169ecdc9251d99792f5c49c2343699ab30e7fdd2960595ae`; the official full-line 500-row source sample SHA-256 is `383e7bac70eae14d9707bee00aeda0a29d649445c6e73f08fd2bc548703f461c`. The reference file's raw hash differs from the normalized/canonical hash used by the historical Research D manifest, so S7 locks the actual raw file and pinned source commit instead of claiming that the historical byte representation matches. Selected station CSV hashes are in the execution lock. Upstream data and fitted objects are not copied into Git.

The official full graph has 98 nodes, 485 directed edges, and is a DAG; the paired full-line source frame has 500 rows and 98 finite columns. Station2 has 34 nodes/77 within-station edges and Station3 has 16 nodes/11 within-station edges. Both contain directed cross-station parent relationships in the official joint graph. They are therefore not fitted as isolated station DAGs. The selected tasks retain the official full joint graph and fit all 98 mechanisms, preserving cross-station parents.

## Outcome-blind selection

The deterministic rule is: among each station's strictly indirect ordered pairs, choose the pair with no directed backdoor support in the full graph if possible; then minimize station-local directed path length; then break ties lexically by action and target IDs. This selects Station2 `Station2_mp_13 → Station2_mp_33` and Station3 `Station3_mp_43 → Station3_mp_45`, each with a two-edge station-local directed path and no detected full-graph directed backdoor support. Selection uses only the official graph, before any DRF fitting, G0 generation, or policy outcome.

## Important qualification

These are two station-specific task strata evaluated in one fitted joint assembly-line DRF DGP, with a shared training frame. They are not two independent DGPs or two independent manufacturing populations. This is a new conditional semisynthetic reconstruction, not an exact Research D rerun, and not physical manufacturing intervention validation. The full graph's 485 edges and the fixed 15%/5% corruption mechanism imply a substantially larger corruption opportunity set than Station1; the fixed mechanism is not tuned after results.

## Runtime eligibility

The existing S5-only runtime is present: Python 3.11.15, R 4.5.3, `drf` 1.3.1, `rpy2` 3.6.2, NumPy 2.2.6, pandas 2.3.1, NetworkX 3.4.2, and causalAssembly 1.2.1. The R package check reports `drf` installed and the pinned causalAssembly source imports from its local checkout. Known Windows `sh`/locale warnings remain. The locked run has cumulative caps of 14,400 seconds and 4 GiB process-tree RSS; no fit, training frame, G0, recommendation, or response rows have been generated at this feasibility-gate revision.

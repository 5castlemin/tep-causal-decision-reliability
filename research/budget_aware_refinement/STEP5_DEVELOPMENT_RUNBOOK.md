# Step 5 Development Cohort Runbook (Preflight Only)

This operational handoff does not amend the frozen Step 4 contract. It is outside the frozen content manifest because it records execution procedure, not research settings or implementation. It authorizes no run by itself. PR #38 must first be integrated by a separate explicit decision; the operator must then bind the actual clean main commit/tree and rerun production readiness.

## Cohort identity and RNG

- Cohort namespace: `development`.
- Run/output identity: `step5-development-v1`.
- Master seed: `20261116`, fixed before outcomes are observed. Do not change it to improve yield or results. If this run is interrupted, resume the same output root with the same seed, code, settings, manifest, commit/tree, and inputs.
- Confirmation namespace is `confirmation`; it uses a separate cohort RNG namespace and separate output root. Do not initialize, inspect, or reuse confirmation proposal IDs, RNG keys, registry rows, or raw records during Step 5.
- Proposal IDs follow the orchestrator's deterministic sequence `development:proposal-000001` through the configured cap. The cap is 386; stop at 64 registry admissions or the cap, whichever comes first. Post-admission failures count against the target and are never replaced.

## Preflight gate

1. Obtain explicit authorization for the development cohort and integrate PR #38 through the repository's normal review process. Do not run from an unmerged feature branch.
2. Use the frozen Windows `Windows-10-10.0.26200-SP0`, CPython 3.11.15 environment and pinned NumPy 2.4.3, pandas 3.0.1, and NetworkX 3.6.1.
3. Check out the approved main revision, verify a clean worktree, record `git rev-parse HEAD` and `git rev-parse 'HEAD^{tree}'`, and verify every file in `step4c2_final_freeze_manifest.json` plus the operational settings SHA-256.
4. Run the non-generative readiness check:

   ```powershell
   python -c "import subprocess; from research.budget_aware_refinement.step4c2_freeze import assert_production_ready; c=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(); t=subprocess.check_output(['git','rev-parse','HEAD^{tree}'],text=True).strip(); assert_production_ready(expected_commit=c,expected_tree=t); print('production readiness passed; no proposal generated')"
   ```

5. Use a dedicated output root outside the repository, for example `C:\DAT_STEP5_RUNS\step5-development-v1`. Confirm available space is at least the configured 1 GiB floor and the root is not shared with any other cohort.
6. Record the approved commit/tree, manifest/settings hashes, environment fingerprint, seed, cohort name, and output path in the execution ticket before launch.

## Launch and resume

Only after the preflight and separate authorization, run:

```powershell
python -m research.budget_aware_refinement.run_step4c2_research_cohort `
  --cohort development `
  --master-seed 20261116 `
  --output-root C:\DAT_STEP5_RUNS\step5-development-v1 `
  --expected-commit <approved-main-commit> `
  --expected-tree <approved-main-tree>
```

On interruption, use the same command, same output root, and same bindings. The runner restores proposal position, registry/ledger state, resource counters, and RNG bindings. A changed revision, tree, manifested file, settings, runtime, or input must fail closed; do not copy records into a new run to bypass that check.

## Stop states and denominators

- Normal stop: 64 registry admissions reached. Report proposals attempted, Q-common rejections, registry admissions, generation successes, full FN/FP/REV evaluation vectors, complete SCM composites, failures, and shortfall separately.
- Proposal cap stop: report shortfall at 386 attempts. Do not add a new seed or alter strata after observing the yield.
- Time, sampled RSS, per-ledger/cohort storage, minimum-free-space, timeout, I/O, learner, recommendation, numeric, or GT failure: preserve the failure event and denominators; do not call it success and do not replace an admitted SCM. A resource cap is a safe stop, not a quota or worst-case guarantee.
- Any missing/nonfinite type result prevents that SCM composite. Do not impute zero or silently use a type-specific denominator for the primary composite.
- Option B permits descriptive estimates and sensitivity summaries only; do not report confirmatory superiority/equivalence claims.

## Checkpoint custody and raw-data protection

Keep the registry, WAL, ledgers, and checkpoint files under the dedicated run root. Never edit raw ledgers in place. At a planned backup, stop the runner cleanly, use SQLite's online backup API for `registry.sqlite` (do not copy a live database while its WAL is changing), copy the complete ledger/checkpoint tree, and write a SHA-256 inventory for both source and backup. Resume only from the canonical run root; retain backups read-only as recovery copies. Record any recovery action and never discard failed proposals or rejected denominators.

## Development/replication boundary

Step 5 development (`N=64`) is for development exploration and quality assessment under the frozen rules. It does not license silent changes to policy, budget, weights, population, or outcomes. A genuine implementation defect requires preserving the old run, documenting its impact, and issuing a new version/freeze; invalidate the development cohort when the defect compromises its contract. Step 6 (`N=200`) is a held-out replication under the unchanged frozen contract and separate RNG/ID/output namespace. Do not generate or inspect Step 6 data while Step 5 is running or being reviewed. Neither cohort is confirmatory superiority evidence under Option B.

## Status

This runbook is a preflight document only. No cohort was started by writing it. PR #38 remains Draft/unmerged; production readiness is not itself research execution authorization.

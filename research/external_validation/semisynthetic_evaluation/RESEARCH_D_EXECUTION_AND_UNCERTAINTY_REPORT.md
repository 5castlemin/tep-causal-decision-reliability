# Research D Execution and Uncertainty Report

## Execution record

The Development Pilot used the approved Research D feature branch and the pinned causalAssembly source/data already present in local ignored work directories. The exact pre-evaluation lock and Recommendation lock are linked by SHA-256. Raw public source data, generated 512-row training frames, fitted R objects, recommendation manifest, and raw evaluator output remain under ignored local paths or memory; only code, hashes and aggregate summaries are tracked.

| Artifact | Binding value |
|---|---|
| Development run lock SHA-256 | `9f3c63c5aa33123a0619511bfc5cc129b887200700227c5fec4d2f4c2b88a404` |
| Recommendation lock SHA-256 | `dd0edcef3a060d7f18857fb2a06df5b080231ee28f712100e87f9485b26c7c9b` |
| Development G0 manifest SHA-256 | `03a238576ca3e25af47ac30bf818e86dbf06808d1c713924aed8956f59245a91` |
| Local evaluator artifact SHA-256 | `6d92f8dbed13c0b82da012b7366847b5ca5ade7fe8463d48f87a4f4fa3d68eb4` |
| Pinned semisynthetic sample SHA-256 | `afc079bfca962a4746afd316713743d7702ebc7ea00f98255cd8289d72ecef0e` |
| Pinned reference SHA-256 | `86378888c66089aebb94616dce121b5e8400414112eb221b78dff3a4ca84cab8` |

The source is causalAssembly `1.2.1` at `8da3729e6383f0e1cbe7740bb6ab7ac4977ac7f9`, declared AGPL-3.0. Prior source review found no separate per-file data license override. No external source code or source data was copied into this repository; attribution and license review remain necessary before any later redistribution.

## Commands actually run

Repository test environment:

```text
..\ci-venv\Scripts\python.exe -m unittest tests.test_research_d_float_hard_do_adapter tests.test_research_d_semisynthetic_pipeline -v
```

Outcome-blind structural preflight:

```text
$env:R_LIBS_USER = (Resolve-Path ..\causalassembly-preflight-venv\R-library).Path
..\causalassembly-preflight-venv\Scripts\python.exe -X utf8 -m research.external_validation.semisynthetic_evaluation.run_development_pilot --mode structural --source-root ..\assembly --data-root ..\data --output research/external_validation/semisynthetic_evaluation/structural_preflight.json
```

Disposable, non-reusable timing smoke:

```text
..\causalassembly-preflight-venv\Scripts\python.exe -X utf8 -m research.external_validation.semisynthetic_evaluation.run_sampling_performance_smoke --source-root ..\assembly --data-root ..\data --rows 8 --seed 91420901
```

Bounded Development Pilot:

```text
..\causalassembly-preflight-venv\Scripts\python.exe -X utf8 -m research.external_validation.semisynthetic_evaluation.run_development_pilot --mode pilot --source-root ..\assembly --data-root ..\data --output research/external_validation/semisynthetic_evaluation/RESEARCH_D_DEVELOPMENT_PILOT_RESULTS.md --structural research/external_validation/semisynthetic_evaluation/structural_preflight.json --lock research/external_validation/semisynthetic_evaluation/development_run_lock.json --recommendations ..\data\local\research-d-semisen-pilot\recommendations.json --evaluation ..\data\local\research-d-semisen-pilot\evaluation.json --summary research/external_validation/semisynthetic_evaluation/development_pilot_summary.json --r-library ..\causalassembly-preflight-venv\R-library --timeout-seconds 21600
```

Outcome-blind locked G0 audit and post-run aggregate checks:

```text
..\ci-venv\Scripts\python.exe -X utf8 -m research.external_validation.semisynthetic_evaluation.write_development_g0_manifest --structural research/external_validation/semisynthetic_evaluation/structural_preflight.json --run-lock research/external_validation/semisynthetic_evaluation/development_run_lock.json --recommendations ..\data\local\research-d-semisen-pilot\recommendations.json --output research/external_validation/semisynthetic_evaluation/development_g0_manifest.json
..\ci-venv\Scripts\python.exe -X utf8 -m research.external_validation.semisynthetic_evaluation.summarize_development_artifacts --recommendations ..\data\local\research-d-semisen-pilot\recommendations.json --evaluation ..\data\local\research-d-semisen-pilot\evaluation.json --output research/external_validation/semisynthetic_evaluation/development_policy_diagnostics.json
..\ci-venv\Scripts\python.exe -X utf8 -m research.external_validation.semisynthetic_evaluation.merge_policy_diagnostics --summary research/external_validation/semisynthetic_evaluation/development_pilot_summary.json --diagnostics research/external_validation/semisynthetic_evaluation/development_policy_diagnostics.json
```

The evaluator subprocess completed with `PASS`, 1,280 rows and 151.793 seconds of sampling. Total post-lock wall time was 197.766 seconds, inside the six-hour cap. Its deterministic refit check matched exactly. Windows emitted `sh` not found, R ABI fallback and locale startup warnings; the successful executions returned exit code zero. Peak native R memory was not measured.

The earlier disposable 8-row smoke took 49.382 seconds, while the actual batched 256-row-per-action evaluator averaged 30.359 seconds/action. The discrepancy shows substantial call/batch overhead and cautions against extrapolating timing from the tiny smoke. At the observed 256-row batch rate, a future 2,500-row/action proposal would take roughly 25 minutes for five actions, but that is a planning estimate only.

## Uncertainty decomposition

Primary Development mean `Δ_D=0.003338` has a G0-only percentile interval `[0.000587, 0.007372]` when the evaluation action loss table is held fixed. That interval omits the dominant evaluator sample uncertainty and should not stand alone. Resampling action evaluation rows while holding G0s fixed gave `[-0.058536, 0.063438]`. The paired two-source bootstrap, which resamples G0s and action rows while sharing each action's resampled loss across every policy and seed, gave `[-0.065322, 0.075465]`.

The two-source 95% half-width is about `0.0704` standardized target-loss units. The action-Monte-Carlo-only half-width is about `0.0610`. The G0 SD estimate `0.01087` is conditional on one DGP and one learner sample; it does not include training-sample or generator-fit variation. The 2,000 bootstrap replicates quantify resampling uncertainty under the locked model and do not create 2,000 independent external mechanisms.

## Proposed final precision planning (not approved)

For contract review, a candidate precision goal is a two-sided 95% Monte Carlo half-width no larger than `0.02` standardized-loss units for the Primary mean contrast. This is a proposed reporting tolerance, not chosen from the pilot effect sign or significance; it is approximately 27% of the historical Research C Held-out point estimate `0.074836`. Under a first-order `1/sqrt(n)` scaling from the pilot action-MC half-width, the evaluator needs about `256 × (0.0610/0.02)^2 ≈ 2,380` rows per action. A rounded planning value of 2,500 per action (12,500 total across five actions) gives a modest buffer. The exact number should be revalidated with a prespecified pilot-based simulation of the locked two-source estimator before final approval; do not tune to the external contrast estimate.

An initial final G0 count of 200 can be considered for the conditional G0 seed distribution, but it is not 200 SCMs, graphs, DRF fits, or physical systems. A final evaluation plan should preserve the paired G0/action-loss structure, use 10,000 bootstrap replicates for Monte Carlo stability, use new final train/G0/evaluator seed namespaces, and state clearly that generator-fit variability remains outside the primary scope. A separate training-seed sensitivity may be proposed, but it must not be blended into the primary without an explicit contract change.\n

## Post-run source integrity note

After the pilot artifacts were committed, a documentation whitespace cleanup accidentally replaced the final newline of pipeline.py with the two literal characters \n, making the module fail to import. This was a post-run file-formatting error, not a pilot execution failure. The syntax was repaired immediately; no executable statement changed. However, the current source SHA-256 (5a36774cca62dd3b33bb61e2d9aff74e1a90f72a665d66b54edf153902be150f) no longer matches the pre-run code digest recorded in development_run_lock.json (cbb830bc9421bbde851183868037ddc7681dbbac72c1847feb662cf75ae51291). For strict byte-level provenance, treat the pilot lock as not byte-reproducible until a fresh bounded development run under a newly locked code digest is approved; the reported pilot aggregates remain archived as exploratory development output and are not promoted to final evidence.

## Superseding follow-up: same-condition Development reproduction

The preceding post-run source-integrity statement describes the historical pilot lock only. It is not the final status of the separately authorized reproduction. The reproduction used a distinct run lock and source identity at commit `4f0bda50816b2fa08b8bf8cce31fc3fea44582eb`, tree `595379c1020649c9bbaec3b9794e0937aa2a2fa1`, with a clean worktree at lock and evaluator completion. Run-lock SHA-256: `1476308f85c01b0c02941275d6b37d2d8ea973a0487f33efa4cff8a40abad8fa`; execution-manifest SHA-256: `2c291c1de94feb56c472addf68b59e8a70ffe949411af509e728a70bfee42e75`.

The run reused the preserved, exact 512-row training frame after verifying its raw CSV and numeric digests; it reconstructed/compared all 32 deterministic G0 inputs. Recommendations (2,720 rows) were locked before the evaluator subprocess. The evaluator refit check matched its 16-row digest and sampled 256 rows at each of five actions (1,280 total), in 350.868 seconds of evaluator sampling; fit took 34.842 seconds and post-lock runner wall time was 463.614 seconds. The response vectors are retained locally, outside Git, with SHA-256 `251ee7d5fbfb6ec473fa79229ac8741af0ce6d4a325a0377d5f9d3fb388ca803`.

The independently recomputed Primary from those vectors is `+0.0033381254737865317`; the paired two-source interval is `[-0.06532199359741737, 0.07546540523357707]`. All five action summaries/losses, all 2,720 recommendations, and the three new bootstrap intervals match the evaluator output; action hashes/means/variances also match the saved historical summaries. Historical raw evaluator rows remain unavailable, so historical bootstrap resampling was not independently re-run. The final gate is `READY_FOR_EXTERNAL_FINAL_CONTRACT_REVIEW`; no final sample or seed was generated.

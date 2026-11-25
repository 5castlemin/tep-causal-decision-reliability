# Research D Development reproduction record

**Current status: `COMPLETED_AND_REPRODUCED`; final gate: `READY_FOR_EXTERNAL_FINAL_CONTRACT_REVIEW`.** The successful run was a same-condition Development reproduction, not the final evaluation. No final seeds or evaluation samples were generated. The first historical failed run and the post-training lock-check failure are retained below.

## Attempt history

| Attempt | Stage and result | Generated research material |
|---|---|---|
| Earlier run `rd-development-reproduction-20261125-01` | Failed before fit at the historical audit JSON status-path check; correction is in `4007dbf5bdd4b57f7c9df413ec78243706e4a7f6`. | 0 training rows, G0s, recommendations, evaluator rows or bootstrap draws. |
| Run `...-02`, runner attempt at commit `a13e9170ff7544561d7ac6d30a72610b68a5c203` | Passed fit/training and deterministic generation, then stopped because `action_grid.support_checks` inherited nondeterministic descendant-set order. The five action values and all other scientific conditions matched. | 48 diagnostic draw rows, one 512-row training frame, 32 deterministic G0 records; 0 recommendations and 0 evaluator rows. |
| Run `...-02`, recovered continuation at commit `4f0bda50816b2fa08b8bf8cce31fc3fea44582eb` | Fixed the metadata ordering; revalidated and reused the exact prior training frame and G0 request. Lock comparison passed and the one complete evaluation finished. | No additional training rows; 2,720 recommendations and exactly 1,280 evaluator rows. |

The failed-run learner frame was not discarded or replaced. Its raw CSV SHA-256 is `dfc77931debb528db05defaf8302198048a04337d2d20a95ab51e5b1685a7094`; exact round-trip numeric SHA-256 is `bcca5e56b01dd8cc59d227272906fcee6f9160897e9be2179bd9751619b4bc39`, matching the original Development lock. The preserved recommendation input was hash-checked and then compared with the deterministically reconstructed Station1 graph, actions, nodes, edges and 32 G0 records. The recovery manifest is external and its hash is recorded in the reproduction preflight.

## Locked conditions and provenance

- Run ID `rd-development-reproduction-20261125-02`; mode `development_reproduction_only`.
- causalAssembly `1.2.1`, source commit `8da3729e6383f0e1cbe7740bb6ab7ac4977ac7f9`; pinned public sample SHA-256 `afc079bfca962a4746afd316713743d7702ebc7ea00f98255cd8289d72ecef0e`; official reference SHA-256 `86378888c66089aebb94616dce121b5e8400414112eb221b78dff3a4ca84cab8`.
- Official Station1 graph: 6 nodes / 7 edges; benchmark virtual task `Station1_mp_0 → Station1_mp_1 → Station1_mp_4`; five original action values unchanged.
- Target `15.460000542160238`; scale `1.565469292160237` (`mean(Y_train)+SD(Y_train)`, sample SD, `ddof=1`). Learner training rows: 512, exact prior frame reused.
- G0 seeds `702001–702032`; 17 existing policies; budgets `0–4`; B=2 S0−Full Greedy is Primary; M4 remains Secondary.
- Evaluator: 256 rows/action × 5 actions = 1,280 rows; seed root `3218321017`; 2,000 paired/two-source bootstrap replicates, seed `91420263`; bias-corrected squared mean loss, no truncation.
- Runtime: Python 3.11.15, R 4.5.3, DRF 1.3.1, causalAssembly 1.2.1, rpy2 3.6.2, NumPy 2.2.6, pandas 2.3.1, NetworkX 3.4.2, Windows 10.
- The immutable source lock records commit `4f0bda50816b2fa08b8bf8cce31fc3fea44582eb`, tree `595379c1020649c9bbaec3b9794e0937aa2a2fa1`, and a clean worktree. Run-lock raw SHA-256: `1476308f85c01b0c02941275d6b37d2d8ea973a0487f33efa4cff8a40abad8fa`; execution manifest SHA-256: `2c291c1de94feb56c472addf68b59e8a70ffe949411af509e728a70bfee42e75`.

## Original versus reproduced evidence

| Check | Result |
|---|---|
| Same-seed DRF diagnostic digest | Exact match: `11f3a13511bfcf405c8ab167aced154a01fd068711a1fee06fca89e6362856f1`. This is a 16-row refit diagnostic, not proof of full DGP identity. |
| Learner-training numeric digest | Exact match to historical lock. |
| Action grid, target and scale | Exact match. |
| G0 seed IDs and initial graph hashes | Exact match for all 32. |
| Recommendations | 2,720/2,720 keys match; zero differences in recommended action, edit cost, initial graph hash or repaired graph hash. |
| Action response vectors | All five float64 vector digests match the historical stored summary digests; each vector has 256 rows. Reproduction-only vectors are retained externally with SHA-256 `251ee7d5fbfb6ec473fa79229ac8741af0ce6d4a325a0377d5f9d3fb388ca803` (11,828 bytes). |
| Per-action summaries and losses | All five response means, sample variances, response hashes and bias-corrected/plugin losses match exactly. |
| Primary and uncertainty | Primary point `+0.0033381254737865317` matches exactly. Independent recomputation from the saved vectors reproduces the evaluator point and all three intervals. |
| M4 and graph-free baseline | M4/Full Greedy chose the same action in 32/32 B=2 seeds; M4−Full Greedy mean loss contrast `0`. The graph-free association baseline matches the historical summary. |

The historical raw response rows were deleted. Therefore historical response means and vector hashes can only be checked against their saved summaries, and the historical bootstrap itself cannot be independently rerun. The reproduction bootstrap was independently recalculated from the new evaluator-only vectors and exactly matched the new evaluator JSON; its equality with the historical saved interval is a comparison to retained historical aggregate evidence, not a fresh bootstrap from historical rows.

## Development results

- Primary `Δ_D = Regret(S0) − Regret(Full Greedy)` at B=2: `+0.0033381254737865317` standardized loss units.
- Paired two-source 95% percentile interval: `[-0.06532199359741737, 0.07546540523357707]`; it includes zero. G0-only interval: `[0.0005872563106569806, 0.007371723023403182]`. Action-Monte-Carlo-only interval: `[-0.05853612495588549, 0.06343823975974354]`.
- M4−Full Greedy B=2 mean contrast: `0`; mean edit costs are Full Greedy `1.15625`, M4 `0.1875`.
- All five evaluator means are below the training-only target `15.460000542160238` (observed means `13.8242–14.0352`). This flags a target-support limitation in this finite evaluation sample; it does not prove population-level target infeasibility and is not a basis to change the task or target.
- Evaluator sampling time `350.868` seconds, evaluator DRF fit `34.842` seconds, runner post-lock wall time `463.614` seconds. Windows emitted known `sh`/cffi ABI/locale warnings; the evaluator and runner returned success. Peak memory was not instrumented by the lock.

These data describe one fixed fitted DRF, one training frame and 32 graph-corruption draws. The 32 G0 seeds are not 32 independent external SCMs. They do not establish physical manufacturing effects, generator-fit uncertainty, or deployment readiness. Small or uncertain policy effects do not invalidate the technical reproduction.

## Evaluator-only response data and independent analysis

The 1,280 response values are saved only in the ignored external work directory as `response_vectors.npz`; raw response vectors, training CSV, recommendation JSON, evaluator JSON and fitted R objects were not copied into the public repository. The tracked comparison contains hashes and aggregate results only. The reproduction analyzer included in the locked run had a post-run axis-order bug; its bytes were preserved. A separate `analyze_development_reproduction_v2.py` then fixed the axis handling and historical summary lookup, reproduced the evaluator Primary and intervals from the saved NPZ, and passed a regression fixture. No evaluator sampling was repeated during this analysis repair.

## Final gate

`READY_FOR_EXTERNAL_FINAL_CONTRACT_REVIEW`. This is not final study approval. The final sample count and whether to freeze the existing training frame or use a fresh final training frame remain for user review. No final seeds, final learner frame, final evaluator response or final evaluation artifact was generated.

# Research D final external semisynthetic evaluation contract

**Status: locked for the authorized final evaluation.** Study type: `CONDITIONAL_EXTERNAL_SEMISYNTHETIC_ROBUSTNESS`. This is one fixed DRF-based DGP refit to causalAssembly's pinned public semisynthetic sample and official Station1 benchmark graph. It is not physical manufacturing validation, a complete physical-GT claim, a population of independent SCMs, or deployment evidence.

## Fixed source, graph, learner and task

- causalAssembly 1.2.1, source commit `8da3729e6383f0e1cbe7740bb6ab7ac4977ac7f9`; public sample SHA-256 `afc079bfca962a4746afd316713743d7702ebc7ea00f98255cd8289d72ecef0e`; reference SHA-256 `86378888c66089aebb94616dce121b5e8400414112eb221b78dff3a4ca84cab8`.
- Station1 reference has 6 nodes and 7 directed edges. Reference-relative discrepancies are not asserted to be physical-GT errors.
- Refit the fixed DRF with seed `91420261`; require the existing 16-row refit diagnostic digest `11f3a13511bfcf405c8ab167aced154a01fd068711a1fee06fca89e6362856f1`. This diagnostic does not establish identity of the full fitted DGP.
- Reuse the exact Development learner frame: 512 rows, numeric SHA-256 `bcca5e56b01dd8cc59d227272906fcee6f9160897e9be2179bd9751619b4bc39`, raw CSV SHA-256 `dfc77931debb528db05defaf8302198048a04337d2d20a95ab51e5b1685a7094`; parse with pandas `float_precision='round_trip'`.
- Task: virtual hard-do of `Station1_mp_0`, target `Station1_mp_4`, reference path `mp_0 → mp_1 → mp_4`, strict indirect-only relative to benchmark reference. Actions, in order: `0.000155911358968`, `0.0001724093665238`, `0.00018679686613765`, `0.00020263502221978`, `0.00022589388613683002`.
- Target `15.460000542160238`, scale `1.565469292160237`; fixed to training-only `mean(Y_train)+SD(Y_train)` and sample SD (`ddof=1`). No physical operating interpretation is claimed.
- Reuse Research C Ridge learner (`alpha=1`), M1–M4, task zone, FP Rule A, G0-fixed opportunity normalization, FN/FP/REV/UNRES definitions, q=.15, r=.05, equal true-error mix, fair FP orientation, DAG rejection without redraw, atomic edit cost 1, S0, all 15 nonempty metric subsets, Canonical Oracle, and the graph-free X–Y association baseline. All 17 policies and B=0–4 are retained. Canonical Oracle is a structure-only comparator, not a regret oracle.

## Final sample and randomization contract

- Run ID `rd-external-final-20261125-01`.
- New G0 IDs `703001..703200`; all remain in the denominator including no-error, no-task-zone-error, DAG-rejected, no-op, duplicate-repair and unused-budget cases. These are graph-corruption draws under one DGP, not 200 SCMs.
- G0 master seed derivation: first 32 bits, big-endian, of SHA-256 over `research-d-external-semisynthetic-final-v1|g0|<seed_id>`; pass to the unchanged Research C corruption implementation. Evaluator streams use the same namespace with label `action|<index>|<repr(action)>`; bootstrap uses label `bootstrap|primary-two-source`.
- 17,000 recommendation rows (`200 × 5 budgets × 17 policies`); one common action-loss table; 2,500 hard-do response rows per action (12,500 total); 10,000 bootstrap replicates. No new learner training rows.
- The actual generated 32-bit streams must be unique within stream families and disjoint from all recorded Development, Reproduction, Preflight and adapter-Smoke seed values. Fit seed remains the intentionally fixed `91420261`.
- Primary at B=2: `Δ_D = L(a_S0) − L(a_FullGreedy)`; positive favors Full Greedy. `L_bc(a)=((mean_a−target)^2−var_a/n)/scale²`, sample variance `ddof=1`, no negative truncation. Same action always maps to the same shared loss.
- Report G0-only, action-MC-only and two-source paired 95% percentile intervals. Resample G0 rows as paired units; resample within each independent action stream; each replicate's shared action loss table is applied to all policies/G0s. Chunk size is fixed at 128 replicates. Action-MC half-width target ≤.020 and combined half-width target ≤.025 are reporting precision goals, not meaningful-effect thresholds. Do not expand samples if missed.
- Required secondary/descriptive outputs: M4−Full Greedy contrast and interval, repair-cost means/paired differences/reduction, recommendation and repaired-graph agreement, S0 action changes, improved/worse/tied cases, task/off-task error-count changes, no-op and unused-budget rates, all policy-budget loss/cost curves, graph-free baseline, and prespecified descriptive G0 strata.

## Information boundary and execution controls

1. Before final evaluator response generation, lock source/data/code hashes, exact training digest, task/actions/target/scale, seed derivation and IDs, all G0s, all recommendation inputs, policy/budget grid, sample sizes, bootstrap, outputs and resource limits.
2. Generator/recommendation preparation may use pinned source and training data. Recommendation worker receives training data and graph/task inputs only; it does not receive a fitted DRF, evaluator streams or responses.
3. Hash-lock all 17,000 recommendations. Only then may evaluator-only code refit the pinned generator and draw the five fixed actions.
4. Save each completed action vector atomically outside Git immediately after its hash and schema checks. Existing vectors cannot be overwritten or silently regenerated.
5. Independently analyze the saved vectors; do not rerun sampling to repair analysis.
6. Enforce a 7,200-second wall limit and 4-GiB aggregate process-tree RSS limit with a Windows process-tree monitor; action sampling is serial. Stop and preserve any shortfall on breach or integrity failure.
7. Raw vectors, training CSV, recommendation/evaluation artifacts and fitted R objects remain outside the repository. Public outputs contain approved aggregates, manifests and hashes only. Process separation is not described as OS sandboxing.

## Claim limits and stop rules

This estimates policy contrasts conditional on one benchmark reference, one fitted external semisynthetic generator and the fixed Development training frame, over the prespecified G0 corruption distribution. It does not quantify training-frame, DRF-fit, physical-system or manufacturing-population uncertainty. The target is a benchmark tracking value, not operating utility, cost or safety. A null, adverse or imprecise result is a valid result. Stop without replacing seeds/actions/samples on code/data/contract mismatch, unsupported intervention, invalid/nonfinite output, incomplete lock, RNG collision, response overwrite, information-boundary failure or resource breach. Never tune task, target, action, policy, budget or sample count after seeing final outcomes.

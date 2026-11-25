# Research D External Semisynthetic Development Contract

**Status:** `LOCKED_FOR_DEVELOPMENT_PILOT` under the user-authorized 2026-11-25 scope. This is not a final-evaluation contract and does not modify Research C.

## Research claim and limits

This is a conditional robustness study using the public CausalAssembly semisynthetic sample, its official Station1 reference DAG, and a new `fit_drf()` fit to that sample. It is a DRF-based external semisynthetic generator. It is not a real-device intervention study, a physical ground-truth validation, or evidence about deployment at the DAT manufacturing process. The fixed benchmark graph is an Oracle reference for controlled corruption; omitted edges are not thereby proven physical non-effects.

The question is whether the Research C repair-priority relationship is observed under a different external graph and a second-fit DRF generator. The inferential scope is one fixed Station1 graph, one deterministic DRF refit, one observational learner sample, and the prespecified Development G0 seed distribution. Thirty-two G0 seeds are not thirty-two independent manufacturing systems or SCM populations.

## Pinned external inputs

- causalAssembly repository commit: `8da3729e6383f0e1cbe7740bb6ab7ac4977ac7f9`; declared package version `1.2.1`; repository license `AGPL-3.0`.
- Public semisynthetic sample SHA-256: `afc079bfca962a4746afd316713743d7702ebc7ea00f98255cd8289d72ecef0e` (500 × 98 source rows/columns).
- Official reference SHA-256: `86378888c66089aebb94616dce121b5e8400414112eb221b78dff3a4ca84cab8`.
- Station1: 6 nodes and 7 directed edges, official station component, with no external parent. The exact edge and node mapping is in `structural_preflight.json`.
- The native fitted R/DRF object is not loaded from a pickle. Same-seed refits are checked by an exact 16-row observational sample digest before the evaluator process uses its refit.

## Task, actions, target and scale

- Benchmark action: `Station1_mp_0`; target: `Station1_mp_4`.
- Official path: `Station1_mp_0 → Station1_mp_1 → Station1_mp_4`; no direct reference edge joins action and target. This is strict indirect-only relative to the official reference graph and a virtual benchmark `do`, not demonstrated physical controllability.
- Five common actions are the pinned generator-fit source's linear 10%, 30%, 50%, 70%, and 90% quantiles for `Station1_mp_0`:
  `0.000155911358968`, `0.0001724093665238`, `0.00018679686613765`, `0.00020263502221978`, `0.00022589388613683002`.
- Values are finite, distinct, within both generator-fit-source and 512-row generated learner-training marginal ranges, and within observed `Station1_mp_0` parent-input ranges for the two fitted downstream mechanisms that use it. These checks do not establish joint conditional support for every downstream parent combination.
- One common target and scale are computed only from the single observational learner-training sample: `target = mean(Y_train) + 1 × sample_sd(Y_train, ddof=1)` and `scale = sample_sd(Y_train, ddof=1)`. Locked values: target `15.460000542160238`; scale `1.565469292160237`. They are benchmark target-tracking settings, not an operating setpoint or physical cost.
- The quantile action grid replaces Research C's standardized `K=(-1,-0.5,0,0.5,1)` grid. The single-task `+1 SD` target uses the same target-tracking principle but not C's alternating task-level `delta` assignment. These are explicit Research D adaptations.

## Learner and recommendation

- Generate exactly one 512-row observational learner sample from the fixed DRF, using a separate Research D seed. All policies, budgets, and G0 seeds share it.
- Reuse the existing Ridge graph learner and static mean-response recommender (`integrated_pilot.fit_model`, `decision_mvp.static_mean_response`): standardized variables, `alpha=1.0`; do not use the signed-linear Research C population runner or invent external GT coefficients.
- Fit each distinct repaired graph at most once per common training frame and learner setting. Cache key binds the repaired learner input graph (including unresolved states), training digest, and Ridge setting.
- Unresolved pairs remain abstentions and are omitted from the learner's confirmed directed-edge set, matching the existing pipeline convention. Cyclic/invalid graphs, constant scales, nonfinite predictions, and unsupported recommendation values fail closed.
- Deterministic recommendation tie-break: lowest predicted standardized squared target loss, then action nearest the action-grid median, then lower numeric action.
- The additional graph-free reference is a univariate Ridge X–Y association model trained on the same observational sample and action grid. It is an associational predictor, not a causal-effect estimator. It gets no intervention training data.

## Reference repair and policy grid

- Use the official Station1 DAG as a fixed benchmark reference and the existing Research C `policy_engine.py`; no Research C module or contract is edited.
- Reference-relative FN/FP/REV/UNRES, task zone, FP Rule A, fixed G0-opportunity normalization, existing M1–M4, unit edit costs, S0, all 15 nonempty metric subsets, and the Canonical Oracle comparator are retained.
- G0 rates: `q=0.15` on true adjacencies, `r=0.05` on reference-absent pairs; conditional FN/REV/UNRES mix equal; FP direction fair; DAG-invalid proposals are recorded and rejected without redraw. Budgets are `0..4` with B=2 primary.
- Seed IDs: outcome-blind structural qualification `701001..701064`; Development G0 `702001..702032`. Research D derives generator seeds from its own namespace. No seed is chosen or replaced based on outcome.
- Preserve no-error G0, no task-zone error, no-op, duplicate repaired graphs, and unused budgets in the denominator and reports.
- Unit cost is a relative edit count, not expert labor or money. The same q/r and B do not imply the same error burden distribution as Research C.

## Evaluation and estimands

- After all recommendations are content-hash locked, a separate evaluator subprocess refits the pinned DRF and verifies the deterministic refit digest. It reads only the locked recommendations, locked contract, source data, and evaluator seed namespace; it does not load the policy or Research C recommendation modules.
- Generate one common fixed batch of 256 interventional draws for each of the five actions (1,280 total). Action streams are independent and fixed in the run lock. Raw generated evaluation frames are transient in evaluator memory and are not saved.
- For action `a`, the target-tracking loss is `L(a) = (E[Y | do(a)] - target)^2 / scale^2`. It is neither individual-outcome MSE nor physical manufacturing utility.
- Primary Development contrast at B=2: `Δ_D = L_exp(a_S0) − L_exp(a_FullGreedy)`; positive values favor Full Greedy. This is the same-task/action-set population counterpart of the regret contrast because the shared best-action loss cancels. Primary point estimate uses the bias-corrected squared-mean estimator `((mean_a-target)^2 - sample_variance_a/n_a)/scale^2`; do not truncate negative estimates.
- The uncertainty summary separates G0-seed variation conditional on one evaluation table, action-row Monte Carlo variation conditional on the fixed 32 G0s, and a two-source bootstrap. Each replicate resamples G0 seeds as paired units and independently resamples rows within each action; the action-level loss resample is shared across all policies and G0s. This interval is development precision evidence, not external-system population inference.
- M4 remains Secondary. Report the signed `M4 − Full Greedy` loss contrast, policy/action/cost summaries, all budgets and graph-free association baseline. Do not replace the Primary if a secondary contrast is favorable.
- Do not claim absolute regret unless a common action-set minimum and its selection uncertainty are explicitly reported; it is not the Primary here.

## G1/G2/G3, resource limits, and exclusions

- G1: this contract, exact actions/target/scale, seeds, code/data hashes, sample sizes, estimator, bootstrap and resource limits are recorded in `development_run_lock.json` before evaluator draws. Recommendation manifest is separately content-hash locked.
- G2: root unittest discovery covers adapter fixtures, a multi-parent order fixture, lock/tamper tests, recommendation-to-Ridge fixture, evaluator fixture, and fail-closed schema checks. The pinned real R/DRF integration checks `X_train.columns` against sampling parent order and same-seed refit reproducibility.
- G3: bounded Development Pilot only: one DGP, one 512-row train sample, at most 32 G0s, 17 repair policies, five budgets, five actions, 256 evaluator draws/action, maximum 1,280 intervention rows, six-hour wall-time cap, serial sampling. If any cap or integrity gate fails, stop without replacement.
- No final evaluation seeds or final evaluation samples are generated. No physical device is controlled. No task/target/action/policy/budget is changed after response exposure.

## Binding artifacts

- Static contract: `development_contract.json`.
- Exact pre-evaluation lock: `development_run_lock.json` (includes source, graph, training and code hashes, exact action values, target/scale, environment and limits).
- Recommendation lock: local ignored file `data/local/research-d-semisen-pilot/recommendations.json`; its hash is reported in the results, while generated evaluation rows and raw frames stay out of Git.
- Development G0 structural audit: `development_g0_manifest.json`.
- Structural-only qualification: `structural_preflight.json`.\n
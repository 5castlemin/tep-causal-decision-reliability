# Research D External Semisynthetic Final Contract Draft

**Status: PROPOSED FOR REVIEW — NOT APPROVED; NO FINAL EVALUATION DATA GENERATED.** This draft follows the completed bounded Development Pilot. It does not alter or supersede Research C's frozen contract.

## Study type and claim

This would be a **conditional external semisynthetic robustness evaluation**: causalAssembly's pinned manufacturing-process-based public semisynthetic sample and official Station1 benchmark DAG are used to fit one new DRF generator. It is not a real manufacturing intervention study or validation against a complete physical causal graph. The finite hard-do is a virtual intervention in the fitted factorization. The result would be conditional on one reference graph and one fixed DRF DGP, not a population of physical systems or independent SCMs.

## Prespecified task and common actions

- Action `Station1_mp_0`; outcome `Station1_mp_4`; benchmark reference path `Station1_mp_0 → Station1_mp_1 → Station1_mp_4`; no direct reference action-to-target edge.
- Preserve the five pinned-source 10/30/50/70/90% action quantiles recorded in the Development lock. Verify their finite values, support, uniqueness and fitted conditional-input ranges from the source before new final data generation. Do not choose action values from Development evaluator response means.
- Virtual hard-do only. Do not claim that these columns are physically controllable at a plant.
- Generate a fresh observational learner-training sample of 512 from the same deterministic generator refit recipe under a final-only training seed. Use `target=mean(Y_train)+1 sample SD(Y_train,ddof=1)` and `scale=sample SD(Y_train,ddof=1)`. These are training-only benchmark target/scale values, not a physical operating point.
- The Development sample and evaluator responses are exploratory and must not be reused as final learner or evaluator data.

## Reference and structure policy

- Use the official Station1 reference graph in **reference-relative controlled corruption** mode. Classify errors as disagreement with the pinned reference, not proven errors in a complete physical GT.
- Retain the existing Research C task-zone and FP Rule A algorithm, M1–M4 definitions, S0, all 15 metric subsets, Full Greedy, Canonical Oracle comparator, unit edit costs, q=0.15, r=0.05, FN/REV/UNRES conditional equal mix, fair FP orientation, DAG rejection without redraw, and G0-fixed opportunity normalization.
- Use budgets 0–4 and B=2 as Primary. Report every no-error G0, no-task-zone-error G0, no-op, unused budget, DAG rejection, duplicate repaired graph, metric support and task/off-task error count. No seed replacement.
- Start with 200 final G0 seed IDs from a final-only Research D namespace. They are repeated graph-corruption draws under one DAG/DGP, not 200 independent external systems. Final seed IDs are not yet generated.
- A fixed action set and reference must apply to all policies; expose exact initial and final graph hashes and the G0 event ledger.

## Learner and baselines

- Reuse the existing Ridge graph learner and static mean-response recommendation: standardized variables, alpha=1.0, same train sample and action grid for every policy/G0.
- Keep unresolved pairs as abstentions and omit them from the confirmed directed-edge set as in the current learner path. Invalid cycles, constant scales, nonfinite predictions and unsupported actions fail closed.
- Primary policies are S0 and Full Greedy at B=2. M4 remains Secondary. Keep all 17 policies and the Canonical Oracle results.
- Include the univariate Ridge observational X–Y association baseline on the same train sample and action set. Label it associational; it does not estimate `do(X)` effects. It gets no intervention training data.
- Cache only identical repaired learner-input graph + train digest + Ridge settings. Do not use evaluator outcomes for policy recommendation, task selection or cache keys.

## Evaluation and primary estimator

- Generate one common action-level evaluation table, with independent action RNG streams, after all final recommendations are hash-locked. Start with 2,500 finite interventional rows/action (12,500 total) as a **planning value**. Final sample count must be approved against a fixed precision target and resource cap after a pilot-based simulation of the locked two-source estimator.
- Loss per candidate action is `L(a)=((E[Y|do(a)]-target)^2)/scale^2`, a mean-response target-tracking loss. It is neither individual-response MSE nor a plant cost/safety measure.
- Primary estimand at B=2 is `Δ_D=L_exp(a_S0)-L_exp(a_FullGreedy)`; positive favors Full Greedy. With the same task and action set it is the same population contrast as the regret difference because the shared best-action loss cancels. Use the bias-corrected loss `((mean-target)^2-sample_variance/n)/scale^2`, without truncating negative values.
- Report absolute empirical regret only as secondary and only with action-minimum selection uncertainty. Do not use the noisy empirical best action as a recommendation.
- Primary uncertainty: paired G0 resampling plus within-action sample-row resampling, preserving one shared resampled action-loss table across all policies/G0s. Proposed final bootstrap count: 10,000. Report G0-only and action-MC components separately. Do not interpret any interval as manufacturing-system population uncertainty.
- Pilot-based planning suggests an action-MC-only 95% half-width of about 0.061 at 256 rows/action; scaling to a proposed 0.02 tolerance suggests roughly 2,380 rows/action. 2,500/action is a rounded starting proposal, not an approved sample size. The pilot's two-source interval remains the relevant uncertainty evidence and includes zero.

## Information boundary and execution lock

1. Pinned fit-source and official DAG; fixed DRF fit seed/runtime.
2. Separate final-seed 512-row observational training sample; training-only target/scale.
3. Recommendation stage receives only train frame, reference/G0/task/actions/target/scale and existing C policies/learner.
4. Write recommendation manifest, configuration, code/data hashes and seed namespace; validate completeness and content hash.
5. Start evaluator-only subprocess after the lock. It refits from the pinned official source, verifies same-seed reproducibility, reads locked actions/recommendations, and cannot alter recommendations. Keep raw evaluation frames out of Git.
6. Persist aggregate action/policy results, sample counts, hashes, failed/omitted rows and exact analysis script version.

Process separation and module allow-lists are engineering boundaries, not OS-level security isolation. Record that limitation. No unresolved failure may be silently replaced.

## Development evidence and review questions

The Development Primary mean was `+0.003338`, but its two-source 95% bootstrap interval was `[-0.065322,0.075465]`; it does not resolve the effect direction. The target was above all five Development evaluator action means. That observed feasibility gap must be disclosed; it may not be used to pick a different action, task or target. At B=2, M4 selected the same action as Full Greedy in all 32 Development G0s, so the pilot did not discriminate M4 from Full Greedy on the decision outcome.

Before approval, review whether (a) a 0.02 standardized-loss precision tolerance is useful, (b) 200 G0 seeds and 2,500 evaluator rows/action fit the resource budget, (c) one fixed DGP is sufficient for the intended robustness claim, and (d) the target-tracking task remains scientifically useful despite target values above observed action means. No one of these questions is answered by the Development pilot.

## Exclusions and stop conditions

- No physical device actuation, real manufacturing causal effect or deployment claim.
- No new dataset search; no additional causal discovery; no change to Research C.
- No new G0 seed, action, task, target, estimator or Primary selected after viewing Development results.
- Stop final generation on source/hash mismatch, non-reproducible refit, invalid support/schema/nonfinite draws, incomplete recommendation lock, information-boundary violation, or resource-cap breach. Keep all failures and shortfalls; do not replace.\n
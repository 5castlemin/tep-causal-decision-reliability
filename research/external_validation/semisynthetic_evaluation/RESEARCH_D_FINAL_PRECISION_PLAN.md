# Research D final precision and resource plan

**Status: proposal for final-contract review only. No final seeds, training frame, evaluator samples or final evaluation were generated.** The sole Development reproduction is complete and exactly matches the retained historical action-level summaries and recommendations.

## Estimand and scope

Primary remains `Δ_D = L(a_S0) − L(a_FullGreedy)` at B=2, with the same Station1 task, five actions, target/scale rule, reference-relative graph repair rules, learner and shared action-level loss table. The interpretation is conditional on one Station1 graph, one DRF-based external semisynthetic generator, one training frame (if selected), and the prespecified G0 corruption distribution. G0 seeds are graph-corruption draws, not independent SCMs or physical systems.

## Reproduced precision evidence

The 256-row/action reproduction has action-Monte-Carlo-only interval `[-0.0585361, 0.0634382]` and half-width `0.0609872`. The two-source interval is `[-0.0653220, 0.0754654]`; the G0-only interval is `[0.0005873, 0.0073717]`. The primary point is `+0.0033381`. The interval includes zero. These values are planning diagnostics, not a target for obtaining a favorable result.

The exact B=2 recommendation frequency difference `w_a = P(S0=a) − P(FullGreedy=a)` across the 32 Development G0 seeds is:

| Action | `w_a` | Evaluation mean | Sample variance |
|---|---:|---:|---:|
| 0.000155911358968 | −0.18750 | 13.92578 | 2.51604 |
| 0.0001724093665238 | 0.00000 | 13.82422 | 2.89055 |
| 0.00018679686613765 | 0.15625 | 13.91797 | 2.77364 |
| 0.00020263502221978 | 0.00000 | 14.03516 | 2.23797 |
| 0.00022589388613683002 | 0.03125 | 13.87891 | 2.35783 |

The outcome means are below the training-only target `15.460000542160238`. This is a disclosed target-support limitation for the observed pilot sample, not evidence to change the target or action set and not proof of population-level infeasibility.

## Action sample planning

Using the reproduced action means, variances and recommendation weights, the first-order independent-action delta-method Monte Carlo SE at 256 rows/action is `0.031234`, giving a two-sided 95% half-width `0.061218`. Scaling variance by `1/n` gives approximately `2,399` rows/action for a `0.02` half-width. At 2,500/action, the projected action-MC half-width is about `0.0196`.

**Recommended planning candidate:** 2,500 rows/action (12,500 total) with the same five locked actions. This is not approved sample size. The `0.02` value is a reporting precision tolerance candidate, not a manufacturing meaningful-effect threshold. The delta-method calculation is approximate, uses a single 256-row vector per action and Development recommendation weights, and does not account for uncertainty in those weights or the G0 distribution. A preapproved, response-blind simulation of the locked estimator can assess Monte Carlo coverage using these observed vectors or synthetic fixtures; it must not add evaluator draws or select a sample size based on the Primary sign/p-value. A precision target for the combined G0 and action-MC interval should be set explicitly; the action-only 0.02 target alone does not ensure total precision.

## G0 count and uncertainty

Retain 200 new final G0 seeds as a candidate, with seed IDs disjoint from Development and all preflight/smoke streams. Report the 200-seed variation conditional on one DGP and training sample; never label it 200 independent SCMs. Because the current G0-only interval is based on 32 seeds, its variance estimate is preliminary. Do not select or replace seeds based on task-zone errors, recommendations or outcomes. Keep all valid, no-error, no-task-zone-error, DAG-rejected and no-op cases in the locked denominator.

Use 10,000 paired two-source bootstrap replicates as a candidate for stable reported quantiles. Preserve one shared resampled action-loss table across G0 seeds and policies; report G0-only, action-MC-only and combined intervals. Implement row resampling in bounded chunks to avoid a full `10,000 × 2,500` float array per action. Independent action RNG streams remain preferred; retain the recorded covariance structure if the implementation uses common random numbers.

## Training-frame decision for user review

| Choice | Estimand and tradeoff |
|---|---|
| **A. Freeze the reproduced 512-row training frame (recommended)** | Holds training, target/scale, recommendations and policy behavior fixed; new G0 and evaluator streams test the same training-conditioned contrast more precisely. It is the cleanest confirmatory continuation of this Development contract. It does not measure training-sample variability. |
| B. Draw a new 512-row training frame | Evaluates a different training-conditioned environment; target/scale and policy action frequencies may change. This includes one additional training realization but still cannot characterize training variability without multiple prespecified training seeds. Do not pool it with A as though estimands were identical. |

The user must select A or B before final-lock creation. If broader learner-training generality is needed, propose a separately powered multi-training-sample design rather than treating one B sample as a population result.

## Resource estimate and limits for review

The reproduction sampled 1,280 evaluator rows in `350.868` seconds (`70.17` seconds/action); total post-lock runner time was `463.614` seconds and evaluator DRF refit was `34.842` seconds. Linear scaling to 12,500 rows gives about 3,426 seconds (57 minutes) of sampling, before final bootstrapping and recommendation work. A **provisional** final resource ceiling of 2 hours wall time and 4 GiB process memory is recommended, with sequential action sampling and chunked bootstrap; it is a proposed ceiling, not yet measured at the proposed scale. The reproduction lock did not capture peak memory. Before any final draw, validate the chunked bootstrap on a synthetic fixture and run a response-blind resource benchmark, then freeze a stricter measured cap if needed. Stop on any cap breach and report the shortfall; do not silently lower row counts or replace actions/seeds.

## Seed streams and readiness conditions

- Keep the pinned causalAssembly source/data, DRF fit seed, task, graph, action grid, learner, metrics, policy set, budget grid, loss estimator and Primary unchanged.
- Use new final G0 and evaluator seed namespaces. No final stream has been generated.
- If choice A is selected, reuse the exact Development training frame whose numeric digest is `bcca5e56b01dd8cc59d227272906fcee6f9160897e9be2179bd9751619b4bc39`; do not publish the frame.
- Lock the final action/target/scale, G0 IDs, recommendation hash, evaluator RNGs, sample counts, analysis code, uncertainty method and resource cap before evaluator access.
- Keep recommendations and evaluator in separate processes. Preserve recommendation lock and source/code/data hashes; raw evaluator vectors remain outside Git.
- Report the single-DGP provenance and the fact that causalAssembly is externally provided semisynthetic material with a newly fitted DRF, not a physically verified generator.

Final data generation requires a separate approval after the user reviews this proposal and chooses the training-frame design and precision/resource criteria.

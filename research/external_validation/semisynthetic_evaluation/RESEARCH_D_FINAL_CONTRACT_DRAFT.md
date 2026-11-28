# Research D External Semisynthetic Final Contract Draft

**Status: ready for user review; not approved for final evaluation.** Development Reproduction is complete and source/output provenance is verified. This proposal does not modify Research C's frozen contract and has generated no final seeds or samples.

## Study type and claim

This is a conditional external semisynthetic robustness evaluation using causalAssembly's pinned manufacturing-process-based public semisynthetic sample, the official Station1 benchmark DAG and one newly fitted DRF generator. The task is a virtual hard-do in that fitted factorization, not a physical plant intervention. Results are conditional on one reference graph and one fitted generator; they do not represent a population of physical systems or independent SCMs.

## Locked task and structure policy

- Action `Station1_mp_0`; target `Station1_mp_4`; reference path `Station1_mp_0 → Station1_mp_1 → Station1_mp_4`; strict indirect-only relative to the official Station1 DAG.
- Retain the five Development action values exactly: `0.000155911358968`, `0.0001724093665238`, `0.00018679686613765`, `0.00020263502221978`, `0.00022589388613683002`.
- Treat graph errors as discrepancies relative to the official benchmark graph, not proven errors against complete physical GT.
- Retain Research C's existing Task zone, FP Rule A, M1–M4 definitions, S0, all 15 nonempty metric subsets, Full Greedy, Canonical Oracle, atomic edit cost 1, `q=0.15`, `r=0.05`, FN/REV/UNRES mix, fair FP orientation, DAG rejection without redraw and G0-fixed opportunity normalization.
- Policies: all 17 existing policies; budgets `B=0–4`; Primary at `B=2`, S0 versus Full Greedy. M4 remains Secondary. Do not promote Secondary or exploratory contrasts to Primary.
- Use 200 new prespecified G0 seed IDs as a candidate; include all generated cases and rejections without replacement. The seeds are draws under one fixed graph/DGP, not independent SCMs.

## Learner, target and training choice

- Reuse the existing Ridge graph learner (`alpha=1.0`) and recommendation logic. All policies/G0s share one 512-row observational learner frame and common action set.
- Target rule `mean(Y_train)+SD(Y_train)` and scale `sample SD(Y_train, ddof=1)`; the target is a benchmark tracking value, not an operating setpoint or plant utility.
- **Preferred training choice A:** freeze and reuse the reproduced 512-row training frame, numeric digest `bcca5e56b01dd8cc59d227272906fcee6f9160897e9be2179bd9751619b4bc39`. New G0/evaluator streams then estimate the same training-conditioned contrast. No training-frame variability claim follows.
- Alternative B is one new 512-row training draw; it changes target/scale and recommendations and therefore targets another training-conditioned environment. If selected, keep the result separate from A. User choice is required before the final lock.
- Keep the X–Y regression baseline using only the same training frame. Label it observational association, never a causal effect estimator. Do not give it intervention training data.

## Primary evaluation and uncertainty

- For action `a`, `L(a)=((E[Y|do(a)]−target)^2)/scale^2`, estimated by the existing bias-corrected squared sample mean `( (mean−target)^2 − sample_variance/n )/scale^2`, without truncation. This is mean-response target-tracking loss, not individual MSE, plant cost or safety.
- Primary `Δ_D=L_exp(a_S0)−L_exp(a_FullGreedy)` at B=2; positive favors Full Greedy. Use one shared action-level evaluator table for every policy and G0.
- Generate all recommendations first, validate and hash-lock them, then start evaluator-only sampling. Evaluator outcomes cannot alter recommendations, task, actions, target or exclusions.
- Use independent RNG streams per action. Candidate sample count: 2,500 rows/action (12,500 total), pending the reviewed 0.02 standardized-loss-unit 95% action-MC half-width tolerance and resource check. The tolerance is a precision/reporting target, not a domain meaningful-effect threshold.
- Candidate 10,000 paired two-source bootstrap replicates with a shared resampled action-loss table. Report G0-only, action-MC-only and combined intervals. Use chunked resampling and fixed sample counts; no outcome-based sample expansion.
- Report absolute empirical regret only as secondary, with best-action selection uncertainty; shared best-action loss cancels from the common-action policy contrast.

The reproduced delta-method calculation estimates an action-MC half-width of `0.061218` at 256 rows/action and approximately 2,399 rows/action for 0.02; 2,500 is a rounded proposal. The reproduction two-source interval was `[-0.065322, 0.075465]` and included zero. The five evaluator means were below the training-only target; disclose this support limitation without changing the task or implying population infeasibility.

## Training/evaluation information boundary

1. Use pinned source sample, official DAG and fixed DRF fit/runtime configuration.
2. Select training design A or B before final run lock; target and scale are training-only.
3. Recommendation process receives only the training frame, reference/G0/task/action/target/scale and existing learner/policy code.
4. Lock all recommendations, seeds, source/data/code hashes and invocation settings.
5. Evaluator process verifies the lock, independently refits the pinned generator, samples common actions from final-only evaluator seeds and writes raw vectors only to external local storage.
6. Preserve hashes, approved aggregates, exclusions and final code/tree identity. Do not upload raw training, recommendations, response vectors, fitted objects or original public data.

Process/module separation is not an OS-level security sandbox. Oracle-assisted reference access remains an explicit limitation.

## Proposed resource limits and stop rules

Propose a 2-hour wall-time ceiling and 4 GiB process-memory ceiling, sequential sampling and chunked bootstrap. The reproduction took 350.868 seconds to sample 1,280 rows and 463.614 seconds post-lock; linear scaling implies about 57 minutes for 12,500 rows before final bootstrap. The proposed ceiling must be validated with a response-blind resource benchmark and frozen before final generation; peak memory was not measured in the reproduction. Stop on code/source/data/lock mismatch, invalid support/schema/nonfinite draws, incomplete recommendations, information-boundary failure or resource breach. Preserve shortfalls; never replace seeds, actions, policies or samples silently.

## User decisions before final approval

1. Choose fixed Development training frame (A, recommended) or one new training frame (B).
2. Approve or revise 0.02 action-MC half-width tolerance and separate total-interval reporting goal.
3. Approve 200 G0 seeds, 2,500 rows/action, 10,000 bootstrap replicates and proposed 2-hour/4-GiB ceilings after the resource benchmark.

This draft is not execution authorization. No final seed, final training sample, or final evaluator response may be generated until a separate approval locks these decisions.

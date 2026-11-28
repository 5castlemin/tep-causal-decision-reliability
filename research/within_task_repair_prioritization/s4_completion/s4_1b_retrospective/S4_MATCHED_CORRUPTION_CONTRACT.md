# S4 matched structural corruption contract (proposal)

Status: `PROPOSED_NOT_AUTHORIZED`; no matched G0 variants or new SCMs created.

## Estimand and block

Within a fixed SCM and task, compare decision regret and repair-policy behavior across structurally matched G0 corruptions. The SCM—not each corrupted graph—is the independent sampling unit. The first contrasts are conditional on topology strata and corruption recipes; they are not effects for a manufacturing population.

## Matched contrasts

1. **Location:** same error type/count, move its pair to different positions along the same causal path.
2. **Role:** where feasible, compare the same error class in causal-path, backdoor, and other task-zone structures.
3. **Multiplicity:** co-located errors on one path versus dispersed errors across paths; preserve or remove alternative paths as a separately recorded factor.
4. **Scarcity:** evaluate one G0 at B=1,2,3,4 and report K, actual edits, unused budget, graph/action/regret changes.
5. **Unlocking:** distinguish edits that change later candidate feasibility from those that do not.

Structural matching uses no regret, selected action, policy outcome, score gain, or oracle comparison. Reject or label as bundled any pair where the intended factor changes alongside other topology features.

## Analysis lock needed before generation

Specify SCM sample cap, topology strata, task sampler, paired corruption recipes, number of variants, proposal cap, seed namespace, candidate reconstruction, policy set, gamma, action grid and target, evaluator, primary paired contrast, multiplicity family, precision/power target, attrition handling, resource limits, and immutable output paths. Store SCM block ID and matched-variant relation in the private ledger; publish aggregates only.

No proposal counts, sample size, or seed IDs are frozen here. New SCM/G0/observation generation requires a separate user-approved execution contract.

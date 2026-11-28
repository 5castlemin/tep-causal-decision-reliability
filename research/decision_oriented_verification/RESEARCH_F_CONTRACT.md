# Research F-Lite — Frozen Development and Held-out Contract

**Status:** post-hoc exploratory extension; fixed before cohort analysis. No external preregistration.

## Question and scope

Can a limited budget of pairwise expert queries reduce downstream decision regret when the verification policy cannot see the reference graph? This uses only the existing Research C Development (64 SCMs) and Held-out (200 SCMs) inputs, which were already observed in earlier work. It is not a new independent confirmation. No SCM, G0, observational sample, DRF fit, or intervention response is generated.

## Inputs and analysis unit

One original Research C SCM is the paired analysis unit. Each unit is restored from its original proposal and cohort ledger in read-only mode; the restored truth specification, observations, task and initial G0 must match the ledger bindings and the original B=0 S0 record. Existing action grid, target and scale are preserved. Development and Held-out are analyzed separately. Research D is excluded.

## Information boundary

The policy receives only an allow-listed object: ordered node names, the 512-row observational matrix, action/target, fixed action grid, target/scale, current directed and unresolved relations, query history, and remaining query budget. It does not receive truth, reference edges, corruption events, true coefficients, oracle labels, evaluator losses, original payloads, or per-SCM prior outcomes. The expert receives a reference graph and a single queried unordered pair, and returns only `U_TO_V`, `V_TO_U`, or `NO_EDGE`. The evaluator runs only after all recommendation records are written and hashed. These are interface and process-boundary controls, not an OS sandbox.

## Query and repair rules

All unordered node pairs are eligible, including correct, absent, directed and unresolved relations. A query costs one unit even when the expert confirms the current relation. Repeated pairs are forbidden. Budgets are 0–4. The effective learner graph omits unresolved edges, matching the existing C bridge. A verified relation is applied atomically if the resulting directed graph is acyclic; otherwise it is retained as pending and retried in canonical pair order after later edits. No unqueried edge is removed automatically; applied verified relations cannot be reverted by the policy.

## Scores and policies

For each pair, feasible local states are no edge and either direction, with all other current relations fixed. A Gaussian linear DAG BIC is used only as a local fit heuristic. Stable relative weights are proportional to `exp(-0.5 * (BIC-min(BIC)))`; they are not causal probabilities or a full graph posterior. Suspicion is `1-weight(current)`; unresolved starts at one. Decision impact is the equally weighted mean predicted target-tracking opportunity loss over feasible alternative states that differ from the effective current state, using the existing Ridge-1 learner and five action grid. Negative gains beyond numerical tolerance are a contract failure. The proposed score is `suspicion * impact`; query cost is one.

Policies: S0; uniform random verification (32 fixed trajectories per SCM, summarized within SCM); fit-based; suspicion-only; decision-impact-only; decision-weighted. Oracle-assisted M4 and graph-free X–Y association Ridge are diagnostic comparators, not equal-information policies. Existing C's learner/evaluator are reused; no policy receives GT response or loss.

## Outcomes and inference

Primary exploratory contrast at B=4: comparator regret minus decision-weighted regret, separately for each C cohort and each of random, fit-based, suspicion-only and impact-only. Report paired means, medians, better/worse/tie, and 10,000 SCM-level paired bootstrap intervals. Random repeats are averaged within SCM and are not independent SCMs. Report all budgets, query/error/edit counts, remaining errors, action changes, edit/query/runtime/model-score costs, and failures. Pointwise intervals are not simultaneous. All F analyses are post-hoc because the C cohorts and results were previously inspected.

GT regret is `L_GT(selected)-min_a L_GT(a)` on the original five actions, accessed only by the evaluator. No F result changes C's frozen primary or the final C–D–E claims.

## Seeds, provenance and stop rules

Use a distinct `research-f-lite-v1` seed namespace and fixed derivation from cohort, SCM id, policy and repeat. No seed selection or replacement. Require input SHA-256s, exact restored truth/observation/G0/task/action bindings, complete unique keys, DAG validity, query budgets and post-recommendation evaluator ordering. Any mismatch blocks the affected cohort; no replacement units. Keep raw unit-level results outside the public repository. Resource ceilings: 2 hours Development, 3 hours Held-out, 4 GiB process-tree memory; measured limits only are reported as verified.

## Optional noisy expert sensitivity

Only after the perfect-expert core is complete: accuracies 0.9 and 0.8, 16 fixed categorical corruption repeats per SCM, B=4, for Random, Suspicion-only, Impact-only and proposed. Shared potential response keyed by SCM/pair/accuracy/repeat. This is a hypothetical response-noise model, not measured human expertise. If not completed, report `NOT_RUN`.

## Claim boundary

Results concern reference-blind heuristics interacting with a perfect or hypothetically noisy simulated expert on previously observed synthetic SCMs. They do not establish real-expert performance, deployment benefit, physical manufacturing validity, Bayesian optimality, or new confirmatory evidence. Related work includes targeted causal elicitation, expert-in-the-loop causal discovery, and causal preference elicitation; novelty is limited to this benchmark-specific comparison and must not be claimed as first-of-kind.

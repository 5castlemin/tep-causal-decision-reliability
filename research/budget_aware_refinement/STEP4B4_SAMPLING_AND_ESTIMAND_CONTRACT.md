# Step 4B-4 sampling and estimand contract

## Final decision addendum (2026-11-15)

The operative decisions are in [STEP4B4_FINAL_DECISION.md](STEP4B4_FINAL_DECISION.md). N=64 development and N=200 confirmation are fixed operational targets for descriptive estimation only; they do not guarantee power. The candidate ceilings 362 and 1,036 are adopted as finite planning stop limits, not as yield guarantees. P strata remain uniformly proposed at 1/20 and the target remains P conditioned on Q-common; all structural rejections remain in the attempt denominator. The fixed audit's template proportions (107/637, 69/637, 164/637, 297/637) are diagnostics, not frozen future proportions. There is no quota reweighting.

The SCM-level equal-type mean remains the target, but Option B suspends confirmatory superiority claims. A missing type cell makes the SCM composite missing; no zero fill, type-denominator change, or complete-case replacement of the target is allowed. At a candidate cap shortfall, report yield and observed eligible-row descriptions, without a target-population or superiority claim.

Status: **IN_PROGRESS / proposed contract; not frozen**. No confirmation SCMs, coefficients, observational samples, fitted SCM outcomes, effects or regret were generated.

## Target and estimand

The candidate target is the P topology generator conditioned on Q-common eligibility: one topology/task is eligible only when the predeclared indirect-only task has at least two same-type DAG-valid correction candidates for each FN, FP and REV, with one task-relevant and one peripheral candidate and B=1 leaving at least one uncorrected. Eligibility uses topology, task, error positions, operation validity and budget only. The common-cause scaffold task X→Y is preferred when available by the existing rule. It does not condition on policy rank/final graph difference, coefficients, prediction, effect or regret.

The observed structure-only audit used 20 template×node-count strata, 100 candidates per stratum, and uniform proposal probability 1/20. It accepted 637/2000 = 31.850%; pooled descriptive rate 31.85%. The earlier pooled Clopper–Pearson interval [29.811%, 33.942%] treats strata as a common-yield binomial and is not a stratified-design 95% guarantee; use the Bonferroni simultaneous strata interval in [yield review v2](STEP4B4_STRATIFIED_YIELD_REVIEW.md). Settings SHA-256: `a7e44c66387ac77ca10ff344cacec2c3fbf678d04741087701c16b6d042bc414`; compressed raw SHA-256: `c0ce611bf7aeca025407d884111fa919175c5bd091f9d55537de022948aa406e`. This aggregate interval is descriptive for the fixed keyed proposal and does not represent a guaranteed future yield. Stratum rates vary materially; the raw JSON and summary preserve all attempts and zero-yield strata.

Use rejection sampling (A) as the estimand-aligned candidate: sample each P stratum with probability 1/20, accept every Q-common eligible candidate, and stop only at a preregistered finite cap. This targets P conditional on eligible under the fixed proposal, subject to generator determinism and stream design. Do not use post-hoc quotas. If quotas are later required, specify inclusion probabilities and inverse-probability weights plus a design-consistent variance estimator before confirmation.

For the SCM-level primary row, evaluate FN/FP/REV on the same eligible SCM and task; let each type difference be `Regret_Global - Regret_TaskFocused`, and form `D_i = (D_i,FN + D_i,FP + D_i,REV)/3`. Type weights 1/3 define an experimental mixture, not manufacturing error prevalence. One SCM is the independent unit; three type graphs, task repeats, policy runs and Random repetitions are correlated within SCM.

A new independent SCM means distinct structural equations (topology plus role mapping/parents, independently drawn coefficient realization and exogenous distribution). Repeated sampling noise from identical equations does not create a new SCM. Repeated topology is allowed if equation content differs. Exact equation duplicates are logged and rejected under a deterministic duplicate rule; no structural hash alone rejects a valid distinct SCM. Dev/confirmation IDs use disjoint namespaces and RNG cohort keys.

## Yield and sample-size planning (not frozen)

The pilot yield is 637/2000 (31.850%), compared with the earlier 34/100 (34%). For a fixed iid-binomial yield assumption and 95% conditional probability of meeting eligible target, candidate caps are: 236 for N=64 at observed yield; 253 using the lower endpoint 29.811%; 381 at assumed 20%; for N=200 these are 690, 738, and 1107. These are conditional planning probabilities, not overall confidence guarantees. Because yields vary by stratum and some strata have zero observed successes, the earlier homogeneous 738/1,107 candidate cap values are superseded for planning by the stratum-aware 362/1,036 values in v2. No operational maximum is frozen pending resource enforcement.

64 development and 200 confirmation eligible SCMs remain candidates, not approved sizes. Development may estimate nuisance variance and test the frozen workflow; it must not tune eligibility after observing confirmation. Confirmation requires a fresh cohort/key and the predeclared all-type vector. If the finite cap misses target, report shortfall; never extend based on observed outcomes or replace selectively. No inference starts with a shortfall or incomplete primary vector.

## Prior-contract differences

This prospectively implements the B3 Q-common/B=1 H2 target, replacing the older Step 0 P/B=4 selected-policy-versus-Random primary proposal. That older proposal is retained as historical and becomes secondary/exploratory. The 48,720 execution estimate is not reused. A legacy two-task-per-SCM proposal is not the Q-common primary task contract. None of these changes alters prior results.

## Matched Random auxiliary baseline

If retained, use five predeclared `random_baseline` stream replicates per SCM and error type at B=1. Each repeat receives the same initial graph, same-type correction candidate set, task, data, unit costs, DAG constraints and type schedule as the paired Global/Task-Focused runs; only candidate ordering is random. Compare Task-Focused vs Random and Global vs Random as secondary/descriptive contrasts. The five repeats are nested within an SCM and never increase the independent SCM count. Path F1 uses extra GT path information and remains a separate oracle benchmark.


## Dev/confirmation size decision procedure (still prospective)

Keep 64 development SCMs and 200 confirmation SCMs as candidates only. If 64 development SCMs are later run, use them for code/failure-rate diagnostics and a nuisance SD estimate only; before opening any confirmation output, apply a documented precision rule to the fixed candidate N=200. If the valid inference method or a .10 half-width target is not supported, stop and amend the design before confirmation rather than increasing N after inspecting confirmation effects. With no defensible primary CI yet, 200 is not an approved final N.

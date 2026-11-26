# Research E — Budget-Adaptive Causal Graph Repair

**Classification:** `POST_HOC_BUDGET_AND_COST_EFFECTIVENESS_EXTENSION`

**Scope:** Research C original Development and Held-out cohorts; Research D saved final audit summaries; exact, hash-checked reconstruction of the original Research C inputs for budgets above four.
**Status:** Exploratory follow-up. Research C and D primary/secondary contracts remain frozen.

## Research question

How does the efficient graph-repair strategy change when the maximum edit budget and the preference assigned to edits change?

## Data and analysis units

- Research C Development: 64 original SCMs; analysis unit is SCM.
- Research C Held-out: 200 original independent synthetic SCMs; analysis unit is SCM.
- Research D Final: one fixed DRF-based semisynthetic DGP, training frame and benchmark task; published/audited policy-budget aggregates cover 200 graph-corruption draws. Those draws are not independent SCMs.
- Cohorts are always reported separately. Regret and target-tracking loss are never pooled or presented on a shared numeric scale.

## E-1: budget and cost effectiveness

For the original B=0–4 results, all 17 policy rows per unit are read from the original C Ledger or D's saved independent audit. C results include 10,000 paired SCM bootstrap resamples (seed `2026112601`). Adjacent-budget marginal benefit is `mean loss(B−1) − mean loss(B)`; C intervals resample the same SCMs jointly across the compared budgets. The ratio to mean added edge edits is descriptive, not a per-edit causal effect. D's unavailable unit-level rows prevent new paired intervals; its aggregate marginal differences are descriptive only.

Pareto dominance is defined by no greater mean atomic edge-edit count and no greater mean loss/regret, with at least one strict improvement. Equal-coordinate candidates are retained as ties. Fixed-maximum-budget and all-budget frontiers are reported separately. The cost objective is `mean loss + lambda × mean edge edits`, with the supplied common lambda grid and pairwise exact line intersections. Lambda is a hypothetical normalized preference, not a money or time conversion.

## E-2: budget saturation

For each original C unit, `E_i` is the number of distinct initial FN/FP/REV/UNRES adjacencies. The pre-outcome rule is `B_max=max(4,max_i E_i)`: Development `B_max=7`, Held-out `B_max=9`. Each existing input was deterministically restored from its admitted proposal and original seeds. Truth specification, 512-row observation matrix, task and G0 digests matched the original Ledger before use. Original B=0–4 repair graph hashes, edit logs, recommended actions and analytic regrets were replayed exactly for all 264 SCMs and 17 policies. New analysis uses the existing deterministic analytic evaluator; no new SCM or G0 draw was created.

Saturation is separated into: (1) structural—no reference-relative discrepancies remain; (2) policy—no eligible candidate remains for that policy; (3) constraint—policy candidates remain but none is DAG-feasible; and (4) decision—chosen action and evaluated regret stay identical at every later tested budget. None implies the others.

## E-3: exploratory extensions

`ADAPTIVE_M4_BLOCKER_AWARE` first follows M4's existing score and deterministic tie-break. Only when all positive-gain task repairs are cycle-blocked may it delete a reference-relative off-task FP, and only if that one deletion makes at least one positive-gain M4 repair feasible and at least two units of budget remain. It then performs the best unlocked M4 edit and resumes M4. It does not inspect learner predictions, ground-truth effects, loss, or regret. It is one-blocker lookahead, not general planning.

Target sensitivity keeps the five original actions and changes only the training-frame target to `mean(Y_train)+delta×SD(Y_train)`, with delta in `{-1,-0.5,0,0.5,1}`. This is exploratory and does not replace the frozen target or Research C Primary. The reference-DAG learner is a diagnostic, not a regret-optimal oracle. There is no Research C graph-free baseline in the frozen evidence.

## Information and preservation rules

Recommendation remains graph-and-training-only; evaluation uses the frozen SCM coefficients only after action selection. The exact restored training observations are used in memory, verified against original hashes, and not committed. No new cohort, G0 corruption draw, DRF fit, D intervention response or physical experiment is generated. D unit-level extensions are not run because only aggregated audit records were available locally.

All E findings are post-hoc and conditional on the original frozen synthetic environments. They do not change prior Primary status, establish a new confirmatory result, or imply manufacturing cost savings.

# E-1 — Budget-by-policy performance and marginal benefit

## Evidence scope

Source inputs were the original read-only Research C ledgers (Dev 64 SCM; Held-out 200 SCM) and Research D final independent audit JSON. The C policy-budget datasets contain 5,440 and 17,000 completed rows respectively. All 85 policy×budget cells per cohort were recomputed from each SCM's stored result. The D audit exposes 85 aggregate policy×budget rows and five action summary rows, but no per-G0 results or raw response vectors; D unit-level paired distributions and new bootstrap intervals are therefore unavailable.

## Main patterns

- **C Held-out:** M4 mean regret was 0.093439 at B0, 0.029327 at B1, 0.003988 at B2, 0.001435 at B3 and unchanged at B4. Mean edit count rose from 0 to 0.780. The B1→B2 increment gives the largest M4 improvement per additional edit in this range; B3→B4 adds little and no mean improvement.
- **C Held-out, M2:** increasing budget can make mean regret worse: the B0→B1 marginal benefit is −0.004823, then later increments shrink. This is direct evidence against interpreting more budget as automatically better.
- **C Held-out, Full Greedy:** regret declines from 0.093439 to 0.000964 by B4 while average edits rise to 2.005. This is an aggregate curve; SCM-level improvements and ties remain in the original denominator.
- **C Development:** M4 reaches 0.002928 at B2 and 0.002560 at B3, with no further mean improvement at B4. The full cohort—not a selected task-error subset—is retained.
- **D Final:** the existing aggregate audit shows M4 loss 0.823587→0.790592 from B0 to B2, while M2+M4 and Full Greedy reach 0.789362 at B2. D B3–B4 shows no further aggregate improvement for these policies. These are conditional aggregate descriptions; no new D uncertainty interval was estimated.

Adjacent-budget C comparisons use paired SCM bootstrap intervals (10,000 replicates, seed `2026112601`). They quantify SCM variation within each fixed cohort. Pointwise intervals are not simultaneous across all policies or budgets. D's existing B2 Primary intervals remain those in its final report; they are not repurposed as intervals for every policy or increment.

## Interpretation

The empirical returns diminish and are policy-specific. In C Held-out, M4's average error repair is concentrated in early budget units, while some broader policies continue changing structure without changing action or regret. In D, the saved aggregate curve likewise plateaus early for M4, M2+M4 and Full Greedy. Because D unit rows are unavailable, claims about D-level paired worsening, subgroup behavior, or sampling uncertainty are not made.

The marginal ratio is a ratio of cohort means, not an estimate of the causal effect of one edit. A zero added-edit denominator is marked undefined. Negative marginal benefit is preserved.

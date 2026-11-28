# Final paper outline

## Working title

*Beyond Structural Accuracy: Decision-Oriented Causal Graph Verification and Repair under Budget Constraints*

## Storyline

1. **Motivation and question.** Structural similarity does not directly measure whether a graph supports a good downstream action. Ask how limited verification and repair resources should be allocated for a specified decision task.
2. **Framework.** Define task-relative structural discrepancies, graph repair, limited edit/query budgets, and downstream loss. Separate reference-assisted repair from reference-blind querying.
3. **Research C: frozen synthetic evaluation.** Confirmatory within the signed-linear SCM contract; Primary B=2 S0 versus Full Greedy. Report the paired held-out effect and the single-worse-unit counterexample.
4. **Post-hoc mechanism analysis.** Original-ledger-verified analysis of path restoration, effect-sign errors, greedy ordering, and off-task/DAG interactions. Label all as post-hoc.
5. **Research D: conditional external semisynthetic robustness.** One DRF refit on a public semisynthetic manufacturing sample, fixed training frame, and 200 graph-corruption draws. Report positive primary contrast alongside missed precision targets and graph-free tie.
6. **Research E: budget and cost extension.** Post-hoc budget saturation, Pareto/cost trade-offs, target sensitivity and the restricted Adaptive M4 heuristic. No new SCM cohort.
7. **Research F-Lite: reference-blind verification prototype.** Reused C cohorts; Decision-weighted is below Random regret but above Fit-based/Suspicion-only and near Impact-only. Distinguish query responses from accepted edits.
8. **Cross-study synthesis.** Different information sets and cost units prevent a tested unified algorithm claim. Discuss when known-error repair and unknown-error verification differ.
9. **Limitations and implications.** Oracle-assisted reference information, synthetic/semisynthetic scope, task and target dependence, post-hoc extensions, no measured human or monetary costs, and no field validation.
10. **Conclusion.** Resource allocation should be evaluated against a specified decision objective; no universally best policy is established.

## Recommended figures/tables

- Study map showing evidence grade and information boundary for C, D, E and F-Lite.
- C frozen Primary paired-regret figure/table.
- Mechanism case diagram with both path restoration and the `…000076` DAG-blocker counterexample.
- D action-loss result with all three intervals, graph-free tie and precision shortfall.
- E budget/performance and cost frontier, clearly labeled post-hoc.
- F-Lite held-out policy comparison separating query count, edit count, discovery yield and regret.
- Claim–evidence matrix as supplement.

- Supplementary S1/S2 post-hoc section: distinguish Full Greedy (`M1+M2+M3+M4`) from Canonical Oracle; show gamma-dependent policy ranking and the corrected nested B/E/F saved-feature comparison. Explicitly label the empty-DAG learner and Research F association baseline separately.

Do not place C regret, D tracking loss, E post-hoc contrasts and F query-policy outcomes on one common numeric scale.

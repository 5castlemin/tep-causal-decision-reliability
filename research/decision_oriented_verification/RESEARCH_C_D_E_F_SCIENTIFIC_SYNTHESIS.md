# Research C–D–E–F scientific synthesis

## One research question, four evidence layers

The program asks how limited resources should be allocated to improve decisions made with imperfect causal graphs.

- **C — what to repair:** under a frozen synthetic SCM contract, compare graph-repair policies against downstream decision regret. The Held-out B=2 Primary is S0 minus Full Greedy = +0.07483636 (95% paired-t CI [0.05089822, 0.09877450]).
- **Mechanism analysis — why results differ:** original-ledger-verified post-hoc evidence relates path availability, effect sign, edit order and DAG constraints to performance, while preserving counterexamples.
- **D — external semisynthetic robustness:** one DRF refit to a public semisynthetic sample, one fixed training frame, and 200 graph-corruption draws; not real intervention validation. Its B=2 Primary is +0.03422490 with two-source interval [0.00617347, 0.06535080], while graph-free loss matches Full Greedy and precision targets were missed.
- **E — how much to repair:** post-hoc budget extension, Pareto/cost analysis, adaptive heuristic and target sensitivity on reused C/D inputs; not confirmatory.
- **F-Lite — what to verify first without showing the reference to the policy:** post-hoc query-policy evaluation on the same C SCM cohorts. At B=4 decision-weighted beats random on Held-out but loses to fit-based and suspicion-only; it is not incrementally better than impact-only.

## Integrated interpretation

The evidence supports a conditional principle: graph repair can improve decisions in controlled settings, but graph accuracy, decision value, query value, edit count and evaluator performance are distinct. C gives the strongest confirmatory evidence within its synthetic contract. D offers bounded robustness evidence for one semisynthetic generator. E and F-Lite are exploratory post-hoc analyses. F-Lite weakens any claim that a decision-weighted query heuristic automatically allocates expert attention better than simpler structural heuristics.

No phase demonstrates a field deployment, measured economic savings, safety improvement, expert reliability distribution, or oracle-free discovery of causal truth. The query policy was blind at the interface, while the simulated expert had access to the reference.

## F-Lite final audit note

Read-only final audit corrected the interpretation of Random action changes: at B4 Held-out the average within-SCM share of 32 repeats that changed action was 4.09%, while 27% of SCMs changed at least once. A shared-index bootstrap was added as a pointwise sensitivity analysis; historical intervals were preserved. Stored final pending relations were replayed, with none individually DAG-feasible on the final graph. These corrections do not improve the proposed policy's relative result or change F-Lite's post-hoc status. See `RESEARCH_F_FINAL_AUDIT.md` and `outputs/final_audit_manifest.json`.

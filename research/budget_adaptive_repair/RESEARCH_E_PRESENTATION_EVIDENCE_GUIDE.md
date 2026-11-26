# Research E — presentation evidence guide

## Core message

**A larger edit budget does not imply a uniformly better or more efficient repair policy.** Results depend on which reference-relative errors are present, the metric subset, available edit opportunities, task/target, and how an edit is valued. Evidence is post-hoc and limited to the frozen synthetic C cohorts and one semisynthetic D benchmark.

## Recommended figure sequence

1. **E1 heatmap** — all 17 policies, B0–4; keep C Development and Held-out separate and do not combine with D loss.
2. **E2 cohort curves** — all policy losses/regrets over B; selected policy view emphasizes S0, M4, M2+M4 and Full Greedy.
3. **E3 marginal benefit** — retain negative increments; the ratio to average added edit count is descriptive.
4. **E4 Pareto** — show separate cohort frontiers; include D's graph-free point on the edge-edit-count-only comparison.
5. **E5 lambda choices** — lambda is a hypothetical normalized edit penalty, not money.
6. **E6 saturation** — distinguish structural completion, policy candidate exhaustion, DAG feasibility and unchanged action/loss.
7. **E7 Adaptive M4** — show sparse Held-out blocker evidence, paired uncertainty and counterexamples.
8. **E8 target sensitivity** — action set fixed; changing target changes the task.

Every chart is exploratory/descriptive, uses original SCM units for C, and uses aggregate-only fixed-DGP evidence for D where applicable. Pointwise intervals are not simultaneous. Match each SVG under `figures/` with the corresponding aggregate CSV under `outputs/`.

## Suggested result table

| Cohort | Unit | Key result | Inference boundary |
|---|---|---|---|
| C Held-out | 200 original independent synthetic SCMs | M4 regret 0.093439 at B0, 0.001435 at B3/B4; M2+M4 B4 0.000964 at 1.440 edits | Post-hoc extension; original C Primary remains unchanged |
| C budget extension | Same 64/200 SCMs | Bmax 7/9; canonical structural restoration complete at cohort cap | Hash-identically restored existing inputs, not new SCMs |
| D Final | 200 graph-corruption draws conditional on one DGP | Graph-free association mean loss 0.789362 equals Full Greedy at B2 with zero graph edits | Saved aggregate only; not 200 independent SCMs; no new uncertainty |

## Questions to prepare for

- **Does more budget always help?** No. Some policy/unit increments are negative; individual outcomes are non-monotone.
- **Is M4 best?** No universal claim. Held-Out M4 is efficient at low budgets, while other combinations reach a lower observed mean at larger budgets; frontiers are sample summaries.
- **Did Adaptive M4 solve the cycle blocker?** Only a bounded one-blocker case was evaluated. Two blocker repairs occurred in Held-Out; the interval touches zero and evidence is exploratory.
- **Does this show factory cost savings?** No. Edge count is only a structural edit-count proxy.
- **Is the graph known in deployment?** No. Repair is Oracle-assisted against a reference DAG.
- **Did we validate manufacturing interventions?** No. D is a DRF-based semisynthetic generator, not physical intervention evidence.
- **Why no D budget extension?** The accessible audited artifacts lacked unit-level recommendations and response vectors; no synthetic substitute was fabricated.
- **What remains uncertain?** D's original MC-only and combined precision targets were missed. E did not address that by generating more samples. Generator-fit and training-frame variation remain outside scope.

## Claims to avoid

Do not claim that M4 is always best, all off-task errors are harmless, more edits necessarily improve decisions, a Pareto point is statistically superior, Adaptive M4 is general, graph-based recommendations beat graph-free learning, or the findings establish factory deployment or monetary savings.

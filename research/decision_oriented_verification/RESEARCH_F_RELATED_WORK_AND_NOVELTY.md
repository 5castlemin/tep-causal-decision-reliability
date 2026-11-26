# Related work and novelty boundary

This is a scoped comparison of directly relevant sources, not a systematic review or priority search.

## Closest overlap

Ibrahim, John, Guo and Kaski's *Targeted Causal Elicitation* (NeurIPS 2022 workshop) studies learning causal structure for a fixed downstream causal-effect optimization task. It augments a Bayesian model with a domain-expert user model and discusses task-informative active elicitation. This is a close conceptual predecessor to decision-oriented graph queries; F-Lite must not claim the general idea of targeting expert queries to downstream decisions as novel. [OpenReview paper](https://openreview.net/pdf?id=oqRw-a4rf36)

Ankan and Textor's *Expert-In-The-Loop Causal Discovery: Iterative Model Refinement Using Expert Knowledge* (UAI 2025) iteratively uses data-driven conditional-independence diagnostics to locate missing or superfluous edges, then incorporates expert orientations and ranks candidate edges by model-fit impact. It overlaps with query-guided iterative repair, though F-Lite uses a fixed pair query protocol and scores suspicion/decision impact rather than their workflow. [PMLR paper](https://proceedings.mlr.press/v286/ankan25a.html)

Bonilla, Zhao and Steinberg's *Causal Preference Elicitation* (ICML 2026) models three-way noisy expert judgments over edge existence/direction, and selects queries by expected information gain to concentrate a graph posterior. This is materially more principled and explicitly noise-aware than the F-Lite heuristic. [PMLR paper](https://proceedings.mlr.press/v306/bonilla26a.html)

## Evaluation context

Peters and Bühlmann's Structural Intervention Distance evaluates graph differences in terms of intervention statements, illustrating why adjacency accuracy alone need not represent decision relevance. F-Lite evaluates downstream action regret from a fixed learner and finite action grid rather than proposing a graph-distance metric. [Paper](https://people.math.ethz.ch/~peterbu/Files/Manuscripts/SID-final.pdf)

## Defensible contribution wording

F-Lite is a small, post-hoc, reference-blind *query-policy prototype* evaluated on previously used Research C SCMs. Its empirical contribution is the side-by-side diagnostic of four simple query heuristics under a fixed regret task and query budget, including evidence that the product score did not improve on simpler fit/suspicion baselines in the reused Held-out cohort. It is not a new general framework for targeted elicitation, Bayesian active learning, or expert-in-the-loop causal discovery. No systematic novelty claim is made.

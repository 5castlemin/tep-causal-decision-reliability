# Contribution and novelty boundaries

## Defensible contribution

The project evaluates causal graph repair against downstream decision loss under bounded resources, and explicitly separates structural correctness, action choice, and decision outcome. Research C provides the frozen synthetic comparison; the mechanism analysis explains selected pathways post hoc; D tests conditional robustness in one external semisynthetic generator; E and F-Lite add post-hoc budget and reference-blind verification evidence.

## Relationship to adjacent work

The repository's related-work review identifies overlap with targeted causal elicitation, expert-in-the-loop causal discovery, and causal preference elicitation. The defensible distinction is the project's combined experimental framing around task-relative graph repair, a bounded edit budget, and measured downstream regret in its specified synthetic contract. This is a scope distinction, not a verified novelty claim. A systematic literature review was not performed.

## Claims to avoid

- “First,” “novel algorithm,” or “state of the art” without a systematic review and comparative evidence.
- A unified Fit-based verification + M4 repair + Pareto stopping algorithm: no such integrated algorithm was tested.
- General superiority of M4, graph-based methods, the F-Lite proposed weighted verifier, or Adaptive M4.
- Real expert effectiveness, manufacturing savings, safety, deployment readiness, or field validation.
- Generalization from D to manufacturing populations or from F's reused SCMs to a new cohort.

## Evidence grades

- C Primary: confirmatory within the frozen synthetic SCM contract.
- M4: Development-selected Secondary.
- Mechanism: original-ledger-verified post-hoc analysis.
- D: conditional external semisynthetic robustness, one fitted DGP.
- E: post-hoc budget/cost/adaptive/target extension.
- F-Lite: post-hoc reference-blind query-policy prototype on reused C units.

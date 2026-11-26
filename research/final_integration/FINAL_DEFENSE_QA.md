# Final defense: likely questions and evidence-based answers

### Does a more accurate graph always improve the decision?

No. The studies record cases where graph changes leave the action unchanged and cases where a structurally valid correction worsens regret. In the specified C learner, path presence and effect sign strongly explain outcomes, but this is not a universal theorem.

### Is M4 always best?

No. It is Development-selected Secondary in C, loses to Full Greedy in a held-out case, and its performance depends on task definition, budget, target, and graph structure. E's Adaptive M4 is a one-blocker exploratory heuristic, not a general solution.

### Did the work validate a real factory?

No. C is synthetic. D is one DRF fitted to a public semisynthetic manufacturing dataset, not measured factory interventions. No operational cost, safety, or deployment outcome was measured.

### Why do C and D show different effect sizes?

They use different DGPs, task/reference structures, outcome losses, analysis units, learner-training data and uncertainty sources. Their absolute estimates should not be directly compared or attributed to one differing factor.

### Did reference-blind F-Lite beat simpler methods?

Not on the main Held-out average. Decision-weighted beat Random, but Fit-based and Suspicion-only had lower regret and Impact-only was nearly tied. It is a post-hoc prototype, not confirmatory evidence.

### Does F-Lite avoid access to the true graph?

The policy interface receives an allow-listed input without the reference, but the simulated expert answers from the reference. Components run in the same Python process, not an OS sandbox. It is not a fully reference-free real-world study.

### Are verification queries equivalent to graph edits?

No. A query is an expert response; an edit is an accepted graph change. A cycle-blocked answer can remain pending. We report query count and edit count separately.

### What does “cost” mean?

For C/D/E repair policies, it is atomic edge-edit count. In F-Lite the response-query budget is separate. Neither is actual staff time, money, or verification effort.

### What is the central practical lesson?

Treat graph repair and verification as task- and budget-dependent resource allocation problems, and evaluate the resulting action. The evidence does not identify one universally optimal policy.

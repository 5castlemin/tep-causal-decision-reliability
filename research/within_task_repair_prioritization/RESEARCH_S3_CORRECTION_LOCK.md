# Research S3 correction execution lock

**Status:** locked before corrected Research C result recomputation; post-hoc exploratory only.
**Base:** `a230ab96e2e204c5d72ed34b049190ae3c6bb276`.

## Fixed scope
- Cohorts: original Research C Development (64) and Held-out (200) only.
- Metrics: all 63 nonempty equal-weight subsets of T1–T6.
- Greedy budgets: B=0–4; compare S0, frozen M4, frozen Full Greedy, Canonical Oracle, M4-Original, exact expected Random-M4, and four error-type-priority M4 variants.
- Lookahead: all 63 subsets at B=2 if the preregistered compute feasibility check passes; otherwise the fixed 13-set list from the historical lock. Any reduction is decided before corrected outcome calculations and recorded.
- Bootstrap: 10,000 paired SCM resamples, common cohort-specific indices, seed 2026112701. Main comparisons and Holm adjustment are explicitly post-hoc; bootstrap intervals are pointwise.
- Fixed T-gain tie tolerance: absolute 1e-12 in gain-per-cost units.
- Greedy choice: maximize selected-subset structural gain/cost; within tolerance maximize frozen M4 gain/cost; then frozen canonical metric, pair, operation order. A candidate is eligible if either gain is positive beyond tolerance. No outcome value enters selection.
- Lookahead: choose the shortest improving feasible sequence (one or two edits); within a length compare equal-weight selected structural gain per cost, then summed M4 gain/cost, then canonical sequence order. If no feasible two-step sequence exists, use exactly the one-step Greedy selector for that metric subset. Zero-gain first edits are allowed when the complete two-edit sequence has positive structural gain.
- T5: transitive closure over all directed nodes in the learner graph, then score ancestor pairs restricted to the fixed task-zone node set. UNRES edges are not traversed.
- Candidate-level actual Regret is used only in a separate evaluator after normal-policy trajectories and selected structures are hash-locked; ex-post oracle outputs never affect recommendations.
- Objective sensitivity uses frozen trajectories and gamma in {0,.2,.5}; no new data or response generation.
- Input DBs remain read-only; exact byte hashes must match before and after analysis.
- Outputs use a new versioned directory. Historical S3 outputs remain unchanged and labelled superseded where appropriate.

## Stop conditions
Stop and report incomplete if exact input hashes/bindings fail, frozen C replay does not match, a required output would overwrite prior results, or the analysis uses evaluation outcomes in policy selection. Do not substitute units or seeds.

## Chronology
The original S3 calculation preceded its immutable code commit, and all S3 evidence remains exploratory. This correction lock only improves reproducibility of the correction; it does not retroactively create preregistration or confirmatory status.

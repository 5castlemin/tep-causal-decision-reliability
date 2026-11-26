# Presentation evidence guide — Research F-Lite

## Suggested narrative

1. **Problem:** graph quality and decision quality are not the same target.
2. **C/E:** first compare repairs and budget trade-offs when a reference is available.
3. **F-Lite question:** what if the policy cannot see the reference and must ask an expert about one pair at a time?
4. **Method:** four pair-query rules, fixed B=0–4, existing C Development/Held-out SCMs, same learner/action/loss.
5. **Information boundary:** the policy is reference-blind; the simulated expert is not. This is a software-interface distinction, not a real blinded human study.
6. **Result:** on Held-out, decision-weighted beats random but loses to fit-based and suspicion-only at B=4; nearly all its comparisons with impact-only tie.
7. **Takeaway:** decision impact is a useful design consideration, but the tested product heuristic did not show incremental value.

## Recommended figures

- `figures/F1_budget_performance_heatmaps.svg`: all policy families, separate cohorts.
- `figures/F2_budget_curves.svg`: budget curves; label C regret, not manufacturing loss.
- `figures/F3_heldout_paired_contrasts.svg`: B=4 paired comparator-minus-proposal intervals.
- `figures/F4_discovery_vs_regret.svg`: discovery counts are not decision value.
- `figures/F5_queries_and_regret.svg`: query burden and downstream regret.
- `figures/F6_blind_oracle_graphfree_comparison.svg`: distinguish Oracle M4 and graph-free diagnostics.
- `figures/F7_reference_blind_query_fixture.svg`: toy interface illustration only, not an observed SCM case.
- `figures/F8_expert_noise_sensitivity.svg`: include only after the optional sensitivity run and audit complete.
- `figures/F9_research_framework.svg`: role separation at the interface level.

Do not use an expert-noise figure unless the corresponding sensitivity output exists. Any case vignette needs its SCM key, full query/answer history, edited graph and loss source linked; otherwise report the aggregate only.

## Do not overstate

- “The method is novel” or “first decision-aware causal elicitation.”
- “The policy is fully oracle-free” or secure sandboxed.
- “The proposed score is better than simple baselines.”
- “Held-out is a new independent F test.”
- “Simulated expert accuracy represents human experts.”
- “Edge/query counts are dollars, labor hours, or factory savings.”

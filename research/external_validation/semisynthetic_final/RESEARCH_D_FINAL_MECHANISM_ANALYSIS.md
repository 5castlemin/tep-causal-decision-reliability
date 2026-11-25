# Research D final mechanism analysis

At B=2 the policy ranking is not a ranking of graph accuracy alone. M1/M2/M3 primarily address errors in their own metric families and average losses stayed near S0. M4 corrected task-zone discrepancies and reduced mean target-tracking loss to `0.790592` at mean cost 0.335. M4+M2 achieved the lowest B=2 average loss (`0.789362`) among the 17 policies, but this was exploratory/secondary, not the primary. Full Greedy's average loss was `0.789362` at mean cost 1.160. Canonical Oracle is a structure-only reference baseline and had loss `0.798584`; it is not regret-optimal.

## Repair-to-action relation

- Full Greedy changed the S0 action in 56/200 cases; these 56 improved loss and the remaining 144 tied.
- Structural error counts decreased for Full Greedy in 152 cases; 96 of those retained the same action, so measurable structural repair often did not change the decision.
- M4 matched Full Greedy's selected action in 198/200 cases but matched the repaired graph in only 69/200. Thus distinct repair paths often led to the same recommended action.
- M4 used fewer edits than Full Greedy by 0.825/G0 on average. The saving was in edits, not money, engineering hours, or maintenance burden.
- The association baseline picked the first action, whose evaluator loss matched its mean loss. This demonstrates that under this target and training-conditioned setup a graph-free rule was competitive with the primary policy's aggregate loss. It does not identify a causal effect.

The action values and target were fixed before final response generation. All action response means were below target; therefore the observed decision task mostly ranks which supported action is closer to an externally fixed target that was above the observed means. That pattern is conditional on the fitted DRF and finite evaluator draws. It is not evidence that the physical process cannot reach the target.

The 200 graph draws share one reference, one fitted generator and one learner frame. Their intervals quantify the prespecified graph-corruption distribution plus finite intervention Monte Carlo variation only. The original Research C population over independently sampled SCMs and its absolute regret are not reproduced.

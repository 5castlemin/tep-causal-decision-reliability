# Paper contribution guide — Research F-Lite

## Research question progression

- C: Which graph repair policy helps downstream decisions under a limited edit budget?
- D: Does the C result also appear in one external semisynthetic DGP?
- E: How do repair budget and edit-count preference change observed trade-offs?
- F-Lite: When the repair policy cannot see the reference, which relation should be verified first?

These are connected but distinct analyses. F-Lite reused the C SCM cohorts and is post-hoc.

## Defensible contribution

The contribution is a transparent prototype and empirical diagnostic: compare fit, suspicion, decision impact, and their product as pair-query heuristics under an existing downstream regret task. On the reused Held-out cohort the product heuristic beats random, but is worse than fit-based and suspicion-only and nearly tied with impact-only. The negative result is central; do not frame the method as a validated winning policy.

## Management relevance

The work motivates allocating scarce model-review attention using both model uncertainty and downstream decision consequences. It does not estimate a formal value of information or actual review cost. Query count and edge-edit count are operational proxies only.

## Prior literature and novelty

Targeted Causal Elicitation already connects expert queries to a fixed downstream optimization objective; Expert-In-The-Loop Causal Discovery and Causal Preference Elicitation study iterative or Bayesian expert query methods. F-Lite is not the first method to target causal elicitation at decisions. Its narrow contribution is an exploratory comparison on a reused causal repair benchmark with decision-regret outcomes.

## Likely questions

**Is F fully oracle-free?** The policy interface does not receive the reference, but the simulated expert does and returns the queried pair's answer. There is no OS-level sandbox.

**Is suspicion a probability?** No. It is a score derived from local Gaussian BIC alternatives and is not calibrated.

**Does the product score help?** Not clearly. In Held-out it loses to fit and suspicion alone and ties impact-only on most SCMs.

**Why distinguish query and edit cost?** A query can return a correct answer that does not change the current graph, including cycle-pending relations; a question and a graph edit are different resource events.

**Does more accurate structure ensure better decisions?** No. Repair can leave the selected action unchanged, change it in an unhelpful way, or conflict with the target/action grid.

**Is this validated for manufacturing?** No. C and F are synthetic SCM analyses; D is semisynthetic and conditional on one fitted DGP.

**What does expert-noise sensitivity mean?** Only a predeclared hypothetical error process, not measured human accuracy.

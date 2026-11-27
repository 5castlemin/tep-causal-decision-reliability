# S4 policy redundancy and opportunity analysis

## Initial and dynamic candidate sets

Initial M4 candidate count K is the number of initially DAG-feasible, direct task edits. The full distribution and per-unit K>B indicators are in private external artifact root / `opportunity_budget_unit_diagnostics.csv` (private). General K was mostly 0–1 (26/32); Opportunity-rich was selected at K≥2, with 26/32 at K=2. Thus the “opportunity-rich” group mostly had only the minimum eligibility count, not abundant choice.

A structure-only traversal of each saved G0 after each initially feasible M4 edit found 26 initial candidates / 16 first-edit transitions in General and 75 initial candidates / 75 transitions in Opportunity-rich. Remaining legal candidates after a first edit: General 10 transitions had zero, 8 had one, 3 had two, 4 had three; Opportunity-rich 49 had one, 12 had two, 8 had three, 6 had five. Three Opportunity-rich first-edit states made an initially infeasible M4 candidate feasible. This is dynamic structural feasibility, not dynamic edit value.

## Policy redundancy

The 63 B=1 trajectories are materialized as 4,032 unit-policy rows. Final graph, selected action, and regret agreement are separate measures in `policy_redundancy_b1_b2.csv`. At B=2 the original saved evaluator rows provide all 63 T subset results. The pilot previously found 56/63 General subsets with mean regret zero and 59/63 Opportunity-rich subsets matching M4’s mean regret. Mean agreement can conceal unit-level differences; graph/action overlap is therefore reported separately.

The retrospective table compares only policies at the same budget. It does not preserve B=2 edit sequences, so sequence/order redundancy at B=2 is `NOT_AVAILABLE`; graph-hash equality is the supported structural redundancy measure. At B=1, selected pair and operation are in the private-derived unit table; only aggregate data are published.

## Optimality miss cases

M4 at B=2 matched the saved ex-post no/one/two-edit optimum in 31/32 units in each cohort. The two non-matching units are:

| Cohort | Unit | K | feasible ordered 2-edit sequences | M4 B2 regret gap |
|---|---|---:|---:|---:|
| General | `s4-general-019` | 4 | 12 | .3008403 |
| Opportunity-rich | `s4-opportunity_rich_diagnostic-022` | 2 | 2 | .0293325 |

These are isolated diagnostics from small conditional cohorts, not population failure rates. The pilot’s <=2-edit ex-post benchmark enumerates a limited feasible universe and is outcome-aware; it is not a deployable policy or unrestricted optimum.

## B=1 redundancy by initial K

An additional locked, aggregate-only table stratifies the B=1 T-subset versus saved M4 comparison by exact initial K. In General, all 63 subsets were tied with M4 for K=0 (16 SCMs) and K=1 (10 SCMs); differences occurred for 8/63 subsets at K=2 (4 SCMs) and 56/63 at K=4 (1 SCM). At K=3, the sole SCM was tied. In the selected opportunity-rich cohort, 60/63 subsets had at least one non-tied unit at K=2 (26 SCMs), while K=3 (3 SCMs) and K=6 (1 SCM) were tied for every subset; only 1/63 subsets had a non-tied unit at K=4 (2 SCMs).

This shows that B=1 policy separation was concentrated in some higher-opportunity units, especially the selected K=2 group, but is not a monotone relation with K and is not an estimate of a causal K effect. Tiny cells, one SCM at General K=4, structural selection into the opportunity-rich group, and the 63 highly redundant subsets limit interpretation. The full table is `k_stratified_outputs/b1_policy_differences_by_initial_K.csv`; its input hashes and no-generation status are recorded in `k_stratified_outputs/summary.json` and the retrospective manifest.

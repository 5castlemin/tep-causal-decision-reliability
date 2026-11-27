# S4-1B: B=1 policy results

Classification: post-hoc exploratory reaggregation of saved unit-level pilot outcomes. Results are conditional on the two pilot cohorts and `gamma=0`.

All 63 nonempty T1–T6 combinations were selected at B=1 from saved candidate structural gains. Recommendation graph hashes were joined to the already locked recommendation manifest; single-edit regret gains were joined from the saved candidate table. No evaluator or learner was rerun. Output: `outputs_attempt4/b1_all_63_policy_aggregates.csv` (128 cohort-policy rows); 4,032 unit-policy recommendations are retained only in the private external artifact root.

For B=1, `T−M4` is paired within SCM; negative favors T. Singletons:

| Cohort | T set | Mean T−M4 regret | Pointwise 95% SCM bootstrap | T better / worse / tie | Same graph as M4 | Action differs from M4 |
|---|---|---:|---:|---:|---:|---:|
| General | T1 | .024635 | [−.018803,.083415] | 1/2/29 | 81.3% | 9.4% |
| General | T2 | .000000 | [0,0] | 0/0/32 | 96.9% | 0% |
| General | T3 | .000000 | [0,0] | 0/0/32 | 96.9% | 0% |
| General | T4 | −.009401 | [−.028204,0] | 1/0/31 | 96.9% | 3.1% |
| General | T5 | −.009401 | [−.028204,0] | 1/0/31 | 93.8% | 3.1% |
| General | T6 | .000000 | [0,0] | 0/0/32 | 100% | 0% |
| Opportunity-rich | T1 | −.025519 | [−.104317,.041202] | 4/2/26 | 37.5% | 18.8% |
| Opportunity-rich | T2 | .000000 | [0,0] | 0/0/32 | 90.6% | 0% |
| Opportunity-rich | T3 | .024667 | [0,.074002] | 0/1/31 | 75.0% | 3.1% |
| Opportunity-rich | T4 | .000000 | [0,0] | 0/0/32 | 100% | 0% |
| Opportunity-rich | T5 | −.000917 | [−.002750,0] | 1/0/31 | 71.9% | 3.1% |
| Opportunity-rich | T6 | .001518 | [−.002750,.007304] | 1/1/30 | 87.5% | 6.3% |

Full Greedy’s paired B=1 difference from M4 was +.015759 (CI [0,.047278]) in General, with 0 better/1 worse/31 ties; in Opportunity-rich it was +.037777 (CI [−.002929,.097788]), with 2 better/3 worse/27 ties. Positive `Full Greedy−M4` means Full Greedy has higher regret. At B=2 the corresponding M4−Full Greedy results are retained in the correction report.

The B=1 average edit cost was .5 in General and 1.0 in Opportunity-rich. The difference follows the K distribution and structural selection; it does not indicate an economic cost. Sparse nonzero differences and wide intervals preclude a stable ranking. Across 63 subsets, the prior pilot’s many identical outcomes and the new B=1 results demonstrate substantial redundancy, not 63 independent policy tests.

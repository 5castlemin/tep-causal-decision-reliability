# S4-1B: B=1 policy results

Classification: post-hoc exploratory reaggregation of saved unit-level pilot outcomes. Results are conditional on the two pilot cohorts and `gamma=0`.

All 63 nonempty T1–T6 combinations were selected at B=1 from saved candidate structural gains. Recommendation graph hashes were joined to the already locked recommendation manifest; single-edit regret gains were joined from the saved candidate table. Selection matches the S3 implementation, including M4 fallback if all T gains are nonpositive and no-edit if no positive M4 fallback exists. No evaluator or learner was rerun. Output: `outputs_attempt7/b1_all_63_policy_aggregates.csv` (126 cohort-policy rows); 4,032 unit-policy recommendations are retained only in the private external artifact root.

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

### Initial opportunity-count strata (descriptive)

A separately locked, aggregate-only retrospective reaggregation compares each B=1 T subset with the saved M4 B=1 result within exact initial K. It uses the same 64 pilot SCMs and fixed saved outcomes; the 567 output rows are cohort × K × subset aggregates, not independent observations. No per-stratum confidence intervals are reported.

| Cohort | Initial K | SCMs | T subsets with any non-tied regret | Mean across subsets of absolute mean paired difference |
|---|---:|---:|---:|---:|
| General | 0 | 16 | 0/63 | 0.000000 |
| General | 1 | 10 | 0/63 | 0.000000 |
| General | 2 | 4 | 8/63 | 0.034577 |
| General | 3 | 1 | 0/63 | 0.000000 |
| General | 4 | 1 | 56/63 | 0.267414 |
| Opportunity-rich diagnostic | 2 | 26 | 60/63 | 0.016104 |
| Opportunity-rich diagnostic | 3 | 3 | 0/63 | 0.000000 |
| Opportunity-rich diagnostic | 4 | 2 | 1/63 | 0.004200 |
| Opportunity-rich diagnostic | 6 | 1 | 0/63 | 0.000000 |

The larger differences in General K=4 arise from one SCM and are not population-level evidence of a K interaction. The opportunity-rich K=2 stratum has more units but remains selected and conditional; 60/63 subset aggregates contain at least one unit-level non-tie, while many subsets still agree on average or choose the same action. This descriptive pattern is consistent with scarcity creating room for priority differences, but does not show that larger K alone causes policy separation. The full aggregate CSV retains mean/median paired regret, better/worse/tie counts, and graph/action agreement for every cell.

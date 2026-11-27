# 63-subset greedy analysis

All 63 nonempty T1–T6 subsets were evaluated separately at B=1,2,3,4 on both original cohorts. Cohort-level mean/median regret, mean edit count, action-change rate, first-edit disagreement with M4, number of distinct final graphs and fallback rate are available in `tables/s3_policy_aggregates.csv`. All 63 remain exploratory; table minima are not confirmatory policy selection.

At B=1, the six-metric policy averaged 0.002560 regret in Development and 0.021573 in Held-out, compared with M4 0.023753 and 0.029327, respectively. T3 alone averaged 0.002560 in Development and 0.031271 in Held-out. These cohort differences and the retrospective policy development make the ranking unstable as a general claim. At B=2, Held-out T4+T5 and T5 had the lowest observed means (about 0.002790), while the six-metric subset was 0.003717 and M4 0.003988. Tie/trajectory duplication means 63 specifications are not 63 independent evidence sources.

## Lowest observed B=1/B=2 means (descriptive only)

| Cohort | B | Metric subset | Mean regret | Mean edits |
|---|---:|---|---:|---:|
| C_DEVELOPMENT | 1 | T1+T2+T3 | 0.002560 | 0.484375 |
| C_DEVELOPMENT | 1 | T1+T2+T3+T4 | 0.002560 | 0.484375 |
| C_DEVELOPMENT | 1 | T1+T2+T3+T4+T5 | 0.002560 | 0.484375 |
| C_DEVELOPMENT | 1 | T1+T2+T3+T4+T5+T6 | 0.002560 | 0.484375 |
| C_DEVELOPMENT | 1 | T1+T2+T3+T4+T6 | 0.002560 | 0.484375 |
| C_DEVELOPMENT | 2 | T1+T2 | 0.002560 | 0.656250 |
| C_DEVELOPMENT | 2 | T1+T2+T3 | 0.002560 | 0.656250 |
| C_DEVELOPMENT | 2 | T1+T2+T3+T4 | 0.002560 | 0.656250 |
| C_DEVELOPMENT | 2 | T1+T2+T3+T4+T5 | 0.002560 | 0.656250 |
| C_DEVELOPMENT | 2 | T1+T2+T3+T4+T5+T6 | 0.002560 | 0.656250 |
| C_HELDOUT | 1 | T4+T5 | 0.020645 | 0.515000 |
| C_HELDOUT | 1 | T4+T5+T6 | 0.020645 | 0.515000 |
| C_HELDOUT | 1 | T4 | 0.020781 | 0.515000 |
| C_HELDOUT | 1 | T4+T6 | 0.020781 | 0.515000 |
| C_HELDOUT | 1 | T1+T2+T3+T4+T5 | 0.021573 | 0.515000 |
| C_HELDOUT | 2 | T4+T5 | 0.002790 | 0.695000 |
| C_HELDOUT | 2 | T4+T5+T6 | 0.002790 | 0.695000 |
| C_HELDOUT | 2 | T5 | 0.002790 | 0.695000 |
| C_HELDOUT | 2 | T4 | 0.002926 | 0.695000 |
| C_HELDOUT | 2 | T1+T2+T3 | 0.003717 | 0.695000 |
# Mechanism analysis

Within a fixed SCM, legal M4 edits can have widely different regret gains. Role-specific candidate aggregates are in `tables/s3_candidate_value_aggregates.csv`; they are averaged within SCM before cohort-level inference. In Held-out, task false-positive deletions (other_task_fp) were sparse and their mean gain was close to zero; path-related FN and REV groups showed larger positive averages in several cells, while backdoor-related groups were near zero or negative. The intervals and counts must be read alongside those means.

This supports heterogeneity as a post-hoc pattern, not a universal causal ranking. An edge can affect prediction through other paths, and a structure-only score does not measure effect sign or magnitude. Ex-post best feasible edge selection and full edit interaction analysis were not run.

## Candidate opportunity and one-edit regret gain

| Cohort | Error | Structural role | Candidates | SCMs | Mean within-SCM regret gain | 95% SCM-cluster interval |
|---|---|---|---:|---:|---:|---:|
| C_DEVELOPMENT | FN | path_and_backdoor | 1 | 1 | 0.590383 | [0.590383, 0.590383] |
| C_DEVELOPMENT | FN | path | 9 | 9 | 0.277498 | [0.114191, 0.452009] |
| C_DEVELOPMENT | FN | backdoor | 3 | 3 | 0.000000 | [0.000000, 0.000000] |
| C_DEVELOPMENT | FP | other_task_fp | 8 | 7 | 0.060405 | [-0.010090, 0.191305] |
| C_DEVELOPMENT | REV | path | 11 | 11 | 0.165728 | [0.082703, 0.248295] |
| C_DEVELOPMENT | UNRES | path | 8 | 6 | 0.200486 | [0.011717, 0.455112] |
| C_DEVELOPMENT | UNRES | backdoor | 6 | 5 | 0.000000 | [0.000000, 0.000000] |
| C_HELDOUT | FN | path_and_backdoor | 4 | 4 | 0.084697 | [0.000000, 0.254091] |
| C_HELDOUT | FN | path | 43 | 39 | 0.195117 | [0.121275, 0.273851] |
| C_HELDOUT | FN | backdoor | 6 | 6 | 0.072670 | [0.000000, 0.218011] |
| C_HELDOUT | FP | other_task_fp | 20 | 17 | -0.018297 | [-0.089481, 0.049865] |
| C_HELDOUT | REV | path_and_backdoor | 2 | 2 | 0.000000 | [0.000000, 0.000000] |
| C_HELDOUT | REV | path | 18 | 17 | 0.159040 | [0.052577, 0.293581] |
| C_HELDOUT | REV | backdoor | 11 | 11 | -0.002479 | [-0.007436, 0.000000] |
| C_HELDOUT | UNRES | path_and_backdoor | 2 | 2 | 0.000000 | [0.000000, 0.000000] |
| C_HELDOUT | UNRES | path | 39 | 36 | 0.176855 | [0.102870, 0.255535] |
| C_HELDOUT | UNRES | backdoor | 12 | 10 | 0.000000 | [0.000000, 0.000000] |
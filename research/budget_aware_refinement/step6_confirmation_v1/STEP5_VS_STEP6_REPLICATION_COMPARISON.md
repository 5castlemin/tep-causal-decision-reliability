# Step 5 Development vs Step 6 Held-Out Descriptive Comparison

## Scope

Step 5 (`N=64`) and Step 6 (`N=200`) are separate cohort namespaces with the same frozen master-seed number and domain-separated RNG keys. Step 6 was not used to alter the design. This is a descriptive comparison, not an inferential test between cohorts and not confirmatory evidence under Option B.

## SCM-level paired differences

| Cohort | n complete | Mean `D_i` | Median | SD | Positive / negative / zero | Range |
|---|---:|---:|---:|---:|---:|---:|
| Step 5 development | 64 | 0.0146605 | 0 | 0.0621579 | 6 / 1 / 57 | [-0.0006981, 0.4195602] |
| Step 6 held-out | 200 | 0.0200725 | 0 | 0.0824273 | 25 / 8 / 167 | [-0.1447869, 0.6097471] |

Both cohort means are positive and both distributions have a median of zero. This is directionally similar descriptive evidence, with substantial zero mass and both positive and negative nonzero SCMs in Step 6. It does not establish policy superiority.

## Error-type comparison

| Type | Step 5 mean `D` | Step 6 mean `D` | Step 5 Global / Task-Focused regret means | Step 6 Global / Task-Focused regret means |
|---|---:|---:|---:|---:|
| FN | 0.0058258 | 0.0307732 | 0.0083625 / 0.0025367 | 0.0493737 / 0.0186005 |
| FP | 0 | 0.0021787 | 0.0010743 / 0.0010743 | 0.0108991 / 0.0087204 |
| REV | 0.0381557 | 0.0272656 | 0.0406924 / 0.0025367 | 0.0419844 / 0.0147188 |

REV was the largest Step 5 type mean; FN was slightly larger than REV in Step 6. FP remained close to zero. The type pattern is not identical, and no type-specific superiority claim is warranted.

## Output agreement and cohort composition

Both cohorts had the same selected action for Global and Task-Focused in every paired type case (Step 5 64/64; Step 6 200/200). Final graph agreement was lower in Step 6: FN 62.0% vs 71.9%, FP 45.5% vs 51.6%, REV 53.5% vs 59.4%. Selected-`k` agreement was FN 93.0% vs 95.3%, FP 98.5% vs 100%, and REV 87.5% vs 92.2% (Step 6 vs Step 5). Different graphs frequently still produced the same action, while a small set of differing selected-`k` cases contributed to regret differences.

Step 5 template counts were chain 17, fork 5, multiple paths 32, common cause 10. Step 6 counts were 49, 28, 88, and 35, respectively. These counts are consistent with separate draws under the same proposal distribution and strict eligibility conditioning; no post-hoc weights were used. Delta was balanced in both: Step 5 32/32 and Step 6 100/100.

## Extreme-value sensitivity

| Cohort | Full mean | Excluding largest `D_i` | Excluding two largest `D_i` | Largest one / two share of summed `D_i` |
|---|---:|---:|---:|---:|
| Step 5 | 0.0146605 | 0.0082335 | 0.0046345 | 44.7% / 69.4% |
| Step 6 | 0.0200725 | 0.0171093 | 0.0143115 | 15.2% / 29.4% |

The development mean was more concentrated in its top two cases. Step 6's mean remained positive after removing the two largest values, but this is a pre-specified descriptive sensitivity only; the full mean remains primary. Neither cohort is modified or selectively filtered.

## Denominators and conclusions

Step 5: 211 proposals = 145 structural rejections + 2 topology/task failures + 64 admissions; 64/64 complete; no post-admission failure, missing type, fallback, or cap stop.

Step 6: 675 proposals = 466 structural rejections + 9 topology/task failures + 200 admissions; 200/200 complete; no post-admission failure, missing type, fallback, or cap stop.

The two cohorts provide consistent positive SCM-level mean descriptions but sparse, heterogeneous differences, with both signs and many exact ties. The results support reporting and further research, not a confirmatory superiority conclusion or a claim about real-world DAT interventions. Step 4 remains FROZEN; no Step 6 retuning or additional sampling was performed.

# S4 Independent T5 Replication — Primary Results

Run: `s4-t5-independent-replication-20261128-v1`  
Execution code revision: `f60f50f0d6f11cc2b8135607e7ddf99a7e19d730`  
Classification: new independent replication within an outcome-blind Q-common-admitted strict-indirect population; analytic, post-hoc extension of the broader project

## Generation

The fixed 160 SCM target completed after 560 proposal screens. It generated 81,920 observational rows and 160 analysis G0 draws. The sealed recommendation manifest contained 746 distinct SCM-graph recommendation states, mapping to 22,720 policy-budget rows. No intervention-response rows were generated. The primary denominator retains all 160 SCMs, including units with no feasible M4 edit. The initial feasible M4 candidate distribution was 0: 63, 1: 56, 2: 27, 3: 8, 4: 6; 41/160 had at least two candidates.

## Frozen primary: T5-guided M4 minus Frozen M4, B=1, gamma=0

The estimand is the SCM-paired analytic-regret difference `T5_GUIDED_M4 − M4`; negative values favor T5. The mean difference was **−0.0086644**, median 0, with a 10,000-replicate SCM paired percentile interval **[−0.0203910, 0.0000000]**. T5 had lower regret on 4 SCMs, higher regret on 1, and tied on 155. The interval includes zero; superiority is not established. Its half-width is approximately 0.01020, slightly above the predeclared 0.010 precision target. No SESOI was set.

T5 and Frozen M4 had equal mean edit count (0.60625). Their final graphs agreed on 148/160 SCMs and selected actions agreed on 155/160. These high agreement rates are descriptive and do not imply equivalence.

## Secondary comparisons

| Contrast (left − right) | Mean | 95% SCM paired interval | Left better / worse / tie |
|---|---:|---:|---:|
| Full T1–T6 − Frozen M4, B=1 | −0.0074260 | [−0.0199855, 0.0027889] | 4 / 1 / 155 |
| Frozen M4 − S0, B=2 | −0.0658466 | [−0.0952710, −0.0396177] | 31 / 1 / 128 |
| Full Greedy − S0, B=2 | −0.0455834 | [−0.0746464, −0.0196025] | 21 / 3 / 136 |

The T5 and Full T policies had the same mean edit cost, 0.60625. Their final graphs agreed on 155/160 SCMs and actions on 158/160. All intervals here are pointwise, not multiplicity-adjusted. The extra T subsets are exploratory and do not replace the frozen primary.

## Interpretation and limits

This is not a recovery of the missing other-PC S4-3 run. It is an independently seeded new replication under the current verified implementation. The T5 point estimate favors T5, but almost all SCMs tie, the interval includes zero, and the precision target is missed; the result does not demonstrate T5 superiority. It also does not establish noninferiority to Full T. The Q-common admission screen defines the target population; this is not an unconditional Research C population. Outcome evaluation is analytic from known SCM truth, not sampled intervention data. The results do not generalize to the conditional external DRF environment or a physical manufacturing process.

Aggregate outputs, locked seeds and checksums are in `outputs/confirmation_v1/`. Private unit data are archived outside Git under `C:\DAT_RESEARCH\archives\research-s4-s5\`; the archive is on the same device, with no off-device backup completed.

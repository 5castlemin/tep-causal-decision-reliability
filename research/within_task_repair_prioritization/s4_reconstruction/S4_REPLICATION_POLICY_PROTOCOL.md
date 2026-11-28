# S4 replication policy protocol

`T5_GUIDED_M4` is retained as the replication candidate because it was previously reported as selected on a different PC. That prior selection report is not independently verifiable, and the present analysis does not pretend T5 was newly selected without prior information. The confirmation comparison is frozen before generating any replication SCMs.

At each step, evaluate the legal direct M4 edit candidates using the public S3 T5 task-ancestor F1 gain per unit edit cost. Break ties by the existing M4 gain per unit cost, then the existing canonical metric/pair/operation order. If no positive T5 gain exists, use the existing M4 positive-gain fallback; if neither has positive gain, stop. Recompute candidate feasibility after each edit. Do not pass truth response, regret, or evaluator outcomes to the policy. Frozen M4 retains the already committed Research C policy implementation.

Primary: `T5_GUIDED_M4 − FROZEN_M4`, B=1, gamma=0. Secondary comparisons do not replace it: T5 versus Full T1–T6, M4 versus Full Greedy, and M4/T5 versus S0 at B=2; B=2–3 and gamma=.2/.5 are sensitivity summaries only if fixed-input computations pass. No noninferiority or superiority claim is made from a nonsignificant interval. T5 selection counts, fallback counts, first-edit and action agreement, edit costs, and zero-opportunity units are reported separately.

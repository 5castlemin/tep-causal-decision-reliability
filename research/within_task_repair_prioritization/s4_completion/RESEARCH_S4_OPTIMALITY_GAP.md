# S4 repair-policy optimality gap

**Status: S3 retrospective diagnostics recomputed; S4 confirmation proposed only.** In the enumerated S3 search universe (no edit, feasible initial singles, and feasible ordered pairs), Held-out gamma=0 mean regret was 0.002790 for the ex-post optimum and 0.015930 for regret-greedy, a mean gap of 0.013141 (SCM bootstrap 95% interval 0.004117–0.023918). Development gap was zero at gamma 0. At gamma 0.2 and 0.5, Held-out gaps were 0.002556 and 0.002012; Development gaps were 0.002233 and zero.

This is an exact optimum only within the enumerated <=2-edit feasible universe. The outcome-aware regret-greedy and optimum are privileged retrospective benchmarks, not implementable policies. Structural-policy gap (structure score policy vs regret-greedy) and search gap (regret-greedy vs enumerated optimum) must be reported separately. No unrestricted B=3–4 optimum was computed.

S4 should use a common initial graph, candidate set, unit edit cost, and budget for all policies. Report budget spent as well as cap; do not compare the oracle-assisted structural framework to an oracle-free system without labeling information differences.

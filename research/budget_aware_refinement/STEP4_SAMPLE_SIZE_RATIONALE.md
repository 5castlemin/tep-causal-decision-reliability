# Sample size and cost — proposal, not a power guarantee

2026-11-10; base `42b7c2a0e9d6c11ed72aae4205c0bb7114221a2a`; saved-input hash in readiness audit. Candidate 64 development / 200 independent confirmation SCMs; n=200 counts independent SCMs, not graphs, tasks, or random seeds. Minimum meaningful standardized regret difference 0.10 is a candidate decision threshold on the existing squared-loss scale, not a previously measured or stakeholder-validated effect size.

For independent paired SCM differences, approximate 95% normal CI half-width is 1.96 σ/√200; two-sided Bonferroni α=.025 is a conservative approximation to the first Holm comparison, not exact joint Holm power. Assuming true mean difference .10 and normally distributed differences:

| SD of SCM paired differences | 95% half-width | Approximate power |
|---:|---:|---:|
| 0.2 | 0.0277 | 1.000 |
| 0.3 | 0.0416 | 0.993 |
| 0.5 | 0.0693 | 0.721 |
| 0.7 | 0.0970 | 0.413 |
| 1.0 | 0.1386 | 0.204 |

Approximate 80% first-Holm-step power at .10 requires SD ≲0.459. Unknown SD, mass at zero, skew or rare extreme regrets can invalidate this approximation and destabilize bootstrap intervals. The two old SCMs cannot estimate population SD. Do not promise 80% power or resize after seeing confirmation outcomes. If expected precision or available resources are inadequate, leave the proposed N unapproved and specify alternatives before any outcome access; inconclusive intervals are a legitimate outcome.

Illustrative execution count: 64×2 tasks×3 graphs×5 budgets×(14 policies+no-edit+5 matched-random seeds+1 matched Path-F1)=40,320 graph/fit/evaluation runs, plus 200×2×3×1 budget×(1 selected+5 matched random+1 matched Path-F1)=8,400, total 48,720; full-pool extras, retries, validation and discovery cost additional. Random seeds are within-SCM repetitions. Step 3's small-graph time is not a scalability benchmark. Determine memory, ledger byte sizes, fitting cost and wall time with mock graphs only before freeze. Path enumeration at n≤10 has at most 2^(n−2)=256 distinct X→Y simple paths in a DAG, but repeated candidate rescoring can still be costly. Set wall-clock/memory caps and timeout accounting in the runner before registration; no such validated cap currently exists.

The existing 456-row supplement JSONL occupies 1,342,139 bytes on the Windows checkout, about 2,943 bytes per row; mechanically extrapolated to 48,720 rows this is about 137 MiB before metadata or retries. This is not an upper bound: larger graphs and repeated candidate/rejection ledgers may be much larger, and Git line-ending conventions change byte counts.

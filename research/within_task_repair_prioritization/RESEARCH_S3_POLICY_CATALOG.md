# S3 policy catalog

The analysis enumerates all 63 nonempty subsets of T1–T6. At a current graph, for edit e and subset J, the score is `(mean_j∈J [Tj(after)-Tj(before)]) / atomic_cost`. Equal fixed weights are used; zero-support metrics contribute zero while remaining in the denominator. Positive gain candidates are ranked by score, then the frozen M4 normalized gain, then canonical M4 metric/pair/operation ordering. If no candidate has positive new-metric gain, fallback admits only edits with positive frozen M4 gain; if none exist the policy stops. Candidates remain the original initial M4 error pool and must still correct the same reference-relative error and preserve DAG validity.

The original M4 policy is replayed unchanged. The Random-M4 comparator is the exact SCM-level expectation over uniformly selected currently legal initial M4 edits at B=1 (or no edit when none exist); it is not a finite Monte Carlo draw.

Lookahead compares equal-length legal M4 sequences up to two edits using mean structural potential change per cost. It uses the frozen M4 gain and canonical IDs for ties and falls back to M4 ranking when no sequence has positive structural gain. Thirteen combinations were evaluated: T1–T6, T1+…+T6, and T3+T4, T3+T5, T3+T6, T4+T5, T4+T6, T5+T6.

Ex-post best feasible single-edit/sequence oracle was not executed; it would use observed Regret for selection and must remain separate from deployable policies.
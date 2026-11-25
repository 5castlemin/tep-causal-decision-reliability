# Research D final contract review

**Decision: not ready for final contract approval. Gate remains `DEVELOPMENT_PILOT_INCOMPLETE`.** This is a review record, not authorization for final evaluation.

## Verified

- The original `pipeline.py` byte stream was restored exactly in recovery commit `116e81d48dbeb4ee86ea164be8f1ffd908c03f62` at the original expected SHA-256.
- The retained historical artifacts were audited and their recommendation/evaluation row counts, hashes, bindings, action-loss consistency, and saved Primary arithmetic checked. Historical bootstrap intervals could not be independently recomputed because raw response rows are unavailable. The old pilot remains `execution completed / provenance incomplete at original closeout`.
- Lock, source/runtime fingerprint, evaluator CLI binding, recommendation subprocess, and fail-closed guards were added. Targeted tests passed, and GitHub Actions at commit `16445173224f405c88a32e8856435bbc4290876b` succeeded, including full unittest discovery.
- The corrected pre-fit historical-audit schema gate has a regression test in `4007dbf5bdd4b57f7c9df413ec78243706e4a7f6`; its CI run must be recorded separately.

## Not verified

The one authorized reproduction invocation stopped before DRF fitting because the runner read the audit status from the wrong JSON level. No recommendation/evaluator pipeline, same-seed scientific comparison, Monte Carlo precision check, or end-to-end information-boundary check under the reproduction lock occurred. No run lock or execution manifest was created. The invocation was not retried.

Consequently this review cannot confirm same-seed reproduction, compare the new and old 2,720 recommendations, compare response-vector hashes or action losses, or validate the three intervals. The old reported `Δ=+0.003338` and two-source interval `[-0.065322, 0.075465]` remain exploratory historical values only.

## Contract points preserved for future review

- Conditional external semisynthetic robustness only: one DRF refit from the pinned public semisynthetic source and official Station1 benchmark DAG; no physical intervention or deployment claim.
- Task `Station1_mp_0 → Station1_mp_4` through `Station1_mp_1`, five historical common action values, 512-row training design, training-only `mean(Y)+SD(Y)` target, 32 Development G0 seeds, 17 policies, budgets 0–4, and Primary B=2 S0 versus Full Greedy remain as previously locked.
- M4 remains Secondary; graph-free X–Y association remains in the report and is not called causal.
- Final proposal of 200 G0s, 2,500 evaluation rows/action, and 10,000 bootstrap replicates remains unapproved. No final seeds or samples were generated.

## Review conclusion

Do not advance to final evaluation. The next permissible step would require fresh explicit authorization for a new, single Development reproduction with a new run ID after review of the corrected guard. If no further reproduction is authorized, close Research D as incomplete and retain Research C as the completed primary study. No dataset search, physical control, Research C rerun, or final evaluation is proposed here.

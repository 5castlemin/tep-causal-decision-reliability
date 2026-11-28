# Research S3 correction audit

**Status:** correction replay completed with limitations. Historical S3 outputs are preserved; corrected aggregates are a separate version in `tables/correction_v1/`. The prior Gate remains a historical status. This is still a post-hoc exploratory analysis because the first S3 calculation preceded a committed analysis revision.

## Corrections implemented

- Greedy uses positive new T-subset gain per edit cost; within absolute 1e-12 ties, frozen M4 gain per cost, then canonical metric/pair/operation order. If no candidate has positive T gain, it uses the existing M4 gain fallback.
- T5 computes directed transitive closure over all learner-graph nodes, ignores UNRES, then scores ancestor pairs only on the fixed task-zone node set.
- When no legal two-edit lookahead exists, selection falls back to exactly the same one-step T Greedy selector. Lookahead fallback counts are now measured.
- Source SQLite bytes are rehashed after the corrected replay; all four matched their prior pinned SHA-256.

## Historical versus corrected implementation

An exact historical source snapshot from `a230ab96e2e204c5d72ed34b049190ae3c6bb276` was compared with the corrected graph selector. Across 63 metric subsets × B=1–4 × 264 original SCMs (66,528 cohort-policy-budget units; these are analysis units, not distinct SCMs):

- Final repair graph changed in **218** units.
- Recommended action changed in **70** units.
- Realized Research C regret changed in **70** units.
- Among 554 distinct final graph hashes inspected for T5, **0** had a different T5 score under the corrected closure.

The T5 fix is a general implementation correction, but it did not alter T5 values on the exercised graph set. No unit-level results were published. Aggregate differences are in `tables/correction_v1/corrected_vs_historical_aggregate.csv`.

## Integrity and boundaries

The corrected replay used only the same original Development 64 and Held-out 200 cohort inputs. No new SCM, G0, observations, or intervention responses were generated. Historical v1 output remains untouched in the ignored local `outputs_v6`; corrected outputs were generated in a new ignored run directory and only cohort-level aggregates were copied into this repository. Result summaries remain post-hoc and are not confirmatory.

# Independent Step 5 Raw Data Audit

Audit performed before any Step 6 confirmation proposal was generated. The audit used read-only SQLite access and a separate inline verifier; it did not call the Step 5 analysis script to derive the checks below.

## Raw integrity and denominators

- SQLite `PRAGMA integrity_check`: `ok`.
- Independently recomputed raw inventory: 66 files, 7,726,714 bytes; every path, byte size, and SHA-256 matched `STEP5_DEVELOPMENT_RAW_INVENTORY.json`.
- Proposal rows: 211 total; 145 structural rejections (`missing_same_type_two_candidate_support`), 2 pre-admission proposal failures (`no_indirect_only_task`), and 64 completed admissions.
- Accepted SCM IDs and equation signatures were unique (64 each); accepted ordinals were 0–63 and delta assignment alternated +1/-1 (32 each).
- All 64 admitted ledgers had the expected ordered stages, complete newline termination, matching cohort/run/SCM/RNG/config/input bindings, and valid canonical event/output hashes.
- All 64 had successful FN/FP/REV GT evaluations and finite nonnegative policy regrets. No post-admission failure or missing type was found.

## Independent recomputation

For each SCM and type, the auditor recomputed `Regret_Global - Regret_TaskFocused`; then recomputed the equal-weight three-type SCM composite and compared it with the logged composite.

- Mean `D_i`: `0.014660484921723964`; median `0`; positive/negative/zero: `6/1/57`.
- FN mean: `0.005825787787239571`; FP mean: `0`; REV mean: `0.03815566697793233`.
- Same final graph counts: FN 46/64, FP 33/64, REV 38/64.
- Same selected action counts: 64/64 for each type.
- Same selected `k` counts: FN 61/64, FP 64/64, REV 59/64.
- `development-proposal-000059`: recomputed `D_i=0.4195602263615929`; global regrets FN/FP/REV = 0/0/1.2586806790847787, Task-Focused = 0/0/0.
- `development-proposal-000114`: recomputed `D_i=0.23137325471964898`; global regrets FN/FP/REV = 0.34705988207947347/0/0.34705988207947347, Task-Focused = 0/0/0.

No Step 5 raw files were changed. The raw directory was rehashed after analysis and still matched the inventory. These checks validate record arithmetic and binding consistency; they do not independently reimplement the analytic SCM truth evaluator from first principles. The frozen evaluator and its fixture validation remain the basis for evaluator correctness.

## Step 6 analysis rules fixed before execution

The Step 6 primary descriptive quantity remains the equal-weight SCM-level paired mean difference, with each SCM as the independent unit. The report will show the mean, median, sample SD, quartiles, range, sign counts, type-specific differences and policy regrets, policy graph/action/selected-k agreement, delta/template summaries, and denominators/failures. Extreme-value sensitivity will report the mean after removing the largest one and largest two `D_i` values, plus their contribution; the full-cohort mean remains primary.

No confirmatory superiority/equivalence test will be run. No policy, weight, eligibility rule, budget, seed, or cohort will be changed after outcomes are observed. Step 6 proposal/admission/completion denominators will be recomputed dynamically from its own read-only registry and ledgers.

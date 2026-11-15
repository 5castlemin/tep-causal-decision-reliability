# Step 4B-3 context-keyed RNG structural feasibility report

Status: new RNG contract implemented and structurally exercised; no random SCM coefficients or observations were drawn. Step 4 remains `IN_PROGRESS / NOT FROZEN`.

## RNG contract

`step4_rng.py` derives 256-bit integer seeds as SHA-256 over canonical, sorted JSON containing protocol version, cohort, master seed, independent SCM ID, template, node count, topology attempt, stream name, replicate and optional substream. Streams are declared for topology, coefficient, exogenous noise, observational sample, node relabeling, task selection, error injection, policy schedule, Random baseline and Q recipe selection. The latter six plus topology are used for the structural-only run; coefficient/noise/observation/Random streams were not drawn in this run. NumPy SeedSequence support is lazy and was not used. The derivation is stable domain separation, not a mathematical proof that streams are independent.

Tests verify that a repeated full key reproduces the same seed; changing cohort, SCM ID, template, node count, attempt, stream or Random replicate produces a different key in the tested set; and seed derivation does not depend on execution order. Python process hash randomization is not used.

The Step 2 engine now accepts optional `schedule_seed`, defaulting to the old `seed` for compatibility. The Random selection seed and type schedule can therefore be different. Tests verify the legacy seeds `{0,6,12,18,24}` all share schedule seed 0 for the three-type case, and that Global/Task-Focused retain a matched schedule. This allows the policy schedule stream to be shared while Random's draw stream changes by replicate.

## Versioned fixed-grid run

The run uses development cohort keys for master seeds 11–15, 4 templates, n=6–10, one topology attempt per stratum, and 100 topology IDs total. It records 1,000 planned P task-condition rows: for each of 200 task slots, A once, B separately for FN/FP/REV, and C once. A failed selected task yields five failed condition rows but remains one failed task slot. No retries or replacements are made. All 100 generated truth topologies are DAGs and have distinct topology hashes.

Across the 150 same-node-count/seed pairs of distinct templates, new `id_mapping` equality was 0/150, versus 150/150 under the prior seed-only stream key. Action role labels are distributed differently by template; with five seeds per stratum they are not expected to be exactly uniform. The purpose is to remove deterministic cross-template reuse, not claim perfectly uniform label frequencies.

| Condition cell | Accepted | Planned | Failures and reasons |
|---|---:|---:|---|
| A, all errors | 197 | 200 | 3 task-selection failures (`no_indirect_only_task`) |
| B-FN | 37 | 200 | 160 no path-preserving task-related FN; 3 task-selection failures |
| B-FP | 197 | 200 | 3 task-selection failures |
| B-REV | 37 | 200 | 160 no path-preserving task-related REV; 3 task-selection failures |
| C, mixed | 197 | 200 | 3 task-selection failures |

There were three distinct missing indirect task slots, repeated as 15 condition rows. Failures remain in their planned denominators. The exact task type, error type, DAG, path status, error count and overlapping location tags are stored row by row.

## Q competition support

Q was planned for 600 task-type cells. The outcome-blind rule required two same-type corrections, distinct task/peripheral locations, individually DAG-valid corrections, an initial DAG, a surviving task path, and a unit budget that cannot repair both. Acceptance: FN 34/200, FP 197/200, REV 55/200; failures: FN 166, FP 3, REV 145. No failed type was replaced. Selected recipes were not screened on rankings or final graph differences.

| Q type | Accepted / planned | Candidate-ranking divergence | B=1 final graph difference | B=2+ final graph difference |
|---|---:|---:|---:|---:|
| FN | 34 / 200 | 17 | 17 | 0 |
| FP | 197 / 200 | 90 | 90 | 0 |
| REV | 55 / 200 | 14 | 14 | 0 |

Overall, 286/600 Q cells were accepted, and 121/286 eligible cells had a different first-candidate ranking (and a different final graph at B=1). The type-cell mixture is unequal; type rates cannot be described as common-population rates. The strict same-SCM/task common support across all three types has 34 SCM IDs and 34 task slots, all indirect: Chain 7, Fork 4, Multiple Paths 14, Common Cause 9. Every type has those same 34 cells; their B=1 final graph differences are FN 17, FP 16 and REV 14 (47/102 type-version comparisons). This is the structural basis for the proposed equal-type Q-common H2 estimand. At B=2, all selected graphs converge because both unit repairs fit. Candidate ranking differences remain part of the Q diagnostic, not an eligibility requirement.

P/Q here consists of topology-only structures, not independently sampled SCMs. For Q-common, the observed acceptance was 34/100 topology IDs. Reaching 64 or 200 eligible independent Q-common SCMs would require a larger, finite candidate topology pool; at the observed rate the expected candidate counts are approximately 188 and 588. Step 4B-4 must decide actual target sample sizes, maximum attempts, stratum weights and shortfall handling. This estimate is structural and does not establish power.

## Comparison with prior matrices and limits

v1–v4 and the B2 diagnostic are preserved. The new RNG run is a separately versioned sample because the topology, relabel, task and error streams now depend on the complete context. Its B design also plans all three requested error types per task rather than v4's one preassigned B type per row, so B acceptance counts are not a paired before/after comparison. Count changes are expected from those declared design changes; no success-based seed selection occurred.

No policy regret, effect, coefficient, observation, ridge fit or confirmatory outcome was evaluated. Policy/dataset identity does not exist for this feasibility run; the exact structures, tasks, errors and all RNG seeds are in the compressed raw file. The full statistical test, power, missing-data/failure contract, sample allocation and compute/storage limits remain open.

## Artifact hashes

- Settings canonical JSON SHA-256: `ecc8e548d7904751fd9f88581257655f4489c2edfbd7e14f3410691b60a5f4ed`
- Compressed raw v1 SHA-256: `ed55c075c5f20210f0c80e0c84bb4570376829065290a23e2b29802728ff1707`
- Protocol: `STEP4B3_CONTEXT_KEYED_RNG_STRUCTURE_FEASIBILITY_V1`

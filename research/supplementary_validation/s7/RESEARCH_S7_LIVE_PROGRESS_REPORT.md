# S7 Live Progress and Resource Check

**Observed:** 2026-11-28 15:05 KST
**Run:** `s7-causalassembly-two-station-tasks-20261128-v1`, attempt 02  
**State:** `RECOMMENDATION_STAGE_ACTIVE`; no intervention evaluation started.

## Locked workload

- Official causalAssembly joint graph: 98 nodes and 485 directed edges.
- One fitted full-line DRF DGP and one 512-row training frame.
- Two task strata, 200 G0 draws each: 400 G0 total.
- 12 policies × 5 budgets × 400 G0: 24,000 planned recommendations.
- After recommendation sealing: 50,000 planned intervention response rows, 24,000 unit-policy losses, and 10,000 bootstrap replicates for each locked uncertainty analysis.

## Observed completion

The private run directory contains the validated `training.csv` only (643,985 bytes; SHA-256 `833c7dbac00a29f896d1fb433d90ff971c412702fe90495a2de5f5e535917245`). It contains no persisted G0 records, recommendation rows, or sealed recommendation manifest. The public output directory is empty. The last reliable read-only in-memory snapshot, at 14:58, showed the first Station2 G0 at `i=0`, with empty `rows`, `g0_public`, and `recs`, and an empty learner cache: 0/400 G0 and 0/24,000 recommendations. At 15:05 the worker was still in the first `task_zone` traversal; no G0/recommendation files appeared in the run or public output directories. Therefore the latest verified persisted count remains 0/400 and 0/24,000; the 14:58 in-memory count is reported separately and is not extrapolated as a fresh locals read. No completed-unit artifact appeared in the preceding ten minutes: 0 persisted G0 and 0 persisted recommendations.

No G0 or recommendation artifacts were observed to be written during the ten-minute observation window. This is a persisted-output count, not a claim that no in-memory work completed.

## Current bottleneck and duplicate work

A read-only nonblocking `py-spy dump --json` at 15:04:43 located the active stack in `policy_engine.py:92–95`, `task_zone.<locals>.visit`, with recursive depth about 78, inside the first `make_g0 → corrupt_graph_candidate → task_zone` call. The 15:05 file check found no G0/recommendation artifact. The frozen `task_zone` implementation recursively enumerates simple undirected paths in the 98-node, 485-edge truth graph. At that observation, the call had not returned after approximately 3 h 18 min of the run. It is called again for each G0 and again by policy metrics, despite identical truth/task inputs. This is the observed bottleneck; CPU accumulation alone was not used as a progress measure.

The S7 runner caches Ridge action fits by `(station, recommended_graph_hash)`, preventing repeated fits for the same graph within one station. The key includes station, so a graph shared across stations may be fit twice. The runner also recomputes policy repair trajectories separately for each budget and recomputes the same graph-free association fit for each G0. These are duplicate calculation paths, but unit-level duplication counts are unavailable because no recommendation checkpoint exists.

## Checkpoint, resume, and remaining work

The training frame is a valid saved input checkpoint. No G0 or recommendation progress is checkpointed, so the current recommendation stage cannot resume from its exact last completed unit. A deterministic restart could reuse the saved training frame only after a versioned runner explicitly verifies its hash and regenerates the same locked G0 sequence; this resume path is not implemented in attempt 02.

After recommendations are complete and sealed, the contract still requires an evaluation-stage DRF refit, training-frame hash verification, response generation for five actions in each task stratum (50,000 rows total), the shared action-loss table, unit losses and aggregate contrasts, followed by G0-only, action-MC-only, and two-source paired bootstrap analyses. Evaluation must not start before the sealed recommendation manifest exists.

## Resource status

The locked cumulative cap is 14,400 seconds and aggregate process-tree RSS cap is 4 GiB. At 15:05:23, elapsed wall time from supervisor start (11:46:36) was 11,927 seconds (3 h 18 min 47 sec), leaving 2,473 seconds (41 min 13 sec). The recommendation process RSS was 86,867,968 bytes (about 0.081 GiB). The wall cap had not been reached; observed RSS was below the cap. The supervisor samples process-tree RSS every two seconds and will terminate the child at either cap. Its final resource report is written only when the supervisor exits.

## Result

S7 is incomplete at this checkpoint. The first G0 had not completed after more than three hours, and the current runner does not checkpoint G0 or recommendation units. The process remains running under the original lock; no execution contract or experiment design was changed. A result-preserving cache can reuse the pure `task_zone(truth, action, target)` result across identical calls, but it does not remove the current first-call path-enumeration bottleneck. No such optimization was inserted into the active run. Exact continuation from an incomplete first G0 is not currently available: the saved training frame alone is insufficient to resume recommendation work at a completed-unit boundary. After a cap stop, preserve this attempt and classify it `PARTIAL`; do not start evaluation unless a separately locked recommendation run completes and is sealed. This report does not authorize changes to the cohort, policies, budget, or evaluator.

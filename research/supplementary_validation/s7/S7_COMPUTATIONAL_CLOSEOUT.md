# S7 Computational Feasibility Closeout

**Gate:** `RESOURCE_LIMITATION_WITH_EXIT_TELEMETRY_UNVERIFIED`  
**Original run:** `s7-causalassembly-two-station-tasks-20261128-v1`, attempt 02. No experiment settings were changed and the runner was not restarted.

## Original run disposition

The locked workload used a single 98-node, 485-directed-edge causalAssembly full-line graph, one shared DRF DGP/training frame, and two task strata: Station2 `mp_13→mp_33` and Station3 `mp_43→mp_45`. The plan was 400 G0 and 24,000 recommendations. At the last reliable in-memory snapshot (14:58 KST) and filesystem/process observation (15:05 KST), 0/400 G0 and 0/24,000 recommendations were complete or persisted. The worker was still inside the first Station2 `task_zone` recursive simple-path enumeration; the stack showed roughly 78 recursive levels. No sealed recommendation manifest existed, so intervention evaluation was not run.

At 15:11:11 KST the worker was last reported active, 12,275 seconds after supervisor start at 11:46:36 (3:24:35 of a 14,400-second wall cap). It was subsequently absent, but the attempt-specific final supervisor report is missing. A similarly named resource report predates attempt 02 and records a 2.03-second failed pre-run; it is stale and cannot establish the attempt's exit code, actual final wall time, or peak RSS. Thus cap enforcement, final resource use, and termination reason are **not verifiable**. Do not report that the worker was confirmed to have reached the cap. The persisted completed-unit count remains zero based on the available run directory; no outcome is inferred.

The only validated input checkpoint is `training.csv` (643,985 bytes; SHA-256 `833c7dbac00a29f896d1fb433d90ff971c412702fe90495a2de5f5e535917245`). There are no saved G0s, recommendations, or recommendation seal. The attempt cannot safely resume from a completed-unit boundary. The original 14,400-second / 4-GiB lock is retained; the inefficient runner was not restarted.

## Separate optimization feasibility (not an S7 evaluation)

An isolated exactness implementation was tested without modifying frozen `policy_engine.py` or the S7 contract. Against the pinned causalAssembly commit `8da3729e6383f0e1cbe7740bb6ab7ac4977ac7f9` and ground-truth hash `f015fbe1a1955446169ecdc9251d99792f5c49c2343699ab30e7fdd2960595ae`, it returned:

| Task | Task-zone edge pairs | Task-zone nodes | Independent full-graph reference | Outcome-blind smoke |
|---|---:|---:|---|---|
| Station2 `mp_13→mp_33` | 4 | 4 | Exact match | 1 in-memory recommendation; cost 1; no evaluator |
| Station3 `mp_43→mp_45` | 49 | 22 | Exact match | 1 in-memory recommendation; cost 1; no evaluator |

Elapsed time was 1.474 seconds, below the separate 900-second feasibility cap. Exactness was also checked against the frozen enumerator exhaustively on all four-node DAGs and targeted unresolved-edge classification fixtures (focused tests: 3 passed). The full-graph reference uses an independent collider-pruned DFS implementing the frozen terminal predicates; it is not a claim that the frozen unpruned enumerator returned on the full graph. The smoke tests used synthetic in-memory edge deletions only, not new G0/evaluation samples, and did not access evaluator outcomes.

This establishes a feasible route for **future separately locked** recommendation computation, not completion of the 400-G0/24,000-recommendation S7 contract. No full recommendation run was started. A future run would require a new immutable execution lock, cached task-zone calculation, resumable unit checkpoints, and verifiable supervisor telemetry; this closeout does not authorize that run.

## Remaining locked workload

The planned post-seal work remains unrun: evaluation-stage DRF fitting/checks, 50,000 intervention response rows (two task strata × five actions × 5,000), shared action-loss table, policy contrasts, and the locked uncertainty analyses. With zero sealed recommendations, none may be represented as performed.

The two tasks are strata within the same full-line DGP and are not two independent external environments. S7 supplies no new external performance result. Existing Research D/S5 evidence is unchanged and retains its prior conditional semisynthetic scope.

Machine-readable feasibility output: [`outputs/s7_task_zone_feasibility.json`](outputs/s7_task_zone_feasibility.json). Code and fixtures: [`task_zone_fast.py`](task_zone_fast.py), [`s7_task_zone_feasibility.py`](s7_task_zone_feasibility.py), and repository tests.

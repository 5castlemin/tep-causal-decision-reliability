# Step 4B-4 resource benchmark v2

## Final decision addendum (2026-11-15)

The new `step4b4_mock_runner.py` and `run_step4b4_mock_pipeline.py` provide a mock integrated ledger path and are exercised by `tests/test_step4b4_mock_runner.py`. They add durable per-stage checkpoints, same-key resume, torn-tail recovery, duplicate suppression, wall/unit boundary checks and disk-cap enforcement. They use a deterministic 512×10 dummy matrix, existing graph policy and Ridge/recommendation code, and a truth stub that returns no effect/regret. They are not the final study runner.

Adopt 30 min cohort wall budget, 2 sec/unit observed-time ceiling, 512 MiB RSS monitoring threshold and 100 MiB ledger ceiling for the mock contract. The ledger ceiling is enforced before appends; wall/unit limits are observed at stage boundaries and cannot preempt a stage in-process; RSS is best-effort stage-boundary monitoring, not hard containment. A timeout/RSS hard kill requires a process-isolated Step 4C runner. Thus the ceilings are explicit operational stop rules for this contract, not evidence of worst-case runtime or memory safety on the eventual execution environment.

**판정: 고정 512×10 dummy matrix 전체 학습·추천 path까지 측정. 실제 SCM/관측 자료, GT effect, regret는 생성·계산하지 않았다. 최종 실행 runner는 아직 없으므로 운영 한계는 제안값이다.** Dummy matrix는 deterministic arithmetic fixture이며 인과 SCM에서 나온 자료가 아니다. 10-node DAG Q recipe 진단도 topology-only다.

환경: Python 3.14.3, NumPy 2.4.3, `Windows-11-10.0.26200-SP0`. 컴포넌트별 wall time median/p95/max:

| Path | median | p95 | max |
|---|---:|---:|---:|
| 10-node topology+Q recipe (10 reps) | 243.234 ms | 302.633 ms | 302.797 ms |
| graph policy | 0.613 ms | 0.803 ms | 1.489 ms |
| Ridge fit 512×10 | 1.103 ms | 2.026 ms | 2.433 ms |
| 5 action predictions | 1.553 ms | 1.624 ms | 2.463 ms |
| graph→fit→recommend | 3.693 ms | 6.839 ms | 8.787 ms |
| Path F1 | 0.117 ms | 0.125 ms | 0.199 ms |

Process RSS before/after was 71.7/80.2 MiB; process peak RSS 92.8 MiB, including native NumPy and interpreter. tracemalloc peak 7.97 MiB excludes native. JSONL row sizes: 1 / 10 / 100 candidate graph hashes = 313 / 916 / 6,946 bytes; mocked failure row 141 bytes. Restart/idempotence mock reopened the JSONL and refused duplicate run ID; one row remained.

## Workload and provisional guardrails

For candidate N=64 development + 200 confirmation: six primary policy/type model-recommend variants per SCM =1,584; five Random replicates × three types =3,960 auxiliary; total 5,544. The measured integrated path p95 projects to 38 seconds for these variants. Two-layer candidate cap 362+1,036; using all 10-node Q-recipe p95 as worst case projects candidate generation at 424 seconds. Combined ~7.7 minutes; ×2 margin ~15.4 minutes. GT evaluation path is not measured and excluded.

5,544 rows at the 100-candidate hash-row size project to ~38.5 MB. 264 raw 512×10 float64 matrices add ~10.8 MB, total ~49.3 MB before indexes/checkpoints. Provisional engineering ceilings for the next integrated runner: 30 minutes wall clock across both cohorts, 2 seconds per candidate or policy variant, 512 MiB process peak RSS, 100 MiB total disk, checkpoint after each fully completed SCM. Derived as >2× workload projection, ~5× measured process peak, and ~2× projected storage. The logger mock supports run-ID deduplication, not a validated production checkpoint engine.

At any cap: flush ledger/raw attempt statuses, checkpoint, stop with target shortfall; resume only deterministic pending IDs/keys. These ceilings are proposals, not frozen controls: no end-to-end GT evaluation, final output schema, actual coefficient/data generator, different machine or full cohort has been run. Must implement and stress test in Step 4C before they serve as execution limits.

JSON: `step4b4_resource_bench_v2.json`.

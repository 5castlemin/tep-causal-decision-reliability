# Step 4B-4 resource benchmark

Status: **PARTIAL; operational caps not set**. Step4B4 had no full 10-node feature dataset suitable for Ridge path benchmarking. The only permitted learner timing fixture was the existing fixed Step 3 4×3 unit matrix; it is not newly generated SCM data. The graph engine can be measured on 10-node topology fixtures. Therefore no full-run elapsed-time claim is made.

The planned primary workload, if N eligible SCMs are later approved, is 6 graph/model/evaluation variants per SCM (2 policies × 3 error types), plus 15 Random variants per SCM if five matched Random repetitions × three types are retained as secondary. At N=264 (64+200 candidate), that is 1,584 primary and 3,960 secondary model/evaluation variants, before retries; five action-grid predictions and corresponding truth evaluations per variant gives 27,720 candidate/GT pairs total. These are workload arithmetic, not measured runtimes.

Topology rejection attempts must be separately budgeted. The Q-yield audit's observed 31.85% is heterogeneous across 20 strata; a naive iid 95%-yield cap is only planning arithmetic. The 20% scenario gives caps 381 candidates for 64 and 1,107 for 200 at 95% conditional target attainment, but is not adopted without stratum-aware validation.

A bounded 200-repetition microbenchmark was run on this Windows/Python 3.14/NumPy 2.4.3 environment: 10-node graph refine median 0.000552 s (p95/max in `step4b4_resource_bench_v1.json`); Path F1 and 3-node fixed-fixture Ridge fit are separately recorded there. The Ridge median was 0.000253 s. JSONL example row was 177 bytes. Python `tracemalloc` peak was 222,261 bytes, excluding native NumPy/RSS. This is not a full-run or 10-node Ridge benchmark. Resume/restart and deduplication were not benchmarked. Do not infer full-run storage or elapsed time by multiplying a tiny fixture measurement. Step 4C must benchmark the actual frozen runner on approved mock/fixed fixtures, record hardware and Python/package versions, and adopt a hard wall-clock, RSS, and disk cap with stop-and-preserve behavior.


> **Update:** The initial 3-node Ridge-only limitation was addressed with a 512×10 deterministic dummy matrix through existing Ridge and five-action recommendation code. See [resource benchmark v2](STEP4B4_RESOURCE_BENCHMARK_V2.md). This remains a mock benchmark, not a full experimental runner.

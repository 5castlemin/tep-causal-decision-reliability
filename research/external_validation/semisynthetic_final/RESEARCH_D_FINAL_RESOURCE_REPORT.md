# Research D final resource report

## Limits and measured run

| Measure | Observed | Locked limit | Result |
|---|---:|---:|---|
| Wall time, full supervised process tree | 407.563 s (6.79 min) | 7200 s | PASS |
| Peak process-tree RSS sampled by Windows psutil supervisor | 1,917,583,360 bytes (1.786 GiB) | 4,294,967,296 bytes (4 GiB) | PASS |
| Final intervention rows | 12,500 | 12,500 | PASS |
| Serial action sampling | 1 | 1 | PASS |
| DRF fit in evaluator | 21.152 s | within whole-run limit | PASS |
| Intervention sampling | 238.182 s | within whole-run limit | PASS |

The outer monitor used psutil 7.2.2 to sample recursive process-tree RSS every 2 seconds and terminate the process tree if a sampled value exceeded 4 GiB or elapsed time exceeded 7,200 seconds. The final process tree completed normally with no breach. This is not an OS sandbox, and sub-interval transients are not separately measured.

## Synthetic full-dimension bootstrap benchmark

The response-blind synthetic fixture exercised 17,000 recommendation rows, five synthetic action vectors of 2,500 rows each, 10,000 paired two-source bootstrap replicates, and chunk size 128. It completed in 1.202 s without using final outcome data. Its Windows in-process `GetProcessMemoryInfo` field returned **0 bytes**, which is an invalid measurement and is not treated as evidence of low memory use. The external process-tree supervisor is the valid measured memory record for the complete execution, including the benchmark and final run: 1,917,583,360 bytes. The actual run therefore stayed under the cap; the benchmark-specific internal peak metric remains unavailable.

The pre-run benchmark used its locked synthetic seed and did not choose or alter the task, actions, targets, policies, or sample sizes. Actual run hashes and measurement are in `final_public_execution_manifest.json`.

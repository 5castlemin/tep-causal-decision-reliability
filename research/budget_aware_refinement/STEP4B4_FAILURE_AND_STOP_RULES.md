# Step 4B-4 failure and stop rules

Status: **IN_PROGRESS / proposed mock-validated rules; not frozen**.

| Status | Interpretation | Handling |
|---|---|---|
| `STRUCTURE_INELIGIBLE` | Q-common structural rejection | Keep attempt in topology denominator; no SCM row |
| `TOPOLOGY_FAIL`, `TASK_FAIL` | Generator/task construction failure | Log exact reason, no replacement beyond fixed cap |
| `NO_CANDIDATE`, `UNUSED_BUDGET`, `CYCLE_REJECT` | Normal policy outcome | Include; zero edits/spend is not failure |
| `DATA_FAIL` | Observation generation invalid | One same-key retry only for explicit transient I/O/system fault; otherwise retain failure |
| `RIDGE_FAIL`, `RECOMMEND_FAIL` | Learner/recommendation failed | Intention-to-handle k=0 fallback only if training and truth inputs are valid and k=0 belongs to common action grid; retain original failure and separate fallback result |
| `GT_EVAL_FAIL` | Truth evaluation unavailable | No fallback and no zero imputation; primary SCM vector incomplete |
| `NONFINITE`, `TIMEOUT` | Numerical/resource failure | Retain status, no outcome-directed retry; incomplete vector |
| `IO_FAIL`, `SYSTEM_FAIL` | Infrastructure issue | At most one same-input, same-key retry; deduplicate by run key and preserve both attempt records |

Each SCM primary row needs FN, FP and REV paired differences. If any type is missing after the allowed fallback, `D_i` is missing, never a mean over remaining types. Any missing confirmation primary row prevents confirmatory inference under the current candidate rule; report the analysis as inconclusive. A cap shortfall likewise stops inference without silently lowering N.

Candidate retry policy: structural topology/task/error generation gets no unbounded retries; every attempt, including rejection, is stored. A transient infrastructure retry is limited to one identical-input/identical-key replay. Deterministic invalidity, nonfinite values, GT failure and timeout are not retried. Do not replace an eligible SCM that later fails evaluation after seeing its outcome.

The executable mock categorizes normal, pre-SCM structural rejection and analysis failures, verifies fallback preconditions and preserves original failures. Operational retry counts and confirmation stop thresholds still require Step 4C code-path validation.


> **Feasibility update:** Strict all-type completeness is operationally fragile under even small independent MCAR rates; see [failure feasibility review](STEP4B4_FAILURE_FEASIBILITY_REVIEW.md). Same-key retry remains limited to transient infrastructure failure; no missing value is imputed as zero.

# Research S3 completion report

## Status and scope

**Status: `S3_COMPLETION_RECOMPUTED_WITH_LIMITATIONS`.** This is a post-hoc exploratory reanalysis of the original Research C Development (64 SCMs) and Held-out (200 SCMs) cohorts. Historical first-run and correction-v1 records remain preserved; the current completion outputs are a separate version. No new SCM, G0, observational draw, or intervention sample was generated. The original SQLite cohort and proposal files were read-only and their hashes were checked before and after processing.

The completion replay evaluates 88,440 existing policy-unit rows, 203 initially feasible single-edit candidate rows, and 198 ordered feasible interaction rows over gamma 0, 0.2, and 0.5. It covers the 63 nonempty T1–T6 metric subsets, B=1–4 greedy, and B=2 lookahead. The exact ex-post search is limited to no edit, initially feasible single edits, and feasible ordered two-edit paths; it is not an unrestricted B=3–4 oracle.

## Ex-post decision-value benchmark

For the original gamma=0 task, the ex-post feasible optimum reduced S0 regret by 0.09829 on Development (95% SCM-bootstrap interval 0.05446–0.14856; 17 improved, 0 worse, 47 tied) and by 0.09065 on Held-out (0.06568–0.11673; 51 improved, 0 worse, 149 tied). At gamma=0.2, corresponding gains were 0.02154 (0.00690–0.03989) and 0.03431 (0.02225–0.04787). At gamma=0.5, Development gain was zero; Held-out gain was 0.00773 (0.00158–0.01539; 5 improved, 0 worse, 195 tied).

These are privileged diagnostics because the benchmark selects edits using realized regret. They are not deployable policies. Under gamma=0, mean ex-post-optimal regret was 0.00256 Development and 0.00279 Held-out. Best-single Held-out regret was 0.01593, leaving a mean 0.01314 gap to the <=2-edit optimum. Development had no mean gap between best single and <=2 edits. At gamma=0.2/0.5, the <=2-edit regret-greedy search gap was 0.00223/0.00000 Development and 0.00256/0.00201 Held-out. Held-out gamma=0 search-gap interval was 0.00412–0.02392; intervals are pointwise percentile SCM bootstraps.

## Candidate ranking and interactions

Only 11/64 Development and 35/200 Held-out SCMs had at least two initial feasible M4 edits. On that selected structural subset, Held-out gamma=0 T4+T5 had mean optimality gap 0.02694, tied-best hit rate 1.00, and mean pairwise rank accuracy 0.9167; T4 had gap 0.02772, hit rate 0.9714, rank accuracy 0.9063. These small, selected samples do not establish a generally best metric. M4's corresponding Held-out gap was 0.07655 and pairwise rank accuracy 0.4948. Candidate rows are nested within SCM and were summarized at SCM level.

The SCM-mean interaction contrast was heterogeneous and uncertain. For gamma=0, it averaged -0.02215 (Development, 1 positive / 8 ties / 2 negative SCM means) and +0.05248 (Held-out, 11 / 20 / 4). Held-out gamma=0.2 averaged +0.02293 (6 / 27 / 2), while gamma=0.5 averaged -0.00483 (1 / 33 / 1). All reported cluster bootstrap intervals include zero. Both edit orders were feasible for the 20 Development and 79 Held-out feasible unordered pairs (40 and 158 ordered sequences).

These results support neither universal additivity nor a stable positive synergy claim. Interaction is task- and cohort-conditional; cells are sparse.

## Objective sensitivity and frozen baselines

At B=2, existing C baseline results are reproduced in the aggregate output: Held-out gamma=0 regret is S0 0.093439, Full Greedy 0.018603, M4 0.003988; Development is 0.100852, 0.025641, and 0.002928. Rankings depend on objective: Held-out gamma=0.2 gives 0.117959, 0.092235, and 0.087253, while gamma=0.5 gives 0.085460, 0.082163, and 0.083598. Thus M4 does not lead every objective. This is a post-hoc sensitivity analysis, not a replacement for the frozen Research C primary.

## Limits and interpretation

The original cohorts provide few multi-edit opportunities, especially Development. Ex-post selection uses outcome information, and the candidate-ranking summaries condition on feasible candidate multiplicity. Error type/role summaries are descriptive and do not identify causal effects of error classes. Research D unit-level records were unavailable for this completion analysis; no Research D extension was run. No independent S4 cohort was run. The S3 results remain exploratory and cannot establish that a structural score is universally decision-optimal.

The all-63-combination B=2 lookahead replay had 4,032 Development and 12,600 Held-out policy-SCM runs. A fallback was recorded in 1,286/4,032 (31.9%) and 4,298/12,600 (34.1%) runs, respectively. Across the 63 subsets, the mean number of distinct final graph hashes per SCM was 1.047 Development and 1.115 Held-out; most metric subsets therefore converged to the same final graph. See `lookahead_diagnostics.csv`. These are policy-run counts, not unique SCM counts.

## Coverage audit of requested completion analyses

Completed from the saved replay: all 63 subset Greedy outcomes at B=1–4; all 63 subset two-step lookahead outcomes at B=2; ex-post single and feasible <=2-edit benchmarks; SCM-clustered interaction summaries; three-objective sensitivity; SCM-level candidate ranking and random-selection benchmark; Holm adjustment for the bounded B=2, gamma=0 baseline family; source-before/after digest check; and the baseline replay check.

Not completed in this version: a covariate-rich error-value mechanism analysis by path position, backdoor role, distance, alternate paths, adjustment sets, effect sign/magnitude, and initial graph accuracy; an independent policy ranking evaluation on a new cohort; exact optimal search beyond two edits; a full 63-choose-subsets factorial/marginal-contribution analysis across all contexts; and a Research D unit-level extension. The retained candidate schema does not include all requested graph-role covariates, and these items are not inferred from the aggregate regret tables. Accordingly, S3 is completed only for the analyses listed above, with the remaining mechanism explanations left unresolved.

The successful replay source bytes match runner commit `e0fef84caaa2ddb44e7606a864feabdc2818cc52` (runner SHA-256 recorded in `S3_COMPLETION_RESULT_MANIFEST.json`); independent aggregate finalization is recorded at `6da5435dc5aeb1b73f44f47e2e1fb954981c2c31`. Earlier pre-result technical attempts and the historical S3 first run are preserved in Git history; they are not mixed into the v3 outputs. The four SQLite digests matched their approved values in a fresh read-only check and were also asserted equal before/after replay.

Focused regression suite passed 20/20. Full local discovery ran 461 tests: 459 passed, one failed, and one errored. The failure was a raw SHA check on a frozen JSONL file whose LF-normalized working bytes match the Git blob; the error was the frozen runtime dependency fingerprint (local NumPy 2.4.6/Pandas 3.0.3/NetworkX 3.6.1). The frozen graph verifier and asset checker likewise report working-tree raw-byte mismatches for frozen files, while all affected Git blobs match their recorded hashes and the changed-file list contains no frozen assets. These checks were not weakened. GitHub CI remains the required clean Linux validation.

Machine-readable aggregates are in `tables/completion_v3/`; exact source bindings and analysis settings are recorded in `S3_COMPLETION_ANALYSIS_LOCK.json` and the result manifest.

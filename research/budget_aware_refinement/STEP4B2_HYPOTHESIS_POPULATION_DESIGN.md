# Step 4B-2 hypothesis and population design audit

Status: structural design evidence only; Step 4 remains `IN_PROGRESS / NOT FROZEN`.
No SCM coefficients, observational data, fitted models, intervention effects, Decision Regret, or policy-performance outcomes were generated.

## Evidence and reproducibility

This audit reads the preserved Step 4B-1 v3 matrix and the new C-order-corrected v4 matrix. It does not overwrite v1/v2/v3. The v4 matrix has 600 planned topology-task-condition rows, 491 accepted rows overall, 109 recorded failures, and 200/200 accepted C rows. The 109 overall failures belong to A/B eligibility and are retained; they are not C failures. v4 has 481 distinct initial graph hashes in its full matrix.

The P/Q runner uses the fixed grid of 4 templates × 5 node counts × 5 seeds. That is 100 topology instances and 200 task slots, not 200 independent SCMs. Q has three repeated error-type cells per task slot (600 planned cells), not 600 independent units. Existing v3 C path status was 129/200 surviving and 71/200 disconnected. Re-execution under the corrected v4 C recipe yields 133/200 surviving and 67/200 disconnected.

| Artifact | SHA-256 |
|---|---|
| v3 historical matrix gzip | `df03ccd4ab931580a0e69c1159d67e6b4c5147fa32e1a67fae3f7d2fe721d485` |
| v4 C-order-corrected matrix gzip | `a97b8731f1c5ea53ea8b17d457b54272e15ad350721225ffe203e55711b4afad` |
| P/Q diagnostic gzip | `f4c08e2f2846af0c75b44db664ed658684157dfb6ea67c2950d7f610e2ead68e` |
| P/Q settings canonical JSON | `d1d254418659f9a074e0092a784e338ccfc3937779c61fd4422390771ba23a16` |

The v4 generation settings SHA-256 is `a6909388705fddca537740712d5ed7be4a61b3de79eec7196c0d206afe2cd55c`.

## C recipe-order correction

The previous implementation formed FN→FP, rejected a cyclic intermediate graph, and only then considered REV. That made recipe eligibility depend on one arbitrary prefix. For truth edges A→B, B→C, D→E and task A→C, the recipe FN(D→E), FP(C→A), REV(A→B) has a cyclic FN→FP prefix but a valid FN→REV→FP order and a valid final DAG.

`enumerate_c_recipes` now defines the initial graph from the disjoint one-each FN/FP/REV set, checks its DAG validity, then checks all six atomic correction orders. It accepts the recipe if the initial and final graphs are DAGs and at least one order keeps every intermediate graph a DAG. The fixed counterexample and the independent audit enumerator are both regression-tested. This is complete over the current C recipe space (one disjoint error of each type); it is not an enumeration of arbitrary multi-error recipes.

## Estimands and inference status

| Question | Population and unit | Contrast / result | Status and interpretation |
|---|---|---|---|
| Primary policy effectiveness | P; independent unit is SCM/topology, with tasks and conditions repeated within it | Development-selected policy vs matched Random on SCM-level paired mean Decision Regret; Path-F1 is a separate comparator with extra GT-path information | Proposed confirmatory target, but cohort size, inference, missingness and resource rules remain unfrozen. This audit does not estimate the outcome. |
| H1: error type and location | P, with predeclared type/location strata and only explicitly stated common support | Same-cost structural corrections by FN/FP/REV and location; assess type × location only where support exists | Exploratory/stratified proposal. Do not claim a pooled type ranking from selected successful cells. |
| H2 in P | General fixed topology/task distribution P | Matched Global vs Task-Focused within the same allowed type and budget | Report the population-average contrast if retained, including the many structurally identical decisions. Current v3 had only 12/17,185 final graph differences. It is a poor sole confirmatory test of priority mechanism. |
| H2 in Q | Conditional competition cohort Q; still clustered within the 100 topology instances | Matched Global vs Task-Focused at a budget that prevents both candidates being corrected | A distinct conditional estimand, not pooled with P. Structural distinction is demonstrable, but statistical power and final confirmatory status are not established. |

Matched Random and Path-F1 comparisons do not identify H2. A selected policy beating Random cannot establish that Task-Focused ordering beats Global ordering.

## H1 common support

For this diagnostic, B-style eligibility means exactly one error, an initially DAG-valid graph, at least one Action→Target path retained, and a task-site FN/REV on a GT Action→Target path or FP incident to Action/Target. Each correction has unit cost. This is a structural support screen, not an effect or regret screen.

| Error type | Eligible task slots | Direct | Indirect | Eligible templates (task slots) |
|---|---:|---:|---:|---|
| FN | 35 / 200 | 0 | 35 | Chain 5; Fork 4; Common Cause 12; Multiple Paths 14 |
| FP | 200 / 200 | 100 | 100 | All templates represented |
| REV | 35 / 200 | 0 | 35 | Chain 5; Fork 4; Common Cause 12; Multiple Paths 14 |

There are 35 task slots with all three error types available under this screen, all indirect. In those common slots, cost and error count can be matched at one, but the position semantics still differ: FN/REV occupy true task-path dyads, while an FP cannot occupy a true dyad and is task-endpoint-adjacent. Thus this is not a clean type-only contrast. Direct-only tasks have no path-surviving FN/REV under this definition. The full P and all eligibility failures must remain visible; a successful-cell average cannot replace the P average.

The competing H1 designs are therefore: (A) restrict a type contrast to common-support indirect or direct-and-indirect tasks and explicitly model location; (B) retain direct-only as a separate stratum and compare only feasible types there; or (C) estimate type-specific conditional means without a cross-type superiority claim. Recommendation: use C as the primary reporting structure, show A as a narrowly defined common-support sensitivity, and preserve B as descriptive support evidence. Step 4B statistical work must define exact weights before any outcome is opened.

Task relation counts are 100 direct-only, 94 indirect-only, and 6 direct-and-indirect across the selected 200 task slots. The two slots are distinct Action/Target pairs; these are repeated tasks within topology, not extra independent SCMs.

## H2 competition cohort Q

Q is defined before policy execution: two same-type errors; both corrections individually DAG-valid; distinct dyads; one error on a GT task path (FN/REV) or incident to a task endpoint (FP), and the other truly peripheral (not on path and not adjacent to Action/Target); the initial graph is a DAG; Action→Target path survives; both unit corrections cannot fit in budget 1. Eligibility does not inspect policy rankings, final graphs, effects, or regret. A deterministic domain-separated seed selects one eligible recipe per topology × task × type cell. All failed cells stay in the denominator.

| Type | Accepted / planned cells | Failures | Accepted by template (out of 50 each) | Accepted by node count (out of 40 each) | Selected rank divergences |
|---|---:|---:|---|---|---:|
| FN | 33 / 200 | 167 | Chain 5; Fork 2; Common Cause 12; Multiple Paths 14 | n=6:6, 7:5, 8:3, 9:10, 10:9 | 13 / 33 |
| FP | 200 / 200 | 0 | 50 each | 40 each | 88 / 200 |
| REV | 55 / 200 | 145 | Chain 5; Fork 8; Common Cause 25; Multiple Paths 17 | n=6:10, 7:8, 8:6, 9:16, 10:15 | 12 / 55 |

Overall, 288/600 repeated cells are feasible; there are 288 selected unique initial graph hashes within their respective type strata. 113/288 eligible selections have different Global and Task-Focused candidate orders. That observed divergence is diagnostic after selection, not an eligibility rule. Strong type imbalance in Q means type results target different structural subpopulations; report type-specific support and do not average without prespecified weights. Q is deliberately narrower than P, so conditional H2 has reduced external validity.

At budgets 0/1/2/4/6, paired policy runs on Q are 288 each. Final graph differences are 0/113/0/0/0; candidate sequences differ for 0/113/113/113/113. Both policies spend totals 0/288/576/576/576. At budget 1 the first choice is exposed; by budget 2 both unit fixes are made, so the final graphs converge. This supports B=1 as a structural H2 diagnostic candidate and shows why a single budget should not be forced across hypotheses. It is not evidence of a regret difference.

## Condition C strata and error location

| Template | Direct path survives / disconnected | Indirect path survives / disconnected |
|---|---:|---:|
| Chain / Mediation | 14 / 11 | 15 / 10 |
| Fork / Branch | 20 / 5 | 12 / 13 |
| Observed Common Cause | 19 / 6 | 15 / 10 |
| Multiple Directed Paths | 21 / 4 | 17 / 8 |

Totals are 133 surviving and 67 disconnected. C itself does not require path survival. These strata should be prespecified if the study intends to distinguish path restoration from edits made while a route remains.

Error-location labels are overlapping structural tags: `gt_action_target_path`, `upstream_of_action`, `target_adjacent_off_path`, `action_adjacent_off_path`, and broad `off_path_peripheral`. In the selected C recipes, the counts are FN path 54, upstream 27, target-adjacent off-path 27, action-adjacent off-path 35, peripheral 146; FP target-adjacent 40, action-adjacent 30, peripheral 200; REV path 58, upstream 27, target-adjacent off-path 18, action-adjacent off-path 24, peripheral 142. Counts overlap and are tags, not mutually exclusive strata. B candidate tag counts and all source rows are retained in the raw JSON.

Under hard-do(X), incoming edges to X are severed in the intervention graph; an edge upstream of X is therefore not automatically a direct route to the target. It is still not declared harmless: observational fitting, misspecification, other graph pathways and downstream decisions can matter. Structural tags do not substitute for outcome evaluation.

## Budget opportunities from the path-surviving B cells

Accepted B has FN 13/66, FP 67/67, and REV 11/67 cells in v4. The graph-only raw matrix contains 1,274 policy runs per budget for these accepted cells (14 policy schedules repeated on each accepted type cell). For each type, at budget 1 the actual spend is 104/182 FN runs, 536/938 FP runs, and 88/154 REV runs; the remainder exhausts available candidates after spending zero. At budgets 2, 4 and 6, the respective types still make only 104, 536 and 88 edits across those repeated runs and terminate on candidate exhaustion. Cycle rejection is zero in these B execution records. The one-error B conditions therefore cannot distinguish high budgets after the only correction is used.

This differs from Q, which deliberately supplies two valid corrections and exposes the priority decision at B=1. Recommendation: retain the original broad budget grid for P and test hypotheses with their own prespecified budgets in later design work; consider B=1 for Q and do not label it a common estimand with P budgets.

## Population weights, sample proposal, and limits

P is the equal-weight candidate topology distribution over the 20 template × node-count strata, with five seeds per stratum; direct and indirect tasks are repeated within each topology. If the target is a different population, define its weights before independent confirmation. Q is a conditional subset with unequal type-specific acceptance. Keep Q conditional and separate; do not reweight Q to resemble P without an explicit, justified target distribution and adequate support.

The proposed 64 development and 200 confirmation SCMs remain candidates, not frozen sample sizes. Sixty-four cannot be evenly split over 20 strata; 200 can be evenly allocated at ten per stratum, but that does not by itself establish the desired target population if acceptance rates, tasks, C path strata or Q eligibility are unequal. Randomized remainder allocation for 64 and confirmation weights must be fixed before confirmation. The independent unit remains SCM/topology; tasks, conditions, Q recipes, relabelings, policies and budgets are repeated measures. Replicate topology instances—not rows—when calculating inferential sample size.

No statistical test, power claim, missing-data rule, sample size, compute cap, or final population weighting is frozen here. These remain Step 4B-2/4B follow-up gates. H1 is not currently identifiable as a type-only effect because type and location support differ. H2 is structurally testable in Q at B=1 but its inferential precision is unknown; in P it remains a diluted population-average contrast. The overall selected-policy effectiveness question is distinct and is not answered by this structural audit.

## Role-label and RNG audit

The stored `derive_stream_seeds` function separates stream names, but it keys each derived stream only by the integer seed. For a given node count and seed, the same ID permutation is therefore reused across all four templates: 150/150 template-pairs have identical `id_mapping`. In this 100-topology diagnostic, Action-ID counts vary by template and are not uniform. For Chain, Fork and Multiple Paths each, counts across 25 topology cells are V00:5, V01:2, V02:4, V04:5, V05:4, V06:2, V07:1, V08:1, V09:1 (V03:0); Common Cause counts are V00:1, V01:5, V02:7, V03:3, V04:2, V05:1, V06:1, V07:2, V08:2, V09:1. This dependence is a design flaw in the small fixed diagnostic seed schedule, not evidence of policy performance.

An exhaustive 120-label permutation of a fixed two-FN competition fixture showed that lexical Global order selected either the task-path error or peripheral error in 60 permutations each, while graph-relation Task-Focused order selected the task-path error in all 120. This positive control demonstrates that Global is label-sensitive and Task-Focused is role-stable for that fixture; it does not imply a general policy advantage. Before fixing the independent SCM population, derive streams from a domain-separated key including master seed, template, node count, topology attempt, and stream name, and re-run a topology-only balance audit. Preserve v4 and this diagnostic as historical evidence; those future data should be a new version. The B1 `derive_stream_seeds` behavior is not silently rewritten in this audit.

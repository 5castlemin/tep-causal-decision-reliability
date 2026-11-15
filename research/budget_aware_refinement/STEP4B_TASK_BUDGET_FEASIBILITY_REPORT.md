# Step 4B-1 task and budget feasibility — preliminary result

**State:** Step 4A DONE. Step 4B-1 IN_PROGRESS. Step 4 remains IN_PROGRESS / NOT FROZEN. This is a graph-only diagnostic, not a policy performance, causal effect, regret, or confirmatory analysis.

## Base and fixed design

The code base is main merge `86b47c0da54cee98a337a1ff4c8f2cae001019c6`. The fixed design uses five seeds (11–15), node counts 6–10, four templates, conditions A/B/C, two task slots per structure, budgets {0,1,2,4,6}, gamma=1, and 14 Global/Task-Focused policy/type combinations. No replacement retries are used. All task-condition attempts remain in the denominator. Settings SHA-256: `70699de103caa28390755ed143c85a864246142bccf44e3eebceedd49f730580`. The complete raw record is in gzip-compressed `step4b_task_budget_feasibility.json.gz`; decompressed JSON SHA-256: `c5deb6ab c8b60573 cc14b597 0fe23663 0aeded52 93aa0efb 04d828ea 0cbf6dcb` (spaces for readability; compare as the concatenated 64-hex digest). A second full run reproduced byte-identical decompressed JSON.

## Task contract and role mapping

Ordered pairs are disjointly classified as direct-only, indirect-only, or both-direct-and-indirect. The selector chooses one seeded-rank direct-only pair and one distinct seeded-rank indirect-only pair. For observed-common-cause, it gives priority to the declared scaffold pair `X→Y`, where the common cause is `C`, the action role is its child `X`, and target is `Y`; this pair can be in the overlap class if an additional direct edge exists. The second task is kept distinct, so the overlap pair is not counted twice. For other templates, indirect selection uses indirect-only pairs. Selection uses only the relabeled graph and fixed seed.

Before selecting tasks, the implementation applies a seed-determined bijection from scaffold roles to immutable node IDs and records the full role map. This removes the original fixed role-to-ID assignment in the diagnostic without changing graph structure. With only five seeds, it does not establish complete label neutrality for a future population. Step 4A's source matrix and files are untouched.

## Task and injection results

The matrix retains **600/600 planned task-condition attempts**. It accepted 569 (94.8%) and recorded 31 failures (5.2%). Both task types succeeded for A and B: 200/200 each. Condition C succeeded in 169/200: 69/100 direct and 100/100 indirect. All 31 failures were direct-task C recipes rejected as `no_dag_mixed_related_and_peripheral_recipe`: 21 chain, 6 observed-common-cause, and 4 multiple-path cases. Failures are retained; no weaker recipe was substituted.

The accepted initial graphs contain 547 unique hashes among 569 rows (22 repeated task-condition rows). This is a structural diagnostic set, not 547 independent SCMs. Across accepted rows, A contains 220 FN operations. B contains FN 16, FP 173, REV 11 (200 rows, at least one task-relevant error each). C has 169 accepted rows with one FN, one FP, and one REV each, plus task-related and actual peripheral errors. Task relevance is defined from GT paths and endpoint adjacency for error construction/diagnosis; the Task-Focused policy ranking still receives G0/H and the declared task, not GT error labels or causal effects.

## Graph-only budget opportunity results

The 569 accepted initial graphs were evaluated under 14 policies × 5 budgets = **39,830 runs**. The engine was used only to produce graph edits and its ledger; no SCM model or action outcomes were computed. Among accepted task-condition rows the initial candidate totals were FN 405, FP 342, REV 180. DAG-valid correction counts were FN 403, FP 342, REV 180; the two non-valid FN insertions would form cycles. This is a difference between initial error candidates and corrections that preserve DAG validity.

| Budget | Runs | Total edits / cost | Unused budget total | Cycle rejections | Unique final graph hashes |
|---:|---:|---:|---:|---:|---:|
| 0 | 7,966 | 0 | 0 | 0 | 547 |
| 1 | 7,966 | 5,562 | 2,404 | 8 | 989 |
| 2 | 7,966 | 7,064 | 8,868 | 12 | 1,235 |
| 4 | 7,966 | 7,410 | 24,454 | 12 | 1,234 |
| 6 | 7,966 | 7,410 | 40,386 | 12 | 1,234 |

At budgets 4 and 6, aggregate edits/cost did not increase: the available structural error candidates were exhausted. Candidate traces recorded zero newly appearing correction operations across this finite run. Across all policy pairs within the same task-condition, budget, and initial graph (14 policies), 130,039/258,895 comparisons (50.2%) ended in the same graph. Matched Global vs Task-Focused pairs differed in final graph in 4/19,915 cases and in edit sequence in 16/19,915. These figures describe this bounded structure set only. They do not imply either policy is generally better.

## Limitations and remaining Step 4B work

- Direct-task Condition C is structurally infeasible for 31/100 tested task cases under the current exact mixed-error, peripheral-error, and DAG constraints. Do not claim equally feasible A/B/C sampling or silently replace these failures. Step 4B must decide whether to modify topology/recipe/population weighting before independent data are generated.
- The design uses five seeds and 6–10 node templates only. It is not a representative SCM sample and contains repeated initial graphs.
- Seeded role relabeling reduces systematic ID placement but is not a proof of policy-label neutrality.
- The graph-only engine uses the reference graph to identify/correct error candidates. It computes neither SCM fitting nor Path F1 performance or Decision Regret.
- Statistical analysis, cohort allocations/weights, failure fallback, time/memory/storage caps, independent development/confirmation streams, and preregistration freeze remain unaddressed.

Step 4B-1 has verified task classification, outcome-blind selection, role relabeling, and a first budget opportunity matrix. It is **IN_PROGRESS**, pending review of direct-C infeasibility and repair-opportunity interpretation, full regression/CI, Self-Review, and any design decisions this diagnostic requires. Step 4 remains **IN_PROGRESS / NOT FROZEN**.

## Implementation checks

Six new Step 4B-1 tests and 60 focused Step 4A plus Step 1–3 regression tests pass locally on Python 3.14 (66 total). Research-state validation passes and all 39 frozen Git blobs match their manifest hashes. Local Python 3.11 is present but lacks NumPy, so the Step 3 regression imports cannot run in that interpreter; the Python 3.11 CI result for this branch remains a separate required check. The local asset-manifest script fails its config hash check on this Windows checkout and is not counted as passed.

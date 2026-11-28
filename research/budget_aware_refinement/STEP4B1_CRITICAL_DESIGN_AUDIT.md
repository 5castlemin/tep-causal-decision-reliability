# Step 4B-1 Critical Design Audit and Identifiability Repair

**Status:** Step 4B-1 IN_PROGRESS. Step 4 remains IN_PROGRESS / NOT FROZEN.

This audit covers structural, error-injection, and policy-order feasibility only. No SCM coefficients, observational data, recommendations, intervention effects, Decision Regret, confirmation SCMs, or Step 5 experiments were created or inspected. Historical v1 and v2 results remain unchanged; the corrected run is stored separately as v3.

## Artifacts and reproducibility

- Preserved v1: `step4b_task_budget_feasibility.json.gz` (600 attempts, 569 accepted, 31 failed, 39,830 graph-only policy runs, 547 unique initial hashes).
- Preserved v2: `step4b_task_budget_feasibility_v2.json.gz` (preassigned B type strata and independent RNG streams, before the C recipe-order correction).
- Corrected matrix: `step4b_task_budget_feasibility_v3.json.gz`.
- Settings SHA-256: `ef95a2cfcfe023e626a9f0f8a5229b6c5e4057e8e4c18dd2551032f9e5c07a31`.
- v3 compressed SHA-256: `df03ccd4ab931580a0e69c1159d67e6b4c5147fa32e1a67fae3f7d2fe721d485`; decompressed JSON SHA-256: `840652a50c90a00fa2a7951e923be90ea775e53a503d215bd3dfc254e0eab2f8`.
- Independent audit artifact and 840-cell cross-tab: `step4b1_critical_design_audit_v2.json`.
- Commands: `py -3.14 -m research.budget_aware_refinement.run_step4b_task_budget` and `py -3.14 -m research.budget_aware_refinement.step4b1_critical_audit`.
- v3 retains all 600 planned cells: 491 accepted, 109 failed, and 34,370 graph-only policy runs. These are not 491 independent SCMs.

## Condition C failure diagnosis

The written C contract requires mixed FN/FP/REV errors, with at least one task-related error and at least one actual peripheral error. It does not require the FN to lie on a GT Action-to-Target path and does not require path survival. The former 31 failures came from combining both extra constraints in the search recipe.

An independent exhaustive enumeration of the 31 legacy failed cells yielded:

| Recipe rule | Cells with a valid recipe | Also feasible in fixed FN->FP->REV order |
|---|---:|---:|
| FN on GT route and preserve a route | 8 | 0 |
| FN task-related and preserve a route | 28 | 28 |
| Peripheral FN allowed and preserve a route | 31 | 31 |
| FN on GT route, route survival not required | 31 | 31 |
| Written C contract | 31 | 31 |

The historical failures were therefore not structural impossibilities under the written contract. Twenty-three failed under the added route-FN plus path-survival restriction; recipe order also mattered when those restrictions were imposed. C now allows peripheral FN and checks all six atomic operation orders, retaining a recipe if at least one order keeps every intermediate graph acyclic. It records path survival without requiring it.

The corrected v3 generated 200/200 C cells. Each has exactly one FN, FP, and REV, plus related and peripheral errors. Action-to-Target paths remain in 129/200. The remaining 71 are valid under the written C contract; Step 4B-2 must decide whether path survival is a separate factor.

## Condition B type imbalance and eligibility

The 200 planned B cells were assigned without outcomes: FN 66, FP 67, REV 67. Failed cells were not replaced.

| Requested type | Attempts | Accepted | Failed | Accepted direct / indirect |
|---|---:|---:|---:|---:|
| FN | 66 | 13 | 53 | 0 / 13 |
| FP | 67 | 67 | 0 | 34 / 33 |
| REV | 67 | 11 | 56 | 0 / 11 |

The current B recipe generates related FN/REV on GT routes and additionally requires path survival. A direct-only task has one path; deleting or reversing its direct edge conflicts with that rule. This prevents direct B-FN and B-REV under the current recipe. FP candidates touch a task endpoint, so all planned FP cells were feasible in this small matrix. The 91 accepted cases cannot be treated as a fair cross-type comparison population. Type-specific target populations and weights need a separate preregistered definition.

Candidate opportunities are not the same as the injected error counts. In accepted B graphs, the requested type had 13 FN, 67 FP, and 11 REV DAG-valid correction candidates. Failures remain in their originally assigned type cells.

## H2: Global versus Task-Focused identifiability

Global and Task-Focused differ only in priority within the same allowed error type. We reconstructed the initial graphs and recomputed DAG-valid candidates for all 17,185 matched pairs.

| Structural comparison state | Pairs | Percent |
|---|---:|---:|
| Fewer than two DAG-valid candidates within all allowed types | 16,705 | 97.20% |
| Candidate competition, but same Global/Task rank | 420 | 2.44% |
| Within-type candidate ranking differs | 60 | 0.35% |
| Edit sequence differs, final graph remains same | 36 | 0.21% |
| Final graph differs | 12 | 0.07% |
| Different cycle rejection count | 0 | 0% |

Full edit sequences differed in 48/17,185 pairs: 36 sequence-only differences and 12 pairs with different final graphs. Among the 60 rank-different cases, 36 had enough budget for all initial valid candidates yet ended at the same graph; 12 were budget-limited but still ended at the same graph; 12 produced different final graphs. The 840 condition x task x template x budget x allowed-type cells are retained in the audit JSON.

The main limitation is absence of within-type candidate competition, not absence of nominal policy combinations. B injects one error type, A usually has a route cut, and C injects one error of each type, leaving few alternatives of the same type. The current matrix therefore provides little structural information for H2. A separate H2 challenge cohort with multiple same-type candidates could address this, but would restrict the target population and must have separately declared weights. No graph may be selected using policy performance or regret.

A fixed positive-control fixture was added for each of FN, FP, and REV: two same-type DAG-valid corrections, budget one, and Global/Task-Focused select different operations and final graphs. This verifies that the implementation can distinguish the policies; it does not estimate an H2 effect or its population frequency. A relabeling test confirms Task-Focused follows the structural role in the fixture.

## Budget and correction opportunities

v3 has 34,370 executions (491 accepted task-condition cells x 14 policies x 5 budgets). All corrections cost one unit.

| Budget | Runs | Total spent | Fully used runs | Runs with >=1 edit | Unique final graphs |
|---:|---:|---:|---:|---:|---:|
| 0 | 6,874 | 0 | 6,874 | 0 | 481 |
| 1 | 6,874 | 5,082 | 5,082 | 5,082 | 990 |
| 2 | 6,874 | 6,820 | 1,738 | 5,082 | 1,429 |
| 4 | 6,874 | 7,228 | 0 | 5,082 | 1,428 |
| 6 | 6,874 | 7,228 | 0 | 5,082 | 1,428 |

Raising budget from 4 to 6 increased neither total spend nor unique final graphs; both budgets saturate because candidate corrections are exhausted. At B=0, "fully used" is true by definition and does not mean an edit occurred. Most executions with budget >=2 stop after candidate exhaustion. Cycle rejections were 150 at B=1 and 234 at B>=2; paired policies had no difference in rejection counts. This does not establish B=4 as a good performance budget. For H2 distinguishability, low budgets expose priority differences, but the confirmatory budget must be chosen alongside the full design and resource limits in Step 4B-2.

## Common Cause, node roles, and RNG

The Common Cause scaffold Action-to-Target indirect pair was selected in all 67/67 indirect cells. It was indirect-only in 49 and direct-and-indirect in 18. The direct task is drawn from direct-only pairs and cannot duplicate that scaffold pair. "Preferred" now means the pair is actually selected whenever it is an eligible indirect pair, rather than merely inserted among candidates.

Role relabeling is a seeded bijection on a SHA-256 domain-separated stream independent of topology. Roles are broadly distributed in this small five-seed matrix, but exact balancing is not guaranteed. Global still breaks ties by immutable ID order, so randomized labels do not prove the removal of ID bias. Task-Focused scoring uses graph distance, with ID tie-breaking for score ties. v3 separates topology, relabel, task, error-injection, and policy-schedule RNG streams and records derived seeds in every row. A larger-run relabel balance or stratification rule remains to be fixed before the main experiment.

## H1/H2 and confirmatory comparisons

The proposed selected-policy versus Matched Random and Path-F1 comparisons can support total comparisons for the selected policy, but do not test whether Task-Focused is better than Global (H2). Path-F1 uses additional GT path information and is not an equal-information optimal baseline. H1 error-type/location differences are also not identified by a single pooled mean given B's eligibility imbalance and C's mixed composition.

Step 4B-2 must first decide whether H2 is confirmatory or exploratory. If confirmatory, preregister the direct Global/Task-Focused contrast under identical allowed types, an eligible competition stratum, primary budget, cohort weights, and failure handling before seeing outcomes. Do not combine the target population and H2 challenge cohort as an unweighted mean. H1 needs separate eligible type/location strata and target weights. Statistical tests were not finalized here.

## Status and next gate

- Step 4A remains DONE; its raw outputs were not changed.
- Step 4B-1 remains IN_PROGRESS. The old C recipe failure was corrected, and a positive-control H2 fixture plus order-aware DAG validation were added.
- Current B-1 structure has too little within-type competition to identify H2 as a primary confirmatory effect. Do not mark B-1 DONE.
- Step 4 remains IN_PROGRESS / NOT FROZEN.
- Step 4B-2 should resolve H1/H2 status, competition-cohort and target-population weights, B type eligibility, and budget-selection rules.
- Full tests, Python 3.11 CI, 39 frozen asset checks, and PR Self-Review are reported separately for the final commit.

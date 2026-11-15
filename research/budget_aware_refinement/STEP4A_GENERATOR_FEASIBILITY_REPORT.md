# Step 4A topology and error injection — feasibility result

**Step 4A structural implementation and fixed matrix: DONE. Step 4 remains IN_PROGRESS / NOT FROZEN.** No SCM coefficients, observations, learning, recommendations, regret, Step 5, or confirmation SCMs were generated.

`step4_topology_generator.is_dag` now uses Kahn's algorithm and is invariant to node/edge input order. `_follows_topological_order` is used only for forward-edge topology generation. This fixes the prior bug where every legal edge reversal against the original order was rejected as cyclic.

The topology generator supports 6–10 nodes and four motifs. Motif edges take precedence over the rounded midpoint density target; added edges respect indegree ≤3. Direct and indirect tasks are enumerated from structure, and may overlap.

Condition A finds a finite minimum FN cut and disconnects all action→target paths. Condition B retains a path and injects at least one related FN, FP, or REV; seed rotation tests the error classes separately. Condition C requires an FN, FP and REV together, with at least one task-related error and one peripheral error. GT topology is used to construct and classify the error strata; this is distinct from the Task-Focused policy, which scores only G0/H.

## Fixed matrix

Seeds `(11,12,13,14,15)` × node counts 6–10 × four templates × conditions A/B/C produced **300 planned attempts; 300 accepted; 0 failed; 0 replacements**. Per condition: A 100/100, B 100/100, C 100/100. B selected FN in 30, FP in 48, and REV in 22 cases. C had exactly one of each error type and both related and peripheral errors in all 100 cases. The JSON matrix retains per-cell inputs, outcomes, type/location counts, path and DAG validity, hashes, failures, retry count, and duplicate summaries.

## Verification

Eleven new Step 4A tests pass. Fifty-seven combined focused/regression tests pass across the new generator, saved Step 4 audit, and Step 1–3 engine/pilot tests. `git diff --check` passes. Tests cover legal reversal, actual directed cycle rejection, order invariance, atomic REV, GT and initial DAG validation, A disconnection, B path-preserving REV and single-type cases, and C mixed related/peripheral errors.

These are structural feasibility results for the declared finite design matrix. They do not establish population representativeness, causal/effect behavior, regret, performance, order-dependent repair frequency, or validity of proposed Step 4B statistical/resource contracts. No replacement retry was allowed; every planned cell remains in the denominator.

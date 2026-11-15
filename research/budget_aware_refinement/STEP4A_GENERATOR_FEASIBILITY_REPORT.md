# Step 4A topology and error injection — partial feasibility result

Status: **IN_PROGRESS**. This implementation is a topology-only prototype. It does not generate coefficients or observations, fit models, recommend interventions, or calculate regret. No Step 5 or confirmation SCM was run.

## Implemented contracts

- `step4_topology_generator.py` builds 6–10 node DAGs for chain/mediation, fork/branch, observed common cause, and multiple directed paths. Immutable IDs are `V00`…; canonical ID order is the topological order. Required motif edges take precedence over the requested density: the edge target is `round(midpoint(density) * n(n-1)/2)`, raised to the motif edge count when needed. Augmentation respects a maximum indegree of three.
- Direct task pairs have a direct edge. Indirect task pairs have a directed path of length at least two. The default allows a pair with both direct and indirect paths. Task enumeration uses graph topology only.
- `step4_error_injection.py` classifies pairwise differences as atomic FN, FP, or REV. A uses a finite minimum FN path-edge cut. B enumerates one FN, one REV and one FP, retaining only acyclic initial graphs with an X→Y path. C currently requires a B recipe and a peripheral truth edge; infeasibility is returned explicitly.

## Checks run

`py -3.14 -X utf8 -m unittest tests.test_budget_refinement_step4_generator -q`: **8 tests passed**. Coverage includes deterministic output, all template/node-count DAG and parent constraints, task classification, motif density precedence, atomic REV classification, A disconnection, explicit B infeasibility, and invalid input. `git diff --check` passed.

The B probe used `multiple_directed_paths`, 8 nodes, seed 19. The selected scaffold had two X→Y routes, but added density edges made every enumerated path-preserving FN/FP/REV recipe cyclic or unavailable; the generator returned `no_dag_path_preserving_fn_fp_rev_recipe` with cycle rejection evidence. This is a single diagnostic case, not an estimate of population feasibility. The chain B case also returns explicit infeasibility because a single directed route cannot survive removal of a path FN.

## Not established

No full fixed-seed matrix was run, so there are no defensible template-by-condition success rates, retry distributions, or duplicate rates. C, relevant/peripheral error quotas, order-dependent repair opportunities, and policy-engine candidate counts have not been validated across the design. The prototype does not yet retain a full per-attempt JSONL report. The current four-template proposal therefore cannot be frozen from this result.

## Next Step 4A work

Implement a bounded run driver that records every template × node-count × condition × seed denominator, including failed topology and injection reasons, error counts, relevance counts, graph hashes and cycle rejections. Then assess the full matrix before changing template weights or admitting only feasible strata. Any population-weight change must be documented before independent SCM generation. Keep Step 4 IN_PROGRESS until that audit and the separate Step 4B contracts pass.

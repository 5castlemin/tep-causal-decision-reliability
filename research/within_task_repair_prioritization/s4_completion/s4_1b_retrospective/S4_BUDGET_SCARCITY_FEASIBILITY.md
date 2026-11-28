# S4 budget-scarcity feasibility

## Existing pilot feasibility

K denotes initial legal M4 edits. `K>B` is a structural opportunity condition; it does not guarantee different consequences. Observed counts:

| Cohort | K>B at B=1 | B=2 | B=3 | B=4 |
|---|---:|---:|---:|---:|
| General (Q-common-conditioned) | 6/32 | 2/32 | 1/32 | 0/32 |
| Opportunity-rich (K≥2) | 32/32 | 6/32 | 3/32 | 1/32 |

The first cohort has many no-op/one-option cases; the second has a mean K of only 2.34375. The pilot is therefore weak for distinguishing priorities except at B=1 in the selected cohort. Its 63 policies still had large zero-mass and trajectory redundancy.

## S4-2 proposed structural strata

No new cohort was generated. Proposed matched diagnostic strata are K=2/B=1; K=3/B=1–2; K≥4/B=1–3; and B≥K saturation. For each initial G0, record the full initially feasible candidate set and recompute feasible candidates after every edit. K is not treated as fixed over the trajectory.

Admission must use structural variables only: node/edge topology, error type and role, task-path location, alternative paths, and legal edit counts. Regret, optimum action, policy success, score gains, or oracle gaps are prohibited for admission. Opportunity-rich findings are conditional and cannot estimate the general cohort effect.

## Matched corruption proposal

Within each SCM block, keep coefficients, observational frame, task, learner, action grid, target/scale and evaluator fixed. Generate paired G0 variants that vary a predeclared structural feature: (A) same error type/count at different positions on a causal path; (B) path vs backdoor/task-relevant roles where topology allows; (C) co-located path errors vs dispersed errors, with/without an alternative path; (D) budget B=1–4 on the same G0; (E) edits that do or do not unlock later feasibility. Record any collateral structural changes; if a contrast changes multiple features, label it bundled rather than a single-factor effect.

Use SCM as the independent block and G0 variants as repeated measures. Primary reporting should be paired within SCM, with SCM-cluster bootstrap or a prespecified hierarchical model only when cell support permits. Keep general and opportunity-rich strata separate. S4 pilot is only an implementation/variance source and is not confirmatory.

### Generation contract fields required before separate approval

Freeze generator revision, topology/task sampler, structural eligibility algorithm, strata quotas, proposal ceiling, sample cap, number of matched variants per SCM, seed namespace, corruption allocation, gamma conditions, evaluator, outputs, compute/time/RAM caps, telemetry, failure/attrition and resume rules. Eligibility audit must demonstrate structural balance without reading outcome-derived fields. No generation is authorized by this design note.

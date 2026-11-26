# E-2 — Extended-budget and saturation results

## Budget cap and initial error burden

The cap was computed from each entire original cohort before looking at extended-budget performance: `B_max=max(4,max_i E_i)`, where `E_i` counts distinct reference-relative initial FN, FP, REV and UNRES adjacencies.

| Cohort | n | Min | Mean | Median | P90 | P95 | P99 | Max / Bmax |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| C Development | 64 | 0 | 2.141 | 2 | 4 | 5.85 | 6.37 | 7 |
| C Held-out | 200 | 0 | 2.170 | 2 | 5 | 5 | 7 | 9 |

The same policy definitions and unit edit costs were retained. The maximum was not extended to an arbitrary large value. The new B5–7 Development and B5–9 Held-out analytic evaluations are extra budget views of the original SCMs, not new SCM observations.

## Budget extension

All 17 policies were evaluated at the pre-fixed extended budgets. B0–4 matched exactly before any B>4 result was accepted. The full unit results are kept as local-only artifacts; public outputs are aggregates and hashes, not the SCM-level extended CSV.

For the canonical structural repair at the cohort cap, all initial reference discrepancies were removed in **64/64 Development** and **200/200 Held-out** SCMs. In contrast, M4 structurally saturated in 18/64 Development and 80/200 Held-out cases, with mean residual error counts 1.422 and 1.380. M2+M4 saturated structurally in 27/64 and 109/200 cases, leaving mean 0.719 and 0.655 errors. Full Greedy and Canonical Oracle reached structural saturation throughout. This gap is policy saturation, not evidence that remaining edits have no decision value.

## Saturation distinctions

- Structural saturation means no remaining reference-relative graph discrepancy.
- Policy saturation means no remaining candidate eligible for that metric subset.
- Constraint saturation means eligible candidates remain but every candidate violates DAG feasibility. Final-state candidates were explicitly re-enumerated rather than inferring this solely from cumulative rejection counts.
- Decision saturation means action and analytic regret match at every later tested budget; a single unchanged step is insufficient.

The terminal feasibility audit found DAG-constraint saturation for 2/200 Held-out M4 cases (1%) and none for the other reported policy/cohort combinations; M4 had no remaining eligible candidate in the other cases. Decision saturation is measured separately as the first budget after which action and regret stay unchanged through all later tested budgets. Many individual units already had the same decision at B0 and all later budgets; the report therefore includes the full unit distribution instead of treating the cohort median as a universal “saturation point.” Structural restoration is not a proxy for decision saturation.

## Full-reference learner diagnostic

The reference-DAG learner was fitted on the same reconstructed observations, with the same Ridge alpha and action grid, then evaluated analytically. It is an oracle-structure diagnostic only: it is neither a regret-optimal action oracle nor evidence that structure identification is available in deployment. Residual regret can arise from finite training observations, Ridge fit, action grid and target, among other factors; this analysis does not uniquely decompose those causes.

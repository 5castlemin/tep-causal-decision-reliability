# S4 pilot v1 limitations audit

Status: `RETROSPECTIVE_AUDIT_COMPLETE_WITH_LIMITATIONS` (2026-11-27). This report does not modify the historical pilot contract or its results.

## Cohort and execution scope

The stored pilot contains 32 `general` and 32 `opportunity_rich_diagnostic` SCMs, drawn from a single signed-linear Gaussian generator family. The General admission rule was described in the pilot lock as indirect-task plus Q-common. This differs from frozen Research C: C requires strict indirect-only task eligibility, while Q-common recipe support is a secondary flag rather than an admission condition. Therefore S4 General is a Q-common-conditioned cohort and must not be presented as representative of the C proposal population. The opportunity-rich cohort adds a structural screen requiring at least two initial DAG-feasible M4 edits.

The run generated 64 SCMs, 142 G0 screening draws and 32,768 observational rows. It generated zero sampled intervention response rows; evaluation used the analytic SCM evaluator. No matched-corruption variants were generated. Both cohorts use `gamma=0` only.

## Corrected candidate opportunity diagnosis

The exact initial feasible M4 candidate distribution is in private external artifact root / `opportunity_budget_unit_diagnostics.csv` (private):

| Cohort | K=0 | K=1 | K=2 | K=3 | K=4 | K=6 | Mean K |
|---|---:|---:|---:|---:|---:|---:|---:|
| S4 General (Q-common conditioned) | 16 | 10 | 4 | 1 | 1 | 0 | 0.78125 |
| Opportunity-rich (K≥2 selected) | 0 | 0 | 26 | 3 | 2 | 1 | 2.34375 |

For General, K>B counts were 6/32 at B=1, 2/32 at B=2, 1/32 at B=3, and 0/32 at B=4. For Opportunity-rich they were 32/32, 6/32, 3/32, and 1/32, respectively. The enrichment did create K>B scarcity at B=1, but that alone does not guarantee decision-value heterogeneity.

A structure-only replay of the saved truth/G0 inputs found 26 initially feasible candidate edits in General and 75 in Opportunity-rich. Across these first edits, 10 General first-edit states had no remaining legal M4 continuation; all 75 Opportunity-rich first-edit states had at least one. A previously infeasible M4 candidate became feasible after the first edit in 3 first-edit states, all in Opportunity-rich. This is a structural feasibility diagnosis only; it does not imply a beneficial edit.

## Preflight corrections

- Paired differences are reported with explicit direction. For `M4 − Full Greedy`, a negative value favors M4; counts are therefore relabeled as M4-better / Full-Greedy-better / tie in the correction report.
- The S3 selector itself uses T gain/cost, then M4 gain/cost, then canonical ordering. A saved ranking diagnostic that omits the M4 secondary tie-break and calls tied-set containment a selected-best hit is not equivalent to actual selected-edit accuracy. The latter is a distinct diagnostic limitation.
- Pilot output hashes and checkpoint hashes were rechecked against both private manifests; all listed files matched. See correction report.

## Scientific limits

The General cohort's admission mismatch, small n=32/cohort, structural selection in Opportunity-rich, low outcome variation and high M4 agreement with the limited ≤2-edit benchmark restrict inference. All S4 contrasts are post-hoc, conditional, and exploratory. No causal effect of error type/role is identified, and no confirmatory claim follows from the paired intervals.

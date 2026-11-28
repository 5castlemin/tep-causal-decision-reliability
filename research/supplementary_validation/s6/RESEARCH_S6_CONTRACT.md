# Research S6 — Error-Type Information versus Structural Information

**Gate:** `S6_RETROSPECTIVE_POLICY_EVALUATION_COMPLETED_WITH_LIMITATIONS`
**Classification:** post-hoc retrospective policy evaluation
**Contract lock:** [`RESEARCH_S6_EXECUTION_LOCK.json`](RESEARCH_S6_EXECUTION_LOCK.json)

## Estimand and analysis units

The primary descriptive comparison is B=1 analytic Decision Regret on saved S4 candidate records. Each row in the paired analysis is one SCM. Development has 80 SCMs and is used to rank error types; the 160-SCM Q-common-admitted replication cohort is evaluated with that locked ranking. Replication outcomes were already reported for other policies, so S6 is not a new independent confirmation.

The paired contrast is mean regret of the left policy minus mean regret of the right policy. Negative values favor the left policy. The 95% intervals are SCM-clustered pointwise percentile intervals from 10,000 common bootstrap index arrays (seed `2026112806`). They are not simultaneous intervals and do not establish equivalence or noninferiority.

## Policy rules

The candidate universe is the saved set of initially DAG-legal M4 one-edit candidates. The type ranking is selected only from Development SCM-balanced mean single-edit regret reduction, with lexical tie-breaks. It is `REV → FN → UNRES → FP`. A type-ranked policy selects the highest-ranked available eligible type, then maximizes M4 gain and applies canonical pair/operation order. When no positive M4 candidate exists it falls back to Frozen M4. T5 uses positive T5 gain, M4 secondary tie-break, canonical order, and M4 fallback. The regret oracle may use saved one-edit regret gains and is diagnostic only.

## Deliberate scope limit

This locked run replays B=1 choices only. The saved candidate table contains initial one-edit values, not a complete dynamic trajectory for new type-based policies at B=2–4. No B=2–4 type policy results are inferred from B=1 or generated here. No SCM, graph, observation, or intervention response was created.

# S4 confirmation design update from the bounded pilot

**Status:** `PROPOSED_NOT_LOCKED`; no confirmation cohort is authorized or generated.

## Pilot-based paired-difference precision sensitivity

Using the frozen pilot's within-SCM `Regret(S0)-Regret(M4,B=2)` values, the observed sample SD was 0.1691 in the general cohort (n=32) and 0.2543 in the opportunity-rich diagnostic cohort (n=32). A simple normal-approximation planning calculation, `N ≈ (1.96 × SD / half-width)^2`, gives the following sensitivity values:

| Pilot population used for variance | N for nominal 95% half-width 0.03 | N for half-width 0.02 | N for 80% power at hypothetical paired difference 0.05* |
|---|---:|---:|---:|
| General | 123 | 275 | 90 |
| Opportunity-rich diagnostic | 277 | 622 | 203 |

`*`The 0.05 value is an arithmetic sensitivity point only. It is not a user-approved minimum meaningful effect, industrial threshold, or confirmatory hypothesis.

These calculations are not a final sample-size recommendation: the variance estimates come from small, post-hoc, structurally specified pilot cohorts; the opportunity-rich population has conditional eligibility; normal approximations omit attrition and generation failures; and no independent matched-corruption cohort has yet established the intended sampling unit. A final protocol must first choose whether the target population is general, opportunity-rich, or a paired/matched design; define the primary practical effect or precision goal; freeze the selected comparator and multiplicity family; then recalculate N with a conservative variance/attrition sensitivity before any new SCM generation.

The pilot does not support selecting a policy from the 63 T combinations as confirmatory. Any Development-based selection rule must be written and committed before confirmation data are generated. Existing Research C Held-out units and this S4 pilot are all development/exploration data for that future study.

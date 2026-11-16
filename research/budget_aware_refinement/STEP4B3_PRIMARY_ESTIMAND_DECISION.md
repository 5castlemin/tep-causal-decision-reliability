# Step 4B-3 primary estimand decision

Status: Step 4B-3 structural/design gate is **DONE**. Option B is selected as the **planned primary confirmatory question**, with inferential feasibility still gated by Step 4B-4. This decision changes the proposed Step 4 design prospectively; it does not alter prior hypotheses or results. Step 4 remains `IN_PROGRESS / NOT FROZEN`.

No coefficients, observational data, fitted models, effects, regret, or policy-performance results were calculated.

## Decision and evidence

| Design | Primary contrast | Structural evidence | Decision |
|---|---|---|---|
| Option A | Population P, B=4, development-selected one of 14 policies vs Matched Random | On the preserved v4 P matrix, all 34,370/34,370 policy/random pairs (14 policies × 491 accepted initial graph rows × five preregistered Random seeds) ended with the same graph (100%). Candidate order differed in 412/14,000 A pairs (2.94%) and 0/6,370 B or 0/14,000 C pairs. No pair exhausted budget 4 while an allowed DAG-valid correction remained. | Keep as a secondary/exploratory benchmark. It preserves breadth but does not structurally distinguish final policy results on this matrix. This is not a claim about regret; regret was not calculated. |
| Option B | Q common-support cohort, B=1, matched Global vs Task-Focused within the same error type | In the new context-keyed feasibility grid, 121/286 accepted Q cells had different candidate rankings and final graphs at B=1; the 34-SCM all-type common-support subset had 47/102 differing final graphs. At B=2, all two unit corrections fit and final graphs coincide. | Select as the planned primary confirmatory question, conditional on Q and B=1. It directly targets H2's priority mechanism; it does not generalize automatically to P. |

Option A spent-cost distributions were identical for policy and Random in each matched pair. By condition, spend counts per matched pair were: A, 0:6,000 / 1:7,040 / 2:920 / 3:40; B, 0:2,730 / 1:3,640; C, 0:360 / 1:5,980 / 2:5,660 / 3:2,000. No run spent all four units. All allowed-type DAG-valid correction counts remaining after either run were zero. In A, edit order differed in 412 pairs, all in indirect tasks; final graphs still matched. Five Random seeds are repeated Monte Carlo runs, not additional SCM units.

These are graph-only structural distinguishability findings. Equal graphs do not constitute a computed equality of Decision Regret, and different graphs do not guarantee different regret.

P/B=4 audit settings SHA-256: `665e9e28f981faaeea3c30691fe02f8053d0156f770434d86d0efaf9f89c342e`. Compressed pair log SHA-256: `f879ea7a30ff74659329fe99d6f054f3c2f3815234b7e5a4bf8aef4152400d26`.

## Primary H2 estimand

Let Q-common contain an independent SCM/topology only when one of its prespecified selected tasks is eligible for FN, FP, and REV competition under the same topology-only rule. For each SCM `i`, run one matched error-graph version per type and compute:

`D_i = (D_i,FN + D_i,FP + D_i,REV) / 3`, where `D_i,type = Regret_Global,i,type - Regret_TaskFocused,i,type`.

Positive `D_i` favors Task-Focused. The independent analysis unit is the SCM/topology, not the three error-type versions, tasks, policies, seeds, or budgets. For each paired type version, Global and Task-Focused receive the same initial graph, oracle correction candidates, task, data, cost, allowed error type, type schedule, and schedule RNG; the intended difference is the within-type priority rule. Both policies use oracle-labelled correction candidates. This question tests H2; it is not a comparison of the selected 14-policy winner against Random.

Q-common eligibility is determined before coefficient or outcome generation. It does not require different policy rankings, different final graphs, a favorable effect, or a favorable regret. All eligible rows, including identical-policy results, remain in the target population.

## Q populations, weights, and sample implications

The new structure-only grid contains 100 unique topology instances and 200 selected task slots. The 600 planned Q task-type cells yielded FN 34/200, FP 197/200, REV 55/200; 286 cells were accepted. The accepted-cell mixture is 11.9% FN, 68.9% FP and 19.2% REV if cells are simply pooled. These are unequal, type-conditional structural populations, not interchangeable samples from one common type population.

The all-three-type common support is 34 independent SCM IDs and 34 task slots, all indirect. Its observed template counts are Chain 7, Fork 4, Multiple Paths 14, Common Cause 9; node counts n=6:5, 7:3, 8:6, 9:8, 10:12. Each of the three types has the same 34 common-support SCM/task slots. At B=1, final graphs differ in FN 17/34, FP 16/34, REV 14/34. This cohort is selected by common structural eligibility only; no cell is dropped because its policy rankings coincide.

For the primary composite, use equal type weights `1/3` within each common-support SCM to form one `D_i`. Across SCM strata, target the P generator conditional on Q-common eligibility: conceptually `w(stratum) ∝ w_P(stratum) × Pr(Q-common eligible | stratum)`. If future sampling oversamples sparse strata to meet quotas, use fixed design weights to restore this conditional target. Do not average the full type-specific FN/FP/REV populations without an explicit estimand.

Only 34/100 topology instances in this fixed diagnostic passed Q-common. Thus 64 development or 200 confirmation **eligible Q-common SCMs** cannot be assumed to come from 64/200 P draws. At the observed 34% yield, roughly 188 and 588 topology candidates respectively would be expected to yield those counts; this is a planning approximation, not a guarantee or final attempt limit. Step 4B-4 must set finite attempt caps, nonreplacement handling, target weights, and precision/power before confirmation data exist. If the cap is reached short of target, report the shortfall and keep the prescribed analysis; do not replace failures with outcome-selected graphs.

The broader per-type Q populations remain useful secondary structural strata: FN 34 cells on 34 SCMs, FP 197 cells across 100 SCMs, REV 55 cells on 55 SCMs. If separately estimated, each needs its own SCM-level conditional estimand and support report; those estimates are not a single common-population type contrast.

## Hypothesis status and protocol consequences

- **H2**: planned primary confirmatory target on Q-common at B=1; final inferential confirmation depends on Step 4B-4 sample, power, missingness, and resource feasibility.
- **Primary policy effectiveness (selected policy vs Random in P at B=4)**: secondary/exploratory benchmark, not the primary confirmatory question. The five-seed Matched Random comparison remains useful for breadth, but the fixed structure matrix produced 100% identical final graphs.
- **Path F1**: separate oracle benchmark with extra GT path information; secondary/exploratory and never represented as an equal-information baseline.
- **H1 error type/location**: exploratory/stratified; type and error-location support do not align well enough for an unqualified pooled type effect.
- **H3 cost/structure robustness**: Step 7 secondary analysis. **H4 independent SCM generalization**: Step 6 scope; no claims here.

This is a design decision, not the final statistical freeze. Exact sample allocation, confidence interval, test, multiplicity family, minimum meaningful difference interpretation, failure/fallback rules, compute/storage caps and code/config freeze remain open for Step 4B-4. The earlier Step 0 proposal remains preserved as historical rationale; it is not silently rewritten as if Option A had never been proposed.

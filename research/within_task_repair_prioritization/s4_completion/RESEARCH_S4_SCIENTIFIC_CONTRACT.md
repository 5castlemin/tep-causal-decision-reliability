# Research S4 scientific contract (proposed; not executed)

**Classification:** independent confirmatory follow-up proposed after post-hoc S3. **Status:** `PROPOSED`. No new data or experiment is authorized or represented here.

## Question and estimand

Among task-relevant graph errors, how well do frozen structure-guided repair policies rank and select decision-improving repairs, compared with an outcome-informed feasible optimum, and which prespecified structural conditions modify repair value?

The primary estimand should be the SCM-population mean paired regret difference at a single prespecified task and budget, between frozen M4 and one policy selected using Development only. Positive/negative orientation must be fixed in the finalized protocol. A separate within-SCM diagnostic estimand describes the optimality gap to the best feasible repair under the same initial graph, candidate set, cost, and budget. Outcome-informed benchmarks remain nondeployable.

## Cohorts and units

Use a general cohort sampled from the frozen Research C SCM generator and a separate opportunity-rich diagnostic cohort selected solely by structural eligibility (at least two initially legal M4 edits). Report each separately; do not pool them. The independent unit is SCM. For matched corruption contrasts, retain SCM as a block and vary only prespecified corruption location/type/role while keeping task and truth fixed.

## Policies and budget

Freeze S0, Full Greedy, M4, a small set of T policies selected from Development only, Random-M4 with exact expectation or prespecified randomization, and ex-post single/sequence optimal diagnostics. Primary budget should be B=2 to align with existing evidence; other budgets are secondary. The exact candidate universe, DAG checks, operation costs, early-stop/fallback rules, tie tolerance, and seeds must be versioned before confirmatory outcomes are observed.

## Outcomes and analysis

Primary: SCM-level paired regret contrast. Secondary: edit value, action changes, structural recovery, interaction, opportunity-conditioned effects, and policy optimality gap. Report point estimates and SCM-clustered uncertainty. Candidate edits are not independent observations. Multiplicity scope and Holm family must be prespecified; broad metric-subset searches are exploratory. Separate structure-only observable predictors from oracle truth/effect/regret predictors. The latter may diagnose mechanisms but cannot enter an executable policy.

## Evidence boundary

Existing Research C cohorts are development/exploration only for S4 because they have already been examined. Research D is not eligible until private unit-level recommendation and response artifacts are available with verified hashes. No C regret and D tracking loss pooling. This contract does not authorize execution.

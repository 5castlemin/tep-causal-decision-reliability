# Research S4 independent development pilot — execution report

**Status:** `PILOT_EXECUTED_WITH_LIMITATIONS`; exploratory only. This report supersedes neither Research C/S3 nor any frozen result.

## Locked design and execution

The pilot used the committed contract and seed namespace `research-s4-pilot-v1`. The existing Research C proposal, topology, linear signed-coefficient SCM, Gaussian observation, graph-corruption, Ridge (`alpha=1`) and analytic SCM evaluator implementations were reused. The objective was `gamma=0`; action choices were the five training-standardized `k` values `{-1,-0.5,0,0.5,1}`. The pilot did not sample intervention response rows.

| Cohort | Retained SCMs | Proposal attempts | G0 screening draws | Observations | Eligibility |
|---|---:|---:|---:|---:|---|
| General | 32/32 | 123 | 32 | 16,384 | Existing outcome-blind proposal admission |
| Opportunity-rich diagnostic | 32/32 | 379 | 110 | 16,384 | Same admission plus at least two initial DAG-feasible M4 edits, screened before coefficients/data/outcomes |
| Total | 64 | 502 | 142 | 32,768 | Cohorts remain separate |

The opportunity-rich acceptance yield was 32/110 screened G0s (29.1%). It is a structurally selected diagnostic population, not a prevalence estimate or a representative cohort. Across the 64 retained units, the locked recommendation table contains 371 graph-level rows; the 4,992 policy rows cover S0, M4, Full Greedy at budgets 0–4 and all 63 T-subset Greedy policies at B=2. The analytic evaluator produced 100 initially feasible single-edit candidate rows and 150 ordered feasible two-edit interaction rows. Candidate and interaction rows are nested within SCM and are not independent observations.

## Primary pilot summaries

The estimand is the within-cohort SCM average of `Regret(S0)-Regret(M4, B=2)` under the frozen pilot task and analytic evaluator. Intervals are 2,000-replicate SCM percentile bootstrap intervals, pointwise and descriptive; they are not confirmatory tests.

| Cohort | Mean paired difference | 95% bootstrap interval | SCM differences (M4 improves / worsens / ties) |
|---|---:|---:|---:|
| General, n=32 | 0.049796 | [0.000000, 0.115352] | 3 / 0 / 29 |
| Opportunity-rich, n=32 | 0.131258 | [0.050886, 0.217694] | 10 / 1 / 21 |

Positive values favor M4. The broad interval and high tie frequency in the general cohort show that the pilot is not a precise estimate of average benefit. The larger opportunity-rich contrast is conditional on structural eligibility and must not be generalized to the general cohort.

At B=2, general-cohort mean regret was 0.059197 for S0, 0.009401 for M4 and Full Greedy, and 0 for T3+T4 and T3+T5; their mean edit counts were 0, 0.688, 1.531, 0.688 and 0.688, respectively. In the opportunity-rich cohort, means were 0.132175 for S0, 0.000917 for M4, 0.048376 for Full Greedy, and 0.000917 for T3, T4, T3+T4, T3+T5 and T3+T6. M4 and Full Greedy each used a mean of 2 edits there. These small-cohort descriptive values do not establish a stable ranking among the 63 subsets.

The M4 B=2 minus Full Greedy paired difference was exactly 0 in the general cohort (32/32 ties). In the opportunity-rich cohort it was -0.047459, with a pointwise 95% interval [-0.113196, -0.000589]; negative means lower regret for M4. This is exploratory and conditional, with only 32 SCMs.

The best evaluated M4 sequence of length at most two was a privileged ex-post diagnostic that used analytic outcomes. Its mean regret was 0 in both cohorts; M4 B=2 exceeded that diagnostic by 0.009401 (general) and 0.000917 (opportunity-rich). This search universe includes no edit, feasible initial single edits, and feasible ordered two-edit sequences; it is not an unrestricted optimal policy. In the general cohort, only 6 SCMs contributed the 26 ordered interaction rows; in the structurally enriched cohort, 32 SCMs contributed 124 rows. Most pairwise interaction values were exactly zero (general 24/26; opportunity-rich 110/124); there were 2 negative and 0 positive general rows, and 2 negative, 12 positive, and 110 zero opportunity-rich rows. Ordered pairs are dependent and these counts are descriptive.

Candidate summaries by error type and structural role are in `outputs_pilot_v2/single_edit_aggregates.csv`. They show heterogeneous observed values and many zero-gain candidates, but the small nested candidate counts, selected opportunity cohort, and lack of matched corruption prevent causal interpretation of type or role differences. No stable explanatory regression or general repair rule is identified.

## Execution recovery and resource record

Generation completed once. A type error in the evaluator's candidate-pair dictionary stopped the first evaluator invocation before any evaluator table was saved. The same persisted input and recommendation lock were retained. A separate continuation path then encountered two implementation issues (wrong module import, then a summary field-path error). Both were corrected; the last continuation verified checkpoint digests and read the already written evaluator result tables rather than regenerating any data. No alternate seed, SCM, G0, observation, recommendation, or intervention sample was generated. The final private checkpoint lock is SHA-256 `d7446ab164250af8f64f101bc6ffc5f8829444470186a47785b792b7e3d113ac`; the four private evaluator-table hashes are recorded in that lock and in the external private artifact manifest.

The runner's wall-time and Windows process-RSS guards were active at proposal/SCM and evaluator-unit boundaries. The final summary failed to persist peak RSS and end-to-end elapsed time because execution crossed processes during recovery. Therefore no numeric peak-memory or total runtime claim is made. The observed process snapshots were below 130 MB but are not a substitute for continuous peak telemetry. No cap breach was observed; resource telemetry completeness remains a limitation.

## Integrity, interpretation and remaining scope

The recommendation manifest was written before analytic evaluator access and bound into the continuation lock. The evaluator received no new sampled intervention responses; outcomes came from the existing analytic ground-truth evaluator. Private unit-level inputs, recommendations, evaluator rows and response-related values remain outside the public repository. Public files contain only aggregate summaries.

The pilot supports implementation feasibility for two small cohorts and shows that structural opportunity changes which repairs can be evaluated. It does not isolate causal mechanisms because SCMs/tasks vary, the opportunity cohort is selected on repair feasibility, and no matched corruption variants were generated. It does not validate nonlinear mechanisms, Research D, manufacturing operations, or a confirmatory policy comparison. A frozen independent confirmation protocol remains proposed and requires a separate authorization before generating any new confirmation cohort.

Research D/S5 remains `BLOCKED_UNAVAILABLE_PRIVATE_UNIT_ARTIFACTS`: only the prior audit summary was available in the approved local artifact root; no private recommendation, unit-level G0, training-frame, or response-vector content was available for replay. No D generation, refit, or intervention sampling was attempted.

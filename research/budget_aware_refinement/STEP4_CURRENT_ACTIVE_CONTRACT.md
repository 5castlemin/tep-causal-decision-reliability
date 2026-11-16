# Step 4 Current Active Contract

## CURRENT ACTIVE CONTRACT — FROZEN

**Status:** FROZEN as the research protocol and production execution contract. This does not mean Step 5 or Step 6 data have been generated. The content hashes are in `step4c2_final_freeze_manifest.json`; the exact Git commit/tree are recorded externally in PR/CI evidence to avoid self-reference. A change to any manifested file requires a new version and freeze review.

- Population: P conditioned on strict Q-common structural eligibility. The task is indirect-only: a directed Action→Target path of length at least two exists and the direct Action→Target edge is absent.
- Budget/cost: B=1, gamma=1.
- Paired policies: Task-Focused vs ID-ordered Global, on the same graph, task, data, candidate set and evaluation target.
- Error versions: FN, FP, REV; equal within-SCM weights of 1/3. They are repeated measures, not independent SCMs.
- Independent analysis unit: independently generated SCM.
- Target direction: after strict-Q eligibility and atomic registry admission, assign delta `+1,-1,+1,...` by admitted ordinal separately within each cohort. Persist it before running; all types and both policies for one SCM share the same value. Rejections do not consume an ordinal.
- Targets: 64 development and 200 held-out replication eligible admissions; finite proposal caps 386 and 1,104. Admission targets and complete-composite counts are separate. Post-admission failures stay in the admitted denominator and are not replaced; a cap shortfall is reported without adding proposals.
- Outcome: SCM-level arithmetic mean `D_i=(D_FN+D_FP+D_REV)/3`, with `D_type=Regret_Global-Regret_TaskFocused`.
- Inference: Option B. Report estimates, distributions, denominators, failures and sensitivity analyses. No confirmatory superiority or equivalence claim is licensed.
- SCM generator: signed linear acyclic equations; sorted edge-ID coefficient assignment with magnitudes Uniform[0.25,0.8] and independent fair signs; independent centered Gaussian disturbances with node SD Uniform[0.8,1.2]; one shared 512-row observational sample. The Gaussian family prospectively supersedes the historical Uniform disturbance proposal. No outcome/effect/Regret-based resampling or clipping.
- GT: analytic hard-do intervention mean from the separate truth equations. GT values cannot enter eligibility, error-candidate generation, policy ranking or recommendations. Missing/nonfinite any-type outcomes prevent the SCM composite; no zero imputation.

## FROZEN OPERATIONAL SETTINGS

The research cohort entry point is `run_step4c2_research_cohort.py`. It requires the frozen manifest, matching pinned runtime, explicit expected Git commit and tree, and an output directory outside the repository before generating any proposal. It uses the settings in `step4c2_operational_settings.json`; no research run is authorized by this freeze task.

| Control | Frozen value | Enforcement / limit |
|---|---:|---|
| OS / Python | Windows `Windows-10-10.0.26200-SP0`; CPython 3.11.15 | Exact runtime check at cohort entry |
| Packages | NumPy 2.4.3; pandas 3.0.1; NetworkX 3.6.1 | Exact runtime check; requirements pinned |
| Stage isolation | enabled | Spawned child per stage |
| Unit timeout | 2 s | Child terminated on timeout; stage failure persisted |
| Per-SCM active-stage cap | 1,800 s | Durable stage wall time; downtime excluded |
| Cohort active-stage cap | 7,200 s | Stop at the next safe stage/SCM boundary; one running SCM can finish or hit its per-SCM cap |
| RSS monitor | 512 MiB | Sampled child working-set kill-on-detection; transient overshoot is possible, not an OS hard limit |
| Per-ledger cap | 100 MiB | Pre-write JSONL check |
| Dedicated cohort-root cap | 100 MiB | Pre-write total of registry/WAL, ledgers, checkpoints and other files; 5 MiB reserved for failure records |
| Minimum free disk | 1 GiB | Checked before managed writes |

The total storage guard is a preflight and safe-stop mechanism, not a filesystem quota; external concurrent writers and filesystem/SQLite growth may overshoot between checks. Upon timeout, RSS detection, storage/time cap, system error or incomplete GT evaluation, preserve the failure and denominator; never substitute a new candidate. Same-input restart is allowed only with matching code manifest, settings, runtime fingerprint, commit/tree, RNG and input bindings. Shortfall remains shortfall.

## IMPLEMENTED / FIXTURE-VALIDATED / NOT RUN

The production-isolated fixed-fixture run exercised 14 preserved strict-Q topologies from all four templates across available strata at 6–10 nodes; six strata had no preserved accepted fixture and remain unavailable. Both delta signs, the shared 512-row test input, FN/FP/REV, Global/Task-Focused, Ridge/recommendation, analytic GT, composite validation, SQLite registry, whole-root storage monitor, JSONL ledger, and completed-ledger replay were exercised. This is software/resource qualification only: `independent_scm_n=0`, not a study cohort or policy-effectiveness result. Exact measurements and unavailable strata are recorded in `step4c2_resource_qualification_v2.json`; proposal/rejection timing is in `step4c2_proposal_cost_benchmark_v1.json`.

Implemented: deterministic proposal and SCM generation, strict-Q eligibility, registry/orchestrator, paired pipeline and analytic evaluator, finite complete-vector validation, hash-bound checkpoint/restart, process isolation, sampled RSS termination, per-ledger and total-root preflight caps, settings/runtime gate, and manifest verification. The runner includes the freeze-manifest and settings hashes in the immutable execution configuration. The production cohort entry point refuses a dirty checkout or a mismatched commit/tree.

Not run: any new study SCM, 64-development or 200-replication cohort, research Decision Regret analysis, Step 5, Step 6, TEP/CausalMan experiment. Resource measurements use small repeated fixture sets and are not population-level tail guarantees. Statistical superiority/equivalence remains prohibited under Option B. Numerical eligibility uses only the preregistered finite/sample-variance checks; no condition-number or effect threshold was introduced.

## SUPERSEDED PROPOSALS

Earlier P/B=4 selected-policy vs matched-random and Path-F1 confirmatory proposals in `RESEARCH_PROTOCOL.md`, `STEP4_PREREGISTRATION.md`, and `STEP4_STATISTICAL_ANALYSIS_PLAN.md` are historical and superseded by this frozen active contract. They remain as an audit trail and must not be read as current instructions.

## ARCHIVED PILOTS

Step 4A/4B feasibility matrices and fixed-fixture ledgers are topology/software evidence only. They are not independent SCMs, confirmation data, or policy-performance evidence.

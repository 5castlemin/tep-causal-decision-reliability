# Research S4-1 pilot scientific contract

Status: `LOCKED_BEFORE_PILOT`; classification: independent exploratory development pilot, not confirmation.

## Question and populations

Estimate whether the existing graph-repair/evaluation workflow is feasible on new independent draws from the frozen Research C linear-Gaussian SCM generator, and quantify opportunity, candidate-value heterogeneity, repair-policy behavior, and computation needed to plan confirmation. Report (G) a general cohort and (O) a structurally enriched diagnostic cohort separately. G uses the first 32 eligible SCM proposals under the existing outcome-blind indirect-task and Q-common proposal admission. O uses the first 32 proposals satisfying that same admission and having at least two initially DAG-feasible M4 repairs. O eligibility is assessed before coefficient, observation, learner, recommendation, or outcome generation. It is not representative of the general proposal population.

## Generator, task, learner and outcome

Use the repository's pinned Research C topology and SCM generation code, 6–10 nodes, strict indirect-only action/target task selected by the existing proposal code, signed linear SCM coefficients and independent Gaussian exogenous noise. Generate 512 observational rows per retained SCM. Retain the existing Ridge learner (`alpha=1.0`), five standardized action values `k ∈ {-1,-.5,0,.5,1}`, training-only target `mean(Y)+delta*SD(Y)` with `ddof=1`, and analytic ground-truth intervention response. Assign `delta ∈ {-1,+1}` by a deterministic hash bit of cohort and SCM ID, without outcome access. Evaluate `gamma=0`; this is the existing Research C task objective, not a new objective search. No noisy intervention rows are sampled.

The G0 generator is the existing deterministic Research C candidate corruption implementation, with `q=.15`, `r=.05`, conditional FN/REV/UNRES equal probability, fair FP orientation and DAG-invalid proposal rejection without redraw. `Config`: FP Rule A, fixed-opportunity normalization and unit atomic edit costs. Original Research C contracts and assets are not edited.

## Sample and seed lock

Target 32 retained SCMs per cohort; maximum 2,048 outcome-blind proposal/G0 screening attempts per cohort. No replacement after outcome generation. Any shortfall is reported. Master seeds are `6419173201` (G) and `6419173202` (O); proposal ID prefixes are `s4pilot-general` and `s4pilot-opportunity`; attempt index is 0 per uniquely namespaced proposal ID. The deterministic delta assignment and G0 sub-seed derive from SHA-256 under namespace `research-s4-pilot-v1`. This seed namespace is distinct from Research C, S3 analysis, Development/Reproduction, Research D and smoke runs. The pilot uses one SCM draw per retained topology; no matched variants are generated in this bounded pilot.

## Frozen development analyses

Before evaluator access, produce and hash-lock recommendations for S0, Frozen M4 and Full Greedy at B=0–4, all 63 nonempty T1–T6 equal-weight Greedy subsets at B=2, all initially feasible single M4 edits, and every feasible ordered M4 path of length at most two (including no edit and one edit). Evaluate all unique resulting graphs with the same training frame and action grid. The ex-post states are privileged outcome-aware diagnostics and are never policy inputs. Candidate/edit rows are clustered within SCM. The pilot reports paired SCM-level summaries and 2,000-replicate paired percentile bootstrap intervals with one common resample index array per cohort and frozen seed `6419173299`.

The pilot is not powered for confirmatory inference. No policy selection is declared confirmatory. Any policy choice for later confirmation must use development results only and be frozen in a separate protocol before confirmation data are generated.

## Resources, stopping and artifact boundaries

Single sequential process; 7,200-second wall-time ceiling; 4 GiB process-tree memory ceiling, checked at proposal and SCM boundaries using Windows process RSS; max 32 retained SCMs/cohort and 2,048 screening proposals/cohort. Stop on hash mismatch, pre-existing output, nonfinite data, invalid schema/DAG, recommendation-lock failure, resource-cap breach, or incomplete source binding. No silent rerun or replacement. Private unit-level inputs, recommendations and results stay under `C:\DAT_RESEARCH\research-s4\` and are not committed. Public artifacts are aggregate-only, with counts, hashes, code revision and limitations.

## Primary pilot summaries and interpretation

The pilot's primary feasibility estimands are (i) structural opportunity yield and (ii) within-SCM paired `Regret(S0)-Regret(M4,B=2)` on each cohort. All 63 T-subset results and ex-post comparisons are exploratory; pointwise intervals are descriptive. SCM is the independent unit; the O cohort has structural selection conditioning. No causal effect of error type/role is identified by this pilot. Research C and CausalAssembly results are not pooled. Research D replay remains blocked until private unit-level artifacts are available; no confirmation cohort is authorized by this contract.

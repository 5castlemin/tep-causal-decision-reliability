# Step 4 Frozen Protocol

**Protocol status:** FROZEN on the committed revision identified externally by PR/CI evidence and the production runner's required commit/tree arguments. The content manifest excludes itself; editing a manifested file requires a new version and a new freeze review.

This document consolidates the active Step 4 research and execution contract. Historical P/B=4, confirmatory-testing, and Uniform-noise proposals remain in earlier documents as superseded history and do not override this protocol.

## Research estimand and population

- Target population: P proposal distribution conditioned on strict Q-common structural eligibility. The selected Action→Target task has a directed path of length at least two and no direct Action→Target edge; all FN, FP, and REV types have same-type B=1 structural competition support.
- Task and budget: indirect-only, B=1, gamma=1.
- Paired methods: Task-Focused vs ID-ordered Global, given the same SCM, task, observations, error graph, action candidates, target and cost.
- Error types and within-SCM weights: FN, FP, REV at 1/3 each.
- Independent unit: SCM. The three error types are repeated measures.
- Direction assignment: after structural eligibility and atomic registry admission, delta alternates `+1,-1,+1,...` by admitted ordinal separately within each cohort. It is persisted before execution and shared across the SCM's types and paired methods.
- Targets: 64 development eligible admissions and 200 held-out replication eligible admissions. Proposal caps are 386 and 1,104. Admission targets are not completed-evaluation targets. An admitted failure remains in the denominator and is never replaced.
- SCM-level descriptive outcome: `D_i=(D_i,FN+D_i,FP+D_i,REV)/3`, where `D_i,type=Regret_Global−Regret_TaskFocused`.
- Inference: Option B. Report the arithmetic mean, full SCM distribution, type-specific results, failures and denominators. Do not claim confirmatory superiority or equivalence at 5%. Assumption-based intervals are references only.

## SCM and evaluation generation

Use a signed linear acyclic SCM. Assign coefficients by sorted directed edge ID; sample magnitude Uniform[0.25,0.8] and independent fair sign. Use independent centered Gaussian disturbances with node SD Uniform[0.8,1.2]. Generate one shared 512-row observational dataset per SCM. Topology, coefficients, disturbance, observations, relabeling, task, error injection and policy scheduling use distinct versioned RNG streams. Same DAG with independent parameter streams may represent distinct SCMs; exact RNG-key reuse is a replay, not another sample. Duplicate equation signatures cannot be admitted twice.

The analytic GT evaluator computes hard-do intervention means from separate truth equations. It uses the same candidate action grid and target/loss scale as the learner, but GT values never flow to eligibility, error recipes, policy ranking, fitting or recommendation. All three paired type outcomes are required for the SCM composite. Missing GT, nonfinite values or failed policy output are never imputed as zero. Valid `k=0` fallback behavior preserves the original policy failure and is recorded separately.

## Failure, stopping and shortfall

Expected structural rejections are recorded as proposals. Unexpected exceptions, malformed proposal objects, unknown rejection reasons and replay mismatches are fatal `GENERATOR_ERROR` states, not Q rejections, and stop at the same proposal on restart. Registry and ledger events retain their immutable cohort, proposal, SCM, RNG, settings, input and code-manifest bindings.

Normal candidate exhaustion, unused budget and DAG-rejected edits are valid outcomes. Generation, learner, recommendation, GT, numeric, timeout, memory, I/O, and storage failures remain explicit and policy-specific. A completed composite requires all FN/FP/REV paired results. Proposal caps, time caps or storage caps that prevent target attainment produce a reported shortfall; no new seed or replacement SCM is added.

## Operational environment and resource stop limits

Frozen environment is Windows fingerprint `Windows-10-10.0.26200-SP0`, CPython 3.11.15, NumPy 2.4.3, pandas 3.0.1, and NetworkX 3.6.1. The production entrypoint verifies these pins, the content manifest, a clean worktree and explicit expected Git commit/tree before creating a proposal.

- One spawned child per pipeline stage; 2-second unit timeout.
- 1,800 seconds cumulative active-stage time per SCM; downtime is excluded.
- 7,200 seconds cohort active-stage budget, enforced at safe boundaries. A running SCM remains bounded by its per-SCM cap.
- 512 MiB sampled child working-set monitor. It terminates on detection but permits transient overshoot; it is not a hard OS memory quota.
- 100 MiB per JSONL ledger and 100 MiB total under a dedicated cohort root, with 5 MiB reserved for failure records and 1 GiB minimum free disk. Pre-write accounting is not an OS filesystem quota and can overshoot due to external concurrent writes or SQLite/filesystem growth.
- The configured limits are safe-stop budgets supported by fixed-fixture qualification, not worst-case performance guarantees. A cap failure preserves the ledger and denominator and causes shortfall, not replacement.

Resource evidence is in `step4c2_resource_qualification_v2.json` and `step4c2_proposal_cost_benchmark_v1.json`. It uses preserved topology diagnostics and deterministic explicit-coefficient fixtures; `independent_scm_n=0`. It is not a policy-performance experiment or study sample.

## Freeze binding and future execution

`step4c2_final_freeze_manifest.json` hashes required source, settings, environment, active-contract, failure/statistical, validation and fixture-resource artifacts. UTF-8 text hashes normalize CRLF/CR to LF; binary artifacts use byte hashes. The manifest excludes itself. A run ledger binds the normalized content-manifest hash, settings hash, execution inputs, RNG, cohort/SCM IDs, and exact configuration. The operator must also provide the expected clean Git commit and tree at entry; these identities are kept outside the manifest to avoid self-reference. A changed code/settings file blocks resume.

Freeze makes the protocol ready for a separately authorized development cohort. It does not create development SCMs, held-out SCMs, a Step 5 result, a Step 6 replication, or evidence of manufacturing intervention effects. No such study data or results exist as of this freeze.

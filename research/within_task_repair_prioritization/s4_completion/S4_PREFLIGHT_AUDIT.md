# S4 pre-flight and S3 source audit

Status: `PREFLIGHT_VERIFIED_WITH_LIMITATIONS` (2026-11-27).

## Source and frozen-input checks

The active checkout is `research/s4-error-value-mechanisms` at `ce25e8dacca5be38aaeac8276dc343711fbbcd2a`. The branch is intentionally based on the corrected S3 line and is separate from `main`; no merge is performed here. The local Research C ledgers were opened read-only and their current SHA-256 values match `S3_COMPLETION_ANALYSIS_LOCK.json`:

| Input | SHA-256 | Status |
|---|---|---|
| Development cohort SQLite | `dd4264d5085adbabe9510bf99b564ec6c2b33e35d4eeb346a079cc4ccfb9b716` | verified |
| Development proposal SQLite | `1d00d1790788c342e15a81a0c405768e5e2a3e46ee75c57c0bbe34f8c0fcb584` | verified |
| Held-out cohort SQLite | `37b3c265ecb65b09a97eda91d29411844c3a3851c9fbff6cfa06445f919a3eba` | verified |
| Held-out proposal SQLite | `59f1abcf5661a5b3d0658d0db0f7e6afe601ebd09997035228df0716800538d6` | verified |

The prior completion lock and result manifest identify only the original 64 Development and 200 Held-out units, with zero new SCM/G0/observation/intervention rows. `run_s3_completion.py` implements T-gain/cost, M4-gain/cost, then canonical tie-break; its `sequence2` re-evaluates M4 candidates after the first edit, checks DAG feasibility, and returns exact only over the enumerated no-edit, one-edit, and ordered two-edit state space. This is not an unrestricted repair optimum. The prior ranking reports must be read with their explicit selected-best, tied-set containment, rank, and regret-gain definitions; tied-set containment is not actual selected-edit accuracy.

This audit is source-level plus hash verification. It does not rerun the full S3 cohort analysis, and does not promote the historical S3 result beyond post-hoc exploratory evidence.

## Pilot implementation decision

The new pilot lock uses the existing Research C topology, signed-linear SCM, observation, corruption, Ridge learner, policy and analytic intervention evaluator modules without editing them. A new General cohort follows the existing outcome-blind proposal admission; an Opportunity-rich diagnostic cohort is screened solely on the count of initially DAG-feasible M4 repairs. Outcome, coefficients, fitted learner, action, regret and policy performance are not used for cohort admission. Both cohorts are separately reported, and the latter is explicitly conditional on structural opportunity.

## Research D/S5 artifact availability

The approved local root `C:\DAT_RESEARCH\research-d` currently contains `final-reaudit-20261126.json` only. That summary records a successful earlier audit and hashes for five action response vectors, but the response-vector files, private recommendation artifact, run lock, final execution manifest and fixed training frame are not present under that root. No broader disk search, download, refit, sampling, or substitute data generation was performed. Therefore S5 historical replay and G0-level extension are `BLOCKED_UNAVAILABLE_PRIVATE_UNIT_ARTIFACTS`; prior audit history is reported as historical evidence, not a fresh read-only re-audit.

## Remaining pre-flight limitation

The CausalAssembly read-only feasibility status is similarly limited to the prior public closeout and the local summary above. This task does not reopen the evaluator-only artifact store or rerun Research D. No causalAssembly intervention data are generated.

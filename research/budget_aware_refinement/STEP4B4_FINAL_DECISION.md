# Step 4B-4 Final Decision Gate

Date: 2026-11-15. Contract decision; Step 4 remains IN_PROGRESS / NOT FROZEN. No new SCM, observations, effects, Decision Regret, confirmation SCM, or Step 5 run.

## Decision: Option B — suspend confirmatory superiority claims

The primary question and estimand remain fixed: Q-common, indirect-only, B=1, gamma=1, Task-Focused versus ID-ordered Global; type differences are equally weighted 1/3 into one SCM row `D_i=(D_FN+D_FP+D_REV)/3`, with SCM as the independent unit.

The current protocol does not imply a finite range for `D_i`. Coefficient magnitudes and disturbance SD are proposed as bounded, but the disturbance support/distribution is not fully fixed; the action grid depends on finite-sample means and standard deviations; and no positive lower bound is imposed on the target's sample SD. Step 3's standardized squared-response loss divides by that SD squared, so the loss contrast can grow without a contractually justified bound as the denominator approaches zero. No variance bound or valid bounded-mean guarantee follows. A finite-variance/CLT or approximate-normal assumption could motivate a paired-t reference interval, but that assumption is not established by topology fixtures or the current generator draft. The n=200 zero-heavy skew stress case has Type I error 13.4% and coverage about 86%; bootstrap intervals also fail some skew/tail cases. This demonstrates a failure mode, not the future Q-common distribution.

We therefore do not claim 5% confirmatory superiority, equivalence, or a guaranteed 0.10 improvement. Preserve the arithmetic SCM mean and report the full SCM-level distribution, denominator, missingness/failures, and type-specific summaries. A paired-t interval may be shown only as an assumption-dependent reference, alongside sensitivity summaries, never as calibrated confirmatory evidence. Statistical significance, effect magnitude, the prespecified 0.10 standardized-loss difference, and industrial utility are separate. The 0.10 value is not a 10% cost saving.

No robust test search will continue under this contract. A later change would require a prospectively justified finite range/variance or a clearly relabeled estimand, before accessing confirmation outcomes.

## Cohorts, target and finite attempt limits

- Keep 64 eligible development SCMs and 200 eligible independent confirmation SCMs as fixed operational targets for descriptive estimation, not power-backed sample sizes. Development validates code and reports nuisance dispersion; it cannot increase or decrease confirmation N. No confirmation-driven sample-size change.
- The target is the P proposal distribution conditioned on outcome-blind Q-common eligibility. Each topology candidate selects one of the 20 template×node-count strata with probability 1/20, and every eligible candidate is accepted. No post-hoc quotas or reweighting.
- In the fixed audit, Q-common counts were Chain 107, Fork 69, Observed Common Cause 164, Multiple Directed Paths 297 of 637 (46.6%). These are observed pilot proportions, not guaranteed future weights. Report template-specific SCM means descriptively; do not replace the primary conditional-Q mixture with arbitrary equal-template weights.
- Adopt finite candidate caps of 362 for development and 1,036 for confirmation as operational planning ceilings from the existing v2 stratified lower-yield calculation. They are not yield guarantees. Retain every structural rejection and reason. Stop at target or cap. At cap shortfall, publish denominator/yield and descriptive enrolled-row summaries only; no confirmatory inference, replacement by new seeds, or selective continuation.

## Failures and analysis stops

- Structural ineligibility stays in proposal-attempt denominators and is not an SCM outcome missingness.
- Structural/task construction gets no outcome-directed retry. One replay is permitted only for explicit transient I/O/system failure with identical input and RNG key; retain both attempt records and deduplicate the run key.
- Ridge/recommendation failure may use the common-grid `k=0` fallback only when training and truth inputs are valid. Keep original failure status and fallback outcome separate; report policy-specific rates.
- Missing truth/GT evaluation, nonfinite outcomes, unresolved timeout/resource failure, or any missing FN/FP/REV cell leaves `D_i` missing. Never impute zero, change the type denominator, or substitute a complete-case mean as the primary target. Any missing confirmation SCM vector suspends inferential claims. Descriptive summaries must state the observed-row denominator and cannot be generalized as the full target mean without assumptions.
- Normal states such as no candidate, unused budget, candidate exhaustion and cycle rejection remain valid execution outcomes.

## Mock runner and resource controls

`step4b4_mock_runner.py` implements fsynced event checkpoints, run/event idempotence, conflicting-replay rejection, partial-tail recovery, stage-boundary wall/unit checks, disk-cap checks and resume. The integration fixture runs the existing graph policy and Ridge/candidate recommendation path on deterministic dummy input and a truth-evaluator test double that explicitly returns no effect or regret. It does not implement the future SCM/evaluation runner.

The 30-minute total, 2-second unit, 512 MiB RSS and 100 MiB ledger limits are mock operational guardrails only. The JSONL disk cap is enforced before writes with room reserved for a stop event. Wall time and unit time are checked at stage boundaries: overrunning work cannot be preempted in this in-process runner, but is recorded and not treated as successful. RSS includes native allocations where the OS query succeeds and is monitored at boundaries only; it is not a hard memory kill. Step 4C must implement/test process-isolated preemption if hard timeout/RSS containment is required by the final runtime.

Verified mock cases: actual child-process forced exit after a checkpoint, deterministic resume without duplicating the completed graph stage, torn final JSONL line repair, duplicate/conflicting run IDs, single-policy failure, GT failure, incomplete three-type vector, unit/wall limit records, and disk-cap stop with preserved ledger. These are engineering fixtures, not study outcomes.

Reproducibility manifest: `step4b4_final_gate_manifest.json`; settings SHA-256 `81ec984a921f8c783e4e84d26df27d1180f4848b3b5e49df626ac1c9e19044c7`. It records hashes for the runner, integration script and fixed JSONL mock ledger.

## Protocol history and status

This decision prospectively supersedes the old P/B4 policy-vs-Random confirmatory proposal and the earlier interpretation of N=64/200 as potentially power-supported. Historical documents/results are not rewritten; the current decision governs future work. Step 4B-4 closes its design decision by selecting Option B, but the full Step 4 and preregistration remain IN_PROGRESS / NOT FROZEN. Step 4C must reconcile every current contract, implement the production runner/OS limits, pin configuration/code hashes and perform final freeze review before any study execution.

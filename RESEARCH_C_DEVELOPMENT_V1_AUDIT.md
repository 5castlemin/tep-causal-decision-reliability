# Research C Development v1 — Read-only audit

**Audit status:** `METADATA_ONLY_CONFIRMED` for the stale G0 labels; Development results are preserved as exploratory evidence, not held-out confirmation.

**Scope:** Integrity and provenance review of the already completed Development run, SCM-level recalculation of P1, descriptive M4 comparisons, and a proposed analysis lock for a future Held-out cohort. No cohort was rerun, no new SCM was generated, and no Held-out analysis was run.

## 1. Inputs and preservation

Run ID: `development-20261123-seed-2026112301-v1`
Approved config: `C:\DAT_RESEARCH\research-c\approvals\development-v1-approved.json`
Config canonical JSON SHA-256: `96267e6f6004bc4255ae3765c8b4a939f3511690b1d4c34d2fd8195a8294b3f4`
Config file-byte SHA-256: `5a22f5601705bae7c8d1675ef37807964bbf6c7382779fb0216e5b5169159819`
Manifest: `C:\DAT_RESEARCH\research-c\approvals\development-v1-manifest.json`
Manifest canonical JSON SHA-256: `d992806153622173644edf470e3b79f41f29bc547fc588922f6e96bd9f3273ac`
Manifest file-byte SHA-256: `97ba1d89e75751d932b81e0a2ae1e07c797cdee93eaa1eeed7d7b5d491640c61`

| Immutable raw input | Bytes | SHA-256 | Integrity |
|---|---:|---|---|
| `C:\DAT_RESEARCH\research-c\development\development-20261123-seed-2026112301-v1\research_c_cohort.sqlite` | 21,344,256 | `dd4264d5085adbabe9510bf99b564ec6c2b33e35d4eeb346a079cc4ccfb9b716` | SQLite integrity OK; no foreign-key issues; 64/64 result row checksums valid |
| `C:\DAT_RESEARCH\research-c\development\development-20261123-seed-2026112301-v1\research_c_proposal_stage.sqlite` | 200,704 | `1d00d1790788c342e15a81a0c405768e5e2a3e46ee75c57c0bbe34f8c0fcb584` | SQLite integrity OK; proposal checksums valid |

The cohort was bound to source commit `01473797e8edd9e01935a7bee57107b63a4d53ca`, tree `3a1577c806ef0e6eff02fc1ffaa020f490ef6be9`, and the Manifest code hash map. The recorded runtime is CPython 3.11.15 on Windows AMD64, with NumPy 2.4.3 and pandas 3.0.1 among the 13 locked packages. The approved Development master seed is `2026112301`.

The Manifest G0 helper hash is `b09a23176cb949c4f4755dbf3ac9b799621edb9f62f976be2f926aea3b0e9c1c`; its proposal pipeline, runner, cohort runner, policy engine, and E2E hashes also match the stored run map.

The two SQLite databases were opened with `mode=ro` and `PRAGMA query_only=ON`. No raw database, approval config, or Manifest was rewritten. A separate audit snapshot was written to `C:\DAT_RESEARCH\research-c\audits\development-v1-audit-v7.json`; its embedded canonical audit payload SHA-256 is `72a5a8c2ed6deb9f902324ef43631746b644194b9f95b92a20c18a5951b8bc31`. It contains per-SCM G0 payload, E2E input, and result hashes.

Run accounting: 64 proposal attempts, 64 strict-task eligible/admitted SCMs, 18 Q-common SCMs, 64 completed SCMs, 64 complete P1 pairs, and 5,440 successful policy-budget evaluations (17 × 5 × 64). There were no evaluation failures; 7 initial G0 graphs had no errors. The proposal cap was not reached. Proposal/checkpoint and cohort ledger checksums and SQLite integrity checks passed.

## 2. G0 provenance discrepancy

### Finding

**`METADATA_ONLY_CONFIRMED`.** Both legacy strings occur in all 64 nested G0 metadata records:

- `contract_status=PROPOSED_NOT_APPROVED`
- `test_or_cohort_use=not_authorized`

The strings are stale labels returned by the shared G0 helper. They are not used as execution settings, admission criteria, policy inputs, or evaluation inputs. The actual run used the approved Research Mode gate and Research Generated Factory. The labels do not by themselves invalidate the Development run.

### Code and run evidence

- [g0_candidate.py](C:/Users/ehfal/Documents/Codex/2026-11-15/dat-solo-research-workflow-main-0/work/repo/research/original_objective/g0_candidate.py:14) defines the q/r constants as 0.15 and 0.05; `corrupt_graph_candidate` defaults to them. The return record at [line 129](C:/Users/ehfal/Documents/Codex/2026-11-15/dat-solo-research-workflow-main-0/work/repo/research/original_objective/g0_candidate.py:129) hard-codes the two stale labels, while also recording configured rates, realized events, retry count, and graph hash.
- [proposal_pipeline.py](C:/Users/ehfal/Documents/Codex/2026-11-15/dat-solo-research-workflow-main-0/work/repo/research/original_objective/proposal_pipeline.py:112) creates the Research Generated Factory. It generates SCM parameters and the common observational sample, then calls the G0 helper with the proposal truth graph, task, and dedicated G0 seed. It does not pass SCM coefficients, observations, intervention losses, or regret to the helper. Its returned G0 record is stored under `fixture_metadata.g0_generation`.
- [runner.py](C:/Users/ehfal/Documents/Codex/2026-11-15/dat-solo-research-workflow-main-0/work/repo/research/original_objective/runner.py:135) checks the approved contract values, including q/r, error mixture, retry rule, policies, costs, and evaluation contract. [Research Mode](C:/Users/ehfal/Documents/Codex/2026-11-15/dat-solo-research-workflow-main-0/work/repo/research/original_objective/runner.py:348) checks `USER_APPROVED`, preregistration state, config/Manifest, code tree, runtime, and resource binding before starting proposals. It does not inspect or consume the helper’s descriptive metadata labels.
- [proposal_pipeline.py](C:/Users/ehfal/Documents/Codex/2026-11-15/dat-solo-research-workflow-main-0/work/repo/research/original_objective/proposal_pipeline.py:326) sets `apply_g0_generator=False` because the generated factory has already created G0. Thus the factory’s recorded G0—not a second fixture generator call—was used by the policy path.
- The read-only audit checked all 64 G0 records for the exact configured q/r and 1/3 FN/REV/UNRES mix, zero retries, and the expected generation classification; all matched. It also checked 64/64 result checksums, per-policy shared-input binding for P1, and proposal/config/source/Manifest binding.

The approval Gate did not reject the stale labels because they are not approval fields: authorization is checked against the approved config and Manifest before the proposal pipeline starts. That check passed for this run. The Manifest pins the code used at execution, including the helper that emitted the stale labels.

### Provenance correction record

See [RESEARCH_C_DEVELOPMENT_V1_PROVENANCE_CORRECTION.md](C:/Users/ehfal/Documents/Codex/2026-11-15/dat-solo-research-workflow-main-0/work/repo/RESEARCH_C_DEVELOPMENT_V1_PROVENANCE_CORRECTION.md). It records the original database hashes and directs later analysis to treat the labels as descriptive helper metadata, not the authorization status. Raw G0 records remain unchanged.

## 3. Independent P1 recalculation

The audit reads the SCM-level result payloads and recomputes `delta_i = Regret_i(S0,B=2) - Regret_i(FullGreedy,B=2)`; the persisted P1 deltas agree for all 64 SCMs.

| Statistic | Recomputed Development result |
|---|---:|
| Complete pairs | 64 SCMs |
| Mean S0 Regret | 0.1008517293 |
| Mean Full Greedy Regret | 0.0256408438 |
| Mean paired delta | **+0.0752108855** |
| Median delta | 0 |
| Sample SD of SCM deltas | 0.1720756403 |
| Improved / worsened / tied | **14 / 1 / 49** |
| S0 and Full Greedy choose same action | 49/64 |
| Full Greedy mean edits and cost | 1.453125 / 1.453125 |
| Full Greedy no-op | 7/64 |

The two-sided 95% paired-t interval is **[0.0322276695, 0.1181941016]**, with mean as above, `n=64`, `df=63`, standard error `0.0215094550`, and `t(0.975,63)=1.9983405425`. The direction is defined so positive values favor Full Greedy over S0 in this Development sample. The reported +0.07521 and 14/1/49 are reproduced.

The explicit cross-tab confirms all 49 paired-Regret ties are same-action pairs; no tied pair changes action. Of these, 7 are the same SCMs as the no-error G0 cases and Full Greedy no-ops; the other 42 have different final graphs but the same recommended action. Thus the no-error count and no-op count are not merely numerically equal: their intersection is all 7, with no errors-with-no-op or no-error-with-edits cases. These ties are retained, not dropped.

The interval is a Development summary, not independent confirmation. The mass at zero (49/64) and observed skew make the paired-t interval’s distributional approximation worth checking in Held-out; it is not evidence of a universal process effect. The approved 10,000-resample SCM bootstrap was **not run** because its analysis seed has not yet been fixed.

## 4. M4 Development exploration

M4’s mean B=2 Regret was **0.0029277742**. In this Development sample it had lower Regret than S0 in 17 SCMs, equal in 46, and higher in 1; mean `Regret(S0)-Regret(M4)` was `+0.0979239552`. M4 compared with Full Greedy had lower Regret in 3 SCMs and a tie in 61 (mean `Regret(FullGreedy)-Regret(M4)=+0.0227130696`). Compared with Canonical Oracle, M4 was lower in 9 and tied in 55 (mean difference `+0.0531192095`).

M4 made 42 edits in total across 31 SCMs (33/64 no-ops; mean 0.65625 edits and cost per SCM). Those edits were FN 12, FP 6, REV 11, UNRES 13; all were in the task zone, as M4 is defined to score that zone. Its final graph matched Full Greedy in 19/64 SCMs, S0 in 33/64, Canonical Oracle in 18/64, M1+M4 in 44/64, M2+M4 in 33/64, and M3+M4 in 43/64. M4 and M1+M4 produced identical actions and Regrets for all 64; this demonstrates policy result overlap, not independent evidence for either policy.

In three SCMs Full Greedy had higher Regret than M4. For example, `dev-scm-development-proposal-000014-a0013`: Full Greedy spent both B=2 edits resolving off-task UNRES edges, while M4 added a task-zone FN edge; observed Regret was 0.5903829921 for Full Greedy and 0 for M4. This is consistent with a task-location explanation in this case, but the result remains oracle-assisted and exploratory; the logs do not justify generalizing that pattern beyond this generated sample.

The comparisons are descriptive and post-development exploratory. The apparent M4 advantage is not a deployment-ready policy result: its candidate classification and task zone use the true DAG, so the observed result is conditional on oracle-assisted structural information in this synthetic setting. It does not show that a real factory can identify the same edges without a known graph.

## 5. Structural and decision outcomes

- For P1, Full Greedy reduced common structural penalty `P_all` relative to S0 in 43 SCMs, yet in 42 of those it did not change the recommended action and Regret tied. One further SCM had lower `P_all` and a changed action but worse Regret.
- Example of structural improvement without decision change: `dev-scm-development-proposal-000001-a0000` moved `P_all` from 2 to 0 under Full Greedy, with two edits (task-zone FP deletion, then off-task UNRES resolution), but the action stayed `1.0467398643` and both Regrets were zero.
- Example of fewer structural errors but worse decision: `dev-scm-development-proposal-000022-a0021` moved `P_all` from 3 to 1, but S0 Regret was 0 and Full Greedy Regret was `0.0235423962`. Its two edits oriented a task-zone REV and deleted a task-zone FP; the changed action had higher GT loss than S0’s choice.
- An equal `P_all` score does not determine Regret across policies. For example, in `dev-scm-development-proposal-000009-a0008`, M2 and M4 both ended with `P_all=1`, while their Regrets were `0.3942870703` and 0. This is a single Development case, not a general law.
- There were no P1 SCMs where `P_all` was unchanged from S0 while Regret changed. This does not imply P_all is a surrogate for Regret: the cases above show the converse failure modes.

These cases support keeping graph change, action change, and regret change as distinct outcomes. Individual SCMs illustrate mechanisms; they do not establish population-wide causal rules.

## 6. Held-out analysis lock proposal

Held-out remains **unrun and sealed**. Before its results are opened, fix and hash the analysis code and bundle, then apply these rules:

1. Keep P1 exactly as approved: B=2, Full Greedy versus S0, `delta=Regret(S0)-Regret(FullGreedy)`, SCM-level complete-pair mean, two-sided 95% paired-t interval. Report the actual complete-pair denominator and all failures separately; never fill missing pairs with zero or selectively replace SCMs.
2. Keep all 15 metric subsets and S0 in a complete descriptive results table at the approved budgets. Do not promote the Development-selected M4 policy to Primary.
3. If M4 is carried forward, label it as a candidate chosen after inspecting Development. Freeze one secondary Held-out comparison, **M4 versus S0 at B=2**, and report its paired mean/interval and improve/worsen/tie counts regardless of direction. Comparisons of M4 to other policies remain exploratory and should be presented as a full, prelisted family rather than selecting favorable pairs.
4. Retain B=1 secondary and B=3/4 saturation diagnostics. Preserve structural metrics, edit opportunity, action changes, and Regret as separate outputs.
5. Keep complete-pair analysis separate from admitted-cohort failure rates. Discuss the risk that failures depend on SCM or policy and hence complete-case selection.
6. Do not use `s_max/h` or held-out observations to increase sample size, change Primary, or change policy. Held-out target/cap remain 200 admitted SCMs/1,104 proposals under the approved contract.
7. Fix the analysis source commit/hash, runtime lock, and the 10,000-draw paired SCM bootstrap method before unsealing. Bootstrap resampling unit is SCM, preserving each SCM’s paired policy outcomes. No bootstrap was run in this audit.

**Bootstrap seed candidate for user approval:** `2026112302`, isolated under a named analysis-only namespace and distinct from all cohort RNG streams. It is not fixed or used yet. The paired-t interval remains the approved primary uncertainty summary; the bootstrap is a sensitivity summary.

## 7. Reproduction and audit artifact

Read-only command used:

```powershell
python scripts\audit_research_c_development_v1.py `
  --run-dir C:\DAT_RESEARCH\research-c\development\development-20261123-seed-2026112301-v1 `
  --approved-config C:\DAT_RESEARCH\research-c\approvals\development-v1-approved.json `
  --manifest C:\DAT_RESEARCH\research-c\approvals\development-v1-manifest.json `
  --output C:\DAT_RESEARCH\research-c\audits\development-v1-audit-v7.json
```

Result: exit code 0, audit `PASS`, no integrity errors. Audit JSON file-byte SHA-256: `a3285992c36aa046666a008e98c8016cf9e2715423cc06707c58f86c51872ee6`; its embedded canonical payload hash is above. The analysis script SHA-256 is `84e55a5896ec81789d212c35c97bfff68261afe8d1f40d315169c1a08b245506`. The output location is separate from the immutable Development directory. No bootstrap, model fit, proposal generation, or policy rerun was performed.

# Research F-Lite final audit

## Scope and evidence

This closeout reads the saved F-Lite recommendation/evaluator files and query-score replay plus the original C cohort/proposal SQLite payloads in read-only mode. It did not invoke `restore_cohort()`: that helper regenerates SCM parameters and observational arrays from seeds, which is outside this audit authorization. The four C database hashes and five private F artifact hashes matched their recorded values before analysis; C database hashes were unchanged afterward. The saved F outputs contain 12,480 Development and 39,000 Held-out recommendation/evaluator rows with complete unique keys. The original per-unit F files remain outside Git.

Reproducible command: `python research/decision_oriented_verification/final_audit.py`. Public aggregate output: `outputs/final_audit_aggregate.json`; the corrected Random action definition is also in `outputs/random_action_change_audit.csv`.

The pre-closeout `research_f_integrity_manifest.json` is retained as the original F-Lite release snapshot. The new `outputs/final_audit_manifest.json` binds this read-only audit's source revision, source database/private artifact hashes, and public aggregate hashes; the repository commit binds the accompanying report and synthesis edits.

## Random action-change definitions

The historical aggregate's `action_change_rate` for Random is the proportion of SCMs whose action changed at least once across 32 seeded trajectories. This is not comparable to a deterministic policy's per-SCM indicator. The new audit reports both quantities:

| Cohort | Budget | Mean within-SCM share of 32 repeats changed | SCMs changed at least once |
|---|---:|---:|---:|
| Development | 4 | 5.08% | 28.13% |
| Held-out | 4 | 4.09% | 27.00% |

The stored trajectories and regret values are unchanged. Do not cite 27% as the mean Random action-change rate.

## Shared-index paired bootstrap

At B=4, SCM-level Random regret was averaged over its 32 repeats. For every comparator against decision-weighted, one matrix of 10,000 SCM bootstrap indices was reused across all comparisons within cohort. Intervals are pointwise 95% percentile intervals, not simultaneous intervals. Seed derivation is recorded in the JSON. Held-out comparator-minus-proposed contrasts were: Random `+0.064942` `[0.045611, 0.086164]`; Fit-based `−0.012511` `[−0.023466, −0.004040]`; Suspicion-only `−0.010220` `[−0.020108, −0.002814]`; Impact-only `+0.000988` `[0, 0.002881]`. Point estimates and better/worse/tie counts reproduce the saved rows. The common-index interval differs slightly from the historical intervals because the historical code consumed the RNG sequentially by comparator; the old results are retained, not overwritten.

## Query score and error-discovery diagnostics

The saved 4,224 query-score replay decisions were read and matched to stored answers; 113,984 candidate score rows were present (28,528 Development; 85,456 Held-out). At B=4, query counts are four per SCM for these policies. Held-out true errors discovered were 383/800 Fit-based queries (47.88%), 379/800 Suspicion-only (47.38%), 85/800 Impact-only (10.63%), and 90/800 Decision-weighted (11.25%). These are yield among queried pairs in these fixed cohorts, not error-recall estimates over an independent population.

Across candidate-pair snapshots at each saved decision point, a true current relation error had exactly zero impact score in 1,464/1,589 Decision-weighted snapshots (92.13%) and exactly zero suspicion in 12/1,589 (0.76%); fit gain was non-positive in 125/1,589. Snapshots repeat pairs across policies and steps and are not independent observations. This supports the limited interpretation that one-edge predicted decision impact is often zero for a structural discrepancy; it does not show that impact is generally useless. The impact-only and decision-weighted policies chose the same final action in 198/200 Held-out SCMs, but had the same full query sequence in 168/200.

For a concrete counterexample chosen as the largest held-out Fit-based advantage over Decision-weighted at B=4, `rep-scm-confirmation-proposal-000111-a0110` had Fit regret 0 and Decision-weighted regret 0.649627. This is a selected descriptive example, not an independent test. The broader table shows Fit was lower in 10/200 SCMs, the proposed policy was lower in 0, and 190 tied. The error-discovery yield comparison gives a plausible policy-level description (48% vs 11%), but this aggregate association is not a causal mediation analysis.

All candidate scores were exactly zero at 1,211/3,200 Held-out decision snapshots (397/1,024 Development); the implementation then uses canonical pair order. A further 29 Held-out selected scores were zero while not every candidate score was exactly zero, reflecting numerical/tie details. Fit-based's higher discovery yield and lower regret coexist in these cohorts; these data do not support a claim that error discovery and regret diverge in general. A multi-edge joint effect being missed is a plausible limitation of local scoring, not a separately identified causal mechanism here.

The deterministic scoring function computes local BIC, suspicion, impact, and fit gain for each candidate regardless of which single component a policy selects. No per-policy runtime or candidate evaluation count was saved. Therefore comparative compute cost is unmeasured; query count is not computational runtime.

## Pending answers and policy sequence

Stored answers were replayed from each original G0 and compared with saved final relations/pending counts. There were zero replay mismatches. At B=4, among the four deterministic query policies there were 2 pending policy-SCM rows in Development and 4 in Held-out (the same SCM can appear for two policies); none of these pending directions was individually DAG-feasible against its final graph. This audit found no leftover pending relation that the single final graph test would admit. It does not change the policy or retrospectively rerun it.

## Query and edit budget are different resources

Held-out B=4 averages: Fit-based made 4 queries, 1.905 edits, and mean regret `.003770`; Suspicion-only 4 queries, 1.885 edits, `.006061`; Impact-only 4 queries, `.425` edits, `.017270`; Decision-weighted 4 queries, `.450` edits, `.016281`; Random 4 queries, `.305` edits, `.081223`. Query budget counts expert responses; edit count counts accepted graph changes. Oracle-assisted M4 is excluded from this query-cost comparison because it does not spend the same query resource. The graph-free diagnostic has no meaningful residual structural-error quantity: the historical CSV's `9.52` is retained as a raw diagnostic but should be `n/a` in repair-policy comparisons.

Fit-based B=3 and B=4 had the same selected action in 200/200 Held-out SCMs, while mean edits rose from 1.705 to 1.905 and mean regret stayed `.003770` at the reported precision. In Development, actions matched in 63/64. The aggregate plateau therefore hides unit-level change in Development and additional edits without action changes in Held-out.

## Clarifications and limitations

The C Development table's M4/Full Greedy action agreement of 46/64 is a cohort-level action comparison. The mechanism report's “46 off-task selections, 3 ties” is a different statistic: Held-out B=2 greedy steps at which an off-task candidate was selected while a task candidate was available, with 3 score ties resolved by metric order. They are not contradictory counts.

The proposed weighted policy was better than Random but worse than Fit-based and Suspicion-only on Held-out, and nearly identical to Impact-only. At accuracy .8, the previously reported Impact-only-minus-proposed interval `[0.001296,0.010694]` is retained; no claim that the combined score never helps is warranted. Expert-noise results are hypothetical categorical-response corruption, not a measured expert accuracy study. The interface uses an allow-list in one Python process, not an OS sandbox; the simulated expert still has access to reference structure. This is not a fully oracle-free verification study.

## Gate

F-Lite remains `RESEARCH_F_LITE_COMPLETED_WITH_LIMITATIONS`. Its proposal is not shown superior to simpler policies. The closeout adds corrected Random interpretation, common-index pointwise intervals, pending-state audit, and evidence-bound failure diagnostics without changing the historical evaluation.

## Validation environment

The focused F-Lite suite passed 19/19 tests. Full local Windows discovery ran 429 tests: 427 passed, one failed, and one errored. The failure is the existing frozen raw-data hash check on a CRLF checkout; the error is the frozen runtime dependency fingerprint (`numpy 2.4.6`, `pandas 3.0.3`, `networkx 3.6.1`). No frozen file or check was changed. `graphs/final/verify_and_load.py` reported 31 raw-byte mismatches, while all 39 manifest files match after LF normalization; the checkout has no Git changes in those paths. `src/verify_recovery.py` could not run because the private `data/local/datasetTE.csv` is absent. These local limitations are separate from PR Actions; the updated PR head CI remains the required integration check.

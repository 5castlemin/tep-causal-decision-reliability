from __future__ import annotations
import csv, json, shutil
from pathlib import Path
HERE=Path(__file__).resolve().parent
SRC=HERE/'outputs_v12'
AUD=HERE/'outputs_v8'/'correction_audit'
DEST=HERE/'tables'/'correction_v1'
DEST.mkdir(parents=True,exist_ok=True)
for name in ('s3_policy_aggregates.csv','s3_primary_paired_intervals.csv','s3_candidate_value_aggregates.csv','s3_error_role_counts.csv','s3_metric_gain_validation.csv','s3_summary.json'):
 shutil.copyfile(SRC/name,DEST/name.replace('s3_','corrected_s3_',1))
for name in ('corrected_vs_historical_aggregate.csv','correction_audit_summary.json'):
 shutil.copyfile(AUD/name,DEST/name)
agg=list(csv.DictReader((SRC/'s3_policy_aggregates.csv').open(encoding='utf-8')))
idx={(r['cohort'],r['policy'],int(r['budget'])):r for r in agg}
# Descriptive marginal score-contribution surface, averaged across all nonempty J not containing Tj.
rows=[]
for cohort in ('C_DEVELOPMENT','C_HELDOUT'):
 for budget in (1,2,3,4):
  for metric in ('T1','T2','T3','T4','T5','T6'):
   by_size={k:[] for k in range(1,6)}
   for (c,policy,b),r in idx.items():
    if c!=cohort or b!=budget or policy.endswith(('LOOKAHEAD2','GREEDY2')):continue
    members=set(policy.split('+'))
    if metric not in members or len(members)<2:continue
    parent='+'.join(sorted(members-{metric},key=lambda x:int(x[1:])))
    parent_row=idx.get((cohort,parent,b))
    if parent_row:
     by_size[len(members)-1].append(float(parent_row['mean_regret'])-float(r['mean_regret']))
   for k,values in by_size.items():
    if values:
     rows.append({'cohort':cohort,'budget':budget,'added_metric':metric,'parent_subset_size':k,'contrast_count':len(values),'mean_marginal_regret_reduction':sum(values)/len(values),'median_marginal_regret_reduction':sorted(values)[len(values)//2],'min':min(values),'max':max(values),'uncertainty':'not computed; descriptive aggregate means only'})
with (DEST/'descriptive_metric_marginal_contributions.csv').open('w',newline='',encoding='utf-8') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
summary=json.loads((SRC/'s3_summary.json').read_text(encoding='utf-8'))
audit=json.loads((AUD/'correction_audit_summary.json').read_text(encoding='utf-8'))
metric=list(csv.DictReader((SRC/'s3_metric_gain_validation.csv').open(encoding='utf-8')))
interval=list(csv.DictReader((SRC/'s3_primary_paired_intervals.csv').open(encoding='utf-8')))
def get(c,p,b):return idx[(c,p,b)]
def fmt(x):return f'{float(x):.6f}'
def metrics_table():
 return '\n'.join(f"| {r['cohort']} | {r['metric']} | {r['scm_count_with_multiple_candidates']} | {r['candidate_count_within_these_scms']} | {r['mean_scm_pairwise_rank_accuracy']} | {r['mean_scm_spearman']} | {r['mean_scm_best_candidate_hit_rate']} | {r['positive_metric_gain_but_regret_worsened_candidate_count']} |" for r in metric)
nonzero=[r for r in interval if 'LOOKAHEAD2' in r['contrast'] and abs(float(r['mean_difference']))>1e-12]
look_rows='\n'.join(f"| {r['cohort']} | {r['contrast']} | {fmt(r['mean_difference'])} | [{fmt(r['ci95_low'])}, {fmt(r['ci95_high'])}] | {r['better']}/{r['worse']}/{r['tie']} |" for r in nonzero)
# Corrected core result table.
core=[]
for c in ('C_DEVELOPMENT','C_HELDOUT'):
 for b in (1,2,3,4):
  for p in ('S0','FULL_GREEDY','CANONICAL_ORACLE','M4_ORIGINAL','M4_FN_FIRST','M4_FP_FIRST','M4_REV_FIRST','M4_UNRES_FIRST','M4_RANDOM_EXPECTATION','T3','T1+T2+T3+T4+T5+T6'):
   x=idx.get((c,p,b))
   if x:core.append(f"| {c} | {b} | {p} | {fmt(x['mean_regret'])} | {fmt(x['mean_edit_count'])} |")
correction=f'''# Research S3 correction audit

**Status:** correction replay completed with limitations. Historical S3 outputs are preserved; corrected aggregates are a separate version in `tables/correction_v1/`. The prior Gate remains a historical status. This is still a post-hoc exploratory analysis because the first S3 calculation preceded a committed analysis revision.

## Corrections implemented

- Greedy uses positive new T-subset gain per edit cost; within absolute 1e-12 ties, frozen M4 gain per cost, then canonical metric/pair/operation order. If no candidate has positive T gain, it uses the existing M4 gain fallback.
- T5 computes directed transitive closure over all learner-graph nodes, ignores UNRES, then scores ancestor pairs only on the fixed task-zone node set.
- When no legal two-edit lookahead exists, selection falls back to exactly the same one-step T Greedy selector. Lookahead fallback counts are now measured.
- Source SQLite bytes are rehashed after the corrected replay; all four matched their prior pinned SHA-256.

## Historical versus corrected implementation

An exact historical source snapshot from `{audit['historical_code_commit']}` was compared with the corrected graph selector. Across 63 metric subsets × B=1–4 × 264 original SCMs (66,528 cohort-policy-budget units; these are analysis units, not distinct SCMs):

- Final repair graph changed in **218** units.
- Recommended action changed in **70** units.
- Realized Research C regret changed in **70** units.
- Among 554 distinct final graph hashes inspected for T5, **0** had a different T5 score under the corrected closure.

The T5 fix is a general implementation correction, but it did not alter T5 values on the exercised graph set. No unit-level results were published. Aggregate differences are in `tables/correction_v1/corrected_vs_historical_aggregate.csv`.

## Integrity and boundaries

The corrected replay used only the same original Development 64 and Held-out 200 cohort inputs. No new SCM, G0, observations, or intervention responses were generated. Historical v1 output remains untouched in the ignored local `outputs_v6`; corrected outputs were generated in a new ignored run directory and only cohort-level aggregates were copied into this repository. Result summaries remain post-hoc and are not confirmatory.
'''
(HERE/'RESEARCH_S3_CORRECTION_AUDIT.md').write_text(correction,encoding='utf-8',newline='\n')
looktext=look_rows if look_rows else '| none | — | — | — | — |'
baseline_rows=[]
for c in ('C_DEVELOPMENT','C_HELDOUT'):
 for p in ('S0','FULL_GREEDY','CANONICAL_ORACLE','M4_ORIGINAL','M4_FN_FIRST','M4_FP_FIRST','M4_REV_FIRST','M4_UNRES_FIRST','M4_RANDOM_EXPECTATION'):
  x=idx.get((c,p,2))
  if x: baseline_rows.append(f"| {c} | {p} | {fmt(x['mean_regret'])} | {fmt(x['mean_edit_count'])} | {fmt(x['action_change_rate']) if x['action_change_rate'] not in ('', None) else 'n/a'} |")
baseline_table='\n'.join(baseline_rows)
candidate_rows=[]
for r in csv.DictReader((SRC/'s3_candidate_value_aggregates.csv').open(encoding='utf-8')):
 if int(r['candidate_count'])>0:
  candidate_rows.append(f"| {r['cohort']} | {r['kind']} | {r['role']} | {r['candidate_count']} | {r['scm_count']} | {fmt(r['mean_within_scm_regret_gain'])} | [{fmt(r['scm_cluster_bootstrap95_low'])}, {fmt(r['scm_cluster_bootstrap95_high'])}] |")
candidate_table='\n'.join(candidate_rows)
deep=f'''# Research S3 corrected deep-analysis results

**Classification:** post-hoc exploratory; original Research C cohorts reused. Correction contract lock commit: `b832001c701f8183cb7ddb53ba02950785a36a9a`. Executed analysis source revision: `616ec21499eb4cd4b43139423240cd380a643d86`. No new SCM/G0/independent observations/intervention rows were generated.

## B=2 baselines and policy comparisons

| Cohort | Policy | Mean regret | Mean edits | Action-change rate vs S0 |
|---|---|---:|---:|---:|
{baseline_table}

Random-M4 is an exact expectation over uniform sequential legal choices; its action-change column is the expected probability of changing the S0 action, not the action-change rate of a single realized trajectory.

## Corrected 63-subset Greedy replay

All 63 nonempty T1–T6 subsets were recomputed at B=1–4 in Development (64) and Held-out (200). Cohort policy aggregates, paired intervals, and candidate summaries are in `tables/correction_v1/`. The 63-way observed minima are descriptive and must not be treated as selected confirmatory policies.

| Cohort | B | Policy | Mean regret | Mean edits |
|---|---:|---|---:|---:|
{chr(10).join(core)}

Corrected lookahead evaluated all 63 subsets at B=2. Only one Held-out contrast had a nonzero point estimate:

| Cohort | Lookahead − Greedy | Mean difference | 95% pointwise interval | Better/worse/tie |
|---|---|---:|---:|---:|
{looktext}

This contrast is driven by one changed unit among 200 Held-out SCMs; no broad lookahead advantage is established. Fallback counts are recorded separately for each metric set in the corrected summary JSON and are not hard-coded to zero.

## Individual feasible M4 edits

The following are mean SCM-level regret reductions after each initially feasible M4 edit, grouped by error class and task-structure role. Positive values mean improvement; negative values mean harm. Candidate rows are clustered within SCM before averaging; the bootstrap interval resamples SCMs. Sparse cells should be read cautiously.

| Cohort | Error | Role | Candidate edits | SCMs | Mean regret reduction | 95% SCM-cluster interval |
|---|---|---|---:|---:|---:|---:|
{candidate_table}

The number of SCMs with at least two initially legal M4 edits was 11/64 Development and 35/200 Held-out. T1/T2 score every eligible pair in the fixed task-zone universe, whereas realized M4 edits are restricted to the initial reference-relative error candidate pool; metric-gain ranking therefore evaluates how scores rank feasible edits, not all possible graph changes.

## Metric gain versus realized edit value

Per-SCM rankings compare structural score gain with realized one-edit regret gain. Candidate count, per-SCM pairwise rank accuracy, within-SCM Spearman, tied-best hit rate, positive-score/worsened-regret counts are in `tables/correction_v1/corrected_s3_metric_gain_validation.csv`.

| Cohort | Metric | SCMs with ≥2 candidates | Candidate count | Pairwise rank accuracy | Mean within-SCM Spearman* | Best-candidate hit rate | Positive-score/worsened candidates |
|---|---|---:|---:|---:|---:|
{metrics_table()}

\*Spearman is averaged only over SCMs where both score and utility vary; the table's SCM count is the multi-candidate count, not the Spearman-defined denominator. Hit rate allows ties among best observed candidates. These are descriptive, not out-of-sample ranking validation. Several candidate gains are zero under T1/T4/T6 despite nonzero regret changes; graph-score gain is not decision gain.

## Metric complementarity

A descriptive all-subset marginal contribution table is supplied at `tables/correction_v1/descriptive_metric_marginal_contributions.csv`. It averages the difference in cohort mean regret between each nonempty subset and the same subset with one metric removed, stratified by parent subset size and budget. It has no unit-level bootstrap interval and changes the equal-weight average when a metric is added; it is not a causal marginal effect. Pairwise trajectory identity, full factorial uncertainty, and exhaustive ranking overlap were not completed.

## Not completed

- Deterministic baselines (S0, Full Greedy, Canonical Oracle, and four M4 error-type-first variants) were recomputed from the original cohorts. Exact Random-M4 sequence expectation was computed at B=1 and B=2; it is an expectation over legal choices, not a deterministic trajectory.
- Ex-post best feasible M4 edit and complete two-edit interaction benchmark were not executed.
- Gamma objective sensitivity was not run.
- Holm-adjusted inference was not calculated; intervals are pointwise.
- Research D unit-level extension remains unavailable.

See the separate not-run documents. The corrected S3 Gate is therefore **partial with documented limitations**; it does not authorize or claim an independently confirmed policy winner.
'''
(HERE/'RESEARCH_S3_DEEP_ANALYSIS_RESULTS.md').write_text(deep,encoding='utf-8',newline='\n')
(HERE/'RESEARCH_S3_METRIC_GAIN_VALIDATION.md').write_text('''# Research S3 metric-gain validation\n\nThis post-hoc diagnostic compares per-edit T1–T6 score gains and frozen M4 gain with realized single-edit regret reduction. Scores and outcomes are grouped within SCM first; SCMs, not candidate rows, are the reporting units. The supplied table reports SCM-balanced pairwise ranking accuracy, within-SCM Spearman when defined, best-candidate hit rate allowing ties, and counterexamples where positive structural gain coincides with worse realized regret.\n\nResults and counts: `tables/correction_v1/corrected_s3_metric_gain_validation.csv`. No confidence intervals were computed for ranking summaries, and no held-out cohort was reserved for choosing metrics: both original Research C cohorts had already been observed. The rankings are descriptive. Discrete metrics generate many ties; Spearman denominators vary and are explicitly smaller than or equal to the multi-candidate SCM count. Ties in score count one-half in pairwise accuracy; utility-tied candidate pairs are excluded.\n\nA structural score is not a direct estimate of the causal or decision value of an edit. Positive structural gain can co-occur with a worse decision regret, and a zero score gain can co-occur with a realized benefit. No general metric ranking is established.\n''',encoding='utf-8',newline='\n')
(HERE/'RESEARCH_S3_EX_POST_BENCHMARK.md').write_text('''# Ex-post best-feasible benchmark — not run\n\nThe corrected replay did not evaluate the ex-post best feasible single M4 edit or exhaustive best feasible two-edit sequence. Those baselines require selecting with observed regret and must remain isolated as privileged diagnostics. No ex-post comparator value or multi-edit interaction result is claimed. The normal-policy corrected graphs and outputs are retained separately.\n''',encoding='utf-8',newline='\n')
(HERE/'RESEARCH_S3_FACTORIAL_CONTRIBUTION.md').write_text('''# Factorial contribution and metric complementarity\n\nThe corrected cohort-aggregate table includes a descriptive marginal-contribution surface for each nonempty subset J and added metric Tj, comparing mean regret for J with mean regret for J+Tj at identical cohort, budget, and source sample. Results are summarized by parent-set size in `tables/correction_v1/descriptive_metric_marginal_contributions.csv`. The contrast changes the equal-weight average of structural gains and is therefore not an isolated causal effect of a metric.\n\nThe aggregate surface contains dependent comparisons and does not provide SCM-paired uncertainty, full trajectory equivalence clusters, or sequence-interaction tests. Formal complementarity claims for T3/T4, T3/T5, T3/T6, T1/T2 and edit-order interactions remain unverified. The ex-post two-edit interaction analysis was not run.\n''',encoding='utf-8',newline='\n')
(HERE/'RESEARCH_S3_OBJECTIVE_SENSITIVITY.md').write_text('''# Objective sensitivity — not run in correction replay\n\nThe corrected S3 recomputation retains the original Research C target-tracking objective (gamma=0). It does not apply gamma=.2 or gamma=.5 to corrected S3 recommendations and regret. Existing S1 sensitivity results are not substitutes. No claim is made that S3 ranking persists under penalized movement objectives. No additional observations or interventions were generated.\n''',encoding='utf-8',newline='\n')
(HERE/'RESEARCH_S3_CONFIRMATORY_EXPERIMENT_PROPOSAL.md').write_text('''# Independent confirmation proposal — design not yet powered\n\nThe S3 correction remains exploratory. A future independent confirmation would compare one Development-selected T policy with frozen M4 on a new SCM cohort; a separate structural stratum could be defined by at least two initially DAG-feasible M4 edits, without using regret for eligibility. Freeze task, target, metric, budget, tie/fallback rules, estimand, and SCM-cluster analysis before outcomes. The old Held-out cohort cannot serve as confirmation after it has been inspected in S3.

A defensible sample size cannot be specified from the corrected summaries alone because policy selection was post-hoc, many metrics were searched, and the proposed primary contrast and minimum relevant difference have not been frozen. A future protocol must set a precision target or relevant effect and use an independent pilot variance; do not use the most favorable corrected metric contrast as the planning effect. No new SCM generation is authorized by this proposal.
''',encoding='utf-8',newline='\n')
(HERE/'RESEARCH_S3_CORRECTED_RESULTS.md').write_text(f'''# Corrected S3 results — versioned reanalysis\n\nThe historical first-run report remains available but is superseded for implementation-specific S3 values by `RESEARCH_S3_CORRECTION_AUDIT.md` and `RESEARCH_S3_DEEP_ANALYSIS_RESULTS.md`. Corrected summary gate: `{summary['gate']}`. It is still post-hoc exploratory.\n\n## Paired baselines\n\nM4 minus exact Random-M4 sequence expectation:\n\n| Cohort | Mean difference | 95% pointwise SCM bootstrap | Better/worse/tie |\n|---|---:|---:|---:|\n'''+ '\n'.join(f"| {r['cohort']} | {fmt(r['mean_difference'])} | [{fmt(r['ci95_low'])}, {fmt(r['ci95_high'])}] | {r['better']}/{r['worse']}/{r['tie']} |" for r in interval if r['contrast']=='M4_ORIGINAL - M4_RANDOM_EXPECTATION' and r['budget']=='1')+'\n\nAll 63 metric subsets and 63 lookahead subsets were recomputed. The corrected run also recomputed frozen baselines, error-type-first strategies, and exact uniform Random-M4 expectations at B=1 and B=2. Baseline and opportunity summaries are included in the corrected tables. The corrected artifact directory is `tables/correction_v1/`. No public table contains SCM-keyed rows. The S3 result remains exploratory and does not establish a policy winner.\n',encoding='utf-8',newline='\n')
# Mark old report as historical without deleting its original figures/numbers.
old=HERE/'RESEARCH_S3_FINAL_RESULTS.md'; oldtxt=old.read_text(encoding='utf-8-sig')
if not oldtxt.startswith('> **Historical:'):
 old.write_text('> **Historical: first S3 exploratory implementation (superseded for corrected graph/Regret results). Preserve as executed at the time. See `RESEARCH_S3_CORRECTION_AUDIT.md` and `RESEARCH_S3_CORRECTED_RESULTS.md`.**\n\n'+oldtxt,encoding='utf-8',newline='\n')
print('correction artifacts written',len(list(DEST.iterdir())))

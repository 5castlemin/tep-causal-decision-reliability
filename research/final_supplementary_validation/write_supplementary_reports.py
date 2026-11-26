"""Render public Research C supplementary reports and compact SVG figures."""
from __future__ import annotations
import csv, hashlib, json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "outputs"

def read_csv(name):
    with (OUT / name).open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
    return h.hexdigest()

def fmt(x,n=4):
    try:return f"{float(x):.{n}f}"
    except (ValueError,TypeError):return str(x)

def write(name, text):
    (ROOT/name).write_text(text.strip()+"\n",encoding="utf-8",newline="\n")

def svg_line(name,title,subtitle,series,ylabel):
    # Minimal dependency-free, accessible SVG line chart.
    W,H=960,560;L,R,T,B=95,30,85,90;pw=W-L-R;ph=H-T-B
    vals=[v for _,pts,_ in series for _,v in pts if v is not None]
    ymin=min(vals);ymax=max(vals);pad=(ymax-ymin)*.12 or .1;ymin-=pad;ymax+=pad
    xs=sorted({x for _,pts,_ in series for x,_ in pts})
    def X(i):return L+(i/(len(xs)-1 if len(xs)>1 else 1))*pw
    def Y(v):return T+(ymax-v)/(ymax-ymin)*ph
    colors=["#225ea8","#d95f0e","#31a354","#756bb1","#636363","#e7298a"]
    s=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
       '<rect width="100%" height="100%" fill="white"/>',
       f'<text x="{L}" y="35" font-family="Arial,sans-serif" font-size="24" font-weight="700">{title}</text>',
       f'<text x="{L}" y="61" font-family="Arial,sans-serif" font-size="14" fill="#444">{subtitle}</text>']
    for j in range(5):
        v=ymin+(ymax-ymin)*j/4;y=Y(v)
        s.extend([f'<line x1="{L}" y1="{y:.1f}" x2="{W-R}" y2="{y:.1f}" stroke="#ddd"/>',
                  f'<text x="{L-10}" y="{y+5:.1f}" text-anchor="end" font-family="Arial" font-size="12">{v:.3f}</text>'])
    s.extend([f'<line x1="{L}" y1="{T}" x2="{L}" y2="{H-B}" stroke="#333"/>',f'<line x1="{L}" y1="{H-B}" x2="{W-R}" y2="{H-B}" stroke="#333"/>'])
    for i,x in enumerate(xs):s.append(f'<text x="{X(i):.1f}" y="{H-B+24}" text-anchor="middle" font-family="Arial" font-size="12">{x}</text>')
    for k,(label,pts,color) in enumerate(series):
        pts=sorted(pts);coords=" ".join(f"{X(xs.index(x)):.1f},{Y(v):.1f}" for x,v in pts if v is not None)
        s.append(f'<polyline points="{coords}" fill="none" stroke="{color or colors[k%len(colors)]}" stroke-width="3"/>')
        for x,v in pts:
            if v is not None:s.append(f'<circle cx="{X(xs.index(x)):.1f}" cy="{Y(v):.1f}" r="4" fill="{color or colors[k%len(colors)]}"/>')
        ly=H-28-(k//3)*20;lx=L+(k%3)*280
        s.extend([f'<line x1="{lx}" y1="{ly-4}" x2="{lx+25}" y2="{ly-4}" stroke="{color or colors[k%len(colors)]}" stroke-width="3"/>',f'<text x="{lx+32}" y="{ly}" font-family="Arial" font-size="13">{label}</text>'])
    s.extend([f'<text x="25" y="{T+ph/2:.1f}" transform="rotate(-90 25 {T+ph/2:.1f})" text-anchor="middle" font-family="Arial" font-size="14">{ylabel}</text>','</svg>'])
    (ROOT/name).write_text("\n".join(s)+"\n",encoding="utf-8")

def svg_dots(name,title,subtitle,labels,values,xlabel):
    W,H=1000,470;L,R,T,B=290,40,85,45;pw=W-L-R;ph=H-T-B
    lo=min(0.0,min(values));hi=max(0.0,max(values));pad=(hi-lo)*.12 or .05;lo-=pad;hi+=pad
    X=lambda v:L+(v-lo)/(hi-lo)*pw
    s=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">','<rect width="100%" height="100%" fill="white"/>',f'<text x="{L}" y="35" font-family="Arial" font-size="23" font-weight="700">{title}</text>',f'<text x="{L}" y="60" font-family="Arial" font-size="14" fill="#444">{subtitle}</text>']
    for j in range(5):
        v=lo+(hi-lo)*j/4;x=X(v);s += [f'<line x1="{x:.1f}" y1="{T}" x2="{x:.1f}" y2="{H-B}" stroke="#ddd"/>',f'<text x="{x:.1f}" y="{H-B+20}" text-anchor="middle" font-family="Arial" font-size="12">{v:.2f}</text>']
    s.append(f'<line x1="{X(0):.1f}" y1="{T}" x2="{X(0):.1f}" y2="{H-B}" stroke="#333" stroke-dasharray="5,4"/>')
    for i,(lab,val) in enumerate(zip(labels,values)):
        y=T+(i+.5)*ph/len(labels);s += [f'<text x="{L-12}" y="{y+5:.1f}" text-anchor="end" font-family="Arial" font-size="13">{lab}</text>',f'<circle cx="{X(val):.1f}" cy="{y:.1f}" r="6" fill="#225ea8"/>']
    s += [f'<text x="{L+pw/2:.1f}" y="{H-5}" text-anchor="middle" font-family="Arial" font-size="14">{xlabel}</text>','</svg>']
    (ROOT/name).write_text("\n".join(s)+"\n",encoding="utf-8")

def main():
    summary=json.loads((OUT/"supplementary_summary.json").read_text(encoding="utf-8"))
    aud=json.loads((OUT/"supplementary_audit_summary.json").read_text(encoding="utf-8"))
    agg=read_csv("s1_aggregate.csv");contr=read_csv("s1_corrected_primary_contrasts.csv");corr=read_csv("s2_shared_index_metric_correlations.csv");models=read_csv("s2_nested_model_validation.csv");cls=read_csv("s2_zero_regret_classification.csv");opt=read_csv("s1_optimum_distribution.csv")
    final_audit=json.loads((OUT/"final_supplementary_audit_summary.json").read_text(encoding="utf-8"))
    objcorr=read_csv("s1_s2_common_graph_objective_associations.csv")
    objmap={(r["cohort"],r["condition"],r["metric"]):r for r in objcorr}
    objconditions=["delta=original;gamma=0.0","delta=original;gamma=0.2","delta=original;gamma=0.5","delta=original;gamma=1.0","delta=-0.25;gamma=0.2","delta=0.25;gamma=0.2"]
    objlabels=["Original γ=0","Original γ=.2","Original γ=.5","Original γ=1","δ=−.25, γ=.2","δ=+.25, γ=.2"]
    objective_corr_rows=[]
    for cond,label in zip(objconditions,objlabels):
        dr=objective_corr_rows
        f1=objmap[("C_HELDOUT",cond,"directed_f1")]
        te=objmap[("C_HELDOUT",cond,"task_error_rate")]
        path=objmap[("C_HELDOUT",cond,"xy_path")]
        dr.append(f"| {label} | {int(float(path['n_scm']))} | {fmt(f1['spearman_scm_balanced'],3)} | {fmt(te['spearman_scm_balanced'],3)} | {fmt(path['spearman_scm_balanced'],3)} |")
    objective_corr_table="\n".join(objective_corr_rows)
    # Primary contrast tables report A-B; negative values mean A has lower regret.
    primary="\n".join(f"| {r['cohort']} | {r['contrast']} | {float(r['mean_difference']):+.5f} | [{float(r['ci95_low']):+.5f}, {float(r['ci95_high']):+.5f}] | {r['better']}/{r['worse']}/{r['tie']} |" for r in contr)
    model_table="\n".join(f"| {r['model']} | {float(r['heldout_mae']):.5f} | {float(r['heldout_r2']):.3f} | {r['n_heldout_scm']} |" for r in models)
    cls_table="\n".join(f"| {r['model']} | {float(r['heldout_brier']):.4f} | {float(r['heldout_auroc']):.3f} | {float(r['heldout_average_precision']):.3f} | {r['heldout_positive_graphs']}/{r['heldout_graph_rows']} |" for r in cls)
    held_corr={r['metric']:r for r in corr if r['cohort']=='C_HELDOUT' and r.get('ci95_low')}
    metric_labels={"directed_f1":"directed_f1","directed_shd":"directed_shd","task_error_rate":"task_error_rate","xy_path":"xy_path","abs_effect_magnitude_error":"abs_signed_total_effect_slope_error"}
    corr_table="\n".join(f"| {metric_labels[m]} | {float(held_corr[m]['spearman_scm_balanced']):+.3f} | [{float(held_corr[m]['ci95_low']):+.3f}, {float(held_corr[m]['ci95_high']):+.3f}] |" for m in metric_labels)
    optrows=[r for r in opt if r["cohort"]=="C_HELDOUT" and r["target_delta"]=="original"]
    opt_table="\n".join(f"| {float(r['gamma']):g} | {float(r['endpoint_fraction']):.1%} | {float(r['zero_fraction']):.1%} | {float(r['nonzero_interior_fraction']):.1%} |" for r in optrows)
    primary_by={(r["cohort"],r["contrast"]):r for r in contr}
    held_fg_s0=primary_by[("C_HELDOUT","FullGreedy-S0")]
    held_m4_fg=primary_by[("C_HELDOUT","M4-FullGreedy")]
    effect_diag=read_csv("s1_corrected_effect_diagnostics.csv")
    effect_held={r["policy"]:r for r in effect_diag if r["cohort"]=="C_HELDOUT"}
    objective=read_csv("s1_corrected_objective_policy_summary.csv")
    objective_by={(r["cohort"],float(r["gamma"]),r["policy"]):r for r in objective}
    objective_lines=[]
    for g in (0,.05,.2,.5,1):
        vals=[float(objective_by[("C_HELDOUT",g,p)]["mean_regret"]) for p in ("S0","M1+M2+M3+M4","M4","M2+M4")]
        objective_lines.append(f"| {g:g} | " + " | ".join(f"{v:.8f}" for v in vals) + " |")
    objective_table="\n".join(objective_lines)
    write("SUPPLEMENTARY_INPUT_PROVENANCE.md",f'''# Supplementary input provenance

## Scope

The analysis used the original Research C Development (64 SCM) and Held-out (200 SCM) cohort/proposal SQLite databases in read-only mode. It did not use Research D because the private unit-level response materials were not available in this checkout. No new SCM, G0, observation, intervention response, or expert response was generated. Research E/F outputs were not treated as new cohorts.

The C truth specifications and observational arrays were deterministically reconstructed in memory and admitted only after their full digests matched the original ledger bindings. The analysis reports source SHA-256 values from the execution record:

| Input | SHA-256 |
|---|---|
| C Development cohort DB | `{summary['source_sha256']['C_DEVELOPMENT']['cohort_db_sha256']}` |
| C Development proposal DB | `{summary['source_sha256']['C_DEVELOPMENT']['proposal_db_sha256']}` |
| C Held-out cohort DB | `{summary['source_sha256']['C_HELDOUT']['cohort_db_sha256']}` |
| C Held-out proposal DB | `{summary['source_sha256']['C_HELDOUT']['proposal_db_sha256']}` |

SQLite integrity checks returned `ok`; connections used query-only mode. Exact truth and observation digest checks passed for 64 Development and 200 Held-out SCMs. The database files were not modified. See `supplementary_integrity_manifest.json` for public output and source-code hashes; raw unit-level tables remain local and gitignored.

## Research D exclusion

Research D's stored aggregate results remain valid historical outputs, but its local evaluator response vectors and unit-level recommendation material were absent. No D-level supplementary estimate is reported. This is an access limitation, not an inference that the earlier D audit did not occur.
''')
    write("SUPPLEMENTARY_FIXTURE_VALIDATION.md",'''# Supplementary code and fixture validation

The new calculation paths were checked with deterministic fixtures before reading cohort results. Tests cover gamma-zero identity with target-tracking loss, positive gamma action penalty, action tie-breaking, saved-edge replay and DAG validity, distinction between directed and skeleton metrics, SCM-grouped folds, heterogeneous CSV schemas, and weighted AUROC bounds/ties.

The supplementary audit also checks that duplicate `(SCM, structural graph hash)` rows agree on learner inputs, recommendation and loss before deduplication. Gamma-zero action/regret outputs reproduce the stored Research C outputs within the original `1e-12` regret tolerance. The original stored trajectory and result tables are not rewritten.

`SID/AID` was not run: this frozen environment contained no verified implementation and compatible fixture for the exact unresolved-edge and graph conventions. No result is imputed for those metrics.

The logistic classification audit initially exposed an AUROC implementation error (values above 1). It was corrected to a weighted Mann–Whitney calculation, a perfect/reversed/tied score regression test was added, and the stored-only audit was rerun. The final AUROC values are all in `[0,1]`.
''')
    write("S1_DECISION_OBJECTIVE_ROBUSTNESS.md",f'''# S1 — Decision-objective robustness

## Design

Post-hoc re-analysis of Research C only. It changes the target-tracking objective by adding `gamma × k²` to squared standardized target loss, with `gamma ∈ {{0,.05,.2,.5,1}}`, and varies the training-derived target by `delta ∈ {{-.25,+.25}}` SD. Action grid and per-SCM scale are held fixed. This is a robustness analysis, not a new confirmatory test; gamma is a dimensionless preference penalty, not measured operating cost.

## Primary condition

Original target, `gamma=.2`, `B=2`; intervals are paired SCM percentile-bootstrap pointwise 95% intervals (10,000 common-index resamples). Table entries are `Regret(A)-Regret(B)`, so negative favors the first named policy.

| Cohort | Contrast | Mean difference | 95% interval | Better / worse / tie |
|---|---|---:|---:|---:|
{primary}

The corrected Full Greedy contrast uses policy ID `M1+M2+M3+M4`; `CANONICAL_ORACLE` is a distinct structural-only diagnostic. Held-out Full Greedy−S0 is {float(held_fg_s0['mean_difference']):+.5f} ({float(held_fg_s0['ci95_low']):+.5f}, {float(held_fg_s0['ci95_high']):+.5f}); M4−Full Greedy is {float(held_m4_fg['mean_difference']):+.5f} ({float(held_m4_fg['ci95_low']):+.5f}, {float(held_m4_fg['ci95_high']):+.5f}). The earlier contrast used Canonical Oracle under the Full Greedy label; the original contract snapshot is retained and this correction is separately versioned. These exploratory intervals do not alter the frozen Research C primary or M4's Development-selected secondary status.

## Objective support

Original target, Held-out mean regret at B=2:

| gamma | S0 | Full Greedy | M4 | M2+M4 |
|---:|---:|---:|---:|---:|
{objective_table}

The named Full Greedy column is policy `M1+M2+M3+M4`; Canonical Oracle is a different diagnostic policy.

Held-out analytic-GT optimum category by original target:

| gamma | endpoint | zero action | nonzero interior |
|---:|---:|---:|---:|
{opt_table}

At gamma 0, all SCMs select endpoints, reproducing the boundary-action limitation. Positive penalty creates interior and zero-action optima, but does not do so uniformly: at gamma .2, 9% choose zero and 32.5% choose nonzero interior; at gamma .5, 73.5% choose nonzero interior and 26.5% choose zero. Under target offsets ±.25 and gamma .2, most Held-out optima are zero. Thus the robustness check broadens objective support in some conditions while preserving strong target dependence.

## Mechanism diagnostics

At gamma .2/B2, corrected Held-out total-effect sign accuracy is S0 {float(effect_held['S0']['total_effect_sign_accuracy_zero_as_category']):.3f}, Full Greedy {float(effect_held['M1+M2+M3+M4']['total_effect_sign_accuracy_zero_as_category']):.3f}, M4 {float(effect_held['M4']['total_effect_sign_accuracy_zero_as_category']):.3f}, M2+M4 {float(effect_held['M2+M4']['total_effect_sign_accuracy_zero_as_category']):.3f}, and Adaptive M4 {float(effect_held['ADAPTIVE_M4_BLOCKER_AWARE']['total_effect_sign_accuracy_zero_as_category']):.3f}. The stored `abs_effect_magnitude_error` is `abs(estimated_slope - true_slope)`, an absolute signed-total-effect slope error, not `abs(abs(estimated_slope)-abs(true_slope))`; numeric values are preserved under this corrected label. Sign accuracy keeps zero effects separate. The unit table contains slope but not intercept estimates, and per-action predictions were not saved, so intercept-error and oracle intercept/slope substitution diagnostics could not be run.

For Full Greedy, sign was correct but the canonical grid action was wrong in 171/200 Held-out SCMs; only 2/65 nonzero-interior-optimum SCMs had the canonical action match. The reference-graph learner's mean absolute signed slope error was .16799 (Held-out) and .15283 (Development); its optimum-action agreement was 99% at gamma=0 and 11% at gamma=.2 in Held-out. Intercept error cannot be computed because intercept values were not saved. Multiple-optimum agreement is not separately available in the local optimum artifact; these rates use the saved canonical optimum action.

See `outputs/s1_corrected_primary_contrasts.csv`, `outputs/s1_corrected_objective_policy_summary.csv`, `outputs/s1_corrected_effect_diagnostics.csv`, and `outputs/s1_optimum_distribution.csv`. The earlier `s1_primary_contrasts.csv` is retained as a historical, superseded output.
''')
    write("S1_EFFECT_MAGNITUDE_MECHANISM.md",'''# S1 — Effect magnitude and mechanism diagnostics

The objective penalty changes which action is preferred even when the graph and learner remain fixed. In the original target condition, gamma zero reproduces the endpoint optimum for every C SCM; increasing gamma yields interior and zero-action optima. This means the original endpoint concentration is partly a property of the target-tracking setup rather than a general statement about causal decision tasks.

The prior `abs_effect_magnitude_error` field computed `abs(estimated_slope - true_slope)`, an absolute signed total-effect slope error, not pure absolute-magnitude error. Corrected summaries preserve the numeric values and rename their interpretation. Saved per-action prediction vectors were unavailable, so oracle intercept-only or slope-only substitution diagnostics were not run. These are post-hoc diagnostics, not causal mediation evidence.

The empty-DAG learner is named `EMPTY_DAG_LEARNER`; it is not the Research F observational X–Y association learner. The existing F association baseline's gamma-zero Held-out regret is {float(final_audit['saved_f_association_baseline'][1]['mean_gamma_zero_regret']):.8f}; it was not newly evaluated over S1 gamma conditions. The action penalty is an abstract sensitivity parameter, not measured cost. Raw regret across gamma or cohorts is not a common economic scale.
''')
    write("S2_STRUCTURAL_METRIC_VALIDATION.md",f'''# S2 — Structural metric validation

## Analysis unit and uncertainty

There were 23,760 saved policy-budget graph rows and 1,333 unique `(SCM, structural graph hash)` rows (336 Development; 997 Held-out). Duplicates were checked for identical task, learner input, recommendation, and regret before collapsing. Correlation intervals resample SCM clusters, preserve within-SCM dependence, and are pointwise; graph rows and within-SCM pairs are not independent samples.

## Held-out metric association with regret

| Metric | SCM-balanced Spearman | 95% SCM-cluster interval |
|---|---:|---:|
{corr_table}

Task-related error rate and X→Y path presence show stronger association with decision regret than global directed F1/SHD in these stored C graphs. Absolute effect-magnitude error has no clear association (the interval includes zero in both cohorts). This is cohort- and task-specific, not a universal ranking of graph metrics. In same-SCM groups with identical SHD or skeleton F1, regret can still vary materially, showing that aggregate structure scores do not uniquely determine downstream performance.

## Predictive validation

| Feature model | Held-out SCM-balanced MAE | OOS R² | Unique Held-out graphs |
|---|---:|---:|---:|
{model_table}

Historical B and E were not nested. This corrected post-hoc comparison refits `B_original`, `E_nested = B_original + task features`, and `F_nested = E_nested + X→Y path` from the same saved graph features with the same Development grouped folds, SCM weighting, alpha candidates, and preprocessing. Results and common-index paired intervals are in `outputs/s2_nested_model_validation.csv` and `outputs/s2_nested_prediction_bootstrap.csv`. No held-out tuning or data generation occurred; historical non-nested B/E results remain separate.

## Zero-regret classification (secondary)

| Feature model | Brier | AUROC | Weighted Average Precision (AP) | Positive-regret graphs / rows |
|---|---:|---:|---:|---:|
{cls_table}

Held-out folds were not used to choose features or alpha; alpha was selected using grouped Development CV. Classification is post-hoc and SCM-balanced. The target is whether stored graph regret exceeds `1e-12`; it is not an independent outcome. The reported PR metric is weighted Average Precision: tied score blocks are processed together. It is not trapezoidal PR-AUC.

## Metric limits

Directed F1, SHD and frozen task-zone supports answer different structural questions. Unresolved edges are not silently treated as directed. SID/AID were not computed because a verified compatible implementation and fixture were unavailable. No claim that one score is a universally optimal structural metric is supported.
''')
    write("S2_GROUPED_PREDICTIVE_VALIDATION.md",'''# S2 — Grouped predictive validation

Models were trained and regularization selected only with five-fold Development CV grouped by SCM, using equal total SCM weight. The existing Held-out cohort was then evaluated once. The B-vs-E comparison is post-hoc because the C cohorts and outcomes had already been observed when this supplement was designed.

General structure features alone (B) yield Held-out SCM-balanced MAE .06966. Task-only features (D) yield .05763. General plus task features (E) yield .06047; paired SCM bootstrap reports B–E MAE difference .00919 (95% [.00239,.01576], 110 better / 73 worse / 17 tied). Structure plus directed-path (F) yields .03749; the oracle-effect diagnostic model G yields .03769 MAE and is not deployable. Full model outputs and paired intervals are in `outputs/s2_model_validation.csv` and `outputs/s2_prediction_bootstrap.csv`.

Positive-regret classification uses logistic models with the same grouped folds. The corrected Held-out AUROC values are .856 (B), .905 (E), and .961 (F), with Brier .114, .083, and .022. These are historical post-hoc discrimination results, not prospective calibration or an operational screening guarantee. Held-out PR-AUC is prevalence-sensitive and should be interpreted alongside the SCM-balanced positive prevalence.

The B/E results above are the original non-nested feature comparison and must not be interpreted as a controlled add-task-features comparison. Use the corrected nested `B_original`/`E_nested`/`F_nested` analysis in `S2_STRUCTURAL_METRIC_VALIDATION.md` and `outputs/s2_nested_model_validation.csv` for that question. Classification's PR metric is weighted Average Precision with ties processed as groups, not trapezoidal PR-AUC.
''')
    write("S2_SID_AID_FEASIBILITY.md",'''# SID/AID feasibility

Status: `SID_AID_NOT_RUN_WITH_DOCUMENTED_REASON`.

The local frozen environment did not contain a verified SID/AID implementation and fixtures matching the project's treatment of unresolved adjacencies, orientation, and the restricted task graph. Adding an unverified implementation at closeout would create a new metric pipeline without an independent correctness basis. Core structural analysis therefore reports the frozen M1–M4 supports, skeleton/directed scores, directed SHD, and task-zone metrics only. No SID/AID estimate is implied or substituted.
''')
    write("S1_S2_INTEGRATED_ANALYSIS.md",f'''# S1–S2 integrated analysis

Across the stored C cohorts, graph metrics tied to the task structure—especially task-zone error rate and X→Y path presence—are more strongly associated with regret than global accuracy alone. The relationship is not deterministic: graphs with the same SCM and similar aggregate score can have different policy recommendations and regrets. S1 further shows that the decision objective can change the optimal action distribution substantially.

Together these analyses support a conditional conclusion: structural quality matters through the task and objective used to make decisions. They do not show that any single structural metric causes a reduction in regret, nor that task-zone metrics dominate for other tasks. A corrected common-graph analysis uses the same B=2 graph set (84 Development graph rows/36 SCMs; 250 Held-out graph rows/121 SCMs), SCM-balanced weighting, and shared paired SCM bootstrap indices to compare correlations across original target gamma 0/.2/.5/1 and offsets ±.25 at gamma .2. Results are in `outputs/s1_s2_common_graph_objective_associations.csv`; they are descriptive and pointwise, not independent replications. Undefined correlations under constant outcomes remain NA. This does not validate S2 predictive performance under each objective.

Held-out common-graph SCM-balanced Spearman correlations (121 common SCMs, 250 graph rows; point estimates):

| Objective condition | SCMs | Directed F1 | Task error rate | X→Y path |
|---|---:|---:|---:|---:|
{objective_corr_table}
''')
    write("SUPPLEMENTARY_CRITICAL_REVIEW.md",'''# Critical review and limitations

1. This is post-hoc reuse of previously observed C cohorts; it is not a new confirmation.
2. Research D unit-level artifacts were unavailable here, so no D extension was run.
3. The penalty gamma is not an elicited utility or monetary cost.
4. Only one signed-linear synthetic SCM family and a fixed learner/task/action grid underpin S1/S2.
5. Graph rows repeat within SCM; inference therefore resamples SCMs, but the effective cohort remains 64/200 SCMs.
6. Task and path features are reference-assisted and do not solve unknown-ground-truth graph verification.
7. Model G uses oracle effect diagnostics and cannot be deployed as a predictor without those quantities.
8. SID/AID were unavailable under verified conventions.
9. Predictive associations are not causal effects of changing a metric.
10. Findings do not establish industrial utility, safety, economic savings, or universal metric superiority.

The key positive result is conditional objective robustness in Held-out under the pre-fixed gamma=.2/B2 comparison. Key counterweights are Development intervals that include zero for some contrasts, remaining objective sensitivity, and non-deterministic links between global structural scores and decision performance.
''')
    write("SUPPLEMENTARY_FINAL_RESULTS.md",f'''# Final supplementary results

Gate: `SUPPLEMENTARY_ANALYSIS_COMPLETED_WITH_LIMITATIONS`.

This is a post-hoc saved-data supplement and does not alter C's frozen primary. At original target, gamma=.2, B=2 Held-out, Full Greedy is `M1+M2+M3+M4` and `CANONICAL_ORACLE` is distinct. Mean regret: S0 .11795863, Full Greedy .09223511, M4 .08725290, M2+M4 .09031225, and reference-graph learner .08635285. The reference learner is a diagnostic with access to the reference DAG, not a deployable oracle. Shared-index paired SCM bootstrap pointwise intervals: Full Greedy−S0 −.02572 [{float(held_fg_s0['ci95_low']):.5f}, {float(held_fg_s0['ci95_high']):.5f}]; M4−Full Greedy −.00498 [{float(held_m4_fg['ci95_low']):.5f}, {float(held_m4_fg['ci95_high']):.5f}]. Development intervals include zero for both contrasts. At gamma=.5 Full Greedy regret .08216346 is below M4 .08359752; at gamma=1 the four repair policies all select `k=0` in 200/200 saved units. Objective dependence means M4 is not uniformly best.

`EMPTY_DAG_LEARNER` is the blank graph passed to the existing SCM learner; it is not Research F's observational association baseline. Saved F association results at gamma zero are .02939 Development/.03873 Held-out, and were not evaluated on the supplementary objective grid. S2 nested held-out MAE is .06966 (B_original), .06153 (E_nested), .03768 (F_nested); paired pointwise SCM bootstrap B−E is .00813 [{.00209:.5f}, {.01390:.5f}] and E−F is .02386 [.01674,.03116].

No new data were generated. Research D is excluded for lack of private unit-level artifacts. This supplement does not supersede Research C's frozen primary, change Research D's interpretation, or establish operational benefit.
''')
    write("SUPPLEMENTARY_PAPER_CONTRIBUTION_GUIDE.md",'''# Paper contribution guide

## Defensible contribution

The supplementary work demonstrates that (i) decision-objective specification can materially change action-optimum support, and (ii) task/path-aware structural summaries can be more informative about regret than global graph scores in the observed C cohorts. It adds sensitivity and measurement evidence to the C–F sequence; it is post-hoc and should be labeled as such.

## Suggested framing

“Within the evaluated synthetic SCM cohorts, decision performance was more closely associated with task-relevant path and error features than with global structural scores alone, and the pattern depended on the target-tracking objective.”

## Avoid

Do not call this a new confirmatory validation, a universal graph metric, an industrial result, a causal effect of metric choice, or proof of a deployable verification policy. Keep oracle-informed model G separate from deployable feature sets. State that D was not reanalyzed at unit level.
''')
    write("SUPPLEMENTARY_PRESENTATION_EVIDENCE_GUIDE.md",'''# Presentation evidence guide

1. **Question:** why structural accuracy alone may be insufficient. Cite the final C report and frozen contract.
2. **Objective sensitivity:** show `S1_OBJECTIVE_ROBUSTNESS.svg`; explain gamma as a dimensionless penalty and distinguish original target from offsets.
3. **Paired supplementary contrasts:** use `outputs/s1_corrected_primary_contrasts.csv`; Full Greedy is `M1+M2+M3+M4`, distinct from Canonical Oracle. Define contrast sign and shared SCM bootstrap unit.
4. **Metric associations:** show `S2_METRIC_ASSOCIATIONS.svg`; state SCM-clustered, pointwise intervals and post-hoc status.
5. **Predictive feature groups:** show `S2_PREDICTIVE_VALIDATION.svg`; note Development grouped CV, fixed historical Held-out, and oracle-informed G exclusion from deployment claims.
6. **Limitations:** no private D unit files; no SID/AID; synthetic-only; reference-assisted; no industrial or economic claim.

Likely questions: gamma meaning (sensitivity parameter only); why task metrics (stronger observed association in these cohorts); why no SID/AID (no verified compatible implementation); whether external manufacturing performance was re-tested (no); whether metrics cause better decisions (not established).
''')
    write("SUPPLEMENTARY_CLAIMS_EVIDENCE_MATRIX.md",f'''# Supplementary claims and evidence matrix

| Claim | Evidence | Unit / estimand | Grade | Limit / permitted wording |
|---|---|---|---|---|
| The objective changes action-optimum support. | `outputs/s1_optimum_distribution.csv` | C SCM; analytic grid optimum under fixed target/gamma | Post-hoc robustness | “In these cohorts, positive gamma produced interior/zero optima in some conditions.” Not universal. |
| At gamma .2/B2, repair policies have lower Held-out regret than S0. | `outputs/s1_corrected_primary_contrasts.csv` | Paired Held-out SCM; regret difference | Post-hoc | Full Greedy=`M1+M2+M3+M4`; Canonical Oracle is separate; pointwise shared-index intervals; does not alter C primary. |
| Task/path structure is more informative than global scores for regret here. | `outputs/s2_shared_index_metric_correlations.csv`, `outputs/s2_nested_model_validation.csv` | SCM-balanced graph association and Held-out prediction | Post-hoc metric evidence | Cohort/task conditional; weighted Spearman means midrank then SCM-weighted Pearson; not a causal metric effect. |
| Path features improve predictive MAE over general/task features. | `outputs/s2_nested_model_validation.csv`, `outputs/s2_nested_prediction_bootstrap.csv` | Fixed historical Held-out SCM-balanced MAE | Post-hoc | Nested B/E/F saved-feature comparison; model selection in Development; one historical Held-out evaluation. |
| Oracle-informed G is deployable. | No | N/A | Unsupported | G uses oracle effect diagnostics; do not claim deployability. |
| SID/AID establishes metric superiority. | Not computed | N/A | Unsupported | No verified compatible implementation. |
| Research D has supplementary unit-level validation here. | D private unit-level data absent | N/A | Unsupported | State the exclusion. |
| The findings establish plant-level gains or economic savings. | No physical/economic evaluation | N/A | Unsupported | Do not claim. |
''')
    write("SUPPLEMENTARY_FINAL_AUDIT.md",'''# Final supplementary audit

## Scope and gate

Read-only reanalysis of original C cohort data and saved C policy trajectories; no SCM, G0, observations, interventions, or expert responses were generated. F-Lite stored evaluation rows were not changed. Research D private unit-level materials were not available and were excluded.

## Corrections and validation

- Full Greedy is `M1+M2+M3+M4`; `CANONICAL_ORACLE` is distinct. The corrected shared-index paired contrasts are in `outputs/s1_corrected_primary_contrasts.csv`; the original incorrect comparison is retained as historical/superseded.
- The empty-DAG graph learner is labeled `EMPTY_DAG_LEARNER`, not Graph-free association. The saved Research F association baseline is reported only for gamma zero and was not reevaluated for the supplementary objective grid.
- The original S2 B/E feature comparison was not nested. Corrected B_original/E_nested/F_nested results use shared saved features and Development grouped folds, with Held-out reserved for evaluation.
- A same-graph-set objective-association reaggregation covers six prespecified saved objectives. It is SCM-balanced and uses common SCM bootstrap draws; it is descriptive and does not rerun predictive validation under each objective.
- The weighted AUROC implementation was corrected after range validation found values above 1; the corrected held-out AUROC values are B=.856, E=.905, F=.961.
- Gamma-zero reproduction and deterministic fixtures passed. AP tie-group fixtures include perfect, reversed, all-tied, nonuniform-weight, and within-tie permutation checks.
- Paired contrasts and metric associations use common SCM resamples and SCM as the independent unit; intervals are pointwise, not simultaneous.
- SID/AID remain unrun because no verified compatible implementation/fixture was available.
- All public tables are aggregate only. Unit-level S1/S2 files are gitignored and stay local.

Detailed hashes, CI counts, exact commands, and any environment caveats are recorded in the integrity manifest and the accompanying closeout.
''')
    # Figures from public aggregates.
    for cohort,tag in [("C_HELDOUT","HELDOUT"),("C_DEVELOPMENT","DEVELOPMENT")]:
        keep=[r for r in agg if r.get("cohort")==cohort and r.get("target_delta")=="original" and float(r.get("gamma",-1)) in (0,.05,.2,.5,1) and r.get("budget")=="2"]
        lines=[]
        for pol in ["S0","M1+M2+M3+M4","CANONICAL_ORACLE","M4","M2+M4","ADAPTIVE_M4_BLOCKER_AWARE"]:
            pts=[]
            for g in (0,.05,.2,.5,1):
                r=next((q for q in keep if q.get("policy")==pol and float(q.get("gamma",-1))==g),None)
                if r:pts.append((g,float(r["mean_regret"])))
            if pts:lines.append((pol,pts,None))
        if lines:svg_line(f"S1_OBJECTIVE_ROBUSTNESS_{tag}.svg",f"S1 objective robustness — {tag}","Stored C cohort; B=2; original training-derived target; post-hoc",lines,"Mean regret")
    metric_names=["directed_f1","directed_shd","task_error_rate","xy_path","abs_effect_magnitude_error"]
    metric_display=["directed_f1","directed_shd","task_error_rate","xy_path","abs_signed_total_effect_slope_error"]
    svg_dots("S2_METRIC_ASSOCIATIONS.svg","Structural metrics vs regret — Held-out","SCM-balanced Spearman; pointwise 95% SCM-cluster intervals in CSV",metric_display,[float(held_corr[m]["spearman_scm_balanced"]) for m in metric_names],"SCM-balanced Spearman correlation")
    model_names=["B_original","E_nested","F_nested"]
    svg_dots("S2_PREDICTIVE_VALIDATION.svg","Nested structural feature models predicting regret — Held-out","Post-hoc; grouped Development CV; SCM-balanced MAE",model_names,[float(next(q for q in models if q["model"]==m)["heldout_mae"]) for m in model_names],"SCM-balanced MAE (lower is better)")
    (ROOT/"supplementary_summary.json").write_text(json.dumps({"status":"SUPPLEMENTARY_ANALYSIS_COMPLETED_WITH_LIMITATIONS","classification":"POST_HOC_SUPPLEMENTARY_DECISION_ROBUSTNESS_AND_METRIC_VALIDATION","correction":"SUPPLEMENTARY_CONTRACT_CORRECTION_V2.md; original contract and primary contrasts retained as historical; corrected Full Greedy contrasts use M1+M2+M3+M4","corrected_audit_summary_sha256":sha(OUT/"final_supplementary_audit_summary.json"),"source_summary_sha256":sha(OUT/"supplementary_summary.json"),"audit_summary_sha256":sha(OUT/"supplementary_audit_summary.json"),"figures":["S1_OBJECTIVE_ROBUSTNESS_DEVELOPMENT.svg","S1_OBJECTIVE_ROBUSTNESS_HELDOUT.svg","S2_METRIC_ASSOCIATIONS.svg","S2_PREDICTIVE_VALIDATION.svg"],"research_d_unit_level_analysis":"NOT_RUN_PRIVATE_UNIT_MATERIAL_UNAVAILABLE","sid_aid":"NOT_RUN_NO_VERIFIED_COMPATIBLE_IMPLEMENTATION","new_data_generated":False},indent=2)+"\n",encoding="utf-8")
    print("Wrote supplementary reports and figures")

if __name__=="__main__":main()

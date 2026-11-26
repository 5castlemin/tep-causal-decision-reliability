"""Supplementary diagnostics from saved units; no policy or response resampling."""
from __future__ import annotations
import csv, json, math
from collections import defaultdict, Counter
from pathlib import Path
import numpy as np
from research.final_supplementary_validation.analyze_supplementary import (
    ROOT, OUT, GAMMAS, DELTAS, K, read_cohorts, run_predictive_s2, save_csv,
)

BOOT=10_000
SEED=2026112602

def read_csv(name):
    with (OUT/name).open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))

def ranks(x):
    x=np.asarray(x); order=np.argsort(x,kind="mergesort"); out=np.empty(len(x),float); i=0
    while i<len(x):
        j=i+1
        while j<len(x) and x[order[j]]==x[order[i]]:j+=1
        out[order[i:j]]=(i+j-1)/2+1;i=j
    return out

def weighted_spearman(x,y,w):
    x=np.asarray(x,float);y=np.asarray(y,float);w=np.asarray(w,float)
    ok=np.isfinite(x)&np.isfinite(y)&np.isfinite(w)&(w>0)
    if ok.sum()<3:return None
    rx,ry=ranks(x[ok]),ranks(y[ok]); ww=w[ok]; mx=np.average(rx,weights=ww);my=np.average(ry,weights=ww)
    dx=rx-mx;dy=ry-my; den=math.sqrt(float(np.sum(ww*dx*dx)*np.sum(ww*dy*dy)))
    return float(np.sum(ww*dx*dy)/den) if den else None

def correlation_audit(rows):
    metric_names=["skeleton_f1","directed_f1","directed_shd","atomic_error_count","task_error_count","task_error_rate","xy_path","abs_effect_magnitude_error"]
    result=[]; rng=np.random.default_rng(SEED)
    for cohort in ("C_DEVELOPMENT","C_HELDOUT"):
        rr=[r for r in rows if r["cohort"]==cohort]
        by=defaultdict(list)
        for r in rr:by[r["scm_id"]].append(r)
        ids=sorted(by)
        for metric in metric_names:
            x=[float(r[metric]) if r[metric] not in (None,"") else float("nan") for r in rr]; y=[float(r["regret"]) for r in rr]
            w=[1/len(by[r["scm_id"]]) for r in rr]
            point=weighted_spearman(x,y,w); vals=[]
            for _ in range(BOOT):
                draw=rng.integers(0,len(ids),size=len(ids)); bx=[];byy=[];bw=[]
                for j in draw:
                    cluster=by[ids[j]]; wt=1/len(cluster)
                    for r in cluster:
                        bx.append(float(r[metric]) if r[metric] not in (None,"") else float("nan"));byy.append(float(r["regret"]));bw.append(wt)
                corr=weighted_spearman(bx,byy,bw)
                if corr is not None: vals.append(corr)
            result.append({"cohort":cohort,"metric":metric,"n_scm":len(ids),"n_unique_graph":len(rr),"spearman_scm_balanced":point,"ci95_low":float(np.quantile(vals,.025)) if vals else None,"ci95_high":float(np.quantile(vals,.975)) if vals else None,"bootstrap_replicates_valid":len(vals),"interval":"cluster bootstrap by SCM; pointwise"})
    # Initial G0 one row per SCM, separately, avoids policy/budget pseudoreplication.
    for cohort in ("C_DEVELOPMENT","C_HELDOUT"):
        rr=[r for r in rows if r["cohort"]==cohort and r["policy"]=="S0" and int(r["budget"])==0]
        for metric in metric_names:
            valsx=[float(r[metric]) if r[metric] not in (None,"") else float("nan") for r in rr];valsy=[float(r["regret"]) for r in rr]
            result.append({"cohort":cohort,"analysis":"initial_G0","metric":metric,"n_scm":len(rr),"n_unique_graph":len(rr),"spearman_scm_balanced":weighted_spearman(valsx,valsy,[1]*len(rr)),"ci95_low":None,"ci95_high":None,"bootstrap_replicates_valid":0,"interval":"descriptive; initial-G0 row only"})
    return result

def same_scm_ranges(rows):
    out=[]
    for cohort in ("C_DEVELOPMENT","C_HELDOUT"):
        rr=[r for r in rows if r["cohort"]==cohort]; groups=defaultdict(list)
        for r in rr:groups[(r["scm_id"],r["directed_shd"])].append(float(r["regret"]))
        ranges=[max(v)-min(v) for v in groups.values() if len(v)>1]
        out.append({"cohort":cohort,"metric":"directed_shd","scm_metric_tie_groups":len(ranges),"within_scm_tie_group_regret_range_mean":float(np.mean(ranges)) if ranges else None,"median":float(np.median(ranges)) if ranges else None,"p90":float(np.quantile(ranges,.9)) if ranges else None,"max":float(np.max(ranges)) if ranges else None,"interpretation":"among distinct structural graphs within SCM sharing the same directed SHD"})
        groups=defaultdict(list)
        for r in rr:groups[(r["scm_id"],r["skeleton_f1"])].append(float(r["regret"]))
        ranges=[max(v)-min(v) for v in groups.values() if len(v)>1]
        out.append({"cohort":cohort,"metric":"skeleton_f1","scm_metric_tie_groups":len(ranges),"within_scm_tie_group_regret_range_mean":float(np.mean(ranges)) if ranges else None,"median":float(np.median(ranges)) if ranges else None,"p90":float(np.quantile(ranges,.9)) if ranges else None,"max":float(np.max(ranges)) if ranges else None,"interpretation":"among distinct structural graphs within SCM sharing the same skeleton F1"})
    return out

def prediction_bootstrap(graph_rows):
    models,unique,preds=run_predictive_s2(graph_rows)
    by_model={m: {(r["scm_id"],r["structural_graph_hash"]):(r["y"],r["prediction"]) for r in ps["rows"]} for m,ps in preds.items()}
    held=[r for r in graph_rows if r["cohort"]=="C_HELDOUT"]
    groups=defaultdict(list)
    for r in held:groups[r["scm_id"]].append(r)
    ids=sorted(groups); rng=np.random.default_rng(SEED+100)
    out=[]
    pairs=[("B_GENERAL_STRUCTURE","E_GENERAL_PLUS_TASK"),("B_GENERAL_STRUCTURE","F_STRUCTURE_PLUS_PATH"),("E_GENERAL_PLUS_TASK","F_STRUCTURE_PLUS_PATH"),("F_STRUCTURE_PLUS_PATH","G_ORACLE_EFFECT_DIAGNOSTICS")]
    for ma,mb in pairs:
        scm_delta=[]
        for sid in ids:
            ea=[];eb=[]
            for r in groups[sid]:
                key=(sid,r["structural_graph_hash"]); y,pa=by_model[ma][key];_,pb=by_model[mb][key]
                ea.append(abs(y-pa));eb.append(abs(y-pb))
            scm_delta.append(float(np.mean(ea)-np.mean(eb)))
        arr=np.asarray(scm_delta); draws=rng.integers(0,len(arr),size=(BOOT,len(arr))); boot=arr[draws].mean(axis=1)
        out.append({"contrast":f"MAE({ma})-MAE({mb})","mean_scm_balanced_delta_mae":float(arr.mean()),"ci95_low":float(np.quantile(boot,.025)),"ci95_high":float(np.quantile(boot,.975)),"better":int((arr>1e-12).sum()),"worse":int((arr< -1e-12).sum()),"tie":int((np.abs(arr)<=1e-12).sum()),"n_heldout_scm":len(arr),"interval":"paired SCM bootstrap; pointwise"})
    save_csv(OUT/"s2_prediction_bootstrap.csv",out)
    pred_rows=[]
    for model,ps in preds.items():
        for r in ps["rows"]:pred_rows.append({"model":model,**r})
    save_csv(OUT/"s2_predictions_local.csv",pred_rows)
    return out

def optimum_diagnostics(cohorts):
    rows=[]
    for cohort,units in cohorts.items():
        for u in units:
            p=u["payload"]; nodes=tuple(u["proposal"]["nodes"]); y=p["input_binding"]["target"]
            # Here target is the outcome node; action-response means are stored in the original evaluator rows.
            base_item=p["e2e_result"]["budgets"][0]["policies"][0]
            truth_by_k={float(q["k"]):float(q["mean"]) for q in base_item["evaluation"]["truth"]}
            yi=nodes.index(y); sd=float(u["data"].std(axis=0,ddof=1)[yi]); mean=float(u["data"].mean(axis=0)[yi]); orig=mean+int(p["input_binding"]["delta"])*sd
            for delta in DELTAS:
                target=orig if delta=="original" else mean+float(delta)*sd
                for gamma in GAMMAS:
                    losses={k:((v-target)/sd)**2+gamma*k*k for k,v in truth_by_k.items()}
                    minimum=min(losses.values()); opt=sorted(k for k,v in losses.items() if abs(v-minimum)<=1e-12)
                    category="multiple" if len(opt)>1 else "endpoint" if abs(opt[0])==1 else "zero" if opt[0]==0 else "nonzero_interior"
                    rows.append({"cohort":cohort,"scm_id":u["scm_id"],"target_delta":delta,"gamma":gamma,"optimal_k_set":";".join(map(str,opt)),"argmin_set_size":len(opt),"category":category,"mean_y_train":mean,"sd_y_train":sd,"target":target})
    agg=[]
    keys=sorted({(r["cohort"],r["target_delta"],r["gamma"]) for r in rows},key=str)
    for key in keys:
        rr=[r for r in rows if (r["cohort"],r["target_delta"],r["gamma"])==key]; c=Counter(r["category"] for r in rr)
        agg.append({"cohort":key[0],"target_delta":key[1],"gamma":key[2],"n_scm":len(rr),"endpoint":c["endpoint"],"zero":c["zero"],"nonzero_interior":c["nonzero_interior"],"multiple_optimum":c["multiple"],"endpoint_fraction":c["endpoint"]/len(rr),"zero_fraction":c["zero"]/len(rr),"nonzero_interior_fraction":c["nonzero_interior"]/len(rr),"multiple_fraction":c["multiple"]/len(rr)})
    save_csv(OUT/"s1_optimum_distribution.csv",agg)
    # Local unit-level details carry target values and are deliberately ignored by git.
    save_csv(OUT/"s1_optimum_diagnostics_local.csv",rows)
    return agg

def integrated(rows_s1,graphs):
    gmap={(r["cohort"],r["scm_id"],r["structural_graph_hash"]):r for r in graphs}
    selected={}
    for r in rows_s1:
        if r["target_delta"] not in ("original","-0.25","0.25") or float(r["gamma"])!=.2:continue
        if r["policy"] not in ("S0","CANONICAL_ORACLE","M4","M2+M4"):continue
        key=(r["cohort"],r["scm_id"],r["graph_hash"],r["target_delta"],r["gamma"])
        selected[key]=r
    out=[]
    for cohort in ("C_DEVELOPMENT","C_HELDOUT"):
      for delta in ("original","-0.25","0.25"):
        metrics=[]; losses=[]
        for (c,sid,gh,d,g),r in selected.items():
            if c!=cohort or d!=delta:continue
            gr=gmap.get((c,sid,gh))
            if gr: metrics.append(gr);losses.append(float(r["regret"]))
        for metric in ("directed_shd","task_error_count","skeleton_f1","xy_path"):
            corr=weighted_spearman([float(r[metric]) for r in metrics],losses,[1]*len(metrics)) if metrics else None
            out.append({"cohort":cohort,"target_delta":delta,"gamma":.2,"metric":metric,"n_graph_task_rows":len(metrics),"spearman":corr,"interpretation":"post-hoc association; repeated graphs/tasks are clustered within SCM and not independent"})
    save_csv(OUT/"s1_s2_integrated_associations.csv",out)
    return out

def main():
    rows=read_csv("s2_unique_graph_metrics.csv"); s1=read_csv("s1_unit_metrics.csv")
    cohorts,hashes=read_cohorts()
    corr=correlation_audit(rows);save_csv(OUT/"s2_metric_correlations.csv",corr)
    ties=same_scm_ranges(rows);save_csv(OUT/"s2_same_scm_metric_ties.csv",ties)
    pred=prediction_bootstrap(rows)
    opt=optimum_diagnostics(cohorts)
    integ=integrated(s1,rows)
    report={"source_sha256":hashes,"s2_metric_correlations":corr,"s2_same_scm_metric_ties":ties,"s2_prediction_bootstrap":pred,"s1_optimum_distribution":opt,"s1_s2_integrated":integ,"bootstrap_replicates":BOOT,"no_new_scm_or_g0":True,"no_new_intervention_samples":True}
    (OUT/"supplementary_audit_summary.json").write_text(json.dumps(report,indent=2,allow_nan=False),encoding="utf-8")
    print(json.dumps({"s2_metric_correlations":corr,"s2_same_scm_metric_ties":ties,"s2_prediction_bootstrap":pred,"s1_optimum_distribution":opt,"input_hashes":hashes},indent=2,allow_nan=False))

if __name__=="__main__":main()

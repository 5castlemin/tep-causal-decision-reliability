"""Post-hoc S1/S2 analyses over hash-bound, already completed Research C units.

The only reconstructed arrays are the exact original C SCM/training arrays;
their digests are checked against read-only SQLite bindings before use.
No policy cohort or evaluation sample is drawn here.
"""
from __future__ import annotations

import csv, hashlib, json, math, os, sqlite3, sys
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / "outputs"
DATA_ROOT = Path(os.environ.get("DAT_RESEARCH_ROOT", "C:/DAT_RESEARCH"))
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from research.budget_aware_refinement.step4c1_scm import generate_scm_parameters, generate_observations
from research.budget_aware_refinement.step4c1_gt import analytic_intervention_means
from research.budget_aware_refinement.step3_adapter import K
from research.original_objective import policy_engine as pe
from integrated_pilot import fit_model
from decision_mvp import static_mean_response

EXPECTED_DB = {
    "C_DEVELOPMENT": ("dd4264d5085adbabe9510bf99b564ec6c2b33e35d4eeb346a079cc4ccfb9b716", "1d00d1790788c342e15a81a0c405768e5e2a3e46ee75c57c0bbe34f8c0fcb584", "development"),
    "C_HELDOUT": ("37b3c265ecb65b09a97eda91d29411844c3a3851c9fbff6cfa06445f919a3eba", "59f1abcf5661a5b3d0658d0db0f7e6afe601ebd09997035228df0716800538d6", "confirmation"),
}
GAMMAS = (0.0, 0.05, 0.2, 0.5, 1.0)
DELTAS = ("original", -0.25, 0.25)
BOOTSTRAPS = 10_000
SEED_S1 = 2026112601
SEED_S2 = 2026112602
TOL = 1e-12


def sha(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""): h.update(b)
    return h.hexdigest()


def canonical_hash(obj) -> str:
    return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(",",":"),ensure_ascii=True,allow_nan=False).encode()).hexdigest()


def cfg_from(payload):
    c=dict(payload["config"]["repair_config"])
    c["costs"]=tuple(tuple(x) for x in c["costs"]); c["beta"]=tuple(c["beta"]); c["weights"]=tuple(c["weights"]); c["route_relevant_fp"]=tuple(tuple(x) for x in c["route_relevant_fp"])
    return pe.Config(**c)


def paths_for():
    return {
        "C_DEVELOPMENT": (DATA_ROOT/"research-c/development/development-20261123-seed-2026112301-v1/research_c_cohort.sqlite", DATA_ROOT/"research-c/development/development-20261123-seed-2026112301-v1/research_c_proposal_stage.sqlite"),
        "C_HELDOUT": (DATA_ROOT/"research-c/heldout/independent-evaluation-20261123-seed-2026112303-v1/research_c_cohort.sqlite", DATA_ROOT/"research-c/heldout/independent-evaluation-20261123-seed-2026112303-v1/research_c_proposal_stage.sqlite"),
    }


def apply_saved_edits(initial, truth, log):
    g=dict(initial)
    for edit in log:
        p=pe.pair(*edit["pair"]); kind=edit["error_type"]
        if edit["operation"] == "delete": replacement=None
        elif kind in ("FN","REV","UNRES"):
            replacement=truth.get(p)
            if replacement is None or replacement == pe.UNRES: raise ValueError("saved edit has no truth replacement")
        else: raise ValueError("unknown saved edit operation")
        candidate=dict(g)
        if replacement is None: candidate.pop(p,None)
        else: candidate[p]=replacement
        if not pe.dag(candidate): raise ValueError("saved edit sequence violates DAG")
        g=candidate
        if pe.graph_hash(g) != edit["after_hash"]: raise ValueError("saved edit graph hash mismatch")
    return g


def predictions_and_truth(data, nodes, graph, action, target, truth_spec, target_value, scale_y):
    directed={e for e in graph.values() if e != pe.UNRES}
    model=fit_model(data,list(nodes),directed,1.0)
    x=nodes.index(action); mean_x=float(data.mean(axis=0)[x]); sd_x=float(data.std(axis=0,ddof=1)[x])
    pred=[]; actual=[]
    for k in K:
        a=mean_x+float(k)*sd_x
        py=float(static_mean_response(model,action,a)[target])
        gy=float(analytic_intervention_means(truth_spec,action,a)[target])
        pred.append(py); actual.append(gy)
    return pred,actual,mean_x,sd_x


def choose(losses):
    return min(range(len(K)),key=lambda i:(float(losses[i]),abs(float(K[i])),float(K[i])))


def gamma_loss(mu,target,scale,gamma):
    return ((np.asarray(mu,dtype=float)-target)/scale)**2 + gamma*np.asarray(K,dtype=float)**2


def structural_features(truth, estimate, action, target, config, nodes):
    tdir={e for e in truth.values() if e!=pe.UNRES}; edir={e for e in estimate.values() if e!=pe.UNRES}
    ts={p for p in truth}; es={p for p in estimate}
    sk_tp=len(ts&es); sk_fp=len(es-ts); sk_fn=len(ts-es)
    sk_p=sk_tp/(sk_tp+sk_fp) if sk_tp+sk_fp else None; sk_r=sk_tp/(sk_tp+sk_fn) if sk_tp+sk_fn else None
    sk_f=(2*sk_p*sk_r/(sk_p+sk_r)) if sk_p is not None and sk_r is not None and sk_p+sk_r else (1.0 if not ts and not es else 0.0)
    d_tp=len(tdir&edir); d_fp=len(edir-tdir); d_fn=len(tdir-edir)
    d_p=d_tp/(d_tp+d_fp) if d_tp+d_fp else None; d_r=d_tp/(d_tp+d_fn) if d_tp+d_fn else None
    d_f=(2*d_p*d_r/(d_p+d_r)) if d_p is not None and d_r is not None and d_p+d_r else (1.0 if not tdir and not edir else 0.0)
    # Pairwise directed SHD: reversal costs one; unresolved-known direction costs one.
    shd=0
    for p in set(truth)|set(estimate):
        tv=truth.get(p); ev=estimate.get(p)
        if tv==ev: continue
        if tv is None or ev is None: shd += 1
        elif tv==pe.UNRES or ev==pe.UNRES: shd += 1
        elif tv == tuple(reversed(ev)): shd += 1
        else: shd += 2
    stats=pe.metrics(truth,estimate,action,target,config)
    m4=sum(stats["counts"]["M4"].values()); task_support=sum(stats["support"]["M4"].values())
    # Directed X->Y reachability.
    children=defaultdict(list)
    for u,v in edir: children[u].append(v)
    seen={action}; todo=[action]; path=False
    while todo:
        u=todo.pop()
        for v in children[u]:
            if v==target: path=True; todo=[]; break
            if v not in seen: seen.add(v); todo.append(v)
    return {
        "skeleton_precision":sk_p,"skeleton_recall":sk_r,"skeleton_f1":sk_f,
        "directed_precision":d_p,"directed_recall":d_r,"directed_f1":d_f,
        "directed_shd":shd,"atomic_error_count":sum(sum(v.values()) for v in stats["counts"].values()),
        "task_error_count":m4,"task_error_rate":m4/task_support if task_support else None,
        "task_fn":stats["counts"]["M4"]["FN"],"task_fp":stats["counts"]["M4"]["FP"],
        "task_rev":stats["counts"]["M4"]["REV"],"task_unres":stats["counts"]["M4"]["UNRES"],
        "task_support":task_support,"offtask_error_count":sum(sum(v.values()) for m,v in stats["counts"].items() if m!="M4"),
        "xy_path":int(path),"n_nodes":len(nodes),"n_truth_edges":len(tdir),"n_estimated_adjacencies":len(es),
        "unresolved_count":sum(v==pe.UNRES for v in estimate.values())
    }


def read_cohorts():
    out={}; source_hashes={}; expected_ids={"C_DEVELOPMENT":64,"C_HELDOUT":200}
    for cohort,(db,propdb) in paths_for().items():
        expected_db,expected_prop,proposal_cohort=EXPECTED_DB[cohort]
        if not db.is_file() or not propdb.is_file(): raise FileNotFoundError(f"missing original source for {cohort}")
        hdb,hprop=sha(db),sha(propdb)
        if (hdb,hprop)!=(expected_db,expected_prop): raise ValueError(f"source hash mismatch for {cohort}")
        source_hashes[cohort]={"cohort_db_sha256":hdb,"proposal_db_sha256":hprop}
        c=sqlite3.connect(f"file:{db}?mode=ro",uri=True); c.execute("pragma query_only=on")
        p=sqlite3.connect(f"file:{propdb}?mode=ro",uri=True); p.execute("pragma query_only=on")
        if c.execute("pragma integrity_check").fetchone()[0]!="ok" or p.execute("pragma integrity_check").fetchone()[0]!="ok": raise ValueError("SQLite integrity failure")
        props={}
        for (raw,) in p.execute("select proposal_json from proposal_attempts where status='ELIGIBLE'"):
            q=json.loads(raw); props[q["scm_id"]]=q
        rows=list(c.execute("select scm_id,status,result_json from scms order by ordinal"))
        if len(rows)!=expected_ids[cohort] or len({r[0] for r in rows})!=expected_ids[cohort] or any(r[1]!="COMPLETED" for r in rows): raise ValueError("cohort count/status/key failure")
        units=[]
        for scm_id,_,raw in rows:
            payload=json.loads(raw)["payload"]; proposal=props.get(scm_id)
            if proposal is None: raise ValueError("no eligible proposal binding")
            scm=generate_scm_parameters(proposal); obs=generate_observations(proposal,scm)
            binding=payload["input_binding"]
            if scm["equation_signature_sha256"]!=binding["truth_spec_sha256"] or obs["data_sha256"]!=binding["observations_sha256"]: raise ValueError(f"exact reconstruction hash mismatch {scm_id}")
            if (proposal["action"],proposal["target"],proposal["nodes"])!=(binding["action"],binding["target"],binding["nodes"]): raise ValueError("task/node binding mismatch")
            truth_spec=scm["truth_spec"]; truth=pe.state([tuple(e) for e in truth_spec["edges"]])
            initialj=payload["g0_generation"]["initial_graph"]
            initial=pe.state([tuple(e) for e in initialj["edges"]],unresolved=[tuple(e) for e in initialj["unresolved"]])
            if pe.graph_hash(initial)!=binding["initial_structural_graph_sha256"]: raise ValueError("G0 hash mismatch")
            units.append({"cohort":cohort,"scm_id":scm_id,"payload":payload,"proposal":proposal,"truth_spec":truth_spec,"truth":truth,"initial":initial,"data":np.asarray(obs["rows"],dtype=float),"config":cfg_from(payload)})
        c.close();p.close();out[cohort]=units
    return out,source_hashes


def save_csv(path,rows):
    path.parent.mkdir(parents=True,exist_ok=True)
    if not rows: path.write_text("",encoding="utf-8"); return
    fields=list(rows[0])
    with path.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)


def s1_and_s2(cohorts):
    s1=[]; graphs=[]; source_targets={}
    adaptive_path=ROOT/"research/budget_adaptive_repair/outputs/adaptive_m4_unit_results.csv"
    adaptive_rows={}
    if adaptive_path.is_file():
        with adaptive_path.open(encoding="utf-8-sig",newline="") as f:
            for row in csv.DictReader(f):
                key=(row["cohort"],row["scm_id"],int(row["budget"]))
                if key in adaptive_rows: raise ValueError("duplicate saved adaptive row")
                adaptive_rows[key]=row
    for cohort,units in cohorts.items():
        for u in units:
            p=u["payload"]; prop=u["proposal"]; nodes=tuple(prop["nodes"]); action,target=prop["action"],prop["target"]
            data=u["data"]; mean=data.mean(axis=0); sd=data.std(axis=0,ddof=1); yidx=nodes.index(target)
            scale=float(sd[yidx]); original_target=float(mean[yidx]+int(p["input_binding"]["delta"])*scale)
            policy_items=[]
            for b in p["e2e_result"]["budgets"]:
                for item in b["policies"]:
                    graph=apply_saved_edits(u["initial"],u["truth"],item["edit_log"])
                    if pe.graph_hash(graph)!=item["structural_graph_sha256"]: raise ValueError("saved structural graph hash mismatch")
                    if pe.graph_hash(graph)!=item["final_graph_sha256"]: raise ValueError("saved final graph hash mismatch")
                    pid=item["policy_id"]
                    pred,gt,mean_x,sd_x=predictions_and_truth(data,nodes,graph,action,target,u["truth_spec"],original_target,scale)
                    old=item["evaluation"]
                    base_pred=gamma_loss(pred,original_target,scale,0.0); base_gt=gamma_loss(gt,original_target,scale,0.0)
                    chosen=choose(base_pred); best=choose(base_gt); regret=float(base_gt[chosen]-base_gt[best])
                    if float(K[chosen])!=float(old["selected_k"]) or abs(regret-float(old["regret"]))>TOL: raise ValueError(f"gamma-zero replay mismatch {cohort}/{u['scm_id']}/{pid}/{b['budget']}")
                    # saved graph-level structural record is used by S2; no policy is rerun.
                    feat=structural_features(u["truth"],graph,action,target,u["config"],nodes)
                    for delta in DELTAS:
                        target_value=original_target if delta=="original" else float(mean[yidx]+float(delta)*scale)
                        for gamma in GAMMAS:
                            pl=gamma_loss(pred,target_value,scale,gamma); tl=gamma_loss(gt,target_value,scale,gamma)
                            pk=choose(pl); tk=choose(tl); reg=float(tl[pk]-tl[tk])
                            if reg < -TOL or not math.isfinite(reg): raise ValueError("invalid regret")
                            s1.append({"cohort":cohort,"scm_id":u["scm_id"],"policy":pid,"budget":b["budget"],"target_delta":delta,"gamma":gamma,"predicted_k":float(K[pk]),"true_optimal_k":float(K[tk]),"regret":max(0.0,reg),"track_component":float(((gt[pk]-target_value)/scale)**2),"action_penalty_component":float(gamma*K[pk]**2),"edit_count":int(item["total_edit_cost"]),"true_slope":float((gt[-1]-gt[0])/(2*scale)),"estimated_slope":float((pred[-1]-pred[0])/(2*scale)),"graph_hash":pe.graph_hash(graph)})
                    policy_items.append((b["budget"],pid,item,graph,feat,pred,gt))
            # The separately saved adaptive trajectory is consumed as-is; it is not rerun.
            if adaptive_rows:
                expected_adaptive=len(units)*5
                actual_adaptive=sum(k[0]==cohort and k[2] in range(5) for k in adaptive_rows)
                if actual_adaptive!=expected_adaptive: raise ValueError(f"adaptive saved-row count mismatch for {cohort}")
                for budget in range(5):
                    ar=adaptive_rows[(cohort,u["scm_id"],budget)]
                    log=json.loads(ar["edits"])
                    normlog=[{"pair":x["pair"],"error_type":x["kind"],"operation":x["operation"],"after_hash":x["after_hash"]} for x in log]
                    graph=apply_saved_edits(u["initial"],u["truth"],normlog)
                    pred,gt,mean_x,sd_x=predictions_and_truth(data,nodes,graph,action,target,u["truth_spec"],original_target,scale)
                    pk=choose(gamma_loss(pred,original_target,scale,0.0)); tk=choose(gamma_loss(gt,original_target,scale,0.0))
                    saved_action=float(ar["action"]); recomputed_action=float(mean_x+float(K[pk])*sd_x)
                    saved_regret=float(ar["regret"]); recomputed_regret=float(gamma_loss(gt,original_target,scale,0.0)[pk]-gamma_loss(gt,original_target,scale,0.0)[tk])
                    if abs(saved_action-recomputed_action)>1e-12 or abs(saved_regret-recomputed_regret)>TOL: raise ValueError("saved Adaptive M4 action/regret mismatch")
                    item={"edit_log":normlog,"structural_graph_sha256":pe.graph_hash(graph),"final_graph_sha256":pe.graph_hash(graph),"evaluation":{"selected_k":float(K[pk]),"regret":saved_regret},"total_edit_cost":float(ar["cost"])}
                    feat=structural_features(u["truth"],graph,action,target,u["config"],nodes)
                    pid="ADAPTIVE_M4_BLOCKER_AWARE"
                    for delta in DELTAS:
                        target_value=original_target if delta=="original" else float(mean[yidx]+float(delta)*scale)
                        for gamma in GAMMAS:
                            pl=gamma_loss(pred,target_value,scale,gamma); tl=gamma_loss(gt,target_value,scale,gamma); pk2=choose(pl); tk2=choose(tl); reg=float(tl[pk2]-tl[tk2])
                            if reg < -TOL or not math.isfinite(reg): raise ValueError("invalid Adaptive M4 regret")
                            s1.append({"cohort":cohort,"scm_id":u["scm_id"],"policy":pid,"budget":budget,"target_delta":delta,"gamma":gamma,"predicted_k":float(K[pk2]),"true_optimal_k":float(K[tk2]),"regret":max(0.0,reg),"track_component":float(((gt[pk2]-target_value)/scale)**2),"action_penalty_component":float(gamma*K[pk2]**2),"edit_count":int(float(ar["cost"])),"true_slope":float((gt[-1]-gt[0])/(2*scale)),"estimated_slope":float((pred[-1]-pred[0])/(2*scale)),"graph_hash":pe.graph_hash(graph)})
                    policy_items.append((budget,pid,item,graph,feat,pred,gt))
            # Add valid reference and graph-free diagnostics without using evaluation response to recommend.
            diag=[]
            diag.append(("REFERENCE_GRAPH",u["truth"],"reference"))
            empty=pe.state((),())
            diag.append(("GRAPH_FREE",empty,"graphfree"))
            for pid,graph,_ in diag:
                pred,gt,_,_=predictions_and_truth(data,nodes,graph,action,target,u["truth_spec"],original_target,scale)
                for delta in DELTAS:
                    target_value=original_target if delta=="original" else float(mean[yidx]+float(delta)*scale)
                    for gamma in GAMMAS:
                        tl=gamma_loss(gt,target_value,scale,gamma); pl=gamma_loss(pred,target_value,scale,gamma); pk=choose(pl); tk=choose(tl)
                        s1.append({"cohort":cohort,"scm_id":u["scm_id"],"policy":pid,"budget":0,"target_delta":delta,"gamma":gamma,"predicted_k":float(K[pk]),"true_optimal_k":float(K[tk]),"regret":max(0.0,float(tl[pk]-tl[tk])),"track_component":float(((gt[pk]-target_value)/scale)**2),"action_penalty_component":float(gamma*K[pk]**2),"edit_count":0,"true_slope":float((gt[-1]-gt[0])/(2*scale)),"estimated_slope":float((pred[-1]-pred[0])/(2*scale)),"graph_hash":pe.graph_hash(graph)})
            # S2 graph-level rows from stored C B0..4 policy graph/edit records.
            for budget,pid,item,graph,feat,pred,gt in policy_items:
                if budget>4: continue
                old=item["evaluation"]; ghash=pe.graph_hash(graph)
                gfit=pe.graph_hash(pe.state([e for e in graph.values() if e!=pe.UNRES]))
                errors=abs(float((gt[-1]-gt[0])/(2*scale))-float((pred[-1]-pred[0])/(2*scale)))
                row={"cohort":cohort,"scm_id":u["scm_id"],"policy":pid,"budget":budget,"structural_graph_hash":ghash,"learner_graph_hash":gfit,
                     "regret":float(old["regret"]),"selected_k":float(old["selected_k"]),"estimated_effect_slope":float((pred[-1]-pred[0])/(2*scale)),"true_effect_slope":float((gt[-1]-gt[0])/(2*scale)),"abs_effect_magnitude_error":float(errors),"effect_sign_error":int(np.sign((pred[-1]-pred[0]))!=np.sign((gt[-1]-gt[0]))),**feat}
                graphs.append(row)
            source_targets[u["scm_id"]]={"target":original_target,"scale":scale,"mean_y":float(mean[yidx])}
    return s1,graphs


def bootstrap_paired(a,b,seed,reps=BOOTSTRAPS):
    # input arrays indexed by common SCM order.
    a=np.asarray(a,float);b=np.asarray(b,float);d=a-b;n=len(d);rng=np.random.default_rng(seed)
    ix=rng.integers(0,n,size=(reps,n)); vals=d[ix].mean(axis=1)
    return float(d.mean()),float(np.quantile(vals,.025)),float(np.quantile(vals,.975)),int(np.sum(d< -TOL)),int(np.sum(d>TOL)),int(np.sum(np.abs(d)<=TOL))


def summarize_s1(rows):
    agg=[]
    keys=sorted({(r["cohort"],r["policy"],r["budget"],r["target_delta"],r["gamma"]) for r in rows},key=str)
    for key in keys:
        rs=[r for r in rows if (r["cohort"],r["policy"],r["budget"],r["target_delta"],r["gamma"])==key]
        opt=[r["true_optimal_k"] for r in rs]; reg=np.array([r["regret"] for r in rs])
        agg.append(dict(cohort=key[0],policy=key[1],budget=key[2],target_delta=key[3],gamma=key[4],n=len(rs),mean_regret=float(reg.mean()),median_regret=float(np.median(reg)),sd_regret=float(reg.std(ddof=1)),action_agreement=float(np.mean([r["predicted_k"]==r["true_optimal_k"] for r in rs])),endpoint_optimum=float(np.mean([abs(k)==1 for k in opt])),zero_optimum=float(np.mean([k==0 for k in opt])),nonzero_interior_optimum=float(np.mean([abs(k)==0.5 for k in opt])),mean_edit_count=float(np.mean([r["edit_count"] for r in rs])),mean_abs_effect_error=float(np.mean([abs(r["estimated_slope"]-r["true_slope"]) for r in rs])),effect_sign_accuracy=float(np.mean([np.sign(r["estimated_slope"])==np.sign(r["true_slope"]) for r in rs]))))
    contrasts=[]
    for cohort in ("C_DEVELOPMENT","C_HELDOUT"):
        ids=sorted({r["scm_id"] for r in rows if r["cohort"]==cohort})
        subset=[r for r in rows if r["cohort"]==cohort and r["target_delta"]=="original" and r["gamma"]==.2 and r["budget"]==2]
        by={(r["scm_id"],r["policy"]):r["regret"] for r in subset}
        for a,b in (("CANONICAL_ORACLE","S0"),("M4","CANONICAL_ORACLE"),("M4","S0")):
            vals=[by[(i,a)]-by[(i,b)] for i in ids]
            mean,lo,hi,better,worse,tie=bootstrap_paired(vals,np.zeros(len(vals)),SEED_S1+len(contrasts))
            label="FullGreedy-S0" if a=="CANONICAL_ORACLE" else "M4-FullGreedy" if b=="CANONICAL_ORACLE" else "M4-S0"
            contrasts.append(dict(cohort=cohort,condition="original_target_gamma_0.2_B2",contrast=label,source_policy_a=a,source_policy_b=b,mean_difference=mean,ci95_low=lo,ci95_high=hi,better=better,worse=worse,tie=tie,n=len(ids),interval="pointwise paired SCM percentile bootstrap"))
    return agg,contrasts


def deduplicate_graphs(rows):
    keys={}
    for r in rows:
        k=(r["cohort"],r["scm_id"],r["structural_graph_hash"])
        if k not in keys: keys[k]=r
        else:
            prev=keys[k]
            for col in ("regret","selected_k","estimated_effect_slope","true_effect_slope"):
                if abs(float(prev[col])-float(r[col]))>1e-10: raise ValueError(f"duplicate structural graph differs on {col}: {k}")
    return list(keys.values())


def model_features(row, group):
    common=["n_nodes"]
    groups={
      "A_NULL":[],
      "B_GENERAL_STRUCTURE":["skeleton_precision","skeleton_recall","skeleton_f1","directed_precision","directed_recall","directed_f1","directed_shd","atomic_error_count"],
      "C_OFF_TASK":["offtask_error_count"],
      "D_TASK_RELATED":["task_error_count","task_fn","task_fp","task_rev","task_unres","task_support"],
      "E_GENERAL_PLUS_TASK":["skeleton_f1","directed_f1","directed_shd","atomic_error_count","task_error_count","task_fn","task_fp","task_rev","task_unres","task_support"],
      "F_STRUCTURE_PLUS_PATH":["skeleton_f1","directed_f1","directed_shd","atomic_error_count","task_error_count","task_fn","task_fp","task_rev","task_unres","task_support","xy_path"],
      "G_ORACLE_EFFECT_DIAGNOSTICS":["skeleton_f1","directed_f1","directed_shd","atomic_error_count","task_error_count","task_fn","task_fp","task_rev","task_unres","task_support","xy_path","abs_effect_magnitude_error","effect_sign_error"]}
    cols=common+groups[group]
    return np.array([float(row[c]) if row[c] is not None else np.nan for c in cols],float)


def grouped_folds(rows, nfold=5):
    groups=sorted({r["scm_id"] for r in rows}); buckets=[groups[i::nfold] for i in range(nfold)]
    for val in buckets:
        tr=set(groups)-set(val)
        if tr & set(val): raise ValueError("SCM leakage between grouped folds")
        yield [r for r in rows if r["scm_id"] in tr],[r for r in rows if r["scm_id"] in set(val)]


def weights_by_scm(rows):
    counts=defaultdict(int)
    for r in rows: counts[r["scm_id"]]+=1
    return np.array([1.0/counts[r["scm_id"]] for r in rows],float)


def fit_ridge(x,y,w,alpha):
    mu=np.average(x,axis=0,weights=w); sd=np.sqrt(np.average((x-mu)**2,axis=0,weights=w)); sd[sd<1e-12]=1
    z=(x-mu)/sd; ym=np.average(y,weights=w); zy=y-ym
    # Weighted ridge with unpenalized intercept; alpha fixed by contract.
    zw=z*np.sqrt(w[:,None]); yw=zy*np.sqrt(w)
    beta=np.linalg.solve(zw.T@zw+alpha*np.eye(z.shape[1]),zw.T@yw)
    return lambda xx: ym+((xx-mu)/sd)@beta


def regression_metrics(y,p,w):
    mae=float(np.average(np.abs(y-p),weights=w)); rmse=float(np.sqrt(np.average((y-p)**2,weights=w))); mean=float(np.average(y,weights=w)); den=float(np.average((y-mean)**2,weights=w)); num=float(np.average((y-p)**2,weights=w)); r2=1-num/den if den else None
    def ranks(v):
        order=np.argsort(v,kind="mergesort"); out=np.empty(len(v),float); i=0
        while i<len(v):
            j=i+1
            while j<len(v) and v[order[j]]==v[order[i]]: j+=1
            out[order[i:j]]=(i+j-1)/2+1; i=j
        return out
    ry,rp=ranks(y),ranks(p)
    rank=float(np.corrcoef(ry,rp)[0,1]) if len(y)>1 and np.std(ry)>0 and np.std(rp)>0 else None
    return {"mae":mae,"rmse":rmse,"r2":r2,"rank_corr_approx":None if rank is None else float(rank)}


def run_predictive_s2(graph_rows):
    unique=deduplicate_graphs(graph_rows)
    dev=[r for r in unique if r["cohort"]=="C_DEVELOPMENT"]; held=[r for r in unique if r["cohort"]=="C_HELDOUT"]
    models=["A_NULL","B_GENERAL_STRUCTURE","C_OFF_TASK","D_TASK_RELATED","E_GENERAL_PLUS_TASK","F_STRUCTURE_PLUS_PATH","G_ORACLE_EFFECT_DIAGNOSTICS"]
    results=[]; prediction_store={}
    for name in models:
        # Development grouped CV selects alpha and gives out-of-fold predictions.
        alpha_scores={a:[] for a in (.01,.1,1,10,100)}
        for tr,va in grouped_folds(dev):
            yy=np.array([r["regret"] for r in tr]); wy=weights_by_scm(tr); yv=np.array([r["regret"] for r in va]); wv=weights_by_scm(va)
            if name=="A_NULL":
                pred=np.full(len(va),np.average(yy,weights=wy));
                for a in alpha_scores: alpha_scores[a].append(float(np.average(abs(yv-pred),weights=wv)))
            else:
                x=np.vstack([model_features(r,name) for r in tr]); xv=np.vstack([model_features(r,name) for r in va])
                # Missing diagnostic features are imputed from the training fold only.
                med=np.nanmedian(x,axis=0); med=np.where(np.isfinite(med),med,0); x=np.where(np.isfinite(x),x,med); xv=np.where(np.isfinite(xv),xv,med)
                for a in alpha_scores:
                    f=fit_ridge(x,yy,wy,a); pp=np.maximum(0,f(xv)); alpha_scores[a].append(float(np.average(abs(yv-pp),weights=wv)))
        alpha=min(alpha_scores,key=lambda a:np.mean(alpha_scores[a]))
        # OOF selected model metrics.
        oof=[]
        for tr,va in grouped_folds(dev):
            yy=np.array([r["regret"] for r in tr]); wy=weights_by_scm(tr); yv=np.array([r["regret"] for r in va]); wv=weights_by_scm(va)
            if name=="A_NULL": pp=np.full(len(va),np.average(yy,weights=wy))
            else:
                x=np.vstack([model_features(r,name) for r in tr]); xv=np.vstack([model_features(r,name) for r in va]); med=np.nanmedian(x,axis=0); med=np.where(np.isfinite(med),med,0); x=np.where(np.isfinite(x),x,med); xv=np.where(np.isfinite(xv),xv,med); pp=np.maximum(0,fit_ridge(x,yy,wy,alpha)(xv))
            oof.extend((r["scm_id"],float(r["regret"]),float(q)) for r,q in zip(va,pp))
        # Fit on Development, one locked transfer evaluation on historical Held-out.
        y=np.array([r["regret"] for r in dev]); w=weights_by_scm(dev); yh=np.array([r["regret"] for r in held]); wh=weights_by_scm(held)
        if name=="A_NULL": ph=np.full(len(held),np.average(y,weights=w))
        else:
            x=np.vstack([model_features(r,name) for r in dev]); xh=np.vstack([model_features(r,name) for r in held]); med=np.nanmedian(x,axis=0); med=np.where(np.isfinite(med),med,0); x=np.where(np.isfinite(x),x,med); xh=np.where(np.isfinite(xh),xh,med); ph=np.maximum(0,fit_ridge(x,y,w,alpha)(xh))
        oof_ids=[z[0] for z in oof]
        oof_weight_map=defaultdict(int)
        for sid in oof_ids:oof_weight_map[sid]+=1
        oof_weights=np.array([1.0/oof_weight_map[sid] for sid in oof_ids])
        dm=regression_metrics(np.array([z[1] for z in oof]),np.array([z[2] for z in oof]),oof_weights)
        hm=regression_metrics(yh,ph,wh)
        results.append({"model":name,"selected_alpha":alpha,"development_grouped_cv_mae":dm["mae"],"development_grouped_cv_rmse":dm["rmse"],"development_grouped_cv_r2":dm["r2"],"heldout_scm_balanced_mae":hm["mae"],"heldout_scm_balanced_rmse":hm["rmse"],"heldout_oos_r2":hm["r2"],"heldout_spearman_approx":hm["rank_corr_approx"],"n_development_scm":len({r['scm_id'] for r in dev}),"n_heldout_scm":len({r['scm_id'] for r in held}),"n_dev_graphs":len(dev),"n_heldout_graphs":len(held),"status":"post-hoc grouped prediction; fixed historical heldout"})
        prediction_store[name]=dict(y=yh.tolist(),pred=ph.tolist(),ids=[r["scm_id"] for r in held])
    return results,unique,prediction_store


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    cohorts,hashes=read_cohorts()
    s1,graphs=s1_and_s2(cohorts)
    s1agg,s1contr=summarize_s1(s1)
    model_results,unique_graphs,preds=run_predictive_s2(graphs)
    save_csv(OUT/"s1_unit_metrics.csv",s1); save_csv(OUT/"s1_aggregate.csv",s1agg); save_csv(OUT/"s1_primary_contrasts.csv",s1contr)
    save_csv(OUT/"s2_unique_graph_metrics.csv",unique_graphs); save_csv(OUT/"s2_model_validation.csv",model_results)
    summary={"status":"COMPLETED_POST_HOC_SUPPLEMENTARY_ANALYSIS","classification":"POST_HOC_SUPPLEMENTARY_DECISION_ROBUSTNESS_AND_METRIC_VALIDATION","cohorts":{k:len(v) for k,v in cohorts.items()},"source_sha256":hashes,"s1":{"n_rows":len(s1),"n_aggregate_rows":len(s1agg),"primary_contrasts":s1contr,"analysis_unit":"original SCM, paired"},"s2":{"stored_policy_budget_rows":len(graphs),"unique_structural_graph_rows":len(unique_graphs),"predictive_models":model_results,"unit":"unique SCM-graph, SCM-balanced"},"no_new_scm_or_g0":True,"no_new_intervention_samples":True,"sid_aid":"SID_AID_NOT_RUN_WITH_DOCUMENTED_REASON: no verified compatible implementation/fixture included in this frozen environment; core structural metrics proceed."}
    (OUT/"supplementary_summary.json").write_text(json.dumps(summary,indent=2,allow_nan=False),encoding="utf-8")
    print(json.dumps(summary,indent=2,allow_nan=False))


if __name__=="__main__": main()

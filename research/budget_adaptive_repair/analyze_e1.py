"""Read-only Research E E1 analysis over the original C ledgers and D summaries."""
from __future__ import annotations

import csv
import hashlib
import json
import os
import sqlite3
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / "outputs"
DATA_ROOT = Path(os.environ.get("DAT_RESEARCH_ROOT", "C:/DAT_RESEARCH"))
DEV = DATA_ROOT / "research-c/development/development-20261123-seed-2026112301-v1/research_c_cohort.sqlite"
HELD = DATA_ROOT / "research-c/heldout/independent-evaluation-20261123-seed-2026112303-v1/research_c_cohort.sqlite"
D_AUDIT = DATA_ROOT / "research-d/final-reaudit-20261126.json"
SEED = 2026112601
B = 10_000

def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def load_c(path: Path, cohort: str):
    con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    con.execute("PRAGMA query_only=ON")
    units = []
    for scm_id, status, raw, result_hash in con.execute("SELECT scm_id,status,result_json,result_sha256 FROM scms ORDER BY ordinal"):
        outer = json.loads(raw)
        payload = outer["payload"]
        body = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode()
        assert hashlib.sha256(body).hexdigest() == outer["payload_sha256"]
        assert status == "COMPLETED"
        budgets = payload["e2e_result"]["budgets"]
        assert [x["budget"] for x in budgets] == list(range(5))
        for budget_row in budgets:
            assert len(budget_row["policies"]) == 17
            for p in budget_row["policies"]:
                assert p["status"] == "OK" and p["evaluation_status"] == "RESEARCH_OK"
                ev = p["evaluation"]
                assert ev is not None and len(ev["truth_rows"]) == 5
                errors = p["final_error_counts"]
                units.append({"cohort": cohort, "scm_id": scm_id, "budget": p["budget"], "policy": p["policy_id"],
                              "loss": float(ev["regret"]), "cost": float(p["total_edit_cost"]),
                              "unused": float(p["unused_budget"]), "task_edits": float(p["selected_edit_counts_by_metric"]["M4"]),
                              "offtask_edits": float(sum(p["selected_edit_counts_by_metric"][m] for m in ("M1","M2","M3"))),
                              "initial_errors": int(p["initial_error_count"]),
                              "remaining_errors": int(sum(sum(v.values()) for v in errors.values())),
                              "action": float(ev["selected_action"]), "changed_from_s0": bool(not p["same_action_as_S0"]),
                              "no_op": bool(p["total_edit_cost"] == 0), "stop_reason": p["stop_reason"],
                              "improved_vs_s0": float(ev["regret"]) < float(budgets[0]["policies"][0]["evaluation"]["regret"])-1e-12,
                              "worsened_vs_s0": float(ev["regret"]) > float(budgets[0]["policies"][0]["evaluation"]["regret"])+1e-12})
    con.close()
    return units

def load_d():
    d = json.loads(D_AUDIT.read_text(encoding="utf-8"))
    assert d["status"] == "PASS" and len(d["independent_policy_budget_curve"]) == 85
    rows = []
    for r in d["independent_policy_budget_curve"]:
        rows.append({"cohort":"D_FINAL","budget":r["budget"],"policy":r["policy"],
                     "loss":r["mean_bias_corrected_loss"],"cost":r["mean_edit_cost"],
                     "task_edits":r["mean_task_zone_edits"],"offtask_edits":r["mean_off_task_edits"],
                     "no_op_rate":r["no_op_rate"],"unused_budget_rate":r["unused_budget_rate"]})
    return rows, d

def mean_ci(values, rng):
    a=np.asarray(values,dtype=float); n=len(a)
    idx=rng.integers(0,n,size=(B,n))
    means=a[idx].mean(axis=1)
    return float(a.mean()), float(np.quantile(means,.025)), float(np.quantile(means,.975))

def write_csv(path, rows):
    if not rows: return
    with path.open("w",newline="",encoding="utf-8") as f:
        fields=list(dict.fromkeys(k for row in rows for k in row))
        w=csv.DictWriter(f,fieldnames=fields,extrasaction="raise"); w.writeheader(); w.writerows(rows)

def pareto(rows, include_d_graphfree=False):
    pts=[]
    for r in rows:
        pts.append({"cohort":r["cohort"],"policy":r["policy"],"budget":r["budget"],"cost":r["cost"],"loss":r["loss"]})
    if include_d_graphfree:
        pts.append({"cohort":"D_FINAL","policy":"GRAPH_FREE_ASSOCIATION","budget":0,"cost":0.0,"loss":0.7893621879206892})
    out=[]
    for p in pts:
        dominated=any(q["cost"]<=p["cost"]+1e-12 and q["loss"]<=p["loss"]+1e-12 and
                      (q["cost"]<p["cost"]-1e-12 or q["loss"]<p["loss"]-1e-12) for q in pts if q is not p)
        if not dominated: out.append(p)
    return sorted(out,key=lambda x:(x["cost"],x["loss"],x["policy"],x["budget"]))

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    cdev=load_c(DEV,"C_DEVELOPMENT"); cho=load_c(HELD,"C_HELDOUT")
    drows,d=load_d()
    assert len(cdev)==64*17*5 and len(cho)==200*17*5
    write_csv(OUT/"c_development_unit_results.csv",cdev)
    write_csv(OUT/"c_heldout_unit_results.csv",cho)
    write_csv(OUT/"d_final_aggregate_results.csv",drows)
    rng=np.random.default_rng(SEED)
    summaries=[]; marginals=[]
    for cohort, rows in (("C_DEVELOPMENT",cdev),("C_HELDOUT",cho)):
        for policy in sorted({r['policy'] for r in rows}):
            byb={b:[r for r in rows if r['policy']==policy and r['budget']==b] for b in range(5)}
            for b, vals in byb.items():
                loss=[r['loss'] for r in vals]; m,lo,hi=mean_ci(loss,rng)
                summaries.append({"cohort":cohort,"analysis_unit":"SCM","n":len(vals),"policy":policy,"budget":b,
                    "mean_loss":m,"median_loss":float(np.median(loss)),"sd_loss":float(np.std(loss,ddof=1)),
                    "q25_loss":float(np.quantile(loss,.25)),"q75_loss":float(np.quantile(loss,.75)),"bootstrap95_lo":lo,"bootstrap95_hi":hi,
                    "mean_cost":float(np.mean([r['cost'] for r in vals])),"mean_unused":float(np.mean([r['unused'] for r in vals])),
                    "mean_task_edits":float(np.mean([r['task_edits'] for r in vals])),"mean_offtask_edits":float(np.mean([r['offtask_edits'] for r in vals])),
                    "remaining_errors":float(np.mean([r['remaining_errors'] for r in vals])),"action_change_rate":float(np.mean([r['changed_from_s0'] for r in vals])),
                    "improved_vs_s0":float(np.mean([r['improved_vs_s0'] for r in vals])),"worsened_vs_s0":float(np.mean([r['worsened_vs_s0'] for r in vals])),
                    "no_op_rate":float(np.mean([r['no_op'] for r in vals]))})
            for b in range(1,5):
                prev=byb[b-1]; cur=byb[b]; assert [x['scm_id'] for x in prev]==[x['scm_id'] for x in cur]
                delta=np.array([y['loss']-x['loss'] for x,y in zip(prev,cur)])
                costdelta=np.array([y['cost']-x['cost'] for x,y in zip(prev,cur)])
                benefit=-delta; mean_b,lo,hi=mean_ci(benefit,rng); denom=float(costdelta.mean())
                marginals.append({"cohort":cohort,"unit":"SCM paired","policy":policy,"from_budget":b-1,"to_budget":b,
                    "marginal_benefit":mean_b,"bootstrap95_lo":lo,"bootstrap95_hi":hi,"mean_added_edits":denom,
                    "benefit_per_added_edit":(mean_b/denom if abs(denom)>1e-15 else None),
                    "no_added_edit_fraction":float(np.mean(costdelta==0)),"improved_fraction":float(np.mean(benefit>1e-12)),
                    "worsened_fraction":float(np.mean(benefit< -1e-12)),"unchanged_fraction":float(np.mean(np.abs(benefit)<=1e-12)),
                    "additional_edit_but_no_loss_change_fraction":float(np.mean((costdelta>0)&(np.abs(benefit)<=1e-12)))})
    # D has only locked aggregate curve; keep it separate and don't invent unit-level uncertainty.
    for policy in sorted({r['policy'] for r in drows}):
        byb={r['budget']:r for r in drows if r['policy']==policy}
        for b,r in byb.items():
            summaries.append({"cohort":"D_FINAL","analysis_unit":"aggregate of 200 G0; no unit rows in audit artifact","n":200,
                "policy":policy,"budget":b,"mean_loss":r['loss'],"mean_cost":r['cost'],"mean_task_edits":r['task_edits'],
                "mean_offtask_edits":r['offtask_edits'],"no_op_rate":r['no_op_rate'],"unused_budget_rate":r['unused_budget_rate']})
        for b in range(1,5):
            p,r=byb[b-1],byb[b]; benefit=p['loss']-r['loss']; dd=r['cost']-p['cost']
            marginals.append({"cohort":"D_FINAL","unit":"published aggregate only","policy":policy,"from_budget":b-1,"to_budget":b,
                "marginal_benefit":benefit,"mean_added_edits":dd,"benefit_per_added_edit":benefit/dd if dd else None,
                "uncertainty":"NOT_RECOMPUTABLE: no G0-level rows / response vectors in accessible audit artifact"})
    write_csv(OUT/"budget_policy_summary.csv",summaries); write_csv(OUT/"marginal_benefit.csv",marginals)
    front=[]
    for cohort, rows in (("C_DEVELOPMENT",cdev),("C_HELDOUT",cho),("D_FINAL",drows)):
        agg=[]
        if cohort.startswith("C_"):
            for p in sorted({x['policy'] for x in rows}):
                for b in range(5):
                    xs=[x for x in rows if x['policy']==p and x['budget']==b]
                    agg.append({"cohort":cohort,"policy":p,"budget":b,"cost":float(np.mean([x['cost'] for x in xs])),"loss":float(np.mean([x['loss'] for x in xs]))})
        else: agg=rows
        front.extend(pareto(agg,include_d_graphfree=cohort=="D_FINAL"))
    write_csv(OUT/"pareto_frontiers.csv",front)
    fixed=[]
    for cohort, rows, maxb in (("C_DEVELOPMENT",cdev,7),("C_HELDOUT",cho,9),("D_FINAL",drows,4)):
        agg=[]
        for p in sorted({x['policy'] for x in rows}):
            for b in sorted({x['budget'] for x in rows if x['policy']==p}):
                if b>maxb: continue
                xs=[x for x in rows if x['policy']==p and x['budget']==b]
                agg.append({"cohort":cohort,"policy":p,"budget":b,"cost":float(np.mean([x['cost'] for x in xs])),"loss":float(np.mean([x['loss'] for x in xs]))})
        if cohort=='D_FINAL': agg.append({"cohort":cohort,"policy":"GRAPH_FREE_ASSOCIATION","budget":0,"cost":0.0,"loss":0.7893621879206892})
        for cap in range(maxb+1):
            candidates=[x for x in agg if x['budget']<=cap]
            for x in pareto(candidates): fixed.append({"frontier":"FIXED_MAX_BUDGET","max_budget":cap,**x})
        for x in pareto(agg): fixed.append({"frontier":"CROSS_BUDGET","max_budget":maxb,**x})
    write_csv(OUT/"fixed_and_cross_budget_frontiers.csv",fixed)
    # Exact supported-line breakpoints for the loss + lambda*edit-count objective.
    breakpoints=[]
    for cohort in ("C_DEVELOPMENT","C_HELDOUT","D_FINAL"):
        candidates=[{"policy":x['policy'],"budget":x['budget'],"cost":x['mean_cost'],"loss":x['mean_loss']}
                    for x in summaries if x['cohort']==cohort]
        if cohort=='D_FINAL': candidates.append({"policy":"GRAPH_FREE_ASSOCIATION","budget":0,"cost":0.0,"loss":0.7893621879206892})
        points={0.0}
        for i,a in enumerate(candidates):
            for b in candidates[i+1:]:
                dc=a['cost']-b['cost']
                if abs(dc)<1e-14: continue
                lam=(b['loss']-a['loss'])/dc
                if lam>=0 and np.isfinite(lam): points.add(float(lam))
        vals=sorted(points)
        bounds=[0.0]+[v for v in vals if v>0]
        for j,left in enumerate(bounds):
            right=bounds[j+1] if j+1<len(bounds) else float('inf')
            probe=(left+right)/2 if np.isfinite(right) else left+max(1.0,left)
            obj=[x['loss']+probe*x['cost'] for x in candidates]; best=min(obj)
            winners=[x for x,v in zip(candidates,obj) if abs(v-best)<1e-10]
            breakpoints.append({"cohort":cohort,"lambda_left":left,"lambda_right":right,
                "optimal_candidates":";".join(f"{x['policy']}@B{x['budget']}" for x in winners),"probe_lambda":probe})
    write_csv(OUT/"lambda_exact_intervals.csv",breakpoints)
    # Cross-budget frontier inclusion frequencies under paired SCM bootstrap (C only).
    frontier_stability=[]; rs=np.random.default_rng(2026112602)
    for cohort,rows,n in (("C_DEVELOPMENT",cdev,64),("C_HELDOUT",cho,200)):
        ids=sorted({x['scm_id'] for x in rows}); idx={v:i for i,v in enumerate(ids)}
        candidates=[]; matrices=[]
        for policy in sorted({x['policy'] for x in rows}):
            for b in range(5):
                xs=[x for x in rows if x['policy']==policy and x['budget']==b]
                loss=np.zeros(n); cost=np.zeros(n)
                for x in xs: loss[idx[x['scm_id']]]=x['loss'];cost[idx[x['scm_id']]]=x['cost']
                candidates.append((policy,b));matrices.append((loss,cost))
        losses=np.stack([x[0] for x in matrices]); costs=np.stack([x[1] for x in matrices]); counts=np.zeros(len(candidates),dtype=int)
        for _ in range(B):
            take=rs.integers(0,n,size=n); l=losses[:,take].mean(axis=1);c=costs[:,take].mean(axis=1)
            dominated=np.zeros(len(candidates),dtype=bool)
            for i in range(len(candidates)):
                mask=(c<=c[i]+1e-12)&(l<=l[i]+1e-12)&((c<c[i]-1e-12)|(l<l[i]-1e-12))
                if mask.any(): dominated[i]=True
            counts+=~dominated
        for (policy,b),count in zip(candidates,counts): frontier_stability.append({"cohort":cohort,"policy":policy,"budget":b,"frontier_inclusion_probability":count/B,"bootstrap_replicates":B,"unit":"paired SCM"})
    write_csv(OUT/"pareto_bootstrap_stability.csv",frontier_stability)
    # Held-out B=4 M4 versus Full Greedy leave-one-out sign sensitivity.
    loo=[]
    for policy in ("M4","M1+M2+M3+M4"):
        xs=[x for x in cho if x['policy']==policy and x['budget']==4]
        a=np.array([x['loss'] for x in xs])
        for i,x in enumerate(xs):
            loo.append({"cohort":"C_HELDOUT","budget":4,"policy":policy,"left_out_scm_id":x['scm_id'],"loo_mean_regret":float(np.delete(a,i).mean())})
    write_csv(OUT/"heldout_b4_leave_one_out.csv",loo)
    # lambda optima and exact pairwise breakpoints
    lambda_rows=[]
    grids=[0,.0001,.001,.005,.01,.02,.05,.10,.25]
    for cohort in ("C_DEVELOPMENT","C_HELDOUT","D_FINAL"):
        source=[x for x in summaries if x['cohort']==cohort and x['budget'] is not None]
        if cohort.startswith('C_'):
            candidates=[{"policy":x['policy'],"budget":x['budget'],"loss":x['mean_loss'],"cost":x['mean_cost']} for x in source]
        else:
            candidates=[{"policy":x['policy'],"budget":x['budget'],"loss":x['mean_loss'],"cost":x['mean_cost']} for x in source]
            candidates.append({"policy":"GRAPH_FREE_ASSOCIATION","budget":0,"loss":0.7893621879206892,"cost":0.0})
        for lam in grids:
            vals=[x['loss']+lam*x['cost'] for x in candidates]; opt=min(vals)
            for x,v in zip(candidates,vals):
                if abs(v-opt)<=1e-12: lambda_rows.append({"cohort":cohort,"lambda":lam,"policy":x['policy'],"budget":x['budget'],"objective":v,"status":"OPTIMAL_TIE" if sum(abs(z-opt)<=1e-12 for z in vals)>1 else "OPTIMAL"})
    write_csv(OUT/"lambda_optima.csv",lambda_rows)
    summary={"status":"E1_ANALYZED_WITH_D_UNIT_LEVEL_LIMITATION","source_hashes":{"c_development_cohort":sha(DEV),"c_development_proposal":sha(DEV.with_name('research_c_proposal_stage.sqlite')),"c_heldout_cohort":sha(HELD),"c_heldout_proposal":sha(HELD.with_name('research_c_proposal_stage.sqlite')),"d_local_audit":sha(D_AUDIT)},
      "rows":{"c_development":len(cdev),"c_heldout":len(cho),"d_aggregate":len(drows)},"bootstrap":{"replicates":B,"seed":SEED,"unit":"paired SCM for C; no new D bootstrap"},
      "d_limit":"Only 85 aggregate policy-budget rows and five action summary rows in the locally accessible final audit JSON; no per-G0 recommendations or raw response vectors found in the designated local Research D store. E1 D paired variability cannot be recomputed; E2/E3 D extensions blocked.",
      "d_audit_status":d['status'],"generated_outputs":[p.name for p in OUT.iterdir()]}
    (OUT/"e1_summary.json").write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps(summary,indent=2))

if __name__=='__main__': main()

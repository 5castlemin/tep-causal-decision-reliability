"""Hash-locked S4-1B reaggregation; consumes saved outcomes only."""
from __future__ import annotations
import csv, hashlib, itertools, json, os
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
CONTRACT = json.loads((HERE / "retrospective_contract.json").read_text(encoding="utf-8-sig"))
ROOT = Path(os.environ.get("S4_PILOT_INPUT", CONTRACT["input_root"]))
OUT = HERE / "outputs_attempt4"
PRIVATE_OUT = Path(os.environ.get("S4_RETROSPECTIVE_PRIVATE_OUT", r"C:\\DAT_RESEARCH\\research-s4\\s4-1b-retrospective-20261127-v1"))
T = tuple(f"T{i}" for i in range(1, 7))
SETS = tuple(s for n in range(1, 7) for s in itertools.combinations(T, n))
TOL = 1e-12

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def load(name):
    path = ROOT / name
    if not path.is_file(): raise FileNotFoundError(path)
    actual = sha(path)
    expected = CONTRACT["input_sha256"][name]
    if actual != expected: raise ValueError(f"input hash mismatch {name}: {actual}")
    return json.loads(path.read_text(encoding="utf-8-sig"))
def write_csv(path, rows):
    if not rows: path.write_text("", encoding="utf-8"); return
    with path.open("w", newline="", encoding="utf-8") as f:
        fields=list(dict.fromkeys(key for row in rows for key in row))
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)
def boot_summary(values, ix):
    a=np.asarray(values,dtype=float)
    boot=a[ix].mean(axis=1)
    return {"mean":float(a.mean()),"median":float(np.median(a)),"sd":float(a.std(ddof=1)),
            "ci95_low":float(np.quantile(boot,.025)),"ci95_high":float(np.quantile(boot,.975)),
            "better":int(np.sum(a < -TOL)),"worse":int(np.sum(a > TOL)),"tie":int(np.sum(np.abs(a)<=TOL))}

def main():
    names=list(CONTRACT["input_sha256"])
    data={name:load(name) for name in names}
    inputs=data["pilot_inputs_private.json"]
    candidates=data["candidate_values_private.json"]
    saved_policies=data["policy_results_private.json"]
    units=data["unit_results_private.json"]
    rec=data["recommendation_manifest_private.json"]
    if len(inputs)!=64 or len(units)!=64: raise ValueError("pilot unit count mismatch")
    recmap={(r['cohort'],r['scm_id'],r['graph_hash']):r for r in rec}
    unitmap={(r['cohort'],r['scm_id']):r for r in units}
    candmap={}
    for r in candidates: candmap.setdefault((r['cohort'],r['scm_id']),[]).append(r)
    policy_map={(r['cohort'],r['scm_id'],r['policy'],int(r['budget'])):r for r in saved_policies}
    # B1 selected graph is chosen using only saved structural gains; outcomes are joined after selection.
    b1=[]
    for cohort,sid in sorted(unitmap):
        rows=candmap.get((cohort,sid),[])
        for subset in SETS:
            ranked=[]
            for r in rows:
                score=sum(float(r[f'{t}_gain']) for t in subset)/len(subset)
                m4=float(r['M4_gain'])
                ranked.append((score,m4,r))
            if not ranked:
                base=policy_map[(cohort,sid,'S0',0)]
                b1.append({"cohort":cohort,"scm_id":sid,"policy":"T_GREEDY:"+'+'.join(subset),"budget":1,
                    "graph_hash":base['graph_hash'],"cost":0,"regret":base['regret'],"selected_k":base['selected_k'],"action_changed_from_s0":False,"n_initial_m4_candidates":0})
                continue
            best_t=max(x[0] for x in ranked)
            tied=[x for x in ranked if abs(x[0]-best_t)<=TOL]
            best_m=max(x[1] for x in tied)
            tied=[x for x in tied if abs(x[1]-best_m)<=TOL]
            _,_,r=min(tied,key=lambda x:(json.loads(x[2]['pair']),x[2]['operation']))
            out=recmap[(cohort,sid,r['graph_hash'])]
            b1.append({"cohort":cohort,"scm_id":sid,"policy":"T_GREEDY:"+'+'.join(subset),"budget":1,
                "graph_hash":r['graph_hash'],"cost":1,"regret":float(unitmap[(cohort,sid)]['s0_regret'])-float(r['regret_gain']),
                "selected_k":out['selected_k'],"action_changed_from_s0":bool(r['action_changed']),"n_initial_m4_candidates":len(rows),
                "selected_pair":r['pair'],"selected_operation":r['operation']})
    # Add saved M4, S0, Full Greedy and B2 T outcomes for redundancy and benchmarks.
    compare=[]
    for cohort in ('general','opportunity_rich_diagnostic'):
        sids=sorted(sid for c,sid in unitmap if c==cohort)
        rng=np.random.default_rng(2026112702)
        ix=rng.integers(0,len(sids),size=(10000,len(sids)))
        policies=[]
        for p in b1:
            if p['cohort']==cohort: policies.append(p)
        for p in saved_policies:
            if p['cohort']==cohort and (p['budget'] in (1,2) and p['policy'] in ('M4','FULL_GREEDY') or p['budget']==2 and p['policy'].startswith('T_GREEDY:')):
                policies.append(p)
        bypol={}
        for p in policies: bypol.setdefault((p['policy'],int(p['budget'])),{})[p['scm_id']]=p
        for (pol,budget),pr in sorted(bypol.items()):
            if (pol,budget)==('M4',budget):
                continue
            ref=bypol.get(('M4',budget))
            if ref is None: continue
            d=[float(pr[s]['regret'])-float(ref[s]['regret']) for s in sids]
            sm=boot_summary(d,ix)
            costs=[float(pr[s]['cost']) for s in sids]
            action=[bool(pr[s]['selected_k']!=ref[s]['selected_k']) for s in sids]
            # Distinct final graph hashes and selected actions measure separate redundancy dimensions.
            compare.append({"cohort":cohort,"policy":pol,"budget":budget,
                "n_scm":len(sids),**sm,"mean_edit_cost":float(np.mean(costs)),"action_change_vs_M4":float(np.mean(action)),
                "same_graph_as_M4":float(np.mean([pr[s]['graph_hash']==ref[s]['graph_hash'] for s in sids])),
                "same_regret_as_M4":float(np.mean([abs(float(pr[s]['regret'])-float(ref[s]['regret']))<=TOL for s in sids]))})
    # Initial opportunity and budget-to-K diagnostics.
    krows=[]
    for (cohort,sid),u in sorted(unitmap.items()):
        k=int(u['initial_m4_candidates'])
        krows.append({"cohort":cohort,"scm_id":sid,"K_initial":k,"B1_over_K":(1/k if k else None),"B2_over_K":(2/k if k else None),
                      "n_feasible_two_edit_orders":u['n_feasible_two_edit_orders'],"M4_B2_equals_le2_optimum":abs(float(u['m4_b2_regret'])-float(u['expost_le2_regret']))<=TOL,
                      "M4_B2_optimality_gap":float(u['m4_b2_regret'])-float(u['expost_le2_regret'])})
    aggregate=[]
    groups={}
    for r in b1: groups.setdefault((r['cohort'],r['policy']),[]).append(r)
    for (cohort,pol),rows in sorted(groups.items()):
        vals=np.array([r['regret'] for r in rows]); aggregate.append({"cohort":cohort,"policy":pol,"budget":1,"n_scm":len(rows),
          "mean_regret":float(vals.mean()),"median_regret":float(np.median(vals)),"sd_regret":float(vals.std(ddof=1)),
          "zero_regret_fraction":float(np.mean(np.abs(vals)<=TOL)),"mean_edit_cost":float(np.mean([r['cost'] for r in rows])),
          "action_change_rate":float(np.mean([r['action_changed_from_s0'] for r in rows]))})
    OUT.mkdir(exist_ok=False)
    PRIVATE_OUT.mkdir(parents=True, exist_ok=False)
    write_csv(PRIVATE_OUT/'b1_all_63_unit_recommendations.csv',b1)
    write_csv(PRIVATE_OUT/'opportunity_budget_unit_diagnostics.csv',krows)
    write_csv(OUT/'b1_all_63_policy_aggregates.csv',aggregate)
    write_csv(OUT/'policy_redundancy_b1_b2.csv',compare)
    opportunity=[]
    for cohort in ('general','opportunity_rich_diagnostic'):
        rr=[r for r in krows if r['cohort']==cohort]
        for b in (1,2,3,4):
            opportunity.append({'cohort':cohort,'n_scm':len(rr),'budget':b,'K_gt_B_count':sum(r['K_initial']>b for r in rr),'K_gt_B_fraction':sum(r['K_initial']>b for r in rr)/len(rr)})
    write_csv(OUT/'opportunity_budget_summary.csv',opportunity)
    summary={"analysis_id":CONTRACT['analysis_id'],"classification":"post_hoc_exploratory","n_units":64,"new_scm":0,"new_g0":0,"new_observation_rows":0,"new_intervention_rows":0,
      "B1_policy_rows":len(b1),"expected_B1_policy_rows":64*63,"input_hashes":{n:sha(ROOT/n) for n in names},"contracts":CONTRACT['analysis'],
      "cohorts":{}}
    for c in ('general','opportunity_rich_diagnostic'):
        kr=[x for x in krows if x['cohort']==c]
        kk=np.array([x['K_initial'] for x in kr])
        summary['cohorts'][c]={"n":len(kr),"K_mean":float(kk.mean()),"K_median":float(np.median(kk)),"K_min":int(kk.min()),"K_max":int(kk.max()),
           "K_distribution":{str(int(k)):int(np.sum(kk==k)) for k in sorted(set(kk))},"M4_B2_not_le2_optimal":int(sum(not x['M4_B2_equals_le2_optimum'] for x in kr))}
    (OUT/'retrospective_summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n',encoding='utf-8')
if __name__=='__main__': main()

"""Aggregate-only retrospective S6 replay of saved one-edit candidates."""
from __future__ import annotations
import argparse, csv, hashlib, itertools, json
from collections import defaultdict
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent
LOCK=HERE/'RESEARCH_S6_EXECUTION_LOCK.json'

TOL=1e-12; BOOT=10_000; SEED=2026112806; TYPES=("FN","FP","REV","UNRES")
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def canon(r): return tuple(r.get("pair",("",""))),str(r.get("operation",""))
def pick(rows,rule,order):
    if rule=="S0": return None
    if rule=="M4": pool=rows; score=lambda r:float(r["M4_gain"])
    elif rule=="T5":
        pool=[r for r in rows if float(r.get("T5_gain",0))>TOL]
        if not pool: return pick(rows,"M4",order)
        best=max(float(r["T5_gain"]) for r in pool); pool=[r for r in pool if best-float(r["T5_gain"])<=TOL]
        m4=max(float(r["M4_gain"]) for r in pool); pool=[r for r in pool if m4-float(r["M4_gain"])<=TOL]
        return min(pool,key=canon)
    elif rule=="TYPE":
        pool=[]
        for kind in order:
            pool=[r for r in rows if r.get("error_type",r.get("kind"))==kind and float(r["M4_gain"])>TOL]
            if pool: break
        if not pool: return pick(rows,"M4",order)
        score=lambda r:float(r["M4_gain"])
    elif rule=="ORACLE": pool=rows; score=lambda r:float(r.get("regret_gain",0))
    else: raise ValueError(rule)
    if not pool: return None
    best=max(score(r) for r in pool)
    if best<=TOL: return None
    return min((r for r in pool if best-score(r)<=TOL),key=canon)
def load(path, unit_path):
    groups=defaultdict(list)
    for r in json.loads(path.read_text(encoding="utf-8")): groups[str(r["scm_id"])].append(r)
    unit_ids=[str(r["scm_id"]) for r in json.loads(unit_path.read_text(encoding="utf-8"))]
    if len(unit_ids)!=len(set(unit_ids)): raise ValueError("duplicate unit IDs in cohort inputs")
    if set(groups)-set(unit_ids): raise ValueError("candidate SCM key absent from cohort inputs")
    return {s:sorted(groups.get(s,[]),key=canon) for s in unit_ids}
def write(path,rows):
    if not rows: raise ValueError(f"empty output {path}")
    with path.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--development',type=Path,required=True); ap.add_argument('--development-units',type=Path,required=True); ap.add_argument('--confirmation',type=Path,required=True); ap.add_argument('--confirmation-units',type=Path,required=True); ap.add_argument('--output',type=Path,required=True); a=ap.parse_args()
    if a.output.exists() and any(a.output.iterdir()): raise FileExistsError(f"refusing overwrite: {a.output}")
    lock=json.loads(LOCK.read_text(encoding='utf-8')); expected=lock['inputs']
    actual={'development_candidate_values_sha256':sha(a.development),'confirmation_candidate_values_sha256':sha(a.confirmation),'development_inputs_sha256':sha(a.development_units),'confirmation_inputs_sha256':sha(a.confirmation_units)}
    if actual!=expected: raise ValueError(f'S6 input hash mismatch: {actual}')
    cohorts=[("development80",load(a.development,a.development_units),a.development,80),("replication160",load(a.confirmation,a.confirmation_units),a.confirmation,160)]
    order=None; errors=[]; within_type=[]; aggregates=[]; contrasts=[]; redundancy=[]
    for label,units,src,expected in cohorts:
        sids=sorted(units)
        if len(sids)!=expected: raise ValueError(f"{label}: expected {expected} SCMs, got {len(sids)}")
        scm_type={t:[] for t in TYPES}; candidate_type={t:[] for t in TYPES}; by_scm_type={}
        for sid in sids:
            by=defaultdict(list)
            for r in units[sid]: by[r.get('error_type',r.get('kind'))].append(r)
            for t,rr in by.items():
                if t in scm_type:
                    vals=[float(r.get('regret_gain',0)) for r in rr]; scm_type[t].append(float(np.mean(vals))); candidate_type[t].extend(vals)
                    by_scm_type.setdefault(sid,{})[t]=float(np.mean(vals))
        if label=='development80':
            order=sorted(TYPES,key=lambda t:(-float(np.mean(scm_type[t])) if scm_type[t] else float('inf'),t))
        for t in TYPES:
            cv=np.asarray(candidate_type[t],float); sv=np.asarray(scm_type[t],float)
            support_ids=[s for s in sids if t in by_scm_type.get(s,{})]; sv=np.asarray([by_scm_type[s][t] for s in support_ids])
            rng=np.random.default_rng(SEED); ix=rng.integers(0,len(sv),size=(BOOT,len(sv))) if len(sv) else np.empty((0,0),dtype=int)
            ci=np.quantile(sv[ix].mean(axis=1),[.025,.975]) if len(sv) else [None,None]
            act=[bool(r.get('action_changed',False)) for s in sids for r in units[s] if r.get('error_type',r.get('kind'))==t]
            errors.append({'cohort':label,'error_type':t,'candidate_count':len(cv),'scm_support':len(sv),'candidate_weighted_mean_regret_reduction':float(cv.mean()) if len(cv) else None,'scm_balanced_mean_regret_reduction':float(sv.mean()) if len(sv) else None,'scm_clustered_ci95_low':float(ci[0]) if len(sv) else None,'scm_clustered_ci95_high':float(ci[1]) if len(sv) else None,'scm_balanced_median':float(np.median(sv)) if len(sv) else None,'positive_candidate_fraction':float((cv>TOL).mean()) if len(cv) else None,'negative_candidate_fraction':float((cv< -TOL).mean()) if len(cv) else None,'zero_candidate_fraction':float((np.abs(cv)<=TOL).mean()) if len(cv) else None,'action_change_candidate_rate':float(np.mean(act)) if act else None,'type_rank_from_development':order.index(t)+1})
        for left,right in itertools.combinations(TYPES,2):
            shared=[s for s in sids if left in by_scm_type.get(s,{}) and right in by_scm_type.get(s,{})]
            if not shared: continue
            d=np.asarray([by_scm_type[s][left]-by_scm_type[s][right] for s in shared]); rng=np.random.default_rng(SEED); ix=rng.integers(0,len(d),size=(BOOT,len(d))); b=d[ix].mean(axis=1)
            within_type.append({'cohort':label,'left_type':left,'right_type':right,'n_shared_scms':len(d),'mean_within_scm_regret_reduction_difference':float(d.mean()),'ci95_pointwise_low':float(np.quantile(b,.025)),'ci95_pointwise_high':float(np.quantile(b,.975)),'left_higher_count':int((d>TOL).sum()),'left_lower_count':int((d< -TOL).sum()),'tie_count':int((np.abs(d)<=TOL).sum())})
        policies={'S0':'S0','FROZEN_M4_B1':'M4','TYPE_RANKED_M4_B1':'TYPE','T5_GUIDED_M4_B1':'T5','REGRET_ORACLE_B1':'ORACLE'}
        chosen={p:{} for p in policies}; deltas={p:{} for p in policies}
        for sid in sids:
            for policy,rule in policies.items():
                e=pick(units[sid],rule,order); chosen[policy][sid]=e
                deltas[policy][sid]=-float(e.get('regret_gain',0)) if e else 0.0
        for policy in policies:
            vals=np.array([deltas[policy][s] for s in sids]); edits=np.array([chosen[policy][s] is not None for s in sids])
            typecounts={t:sum(chosen[policy][s] is not None and chosen[policy][s].get('error_type',chosen[policy][s].get('kind'))==t for s in sids) for t in TYPES}
            aggregates.append({'cohort':label,'budget':1,'policy':policy,'n_scm':expected,'mean_regret_change_vs_S0':float(vals.mean()),'median_regret_change_vs_S0':float(np.median(vals)),'mean_regret_reduction_vs_S0':float(-vals.mean()),'mean_actual_edits':float(edits.mean()),'no_op_rate':float(1-edits.mean()),'selected_type_counts':json.dumps(typecounts,sort_keys=True)})
        rng=np.random.default_rng(SEED); ix=rng.integers(0,len(sids),size=(BOOT,len(sids)))
        for left,right in [('TYPE_RANKED_M4_B1','FROZEN_M4_B1'),('T5_GUIDED_M4_B1','FROZEN_M4_B1'),('TYPE_RANKED_M4_B1','T5_GUIDED_M4_B1'),('FROZEN_M4_B1','REGRET_ORACLE_B1')]:
            d=np.array([deltas[left][s]-deltas[right][s] for s in sids]); b=d[ix].mean(axis=1)
            better=int((d< -TOL).sum()); worse=int((d>TOL).sum())
            contrasts.append({'cohort':label,'left_policy':left,'right_policy':right,'budget':1,'n_scm':expected,'mean_regret_difference_left_minus_right':float(d.mean()),'median_regret_difference':float(np.median(d)),'ci95_pointwise_low':float(np.quantile(b,.025)),'ci95_pointwise_high':float(np.quantile(b,.975)),'left_better':better,'left_worse':worse,'tie':expected-better-worse,'bootstrap_replicates':BOOT,'bootstrap_seed':SEED})
        for left,right in itertools.combinations(('FROZEN_M4_B1','TYPE_RANKED_M4_B1','T5_GUIDED_M4_B1'),2):
            same=sum((chosen[left][s] is None and chosen[right][s] is None) or (chosen[left][s] is not None and chosen[right][s] is not None and canon(chosen[left][s])==canon(chosen[right][s])) for s in sids)
            redundancy.append({'cohort':label,'left_policy':left,'right_policy':right,'n_scm':expected,'same_selected_edit_count':same,'same_selected_edit_rate':same/expected,'both_noop_count':sum(chosen[left][s] is None and chosen[right][s] is None for s in sids)})
    a.output.mkdir(parents=True,exist_ok=True)
    write(a.output/'error_type_summary.csv',errors); write(a.output/'within_scm_type_contrasts.csv',within_type); write(a.output/'policy_budget_aggregates.csv',aggregates); write(a.output/'paired_policy_contrasts.csv',contrasts); write(a.output/'policy_redundancy.csv',redundancy)
    (a.output/'execution_manifest.json').write_text(json.dumps({'schema':'S6_SAVED_CANDIDATE_MANIFEST_V1','status':'EXECUTED','analysis_script_sha256':sha(Path(__file__)),'contract_lock_sha256':sha(LOCK),'cohorts':{k:len(v) for k,v,_,_ in cohorts},'bootstrap_replicates':BOOT,'bootstrap_seed':SEED,'type_priority_development_only':order,'input_sha256':actual,'scope':'retrospective B=1 replay from saved initial legal single-edit values; units without candidates retained as no-op; no new samples; intervals pointwise'},sort_keys=True,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'type_priority':order,'aggregate_rows':len(aggregates),'paired_contrasts':len(contrasts),'output':str(a.output)},sort_keys=True))
if __name__=='__main__': main()

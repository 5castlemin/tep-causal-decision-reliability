"""Retrospective B=1 policy matrix from saved S4 candidate rows only."""
from __future__ import annotations
import argparse, csv, hashlib, json
from pathlib import Path
import numpy as np
from scipy.stats import ttest_1samp
TOL=1e-12; BOOT=10_000; SEED=2026112810
KINDS=("FN","FP","REV","UNRES")
TMETRICS=tuple(f"T{i}_gain" for i in range(1,7))
def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''): h.update(b)
    return h.hexdigest()
def canon(r): return tuple(r.get('pair',('', ''))),str(r.get('operation',''))
def best(rows,score):
    if not rows:return None
    vals=[float(score(r)) for r in rows];top=max(vals)
    if top<=TOL:return None
    return min((r for r,v in zip(rows,vals) if top-v<=TOL),key=canon)
def best_tie(rows,score):
    """Canonical argmax without a positivity gate; secondary tie-break only."""
    if not rows:return None
    vals=[float(score(r)) for r in rows];top=max(vals)
    return min((r for r,v in zip(rows,vals) if top-v<=TOL),key=canon)
def frozen(rows):return best(rows,lambda r:r['M4_gain'])
def guided(rows,metric):
    pool=[r for r in rows if float(r[metric])>TOL]
    if not pool:return frozen(rows),True
    top=max(float(r[metric]) for r in pool);tied=[r for r in pool if top-float(r[metric])<=TOL]
    return best_tie(tied,lambda r:r['M4_gain']),False
def type_first(rows,kind):
    pool=[r for r in rows if r['kind']==kind and float(r['M4_gain'])>TOL]
    return (best(pool,lambda r:r['M4_gain']),False) if pool else (frozen(rows),True)
def write_csv(path,rows):
    if not rows:raise ValueError(f'empty output {path}')
    with Path(path).open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def holm(pvalues):
    order=sorted(range(len(pvalues)),key=lambda i:pvalues[i]);out=[1.0]*len(pvalues);running=0.0;m=len(pvalues)
    for rank,i in enumerate(order):running=max(running,min(1.0,(m-rank)*pvalues[i]));out[i]=running
    return out
def grouped_ridge_cv(ids,by):
    rows=[];groups=[];basefeat=[];types=[];ops=[];tfeat=[];y=[]
    for sid in ids:
        for r in by[sid]:
            rows.append(r);groups.append(sid);basefeat.append([float(r['M4_gain']),float(len(by[sid]))]);types.append(str(r['kind']));ops.append(str(r['operation']));tfeat.append([float(r[k]) for k in TMETRICS]);y.append(float(r['regret_gain']))
    if len(rows)<20:return [{'cohort':'development80','model':m,'status':'NOT_RUN_INSUFFICIENT_CANDIDATES'} for m in ['A','B','C']]
    ordered=sorted(set(groups));foldmap={sid:i%5 for i,sid in enumerate(ordered)};opcats=sorted(set(ops));kindcats=sorted(set(types))
    base=np.asarray(basefeat,float);opmat=np.asarray([[float(x==c) for c in opcats] for x in ops],float);typemat=np.asarray([[float(x==c) for c in kindcats] for x in types],float);tmat=np.asarray(tfeat,float);yy=np.asarray(y,float)
    mats={'A':np.column_stack([base,opmat]),'B':np.column_stack([base,opmat,typemat]),'C':np.column_stack([base,opmat,typemat,tmat])};preds={m:np.full(len(rows),np.nan) for m in mats}
    for fold in range(5):
        te=np.asarray([foldmap[s]==fold for s in groups]);tr=~te
        if not te.any() or not tr.any():continue
        gs=np.asarray(groups)[tr];counts={g:int(np.sum(gs==g)) for g in set(gs)};w=np.asarray([1/counts[g] for g in gs],float)
        for m,X in mats.items():
            mu=np.average(X[tr],axis=0,weights=w);sd=np.sqrt(np.average((X[tr]-mu)**2,axis=0,weights=w));sd=np.where(sd>1e-12,sd,1.);xt=(X[tr]-mu)/sd;xe=(X[te]-mu)/sd;ym=np.average(yy[tr],weights=w);beta=np.linalg.solve(xt.T@(w[:,None]*xt)+np.eye(xt.shape[1]),xt.T@(w*(yy[tr]-ym)));preds[m][te]=ym+xe@beta
    errors={m:{} for m in mats}
    for i,sid in enumerate(groups):
        for m in mats:
            if np.isfinite(preds[m][i]):errors[m].setdefault(sid,[]).append(abs(yy[i]-preds[m][i]))
    out=[]
    for m,d in errors.items():
        v=np.asarray([np.mean(e) for e in d.values()]);out.append({'cohort':'development80','model':m,'n_scms_with_oof_predictions':len(v),'candidate_rows':int(np.isfinite(preds[m]).sum()),'mean_scm_balanced_mae':float(v.mean()) if len(v) else None,'median_scm_mae':float(np.median(v)) if len(v) else None,'alpha':1.0,'folds':'deterministic 5-fold SCM grouped','features':{'A':'M4 gain, initial candidate count, operation indicators','B':'A + error-type indicators','C':'B + T1-T6 gains'}[m],'status':'POST_HOC_AUXILIARY'})
    return out
def main():
    ap=argparse.ArgumentParser()
    for n in ['development-candidates','development-inputs','development-units','replication-candidates','replication-inputs','replication-units','baseline-aggregates']:ap.add_argument('--'+n,type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    if a.output.exists() and any(a.output.iterdir()):raise FileExistsError(f'refusing overwrite {a.output}')
    expected={'development-candidates':'b6bad271d0b7154b873ebb081e31187969280dd53ac340bfa42039ab0cc5a477','development-inputs':'a6fe959b5d7fadd05a02321bd107e9265ff69dfe004a1e4c92a5e8847b6ee3cc','replication-candidates':'2005a1d16c9e740b2970a6d5b04f2aea0a30ebd72dbc6f9b78bc54a7a5be4b7b','replication-inputs':'65dbdc2befa7df610cb71912db6a94c6fb77542bdc3f45f10ae4641e5d0e8fe0'}
    actual={k:sha(getattr(a,k.replace('-','_'))) for k in expected}
    if actual!=expected:raise ValueError(f'locked S6 candidate/input hash mismatch: {actual}')
    cohorts=[]
    for label,cp,ip,up,n in [('development80',a.development_candidates,a.development_inputs,a.development_units,80),('replication160',a.replication_candidates,a.replication_inputs,a.replication_units,160)]:
        units=json.loads(ip.read_text(encoding='utf-8'));base=json.loads(up.read_text(encoding='utf-8'));cands=json.loads(cp.read_text(encoding='utf-8'));ids=[str(x['scm_id']) for x in units];baseby={str(x['scm_id']):x for x in base}
        if len(ids)!=n or len(set(ids))!=n or set(ids)!=set(baseby):raise ValueError(f'{label} unit key/count mismatch')
        by={s:[] for s in ids}
        for r in cands:
            s=str(r['scm_id'])
            if s not in by:raise ValueError(f'{label} candidate key mismatch')
            if any(k not in r for k in ('M4_gain','regret_gain','kind','pair','operation',*TMETRICS)):raise ValueError('candidate schema incomplete')
            x=dict(r);x['_FULL_T']=float(np.mean([float(x[k]) for k in TMETRICS]));by[s].append(x)
        if sum(map(len,by.values()))!=len(cands):raise ValueError('candidate accounting failure')
        cohorts.append((label,ids,by,baseby))
    # Outcome-ranked type priority is selected on Development only, SCM-balanced.
    dev=cohorts[0][2];means={k:float(np.mean([np.mean([float(r['regret_gain']) for r in dev[s] if r['kind']==k]) for s in dev if any(r['kind']==k for r in dev[s])])) for k in KINDS};order=sorted(KINDS,key=lambda k:(-means[k],k))
    policies=['FROZEN_M4','FN_FIRST_M4','FP_FIRST_M4','REV_FIRST_M4','UNRES_FIRST_M4','TYPE_RANKED_M4']+[f'T{i}_GUIDED_M4' for i in range(1,7)]+['FULL_T_GUIDED_M4','RANDOM_M4','EXPOST_SINGLE_EDIT_ORACLE']
    ag=[];pairs=[];choices=[];reg=[];rng=np.random.default_rng(SEED);old={}
    with a.baseline_aggregates.open(newline='',encoding='utf-8') as f:
        for r in csv.DictReader(f):
            if int(r.get('budget',1))==1:old[(r['cohort'],r['policy'])]=r
    for label,ids,by,baseby in cohorts:
        gain={p:{} for p in policies};sel={p:{} for p in policies};cost={p:{} for p in policies};act={p:{} for p in policies};fallback={p:0 for p in policies};typecnt={p:{k:0 for k in KINDS} for p in policies}
        for sid in ids:
            rows=by[sid];pick={'FROZEN_M4':(frozen(rows),False)}
            for k in KINDS:pick[f'{k}_FIRST_M4']=type_first(rows,k)
            typ=None
            for k in order:
                pool=[r for r in rows if r['kind']==k and float(r['M4_gain'])>TOL]
                if pool:typ=(best(pool,lambda r:r['M4_gain']),False);break
            pick['TYPE_RANKED_M4']=typ if typ else (frozen(rows),True)
            for i in range(1,7):pick[f'T{i}_GUIDED_M4']=guided(rows,f'T{i}_gain')
            pick['FULL_T_GUIDED_M4']=guided(rows,'_FULL_T')
            oracle=best(rows,lambda r:r['regret_gain'])
            for p,(e,fb) in pick.items():
                sel[p][sid]=e;gain[p][sid]=float(e['regret_gain']) if e else 0.;cost[p][sid]=int(e is not None);act[p][sid]=int(bool(e and e.get('action_changed',False)));fallback[p]+=int(fb)
                if e:typecnt[p][str(e['kind'])]+=1
            sel['RANDOM_M4'][sid]=None;gain['RANDOM_M4'][sid]=float(np.mean([float(r['regret_gain']) for r in rows])) if rows else 0.;cost['RANDOM_M4'][sid]=int(bool(rows));act['RANDOM_M4'][sid]=float(np.mean([bool(r.get('action_changed',False)) for r in rows])) if rows else 0.
            sel['EXPOST_SINGLE_EDIT_ORACLE'][sid]=oracle;gain['EXPOST_SINGLE_EDIT_ORACLE'][sid]=float(oracle['regret_gain']) if oracle else 0.;cost['EXPOST_SINGLE_EDIT_ORACLE'][sid]=int(oracle is not None);act['EXPOST_SINGLE_EDIT_ORACLE'][sid]=int(bool(oracle and oracle.get('action_changed',False)))
            if oracle:typecnt['EXPOST_SINGLE_EDIT_ORACLE'][str(oracle['kind'])]+=1
        s0=np.asarray([float(baseby[s].get('s0_regret',baseby[s].get('s0_mean_regret',0))) for s in ids],float)
        if not np.any(s0):raise ValueError(f'{label}: missing SCM S0 regret')
        for p in policies:
            g=np.asarray([gain[p][s] for s in ids]);c=np.asarray([cost[p][s] for s in ids]);ac=np.asarray([act[p][s] for s in ids]);r=s0-g
            ag.append({'cohort':label,'policy':p,'budget':1,'n_scm':len(ids),'candidate_scms':sum(bool(by[s]) for s in ids),'candidate_rows':sum(map(len,by.values())),'mean_regret':float(r.mean()),'median_regret':float(np.median(r)),'sd_regret':float(r.std(ddof=1)),'mean_regret_reduction_vs_s0':float(g.mean()),'mean_edit_count':float(c.mean()),'mean_unused_budget':float(1-c.mean()),'no_op_rate':float(1-c.mean()),'action_change_rate_or_expectation':float(ac.mean()),'fallback_count':fallback.get(p,0),'selected_type_counts':json.dumps(typecnt[p],sort_keys=True)})
        ix=rng.integers(0,len(ids),size=(BOOT,len(ids)));comp=[p for p in policies if p!='FROZEN_M4'];temp=[];ps=[]
        for p in comp:
            d=np.asarray([-(gain[p][s]-gain['FROZEN_M4'][s]) for s in ids]);b=d[ix].mean(axis=1);pv=float(ttest_1samp(d,0.).pvalue) if np.std(d,ddof=1)>0 else 1.;temp.append((p,d,b,pv));ps.append(pv)
        for (p,d,b,pv),ph in zip(temp,holm(ps)):
            better=int((d< -TOL).sum());worse=int((d>TOL).sum())
            pairs.append({'cohort':label,'left_policy':p,'right_policy':'FROZEN_M4','budget':1,'n_scm':len(ids),'mean_regret_difference_left_minus_right':float(d.mean()),'median_regret_difference':float(np.median(d)),'paired_bootstrap_95_low':float(np.quantile(b,.025)),'paired_bootstrap_95_high':float(np.quantile(b,.975)),'better':better,'worse':worse,'tie':len(ids)-better-worse,'p_paired_t_two_sided':pv,'p_holm_within_cohort_vs_m4':float(ph),'bootstrap_replicates':BOOT,'bootstrap_seed':SEED})
        if label=='development80':reg=grouped_ridge_cv(ids,by)
        for p in policies:choices.append({'cohort':label,'policy':p,'n_scm':len(ids),'selected_nonnoop':sum(cost[p].values()),'fallback_or_m4_count':fallback.get(p,0),'action_changed_count_or_expected_rate':float(sum(act[p].values())),'distinct_selected_edits':len({canon(e) for e in sel[p].values() if e is not None})})
    consistency=[];oldname={'FROZEN_M4':'FROZEN_M4_B1','TYPE_RANKED_M4':'TYPE_RANKED_M4_B1','T5_GUIDED_M4':'T5_GUIDED_M4_B1'}
    for r in ag:
        if r['policy'] in oldname and (r['cohort'],oldname[r['policy']]) in old:
            prev=float(old[(r['cohort'],oldname[r['policy']])]['mean_regret_reduction_vs_S0']);diff=abs(r['mean_regret_reduction_vs_s0']-prev)
            consistency.append({'cohort':r['cohort'],'policy':r['policy'],'new_mean_regret_reduction':r['mean_regret_reduction_vs_s0'],'old_v4_mean_regret_reduction':prev,'absolute_difference':diff,'matches_within_1e-12':diff<=1e-12})
    out=a.output;out.mkdir(parents=True,exist_ok=True);write_csv(out/'policy_aggregates.csv',ag);write_csv(out/'paired_vs_frozen_m4.csv',pairs);write_csv(out/'policy_choice_diagnostics.csv',choices);write_csv(out/'v4_replay_consistency.csv',consistency);write_csv(out/'nested_grouped_ridge_cv_development.csv',reg)
    manifest={'schema':'S6_POLICY_MATRIX_V1','status':'EXECUTED','classification':'POST_HOC_RETROSPECTIVE_POLICY_EVALUATION','analysis_revision':'s6-policy-matrix-v1','cohorts':{'development80':80,'replication160':160},'unit':'SCM','budget':1,'objective':'gamma=0 analytic regret','candidate_universe':'same saved initial legal M4 candidates for every policy','policies':policies,'development_type_priority':order,'development_type_mean_regret_gain':means,'positive_gain_tolerance':TOL,'fallback':'T-guided policies use frozen M4 if no positive T gain; type-first policies use frozen M4 if preferred type has no positive M4 gain','tie_break':'maximum primary gain; T policies use M4 gain as secondary within absolute 1e-12; canonical pair and operation','random_policy':'exact expected outcome for uniform draw from saved legal initial candidates','oracle':'ex-post best saved regret reduction, no-op allowed; privileged diagnostic only','bootstrap':{'replicates':BOOT,'seed':SEED,'common_indices_within_cohort':True,'interval':'pointwise percentile 95%'},'holm':'two-sided paired t-tests vs Frozen M4, Holm adjusted within cohort across other policies; supplementary only','inputs_sha256':actual,'frozen_t5_consistency':consistency,'private_raw_inputs_excluded':True}
    (out/'execution_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'output':str(out),'policy_rows':len(ag),'paired_rows':len(pairs),'consistency':consistency,'type_priority':order},ensure_ascii=False,sort_keys=True))
if __name__=='__main__':main()

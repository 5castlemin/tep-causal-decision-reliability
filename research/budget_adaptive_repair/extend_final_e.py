"""Read-only final E extension aggregation from saved S4/S5 unit records.

No SCM, G0, observational frame, DRF fit, or intervention response is created.
Private input paths are supplied explicitly and never copied into the repository.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, math, random
from collections import defaultdict
from pathlib import Path

POLICY_MAP = {
    "S0": "No-repair", "M4": "Frozen M4", "FULL_GREEDY": "Full Greedy",
    "T5_GUIDED_M4": "T5-guided M4", "M2+M4": "M2+M4",
    "RANDOM_M4": "Random-M4", "M1": "M1", "M2": "M2", "M3": "M3",
    "M1+M2+M3+M4": "Full Greedy", "GRAPH_FREE_ASSOCIATION": "Graph-free association",
    "REFERENCE_GRAPH_LEARNER": "Reference-graph learner",
    "FULL_T1_T6": "Full T1–T6",
}
CORE = {"S0", "M4", "FULL_GREEDY", "T5_GUIDED_M4", "M2+M4", "RANDOM_M4", "M1", "M2", "M3", "M1+M2+M3+M4", "GRAPH_FREE_ASSOCIATION", "REFERENCE_GRAPH_LEARNER", "FULL_T1_T6"}

def sha(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''): h.update(block)
    return h.hexdigest()

def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True,exist_ok=True)
    if not rows: path.write_text('',encoding='utf-8'); return
    with path.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)

def read_s4(path: Path, cohort: str) -> list[dict]:
    rows=json.loads(path.read_text(encoding='utf-8'))
    out=[]
    for r in rows:
        raw=r['policy']
        # The stored B=1 T5 alias duplicates the canonical subset row; retain one key.
        if raw=='T5_GUIDED_M4': continue
        policy=raw
        if raw in ('T_GREEDY:T5','T_GREEDY_B1:T5'): policy='T5_GUIDED_M4'
        elif raw in ('T_GREEDY:T1+T2+T3+T4+T5+T6','T_GREEDY_B1:T1+T2+T3+T4+T5+T6'): policy='FULL_T1_T6'
        if policy not in CORE: continue
        out.append({'cohort':cohort,'unit_id':r['scm_id'],'policy':policy,'budget':int(r['budget']),
                    'loss':float(r['regret']),'cost':float(r['cost']),'action':r['selected_k'],
                    'changed':bool(r['action_changed_from_s0']),'unused':max(0,int(r['budget'])-float(r['cost']))})
    return out

def read_s5(path: Path) -> list[dict]:
    rows=json.loads(path.read_text(encoding='utf-8'))
    out=[]
    for r in rows:
        raw=r['policy_id']; policy='FULL_GREEDY' if raw=='M1+M2+M3+M4' else raw
        if policy not in CORE: continue
        out.append({'cohort':'S5_EXTERNAL_G0','unit_id':str(r['g0_seed_id']),'policy':policy,'budget':int(r['budget']),
                    'loss':float(r['loss']),'cost':float(r['edit_count']),'action':r['recommended_action'],
                    'changed':None,'unused':float(r['unused_budget'])})
    return out

def aggregate(rows: list[dict]) -> list[dict]:
    groups=defaultdict(list)
    for r in rows: groups[(r['cohort'],r['policy'],r['budget'])].append(r)
    out=[]
    for (cohort,policy,b), rr in sorted(groups.items()):
        vals=[x['loss'] for x in rr]; costs=[x['cost'] for x in rr]; n=len(vals)
        out.append({'cohort':cohort,'policy':policy,'budget':b,'n_units':n,
          'mean_loss':sum(vals)/n,'median_loss':sorted(vals)[n//2] if n%2 else (sorted(vals)[n//2-1]+sorted(vals)[n//2])/2,
          'sd_loss':math.sqrt(sum((v-sum(vals)/n)**2 for v in vals)/(n-1)) if n>1 else 0.0,
          'mean_edit_count':sum(costs)/n,'mean_unused_budget':sum(x['unused'] for x in rr)/n,
          'action_change_rate':sum(bool(x['changed']) for x in rr if x['changed'] is not None)/n if any(x['changed'] is not None for x in rr) else 'NA',
          'no_op_rate':sum(x['cost']==0 for x in rr)/n})
    return out

def marginal(aggs: list[dict]) -> list[dict]:
    d={(r['cohort'],r['policy'],r['budget']):r for r in aggs}; out=[]
    for (cohort,policy,b),r in sorted(d.items()):
        if b==0 or (cohort,policy,b-1) not in d: continue
        p=d[(cohort,policy,b-1)]; dc=r['mean_edit_count']-p['mean_edit_count']; mb=p['mean_loss']-r['mean_loss']
        out.append({'cohort':cohort,'policy':policy,'budget_from':b-1,'budget_to':b,'marginal_benefit':mb,
                    'additional_mean_edits':dc,'benefit_per_additional_edit':mb/dc if dc>0 else 'NA',
                    'loss_change_zero_cost':abs(dc)<1e-15})
    return out

def frontier(aggs: list[dict]) -> list[dict]:
    out=[]
    by=defaultdict(list)
    for r in aggs: by[(r['cohort'],r['budget'])].append(r)
    for (cohort,b), rows in by.items():
        for r in rows:
            dominated=any((q['mean_edit_count']<=r['mean_edit_count']+1e-12 and q['mean_loss']<=r['mean_loss']+1e-12 and
                           (q['mean_edit_count']<r['mean_edit_count']-1e-12 or q['mean_loss']<r['mean_loss']-1e-12)) for q in rows)
            out.append({'cohort':cohort,'frontier_type':'fixed_budget','budget':b,'policy':r['policy'],'mean_edit_count':r['mean_edit_count'],'mean_loss':r['mean_loss'],'is_frontier':not dominated})
    by=defaultdict(list)
    for r in aggs: by[r['cohort']].append(r)
    for cohort,rows in by.items():
        for r in rows:
            dominated=any((q['mean_edit_count']<=r['mean_edit_count']+1e-12 and q['mean_loss']<=r['mean_loss']+1e-12 and
                           (q['mean_edit_count']<r['mean_edit_count']-1e-12 or q['mean_loss']<r['mean_loss']-1e-12)) for q in rows)
            out.append({'cohort':cohort,'frontier_type':'cross_budget','budget':r['budget'],'policy':r['policy'],'mean_edit_count':r['mean_edit_count'],'mean_loss':r['mean_loss'],'is_frontier':not dominated})
    return out

def lambda_breaks(aggs: list[dict]) -> list[dict]:
    out=[]; by=defaultdict(list)
    for r in aggs: by[r['cohort']].append(r)
    for cohort,rr in by.items():
        lines=[(r['mean_edit_count'],r['mean_loss'],r['policy'],r['budget']) for r in rr]
        points={0.0}
        for i,(c1,l1,*_) in enumerate(lines):
            for c2,l2,*_ in lines[i+1:]:
                if abs(c1-c2)>1e-12:
                    x=(l2-l1)/(c1-c2)
                    if x>0: points.add(x)
        pts=sorted(points); intervals=[]
        probes=[0.0]+[(a+b)/2 for a,b in zip(pts,pts[1:])]+[pts[-1]+max(1,abs(pts[-1]))]
        chosen=[]
        for lam in probes:
            best=min(l+lam*c for c,l,_,_ in lines); tied=sorted(f'{p}@B{b}' for c,l,p,b in lines if abs(l+lam*c-best)<=1e-10)
            chosen.append(tuple(tied))
        for i in range(1,len(pts)):
            if chosen[i]!=chosen[i-1]: intervals.append((pts[i],chosen[i-1],chosen[i]))
        for x,left,right in intervals: out.append({'cohort':cohort,'lambda_breakpoint':x,'from_choices':' | '.join(left),'to_choices':' | '.join(right),'interpretation':'in-sample descriptive lower-envelope switch; lambda is hypothetical loss per edit'})
    return out

def bootstrap_contrasts(rows: list[dict], replicates: int=10000, seed: int=2026112801) -> list[dict]:
    """Paired SCM bootstrap; shared unit resamples across contrasts within cohort."""
    by=defaultdict(dict)
    for r in rows:
        by[(r['cohort'],r['unit_id'])][(r['policy'],r['budget'])]=r['loss']
    result=[]; rng=random.Random(seed)
    specs=[('M4','S0',1),('M4','S0',2),('FULL_GREEDY','S0',2),('FULL_GREEDY','M4',2),
           ('FULL_T1_T6','M4',2),('M2+M4','M4',2),('T5_GUIDED_M4','M4',1),
           ('T5_GUIDED_M4','M4',2),('T5_GUIDED_M4','FULL_T1_T6',1)]
    for cohort in sorted({c for c,_ in by}):
        units=sorted(u for c,u in by if c==cohort)
        available=[(a,b,budget) for a,b,budget in specs if all((a,budget) in by[(cohort,u)] and (b,budget) in by[(cohort,u)] for u in units)]
        diffs={x:[by[(cohort,u)][(x[0],x[2])]-by[(cohort,u)][(x[1],x[2])] for u in units] for x in available}
        samples={x:[] for x in available}
        for _ in range(replicates):
            ix=[rng.randrange(len(units)) for _ in units]
            for x in available: samples[x].append(sum(diffs[x][i] for i in ix)/len(ix))
        for x in available:
            ds=diffs[x]; sorted_s=sorted(samples[x]); n=len(ds)
            result.append({'cohort':cohort,'contrast':f'{x[0]}_minus_{x[1]}','budget':x[2],'n_units':n,
               'mean_difference':sum(ds)/n,'median_difference':sorted(ds)[n//2] if n%2 else (sorted(ds)[n//2-1]+sorted(ds)[n//2])/2,
               'better_first_policy':sum(d<0 for d in ds),'worse_first_policy':sum(d>0 for d in ds),'tie':sum(abs(d)<=1e-12 for d in ds),
               'paired_bootstrap_95_low':sorted_s[int(.025*replicates)],'paired_bootstrap_95_high':sorted_s[min(replicates-1,int(.975*replicates))],
               'analysis_unit':'G0 corruption draw conditional on one DGP' if cohort=='S5_EXTERNAL_G0' else 'independent SCM',
               'interval_type':'pointwise paired percentile bootstrap; common unit resamples across contrasts in cohort; S5 is G0-only conditional on fixed action-loss table' if cohort=='S5_EXTERNAL_G0' else 'pointwise SCM paired percentile bootstrap; common resamples across contrasts in cohort',
               'replicates':replicates,'seed':seed})
    return result

def main():
    p=argparse.ArgumentParser(); p.add_argument('--dev',type=Path,required=True); p.add_argument('--confirm',type=Path,required=True); p.add_argument('--s5',type=Path,required=True); p.add_argument('--out',type=Path,required=True); a=p.parse_args()
    inputs={'s4_development':a.dev,'s4_confirmation':a.confirm,'s5_saved_unit_losses':a.s5}
    rows=read_s4(a.dev,'S4_DEVELOPMENT_80')+read_s4(a.confirm,'S4_INDEPENDENT_REPLICATION_160')+read_s5(a.s5)
    aggs=aggregate(rows); mb=marginal(aggs); fr=frontier(aggs); lb=lambda_breaks(aggs); boots=bootstrap_contrasts(rows)
    write_csv(a.out/'budget_policy_aggregate.csv',aggs); write_csv(a.out/'marginal_benefit.csv',mb); write_csv(a.out/'pareto_frontier.csv',fr); write_csv(a.out/'lambda_breakpoints.csv',lb); write_csv(a.out/'paired_bootstrap_uncertainty.csv',boots)
    manifest={'schema':'RESEARCH_E_EXTENSION_SAVED_RESULT_AGGREGATION_V1','classification':'post-hoc descriptive decision-economic extension','unit_rows_read':len(rows),'aggregate_rows':len(aggs),'new_scm':0,'new_g0':0,'new_observations':0,'new_drf_fits':0,'new_intervention_rows':0,'budgets_available':sorted({r['budget'] for r in rows}),'input_sha256':{k:sha(v) for k,v in inputs.items()},'outputs_sha256':{x.name:sha(x) for x in a.out.glob('*.csv')},'limits':['S4/S5 source unit records available only for B=0..4; no B=5..9 values inferred','S5 loss scale is not combined with S4 regret','S5 G0 draws are conditional on one semisynthetic DGP, not independent SCMs']}
    (a.out/'execution_manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps({k:manifest[k] for k in ('unit_rows_read','aggregate_rows','new_scm','new_g0','budgets_available')},sort_keys=True))
if __name__=='__main__': main()

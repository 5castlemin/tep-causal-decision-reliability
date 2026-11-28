"""Reproducible aggregate-only analysis for locked S4 reconstruction outputs."""
from __future__ import annotations
import argparse, csv, json, hashlib
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--private',type=Path,required=True); ap.add_argument('--public',type=Path,required=True); ap.add_argument('--phase',required=True); ap.add_argument('--seed',type=int,required=True); a=ap.parse_args()
    policies=json.loads((a.private/'policy_results_private.json').read_text(encoding='utf-8'))
    units=json.loads((a.private/'unit_results_private.json').read_text(encoding='utf-8'))
    inputs=json.loads((a.private/'inputs_private.json').read_text(encoding='utf-8'))
    assert len(units)==len(inputs) and len({u['scm_id'] for u in units})==len(units)
    assert all(r['cohort']==('general' if a.phase=='development' else 'opportunity_rich_diagnostic') for r in policies)
    by=defaultdict(dict)
    for r in policies: by[r['scm_id']][(r['policy'],int(r['budget']))]=r
    n=len(units); rng=np.random.default_rng(a.seed); ix=rng.integers(0,n,size=(10000,n)); contrasts=[]
    primary=(('T5_GUIDED_M4','M4',1),('T_GREEDY_B1:T1+T2+T3+T4+T5+T6','M4',1),('M4','S0',2),('FULL_GREEDY','S0',2))
    for left,right,b in primary:
        d=np.array([by[u['scm_id']][(left,b)]['regret']-by[u['scm_id']][(right,b)]['regret'] for u in units]); boot=d[ix].mean(axis=1)
        contrasts.append({'contrast':f'{left}-{right}_B{b}','n_scm':n,'mean_difference':float(d.mean()),'median_difference':float(np.median(d)),'ci95_low':float(np.quantile(boot,.025)),'ci95_high':float(np.quantile(boot,.975)),'better_left':int((d<-1e-12).sum()),'worse_left':int((d>1e-12).sum()),'tie':int((np.abs(d)<=1e-12).sum()),'bootstrap_seed':a.seed,'replicates':10000})
    counts=[int(u['initial_m4_feasible_count']) for u in inputs]; hist=Counter(counts)
    scm_ids=sorted(by); redundancy=[]
    for budget in (1,2):
        names=sorted({p for unit in by.values() for p,b in unit if b==budget and p.startswith(('T_GREEDY:', 'T_GREEDY_B1:'))})
        for p in names:
            rows=[by[s][(p,budget)] for s in scm_ids]
            redundancy.append({'budget':budget,'policy':p,'n_scm':len(rows),'unique_final_graphs':len({r['graph_hash'] for r in rows}),'mean_regret':float(np.mean([r['regret'] for r in rows])),'mean_cost':float(np.mean([r['cost'] for r in rows])),'agreement_with_m4_graph':float(np.mean([r['graph_hash']==by[s][('M4',budget)]['graph_hash'] for s in scm_ids])),'agreement_with_m4_action':float(np.mean([r['selected_k']==by[s][('M4',budget)]['selected_k'] for s in scm_ids]))})
    summary={'schema':'S4_RECONSTRUCTION_ANALYSIS_V1','phase':a.phase,'n_scm':n,'policy_rows':len(policies),'unique_scm_ids':len(by),'initial_m4_candidate_count':{'min':min(counts),'mean':float(np.mean(counts)),'median':float(np.median(counts)),'max':max(counts),'histogram':dict(sorted(hist.items())),'n_ge_2':sum(x>=2 for x in counts)},'primary_and_secondary_paired_contrasts':contrasts,'policy_redundancy_rows':len(redundancy),'t_subset_policy_count_b1':len({r['policy'] for r in policies if r['policy'].startswith('T_GREEDY_B1:') and r['budget']==1}),'t_subset_policy_count_b2':len({r['policy'] for r in policies if r['policy'].startswith('T_GREEDY:') and r['budget']==2}),'input_sha256':sha(a.private/'inputs_private.json'),'unit_results_sha256':sha(a.private/'unit_results_private.json'),'policy_results_sha256':sha(a.private/'policy_results_private.json')}
    a.public.mkdir(parents=True,exist_ok=True)
    for name,rows in [('policy_redundancy.csv',redundancy),('paired_contrasts.csv',contrasts)]:
        with (a.public/name).open('w',newline='',encoding='utf-8') as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    (a.public/'analysis_summary.json').write_text(json.dumps(summary,sort_keys=True,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps(summary,sort_keys=True))
if __name__=='__main__': main()

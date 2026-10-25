"""Paired old-data diagnostics; no new learning or confirmation data."""
import argparse,collections,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from path_metric_incremental import load,development_cv
from run_path_incremental_development import paired
from run_diverse_structure_pilot import save

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);a=p.parse_args();out=Path(a.output);out.mkdir(parents=True,exist_ok=False)
    base=ROOT/'research_runs/path_metric_incremental_validation/development_v1';rows=load(base/'development_operational.json')
    result={}
    for policy in ['confirmed_only','mec_minimax','abstain_on_disagreement']:
        cv=development_cv([r for r in rows if r['policy']==policy]);result[policy]=dict(macro_mae=cv['macro_mae'],paired=paired(cv))
    save(out/'policy_specific_cv.json',result)
    result={}
    for alg in ['pc','boss','directlingam']:
        sub=[r for r in rows if r['algorithm']==alg and r['policy']=='confirmed_only'];cv=development_cv(sub)
        result[alg]=dict(macro_mae=cv['macro_mae'],paired=paired(cv),scope='development, algorithm-specific refit, constant quality features do not identify effects')
    save(out/'within_algorithm_cv.json',result)
    empirical=[dict(r,scale_normalized_regret=r['empirical_operational_regret']) for r in rows];cv=development_cv(empirical)
    save(out/'sample_outcome_cv.json',dict(macro_mae=cv['macro_mae'],paired=paired(cv),scope='same features, operational rows and LOSO; only outcome uses original finite do samples'))
    rec=load(base/'stored_sample_precision.json');groups=collections.defaultdict(list)
    specs={s['structure_id']:s for f in ['diverse_structure_pilot','independent_confirmation'] for s in load(ROOT/'research_runs'/f/'PLAN_v1.json')['structures']}
    for r in rec:groups[r['structure_id'],r['task_id'],r['n']].append(r)
    ranks=[]
    for (sid,tid,n),rs in groups.items():
        task=next(t for t in specs[sid]['tasks'] if t['task_id']==tid);grid=task['action_values'];rs=[r for r in rs if r['action_value'] in grid]
        cost=lambda r:task['cost_weight']*(r['action_value']-task['reference_action'])**2
        empirical=min(rs,key=lambda r:((r['mean']-task['target_value'])**2+cost(r),abs(r['action_value']),r['action_value']))['action_value']
        analytic=min(rs,key=lambda r:((r['analytic_mean']-task['target_value'])**2+cost(r),abs(r['action_value']),r['action_value']))['action_value']
        ranks.append(dict(structure_id=sid,task_id=tid,n=n,sample_best=empirical,analytic_best=analytic,mismatch=empirical!=analytic,scope='original five-value grid; stored old samples only'))
    save(out/'stored_full_grid_rankings.json',ranks)
    save(out/'SUMMARY.json',dict(status='DEVELOPMENT_ONLY',new_graph_learning=0,new_independent_structures=0,
        original_grid_mismatches={str(n):dict(mismatch=sum(r['mismatch'] for r in ranks if r['n']==n),cases=sum(r['n']==n for r in ranks)) for n in [128,256,512,768]}))
    print(json.dumps(load(out/'SUMMARY.json')))
if __name__=='__main__':main()

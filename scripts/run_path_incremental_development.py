"""Reanalyse old 20 structures; never label these data independent confirmation."""
import argparse,csv,gzip,hashlib,io,json,math,statistics,sys
from collections import defaultdict,Counter
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from path_metric_incremental import development_rows,development_cv,precision_gate,MODELS,CONTEXT,QUALITY,fit_predict,load,raw,linear_moments
from independent_confirmation import predict_frozen
from repeated_metric_pilot import spearman
from run_diverse_structure_pilot import save,table

def save_gz(p,obj):
    b=(json.dumps(obj,ensure_ascii=False,allow_nan=False,separators=(',',':'))+'\n').encode();Path(str(p)+'.gz').write_bytes(gzip.compress(b,mtime=0))

def paired(result,seed=710002):
    import numpy as np
    s={(x['structure_id'],x['model']):x['mae'] for x in result['structure_scores']};ids=sorted({x[0] for x in s});rng=np.random.default_rng(seed);records=[]
    for a,b in [('M1','M4'),('M5','M6'),('M0','M2'),('M1','M2')]:
        d=[s[i,a]-s[i,b] for i in ids];boots=np.asarray(d)[rng.integers(0,len(d),size=(10000,len(d)))].mean(axis=1)
        lo,hi=np.quantile(boots,[.025,.975]);records.append(dict(left=a,right=b,delta=statistics.mean(d),ci_low=float(lo),ci_high=float(hi),right_better=sum(x>0 for x in d),structures=len(ids),by_structure=dict(zip(ids,d)),scope='development uncertainty only; fixed sequence will apply only to new independent cohort'))
    return records

def diagnostics(rows):
    result=[]
    for policy in ['all','confirmed_only','mec_minimax','abstain_on_disagreement']:
        for algorithm in ['all','pc','boss','directlingam']:
            for selection in ['operational_all','pipeline_ready','computed_only','confirmed_path']:
                items=[r for r in rows if (policy=='all' or r['policy']==policy) and (algorithm=='all' or r['algorithm']==algorithm)]
                if selection=='pipeline_ready':items=[r for r in items if r['pipeline_ready']]
                if selection=='computed_only':items=[r for r in items if r['computed_recommendation']]
                if selection=='confirmed_path':items=[r for r in items if r['predicted_path'] and r['pipeline_ready']]
                for metric in QUALITY+['normalized_shd','unresolved_ratio']:
                    x=[float(r[metric]) for r in items];y=[r['analytic_regret'] for r in items]
                    effect=[r for r in items if r.get('fixed_effect_error') is not None]
                    reason='INSUFFICIENT_VARIATION' if len(set(x))<3 or len(set(y))<3 else 'DESCRIPTIVE_ONLY'
                    result.append(dict(policy=policy,algorithm=algorithm,selection=selection,metric=metric,rows=len(items),metric_unique=len(set(x)),status=reason,
                        rho=None if reason!='DESCRIPTIVE_ONLY' else spearman(x,y),fixed_effect_rho=spearman([float(r[metric]) for r in effect],[r['fixed_effect_error'] for r in effect]) if len({r[metric] for r in effect})>=3 else None))
    overlap=[];data=[r for r in rows if r['policy']=='confirmed_only'];metrics=QUALITY+['normalized_shd','unresolved_ratio']
    for i,a in enumerate(metrics):
        for b in metrics[i+1:]:overlap.append(dict(left=a,right=b,rho=spearman([r[a] for r in data],[r[b] for r in data]),source='20 development structures only'))
    return result,overlap

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);a=p.parse_args();out=Path(a.output);out.mkdir(parents=True,exist_ok=False)
    design=load(ROOT/'research_runs/path_metric_incremental_validation/DESIGN_GATE_PLAN_v1.json')
    save(out/'ANALYSIS_START.json',dict(utc=datetime.now(timezone.utc).isoformat(),design_sha256=hashlib.sha256((ROOT/'research_runs/path_metric_incremental_validation/DESIGN_GATE_PLAN_v1.json').read_bytes()).hexdigest(),new_independent_data_generated=False))
    rows,oracle,inputs=development_rows(ROOT);assert len({r['structure_id'] for r in rows})==20
    save_gz(out/'development_operational.json',rows);save_gz(out/'oracle_diagnostics_NOT_DEPLOYABLE.json',oracle)
    cv=development_cv(rows)
    for key,value in cv.items():
        if isinstance(value,list) and key in ['predictions','artifacts']:save_gz(out/(key+'.json'),value)
        else:save(out/(key+'.json'),value)
    table(out/'structure_scores.csv',cv['structure_scores']);save(out/'paired_development.json',paired(cv))
    frozen={name:fit_predict(rows,[],features)[1] for name,features in MODELS.items()};save(out/'frozen_development_models.json',frozen)
    gate=precision_gate(cv,design);save(out/'INDEPENDENT_PRECISION_GATE.json',gate)
    # Separate conditional forecast experiments and pre-specified context ablation.
    conditional=[r for r in rows if r['pipeline_ready']];cc=development_cv(conditional)
    save(out/'conditional_macro_mae.json',cc['macro_mae']);save(out/'conditional_paired.json',paired(cc))
    minimal=['algorithm_boss','algorithm_directlingam','log_n','n_nodes','predicted_density','unresolved_ratio','policy_mec','policy_abstain']
    ablation=development_cv(rows,{k:(minimal+[f for f in v if f in QUALITY]) for k,v in MODELS.items()})
    save(out/'without_task_information.json',dict(macro_mae=ablation['macro_mae'],paired=paired(ablation),scope='development ablation; identical operational analytic target, no independent claim'))
    groups=[]
    for scope,key in [('policy','policy'),('algorithm','algorithm')]:
        for name in sorted({r[key] for r in rows}):
            by=defaultdict(list)
            for r in cv['predictions']:
                if r[key]==name:by[r['model'],r['structure_id']].append(r['absolute_error'])
            scores=[dict(model=m,structure_id=s,mae=statistics.mean(v)) for (m,s),v in by.items()]
            groups.append(dict(scope=scope,group=name,macro_mae={m:statistics.mean(r['mae'] for r in scores if r['model']==m) for m in MODELS},scope_note='same heldout pooled model; not refitted within algorithm or policy'))
    save(out/'algorithm_policy_prediction.json',groups)
    association,overlap=diagnostics(rows);save(out/'associations.json',association);save(out/'metric_overlap.json',overlap)
    failure=[]
    for algorithm in ['pc','boss','directlingam']:
        for policy in ['confirmed_only','mec_minimax','abstain_on_disagreement']:
            x=[r for r in rows if r['algorithm']==algorithm and r['policy']==policy]
            failure.append(dict(algorithm=algorithm,policy=policy,attempts=len(x),pipeline_ready=sum(r['pipeline_ready'] for r in x),computed_recommendation=sum(r['computed_recommendation'] for r in x),
                failure_types=dict(Counter(r['failure_type'] for r in x)),operational_coverage=len(x),operational_mean_loss=statistics.mean(r['analytic_loss'] for r in x),
                conditional_mean_loss=statistics.mean(r['analytic_loss'] for r in x if r['pipeline_ready'])))
    save(out/'failure_policy_results.json',failure)
    # Same-data algorithm contrasts use task/structure/policy-matched cells.
    cells=defaultdict(dict)
    for r in rows:cells[r['dataset_id'],r['task_id'],r['policy']][r['algorithm']]=r
    algorithm_pairs=[]
    for key,v in cells.items():
        for aa,bb in [('pc','boss'),('pc','directlingam'),('boss','directlingam')]:
            if aa in v and bb in v:algorithm_pairs.append(dict(dataset_id=key[0],task_id=key[1],policy=key[2],left=aa,right=bb,analytic_regret_difference=v[aa]['analytic_regret']-v[bb]['analytic_regret'],path_difference=v[aa]['key_path_edge_recall']-v[bb]['key_path_edge_recall']))
    save_gz(out/'same_data_algorithm_pairs.json',algorithm_pairs)
    policy_pairs=[]
    baseline={(r['graph_id'],r['task_id']):r for r in rows if r['policy']=='confirmed_only'}
    for policy in ['mec_minimax','abstain_on_disagreement']:
        items=[r for r in rows if r['policy']==policy];delta=[r['analytic_regret']-baseline[r['graph_id'],r['task_id']]['analytic_regret'] for r in items]
        policy_pairs.append(dict(policy=policy,cells=len(items),improved=sum(d< -1e-12 for d in delta),worsened=sum(d>1e-12 for d in delta),unchanged=sum(abs(d)<=1e-12 for d in delta),operational_fallback_included=True))
    save(out/'paired_policies.json',policy_pairs)
    c7=[r for r in rows if r['structure_id']=='C07' and r['policy']=='confirmed_only'];detail=[]
    for task in ['direct','path']:
        for alg in ['pc','boss','directlingam']:
            x=[r for r in c7 if r['task_id']==task and r['algorithm']==alg]
            detail.append(dict(task=task,algorithm=alg,chosen_action_counts=dict(Counter(str(r['operational_action']) for r in x)),
                oracle_total_effect=x[0]['oracle_total_effect'],oracle_best_action=x[0]['oracle_best_action'],oracle_improvement_gap=x[0]['oracle_improvement_gap'],
                mean_analytic_regret=statistics.mean(r['analytic_regret'] for r in x),max_analytic_loss=max(r['analytic_loss'] for r in x),
                mean_predicted_slope=statistics.mean(r['estimated_slope'] for r in x if r['estimated_slope'] is not None),target_sd=math.exp(statistics.mean(r['log_target_sd'] for r in x)),
                mean_skeleton_f1=statistics.mean(r['skeleton_f1'] for r in x),mean_path=statistics.mean(r['key_path_edge_recall'] for r in x)))
    without=[r for r in rows if r['structure_id']!='C07'];noc7=development_cv(without)
    save(out/'C07_DIAGNOSIS.json',dict(case=detail,kept_in_primary=True,loss_scale_reference=1.,without_C07_sensitivity_macro=noc7['macro_mae'],without_C07_paired=paired(noc7),
        interpretation='post-observation development diagnosis; no change of old primary endpoint or deletion'))
    # Use stored independent intervention arrays to quantify finite-sample error by prefix.
    mc=[]
    for source in inputs:
        run=Path(source['run']);plan=source['plan']
        for spec in plan['structures']:
            tasks=[t for t in spec['tasks'] if t['task_id'] in ['direct','path']]
            grid=plan['evaluation'].get('candidate_union',tasks[0]['action_values'])
            for task in tasks:
                for vi,value in enumerate(grid):
                    f=run/'do_evaluation'/(spec['structure_id']+'__'+task['action']+'__'+str(vi)+'.csv')
                    records=list(csv.DictReader(io.StringIO(raw(f).decode('utf-8-sig'))));target=task['target'];means,var=linear_moments(spec,task['action'],value)
                    for n in [128,256,512,768]:
                        vals=[float(r[target]) for r in records[:n]];mean=statistics.mean(vals);se=statistics.stdev(vals)/math.sqrt(n)
                        mc.append(dict(structure_id=spec['structure_id'],task_id=task['task_id'],action_value=value,n=n,mean=mean,analytic_mean=means[target],error=mean-means[target],se=se,expected_se=math.sqrt(var[target]/n)))
    save_gz(out/'stored_sample_precision.json',mc)
    save(out/'mc_error_by_n.json',[dict(n=n,conditions=sum(r['n']==n for r in mc),rmse=math.sqrt(statistics.mean(r['error']**2 for r in mc if r['n']==n)),mean_se=statistics.mean(r['se'] for r in mc if r['n']==n)) for n in [128,256,512,768]])
    save(out/'SUMMARY.json',dict(structures=20,rows=len(rows),pipeline_ready=sum(r['pipeline_ready'] for r in rows),computed_recommendations=sum(r['computed_recommendation'] for r in rows),macro_mae=cv['macro_mae'],precision_gate=gate['status'],required_new_structures=gate['required_structures'],new_independent_structures=0,independent_confirmation_executed=False,manufacturing_validated=False,old_results_changed=False))
    save(out/'SHA256.json',{p.relative_to(out).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in out.rglob('*') if p.is_file()})
    print(json.dumps(load(out/'SUMMARY.json'),ensure_ascii=False))
if __name__=='__main__':main()

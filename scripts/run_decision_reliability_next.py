"""Reuse frozen controls, diagnose responses, refit six C07 oracle diagnostics, nested CV."""
import argparse,gzip,hashlib,json,math,statistics,sys
from collections import defaultdict,Counter
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from path_metric_incremental import load,linear_moments
from decision_reliability_next import evaluate,response,choose_response,error_location,match_pair,nested_cv
from diverse_structure_pilot import reference_edges,score_graph
from integrated_pilot import fit_model
from repeated_metric_pilot import recommend_policy,spearman
from run_diverse_structure_pilot import save

def gz(p,x):p.write_bytes(gzip.compress((json.dumps(x,ensure_ascii=False,allow_nan=False,separators=(',',':'))+'\n').encode(),mtime=0))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def sign(x):return 0 if abs(x)<=1e-8 else 1 if x>0 else -1

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);a=ap.parse_args();out=Path(a.output);out.mkdir(parents=True,exist_ok=False)
    planpath=ROOT/'research_runs/decision_reliability_next/PLAN_v1.json';plan=load(planpath)
    save(out/'START.json',dict(utc=datetime.now(timezone.utc).isoformat(),plan_sha256=sha(planpath),code_sha256={p.relative_to(ROOT).as_posix():sha(p) for p in [Path(__file__),ROOT/'src/decision_reliability_next.py']},new_discovery_learning=0,new_reference_structures=0))
    specs={};origin={};controlled=[];model_cache={};inputhash={}
    for folder in ['diverse_structure_pilot','independent_confirmation']:
        base=ROOT/'research_runs'/folder;run=base/'run_v1';p=load(base/'PLAN_v1.json')
        for s in p['structures']:specs[s['structure_id']]=s;origin[s['structure_id']]=(run,p)
        source=run/'controlled_comparison.json';source=source if source.exists() else Path(str(source)+'.gz');inputhash[source.relative_to(ROOT).as_posix()]=sha(source)
        ev=load(run/'intervention_evaluation.json')
        for record in load(run/'controlled_comparison.json'):
            if record['task_id'] not in ['direct','path'] or record['row_status']!='EVALUATED':continue
            sid=record['structure_id'];s=specs[sid];t=next(t for t in s['tasks'] if t['task_id']==record['task_id'])
            f=run/'datasets'/record['dataset_id']/('controlled_'+record['variant']+'_model.json')
            if str(f) not in model_cache:model_cache[str(f)]=load(f)
            artifact=model_cache[str(f)];model=artifact['model'];edges=set(map(tuple,artifact['edges']))
            rec=recommend_policy([model],[edges],t,t,'confirmed_only');selected=rec['selected']['action']
            assert selected==record['recommended_action']
            assert math.isclose(rec['selected']['predicted_y'],record['predicted_target'],abs_tol=1e-9,rel_tol=1e-9)
            pr,slope=response(model,t);q=score_graph(edges,set(),s,t);location=error_location(s,t,edges)
            r=dict(structure_id=sid,dataset_id=record['dataset_id'],task_id=t['task_id'],variant=record['variant'],policy='confirmed_only',
                source_type='artificial_stored_control',recommended_action=selected,recommendation_status=rec['status'],**q,**location,**evaluate(s,t,selected,pr,slope,t['loss_scale']))
            r.update(stored_do_mean=record['actual_target_mean'],stored_do_mean_se=record['actual_target_se'],stored_do_loss=record['target_mean_loss'],
                stored_do_improvement=record['reference_mean_loss']-record['target_mean_loss'],stored_do_candidate_regret=record['candidate_regret'])
            controlled.append(r)
    gz(out/'A_controlled_outcomes.json.gz',controlled)
    cells=defaultdict(dict)
    for r in controlled:cells[r['dataset_id'],r['task_id']][r['variant']]=r
    pairs=[];ineligible=[]
    for (ds,tid),variants in sorted(cells.items()):
        for left,right in plan['A']['pairs']:
            if left not in variants or right not in variants:ineligible.append(dict(dataset_id=ds,task_id=tid,left=left,right=right,reason='VARIANT_NOT_AVAILABLE'));continue
            l,r=variants[left],variants[right]
            if not match_pair(l,r):ineligible.append(dict(dataset_id=ds,task_id=tid,left=left,right=right,reason='GLOBAL_METRICS_OR_ERROR_COUNTS_NOT_MATCHED'));continue
            meaningful=l['key_removed']>0 and r['key_removed']==0
            pairs.append(dict(structure_id=l['structure_id'],dataset_id=ds,task_id=tid,left=left,right=right,
                same_skeleton_f1=l['skeleton_f1'],same_direction_f1=l['strict_directed_f1'],same_shd=l['shd'],
                task_specific_key_vs_peripheral=meaningful,both_paths_preserved=l['path_preserved'] and r['path_preserved'],
                left_action=l['recommended_action'],right_action=r['recommended_action'],left_status=l['recommendation_status'],right_status=r['recommendation_status'],
                left_loss=l['analytic_loss'],right_loss=r['analytic_loss'],left_improvement=l['improvement'],right_improvement=r['improvement'],
                loss_left_minus_right=l['analytic_loss']-r['analytic_loss'],fixed_error_left=l['fixed_effect_error'],fixed_error_right=r['fixed_effect_error'],
                left_worsened=l['worsened'],right_worsened=r['worsened'],stored_do_loss_difference=l['stored_do_loss']-r['stored_do_loss']))
    gz(out/'A_matched_pairs.json.gz',pairs);save(out/'A_not_applicable.json',ineligible)
    grouped=[]
    for name in ['remove_key','reverse_key','remove_key_path_retained']:
        for group in ['all_matched','actual_key_vs_peripheral','actual_key_vs_peripheral_both_paths']:
            selected=[p for p in pairs if p['left']==name and (group=='all_matched' or p['task_specific_key_vs_peripheral']) and (group!='actual_key_vs_peripheral_both_paths' or p['both_paths_preserved'])]
            grouped.append(dict(error=name,group=group,pairs=len(selected),structures=len({p['structure_id'] for p in selected}),
                left_worse=sum(p['loss_left_minus_right']>1e-10 for p in selected),left_better=sum(p['loss_left_minus_right']< -1e-10 for p in selected),ties=sum(abs(p['loss_left_minus_right'])<=1e-10 for p in selected),
                mean_difference=statistics.mean(p['loss_left_minus_right'] for p in selected) if selected else None,scope='dependent development pairs, not independent sample count'))
    save(out/'A_summary.json',grouped)
    # Reuse old discovered graphs and fixed effects; preserve unsuccessful fit/learning status.
    old=load(ROOT/'research_runs/path_metric_incremental_validation/development_v1/development_operational.json');discovery=[]
    for r in old:
        if r['policy']!='confirmed_only':continue
        s=specs[r['structure_id']];t=next(t for t in s['tasks'] if t['task_id']==r['task_id']);pr=None if r['surrogate_reference_gap'] is None else t['target_value']-r['surrogate_reference_gap']
        result=evaluate(s,t,r['operational_action'],pr,r['estimated_slope'],t['loss_scale'])
        discovery.append(dict(structure_id=r['structure_id'],dataset_id=r['dataset_id'],graph_id=r['graph_id'],algorithm=r['algorithm'],task_id=r['task_id'],
            pipeline_ready=r['pipeline_ready'],failure_type=r['failure_type'],recommendation_status=r['recommendation_status'],recommended_action=r['operational_action'],
            **{k:r[k] for k in ['skeleton_f1','strict_directed_f1','key_path_edge_recall','unresolved_ratio','predicted_path']},**result))
    gz(out/'B_discovery_outcomes.json.gz',discovery)
    cases=dict(high_quality_wrong_effect=[r for r in discovery if r['skeleton_f1']>=.9 and r['fixed_effect_error'] is not None and r['fixed_effect_error']>.25],
        low_quality_close_effect=[r for r in discovery if r['skeleton_f1']<=.7 and r['fixed_effect_error'] is not None and r['fixed_effect_error']<=.1],
        worse_than_reference=[r for r in discovery if r['worsened']],large_loss=[r for r in discovery if r['large_deterioration']],
        low_quality_optimal=[r for r in discovery if r['skeleton_f1']<=.7 and not r['nonoptimal']])
    gz(out/'B_cases.json.gz',cases)
    associations=[]
    for sid in sorted(specs):
        for tid in ['direct','path']:
            x=[r for r in discovery if r['structure_id']==sid and r['task_id']==tid and r['fixed_effect_error'] is not None]
            for metric in ['skeleton_f1','strict_directed_f1','key_path_edge_recall','fixed_effect_error']:
                xs=[r[metric] for r in x];ys=[r['raw_regret'] for r in x];valid=len(set(xs))>=3 and len(set(ys))>=3
                associations.append(dict(structure_id=sid,task_id=tid,metric=metric,rows=len(x),unique=len(set(xs)),rho=spearman(xs,ys) if valid else None,status='DESCRIPTIVE_DEPENDENT' if valid else 'INSUFFICIENT_VARIATION'))
    save(out/'B_same_task_associations.json',associations)
    # Explicit oracle controls: no change to stored discovery graphs/models.
    c7=[];oracle_models=[];s=specs['C07'];run,p=origin['C07']
    for ds in sorted({r['dataset_id'] for r in discovery if r['structure_id']=='C07'}):
        import pandas as pd
        artifact=load(run/'datasets'/ds/'boss_models.json')['primary'];frame=pd.read_csv(run/'datasets'/ds/'train.csv');m=fit_model(frame[s['nodes']].to_numpy(),s['nodes'],reference_edges(s),artifact['alpha'])
        oracle_models.append(dict(dataset_id=ds,alpha=artifact['alpha'],model=m,source_type='new_true_structure_fit_on_old_data_ORACLE_DIAGNOSTIC'))
        for t in [t for t in s['tasks'] if t['task_id'] in ['direct','path']]:
            oldref,oldslope=response(artifact,t);oracleref,oracleslope=response(m,t);true_slope=linear_moments(s,t['action'],1)[0][t['target']]
            for mode,intercept,slope in [('original_boss',oldref,oldslope),('replace_slope_only_ORACLE',oldref,true_slope),('replace_intercept_only_ORACLE',0.,oldslope),('true_structure_observational_fit_ORACLE',oracleref,oracleslope)]:
                path=True if mode!='original_boss' else any(r['predicted_path'] for r in old if r['dataset_id']==ds and r['algorithm']=='boss' and r['task_id']==t['task_id'])
                selected,candidates=choose_response(t,intercept,slope,path);c7.append(dict(dataset_id=ds,task_id=t['task_id'],mode=mode,recommended_action=selected['action'],
                    reduced_response_intercept=intercept,reduced_response_slope=slope,**evaluate(s,t,selected['action'],intercept,slope,t['loss_scale'])))
    save(out/'B_C07_response_controls.json',c7);gz(out/'B_C07_oracle_fitted_models.json.gz',oracle_models)
    save(out/'B_summary.json',dict(rows=len(discovery),structures=20,availability=sum(r['pipeline_ready'] for r in discovery),
        nonoptimal=sum(r['nonoptimal'] for r in discovery),worsened=sum(r['worsened'] for r in discovery),large=sum(r['large_deterioration'] for r in discovery),
        cases={k:len(v) for k,v in cases.items()},true_structure_refits=6,new_discovery_learning=0))
    # C is a bounded auxiliary experiment; outer label is absent from inner fitting/selection.
    primary=[r for r in old if r['policy']=='confirmed_only'];cv=nested_cv(primary);save(out/'C_nested_cv.json',cv)
    precision=[]
    for left,right in [('SKELETON','SKEL_PATH'),('SKEL_DIRECTION','ALL')]:
        scores={(r['structure_id'],r['model']):r['mae'] for r in cv['structure_scores']};ids=sorted(specs);d=[scores[s,left]-scores[s,right] for s in ids]
        import numpy as np
        rng=np.random.default_rng(77261025);boot=np.asarray(d)[rng.integers(0,len(d),size=(10000,len(d)))].mean(axis=1);lo,hi=np.quantile(boot,[.025,.975]);sd=statistics.stdev(d)
        precision.append(dict(left=left,right=right,mean_delta=statistics.mean(d),ci_low=float(lo),ci_high=float(hi),better_structures=sum(x>0 for x in d),
            by_structure=dict(zip(ids,d)),sd=sd,required_n_halfwidth_005=math.ceil((1.96*sd/.005)**2),required_n_halfwidth_01=math.ceil((1.96*sd/.01)**2),
            interpretation='development width approximation; not power or guaranteed evidence of a .01 effect'))
    required=max(r['required_n_halfwidth_005'] for r in precision);stable=cv['nested_selected_macro_mae']<=cv['macro_mae']['BASE']+.01
    gate=dict(status='NOT_RUN_NEW_COHORT',comparisons=precision,required_structures_rough=required,learning_calls_at3x3=required*9,
        budget_structures=30,budget_calls=288,model_stability_vs_base=stable,observed_increments_below_01=any(r['mean_delta']<.01 for r in precision),
        note='No meaningful incremental superiority established. Increasing N does not increase underlying effect; no seeds/threshold changes or new reference structures.')
    save(out/'D_precision.json',gate)
    save(out/'INPUT_SHA256.json',inputhash)
    summary=dict(scope='old20 development reanalysis + six new oracle fits, no independent cohort',controlled_rows=len(controlled),matched_pairs=len(pairs),
        meaningful_pairs=sum(p['task_specific_key_vs_peripheral'] for p in pairs),retained_meaningful_pairs=sum(p['task_specific_key_vs_peripheral'] and p['both_paths_preserved'] for p in pairs),
        discovered_rows=len(discovery),oracle_refits=6,model_candidates=len(cv['features']),new_discovery_learning_calls=0,new_reference_structures=0,new_do_samples=0,new_manufacturing_runs=0,
        macro_mae=cv['macro_mae'],nested_selected_mae=cv['nested_selected_macro_mae'],precision=gate['status'])
    save(out/'SUMMARY.json',summary);save(out/'SHA256.json',{f.relative_to(out).as_posix():sha(f) for f in sorted(out.rglob('*')) if f.is_file() and f.name!='SHA256.json'})
    print(json.dumps(summary,ensure_ascii=False))

if __name__=='__main__':main()

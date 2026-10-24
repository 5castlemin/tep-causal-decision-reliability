"""Apply locked exploratory predictors. No fitting to confirmation outcomes."""
import argparse,hashlib,json,statistics,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'));sys.path.insert(0,str(ROOT/'scripts'))
from independent_confirmation import clustered_comparison,descriptive_diagnostics
from decision_mvp import static_mean_response
from run_diverse_structure_pilot import save,table

def analyze(run,base,out):
    plan=json.loads((run/'plan.json').read_text(encoding='utf-8'));out.mkdir(parents=True,exist_ok=False)
    models_path=base/plan['confirmation_analysis']['frozen_models']
    assert hashlib.sha256(models_path.read_bytes()).hexdigest()==plan['frozen_models_sha256']
    models=json.loads(models_path.read_text(encoding='utf-8'))
    rows=json.loads((run/'comparison.json').read_text(encoding='utf-8'));controlled=json.loads((run/'controlled_comparison.json').read_text(encoding='utf-8'))
    evaluation=json.loads((run/'intervention_evaluation.json').read_text(encoding='utf-8'))
    specs={s['structure_id']:s for s in plan['structures']};grid=plan['evaluation']['candidate_union']
    tasks={(sid,t['task_id']):t for sid,s in specs.items() for t in s['tasks']}
    fixed=[];theory_rows=[]
    model_cache={}
    for r in rows+controlled:
        if r['row_status']!='EVALUATED':continue
        t=tasks[r['structure_id'],r['task_id']];prefix=r['structure_id']+'__'+r['action']+'__';target=r['target']
        analytic=[evaluation[prefix+str(grid.index(v))]['post_freeze_analytic_mean'][target] for v in t['action_values']]
        losses=[(mean-t['target_value'])**2+t['cost_weight']*v*v for mean,v in zip(analytic,t['action_values'])]
        chosen=t['action_values'].index(r['recommended_action'])
        theory_rows.append(dict(graph_id=r['graph_id'],source_type=r['source_type'],structure_id=r['structure_id'],task_id=r['task_id'],policy=r['policy'],
            empirical_regret=r['scale_normalized_regret'],analytic_regret=(losses[chosen]-min(losses))/t['loss_scale']**2,
            empirical_best_action=t['action_values'][min(range(len(t['action_values'])),key=lambda i:(
                (evaluation[prefix+str(grid.index(t['action_values'][i]))]['statistics'][target]['mean']-t['target_value'])**2+t['cost_weight']*t['action_values'][i]**2,abs(t['action_values'][i]),t['action_values'][i]))],
            analytic_best_action=t['action_values'][min(range(len(losses)),key=lambda i:(losses[i],abs(t['action_values'][i]),t['action_values'][i]))]))
        if '__' in r['task_id'] or r['policy']!='confirmed_only':continue
        if r['graph_id'] not in model_cache:
            path=run/'datasets'/r['dataset_id']
            model_cache[r['graph_id']]=(json.loads((path/(r['algorithm']+'_models.json')).read_text(encoding='utf-8'))['primary'] if r['source_type']=='discovery' else
                json.loads((path/('controlled_'+r['variant']+'_model.json')).read_text(encoding='utf-8'))['model'])
        m=model_cache[r['graph_id']]
        predicted=static_mean_response(m,r['action'],.5)[target]-static_mean_response(m,r['action'],0)[target]
        actual=evaluation[prefix+str(grid.index(.5))]['statistics'][target]['mean']-evaluation[prefix+'reference']['statistics'][target]['mean']
        true=evaluation[prefix+str(grid.index(.5))]['post_freeze_analytic_mean'][target]
        fixed.append(dict(r,fixed_action=.5,fixed_predicted_effect=predicted,fixed_actual_effect=actual,
            fixed_effect_absolute_error=abs(predicted-actual),fixed_analytic_effect=true,fixed_analytic_error=abs(predicted-true)))
    save(out/'fixed_action_effects.json',fixed);save(out/'theoretical_vs_empirical.json',theory_rows)
    primary=[r for r in rows if r['row_status']=='EVALUATED' and r['policy']=='confirmed_only' and '__' not in r['task_id']]
    result=clustered_comparison(primary,models,**{'seed':plan['confirmation_analysis']['uncertainty']['seed'],'b':plan['confirmation_analysis']['uncertainty']['repeats']})
    contract=dict(all_twelve_structures=len({r['structure_id'] for r in primary})==12,
        sufficient_datasets=all(sum(len({r['algorithm'] for r in primary if r['dataset_id']==d})>=2 for d in {r['dataset_id'] for r in primary if r['structure_id']==sid})>=4 for sid in specs),
        skeleton_variable=len({r['skeleton_f1'] for r in primary})>1,path_variable=len({r['key_path_edge_recall'] for r in primary})>1)
    result['evaluability_checks']=contract
    if not all(contract.values()):result['judgment']='NOT_EVALUABLE'
    save(out/'CONFIRMATION_RESULT.json',result);table(out/'structure_prediction_scores.csv',result['structure_scores'])
    analytic_map={(r['graph_id'],r['task_id'],r['policy']):r['analytic_regret'] for r in theory_rows if r['source_type']=='discovery'}
    analytic_primary=[dict(r,scale_normalized_regret=analytic_map[r['graph_id'],r['task_id'],r['policy']]) for r in primary]
    save(out/'ANALYTIC_OUTCOME_SENSITIVITY.json',clustered_comparison(analytic_primary,models))
    diagnostic_rows=[r for r in rows if '__' not in r['task_id']]
    diagnostics=descriptive_diagnostics(diagnostic_rows,[r for r in fixed if r['source_type']=='discovery'])
    save(out/'diagnostics.json',diagnostics)
    primary_map={(r['graph_id'],r['task_id']):r for r in primary};pairs=[]
    for mode in ['mec_minimax','abstain_on_disagreement']:
        items=[r for r in diagnostic_rows if r['policy']==mode and r['row_status']=='EVALUATED' and (r['graph_id'],r['task_id']) in primary_map]
        deltas=[r['target_mean_loss']-primary_map[r['graph_id'],r['task_id']]['target_mean_loss'] for r in items]
        pairs.append(dict(policy=mode,matched=len(items),improved=sum(v< -1e-12 for v in deltas),worsened=sum(v>1e-12 for v in deltas),unchanged=sum(abs(v)<=1e-12 for v in deltas),
            changed_action=sum(r['recommended_action']!=primary_map[r['graph_id'],r['task_id']]['recommended_action'] for r in items),mean_loss_difference=statistics.mean(deltas) if deltas else None))
    save(out/'policy_paired_changes.json',pairs)
    sensitivity=[]
    for setting in ['primary','fine','low_cost','high_cost']:
        items=[r for r in rows if r['policy']=='confirmed_only' and r['row_status']=='EVALUATED' and tasks[r['structure_id'],r['task_id']]['setting']==setting]
        test=clustered_comparison(items,models)
        sensitivity.append(dict(setting=setting,rows=len(items),macro_mae=test['macro_mae'],delta=test['paired'][0],judgment=test['judgment'],
            same_action_as_primary=sum(r['recommended_action']==primary_map[r['graph_id'],r['task_id'].split('__')[0]]['recommended_action'] for r in items),
            unique_action_count=len({r['recommended_action'] for r in items}),interpretation='predeclared supplementary distribution shift; fixed original models, not refitted'))
    save(out/'sensitivity.json',sensitivity)
    control_pairs=[];fixed_map={(r['graph_id'],r['task_id']):r for r in fixed if r['source_type']=='controlled_error'}
    groups={}
    for r in controlled:
        if r['row_status']=='EVALUATED':groups.setdefault((r['dataset_id'],r['task_id']),{})[r['variant']]=r
    for (ds,task),g in groups.items():
        for a,b in [('remove_key','remove_peripheral'),('reverse_key','reverse_peripheral'),('remove_key_path_retained','remove_peripheral_path_retained')]:
            if a not in g or b not in g:continue
            x,y=g[a],g[b];fx,fy=fixed_map[x['graph_id'],task],fixed_map[y['graph_id'],task]
            control_pairs.append(dict(structure_id=x['structure_id'],dataset_id=ds,task_id=task,left=a,right=b,
                same_skeleton_f1=x['skeleton_f1']==y['skeleton_f1'],same_direction_f1=x['strict_directed_f1']==y['strict_directed_f1'],
                both_paths_present=bool(x['action_target_reachable'] and y['action_target_reachable']),
                left_status=x['recommendation_status'],right_status=y['recommendation_status'],
                loss_difference=x['target_mean_loss']-y['target_mean_loss'],fixed_error_difference=fx['fixed_effect_absolute_error']-fy['fixed_effect_absolute_error'],
                analytic_fixed_error_difference=fx['fixed_analytic_error']-fy['fixed_analytic_error']))
    save(out/'controlled_error_pairs.json',control_pairs)
    save(out/'controlled_not_applicable.json',[dict(structure_id=s['structure_id'],**n) for s in plan['structures'] for n in s['controlled_selection'] if n.get('status')=='NOT_APPLICABLE'])
    attempts=json.loads((run/'graph_inventory.json').read_text(encoding='utf-8'));blocks=json.loads((run/'policy_blocks.json').read_text(encoding='utf-8'))
    unique_best={(r['structure_id'],r['task_id']):(r['empirical_best_action'],r['analytic_best_action']) for r in theory_rows}
    save(out/'task_empirical_analytic_optima.json',[dict(structure_id=k[0],task_id=k[1],empirical_best=v[0],analytic_best=v[1]) for k,v in unique_best.items()])
    summary=dict(structures=len(specs),datasets=sum(len(s['datasets']) for s in specs.values()),attempts=len(attempts),learned=sum(g['status']=='LEARNED' for g in attempts),
        discovery_rows=len(rows),discovery_evaluated=sum(r['row_status']=='EVALUATED' for r in rows),primary_rows=len(primary),
        controlled_rows=len(controlled),do_samples=len(evaluation)*plan['evaluation']['n_per_batch']*plan['evaluation']['batches'],auxiliary_blocks=len(blocks),
        empirical_oracle_best_diff=sum(r['empirical_best_action']!=r['analytic_best_action'] for r in theory_rows),theory_comparison_rows=len(theory_rows),
        unique_task_settings=len(unique_best),unique_task_optimum_diff=sum(v[0]!=v[1] for v in unique_best.values()),
        conclusion=result['judgment'],macro_mae=result['macro_mae'],manufacturing_validated=False,recovery_safety='NOT_RUN',models_updated_on_confirmation=False)
    save(out/'SUMMARY.json',summary)
    save(out/'SHA256.json',{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir() if p.is_file()})
    print(json.dumps(summary,ensure_ascii=False))
def main():
    p=argparse.ArgumentParser();p.add_argument('--run',required=True);p.add_argument('--output',required=True);a=p.parse_args()
    analyze(Path(a.run),ROOT/'research_runs/independent_confirmation',Path(a.output))
if __name__=='__main__':main()

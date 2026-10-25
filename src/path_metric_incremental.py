"""Task-aware analytical evaluation. Existing S/C cohorts are development only."""
import gzip,json,math,statistics
from collections import defaultdict
from pathlib import Path

from decision_mvp import static_mean_response,reachable
from diverse_structure_pilot import analytic_response,reference_edges,all_paths,score_graph
from diverse_metric_analysis import weighted_predict
from independent_confirmation import predict_frozen

CONTEXT=['algorithm_boss','algorithm_directlingam','log_n','n_nodes','predicted_density','unresolved_ratio',
 'policy_mec','policy_abstain','target_goal','goal_gap','goal_gap_squared','goal_gap_std','log_target_sd','log_action_sd',
 'reference_offset_std','range_std','grid_step_std','grid_count','cost_range_squared','cost_to_target_variance',
 'action_indegree','action_outdegree','target_indegree','target_outdegree','predicted_path','predicted_distance',
 'log_predicted_path_count','fit_available','mec_available','estimated_slope','log_abs_estimated_slope','surrogate_reference_gap']
QUALITY=['skeleton_f1','strict_directed_f1','key_path_edge_recall']
MODELS={'M0':CONTEXT,'M1':CONTEXT+QUALITY[:1],'M2':CONTEXT+QUALITY[2:],
 'M3':CONTEXT+QUALITY[1:2],'M4':CONTEXT+[QUALITY[0],QUALITY[2]],'M5':CONTEXT+QUALITY[:2],'M6':CONTEXT+QUALITY}

def raw(p):
    p=Path(p);return p.read_bytes() if p.exists() else gzip.decompress(Path(str(p)+'.gz').read_bytes())
def load(p):return json.loads(raw(p).decode('utf-8-sig'))

def linear_moments(spec,action,value):
    """Independent matrix calculation; does not call the sampler or forecaster."""
    import numpy as np
    names=spec['nodes'];i={n:j for j,n in enumerate(names)};b=np.zeros((len(names),len(names)))
    for e in spec['edges']:b[i[e['target']],i[e['source']]]=e['coefficient']
    b[i[action],:]=0;noise=np.diag([spec['noise_sd'][n]**2 if n!=action else 0. for n in names])
    t=np.linalg.inv(np.eye(len(names))-b);command=np.zeros(len(names));command[i[action]]=value
    means=t@command;cov=t@noise@t.T
    return {n:float(means[j]) for j,n in enumerate(names)},{n:float(cov[j,j]) for j,n in enumerate(names)}

def loss_contract(spec,task,chosen):
    grid=task['action_values'];goal=task['target_value'];ref=task['reference_action'];scale=task['loss_scale']**2
    means=[linear_moments(spec,task['action'],v)[0][task['target']] for v in grid]
    for v,m in zip(grid,means):assert math.isclose(m,analytic_response(spec,task['action'],v)[task['target']],rel_tol=1e-10,abs_tol=1e-10)
    losses=[(m-goal)**2+task['cost_weight']*(v-ref)**2 for m,v in zip(means,grid)]
    index=grid.index(chosen);best=min(range(len(grid)),key=lambda k:(losses[k],abs(grid[k]),grid[k]))
    baseline=(linear_moments(spec,task['action'],ref)[0][task['target']]-goal)**2
    return dict(analytic_mean=means[index],analytic_loss=losses[index],analytic_regret=(losses[index]-losses[best])/scale,
        oracle_best_action=grid[best],oracle_best_loss=losses[best],oracle_reference_loss=baseline,
        oracle_improvement_gap=baseline-losses[best],normalizer=scale,
        oracle_total_effect=linear_moments(spec,task['action'],1.)[0][task['target']])

def task_features(frame,graph,model,task,policy,mec_available):
    """No GT, oracle effect, chosen action or evaluation outcome accepted."""
    import numpy as np
    permitted={'action','target','target_value','reference_action','action_values','cost_weight','loss_scale'}
    assert set(task)<=permitted,'only explicitly pre-decision task fields are permitted'
    a,y=task['action'],task['target'];names=list(frame.columns);n=len(names)
    edges=set(map(tuple,graph.get('confirmed_edges',[])));u=set(map(frozenset,graph.get('unresolved_pairs',[])))
    sy=float(frame[y].std(ddof=0));sa=float(frame[a].std(ddof=0));assert sy>0 and sa>0
    my=float(frame[y].mean());ma=float(frame[a].mean());grid=sorted(task['action_values']);width=grid[-1]-grid[0]
    paths=all_paths(edges,a,y);dist=min((len(p)-1 for p in paths),default=0)
    slope=reference_gap=None
    if model:
        ref=static_mean_response(model,a,task['reference_action'])[y]
        slope=(static_mean_response(model,a,.5)[y]-static_mean_response(model,a,0.)[y])/.5
        reference_gap=task['target_value']-ref
    degree=lambda v,source:sum((x if source else z)==v for x,z in edges)/(n-1)
    return dict(target_goal=task['target_value'],goal_gap=task['target_value']-my,goal_gap_squared=(task['target_value']-my)**2,
        goal_gap_std=(task['target_value']-my)/sy,log_target_sd=math.log(sy),log_action_sd=math.log(sa),
        reference_offset_std=(task['reference_action']-ma)/sa,range_std=width/sa,grid_step_std=min(b-a for a,b in zip(grid,grid[1:]))/sa,
        grid_count=len(grid),cost_range_squared=task['cost_weight']*width**2,cost_to_target_variance=task['cost_weight']*width**2/sy**2,
        action_indegree=degree(a,False),action_outdegree=degree(a,True),target_indegree=degree(y,False),target_outdegree=degree(y,True),
        predicted_path=float(bool(paths)),predicted_distance=dist/(n-1),log_predicted_path_count=math.log1p(len(paths)),
        fit_available=float(model is not None),mec_available=float(mec_available),estimated_slope=slope,
        log_abs_estimated_slope=None if slope is None else math.log1p(abs(slope)),surrogate_reference_gap=reference_gap,
        policy_mec=float(policy=='mec_minimax'),policy_abstain=float(policy=='abstain_on_disagreement'))

def development_rows(root):
    import pandas as pd
    output=[];oracle=[];inputs=[]
    for cohort,folder in [('S','diverse_structure_pilot'),('C','independent_confirmation')]:
        base=Path(root)/'research_runs'/folder;run=base/'run_v1';plan=load(base/'PLAN_v1.json')
        specs={s['structure_id']:s for s in plan['structures']};graphs={g['graph_id']:g for g in load(run/'graph_inventory.json')}
        evaluation=load(run/'intervention_evaluation.json');frozen=load(run/'recommendations_frozen.json');model_cache={};data_cache={}
        for record in frozen:
            if '__' in record['task_id'] or record['task_kind']=='negative_control':continue
            spec=specs[record['structure_id']];task=next(t for t in spec['tasks'] if t['task_id']==record['task_id'])
            graph=graphs[record['graph_id']];gid=graph['graph_id'];ds=record['dataset_id'];path=run/'datasets'/ds
            if ds not in data_cache:data_cache[ds]=pd.read_csv(path/'train.csv')
            if gid not in model_cache:
                f=path/(graph['algorithm']+'_models.json')
                model_cache[gid]=load(f) if f.exists() or Path(str(f)+'.gz').exists() else None
            artifact=model_cache[gid];model=artifact['primary'] if artifact else None
            ready=record['row_status']=='FROZEN' and 'recommendation' in record
            rec=record.get('recommendation');selected=rec['selected']['action'] if ready else task['reference_action']
            fields={k:task[k] for k in ['action','target','target_value','reference_action','action_values','cost_weight','loss_scale']}
            features=task_features(data_cache[ds],graph,model,fields,record['policy'],bool(artifact and artifact.get('extensions')))
            q=score_graph(set(map(tuple,graph['confirmed_edges'])),set(map(frozenset,graph['unresolved_pairs'])),spec,task)
            truth=loss_contract(spec,task,selected);prefix=record['structure_id']+'__'+task['action']+'__'
            grid=plan['evaluation'].get('candidate_union',task['action_values'])
            empirical=[(evaluation[prefix+str(grid.index(v))]['statistics'][task['target']]['mean']-task['target_value'])**2+task['cost_weight']*(v-task['reference_action'])**2 for v in task['action_values']]
            empirical_loss=empirical[task['action_values'].index(selected)]
            reason=('AVAILABLE' if ready else 'CYCLIC_OUTPUT' if model is None and not __import__('repeated_metric_pilot').acyclic(spec['nodes'],set(map(tuple,graph['confirmed_edges']))) else 'FIT_OR_LEARN_FAILED' if model is None else 'DAG_COMPLETION_OR_POLICY_FAILED')
            row=dict(record,cohort=cohort,setting='primary',action=task['action'],target=task['target'],
                pipeline_ready=ready,computed_recommendation=bool(ready and rec['status'] in {'COMPUTED_RECOMMENDATION','COMPUTED_BASELINE'}),
                operational_action=selected,original_attempt_status=record['row_status'],failure_type=reason,
                recommendation_status=rec['status'] if ready else 'OPERATIONAL_REFERENCE_AFTER_FAILURE',
                source_type='discovery',row_status='EVALUATED',**q,**features)
            row.pop('recommendation',None)
            row.update(truth,scale_normalized_regret=truth['analytic_regret'],conditional_regret=truth['analytic_regret'] if ready else None,
                empirical_operational_regret=(empirical_loss-min(empirical))/truth['normalizer'],empirical_mean_loss=empirical_loss)
            if model:
                pred=(static_mean_response(model,task['action'],.5)[task['target']]-static_mean_response(model,task['action'],0)[task['target']])
                actual=linear_moments(spec,task['action'],.5)[0][task['target']]-linear_moments(spec,task['action'],0)[0][task['target']]
                row.update(fixed_effect_error=abs(pred-actual),fixed_predicted_effect=pred,fixed_true_effect=actual)
            else:row.update(fixed_effect_error=None,fixed_predicted_effect=None,fixed_true_effect=None)
            output.append(row)
            if record['policy']=='confirmed_only':
                paths=all_paths(reference_edges(spec),task['action'],task['target'])
                oracle.append(dict(structure_id=spec['structure_id'],dataset_id=ds,graph_id=gid,task_id=task['task_id'],
                    true_paths=len(paths),true_shortest=min(len(p)-1 for p in paths),true_longest=max(len(p)-1 for p in paths),**truth,
                    observed_target_sd=float(data_cache[ds][task['target']].std(ddof=0)),goal=task['target_value'],chosen=selected,
                    recommendation_status=row['recommendation_status'],metrics={k:q[k] for k in QUALITY},
                    estimated_slope=features['estimated_slope'],model_available=model is not None))
        inputs.append(dict(cohort=cohort,run=run.as_posix(),plan=plan,graph_count=len(graphs)))
    return output,oracle,inputs

def fit_predict(train,test,features):
    p,m=weighted_predict(train,test,features,.01)
    return [max(0.,x) for x in p],dict(m,nonnegative_forecast_constraint=True)

def development_cv(rows,features_by_model=None):
    models=features_by_model or MODELS;predictions=[];artifacts=[];scores=[]
    for held in sorted({r['structure_id'] for r in rows}):
        train=[r for r in rows if r['structure_id']!=held];test=[r for r in rows if r['structure_id']==held]
        for name,features in models.items():
            pred,artifact=fit_predict(train,test,features);artifacts.append(dict(model=name,held_out=held,**artifact))
            error=[]
            for r,p in zip(test,pred):
                e=abs(p-r['scale_normalized_regret']);error.append(e)
                predictions.append(dict(model=name,structure_id=held,graph_id=r['graph_id'],dataset_id=r['dataset_id'],task_id=r['task_id'],policy=r['policy'],algorithm=r['algorithm'],train_n=r['train_n'],actual=r['scale_normalized_regret'],prediction=p,absolute_error=e,pipeline_ready=r['pipeline_ready']))
            scores.append(dict(model=name,structure_id=held,mae=statistics.mean(error),rows=len(error)))
    return dict(predictions=predictions,artifacts=artifacts,structure_scores=scores,
        macro_mae={m:statistics.mean(r['mae'] for r in scores if r['model']==m) for m in models},scope='development LOSO only, not independent confirmation')

def precision_gate(result,design):
    scores={(r['structure_id'],r['model']):r['mae'] for r in result['structure_scores']};ids=sorted({r['structure_id'] for r in result['structure_scores']});records=[]
    for left,right in [('M1','M4'),('M5','M6')]:
        delta=[scores[s,left]-scores[s,right] for s in ids];sd=statistics.stdev(delta)
        # Include the fixed three C-family strata and the old hand-designed S cohort.
        groups=[[d for s,d in zip(ids,delta) if (s.startswith('S') if g=='S' else s.startswith('C') and (int(s[1:])-1)//4==g)] for g in ['S',0,1,2]]
        strata=max((statistics.stdev(g) for g in groups if len(g)>1),default=sd);used=max(sd,strata)
        n=math.ceil((1.96*used/design['planning']['desired_95_interval_halfwidth'])**2)
        n=max(design['planning']['independent_structure_min'],3*math.ceil(n/3))
        records.append(dict(left=left,right=right,development_delta_mean=statistics.mean(delta),paired_structure_sd=sd,worst_family_sd=strata,planning_sd=used,required_structures=n,delta_by_structure=dict(zip(ids,delta)),
            sd_without_C07=statistics.stdev([v for s,v in zip(ids,delta) if s!='C07']),scope='rough development-based interval width calculation; no power guarantee'))
    required=max(r['required_structures'] for r in records);budget=design['planning'];calls=required*budget['replicates']*budget['algorithms']
    return dict(status='PASS' if required<=budget['max_structures'] and calls<=budget['max_learning_calls'] else 'BLOCKED_PRECISION_RESOURCE',comparisons=records,
        required_structures=required,planned_learning_calls=calls,max_structures=budget['max_structures'],max_learning_calls=budget['max_learning_calls'],
        practical_increment=budget['practical_increment'],interval_halfwidth=budget['desired_95_interval_halfwidth'],new_reference_structures_generated=0,
        note='Do not reduce precision target or discard C07 after observing planning variance. Bootstrap20 is planning uncertainty, not a guarantee.')

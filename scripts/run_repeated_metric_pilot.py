"""Run the fixed 12-dataset/36-graph synthetic protocol, preserving older results."""
import argparse
import csv
from datetime import datetime,timezone
import hashlib
import importlib.metadata
import json
import math
from pathlib import Path
import platform
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from fcm_acceptance_adapter import load_pinned_module
from integrated_pilot import learn_graph,fit_model,validation_mse
from repeated_metric_pilot import (draw_any,consistent_extensions,recommend_policy,quality,
    describe_mean,analytic_mean,exploratory_associations)


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def save(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def table(path,rows):
    if not rows:return
    with Path(path).open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)


def check_api(module,plan,folder):
    import numpy as np
    import pandas as pd
    folder.mkdir();records=[]
    for fi,family in enumerate(plan['families']):
        seed=plan['acceptance']['seeds'][fi]
        for action in plan['acceptance']['actions']:
            for value in plan['acceptance']['values']:
                frame,noise,meta=draw_any(module,seed,plan['acceptance']['n'],family,plan,action,value)
                repeat,_,_=draw_any(module,seed,len(frame),family,plan,action,value)
                plain,_,_=draw_any(module,seed,len(frame),family,plan,action,value,hook=False)
                g=meta['intervention'];truth={tuple(e) for e in plan['reference_edges']}
                checks=dict(exact_repeat=frame.equals(repeat),hook_transparent=frame.equals(plain),
                    equations=max(meta['reconstruction_errors'].values())<1e-10,
                    returned_gt={tuple(e) for e in meta['reference_returned_edges']}==truth,
                    intervened_edges={tuple(e) for e in g['edges']}=={e for e in truth if e[1]!=action},
                    replaced_equation=float(g['term'])==value,removed_parents=g['parents']==[],
                    removed_noise='u_'+action not in noise,other_equations=g['other_equations_unchanged'],
                    action_constant=bool((frame[action]==value).all()))
                if family=='uniform':checks['noise_range']=all(bool((np.abs(v)<=plan['noise']['uniform_half_width'][k]+1e-12).all()) for k,v in noise.items())
                tag=f'{family}_{action}_{value}'
                frame.to_csv(folder/f'{tag}.csv',index=False);pd.DataFrame(noise).to_csv(folder/f'{tag}_noise.csv',index=False)
                records.append(dict(family=family,seed=seed,action=action,value=value,checks=checks,metadata=meta))
    result=dict(status='PASS' if all(all(r['checks'].values()) for r in records) else 'FAIL',records=records)
    save(folder/'api_acceptance.json',result)
    if result['status']!='PASS':raise ValueError('NEW_ACTION_API_ACCEPTANCE_FAILED_NO_LEARNING')


def main():
    p=argparse.ArgumentParser();p.add_argument('--module',required=True);p.add_argument('--output',required=True)
    args=p.parse_args();out=Path(args.output).resolve()
    if out.exists():raise ValueError('NEW_OUTPUT_REQUIRED')
    if sys.prefix==sys.base_prefix:raise ValueError('ISOLATED_VENV_REQUIRED')
    out.mkdir(parents=True);failures=[];ledger=[]
    def event(stage,**kw):
        ledger.append(dict(sequence=len(ledger),utc=datetime.now(timezone.utc).isoformat(),stage=stage,**kw))
        save(out/'execution_ledger.json',ledger);print(stage,kw,flush=True)
    def failed(stage,exc,**kw):
        item=dict(failed_stage=stage,error=type(exc).__name__+': '+str(exc),**kw);failures.append(item);save(out/'failures.json',failures);event('RECORDED_FAILURE',**item)
    plan_path=ROOT/'research_runs/repeated_metric_pilot/PLAN_v1.json'
    plan=json.loads(plan_path.read_text(encoding='utf-8'));save(out/'plan.json',plan)
    event('PLAN_FROZEN',sha256=sha(plan_path))
    import numpy as np
    import pandas as pd
    module=load_pinned_module(args.module)
    environment=dict(python=platform.python_version(),platform=platform.platform(),upstream_source_sha256=sha(args.module),
        source_commit=plan['source_commit'],base_main=plan['base_main'],plan_sha256=sha(plan_path),
        versions={n:importlib.metadata.version(n) for n in ['numpy','pandas','scipy','sympy','networkx','causal-learn','lingam','scikit-learn']},
        code_sha256={name:sha(ROOT/name) for name in ['scripts/run_repeated_metric_pilot.py','src/repeated_metric_pilot.py','src/integrated_pilot.py','src/decision_mvp.py','src/pilot_fit.py','src/fcm_acceptance_adapter.py']},
        command='python -X utf8 scripts/run_repeated_metric_pilot.py --module <pinned-models_fcm.py> --output research_runs/repeated_metric_pilot/run_v1')
    save(out/'environment.json',environment)
    (out/'requirements.lock.txt').write_text(subprocess.check_output([sys.executable,'-m','pip','freeze','--all'],text=True),encoding='utf-8')
    try:check_api(module,plan,out/'api_acceptance')
    except Exception as exc:
        failed('API_ACCEPTANCE',exc);return 2
    event('API_ACCEPTANCE_PASSED',actions=plan['acceptance']['actions'])
    graphs=[];recommendations=[];memory={};attempts=0
    for cell in plan['datasets']:
        started=time.monotonic();dataset=cell['dataset_id'];folder=out/'datasets'/dataset;folder.mkdir(parents=True)
        family=cell['family'];frames={}
        for split in ['train','validation']:
            frame,noise,meta=draw_any(module,cell[split+'_seed'],cell[split+'_n'],family,plan)
            frame.to_csv(folder/f'{split}.csv',index=False);pd.DataFrame(noise).to_csv(folder/f'{split}_noise.csv',index=False)
            save(folder/f'{split}_generation.json',dict(seed=cell[split+'_seed'],metadata=meta));frames[split]=frame
        names=plan['algorithm_column_order'];train=frames['train'][names].to_numpy();valid=frames['validation'][names].to_numpy()
        z=(train-train.mean(axis=0))/train.std(axis=0,ddof=0);eligible={}
        for alg in ['pc','boss','directlingam']:
            attempts+=1;t0=time.monotonic();graph_id=dataset+'__'+alg
            try:
                edges,unresolved,native=learn_graph(z,names,alg,cell['algorithm_seed'],family,plan)
                record=dict(graph_id=graph_id,**cell,algorithm=alg,status='LEARNED',confirmed_edges=sorted(edges),
                    unresolved_pairs=sorted(sorted(e) for e in unresolved),native=native,seconds=time.monotonic()-t0,
                    assumption_role=plan['families'][family]['directlingam_role'] if alg=='directlingam' else 'PRIMARY_COMPARISON')
                save(folder/f'{alg}_graph.json',record);graphs.append(record)
                fit_model(train,names,edges,plan['scm']['alpha_grid'][0])
                eligible[alg]=(edges,unresolved,native,record)
                event('GRAPH_LEARNED',graph_id=graph_id,seconds=record['seconds'])
            except Exception as exc:
                failed('GRAPH_LEARNING_OR_FIT',exc,graph_id=graph_id)
                if not any(g['graph_id']==graph_id for g in graphs):
                    record=dict(graph_id=graph_id,**cell,algorithm=alg,status='FAILED',error=str(exc))
                    graphs.append(record);save(folder/f'{alg}_graph.json',record)
        selection=[a for a in eligible if family!='gaussian' or a!='directlingam']
        if not selection:
            failed('ALPHA_SELECTION',ValueError('NO_ELIGIBLE_COMPARISON_GRAPH'),dataset_id=dataset);continue
        scores=[]
        for alpha in plan['scm']['alpha_grid']:
            losses={a:validation_mse(fit_model(train,names,eligible[a][0],alpha),valid,names) for a in selection}
            scores.append(dict(alpha=alpha,per_graph_validation_mse=losses,mean_validation_mse=float(np.mean(list(losses.values())))))
        alpha=min(scores,key=lambda r:(r['mean_validation_mse'],-r['alpha']))['alpha']
        save(folder/'alpha_selection.json',dict(selected_alpha=alpha,selection_algorithms=selection,scores=scores,scope='observational validation only, no effect holdout'))
        for alg,(edges,unresolved,native,g) in eligible.items():
            base=fit_model(train,names,edges,alpha);extension_edges=[];extension_models=[];extension_failure=None
            try:
                extension_edges=consistent_extensions(plan['nodes'],edges,unresolved,native,plan['policy']['mec_max_unresolved'])
                extension_models=[fit_model(train,names,e,alpha) for e in extension_edges]
            except Exception as exc:
                extension_failure=type(exc).__name__+': '+str(exc);failed('PDAG_EXTENSIONS',exc,graph_id=g['graph_id'])
            save(folder/f'{alg}_models.json',dict(primary=base,extensions=[dict(edges=sorted(e),model=m) for e,m in zip(extension_edges,extension_models)],extension_failure=extension_failure))
            memory[g['graph_id']]=(edges,unresolved)
            for task in plan['tasks']:
                for mode in plan['policy']['modes']:
                    info=dict(graph_id=g['graph_id'],dataset_id=dataset,family=family,train_n=cell['train_n'],replicate=cell['replicate'],algorithm=alg,
                        assumption_role=g['assumption_role'],task_id=task['task_id'],action=task['action'],target=task['target'],policy=mode)
                    try:
                        if mode!='confirmed_only' and extension_failure:raise ValueError(extension_failure)
                        rec=recommend_policy([base] if mode=='confirmed_only' else extension_models,[edges] if mode=='confirmed_only' else extension_edges,task,plan['policy'],mode)
                        recommendations.append(dict(**info,row_status='RECOMMENDATION_FROZEN',recommendation=rec))
                    except Exception as exc:
                        recommendations.append(dict(**info,row_status='POLICY_BLOCKED',error=str(exc)))
        event('DATASET_COMPLETED',dataset_id=dataset,seconds=time.monotonic()-started,learned_algorithms=len(eligible),alpha=alpha)
        if dataset==plan['datasets'][0]['dataset_id']:
            event('SMALL_CELL_FEASIBILITY_RECORDED',attempts=attempts,seconds=time.monotonic()-started,
                next_action='continue only remaining cells already fixed in plan; no extra repetitions')
    save(out/'graph_inventory.json',graphs)
    frozen=out/'recommendations_frozen.json';save(frozen,recommendations);frozen_sha=sha(frozen)
    event('ALL_RECOMMENDATIONS_FROZEN',attempted_graphs=attempts,rows=len(recommendations),sha256=frozen_sha)
    # Only now expose declared reference paths/edges to graph scoring.
    metrics={}
    for row in recommendations:
        edges,unresolved=memory[row['graph_id']]
        task=next(t for t in plan['tasks'] if t['task_id']==row['task_id'])
        metrics[row['graph_id']+'__'+row['task_id']]=quality(edges,unresolved,plan['reference_edges'],task)
    save(out/'structural_metrics.json',metrics)
    evaluation={};rawfolder=out/'do_evaluation';rawfolder.mkdir()
    for family in plan['families']:
        for ai,action in enumerate(plan['evaluation']['actions']):
            for vi,value in enumerate(plan['policy']['action_values']+[plan['policy']['reference_action']]):
                tag=f'{family}__{action}__'+('independent_reference' if vi==5 else str(vi));frames=[];noises=[];batches=[]
                for batch in range(plan['evaluation']['batches']):
                    seed=plan['evaluation']['seed_base'][family]+ai*10000+vi*100+batch
                    frame,noise,meta=draw_any(module,seed,plan['evaluation']['n_per_batch'],family,plan,action,value)
                    data=frame.copy();data.insert(0,'sample_id',range(len(data)));data.insert(0,'seed',seed);data.insert(0,'batch',batch)
                    u=pd.DataFrame(noise);u.insert(0,'sample_id',range(len(u)));u.insert(0,'seed',seed);u.insert(0,'batch',batch)
                    frames.append(data);noises.append(u);batches.append(dict(seed=seed,batch=batch,metadata=meta))
                data=pd.concat(frames,ignore_index=True);noise=pd.concat(noises,ignore_index=True)
                data.to_csv(rawfolder/f'{tag}.csv',index=False);noise.to_csv(rawfolder/f'{tag}_noise.csv',index=False)
                stats={v:describe_mean(data[v]) for v in plan['nodes']}
                checks={v:dict(analytic_mean=analytic_mean(action,v,value),mean_difference=stats[v]['mean']-analytic_mean(action,v,value)) for v in plan['nodes']}
                evaluation[tag]=dict(family=family,action=action,value=value,batches=batches,statistics=stats,post_freeze_analytic_check=checks)
            event('ACTION_HOLDOUT_GENERATED',family=family,action=action)
    if sha(frozen)!=frozen_sha:raise ValueError('POLICY_MUTATED_AFTER_HOLDOUT')
    save(out/'intervention_evaluation.json',evaluation)
    rows=[]
    for record in recommendations:
        if record['row_status']!='RECOMMENDATION_FROZEN':continue
        task=next(t for t in plan['tasks'] if t['task_id']==record['task_id']);rec=record['recommendation'];selected=rec['selected']
        family=record['family'];action=task['action'];target=task['target'];grid=plan['policy']['action_values']
        base=evaluation[f'{family}__{action}__independent_reference']['statistics'][target]
        losses=[]
        for vi,value in enumerate(grid):
            actual=evaluation[f'{family}__{action}__{vi}']['statistics'][target]
            losses.append((actual['mean']-task['target_value'])**2+plan['policy']['cost_weight']*value**2)
        i=grid.index(selected['action']);actual=evaluation[f'{family}__{action}__{i}']['statistics'][target]
        reference_loss=(base['mean']-task['target_value'])**2
        regret=losses[i]-min(losses);denom=reference_loss-min(losses)
        effect=actual['mean']-base['mean'];se=math.hypot(actual['se'],base['se'])
        row={k:v for k,v in record.items() if k not in ['recommendation','row_status']}
        row.update(row_status='EVALUATED',**metrics[record['graph_id']+'__'+record['task_id']],
            recommendation_status=rec['status'],extension_count=rec['extension_count'],recommended_action=selected['action'],
            predicted_target=selected['predicted_y'],predicted_target_min=selected['predicted_y_min'],predicted_target_max=selected['predicted_y_max'],
            actual_target_mean=actual['mean'],actual_target_se=actual['se'],actual_target_ci_low=actual['ci_low'],actual_target_ci_high=actual['ci_high'],
            mean_prediction_absolute_error=abs(selected['predicted_y']-actual['mean']),target_gap=actual['mean']-task['target_value'],
            action_cost=selected['cost'],target_mean_loss=losses[i],candidate_regret=regret,reference_mean_loss=reference_loss,
            relative_regret=regret/max(reference_loss,1e-12),fraction_reference_gap_lost=regret/denom if denom>1e-8 else None,
            predicted_effect=selected['predicted_effect'],predicted_effect_min=selected['predicted_effect_min'],predicted_effect_max=selected['predicted_effect_max'],
            actual_effect=effect,effect_se=se,effect_ci_low=effect-1.96*se,effect_ci_high=effect+1.96*se,
            effect_prediction_absolute_error=abs(selected['predicted_effect']-effect),
            worst_extension_effect_error=max(abs(selected['predicted_effect_min']-effect),abs(selected['predicted_effect_max']-effect)),
            squared_individual_error_mean_not_computed=True)
        rows.append(row)
    save(out/'comparison.json',rows);table(out/'comparison.csv',rows)
    associations=exploratory_associations(rows,plan);save(out/'exploratory_associations.json',associations);table(out/'exploratory_associations.csv',associations)
    formal=dict(status='INSUFFICIENT_INDEPENDENT_REPETITIONS',dataset_clusters=12,clusters_per_noise=6,clusters_per_noise_size=3,
        minimum_per_noise_size=plan['analysis']['formal_inference']['min_datasets_per_noise_size'],
        no_p_values_or_metric_winner=True,scope='descriptive correlations/deletion sensitivities only; not causal effects of graph metrics')
    save(out/'analysis_scope.json',formal);save(out/'failures.json',failures)
    event('COMPLETED',graph_attempts=attempts,learned_graphs=sum(g['status']=='LEARNED' for g in graphs),evaluated_rows=len(rows),failure_records=len(failures))
    save(out/'SHA256.json',{p.relative_to(out).as_posix():sha(p) for p in sorted(out.rglob('*')) if p.is_file() and p.name!='SHA256.json'})
    return 0 if attempts==36 and len(rows)==432 and not failures else 2


if __name__=='__main__':
    try:sys.exit(main())
    except Exception as exc:
        print('FAILED',type(exc).__name__,str(exc),flush=True)
        raise

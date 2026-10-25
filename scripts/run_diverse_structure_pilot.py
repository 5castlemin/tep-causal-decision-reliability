"""Predeclared eight-structure experiment. Never mutates previous research runs."""
import argparse
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
import csv

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from fcm_acceptance_adapter import load_pinned_module
from integrated_pilot import fit_model,validation_mse
from repeated_metric_pilot import consistent_extensions,recommend_policy,describe_mean
from diverse_structure_pilot import (draw_structure,reference_edges,score_graph,analytic_response,controlled_graphs)

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def table(p,rows):
    if not rows:return
    keys=list(dict.fromkeys(k for r in rows for k in r))
    with Path(p).open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(rows)


def verify_structure(module,spec,folder,plan):
    import pandas as pd
    import numpy as np
    folder.mkdir(parents=True);seed=spec['acceptance_seed'];n=plan['acceptance']['n'];records=[]
    original,u,meta=draw_structure(module,spec,seed,n)
    twin,_,_=draw_structure(module,spec,seed,n);fresh,_,_=draw_structure(module,spec,seed+1,n)
    plain,_,_=draw_structure(module,spec,seed,n,hook=False)
    checks=dict(returned_gt={tuple(e) for e in meta['returned_edges']}==reference_edges(spec),
        observation_equations=max(meta['reconstruction_errors'].values())<1e-10,
        exact_repeat=original.equals(twin),new_seed_different=not original.equals(fresh),hook_transparent=original.equals(plain))
    original.to_csv(folder/'observational.csv',index=False);pd.DataFrame(u).to_csv(folder/'observational_noise.csv',index=False)
    fresh.to_csv(folder/'new_seed_observational.csv',index=False)
    records.append(dict(condition='observational',seed=seed,checks=checks,metadata=meta))
    actions=list(dict.fromkeys(t['action'] for t in spec['tasks']))
    for ai,action in enumerate(actions):
        for vi,value in enumerate(plan['acceptance']['values']):
            active_seed=seed+100+ai*20+vi
            data,noise,m=draw_structure(module,spec,active_seed,n,action,value)
            repeated,_,_=draw_structure(module,spec,active_seed,n,action,value)
            plain,_,_=draw_structure(module,spec,active_seed,n,action,value,hook=False)
            g=m['intervention']
            checks=dict(returned_gt={tuple(e) for e in m['returned_edges']}==reference_edges(spec),
                reconstructed=max(m['reconstruction_errors'].values())<1e-10,
                exact_repeat=data.equals(repeated),hook_transparent=data.equals(plain),
                action_constant=bool((data[action]==value).all()),removed_parents=g['parents']==[],
                replaced_equation=float(g['term'])==value,other_equations_unchanged=g['other_equations_unchanged'],
                removed_noise='u_'+action not in noise,
                correct_mutilated_graph={tuple(e) for e in g['edges']}=={e for e in reference_edges(spec) if e[1]!=action},
                uniform_noise_ranges=all(bool((np.abs(v)<=math.sqrt(3)*spec['noise_sd'][k[2:]]+1e-12).all()) for k,v in noise.items()))
            tag=f'{action}_{value}';data.to_csv(folder/f'{tag}.csv',index=False);pd.DataFrame(noise).to_csv(folder/f'{tag}_noise.csv',index=False)
            records.append(dict(condition='do',action=action,value=value,seed=active_seed,checks=checks,metadata=m))
    result=dict(structure_id=spec['structure_id'],status='PASS' if all(all(r['checks'].values()) for r in records) else 'FAIL',records=records)
    save(folder/'acceptance.json',result)
    if result['status']!='PASS':raise ValueError('STRUCTURE_ACCEPTANCE_FAILED_'+spec['structure_id'])
    return result


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--module',required=True);parser.add_argument('--output',required=True);parser.add_argument('--raw-log-dir',required=True)
    args=parser.parse_args();out=Path(args.output).resolve();raw_logs=Path(args.raw_log_dir).resolve()
    if out.exists() or raw_logs.exists():raise ValueError('NEW_OUTPUT_AND_LOG_DIRECTORY_REQUIRED')
    if sys.prefix==sys.base_prefix:raise ValueError('ISOLATED_VENV_REQUIRED')
    out.mkdir(parents=True);raw_logs.mkdir(parents=True);ledger=[];failures=[];blocks=[]
    plan_path=ROOT/'research_runs/diverse_structure_pilot/PLAN_v1.json';plan=json.loads(plan_path.read_text(encoding='utf-8'));save(out/'plan.json',plan)
    def event(stage,**kw):
        ledger.append(dict(sequence=len(ledger),utc=datetime.now(timezone.utc).isoformat(),stage=stage,**kw));save(out/'execution_ledger.json',ledger);print(stage,kw,flush=True)
    def fail(stage,error,**kw):
        message=str(error).replace(str(ROOT),'<repo>').replace(str(Path.home()),'<user>')
        value=dict(failed_stage=stage,error=message,**kw);failures.append(value);save(out/'failures.json',failures);event('FAILURE_RECORDED',**value)
    event('PLAN_FROZEN',sha256=sha(plan_path))
    import numpy as np
    import pandas as pd
    module=load_pinned_module(args.module)
    save(out/'environment.json',dict(python=platform.python_version(),platform=platform.platform(),base_commit=plan['base_commit'],
        source_commit=plan['source_commit'],upstream_source_sha256=sha(args.module),plan_sha256=sha(plan_path),
        versions={n:importlib.metadata.version(n) for n in ['numpy','pandas','sympy','scipy','networkx','causal-learn','lingam','scikit-learn']},
        code_sha256={n:sha(ROOT/n) for n in ['scripts/run_diverse_structure_pilot.py','scripts/learn_diverse_graph.py','src/diverse_structure_pilot.py','src/repeated_metric_pilot.py','src/integrated_pilot.py','src/decision_mvp.py','src/pilot_fit.py','src/fcm_acceptance_adapter.py']},
        command='python -X utf8 scripts/run_diverse_structure_pilot.py --module <pinned models_fcm.py> --output research_runs/diverse_structure_pilot/run_v1 --raw-log-dir <task archive>/learner_original_console'))
    (out/'requirements.lock.txt').write_text(subprocess.check_output([sys.executable,'-m','pip','freeze','--all'],text=True),encoding='utf-8')
    specs={s['structure_id']:s for s in plan['structures']}
    for ids,stage in [(plan['acceptance']['first_stage'],'FIRST_TWO_GENERATORS_PASSED'),(plan['acceptance']['all_stage'][2:],'ALL_EIGHT_GENERATORS_PASSED')]:
        try:
            for sid in ids:verify_structure(module,specs[sid],out/'acceptance'/sid,plan)
        except Exception as exc:
            fail('GENERATOR_ACCEPTANCE',exc);return 2
        event(stage,structures=ids)
    save(out/'declared_structures.json',plan['structures'])
    inventory=[];recommendations=[];controls=[];graph_memory={};graph_attempts=0
    for spec in plan['structures']:
        sid=spec['structure_id'];names=spec['algorithm_column_order']
        for cell in spec['datasets']:
            dataset=cell['dataset_id'];folder=out/'datasets'/dataset;folder.mkdir(parents=True);frames={};eligible={}
            for split in ['train','validation']:
                frame,noise,meta=draw_structure(module,spec,cell[split+'_seed'],cell[split+'_n'])
                frame.to_csv(folder/f'{split}.csv',index=False);pd.DataFrame(noise).to_csv(folder/f'{split}_noise.csv',index=False)
                save(folder/f'{split}_generation.json',dict(seed=cell[split+'_seed'],metadata=meta))
                frames[split]=pd.read_csv(folder/f'{split}.csv')
            train=frames['train'][names].to_numpy();valid=frames['validation'][names].to_numpy()
            for alg in ['pc','boss','directlingam']:
                graph_attempts+=1;gid=dataset+'__'+alg
                cfg=dict(algorithm=alg,seed=cell['algorithm_seed'],names=names,algorithms=plan['algorithms'],families=plan['families'],train_sha256=sha(folder/'train.csv'))
                save(folder/f'{alg}_learner_config.json',cfg)
                cmd=[sys.executable,'-X','utf8',str(ROOT/'scripts/learn_diverse_graph.py'),'--train',str(folder/'train.csv'),'--config',str(folder/f'{alg}_learner_config.json'),'--output',str(folder/f'{alg}_graph.json')]
                event('GRAPH_ATTEMPT_STARTED',graph_id=gid,timeout_seconds=plan['learner_timeout_seconds'])
                try:
                    result=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=plan['learner_timeout_seconds'])
                    console=result.stdout+'\n'+result.stderr
                    (raw_logs/f'{gid}.txt').write_text(console,encoding='utf-8')
                    cleaned=console.replace(str(ROOT),'<repo>').replace(str(Path.home()),'<user>')
                    (folder/f'{alg}_console.txt').write_text(cleaned,encoding='utf-8')
                    if result.returncode:raise ValueError('WORKER_EXIT_'+str(result.returncode))
                    g=json.loads((folder/f'{alg}_graph.json').read_text(encoding='utf-8'))
                    g.update(graph_id=gid,source_type='discovery',**cell,algorithm=alg);save(folder/f'{alg}_graph.json',g);inventory.append(g)
                    edges={tuple(e) for e in g['confirmed_edges']};unresolved={frozenset(e) for e in g['unresolved_pairs']}
                    graph_memory[gid]=(edges,unresolved)
                    fit_model(train,names,edges,plan['scm']['alpha_grid'][0]);eligible[alg]=(g,edges,unresolved)
                    event('GRAPH_LEARNED',graph_id=gid,seconds=g['seconds'])
                except Exception as exc:
                    message=type(exc).__name__+': '+str(exc).replace(str(ROOT),'<repo>').replace(str(Path.home()),'<user>')
                    if isinstance(exc,subprocess.TimeoutExpired):
                        (raw_logs/f'{gid}_timeout.txt').write_text('TIMEOUT '+str(plan['learner_timeout_seconds'])+' seconds\n',encoding='utf-8')
                        message='LEARNER_TIMEOUT_'+str(plan['learner_timeout_seconds'])+'_SECONDS'
                    fail('LEARNING_OR_DAG_FIT',message,graph_id=gid)
                    if not any(g['graph_id']==gid for g in inventory):
                        g=dict(graph_id=gid,source_type='discovery',**cell,algorithm=alg,status='FAILED',error=message)
                        save(folder/f'{alg}_graph.json',g);inventory.append(g)
            scores=[]
            for alpha in plan['scm']['alpha_grid']:
                mse={alg:validation_mse(fit_model(train,names,e,alpha),valid,names) for alg,(g,e,u) in eligible.items()}
                if mse:scores.append(dict(alpha=alpha,per_graph_mse=mse,mean_mse=float(np.mean(list(mse.values())))))
            alpha=min(scores,key=lambda x:(x['mean_mse'],-x['alpha']))['alpha'] if scores else None
            save(folder/'alpha_selection.json',dict(selected_alpha=alpha,scores=scores,scope='all eligible algorithms, observational validation only'))
            for alg in ['pc','boss','directlingam']:
                gid=dataset+'__'+alg;ready=alg in eligible;base=None;extensions=[];models=[];block=None
                if ready:
                    g,edges,unresolved=eligible[alg];base=fit_model(train,names,edges,alpha)
                    try:
                        extensions=consistent_extensions(spec['nodes'],edges,unresolved,g['native'],plan['policy']['mec_max_unresolved'])
                        if len(extensions)>plan['policy']['mec_max_extensions']:raise ValueError('EXTENSION_COUNT_LIMIT_'+str(len(extensions)))
                        models=[fit_model(train,names,e,alpha) for e in extensions]
                    except Exception as exc:
                        block=str(exc);blocks.append(dict(graph_id=gid,reason=block));extensions=[];models=[]
                    save(folder/f'{alg}_models.json',dict(primary=base,extensions=[dict(edges=sorted(e),model=m) for e,m in zip(extensions,models)],auxiliary_block=block))
                for task in spec['tasks']:
                    for mode in plan['policy']['modes']:
                        row=dict(graph_id=gid,source_type='discovery',structure_id=sid,dataset_id=dataset,train_n=cell['train_n'],replicate=cell['replicate'],algorithm=alg,task_id=task['task_id'],task_kind=task['task_kind'],action=task['action'],target=task['target'],policy=mode)
                        if not ready:recommendations.append(dict(row,row_status='LEARNING_OR_FIT_FAILED'));continue
                        if mode!='confirmed_only' and block:recommendations.append(dict(row,row_status='POLICY_BLOCKED',reason=block));continue
                        rec=recommend_policy([base] if mode=='confirmed_only' else models,[edges] if mode=='confirmed_only' else extensions,task,dict(plan['policy'],**{k:task[k] for k in ['action_values','reference_action','cost_weight']}),mode)
                        recommendations.append(dict(row,row_status='FROZEN',recommendation=rec))
            if sid in plan['controlled_errors']['structures'] and alpha is not None:
                for variant,edges in controlled_graphs(spec,plan).items():
                    gid=dataset+'__controlled__'+variant;model=fit_model(train,names,edges,alpha);graph_memory[gid]=(edges,set())
                    save(folder/f'controlled_{variant}_model.json',dict(source_type='controlled_error',variant=variant,edges=sorted(edges),model=model))
                    for task in [t for t in spec['tasks'] if t['task_kind']!='negative_control']:
                        rec=recommend_policy([model],[edges],task,dict(plan['policy'],**{k:task[k] for k in ['action_values','reference_action','cost_weight']}),'confirmed_only')
                        controls.append(dict(graph_id=gid,source_type='controlled_error',variant=variant,structure_id=sid,dataset_id=dataset,train_n=cell['train_n'],replicate=cell['replicate'],algorithm='ARTIFICIAL_'+variant,task_id=task['task_id'],task_kind=task['task_kind'],action=task['action'],target=task['target'],policy='confirmed_only',row_status='FROZEN',recommendation=rec))
            event('DATASET_COMPLETED',dataset_id=dataset,eligible_algorithms=len(eligible),alpha=alpha)
    save(out/'graph_inventory.json',inventory);save(out/'policy_blocks.json',blocks)
    frozen=out/'recommendations_frozen.json';frozen_control=out/'controlled_recommendations_frozen.json'
    save(frozen,recommendations);save(frozen_control,controls);policy_sha=sha(frozen);control_sha=sha(frozen_control)
    event('ALL_RECOMMENDATIONS_FROZEN',graph_attempts=graph_attempts,discovery_rows=len(recommendations),controlled_rows=len(controls),sha256=policy_sha,controlled_sha256=control_sha)
    # Reference scoring and oracle means are never passed to the learner worker or policy.
    quality_map={}
    for row in recommendations+controls:
        if row['graph_id'] not in graph_memory:continue
        spec=specs[row['structure_id']];task=next(t for t in spec['tasks'] if t['task_id']==row['task_id'])
        e,u=graph_memory[row['graph_id']];quality_map[row['graph_id']+'__'+task['task_id']]=score_graph(e,u,spec,task)
    save(out/'structural_metrics.json',quality_map)
    evaluation={};raw=out/'do_evaluation';raw.mkdir()
    for spec in plan['structures']:
        sid=spec['structure_id'];actions=list(dict.fromkeys(t['action'] for t in spec['tasks']))
        for ai,action in enumerate(actions):
            task=next(t for t in spec['tasks'] if t['action']==action)
            for vi,value in enumerate(task['action_values']+[task['reference_action']]):
                tag=sid+'__'+action+'__'+('reference' if vi==5 else str(vi));data=[];noises=[];batch_records=[]
                for batch in range(plan['evaluation']['batches']):
                    seed=spec['evaluation_seed_base']+ai*1000+vi*10+batch
                    frame,noise,meta=draw_structure(module,spec,seed,plan['evaluation']['n_per_batch'],action,value)
                    u=pd.DataFrame(noise)
                    for x in [frame,u]:x.insert(0,'sample_id',range(len(x)));x.insert(0,'seed',seed);x.insert(0,'batch',batch)
                    data.append(frame);noises.append(u);batch_records.append(dict(batch=batch,seed=seed,metadata=meta))
                df=pd.concat(data,ignore_index=True);uf=pd.concat(noises,ignore_index=True)
                df.to_csv(raw/f'{tag}.csv',index=False);uf.to_csv(raw/f'{tag}_noise.csv',index=False)
                stats={node:describe_mean(df[node]) for node in spec['nodes']};oracle=analytic_response(spec,action,value)
                evaluation[tag]=dict(structure_id=sid,action=action,value=value,batches=batch_records,statistics=stats,post_freeze_analytic_mean=oracle)
            event('ACTION_HOLDOUT_GENERATED',structure_id=sid,action=action)
    if sha(frozen)!=policy_sha or sha(frozen_control)!=control_sha:raise ValueError('RECOMMENDATION_MUTATED_AFTER_HOLDOUT')
    save(out/'intervention_evaluation.json',evaluation)
    def evaluated(record):
        row={k:v for k,v in record.items() if k!='recommendation'}
        q=quality_map.get(record['graph_id']+'__'+record['task_id'],{})
        row.update(q)
        if record['row_status']!='FROZEN':return row
        spec=specs[row['structure_id']];task=next(t for t in spec['tasks'] if t['task_id']==row['task_id']);rec=record['recommendation'];selected=rec['selected']
        prefix=row['structure_id']+'__'+row['action']+'__';grid=task['action_values'];target=row['target']
        i=grid.index(selected['action']);actual=evaluation[prefix+str(i)]['statistics'][target];base=evaluation[prefix+'reference']['statistics'][target]
        losses=[(evaluation[prefix+str(j)]['statistics'][target]['mean']-task['target_value'])**2+task['cost_weight']*(value-task['reference_action'])**2 for j,value in enumerate(grid)]
        regret=losses[i]-min(losses);reference_loss=(base['mean']-task['target_value'])**2
        floor=.01*task['loss_scale']**2;gap=reference_loss-min(losses);effect=actual['mean']-base['mean'];se=math.hypot(actual['se'],base['se'])
        row.update(row_status='EVALUATED',recommendation_status=rec['status'],recommended_action=selected['action'],predicted_target=selected['predicted_y'],
            predicted_target_min=selected['predicted_y_min'],predicted_target_max=selected['predicted_y_max'],actual_target_mean=actual['mean'],actual_target_se=actual['se'],actual_target_ci_low=actual['ci_low'],actual_target_ci_high=actual['ci_high'],
            target_gap=actual['mean']-task['target_value'],action_cost=selected['cost'],target_mean_loss=losses[i],candidate_regret=regret,
            scale_normalized_regret=regret/task['loss_scale']**2,reference_mean_loss=reference_loss,
            relative_regret=regret/reference_loss if reference_loss>=floor else None,relative_regret_status='STABLE' if reference_loss>=floor else 'UNSTABLE_REFERENCE',
            fraction_reference_gap_lost=regret/gap if gap>=floor else None,reference_gap_status='STABLE' if gap>=floor else 'UNSTABLE_REFERENCE_GAP',
            predicted_effect=selected['predicted_effect'],actual_effect=effect,effect_se=se,effect_ci_low=effect-1.96*se,effect_ci_high=effect+1.96*se,
            effect_prediction_absolute_error=abs(selected['predicted_effect']-effect),mean_prediction_absolute_error=abs(selected['predicted_y']-actual['mean']),
            squared_individual_error_mean_computed=False,extension_count=rec['extension_count'])
        return row
    rows=[evaluated(r) for r in recommendations];control_rows=[evaluated(r) for r in controls]
    save(out/'comparison.json',rows);table(out/'comparison.csv',rows);save(out/'controlled_comparison.json',control_rows);table(out/'controlled_comparison.csv',control_rows)
    save(out/'failures.json',failures)
    event('COMPLETED',graph_attempts=graph_attempts,learned_graphs=sum(g['status']=='LEARNED' for g in inventory),discovery_rows=len(rows),evaluated_rows=sum(r['row_status']=='EVALUATED' for r in rows),controlled_rows=len(control_rows),policy_blocked_graphs=len(blocks),learning_failures=len(failures))
    save(out/'SHA256.json',{p.relative_to(out).as_posix():sha(p) for p in sorted(out.rglob('*')) if p.is_file() and p.name!='SHA256.json'})
    return 0 if graph_attempts==144 and not failures else 2

if __name__=='__main__':sys.exit(main())

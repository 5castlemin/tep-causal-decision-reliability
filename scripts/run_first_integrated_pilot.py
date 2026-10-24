"""Execute the preregistered small IID FCM pipeline, never the TEP artifacts."""
import argparse
import csv
import hashlib
import importlib.metadata
import inspect
import json
import platform
import subprocess
import sys
import time
import traceback
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from fcm_acceptance_adapter import load_pinned_module
from integrated_pilot import draw,learn_graph,fit_model,validation_mse,recommend,structure_metrics


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def save(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')


def mean_stats(values):
    import numpy as np
    v=np.asarray(values,dtype=float);m=float(v.mean());se=float(v.std(ddof=1)/np.sqrt(len(v)))
    return dict(n=len(v),mean=m,se=se,ci95_normal=[m-1.96*se,m+1.96*se])


def acceptance(module,family,plan,out):
    import numpy as np
    import pandas as pd
    records=[]
    for seed in plan['noise']['uniform_acceptance_seeds']:
        for action in [None,0.5]:
            f,u,meta=draw(module,seed,plan['noise']['acceptance_n'],family,plan,action)
            repeat,_,_=draw(module,seed,len(f),family,plan,action)
            plain,_,_=draw(module,seed,len(f),family,plan,action,hook=False)
            checks=dict(exact_repeat=f.equals(repeat),hook_transparent=f.equals(plain),
                equations=max(meta['errors'].values())<1e-10,
                graph=meta['original_edges']==sorted(plan['reference_edges']),
                index=list(f.index)==list(range(len(f))))
            # Source returns tuple pairs, JSON plan contains list pairs.
            checks['graph']={tuple(e) for e in meta['original_edges']}=={tuple(e) for e in plan['reference_edges']}
            if action is not None:
                g=meta['mutilated'];checks.update(action_constant=bool((f.A==action).all()),
                    replaced_equation=float(g['action_term'])==action,
                    removed_parents=g['action_parents']==[],other_equations=g['nonaction_terms_unchanged'],
                    removed_noise='u_A' not in u)
            if family=='uniform':
                checks['uniform_objects']=all(s.startswith('UniformDistribution(') for s in meta['distributions'].values())
                checks['uniform_ranges']=all(bool((np.abs(v)<=plan['noise']['uniform_half_width'][k]+1e-12).all()) for k,v in u.items())
            tag=f'{seed}_'+('obs' if action is None else 'do')
            f.to_csv(out/f'{tag}.csv',index=False)
            pd.DataFrame(u).to_csv(out/f'{tag}_noise.csv',index=False)
            records.append(dict(seed=seed,action=action,checks=checks,metadata=meta))
    result=dict(status='PASS' if all(all(r['checks'].values()) for r in records) else 'FAIL',records=records)
    save(out/'acceptance.json',result)
    return result


def main():
    p=argparse.ArgumentParser();p.add_argument('--module',required=True);p.add_argument('--output',required=True)
    args=p.parse_args();out=Path(args.output).resolve()
    if out.exists():raise ValueError('NEW_OUTPUT_DIRECTORY_REQUIRED')
    if sys.prefix==sys.base_prefix:raise ValueError('ISOLATED_VENV_REQUIRED')
    out.mkdir(parents=True)
    plan_path=ROOT/'research_runs/first_integrated_pilot/PLAN_v1.json'
    plan=json.loads(plan_path.read_text(encoding='utf-8'));save(out/'plan.json',plan)
    import numpy as np
    import pandas as pd
    module=load_pinned_module(args.module)
    import causallearn.search.PermutationBased.BOSS as boss_source
    import causallearn.search.ConstraintBased.PC as pc_source
    import lingam
    package_sources={name:sha(inspect.getfile(obj)) for name,obj in [('BOSS',boss_source),('PC',pc_source),('DirectLiNGAM',lingam.DirectLiNGAM)]}
    save(out/'environment.json',dict(python=platform.python_version(),platform=platform.platform(),
        versions={k:importlib.metadata.version(k) for k in ['numpy','pandas','scipy','sympy','networkx','causal-learn','lingam','scikit-learn','semopy']},
        source_commit=plan['source_commit'],upstream_module_sha256=sha(args.module),package_source_sha256=package_sources,
        plan_sha256=sha(plan_path),base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        command='python -X utf8 scripts/run_first_integrated_pilot.py --module <pinned models_fcm.py> --output research_runs/first_integrated_pilot/run_v1',
        code_sha256={str(f.relative_to(ROOT)).replace('\\','/'):sha(f) for f in [Path(__file__),ROOT/'src/integrated_pilot.py',ROOT/'src/decision_mvp.py',ROOT/'src/fcm_acceptance_adapter.py',ROOT/'src/pilot_fit.py']}))
    (out/'requirements.lock.txt').write_text(subprocess.check_output([sys.executable,'-m','pip','freeze','--all'],text=True),encoding='utf-8')
    ledger=[];failures=[];summary=[]
    def event(stage,**kw):
        ledger.append(dict(sequence=len(ledger),stage=stage,**kw));save(out/'execution_ledger.json',ledger)
        print(stage,kw,flush=True)
    event('PLAN_FROZEN',sha256=sha(plan_path))
    for family,cfg in plan['families'].items():
        folder=out/family;folder.mkdir();acc=folder/'acceptance';acc.mkdir()
        try:
            a=acceptance(module,family,plan,acc);event('ACCEPTANCE',family=family,status=a['status'])
            if a['status']!='PASS':raise ValueError('FCM_ACCEPTANCE_FAILED_NO_LEARNING_ALLOWED')
            frames={}
            for split in ['train','validation']:
                frame,noise,meta=draw(module,cfg[split+'_seed'],plan['data'][split+'_n'],family,plan)
                frame.to_csv(folder/f'{split}.csv',index=False);pd.DataFrame(noise).to_csv(folder/f'{split}_noise.csv',index=False)
                save(folder/f'{split}_generation.json',dict(seed=cfg[split+'_seed'],metadata=meta));frames[split]=frame
            event('OBSERVATIONS_CREATED',family=family)
            names=plan['algorithm_column_order'];train=frames['train'][names].to_numpy();valid=frames['validation'][names].to_numpy()
            standardized=(train-train.mean(axis=0))/train.std(axis=0,ddof=0)
            graphs={}
            for alg in ['pc','boss','directlingam']:
                started=time.monotonic()
                try:
                    edges,unres,native=learn_graph(standardized,names,alg,cfg['algorithm_seed'],family,plan)
                    # Eligibility is a graph-evaluation property, not truth-driven repair.
                    fit_model(train,names,edges,plan['scm']['alpha_grid'][0])
                    graphs[alg]=(edges,unres)
                    save(folder/f'{alg}_graph.json',dict(status='LEARNED',column_order=names,seed=cfg['algorithm_seed'],
                        confirmed_edges=sorted(edges),unresolved_pairs=sorted(sorted(e) for e in unres),native=native,
                        seconds=time.monotonic()-started,assumption_role=cfg['directlingam_role'] if alg=='directlingam' else 'PRIMARY_COMPARISON'))
                    event('GRAPH_LEARNED',family=family,algorithm=alg)
                except Exception as exc:
                    failure=dict(family=family,algorithm=alg,stage='LEARNING_OR_DAG_CHECK',error=type(exc).__name__+': '+str(exc))
                    failures.append(failure);save(folder/f'{alg}_failure.json',failure);event('ALGORITHM_FAILED',**failure)
            selection_algs=[a for a in graphs if family!='gaussian' or a!='directlingam']
            if not selection_algs:raise ValueError('NO_ELIGIBLE_MODEL_FOR_COMMON_ALPHA')
            scores=[]
            for alpha in plan['scm']['alpha_grid']:
                per={alg:validation_mse(fit_model(train,names,graphs[alg][0],alpha),valid,names) for alg in selection_algs}
                scores.append(dict(alpha=alpha,per_graph_standardized_mse=per,mean_mse=float(np.mean(list(per.values())))))
            alpha=min(scores,key=lambda r:(r['mean_mse'],-r['alpha']))['alpha']
            save(folder/'alpha_selection.json',dict(selected_alpha=alpha,criterion='OBSERVATIONAL_VALIDATION_NOT_CAUSAL_EFFECT',scores=scores))
            recommendations={}
            for alg,(edges,unres) in graphs.items():
                model=fit_model(train,names,edges,alpha);save(folder/f'{alg}_model.json',model)
                recommendations[alg]=recommend(model,edges,plan)
            frozen=folder/'recommendations_frozen.json';save(frozen,recommendations);frozen_sha=sha(frozen)
            event('RECOMMENDATIONS_FROZEN',family=family,sha256=frozen_sha)
            # Reference graph is first used to score the learned outputs after recommendation freeze.
            metrics={alg:structure_metrics(e,u,plan) for alg,(e,u) in graphs.items()};save(folder/'structural_metrics.json',metrics)
            evaluation={};base=910000 if family=='gaussian' else 920000
            for i,action in enumerate(plan['policy']['action_values']+[plan['policy']['reference_action']]):
                is_ref=i==len(plan['policy']['action_values']);tag='independent_reference' if is_ref else f'action_{i}'
                batches=[];batch_meta=[]
                for j in range(plan['evaluation']['independent_batches_per_action']):
                    seed=base+(1000 if is_ref else 100*i)+j
                    frame,noise,meta=draw(module,seed,plan['evaluation']['n_per_batch'],family,plan,action)
                    frame.to_csv(folder/f'{tag}_batch{j}.csv',index=False)
                    pd.DataFrame(noise).to_csv(folder/f'{tag}_batch{j}_noise.csv',index=False)
                    batches.extend(frame.Y.tolist());batch_meta.append(dict(seed=seed,metadata=meta,statistics=mean_stats(frame.Y)))
                evaluation[tag]=dict(action=action,statistics=mean_stats(batches),batches=batch_meta)
            if sha(frozen)!=frozen_sha:raise ValueError('RECOMMENDATIONS_CHANGED_AFTER_HOLDOUT')
            save(folder/'intervention_evaluation.json',evaluation);event('HOLDOUT_EVALUATED',family=family,recommendations_sha256=frozen_sha)
            ref=evaluation['independent_reference']['statistics'];p=plan['policy']
            losses={k:(v['statistics']['mean']-p['target_value'])**2+p['cost_weight']*(v['action']-p['reference_action'])**2 for k,v in evaluation.items() if k!='independent_reference'}
            for alg,rec in recommendations.items():
                selected=rec['selected'];i=p['action_values'].index(selected['action']);actual=evaluation[f'action_{i}']['statistics']
                effect=actual['mean']-ref['mean'];effect_se=float(np.hypot(actual['se'],ref['se']))
                pred_effect=selected['predicted_y']-rec['predicted_reference']
                summary.append(dict(family=family,algorithm=alg,assumption_role=cfg['directlingam_role'] if alg=='directlingam' else 'PRIMARY_COMPARISON',
                    recommendation_status=rec['status'],**metrics[alg],recommended_a=selected['action'],predicted_y=selected['predicted_y'],
                    actual_mean_y=actual['mean'],actual_mean_y_se=actual['se'],actual_mean_y_ci_low=actual['ci95_normal'][0],actual_mean_y_ci_high=actual['ci95_normal'][1],
                    absolute_mean_prediction_error=abs(selected['predicted_y']-actual['mean']),predicted_effect=pred_effect,
                    actual_effect=effect,effect_se=effect_se,effect_ci_low=effect-1.96*effect_se,effect_ci_high=effect+1.96*effect_se,
                    absolute_effect_prediction_error=abs(pred_effect-effect),target_gap=actual['mean']-p['target_value'],
                    action_cost=selected['cost'],actual_goal_loss=losses[f'action_{i}'],empirical_candidate_regret=losses[f'action_{i}']-min(losses.values())))
        except Exception as exc:
            failure=dict(family=family,stage='FAMILY',error=type(exc).__name__+': '+str(exc))
            failures.append(failure);save(folder/'failure.json',failure);event('FAMILY_FAILED',**failure)
    save(out/'summary.json',summary);save(out/'failures.json',failures)
    if summary:
        with (out/'summary.csv').open('w',newline='',encoding='utf-8-sig') as f:
            w=csv.DictWriter(f,fieldnames=list(summary[0]));w.writeheader();w.writerows(summary)
    event('COMPLETED',successful_model_rows=len(summary),failures=len(failures))
    save(out/'SHA256.json',{str(f.relative_to(out)).replace('\\','/'):sha(f) for f in sorted(out.rglob('*')) if f.is_file() and f.name!='SHA256.json'})
    return 0 if len(summary)==6 and not failures else 2


if __name__=='__main__':sys.exit(main())

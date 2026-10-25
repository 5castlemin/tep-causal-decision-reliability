"""Locked confirmation utilities. Never refit a predictor on confirmation outcomes."""
import math
import statistics
from collections import defaultdict

from diverse_metric_analysis import value,weighted_predict,collinearity
from repeated_metric_pilot import spearman,acyclic
from diverse_structure_pilot import reference_edges,all_paths

COVARIATES=['algorithm_boss','algorithm_directlingam','log_n','n_nodes','predicted_density','unresolved_ratio']
MODEL_FEATURES={'M0':COVARIATES,'M1':COVARIATES+['skeleton_f1'],
    'M2':COVARIATES+['key_path_edge_recall'],'M3':COVARIATES+['strict_directed_f1'],
    'M4_incremental':COVARIATES+['skeleton_f1','key_path_edge_recall']}


def freeze_models(exploratory_rows):
    rows=[r for r in exploratory_rows if r['source_type']=='discovery' and r['row_status']=='EVALUATED'
          and r['task_kind']!='negative_control' and r['policy']=='confirmed_only']
    assert {r['structure_id'] for r in rows}=={'S'+str(i) for i in range(1,9)}
    return {name:weighted_predict(rows,[],features,.01)[1] for name,features in MODEL_FEATURES.items()}


def predict_frozen(model,rows):
    result=[]
    for r in rows:
        z=[]
        for f,im,mu,sd in zip(model['features'],model['feature_imputations'],model['feature_means'],model['feature_scales']):
            v=value(r,f);z.append(((im if v is None else v)-mu)/sd)
        result.append(model['outcome_mean']+model['outcome_scale']*sum(a*b for a,b in zip(z,model['coefficients_standardized'])))
    return result


def clustered_comparison(rows,models,seed=925104,b=10000):
    import numpy as np
    predictions=[];scores=[]
    ids=sorted({r['structure_id'] for r in rows})
    for name,model in models.items():
        p=predict_frozen(model,rows)
        for r,y in zip(rows,p):
            predictions.append(dict(model=name,structure_id=r['structure_id'],graph_id=r['graph_id'],
                task_id=r['task_id'],predicted_loss=y,actual_loss=r['scale_normalized_regret'],
                absolute_error=abs(y-r['scale_normalized_regret'])))
        for sid in ids:
            items=[r for r in predictions if r['model']==name and r['structure_id']==sid]
            scores.append(dict(model=name,structure_id=sid,mae=statistics.mean(r['absolute_error'] for r in items),rows=len(items)))
    macro={m:statistics.mean(r['mae'] for r in scores if r['model']==m) for m in models}
    paired=[]
    rng=np.random.default_rng(seed)
    for left,right in [('M1','M2'),('M0','M1'),('M0','M2'),('M0','M3'),('M1','M4_incremental')]:
        values=[next(r['mae'] for r in scores if r['model']==left and r['structure_id']==s)-next(r['mae'] for r in scores if r['model']==right and r['structure_id']==s) for s in ids]
        boot=np.asarray(values)[rng.integers(0,len(ids),size=(b,len(ids)))].mean(axis=1)
        low,high=np.quantile(boot,[.025,.975]).tolist();delta=statistics.mean(values)
        deletion=[statistics.mean(values[:i]+values[i+1:]) for i in range(len(ids))]
        paired.append(dict(left=left,right=right,delta=delta,ci_low=low,ci_high=high,
            right_better=sum(v>1e-12 for v in values),left_better=sum(v< -1e-12 for v in values),ties=sum(abs(v)<=1e-12 for v in values),
            by_structure=dict(zip(ids,values)),leave_one_structure_out_min=min(deletion),leave_one_structure_out_max=max(deletion),
            bootstrap_units='whole generated reference structures, within selected generator; conditional on exploratory fitted models',bootstrap_repeats=b))
    main=paired[0]
    judgment=('INDEPENDENT_SUPPORT' if main['delta']>=.01 and main['ci_low']>0 else
        'COUNTER_EVIDENCE' if main['delta']<=-.01 and main['ci_high']<0 else 'INCONCLUSIVE')
    return dict(macro_mae=macro,structure_scores=scores,paired=paired,predictions=predictions,
        judgment=judgment,threshold=.01,threshold_is_design_choice=True,p_values_computed=False,
        uncertainty_caveat='12 rule-generated structures, family composition fixed; not manufacturing population; excludes uncertainty in the 8-structure training sample')


def descriptive_diagnostics(rows,fixed_effect_rows):
    metrics=['skeleton_f1','strict_directed_f1','key_path_edge_recall','unresolved_ratio']
    results=[]
    def summarize(items,scope,label,outcome):
        for m in metrics:
            valid=[r for r in items if r.get(m) is not None and r.get(outcome) is not None]
            x=[float(r[m]) for r in valid];y=[float(r[outcome]) for r in valid]
            status='DESCRIPTIVE_CONDITIONAL_NOT_CAUSAL' if len(set(x))>1 and len(set(y))>1 else 'NOT_COMPARABLE_CONSTANT_OR_EMPTY'
            results.append(dict(scope=scope,group=label,metric=m,outcome=outcome,rows=len(valid),
                structures=len({r['structure_id'] for r in valid}),metric_unique=len(set(x)),outcome_unique=len(set(y)),
                status=status,rho=spearman(x,y) if status.startswith('DESCRIPTIVE') else None))
    valid=[r for r in rows if r['row_status']=='EVALUATED' and r['task_kind']!='negative_control']
    for mode in ['confirmed_only','mec_minimax','abstain_on_disagreement']:
        selected=[r for r in valid if r['policy']==mode]
        summarize(selected,'policy',mode,'scale_normalized_regret')
        for status in sorted({r['recommendation_status'] for r in selected}):
            summarize([r for r in selected if r['recommendation_status']==status],'recommendation_reason',mode+'__'+status,'scale_normalized_regret')
    primary=[r for r in valid if r['policy']=='confirmed_only']
    for alg in ['pc','boss','directlingam']:
        summarize([r for r in primary if r['algorithm']==alg],'within_algorithm',alg,'scale_normalized_regret')
        for sid,tid in sorted({(r['structure_id'],r['task_id']) for r in primary}):
            summarize([r for r in primary if r['algorithm']==alg and r['structure_id']==sid and r['task_id']==tid],
                'within_algorithm_structure_task',sid+'__'+tid+'__'+alg,'scale_normalized_regret')
    for low,high in [(0.,.5),(.5,.999999999),(1.,1.)]:
        summarize([r for r in primary if low<=r['orientation_rate']<=high],
            'orientation_rate_stratum',str(low)+'..'+str(high),'scale_normalized_regret')
    summarize([r for r in primary if r['action_target_reachable']],'path_present','confirmed_path_only','scale_normalized_regret')
    for alg in ['all','pc','boss','directlingam']:
        fs=fixed_effect_rows if alg=='all' else [r for r in fixed_effect_rows if r['algorithm']==alg]
        summarize(fs,'fixed_action_effect',alg,'fixed_effect_absolute_error')
        summarize([r for r in fs if r['action_target_reachable']],'fixed_action_path_present',alg,'fixed_effect_absolute_error')
    pairs=[]
    groups=defaultdict(dict)
    for r in primary:groups[r['dataset_id'],r['task_id']][r['algorithm']]=r
    for (ds,task),g in groups.items():
        for a,b in [('pc','boss'),('pc','directlingam'),('boss','directlingam')]:
            if a in g and b in g:
                pairs.append(dict(dataset_id=ds,task_id=task,left=a,right=b,
                    loss_difference=g[a]['scale_normalized_regret']-g[b]['scale_normalized_regret'],
                    skeleton_difference=g[a]['skeleton_f1']-g[b]['skeleton_f1'],
                    path_difference=g[a]['key_path_edge_recall']-g[b]['key_path_edge_recall'],
                    interpretation='paired same-data descriptive algorithm contrast, not causal attribution'))
    return dict(associations=results,same_data_algorithm_pairs=pairs,metric_overlap=collinearity(primary,metrics))


def controlled_graphs(spec,plan):
    return {name:{tuple(e) for e in edges} for name,edges in spec['controlled_variants'].items()}


def select_controls(spec):
    """Fixed lexical rules: no learned graph or observed effect enters selection."""
    truth=reference_edges(spec);task=next(t for t in spec['tasks'] if t['task_id']=='path')
    a,y=task['action'],task['target'];paths=all_paths(truth,a,y)
    keys={e for p in paths for e in zip(p,p[1:])}
    def has_path(edges):return bool(all_paths(edges,a,y))
    # Peripheral means outside every action-to-target path, not no influence on Y.
    peripheral=sorted(truth-keys);key=sorted(keys)
    variants={'oracle_reference':truth};notes=[]
    for name,candidates,reverse in [('remove_key',key,False),('remove_peripheral',peripheral,False),
                                   ('reverse_key',key,True),('reverse_peripheral',peripheral,True)]:
        eligible=[(e,(truth-{e})|({e[::-1]} if reverse else set())) for e in candidates]
        eligible=[(e,g) for e,g in eligible if acyclic(spec['nodes'],g)]
        if eligible:
            e,g=eligible[0];variants[name]=g;notes.append(dict(variant=name,edge=e,path_preserved=has_path(g)))
        else:notes.append(dict(variant=name,status='NOT_APPLICABLE',reason='no eligible acyclic edge under fixed rule'))
    kept=[e for e in key if has_path(truth-{e})]
    if kept and peripheral:
        variants['remove_key_path_retained']=truth-{kept[0]}
        variants['remove_peripheral_path_retained']=truth-{peripheral[0]}
        notes.append(dict(variant='matched_removal_path_retained',key=kept[0],peripheral=peripheral[0],both_paths_preserved=True))
    else:notes.append(dict(variant='matched_removal_path_retained',status='NOT_APPLICABLE',reason='no redundant key path or peripheral edge'))
    extras=[(a,b) for a in sorted(spec['nodes']) for b in sorted(spec['nodes']) if a!=b and (a,b) not in truth and (b,a) not in truth and acyclic(spec['nodes'],truth|{(a,b)})]
    if extras:variants['add_edge']=truth|{extras[0]};notes.append(dict(variant='add_edge',edge=extras[0]))
    return {k:sorted(v) for k,v in variants.items()},notes

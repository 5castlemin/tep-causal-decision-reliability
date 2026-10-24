"""Predeclared descriptive and whole-reference-structure prediction checks."""
import math
import statistics
from collections import defaultdict

from repeated_metric_pilot import spearman


def primary_rows(rows):
    return [r for r in rows if r['source_type']=='discovery' and r['row_status']=='EVALUATED'
            and r['task_kind']!='negative_control' and r['policy']=='confirmed_only']


def correlations(rows,plan):
    spec=plan['analysis']['correlation'];result=[]
    for scope in ['structure_task','within_algorithm','within_sample_size']:
        groups=defaultdict(list)
        for r in primary_rows(rows):
            split=r['algorithm'] if scope=='within_algorithm' else str(r['train_n']) if scope=='within_sample_size' else 'all'
            groups[r['structure_id'],r['task_id'],split].append(r)
        for (sid,task,split),items in sorted(groups.items()):
            for metric in plan['analysis']['metric_candidates']:
                valid=[r for r in items if r.get(metric) is not None]
                datasets={r['dataset_id'] for r in valid};x=[float(r[metric]) for r in valid];y=[r['scale_normalized_regret'] for r in valid]
                reason=('INSUFFICIENT_DATASETS' if len(datasets)<spec['min_datasets'] else
                    'CONSTANT_METRIC' if len(set(x))<spec['min_unique'] else
                    'CONSTANT_OUTCOME' if len(set(y))<spec['min_unique'] else None)
                result.append(dict(scope=scope,structure_id=sid,task_id=task,split=split,metric=metric,
                    dataset_clusters=len(datasets),dependent_rows=len(valid),metric_unique=len(set(x)),outcome_unique=len(set(y)),
                    status=reason or 'DESCRIPTIVE_ONLY',rho=None if reason else spearman(x,y)))
    return result


def collinearity(rows,metrics):
    data=primary_rows(rows);result=[]
    for i,a in enumerate(metrics):
        for b in metrics[i+1:]:
            valid=[r for r in data if r.get(a) is not None and r.get(b) is not None]
            x=[float(r[a]) for r in valid];y=[float(r[b]) for r in valid]
            rho=spearman(x,y) if valid else None
            result.append(dict(metric_a=a,metric_b=b,dependent_rows=len(valid),reference_structures=len({r['structure_id'] for r in valid}),
                rho=rho,high_overlap=rho is not None and abs(rho)>=.95,scope='descriptive pairwise overlap, not independent effects'))
    return result


def value(row,feature):
    if feature=='algorithm_boss':return float(row['algorithm']=='boss')
    if feature=='algorithm_directlingam':return float(row['algorithm']=='directlingam')
    if feature=='log_n':return math.log2(row['train_n']/256)
    v=row.get(feature);return None if v is None else float(v)


def weighted_predict(train,test,features,alpha=.01):
    """All transformations are fitted solely on training structures.

    The structure weights sum equally for each of the seven training structures.
    The prediction experiment does not interpret Ridge coefficients causally.
    """
    import numpy as np
    counts={sid:sum(r['structure_id']==sid for r in train) for sid in {r['structure_id'] for r in train}}
    weights=np.asarray([1/counts[r['structure_id']] for r in train],dtype=float);weights/=weights.sum()
    y=np.asarray([r['scale_normalized_regret'] for r in train]);ym=float(weights@y)
    ys=float(np.sqrt(weights@((y-ym)**2)));ys=ys if ys>1e-12 else 1.
    means=[];scales=[];imputations=[];train_cols=[];test_cols=[]
    for feature in features:
        raw=[value(r,feature) for r in train];observed=[i for i,v in enumerate(raw) if v is not None]
        imputation=float(sum(weights[i]*raw[i] for i in observed)/sum(weights[i] for i in observed)) if observed else 0.
        col=np.asarray([imputation if v is None else v for v in raw]);mean=float(weights@col)
        scale=float(np.sqrt(weights@((col-mean)**2)));scale=scale if scale>1e-12 else 1.
        train_cols.append((col-mean)/scale)
        test_cols.append(np.asarray([(imputation if value(r,feature) is None else value(r,feature))-mean for r in test])/scale)
        means.append(mean);scales.append(scale);imputations.append(imputation)
    if features:
        x=np.column_stack(train_cols);xt=np.column_stack(test_cols)
        coefficient=np.linalg.solve(x.T@(weights[:,None]*x)+alpha*np.eye(len(features)),x.T@(weights*((y-ym)/ys)))
        predicted=ym+ys*(xt@coefficient)
        singular=np.linalg.svd(x*np.sqrt(weights)[:,None],compute_uv=False)
        tol=float(max(x.shape)*np.finfo(float).eps*singular[0]) if len(singular) else 0.
        rank=int(sum(singular>tol));full=rank==len(features)
        condition=float(singular[0]/singular[-1]) if full and singular[-1]>0 else None
    else:
        coefficient=np.array([]);predicted=np.full(len(test),ym);rank=0;condition=None;full=True
    artifact=dict(features=features,feature_means=means,feature_scales=scales,feature_imputations=imputations,
        outcome_mean=ym,outcome_scale=ys,coefficients_standardized=coefficient.tolist(),alpha=alpha,
        training_structures=sorted(counts),train_rows=len(train),structure_equal_weights=True,rank=rank,
        column_count=len(features),full_column_rank=full,condition_number=condition,
        rank_status='RANK_DEFICIENT_RIDGE_PREDICTION_ONLY' if not full else 'ILL_CONDITIONED' if condition and condition>1e6 else 'FULL_RANK',
        negative_predictions_clipped=False,coefficient_interpretation='prediction only; not independent causal explanations')
    return predicted.tolist(),artifact


def loso(rows,plan):
    data=primary_rows(rows);metrics=plan['analysis']['metric_candidates'];ids=[s['structure_id'] for s in plan['structures']]
    cov=['algorithm_boss','algorithm_directlingam','log_n','n_nodes','predicted_density','unresolved_ratio']
    models=[('training_mean',[]),('covariates_only',cov)]
    models += [('metric_only__'+m,[m]) for m in metrics]
    models += [('covariates_plus__'+m,cov+[m]) for m in metrics if m not in cov]
    models += [('joint_quality_ridge',cov+[m for m in metrics if m not in cov])]
    predictions=[];artifacts=[];scores=[]
    for held in ids:
        train=[r for r in data if r['structure_id']!=held];test=[r for r in data if r['structure_id']==held]
        if not train or not test:
            scores.append(dict(held_out_structure=held,model='ALL_MODELS',status='NO_EVALUABLE_TRAIN_OR_TEST'));continue
        assert set(r['structure_id'] for r in train).isdisjoint({held})
        for name,features in models:
            pred,artifact=weighted_predict(train,test,features,.01)
            artifacts.append(dict(model=name,held_out_structure=held,**artifact))
            errors=[]
            for row,prediction in zip(test,pred):
                actual=row['scale_normalized_regret'];errors.append(prediction-actual)
                predictions.append(dict(held_out_structure=held,model=name,structure_id=row['structure_id'],dataset_id=row['dataset_id'],
                    graph_id=row['graph_id'],task_id=row['task_id'],algorithm=row['algorithm'],train_n=row['train_n'],
                    predicted_loss=prediction,actual_loss=actual,absolute_error=abs(prediction-actual),squared_error=(prediction-actual)**2))
            scores.append(dict(held_out_structure=held,model=name,status='EXPLORATORY_HELDOUT_STRUCTURE',test_rows=len(test),
                test_datasets=len({r['dataset_id'] for r in test}),mae=statistics.mean(abs(e) for e in errors),rmse=math.sqrt(statistics.mean(e*e for e in errors))))
    macro=[]
    for name,features in models:
        s=[r for r in scores if r['model']==name and r.get('mae') is not None]
        macro.append(dict(model=name,heldout_structures=len(s),macro_mae=statistics.mean(r['mae'] for r in s) if s else None,
            macro_rmse=statistics.mean(r['rmse'] for r in s) if s else None,
            min_structure_mae=min(r['mae'] for r in s) if s else None,max_structure_mae=max(r['mae'] for r in s) if s else None,
            interpretation='eight fixed hand-designed structures; no pvalue, no definitive metric winner'))
    return dict(predictions=predictions,artifacts=artifacts,fold_scores=scores,macro_scores=macro,
        alias=dict(covariates_plus__unresolved_ratio='ALREADY_IN_COVARIATES'),
        test_outcomes_used_for_selection=False,negative_controls_excluded=True,controlled_error_graphs_excluded=True)

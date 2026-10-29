"""Development-only error -> response -> decision diagnostics; no discovery training."""
import math,statistics
from collections import defaultdict
from decision_mvp import static_mean_response,reachable
from diverse_structure_pilot import reference_edges,all_paths
from path_metric_incremental import linear_moments,loss_contract,fit_predict

BASE=['algorithm_boss','algorithm_directlingam','log_n','n_nodes']
SIMPLE=BASE+['target_goal','range_std','cost_range_squared']
MODELS={'BASE':BASE,'SIMPLE':SIMPLE,'SKELETON':SIMPLE+['skeleton_f1'],'DIRECTION':SIMPLE+['strict_directed_f1'],
 'PATH':SIMPLE+['key_path_edge_recall'],'SKEL_DIRECTION':SIMPLE+['skeleton_f1','strict_directed_f1'],
 'SKEL_PATH':SIMPLE+['skeleton_f1','key_path_edge_recall'],'DIRECTION_PATH':SIMPLE+['strict_directed_f1','key_path_edge_recall'],
 'ALL':SIMPLE+['skeleton_f1','strict_directed_f1','key_path_edge_recall']}
# Nine fixed candidates: 2 base forms + all seven nonempty subsets, as planned.

def evaluate(spec,task,chosen,predicted_reference,predicted_slope,scale=1.):
    truth=loss_contract(spec,task,chosen);ref=truth['oracle_reference_loss'];delta=truth['analytic_loss']-ref
    actual_slope=linear_moments(spec,task['action'],1)[0][task['target']]
    true_effect=actual_slope*(chosen-task['reference_action']);pred_effect=None if predicted_slope is None else predicted_slope*(chosen-task['reference_action'])
    sign_flip=None if predicted_slope is None or abs(actual_slope)<1e-8 or abs(predicted_slope)<1e-8 else actual_slope*predicted_slope<0
    return dict(**truth,improvement=ref-truth['analytic_loss'],raw_regret=truth['analytic_regret']*truth['normalizer'],
        worsened=delta>1e-10,large_deterioration=delta>scale**2,nonoptimal=truth['analytic_regret']>1e-10,
        loss_ratio=truth['analytic_loss']/ref if abs(ref)>1e-8 else None,ratio_status='DEFINED' if abs(ref)>1e-8 else 'BASELINE_NEAR_ZERO',
        true_slope=actual_slope,predicted_slope=predicted_slope,chosen_effect_error=None if pred_effect is None else abs(pred_effect-true_effect),
        fixed_effect_error=None if predicted_slope is None else abs(.5*(predicted_slope-actual_slope)),
        direction_flip=sign_flip,effect_missed=None if predicted_slope is None else abs(actual_slope)>1e-8 and abs(predicted_slope)<=1e-8,
        predicted_reference=predicted_reference,chosen_mean_prediction_error=None if predicted_reference is None else abs(predicted_reference+(chosen-task['reference_action'])*predicted_slope-truth['analytic_mean']))

def response(model,task):
    f=lambda v:static_mean_response(model,task['action'],v)[task['target']]
    return f(task['reference_action']),(f(.5)-f(0))/.5

def choose_response(task,intercept,slope,has_path=True):
    rows=[dict(action=v,predicted_mean=intercept+slope*(v-task['reference_action']),objective=(intercept+slope*(v-task['reference_action'])-task['target_value'])**2+task['cost_weight']*(v-task['reference_action'])**2) for v in task['action_values']]
    chosen=min(rows,key=lambda r:(r['objective'],abs(r['action']),r['action'])) if has_path else next(r for r in rows if r['action']==task['reference_action'])
    return chosen,rows

def error_location(spec,task,edges):
    truth=reference_edges(spec);removed=truth-edges;added=edges-truth
    keys={e for p in all_paths(truth,task['action'],task['target']) for e in zip(p,p[1:])}
    return dict(removed_edges=sorted(removed),added_edges=sorted(added),key_removed=sum(e in keys for e in removed),
        peripheral_removed=sum(e not in keys for e in removed),path_preserved=reachable(edges,task['action'],task['target']),
        key_definition='union of directed truth paths for THIS action/target, not historical variant name')

def match_pair(left,right):
    fields=['dataset_id','task_id','policy','skeleton_f1','strict_directed_f1','added_pairs','missing_pairs','reversed_edges','unresolved_count','edge_count','shd']
    return all(left[k]==right[k] if not isinstance(left[k],float) else math.isclose(left[k],right[k],abs_tol=1e-12,rel_tol=0) for k in fields)

def nested_cv(rows):
    ids=sorted({r['structure_id'] for r in rows});folds=[];scores=[]
    for held in ids:
        train=[r for r in rows if r['structure_id']!=held];test=[r for r in rows if r['structure_id']==held]
        inner={m:[] for m in MODELS}
        for validate in ids:
            if validate==held:continue
            inner_train=[r for r in train if r['structure_id']!=validate];inner_test=[r for r in train if r['structure_id']==validate]
            for m,features in MODELS.items():
                pred,_=fit_predict(inner_train,inner_test,features);inner[m].append(statistics.mean(abs(p-r['scale_normalized_regret']) for p,r in zip(pred,inner_test)))
        inner_mae={m:statistics.mean(v) for m,v in inner.items()};best=min(inner_mae.values())
        eligible=[m for m in MODELS if inner_mae[m]<=best+.01];selected=min(eligible,key=lambda m:(len(MODELS[m]),list(MODELS).index(m)))
        for m,features in MODELS.items():
            pred,artifact=fit_predict(train,test,features);mae=statistics.mean(abs(p-r['scale_normalized_regret']) for p,r in zip(pred,test))
            scores.append(dict(structure_id=held,model=m,mae=mae,selected_in_fold=m==selected))
        selected_mae=next(r['mae'] for r in scores if r['structure_id']==held and r['model']==selected)
        folds.append(dict(held_out=held,training_structures=[s for s in ids if s!=held],inner_mae=inner_mae,selected=selected,selected_test_mae=selected_mae))
    return dict(scope='development nested whole-structure CV; no independent cohort',features=MODELS,folds=folds,structure_scores=scores,
        macro_mae={m:statistics.mean(r['mae'] for r in scores if r['model']==m) for m in MODELS},nested_selected_macro_mae=statistics.mean(f['selected_test_mae'] for f in folds))

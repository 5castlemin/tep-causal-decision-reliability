"""Small synthetic repeated experiment; all GT use is outside learning/policy functions."""
import itertools
import math
import statistics

from fcm_acceptance_adapter import capture_noise
from integrated_pilot import build_family
from decision_mvp import reachable,static_mean_response,task_metrics


def draw_any(module,seed,n,family,plan,action=None,value=None,hook=True):
    import contextlib
    import numpy as np
    fcm,symbols=build_family(module,seed,family,plan)
    terms={str(node):str(fcm.graph.nodes[node]['term']) for node in fcm.nodes}
    gt=fcm.ground_truth
    original=sorted((str(a),str(b)) for a in gt.index for b in gt.columns if gt.loc[a,b]!=0)
    intervention=None
    if action is not None:
        fcm.intervene_on({symbols[action]:float(value)})
        g=fcm.mutilated_dags[fcm.interventions[0]]
        intervention=dict(action=action,value=value,term=str(g.nodes[symbols[action]]['term']),
            parents=[str(p) for p in g.predecessors(symbols[action])],
            edges=sorted((str(a),str(b)) for a,b in g.edges),
            other_equations_unchanged=all(str(g.nodes[symbols[v]]['term'])==terms[v] for v in plan['nodes'] if v!=action))
    with (capture_noise(module) if hook else contextlib.nullcontext({})) as noise:
        frame=(fcm.sample(size=n,additive_gaussian_noise=False,snr=None) if action is None else
               fcm.interventional_sample(size=n,which_intervention=0,additive_gaussian_noise=False,snr=None))
    frame=frame.loc[:,plan['nodes']].astype(float)
    if not np.isfinite(frame.to_numpy()).all():raise ValueError('NONFINITE_DATA')
    errors=None
    if hook:
        expected={}
        for name in ['R','A','M','Y']:
            if name==action:expected[name]=np.full(n,value)
            elif name=='R':expected[name]=noise['u_R']
            elif name=='A':expected[name]=2*frame.R.to_numpy()+noise['u_A']
            elif name=='M':expected[name]=3*frame.A.to_numpy()+noise['u_M']
            else:expected[name]=frame.M.to_numpy()+frame.R.to_numpy()+noise['u_Y']
        errors={name:float(np.max(np.abs(frame[name].to_numpy()-v))) for name,v in expected.items()}
    return frame,noise,dict(reference_returned_edges=original,intervention=intervention,reconstruction_errors=errors)


def acyclic(nodes,edges):
    pending=set(nodes);done=set()
    while pending:
        ready={n for n in pending if all(a in done for a,b in edges if b==n)}
        if not ready:return False
        done|=ready;pending-=ready
    return True


def colliders(edges,pairs):
    result=set()
    for middle in {n for e in edges for n in e}:
        parents=sorted(a for a,b in edges if b==middle)
        for a,b in itertools.combinations(parents,2):
            if frozenset((a,b)) not in pairs:result.add((a,middle,b))
    return result


def consistent_extensions(nodes,edges,unresolved,native,max_unresolved=6):
    """All consistent DAG extensions of a supported PDAG. Takes no truth input.

    Preserve the skeleton and every given direction, forbid cycles/new unshielded
    colliders. This implements the skeleton/v-structure equivalence criterion.
    Non-tail/arrow endpoints are not assumed to define an ordinary PDAG.
    """
    allowed={('TAIL','TAIL'),('TAIL','ARROW'),('ARROW','TAIL')}
    if any((e['endpoint1'],e['endpoint2']) not in allowed for e in native.get('native_edges',[])):
        raise ValueError('UNSUPPORTED_ENDPOINTS_FOR_PDAG_EXTENSION')
    if len(unresolved)>max_unresolved:raise ValueError('EXTENSION_ENUMERATION_LIMIT')
    pairs={frozenset(e) for e in edges}|set(unresolved)
    if len(pairs)!=len(edges)+len(unresolved):raise ValueError('CONFLICTING_DUPLICATE_PAIR')
    fixed_colliders=colliders(edges,pairs);unknown=sorted(tuple(sorted(e)) for e in unresolved)
    results=[]
    for bits in itertools.product([0,1],repeat=len(unknown)):
        candidate=set(edges)|{(b,a) if flip else (a,b) for (a,b),flip in zip(unknown,bits)}
        if acyclic(nodes,candidate) and colliders(candidate,pairs)==fixed_colliders:results.append(candidate)
    if not results:raise ValueError('NO_CONSISTENT_DAG_EXTENSION')
    return results


def recommend_policy(models,edge_sets,task,policy,mode):
    if not models:raise ValueError('NO_MODELS_FOR_POLICY')
    action,target=task['action'],task['target'];base=policy['reference_action']
    predictions=[[static_mean_response(model,action,v)[target] for v in policy['action_values']] for model in models]
    references=[static_mean_response(model,action,base)[target] for model in models]
    candidates=[];individual=[]
    for predictions_i in predictions:
        individual.append(min(range(len(policy['action_values'])),key=lambda i:((predictions_i[i]-task['target_value'])**2+policy['cost_weight']*(policy['action_values'][i]-base)**2,abs(policy['action_values'][i]),policy['action_values'][i])))
    for i,value in enumerate(policy['action_values']):
        ys=[pred[i] for pred in predictions];cost=policy['cost_weight']*(value-base)**2
        effects=[y-r for y,r in zip(ys,references)]
        candidates.append(dict(action=value,predicted_y=statistics.mean(ys),predicted_y_min=min(ys),predicted_y_max=max(ys),
            predicted_effect=statistics.mean(effects),predicted_effect_min=min(effects),predicted_effect_max=max(effects),
            objective=max((y-task['target_value'])**2+cost for y in ys),cost=cost,per_extension_y=ys))
    any_path=any(reachable(edges,action,target) for edges in edge_sets)
    if not any_path:
        selected=next(c for c in candidates if c['action']==base);status='NO_PATH_BASELINE_FALLBACK'
    elif mode=='abstain_on_disagreement' and len(set(individual))>1:
        selected=next(c for c in candidates if c['action']==base);status='AMBIGUITY_ABSTENTION'
    else:
        selected=min(candidates,key=lambda c:(c['objective'],abs(c['action']),c['action']))
        status='COMPUTED_BASELINE' if selected['action']==base else 'COMPUTED_RECOMMENDATION'
    return dict(mode=mode,status=status,selected=selected,candidates=candidates,extension_count=len(models),
        individual_optimal_actions=[policy['action_values'][i] for i in individual],
        possible_path=any_path,all_extensions_have_path=all(reachable(e,action,target) for e in edge_sets),
        prediction_interval_is='range across fitted candidate DAGs, NOT a calibrated confidence interval')


def quality(edges,unresolved,reference,task):
    truth={tuple(e) for e in reference};pairs={frozenset(e) for e in edges}|unresolved;tp={frozenset(e) for e in truth}
    correct=len(edges&truth);denom=len(pairs)+len(truth)
    result=dict(skeleton_f1=2*len(pairs&tp)/denom if denom else 0,
        strict_directed_f1=2*correct/denom if denom else 0,
        confirmed_directed_f1=2*correct/(len(edges)+len(truth)),
        added_pairs=len(pairs-tp),missing_pairs=len(tp-pairs),reversed_edges=sum((b,a) in edges for a,b in truth),
        unresolved_count=len(unresolved),unresolved_ratio=len(unresolved)/len(pairs) if pairs else 0,
        orientation_rate=len(edges)/len(pairs) if pairs else 0,edge_count=len(pairs),confirmed_edges=len(edges))
    result['shd']=result['added_pairs']+result['missing_pairs']+result['reversed_edges']+len(unresolved&tp)
    t=task_metrics(dict(task_id=task['task_id'],action=task['action'],target=task['target'],gt_path=task['key_paths']),edges,truth,unresolved)
    result.update(key_path_edge_recall=t['gt_path_edge_recall'],complete_key_path_fraction=t['complete_gt_path_fraction'],
        all_key_paths_complete=t['complete_gt_path_fraction']==1,action_target_reachable=t['confirmed_action_target_reachable'],
        direct_xy_truth=t['direct_xy_truth'],direct_xy_confirmed=t['direct_xy_confirmed'],direct_xy_state=t['direct_xy_state'],direct_xy_correct=t['direct_xy_correct'])
    return result


def describe_mean(values):
    values=list(map(float,values));m=statistics.mean(values);se=statistics.stdev(values)/math.sqrt(len(values))
    return dict(n=len(values),mean=m,se=se,ci_low=m-1.96*se,ci_high=m+1.96*se)


def analytic_mean(action,target,value):
    """Post-policy-freeze implementation check only; never imported by recommendation."""
    derivatives={'A':{'R':0,'A':1,'M':3,'Y':3},'R':{'R':1,'A':2,'M':6,'Y':7},'M':{'R':0,'A':0,'M':1,'Y':1}}
    return derivatives[action][target]*value


def ranks(values):
    order=sorted(range(len(values)),key=lambda i:values[i]);result=[0.0]*len(values);i=0
    while i<len(order):
        j=i+1
        while j<len(order) and values[order[j]]==values[order[i]]:j+=1
        for k in range(i,j):result[order[k]]=(i+1+j)/2
        i=j
    return result


def spearman(x,y):
    if len(set(x))<2 or len(set(y))<2:return None
    return statistics.correlation(ranks(x),ranks(y))


def exploratory_associations(rows,plan):
    """Descriptive only, preserving dataset clusters in all deletion sensitivities."""
    spec=plan['analysis']['descriptive_spearman'];metrics=['skeleton_f1','strict_directed_f1','confirmed_directed_f1',
        'key_path_edge_recall','complete_key_path_fraction','action_target_reachable','direct_xy_correct',
        'shd','edge_count','unresolved_ratio','orientation_rate']
    groups={}
    # Separate algorithm/size sensitivities are declared before observing outcomes.
    for scope in ['all_algorithms','exclude_gaussian_mismatch','within_algorithm','within_sample_size']:
        for row in rows:
            if row['row_status']!='EVALUATED':continue
            if scope=='exclude_gaussian_mismatch' and row['family']=='gaussian' and row['algorithm']=='directlingam':continue
            split=(row['algorithm'] if scope=='within_algorithm' else str(row['train_n']) if scope=='within_sample_size' else 'pooled')
            key=(scope,row['family'],row['task_id'],row['policy'],split);groups.setdefault(key,[]).append(row)
    results=[]
    for key,group in groups.items():
        for metric in metrics:
            valid=[r for r in group if r[metric] is not None];clusters=sorted({r['dataset_id'] for r in valid})
            x=[float(r[metric]) for r in valid];y=[r['relative_regret'] for r in valid]
            reason=('INSUFFICIENT_DATASET_CLUSTERS' if len(clusters)<spec['min_datasets'] else
                    'INSUFFICIENT_METRIC_VARIATION' if len(set(x))<spec['min_metric_unique'] else
                    'INSUFFICIENT_OUTCOME_VARIATION' if len(set(y))<spec['min_outcome_unique'] else None)
            rho=None if reason else spearman(x,y);deletions=[]
            if rho is not None:
                for cluster in clusters:
                    remaining=[r for r in valid if r['dataset_id']!=cluster]
                    value=spearman([float(r[metric]) for r in remaining],[r['relative_regret'] for r in remaining])
                    if value is not None:deletions.append(value)
            results.append(dict(scope=key[0],family=key[1],task_id=key[2],policy=key[3],split=key[4],metric=metric,
                dataset_clusters=len(clusters),dependent_rows=len(valid),unique_metric_values=len(set(x)),
                status=reason or 'DESCRIPTIVE_ONLY',rho=rho,leave_dataset_out_min=min(deletions) if deletions else None,
                leave_dataset_out_max=max(deletions) if deletions else None,
                interpretation='LODO sensitivity range is not CI; no p-value; algorithm/task/representation confounding remains'))
    return results

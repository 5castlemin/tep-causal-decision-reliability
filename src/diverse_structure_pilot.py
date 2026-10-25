"""Generic declared linear FCM adapter; prediction never reads generating edges."""
import contextlib
import itertools
import math

from fcm_acceptance_adapter import capture_noise
from repeated_metric_pilot import acyclic,quality as previous_quality
from decision_mvp import reachable


def reference_edges(spec):return {(e['source'],e['target']) for e in spec['edges']}


def build_structure(module,spec,seed):
    from sympy import Eq,symbols
    from sympy.stats import Uniform
    if not acyclic(spec['nodes'],reference_edges(spec)):raise ValueError('DECLARED_STRUCTURE_NOT_DAG')
    variables={n:symbols(n) for n in spec['nodes']};equations=[]
    for node in spec['nodes']:
        half=math.sqrt(3)*spec['noise_sd'][node]
        term=Uniform('u_'+node,-half,half)
        for e in spec['edges']:
            if e['target']==node:term+=e['coefficient']*variables[e['source']]
        equations.append(Eq(variables[node],term))
    fcm=module.FCM(name='DIVERSE-'+spec['structure_id'],seed=seed);fcm.input_fcm(equations)
    return fcm,variables


def draw_structure(module,spec,seed,n,action=None,value=None,hook=True):
    import numpy as np
    fcm,symbols=build_structure(module,spec,seed)
    terms={str(node):str(fcm.graph.nodes[node]['term']) for node in fcm.nodes}
    gt=fcm.ground_truth
    returned=sorted((str(a),str(b)) for a in gt.index for b in gt.columns if gt.loc[a,b]!=0)
    intervention=None
    if action is not None:
        fcm.intervene_on({symbols[action]:float(value)})
        graph=fcm.mutilated_dags[fcm.interventions[0]]
        intervention=dict(action=action,value=value,term=str(graph.nodes[symbols[action]]['term']),
            parents=[str(p) for p in graph.predecessors(symbols[action])],edges=sorted((str(a),str(b)) for a,b in graph.edges),
            other_equations_unchanged=all(str(graph.nodes[symbols[v]]['term'])==terms[v] for v in spec['nodes'] if v!=action))
    with (capture_noise(module) if hook else contextlib.nullcontext({})) as noise:
        frame=(fcm.sample(size=n,additive_gaussian_noise=False,snr=None) if action is None else
               fcm.interventional_sample(size=n,which_intervention=0,additive_gaussian_noise=False,snr=None))
    frame=frame.loc[:,spec['nodes']].astype(float)
    if not np.isfinite(frame.to_numpy()).all():raise ValueError('NONFINITE_GENERATED_DATA')
    errors=None
    if hook:
        errors={}
        for node in spec['nodes']:
            expected=(np.full(n,value) if node==action else noise['u_'+node]+sum(
                (e['coefficient']*frame[e['source']].to_numpy() for e in spec['edges'] if e['target']==node),np.zeros(n)))
            errors[node]=float(np.max(np.abs(frame[node].to_numpy()-expected)))
    return frame,noise,dict(returned_edges=returned,equation_terms=terms,intervention=intervention,reconstruction_errors=errors)


def all_paths(edges,source,target):
    result=[]
    def visit(node,path):
        if node==target:result.append(path);return
        for a,b in sorted(edges):
            if a==node and b not in path:visit(b,path+[b])
    visit(source,[source]);return result


def score_graph(edges,unresolved,spec,task):
    truth=reference_edges(spec);paths=all_paths(truth,task['action'],task['target'])
    # Reuse the previous strict definitions for positive paths.
    if paths:
        result=previous_quality(edges,unresolved,truth,dict(task,key_paths=paths))
    else:
        pairs={frozenset(e) for e in edges}|unresolved;true_pairs={frozenset(e) for e in truth}
        correct=len(edges&truth);denom=len(pairs)+len(truth)
        result=dict(skeleton_f1=2*len(pairs&true_pairs)/denom,strict_directed_f1=2*correct/denom,
            confirmed_directed_f1=2*correct/(len(edges)+len(truth)),added_pairs=len(pairs-true_pairs),
            missing_pairs=len(true_pairs-pairs),reversed_edges=sum(e[::-1] in edges for e in truth),
            unresolved_count=len(unresolved),unresolved_ratio=len(unresolved)/len(pairs) if pairs else 0,
            orientation_rate=len(edges)/len(pairs) if pairs else 0,edge_count=len(pairs),confirmed_edges=len(edges))
        result['shd']=result['added_pairs']+result['missing_pairs']+result['reversed_edges']+len(unresolved&true_pairs)
        pair=(task['action'],task['target']);unknown=frozenset(pair) in unresolved
        result.update(key_path_edge_recall=None,complete_key_path_fraction=None,all_key_paths_complete=None,
            action_target_reachable=reachable(edges,*pair),direct_xy_truth=pair in truth,direct_xy_confirmed=pair in edges,
            direct_xy_state='UNRESOLVED' if unknown else 'CONFIRMED' if pair in edges else 'ABSENT',
            direct_xy_correct=None if unknown else ((pair in edges)==(pair in truth)))
    n=len(spec['nodes']);pairs=n*(n-1)/2
    result.update(confirmed_direction_precision=len(edges&truth)/len(edges) if edges else None,
        normalized_shd=result['shd']/len(truth),pair_normalized_shd=result['shd']/pairs,
        predicted_density=result['edge_count']/pairs,reference_edge_count=len(truth),n_nodes=n,
        reference_density=len(truth)/pairs,reference_path_count=len(paths),
        shortest_reference_path_edges=min(len(p)-1 for p in paths) if paths else None,
        longest_reference_path_edges=max(len(p)-1 for p in paths) if paths else None)
    return result


def analytic_response(spec,action,value):
    """Post-freeze equation check only. No regression or policy uses this function."""
    pending=set(spec['nodes']);values={}
    while pending:
        ready=[n for n in sorted(pending) if n==action or all(e['source'] in values for e in spec['edges'] if e['target']==n)]
        if not ready:raise ValueError('CYCLIC_DECLARED_EQUATIONS')
        for node in ready:
            values[node]=value if node==action else sum(e['coefficient']*values[e['source']] for e in spec['edges'] if e['target']==node)
            pending.remove(node)
    return values


def controlled_graphs(spec,plan):
    """Explicitly artificial oracle perturbations; never used as learned graphs."""
    truth=reference_edges(spec);cfg=plan['controlled_errors'];key=tuple(cfg['key_edges'][spec['structure_id']])
    peripheral=tuple(cfg['peripheral_edge']);extra=tuple(cfg['added_edge'])
    variants=dict(oracle_reference=truth,remove_key=truth-{key},remove_peripheral=truth-{peripheral},
        reverse_key=(truth-{key})|{key[::-1]},add_peripheral_to_target=truth|{extra})
    if key not in truth or peripheral not in truth or extra in truth:raise ValueError('CONTROLLED_PERTURBATION_CONTRACT_MISMATCH')
    if not all(acyclic(spec['nodes'],e) for e in variants.values()):raise ValueError('CONTROLLED_VARIANT_NOT_DAG')
    return variants

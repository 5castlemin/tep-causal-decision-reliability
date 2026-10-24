"""Shared machinery for a new synthetic pilot; never reads frozen TEP graphs."""
import random

from fcm_acceptance_adapter import build_fixture,capture_noise,reconstruction
from decision_mvp import static_mean_response,order_equations,reachable
from pilot_fit import fit_ridge


def build_family(module,seed,family,plan):
    if family=='gaussian':return build_fixture(module,seed)
    if family!='uniform':raise ValueError('UNKNOWN_NOISE_FAMILY')
    from sympy import Eq,symbols
    from sympy.stats import Uniform
    R,A,M,Y=symbols('R A M Y');width=plan['noise']['uniform_half_width']
    def u(name):return Uniform(name,-width[name],width[name])
    fcm=module.FCM(name='FIRST-INTEGRATED-UNIFORM-v1',seed=seed)
    fcm.input_fcm([Eq(R,u('u_R')),Eq(A,2*R+u('u_A')),Eq(M,3*A+u('u_M')),Eq(Y,M+R+u('u_Y'))])
    return fcm,dict(R=R,A=A,M=M,Y=Y)


def draw(module,seed,n,family,plan,action=None,hook=True):
    import contextlib
    import numpy as np
    fcm,sym=build_family(module,seed,family,plan)
    distributions={}
    for node in fcm.nodes:
        for u in fcm.graph.nodes[node]['term'].atoms(__import__('sympy.stats.rv',fromlist=['RandomSymbol']).RandomSymbol):
            distributions[str(u)]=str(u.pspace.distribution)
    original_edges=sorted((str(a),str(b)) for a,b in fcm.edges)
    original_terms={str(n):str(fcm.graph.nodes[n]['term']) for n in fcm.nodes}
    mutilated=None
    if action is not None:
        fcm.intervene_on({sym['A']:float(action)})
        graph=fcm.mutilated_dags[fcm.interventions[0]]
        mutilated=dict(action_term=str(graph.nodes[sym['A']]['term']),
            action_parents=[str(n) for n in graph.predecessors(sym['A'])],
            edges=sorted((str(a),str(b)) for a,b in graph.edges),
            nonaction_terms_unchanged=all(str(graph.nodes[sym[n]]['term'])==original_terms[n] for n in ['R','M','Y']))
    with (capture_noise(module) if hook else contextlib.nullcontext({})) as noise:
        frame=(fcm.sample(size=n,additive_gaussian_noise=False,snr=None) if action is None else
               fcm.interventional_sample(size=n,which_intervention=0,additive_gaussian_noise=False,snr=None))
    frame=frame.loc[:,plan['nodes']].astype(float)
    if not np.isfinite(frame.to_numpy()).all():raise ValueError('NONFINITE_GENERATED_DATA')
    errors=reconstruction(frame,noise,action) if hook else None
    return frame,noise,dict(distributions=distributions,errors=errors,original_edges=original_edges,mutilated=mutilated)


def learn_graph(data,names,algorithm,seed,family,plan):
    import numpy as np
    np.random.seed(seed);random.seed(seed)
    if algorithm=='directlingam':
        from lingam import DirectLiNGAM
        model=DirectLiNGAM(random_state=seed,measure='pwling',prior_knowledge=None)
        model.fit(data)
        coefficients=model.adjacency_matrix_
        cutoff=plan['algorithms']['directlingam']['edge_abs_threshold']
        edges={(names[j],names[i]) for i in range(len(names)) for j in range(len(names))
               if i!=j and abs(coefficients[i,j])>=cutoff}
        return edges,set(),dict(adjacency_child_parent=coefficients.tolist(),causal_order=[names[i] for i in model.causal_order_])
    if algorithm=='pc':
        from causallearn.search.ConstraintBased.PC import pc
        cfg=plan['algorithms']['pc'];test=plan['families'][family]['pc_test']
        graph=pc(data,alpha=cfg['alpha'],indep_test=test,stable=True,uc_rule=cfg['uc_rule'],
            uc_priority=cfg['uc_priority'],background_knowledge=None,verbose=False,show_progress=False,
            node_names=names,**({'approx':True} if test=='kci' else {})).G
    elif algorithm=='boss':
        from causallearn.search.PermutationBased.BOSS import boss
        graph=boss(data,score_func='local_score_BIC',parameters={'lambda_value':2.0},verbose=False,node_names=names)
    else:raise ValueError('UNKNOWN_ALGORITHM')
    edges=set();unresolved=set();native=[]
    aliases={f'X{i+1}':name for i,name in enumerate(names)};aliases.update({n:n for n in names})
    for edge in graph.get_graph_edges():
        a=aliases[edge.get_node1().get_name()];b=aliases[edge.get_node2().get_name()]
        e1=str(edge.get_endpoint1());e2=str(edge.get_endpoint2())
        native.append(dict(node1=a,node2=b,endpoint1=e1,endpoint2=e2))
        if (e1,e2)==('TAIL','ARROW'):edges.add((a,b))
        elif (e1,e2)==('ARROW','TAIL'):edges.add((b,a))
        else:unresolved.add(frozenset((a,b)))
    return edges,unresolved,dict(native_edges=native,native_matrix=graph.graph.tolist())


def fit_model(train,names,edges,alpha):
    import numpy as np
    mean=train.mean(axis=0);std=train.std(axis=0,ddof=0)
    if (std<=0).any():raise ValueError('SINGULAR_SCALING')
    z=(train-mean)/std;index={n:i for i,n in enumerate(names)};equations=[]
    for target in names:
        parents=sorted(a for a,b in edges if b==target)
        features=z[:,[index[p] for p in parents]]
        beta,intercept=fit_ridge(features,z[:,index[target]],alpha)
        equations.append(dict(target=target,intercept_standardized=intercept,
            parents=[dict(source=p,lag=0,coefficient_standardized=float(v)) for p,v in zip(parents,beta)]))
    model=dict(scaler_mean=dict(zip(names,mean.tolist())),scaler_std=dict(zip(names,std.tolist())),
               equations=equations,alpha=alpha,status='NEW_SYNTHETIC_MODEL_NOT_TEP_FIT')
    order_equations(model)
    return model


def validation_mse(model,validation,names):
    import numpy as np
    z=(validation-np.array([model['scaler_mean'][n] for n in names]))/np.array([model['scaler_std'][n] for n in names])
    index={n:i for i,n in enumerate(names)};loss=[]
    for eq in model['equations']:
        pred=np.full(len(z),eq['intercept_standardized'])
        for p in eq['parents']:pred+=p['coefficient_standardized']*z[:,index[p['source']]]
        loss.append(float(np.mean((z[:,index[eq['target']]]-pred)**2)))
    return float(np.mean(loss))


def recommend(model,edges,plan):
    p=plan['policy'];rows=[]
    for value in p['action_values']:
        pred=static_mean_response(model,p['action'],value)[p['target']]
        cost=p['cost_weight']*(value-p['reference_action'])**2
        rows.append(dict(action=value,predicted_y=pred,cost=cost,objective=(pred-p['target_value'])**2+cost))
    has_path=reachable(edges,p['action'],p['target'])
    selected=(min(rows,key=lambda r:(r['objective'],abs(r['action']),r['action'])) if has_path else
              next(r for r in rows if r['action']==p['reference_action']))
    return dict(status='RECOMMENDED' if has_path else 'NO_CONFIRMED_PATH_BASELINE_FALLBACK',
        selected=selected,candidates=rows,predicted_reference=next(r['predicted_y'] for r in rows if r['action']==p['reference_action']),
        interpretation='동일한 새 예제 FCM에서 평가하는 모델. 기존 TEP에 전용하지 않음')


def structure_metrics(edges,unresolved,plan):
    truth={tuple(e) for e in plan['reference_edges']};true_pairs={frozenset(e) for e in truth}
    pairs={frozenset(e) for e in edges}|unresolved
    correct=len(edges&truth);denom=len(pairs)+len(truth)
    path=[tuple(e) for e in zip(plan['metrics']['key_path'],plan['metrics']['key_path'][1:])]
    xy=tuple(plan['metrics']['direct_xy']);unknown=frozenset(xy) in unresolved
    miss=len(true_pairs-pairs);extra=len(pairs-true_pairs);rev=sum((b,a) in edges for a,b in truth)
    unres_gt=len(unresolved&true_pairs)
    return dict(skeleton_f1=2*len(pairs&true_pairs)/denom if denom else 0,
        strict_directed_f1=2*correct/denom if denom else 0,
        key_path_edge_recall=sum(e in edges for e in path)/len(path),
        complete_key_path=all(e in edges for e in path),action_target_reachable=reachable(edges,'A','Y'),
        direct_xy_truth=xy in truth,direct_xy_prediction=None if unknown else xy in edges,
        direct_xy_correct=None if unknown else ((xy in edges)==(xy in truth)),
        added_pairs=extra,missing_pairs=miss,reversed_edges=rev,unresolved_gt_pairs=unres_gt,
        shd=miss+extra+rev+unres_gt,predicted_pairs=len(pairs),confirmed_edges=len(edges),unresolved_pairs=len(unresolved))

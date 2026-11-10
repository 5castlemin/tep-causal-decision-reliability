"""Development-only bridge: recommendation is frozen before truth evaluation."""
import math
import numpy as np
from .graph_adapter import run_graph_stage

K = (-1.0, -0.5, 0.0, 0.5, 1.0)

def prepare(request, data, columns, schema, delta, fit_model, response):
    """Graph-only oracle -> learner (data and final DAG only) -> recommendation."""
    if type(columns) is not list or columns != schema or len(set(columns)) != len(columns):
        raise ValueError('schema order mismatch or duplicate')
    data = np.asarray(data, dtype=float)
    if data.ndim != 2 or data.shape[1] != len(schema) or data.shape[0] < 2 or not np.isfinite(data).all():
        raise ValueError('invalid training data')
    if set(request['node_ids']) != set(schema) or request['action'] not in schema or request['target'] not in schema or delta not in (-1, 1):
        raise ValueError('invalid task or schema')
    x, y = (schema.index(request[k]) for k in ('action','target'))
    mean = data.mean(axis=0); sd = data.std(axis=0, ddof=1)
    if not np.isfinite(sd).all() or (sd <= 0).any(): raise ValueError('invalid scale')
    target = float(mean[y] + delta*sd[y])
    graph = run_graph_stage(request)
    edges = {tuple(e) for e in graph['final_graph']}
    # Do not pass oracle hashes, candidate histories, truth or evaluator to learner.
    model = fit_model(data, list(schema), edges, 1.0)
    candidates = []
    for k in K:
        a = float(mean[x] + k*sd[x])
        pred = float(response(model, request['action'], a)[request['target']])
        loss = ((pred-target)/float(sd[y]))**2
        if not math.isfinite(loss): raise ValueError('nonfinite prediction')
        candidates.append(dict(k=k, action=a, predicted_y=pred, predicted_loss=loss))
    chosen = min(candidates, key=lambda r:(r['predicted_loss'], abs(r['k']), r['k']))
    return graph, dict(action=request['action'], target_node=request['target'], target=target,
                       sd_y=float(sd[y]), candidates=candidates, selected_k=chosen['k'])

def evaluate(selection, truth_spec, analytic_response):
    """Truth is accessed only after the recommendation has been frozen."""
    rows=[]
    for row in selection['candidates']:
        mu=float(analytic_response(truth_spec, selection['action'], row['action'])[selection['target_node']])
        loss=((mu-selection['target'])/selection['sd_y'])**2
        if not math.isfinite(loss): raise ValueError('nonfinite truth')
        rows.append(dict(k=row['k'], mean=mu, loss=loss))
    chosen=next(r for r in rows if r['k']==selection['selected_k'])
    optimum=min(rows,key=lambda r:(r['loss'],abs(r['k']),r['k']))
    return dict(truth=rows, optimum_k=optimum['k'], regret=chosen['loss']-optimum['loss'])

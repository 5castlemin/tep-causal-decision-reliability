"""Common static surrogate recommendation; environment gates precede research use."""
import math


def require_research_environment(structure_id, outcome_id, approvals):
    required={'model_controller_identity','variable_intervention_alignment',
              'reference_structure_valid','independent_evaluation_contract'}
    if structure_id != outcome_id or not all(approvals.get(k) is True for k in required):
        raise ValueError('GATE1_BLOCKED: 구조 참조와 실제 평가환경의 대응·승인 미충족')


def order_equations(artifact):
    equations={x['target']:x for x in artifact['equations']}
    if len(equations) != len(artifact['equations']):raise ValueError('중복 equation')
    pending=set(equations);order=[]
    while pending:
        ready=[]
        for name in sorted(pending):
            parents=equations[name]['parents']
            if any(p['lag'] != 0 for p in parents):raise ValueError('정적 engine에 시차 입력 금지')
            if any(p['source'] not in equations for p in parents):raise ValueError('알 수 없는 부모')
            if all(p['source'] in order for p in parents):ready.append(name)
        if not ready:raise ValueError('CYCLIC_OR_UNSUPPORTED: 간선 임의 삭제 금지')
        order.extend(ready);pending.difference_update(ready)
    return order,equations


def static_mean_response(artifact, action, value):
    """Zero residual mean propagation; neither abduction nor validated causal effect."""
    if not math.isfinite(value):raise ValueError('비유한 action')
    order,equations=order_equations(artifact)
    if action not in equations:raise ValueError('미등록 action')
    z={}
    for name in order:
        if name == action:
            z[name]=(value-artifact['scaler_mean'][name])/artifact['scaler_std'][name]
        else:
            eq=equations[name]
            z[name]=eq['intercept_standardized']+sum(p['coefficient_standardized']*z[p['source']] for p in eq['parents'])
        if not math.isfinite(z[name]):raise ValueError('비유한 예측')
    return {v:z[v]*artifact['scaler_std'][v]+artifact['scaler_mean'][v] for v in order}


def recommend_grid(artifact, action, target, deltas, debug_target, cost_weight=0.01):
    if not deltas or any(not math.isfinite(x) or abs(x)>0.1 for x in deltas):
        raise ValueError('dry-run 공통 후보 범위 초과')
    base=artifact['scaler_mean'][action]
    rows=[]
    for delta in deltas:
        value=base+delta
        if not 0<=value<=100:raise ValueError('XMV API 범위 초과; 안전 범위라는 뜻 아님')
        predicted=static_mean_response(artifact,action,value)[target]
        cost=(delta/0.1)**2
        loss=((predicted-debug_target)/artifact['scaler_std'][target])**2+cost_weight*cost
        rows.append(dict(delta_pp=delta,absolute_command=value,predicted_target=predicted,
                         normalized_command_cost=cost,surrogate_objective=loss))
    chosen=min(rows,key=lambda r:(r['surrogate_objective'],abs(r['delta_pp']),r['delta_pp']))
    return dict(status='DRY_RUN_NOT_CAUSAL_VALIDATION',selected=chosen,candidates=rows,
                simulator_execution_allowed=False,strict_counterfactual=False)


def reachable(edges, source, target):
    visited={source};queue=[source]
    while queue:
        node=queue.pop()
        for a,b in edges:
            if a != node:continue
            if b == target:return True
            if b not in visited:visited.add(b);queue.append(b)
    return False


def task_metrics(task, confirmed_edges, gt_edges, unresolved_pairs=None):
    paths=task['gt_path']
    path_edges={edge for path in paths for edge in zip(path,path[1:])}
    if not path_edges or not path_edges<=gt_edges:raise ValueError('GT 경로 불일치')
    recovered=len(path_edges & confirmed_edges)
    exact=sum(all(e in confirmed_edges for e in zip(p,p[1:])) for p in paths)
    pair=(task['action'],task['target'])
    unresolved=frozenset(pair) in (unresolved_pairs or set())
    return dict(task_id=task['task_id'],action=pair[0],target=pair[1],
        gt_path_edge_count=len(path_edges),recovered_gt_path_edges=recovered,
        gt_path_edge_recall=recovered/len(path_edges),complete_gt_path_fraction=exact/len(paths),
        confirmed_action_target_reachable=reachable(confirmed_edges,*pair),
        direct_xy_truth=pair in gt_edges,direct_xy_confirmed=pair in confirmed_edges,
        direct_xy_state='UNRESOLVED' if unresolved else ('CONFIRMED' if pair in confirmed_edges else 'ABSENT'),
        direct_xy_correct=None if unresolved else (pair in gt_edges)==(pair in confirmed_edges),
        interpretation='기존 benchmark 구조 진단. 새 simulator 효과와 연결 금지. 경로 recall은 precision/F1 아님')

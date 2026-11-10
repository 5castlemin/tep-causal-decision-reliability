"""Budgeted oracle graph editing; no SCM fitting, outcome or evaluator interface."""
from collections import deque,Counter
from hashlib import sha256
from itertools import combinations
from random import Random
import json,math

KINDS=("FN","FP","REV")

def _hash(value):
    return sha256(json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode()).hexdigest()

def _node_ids(nodes):
    if type(nodes) not in (list,tuple,set,frozenset):raise ValueError("node IDs must be a concrete collection")
    ids=list(nodes)
    if not ids or any(type(v) is not str or not v for v in ids) or len(set(ids))!=len(ids):
        raise ValueError("node IDs must be unique nonempty strings")
    return tuple(sorted(ids))

def _graph(nodes,edges):
    if type(edges) not in (list,tuple,set,frozenset):raise ValueError("edges must be a concrete collection")
    raw=list(edges);valid=set(nodes);out=set()
    for e in raw:
        if not isinstance(e,(tuple,list)) or len(e)!=2:raise ValueError("invalid edge")
        a,b=e
        if type(a) is not str or type(b) is not str or a not in valid or b not in valid or a==b:raise ValueError("unknown or self edge")
        if (a,b) in out or (b,a) in out:raise ValueError("duplicate or bidirected edge")
        out.add((a,b))
    if not _acyclic(nodes,out):raise ValueError("graph must be DAG")
    return frozenset(out)

def _acyclic(nodes,edges):
    degree={x:0 for x in nodes};children={x:[] for x in nodes}
    for a,b in edges:degree[b]+=1;children[a].append(b)
    q=deque(x for x in nodes if degree[x]==0);n=0
    while q:
        x=q.popleft();n+=1
        for y in children[x]:
            degree[y]-=1
            if not degree[y]:q.append(y)
    return n==len(nodes)

def schema_mapping(ids, expected_ids, values):
    """Bind data columns to a frozen schema; reject silent positional reordering."""
    ids=list(ids);expected=list(expected_ids);values=list(values)
    _node_ids(ids);_node_ids(expected)
    if ids!=expected or len(values)!=len(ids):raise ValueError("schema order or length mismatch")
    return dict(zip(ids,values))

def _candidates(nodes,truth,g,allowed):
    ans=[]
    for a,b in combinations(nodes,2):
        t=(a,b) if (a,b) in truth else (b,a) if (b,a) in truth else None
        x=(a,b) if (a,b) in g else (b,a) if (b,a) in g else None
        op=("FN",*t) if t and not x else ("FP",*x) if x and not t else ("REV",*x) if t and x and t!=x else None
        if op and op[0] in allowed:ans.append(op)
    return ans

def _apply(g,op):
    k,a,b=op;h=set(g)
    if k=="FN":h.add((a,b))
    elif k=="FP":h.remove((a,b))
    else:h.remove((a,b));h.add((b,a))
    return frozenset(h)

def _distance(nodes,g,h,action,target):
    adj={n:set() for n in nodes}
    for a,b in g|h:adj[a].add(b);adj[b].add(a)
    d={action:0,target:0};q=deque(d)
    while q:
        n=q.popleft()
        for m in adj[n]:
            if m not in d:d[m]=d[n]+1;q.append(m)
    return d

def _path_edges(nodes,edges,source,target):
    children={x:[] for x in nodes}
    for a,b in edges:children[a].append(b)
    result=set()
    def visit(x,trail):
        if x==target:result.update(zip(trail,trail[1:]));return
        for y in children[x]:visit(y,trail+[y])
    visit(source,[source]);return result

def path_f1(nodes,truth,graph,action,target):
    r=_path_edges(nodes,truth,action,target);p=_path_edges(nodes,graph,action,target)
    if not r and not p:return None
    return 2*len(r&p)/(len(r)+len(p))

def compare_edits(a,b):
    a=[tuple(x) for x in a];b=[tuple(x) for x in b];aa=set(a);bb=set(b)
    n=0
    for x,y in zip(a,b):
        if x!=y:break
        n+=1
    return {"jaccard":len(aa&bb)/len(aa|bb) if aa|bb else 1.0,"sequence_equal":a==b,"common_prefix_length":n}

def refine(*,node_ids,initial_edges,reference_edges,allowed_types,policy_id,budget,gamma,action,target,prior_edges=(),seed=0,display_names=None,graph_id=None):
    """Policy input is graph-only: rejects outcome/evaluator objects by construction."""
    nodes=_node_ids(node_ids);initial=_graph(nodes,initial_edges);truth=_graph(nodes,reference_edges)
    if type(budget) is not int or budget<0 or type(gamma) is not int or gamma not in (1,2,3) or type(seed) is not int:raise ValueError("invalid budget/gamma/seed")
    if type(action) is not str or type(target) is not str or action not in nodes or target not in nodes or action==target:raise ValueError("invalid task")
    if type(allowed_types) not in (list,tuple,set,frozenset) or type(prior_edges) not in (list,tuple,set,frozenset):raise ValueError("invalid collection")
    if type(policy_id) is not str or (graph_id is not None and (type(graph_id) is not str or not graph_id)):raise ValueError("invalid policy or graph ID")
    raw=list(allowed_types)
    if len(raw)!=len(set(raw)) or not raw or any(x not in KINDS for x in raw):raise ValueError("invalid allowed types")
    allowed=tuple(k for k in KINDS if k in raw);mode=policy_id.split("-")[0]
    expected=mode+"-"+"-".join(allowed)
    if policy_id not in (expected,"NO-EDIT","RANDOM","PATH-F1") or mode not in ("G","T","NO","RANDOM","PATH"):raise ValueError("invalid policy ID")
    if display_names is None:display_names={n:n for n in nodes}
    if type(display_names) is not dict or set(display_names)!=set(nodes) or any(type(x) is not str for x in display_names.values()) or len(set(display_names.values()))!=len(nodes):raise ValueError("invalid display mapping")
    # H is an undirected input; validate IDs and duplicates but not acyclicity.
    h=[];pairs=set()
    for edge in prior_edges:
        if not isinstance(edge,(tuple,list)) or len(edge)!=2:raise ValueError("invalid H")
        a,b=edge
        if type(a) is not str or type(b) is not str or a not in nodes or b not in nodes or a==b or frozenset((a,b)) in pairs:raise ValueError("invalid H")
        pairs.add(frozenset((a,b)));h.append((a,b))
    distances=_distance(nodes,initial,set(h),action,target);graph=initial;rng=Random(seed)
    order=allowed[seed%len(allowed):]+allowed[:seed%len(allowed)]
    graph_hash=lambda g:_hash({"node_ids":nodes,"edges":sorted(g)})
    log={"version":"step2-v1","initial_graph_id":graph_id or graph_hash(initial),"initial_hash":graph_hash(initial),"initial_graph":sorted(initial),"node_ids":nodes,"display_names":display_names,"allowed_types":allowed,"policy_id":policy_id,"budget":budget,"gamma":gamma,"action":action,"target":target,"prior_edges":sorted(h),"seed":seed,"type_schedule":order,"candidate_operations":[],"rejected_operations":[],"edit_sequence":[],"ledger":[],"type_opportunities":[],"failure_reason":None}
    spent=0;path_skips=set()
    if policy_id!="NO-EDIT":
        while True:
            progress=False
            for kind in order:
                ops=_candidates(nodes,truth,graph,(kind,));cost=gamma if kind=="REV" else 1;valid=[]
                log["type_opportunities"].append(kind);log["candidate_operations"].append({"type":kind,"operations":ops})
                for op in ops:
                    if spent+cost>budget:log["rejected_operations"].append({"operation":op,"reason":"budget","cost":0});continue
                    new=_apply(graph,op)
                    if not _acyclic(nodes,new):log["rejected_operations"].append({"operation":op,"reason":"cycle","cost":0});continue
                    valid.append((op,new))
                if not valid:continue
                if mode=="T":
                    def score(op):return sum(1/(1+distances[x]) if x in distances else 0 for x in op[1:])
                    valid.sort(key=lambda x:(-score(x[0]),x[0][1],x[0][2]))
                    log["candidate_operations"][-1]["priority_scores"]=[{"operation":x[0],"score":score(x[0])} for x in valid]
                elif policy_id=="RANDOM":
                    valid.sort(key=lambda x:x[0]);rng.shuffle(valid)
                elif policy_id=="PATH-F1":
                    current=path_f1(nodes,truth,graph,action,target);scores=[]
                    for op,new in valid:
                        after=path_f1(nodes,truth,new,action,target)
                        gain=None if current is None or after is None else after-current
                        scores.append((op,new,gain,after))
                    valid=[(op,new) for op,new,gain,after in sorted(scores,key=lambda x:(-(x[2] if x[2] is not None else -math.inf),x[0])) if gain is not None and gain>0]
                    log["candidate_operations"][-1]["path_scores"]=[{"operation":op,"before":current,"after":after,"gain":gain} for op,new,gain,after in scores]
                    if not valid:
                        why="path_undefined" if all(gain is None for op,new,gain,after in scores) else "path_no_positive_gain"
                        path_skips.add(why);log["rejected_operations"].append({"type":kind,"reason":why,"cost":0});continue
                else:valid.sort(key=lambda x:(x[0][1],x[0][2]))
                log["candidate_operations"][-1]["selection_order"]=[x[0] for x in valid]
                op,graph=valid[0];spent+=cost;progress=True;log["edit_sequence"].append(op);log["ledger"].append({"operation":op,"cost":cost})
            if not progress:break
    remaining=_candidates(nodes,truth,graph,allowed)
    if policy_id=="NO-EDIT":reason="no_edit"
    elif not remaining:reason="candidates_exhausted"
    elif spent==budget:reason="budget_exhausted"
    elif path_skips:reason=next(iter(path_skips)) if len(path_skips)==1 else "path_mixed_skips"
    else:
        reasons={r["reason"] for r in log["rejected_operations"]};reason="no_affordable_candidate" if "budget" in reasons and "cycle" not in reasons else "no_valid_candidate"
    assert sum(x["cost"] for x in log["ledger"])==spent and spent<=budget
    assert len(set(log["edit_sequence"]))==len(log["edit_sequence"])
    log.update(final_graph=sorted(graph),final_hash=graph_hash(graph),spent_budget=spent,unused_budget=budget-spent,termination_reason=reason,type_edit_counts={k:sum(o[0]==k for o in log["edit_sequence"]) for k in KINDS},type_opportunity_counts=dict(Counter(log["type_opportunities"])),reference_hash=graph_hash(truth),path_f1_status="extra_truth_path_oracle" if policy_id=="PATH-F1" else "not_used")
    return log

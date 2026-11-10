"""Small DAG contract fixtures, not a research policy engine."""
from collections import deque
from itertools import combinations

KINDS=("FN","FP","REV")

def dag(nodes, edges):
    incoming={v:0 for v in nodes}; children={v:[] for v in nodes}
    for a,b in edges:
        if a not in incoming or b not in incoming or a==b:return False
        incoming[b]+=1;children[a].append(b)
    ready=deque(v for v in nodes if incoming[v]==0);seen=0
    while ready:
        x=ready.popleft();seen+=1
        for y in children[x]:
            incoming[y]-=1
            if incoming[y]==0:ready.append(y)
    return seen==len(nodes)

def candidates(nodes,truth,graph,allowed):
    if not dag(nodes,truth) or not dag(nodes,graph):raise ValueError("DAG required")
    out=[]
    for a,b in combinations(nodes,2):
        t=(a,b) if (a,b) in truth else (b,a) if (b,a) in truth else None
        g=(a,b) if (a,b) in graph else (b,a) if (b,a) in graph else None
        if t and not g:op=("FN",*t)
        elif g and not t:op=("FP",*g)
        elif t and g and t!=g:op=("REV",*g)
        else:continue
        if op[0] in allowed:out.append(op)
    return out

def apply(graph,op):
    kind,a,b=op;out=set(graph)
    if kind=="FN":out.add((a,b))
    elif kind=="FP":out.remove((a,b))
    elif kind=="REV":out.remove((a,b));out.add((b,a))
    else:raise ValueError(kind)
    return frozenset(out)

def distances(nodes,initial,external,action,target):
    adj={v:set() for v in nodes}
    for a,b in set(initial)|set(external):
        if a not in adj or b not in adj or a==b:raise ValueError("invalid H")
        adj[a].add(b);adj[b].add(a)
    dist={action:0,target:0};q=deque(dist)
    while q:
        a=q.popleft()
        for b in adj[a]:
            if b not in dist:dist[b]=dist[a]+1;q.append(b)
    return dist

def score(op,dist):
    return sum(1/(1+dist[v]) if v in dist else 0 for v in op[1:])

def run(nodes,truth,initial,allowed,budget,action,target,focused=False,external=(),seed=0,gamma=1,policy_id=None):
    if budget<0 or gamma not in (1,2,3):raise ValueError("budget/gamma")
    allowed=tuple(k for k in KINDS if k in allowed)
    if not allowed:raise ValueError("allowed")
    ids={v:i for i,v in enumerate(nodes)}
    if len(ids)!=len(nodes):raise ValueError("duplicate nodes")
    dist=distances(nodes,initial,external,action,target);graph=frozenset(initial)
    log=dict(initial_graph=sorted(initial),allowed_types=allowed,candidate_operations=[],rejected_operations=[],edit_sequence=[],final_graph=[],spent_budget=0,unused_budget=budget,failure_reason=None,policy_id=policy_id or ("T" if focused else "G")+"-"+"-".join(allowed),seed=seed,type_opportunities=[])
    order=allowed[seed%len(allowed):]+allowed[:seed%len(allowed)]
    while True:
        progressed=False
        for kind in order:
            ops=[o for o in candidates(nodes,truth,graph,allowed) if o[0]==kind]
            cost=gamma if kind=="REV" else 1
            log["type_opportunities"].append(kind)
            log["candidate_operations"].append({"type":kind,"operations":ops})
            ops.sort(key=lambda o:((-score(o,dist) if focused else 0),ids[o[1]],ids[o[2]]))
            for op in ops:
                if log["spent_budget"]+cost>budget:
                    log["rejected_operations"].append((op,"budget"));continue
                nxt=apply(graph,op)
                if not dag(nodes,nxt):
                    log["rejected_operations"].append((op,"cycle"));continue
                graph=nxt;log["edit_sequence"].append(op);log["spent_budget"]+=cost;progressed=True;break
        if not progressed:break
    log["final_graph"]=sorted(graph);log["unused_budget"]=budget-log["spent_budget"]
    remaining=candidates(nodes,truth,graph,allowed)
    log["termination_reason"]=("budget_exhausted" if log["unused_budget"]==0 else
        "no_candidates" if not remaining else "no_valid_or_affordable_candidate")
    if not log["edit_sequence"]:log["failure_reason"]="no_edit_budget_or_valid_candidate"
    return log

def enumerate_valid(nodes,truth,graph,allowed,budget,gamma=1):
    """Exhaustively explore valid error-correcting orders (fixture sizes only)."""
    found=[()]
    def visit(g,left,path):
        for op in candidates(nodes,truth,g,allowed):
            cost=gamma if op[0]=="REV" else 1
            if cost<=left:
                nxt=apply(g,op)
                if dag(nodes,nxt):
                    new=path+(op,);found.append(new);visit(nxt,left-cost,new)
    visit(frozenset(graph),budget,())
    return found

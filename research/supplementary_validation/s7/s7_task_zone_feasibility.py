"""Time-bounded exactness/performance feasibility for S7 task-zone calculation."""
from __future__ import annotations
import argparse,hashlib,json,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from research.original_objective import policy_engine as pe
from research.supplementary_validation.s7.task_zone_fast import task_zone_fast

PINNED="8da3729e6383f0e1cbe7740bb6ab7ac4977ac7f9"
TASKS=(("Station2_mp_13","Station2_mp_33"),("Station3_mp_43","Station3_mp_45"))

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def load_graph(path):
    raw=json.loads(Path(path).read_text(encoding="utf-8"));nodes=[x["id"] for x in raw["nodes"]]
    if not raw.get("directed") or len(raw["adjacency"])!=len(nodes):raise ValueError("unexpected pinned reference schema")
    edges=[]
    for u,neigh in zip(nodes,raw["adjacency"]):
        edges.extend((u,x["id"]) for x in neigh)
    if len(set(edges))!=len(edges):raise ValueError("duplicate directed reference edge")
    graph=pe.state(edges)
    if len(nodes)!=98 or len(edges)!=485:raise ValueError(f"reference size mismatch: {len(nodes)} nodes/{len(edges)} edges")
    return graph,nodes,edges

def pruned_reference(truth,action,target,deadline):
    """Independent path traversal with only logically safe collider-prefix pruning."""
    if action==target:raise ValueError("Action and target must differ")
    edges={e for e in truth.values() if e!="UNRES"};adj={n:set() for e in edges for n in e}
    for u,v in edges:adj[u].add(v);adj[v].add(u)
    if action not in adj or target not in adj:return set(),{action,target}
    selected=set();visited_count=0
    def visit(path):
        nonlocal visited_count
        visited_count+=1
        if visited_count%1024==0 and time.monotonic()>deadline:raise TimeoutError("reference traversal exceeded locked feasibility cap")
        last=path[-1]
        if last==target:
            directed=all((u,v) in edges for u,v in zip(path,path[1:]))
            backdoor=(path[1],action) in edges and all(not((path[i-1],path[i]) in edges and (path[i+1],path[i]) in edges) for i in range(1,len(path)-1))
            if directed or backdoor:selected.update(tuple(sorted((u,v))) for u,v in zip(path,path[1:]))
            return
        for nxt in sorted(adj[last]-set(path)):
            # Appending nxt makes the current last node an internal node.
            if len(path)>=2 and (path[-2],last) in edges and (nxt,last) in edges:continue
            visit(path+[nxt])
    visit([action])
    return selected,{n for e in selected for n in e}|{action,target}

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--source-root",type=Path,required=True);ap.add_argument("--time-cap-seconds",type=int,default=900);a=ap.parse_args()
    start=time.monotonic();src=a.source_root.resolve()
    commit=subprocess.check_output(["git","-C",str(src),"rev-parse","HEAD"],text=True).strip()
    if commit!=PINNED:raise ValueError(f"causalAssembly source mismatch: {commit}")
    gp=src/"data"/"ground_truth"/"ground_truth.json";truth,nodes,edges=load_graph(gp)
    table={};deadline=start+a.time_cap_seconds;reference_counts=[]
    for action,target in TASKS:
        remaining=a.time_cap_seconds-(time.monotonic()-start)
        zone,znodes=task_zone_fast(truth,action,target,max_seconds=remaining)
        ref_zone,ref_nodes=pruned_reference(truth,action,target,deadline)
        if (zone,znodes)!=(ref_zone,ref_nodes):raise AssertionError(f"full-graph implementation mismatch for {action}->{target}")
        reference_counts.append({"task":[action,target],"fast_edge_pairs":len(zone),"reference_edge_pairs":len(ref_zone),"exact_match":True})
        table[(action,target)]=(zone,znodes)
    # One in-memory, outcome-blind recommendation smoke per task. No evaluator,
    # response vectors, or action-loss data are loaded or accessed.
    old=pe.task_zone;smoke=[]
    def cached_zone(g,x,y):
        if (x,y) not in table:raise ValueError("smoke requested an unlocked task")
        return table[(x,y)]
    try:
        pe.task_zone=cached_zone
        for action,target in TASKS:
            zone,_=table[(action,target)]
            editable=sorted((p for p in zone if p in truth and truth[p]!="UNRES"))
            if not editable:raise ValueError(f"no structural repair opportunity for smoke task {action}->{target}")
            g0=dict(truth);chosen=editable[0];g0.pop(chosen)
            began=time.monotonic();result=pe.run(truth,g0,action,target,budget=1,subset=("M4",),config=pe.Config())
            smoke.append({"task":[action,target],"g0_edit":"remove one canonical task-zone edge in memory","recommendation_units":1,"candidate_edge_pair":list(chosen),"recommendation_cost":float(result["total_cost"]),"recommendation_count":len(result["edits"]),"stop_reason":result["stop_reason"],"recommendation_elapsed_seconds":time.monotonic()-began,"evaluator_accessed":False})
    finally:pe.task_zone=old
    report={"schema":"S7_TASK_ZONE_FEASIBILITY_V1","status":"PASS_EXACTNESS_SMALL_DAGS_AND_FULL_GRAPH","classification":"IMPLEMENTATION_FEASIBILITY_ONLY","source_commit":commit,"reference_path":"causalAssembly/data/ground_truth/ground_truth.json","reference_sha256":sha(gp),"nodes":len(nodes),"directed_edges":len(edges),"tasks":[{"action":x,"target":y,"task_zone_edge_pairs":len(table[(x,y)][0]),"task_zone_nodes":len(table[(x,y)][1])} for x,y in TASKS],"full_graph_independent_pruned_reference_comparison":reference_counts,"recommendation_smoke":smoke,"elapsed_seconds":time.monotonic()-start,"time_cap_seconds":a.time_cap_seconds,"evaluator_or_intervention_accessed":False,"full_g0_or_recommendation_run":"NOT_RUN","caveat":"Frozen unpruned enumerator did not return in the earlier run. Full-graph exact equality was verified against an independent collider-pruned DFS implementing the frozen terminal predicates; the frozen function itself was exhaustively matched on every 4-node DAG and targeted UNRES classification fixtures."}
    print(json.dumps(report,ensure_ascii=False,sort_keys=True))

if __name__=="__main__":main()

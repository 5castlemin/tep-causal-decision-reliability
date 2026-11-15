"""Bounded benchmarks on existing fixed fixtures; no SCM/data generation."""
from __future__ import annotations
import json, platform, sys, time, tracemalloc
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT)); sys.path.insert(0,str(ROOT/'src'))
from research.budget_aware_refinement.step4_topology_generator import generate_topology, directed_paths
from research.budget_aware_refinement.step4_error_injection import classify_errors
from research.budget_aware_refinement.policy_engine import refine, path_f1
from integrated_pilot import fit_model

REPS=200
# Fixed DAG fixture from the existing Step 3 unit test contract; not sampled.
names=['A','B','Y']
data=np.array([[0.,0.,1.],[1.,2.,3.],[2.,4.,7.],[3.,6.,9.]])
# Topology-only maximum-size fixture with one existing path task.
g=generate_topology(10,'multiple_directed_paths',seed=1904)
truth=set(g.edges)
paths=directed_paths(g.nodes,truth,g.nodes[0],g.nodes[-1])
if not paths: raise RuntimeError('fixed topology fixture unexpectedly lacks endpoint path')
removed=next(iter(sorted(set(zip(paths[0],paths[0][1:])))))
initial=truth-{removed}
request=dict(node_ids=list(g.nodes),initial_edges=sorted(initial),reference_edges=sorted(truth),
             allowed_types=['FN'],policy_id='G-FN',budget=1,gamma=1,
             action=g.nodes[0],target=g.nodes[-1],seed=0)
def timed(fn,reps=REPS):
    vals=[]
    for _ in range(reps):
        t=time.perf_counter();fn();vals.append(time.perf_counter()-t)
    vals.sort()
    return {'repetitions':reps,'median_seconds':vals[len(vals)//2],
            'p95_seconds':vals[int(.95*(len(vals)-1))],'max_seconds':vals[-1]}
tracemalloc.start()
graph_time=timed(lambda:refine(**request))
path_time=timed(lambda:path_f1(g.nodes,truth,initial,g.nodes[0],g.nodes[-1]))
model_time=timed(lambda:fit_model(data,names,{('A','B'),('B','Y')},1.0))
peak=tracemalloc.get_traced_memory()[1];tracemalloc.stop()
logrow={'run_id':'fixture-0001','status':'OK','graph_hash':'0'*64,'policy':'G-FN','spent':1,'unused':0,'elapsed_s':0.00123}
jsonl=(json.dumps(logrow,separators=(',',':'))+'\n').encode()
report={'protocol':'STEP4B4_FIXED_FIXTURE_BENCH_V1','no_new_scm_or_observations':True,
 'python':sys.version.split()[0],'numpy':np.__version__,'platform':platform.platform(),
 'repetitions':REPS,'topology_fixture':{'template':'multiple_directed_paths','nodes':10,'edges':len(truth),'seed':1904,'task':[g.nodes[0],g.nodes[-1]]},
 'step3_fixed_fixture':{'rows':len(data),'columns':len(names),'source':'tests/test_budget_refinement_step3.py::Step3.setUp'},
 'graph_policy_refine':graph_time,'path_f1':path_time,'ridge_fit_fixed_3node_fixture':model_time,
 'python_tracemalloc_peak_bytes':peak,'sample_jsonl_row_bytes':len(jsonl),
 'limits':['tracemalloc excludes native NumPy/RSS allocations','3-node Ridge fixture cannot estimate 10-node model scaling','single machine microbenchmark is not a full-run wall-time guarantee','no resume/restart benchmark in this run']}
out=Path(__file__).with_name('step4b4_resource_bench_v1.json');out.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n',encoding='utf-8')
print(json.dumps({'output':str(out.name),'graph_median_s':graph_time['median_seconds'],'ridge_median_s':model_time['median_seconds'],'peak_python_bytes':peak,'jsonl_row_bytes':len(jsonl)},indent=2))

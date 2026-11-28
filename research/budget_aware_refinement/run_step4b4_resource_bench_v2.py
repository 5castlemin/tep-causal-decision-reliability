"""Mock integration benchmark: fixed numeric matrix, not an SCM or sample."""
from __future__ import annotations
import ctypes,json,math,platform,sys,tempfile,time,tracemalloc
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'src'))
from research.budget_aware_refinement.step4_topology_generator import generate_topology,directed_paths
from research.budget_aware_refinement.step4b2_population import competition_recipes
from research.budget_aware_refinement.policy_engine import refine,path_f1
from research.budget_aware_refinement.step3_adapter import prepare
from integrated_pilot import fit_model
from decision_mvp import static_mean_response
from hashlib import sha256
REPS=200;E2E_REPS=100
def rss_bytes():
 if sys.platform=='win32':
  class PMC(ctypes.Structure):
   _fields_=[('cb',ctypes.c_ulong),('PageFaultCount',ctypes.c_ulong),('PeakWorkingSetSize',ctypes.c_size_t),('WorkingSetSize',ctypes.c_size_t),('QuotaPeakPagedPoolUsage',ctypes.c_size_t),('QuotaPagedPoolUsage',ctypes.c_size_t),('QuotaPeakNonPagedPoolUsage',ctypes.c_size_t),('QuotaNonPagedPoolUsage',ctypes.c_size_t),('PagefileUsage',ctypes.c_size_t),('PeakPagefileUsage',ctypes.c_size_t),('PrivateUsage',ctypes.c_size_t)]
  pmc=PMC();pmc.cb=ctypes.sizeof(PMC);handle=ctypes.windll.kernel32.GetCurrentProcess();fn=ctypes.WinDLL('Psapi.dll').GetProcessMemoryInfo;fn.argtypes=[ctypes.c_void_p,ctypes.POINTER(PMC),ctypes.c_ulong];fn.restype=ctypes.c_int
  if fn(handle,ctypes.byref(pmc),pmc.cb):return {'rss':int(pmc.WorkingSetSize),'peak_rss':int(pmc.PeakWorkingSetSize)}
 return {'rss':None,'peak_rss':None}
def timed(fn,n):
 values=[]
 for _ in range(n):
  start=time.perf_counter();fn();values.append(time.perf_counter()-start)
 values.sort();return {'n':n,'median_s':values[len(values)//2],'p95_s':values[int(.95*(len(values)-1))],'max_s':values[-1]}
def append_once(path,row):
 existing=set()
 if path.exists():
  for line in path.read_text(encoding='utf-8').splitlines():
   if line.strip():existing.add(json.loads(line)['run_id'])
 if row['run_id'] in existing:return False
 with path.open('a',encoding='utf-8',newline='') as f:f.write(json.dumps(row,sort_keys=True,separators=(',',':'))+'\n')
 return True
def run():
 names=[f'V{i:02d}' for i in range(10)];g=generate_topology(10,'multiple_directed_paths',1904);truth=set(g.edges);paths=directed_paths(g.nodes,truth,g.nodes[0],g.nodes[-1]);task=(g.nodes[0],g.nodes[-1]);remove=next(iter(sorted(set(zip(paths[0],paths[0][1:])))));initial=truth-{remove}
 # Deterministic dummy numeric matrix, explicitly not generated from a causal SCM.
 r=np.arange(512,dtype=float)[:,None];c=np.arange(10,dtype=float)[None,:];matrix=np.sin(.013*r*(c+1))+np.cos(.017*r*(c+2))+.07*c+.0003*r
 req={'node_ids':names,'initial_edges':sorted(initial),'reference_edges':sorted(truth),'allowed_types':['FN'],'policy_id':'G-FN','budget':1,'gamma':1,'action':task[0],'target':task[1],'seed':0}
 def graph_run():return refine(**req)
 def q_eligibility_run():
  topo=generate_topology(10,'multiple_directed_paths',1904+q_eligibility_run.counter);q_eligibility_run.counter+=1;ts=[t for t in topo.tasks if t.kind=='indirect'];action,target=ts[0].action,ts[0].target if ts else (topo.nodes[0],topo.nodes[-1]);return {kind:len(competition_recipes(topo.nodes,topo.edges,action,target,kind)) for kind in ('FN','FP','REV')}
 q_eligibility_run.counter=0
 graph=graph_run();edges={tuple(x) for x in graph['final_graph']}
 def fit():return fit_model(matrix,names,edges,1.)
 model=fit();means=matrix.mean(axis=0);sds=matrix.std(axis=0,ddof=1);ai=names.index(task[0]);ti=names.index(task[1]);actions=[float(means[ai]+k*sds[ai]) for k in (-1.,-.5,0.,.5,1.)]
 def candidates():return [static_mean_response(model,task[0],a)[task[1]] for a in actions]
 def end_to_end():return prepare(req,matrix,names,names,1,fit_model,static_mean_response)
 rss_before=rss_bytes();tracemalloc.start();graph_t=timed(graph_run,REPS);q_generation_t=timed(q_eligibility_run,10);path_t=timed(lambda:path_f1(g.nodes,truth,initial,*task),REPS);fit_t=timed(fit,REPS);pred_t=timed(candidates,REPS);e2e_t=timed(end_to_end,E2E_REPS);py_peak=tracemalloc.get_traced_memory()[1];tracemalloc.stop();rss_after=rss_bytes()
 normal={'run_id':'fixture-0001','status':'OK','graph_sha256':sha256(json.dumps(sorted(edges)).encode()).hexdigest(),'policy':'G-FN','n_nodes':10,'edge_count':len(edges),'spent_cost':1,'retry':0,'elapsed_seconds':.001234,'candidate_predictions':[float(x) for x in candidates()]}
 failure={'run_id':'fixture-failure-0001','status':'RIDGE_FAIL','failure_reason':'mocked_expected_failure','retry':0,'fallback_status':'NOT_APPLIED'}
 with tempfile.TemporaryDirectory() as td:
  log=Path(td)/'runs.jsonl';first=append_once(log,normal);second=append_once(log,normal);restarted=append_once(log,normal);records=len(log.read_text(encoding='utf-8').splitlines());resume={'first_append':first,'same_process_duplicate_blocked':not second,'reopened_duplicate_blocked':not restarted,'rows_after_restart':records}
 sizes={};base=dict(normal);base.pop('candidate_predictions')
 for count in (1,10,100):
  row=dict(base,candidate_graph_hashes=[f'{i:064x}' for i in range(count)],status='OK');sizes[str(count)]=len((json.dumps(row,sort_keys=True,separators=(',',':'))+'\n').encode())
 fail_size=len((json.dumps(failure,sort_keys=True,separators=(',',':'))+'\n').encode())
 return {'protocol':'STEP4B4_MOCK_RESOURCE_BENCHMARK_V2','fixture':{'type':'deterministic numeric dummy matrix, not SCM/data','shape':list(matrix.shape),'formula':'sin(.013*r*(c+1))+cos(.017*r*(c+2))+.07*c+.0003*r','topology_template':'multiple_directed_paths','nodes':10,'edge_count':len(truth),'path_task':list(task),'seed':1904},'environment':{'python':sys.version.split()[0],'numpy':np.__version__,'platform':platform.platform()},'measurements':{'topology_plus_q_recipe_eligibility_10node':q_generation_t,'graph_policy':graph_t,'path_f1':path_t,'ridge_fit_512x10':fit_t,'five_candidate_predictions':pred_t,'integrated_prepare_fit_recommend':e2e_t,'python_tracemalloc_peak_bytes':py_peak,'process_rss_before':rss_before,'process_rss_after':rss_after,'process_peak_rss_after':rss_after.get('peak_rss'),'jsonl_row_sizes_bytes':sizes,'failure_row_bytes':fail_size,'resume_idempotence_mock':resume},'limits':['timings describe this machine and dummy matrix only','matrix is not SCM-generated and does not test research inference','RSS peak is process-level and may include prior process memory','no final execution ledger exists; the logger is an isolated mock','Q recipe timing uses only 10 fixed-seed 10-node topology-only attempts','no repeated production workload or hard cap chosen'] }
def main():
 x=run();out=Path(__file__).with_name('step4b4_resource_bench_v2.json');out.write_text(json.dumps(x,sort_keys=True,indent=2,allow_nan=False)+'\n',encoding='utf-8');print(json.dumps({'output':out.name,'measurements':x['measurements']},indent=2))
if __name__=='__main__':main()

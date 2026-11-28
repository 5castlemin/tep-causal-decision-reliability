"""Read-only, aggregate-only comparison of the historical and corrected S3 selector."""
import csv, hashlib, json, subprocess, sys, types
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'src')]
from research.within_task_repair_prioritization import s3_analysis as new
from research.budget_aware_refinement.step3_adapter import prepare,evaluate
from research.budget_aware_refinement.step4c1_gt import analytic_response
from integrated_pilot import fit_model
from decision_mvp import static_mean_response
from research.original_objective import policy_engine as pe
OLD_COMMIT='a230ab96e2e204c5d72ed34b049190ae3c6bb276'
old_src=subprocess.run(['git','show',f'{OLD_COMMIT}:research/within_task_repair_prioritization/s3_analysis.py'],cwd=ROOT,check=True,capture_output=True,text=True).stdout
legacy=types.ModuleType('s3_legacy')
legacy.__file__=str(HERE/'s3_analysis_legacy_snapshot.py')
exec(compile(old_src,legacy.__file__,'exec'),legacy.__dict__)
OUT=HERE/'outputs_v8'/'correction_audit'
if OUT.exists(): raise FileExistsError(OUT)
OUT.mkdir(parents=True)
changed=[]; t5_changed_graphs=set(); graph_cache={}
for cohort,cp,pp in new.SOURCES:
 _,rows=new.load_cohort(cohort,cp,pp)
 for sid,proposal,payload,scm,obs,truth,g0,cfg in rows:
  action,target=proposal['action'],proposal['target']
  ctx=(truth,action,target,*new.structural_sets(truth,action,target,cfg))
  oldctx=(truth,action,target,*legacy.structural_sets(truth,action,target,cfg))
  def T5(fn,g,ctx): return fn(g,ctx)['T5']
  for graph in [g0]:
   h=pe.graph_hash(graph)
   if h not in graph_cache:
    x,y=T5(new.q_metrics,graph,ctx),T5(legacy.q_metrics,graph,oldctx)
    graph_cache[h]=(x,y)
    if abs(x-y)>1e-12:t5_changed_graphs.add(h)
  loss_cache={}
  def loss(g):
   h=pe.graph_hash(g)
   if h not in loss_cache:
    req={'node_ids':proposal['nodes'],'action':action,'target':target}
    _,sel=prepare(req,np.asarray(obs['rows'],dtype=np.float64),proposal['nodes'],proposal['nodes'],payload['input_binding']['delta'],fit_model,static_mean_response,graph_result={'final_graph':[list(e) for e in sorted(e for e in g.values() if e!=pe.UNRES)]})
    ev=evaluate(sel,scm['truth_spec'],analytic_response)
    loss_cache[h]=(float(ev['regret']),float(next(r['action'] for r in sel['candidates'] if r['k']==sel['selected_k'])))
   return loss_cache[h]
  for combo in new.SETS:
   for b in (1,2,3,4):
    go,lo=legacy.greedy(truth,g0,action,target,cfg,combo,b)
    gn,ln=new.greedy(truth,g0,action,target,cfg,combo,b)
    ho,hn=pe.graph_hash(go),pe.graph_hash(gn)
    for graph,h,ct in ((go,ho,oldctx),(gn,hn,ctx)):
     if h not in graph_cache:
      xo,yn=T5(legacy.q_metrics,graph,ct),T5(new.q_metrics,graph,ct)
      graph_cache[h]=(yn,xo)
      if abs(yn-xo)>1e-12:t5_changed_graphs.add(h)
    if ho!=hn:
     ro,ao=loss(go); rn,an=loss(gn)
     changed.append({'cohort':cohort,'policy':'+'.join(combo),'budget':b,'scm':sid,'old_graph':ho,'new_graph':hn,'old_action':ao,'new_action':an,'old_regret':ro,'new_regret':rn})
# private SCM keys are used only in-memory; public audit is aggregate-only.
agg=[]
keys=sorted({(r['cohort'],r['policy'],r['budget']) for r in changed})
for c,p,b in keys:
 rr=[r for r in changed if (r['cohort'],r['policy'],r['budget'])==(c,p,b)]
 agg.append({'cohort':c,'policy':p,'budget':b,'changed_graph_scm_count':len(rr),'changed_action_scm_count':sum(r['old_action']!=r['new_action'] for r in rr),'mean_regret_delta_new_minus_old':float(np.mean([r['new_regret']-r['old_regret'] for r in rr])),'changed_regret_scm_count':sum(abs(r['new_regret']-r['old_regret'])>1e-12 for r in rr)})
with (OUT/'corrected_vs_historical_aggregate.csv').open('w',newline='',encoding='utf-8') as f:
 w=csv.DictWriter(f,fieldnames=list(agg[0]));w.writeheader();w.writerows(agg)
summary={'historical_code_commit':OLD_COMMIT,'corrected_code_commit':'0c5a1870714c7e1ef3229e32bac31a0d1a2fd661','distinct_final_graphs_checked':len(graph_cache),'distinct_graphs_with_t5_value_change':len(t5_changed_graphs),'cohort_policy_budget_units_with_graph_change':len(changed),'scm_level_changed_graph_rows':sum(len([r for r in changed if r['cohort']==c and r['policy']==p and r['budget']==b]) for c,p,b in {(r['cohort'],r['policy'],r['budget']) for r in changed}),'scm_level_changed_action_rows':sum(r['old_action']!=r['new_action'] for r in changed),'scm_level_changed_regret_rows':sum(abs(r['new_regret']-r['old_regret'])>1e-12 for r in changed),'new_scm':0,'new_g0':0,'new_observations':0,'new_interventions':0,'unit_rows_written':False}
(OUT/'correction_audit_summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
print(json.dumps(summary,indent=2))

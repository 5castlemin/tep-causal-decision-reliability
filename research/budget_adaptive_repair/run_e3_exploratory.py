"""Exploratory C-only Adaptive M4 and target sensitivity; no new SCMs."""
from __future__ import annotations
import csv, hashlib, json, sqlite3, sys, time, os
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2]; OUT=Path(__file__).resolve().parent/'outputs'
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'src'))
DATA_ROOT=Path(os.environ.get('DAT_RESEARCH_ROOT','C:/DAT_RESEARCH'))
from research.budget_aware_refinement.step4c1_scm import generate_scm_parameters,generate_observations
from research.budget_aware_refinement.step3_adapter import prepare,evaluate,K
from research.budget_aware_refinement.step4c1_gt import analytic_response
from research.original_objective import policy_engine as pe
from research.budget_adaptive_repair.adaptive_m4 import run as adaptive_run
from integrated_pilot import fit_model
from decision_mvp import static_mean_response
SOURCES=[
 ('C_DEVELOPMENT','development',DATA_ROOT/'research-c/development/development-20261123-seed-2026112301-v1/research_c_cohort.sqlite',DATA_ROOT/'research-c/development/development-20261123-seed-2026112301-v1/research_c_proposal_stage.sqlite'),
 ('C_HELDOUT','confirmation',DATA_ROOT/'research-c/heldout/independent-evaluation-20261123-seed-2026112303-v1/research_c_cohort.sqlite',DATA_ROOT/'research-c/heldout/independent-evaluation-20261123-seed-2026112303-v1/research_c_proposal_stage.sqlite')]
DELTAS=(-1.0,-.5,0.0,.5,1.0)

def cfg_from(p):
 c=dict(p['config']['repair_config']);c['costs']=tuple(tuple(x) for x in c['costs']);c['beta']=tuple(c['beta']);c['weights']=tuple(c['weights']);c['route_relevant_fp']=tuple(tuple(x) for x in c['route_relevant_fp']);return pe.Config(**c)
def main():
 OUT.mkdir(parents=True,exist_ok=True); start=time.perf_counter(); adap=[]; sens=[]; refs=[]; summary=[]
 e2=json.loads((OUT/'e2_reconstruction_summary.json').read_text(encoding='utf-8'))
 bmax_by={x['cohort']:x['B_max'] for x in e2['cohorts']}
 for cohort,pc,cp,pp in SOURCES:
  c=sqlite3.connect(f'file:{cp}?mode=ro',uri=True);c.execute('pragma query_only=on');q=sqlite3.connect(f'file:{pp}?mode=ro',uri=True);q.execute('pragma query_only=on')
  proposals={}
  for(raw,) in q.execute("select proposal_json from proposal_attempts where status='ELIGIBLE'"):
   x=json.loads(raw);proposals[x['scm_id']]=x
  maxerr=0
  for scm_id,_,raw in c.execute('select scm_id,status,result_json from scms order by ordinal'):
   payload=json.loads(raw)['payload'];pr=proposals[scm_id];scm=generate_scm_parameters(pr);obs=generate_observations(pr,scm);bind=payload['input_binding']
   assert scm['equation_signature_sha256']==bind['truth_spec_sha256'] and obs['data_sha256']==bind['observations_sha256']
   data=np.asarray(obs['rows'],dtype=np.float64); nodes=pr['nodes']; truth=pe.state([tuple(e) for e in scm['truth_spec']['edges']]);g=payload['g0_generation']['initial_graph'];initial=pe.state([tuple(e) for e in g['edges']],unresolved=[tuple(e) for e in g['unresolved']]);config=cfg_from(payload)
   initial_count=sum(sum(v.values()) for v in pe.metrics(truth,initial,pr['action'],pr['target'],config)['counts'].values());maxerr=max(maxerr,initial_count)
   mu=data.mean(axis=0);sd=data.std(axis=0,ddof=1);xi=nodes.index(pr['action']);yi=nodes.index(pr['target']);actions=[float(mu[xi]+k*sd[xi]) for k in K]
   cache={}
   def fit_graph(graph):
    gh=pe.graph_hash(graph)
    if gh not in cache:
     directed=[list(e) for _,e in sorted(graph.items()) if e!=pe.UNRES]
     model=fit_model(data,list(nodes),set(tuple(e) for e in directed),1.0)
     pred=[float(static_mean_response(model,pr['action'],a)[pr['target']]) for a in actions]
     cache[gh]=(directed,pred)
    return cache[gh]
   def eval_delta(pred,delta):
    target=float(mu[yi]+delta*sd[yi]); truth_mu=[float(analytic_response(scm['truth_spec'],pr['action'],a)[pr['target']]) for a in actions]
    pl=[((v-target)/sd[yi])**2 for v in pred];best=min(range(len(K)),key=lambda i:(pl[i],abs(K[i]),K[i]))
    tl=[((v-target)/sd[yi])**2 for v in truth_mu];opt=min(range(len(K)),key=lambda i:(tl[i],abs(K[i]),K[i]))
    return {'action':actions[best],'k':K[best],'target':target,'scale':float(sd[yi]),'selected_loss':tl[best],'optimal_grid_loss':tl[opt],
            'regret':tl[best]-tl[opt],'optimal_k':K[opt],'internal_optimum':opt not in (0,len(K)-1)}
   # Reference graph diagnostic, not an optimal-action oracle.
   refgraph=truth; _,refpred=fit_graph(refgraph); ref=eval_delta(refpred,float(bind['delta']))
   refs.append({'cohort':cohort,'scm_id':scm_id,**ref,'graph':'reference DAG learner diagnostic'})
   for budget in range(bmax_by[cohort]+1):
    result=adaptive_run(truth,initial,pr['action'],pr['target'],budget,config); graph=result['final_graph'];_,pred=fit_graph(graph)
    baseline=prepare({'node_ids':nodes,'action':pr['action'],'target':pr['target']},data,nodes,nodes,bind['delta'],fit_model,static_mean_response,graph_result={'final_graph':[list(e) for _,e in sorted(graph.items()) if e!=pe.UNRES]})[1]
    true=evaluate(baseline,scm['truth_spec'],analytic_response)
    # Verify the custom learner result is the same as its explicit prediction/analytic calculation.
    default=eval_delta(pred,float(bind['delta'])); assert abs(default['regret']-true['regret'])<1e-12
    adap.append({'cohort':cohort,'scm_id':scm_id,'budget':budget,'regret':default['regret'],'cost':result['cost'],'unused_budget':result['unused_budget'],
                 'remaining_errors':result['remaining_errors'],'task_edits':sum(x['metric']=='M4' for x in result['edits']),
                 'blocker_edits':sum(x['metric']=='M2_BLOCKER' for x in result['edits']),'action':default['action'],'edits':json.dumps(result['edits'],separators=(',',':'))})
    if budget in (1,2,4):
     chosen={'S0':initial,'M4':None,'M2+M4':None,'M1+M2+M3+M4':None,'ADAPTIVE_M4_BLOCKER_AWARE':graph}
     for name,subset,canon in [('M4',('M4',),False),('M2+M4',('M2','M4'),False),('M1+M2+M3+M4',pe.METRICS,False)]:
      chosen[name]=pe.state((lambda z:z['final_edges'])(pe.run(truth,initial,pr['action'],pr['target'],budget,subset,config,canonical=canon)),unresolved=pe.run(truth,initial,pr['action'],pr['target'],budget,subset,config,canonical=canon)['final_unresolved'])
     chosen['S0']=initial
     for name,graph2 in chosen.items():
      _,pred2=fit_graph(graph2)
      for dlt in DELTAS:
       v=eval_delta(pred2,dlt)
       sens.append({'cohort':cohort,'scm_id':scm_id,'policy':name,'budget':budget,'target_delta':dlt,**v})
  c.close();q.close(); summary.append({'cohort':cohort,'n':len(proposals),'B_max':bmax_by[cohort]})
 # aggregated Adaptive summaries and paired bootstraps
 aggregate=[]; rng=np.random.default_rng(2026112603)
 for co in ('C_DEVELOPMENT','C_HELDOUT'):
  rs=[x for x in adap if x['cohort']==co]
  for b in sorted({x['budget'] for x in rs}):
   xs=[x for x in rs if x['budget']==b]; aggregate.append({'cohort':co,'budget':b,'n':len(xs),'mean_regret':float(np.mean([x['regret'] for x in xs])),
     'mean_cost':float(np.mean([x['cost'] for x in xs])),'mean_task_edits':float(np.mean([x['task_edits'] for x in xs])),
     'mean_blocker_edits':float(np.mean([x['blocker_edits'] for x in xs])),'action_change_rate':None,'mean_remaining_errors':float(np.mean([x['remaining_errors'] for x in xs]))})
 def write(name,rows):
  with (OUT/name).open('w',newline='',encoding='utf-8') as f:
   w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 write('adaptive_m4_unit_results.csv',adap);write('adaptive_m4_aggregate.csv',aggregate);write('target_sensitivity_unit_results.csv',sens);write('reference_graph_learner_diagnostic.csv',refs)
 # Target sensitivity aggregation: means and endpoint/interior optimum proportions.
 sensagg=[]
 for co in ('C_DEVELOPMENT','C_HELDOUT'):
  for pol in sorted({x['policy'] for x in sens}):
   for b in (1,2,4):
    for dlt in DELTAS:
     xs=[x for x in sens if x['cohort']==co and x['policy']==pol and x['budget']==b and x['target_delta']==dlt]
     if xs:sensagg.append({'cohort':co,'policy':pol,'budget':b,'target_delta':dlt,'n':len(xs),'mean_regret':float(np.mean([x['regret'] for x in xs])),
      'mean_action':float(np.mean([x['action'] for x in xs])),'internal_optimum_fraction':float(np.mean([x['internal_optimum'] for x in xs]))})
 write('target_sensitivity_aggregate.csv',sensagg)
 summary={'status':'C_ONLY_EXPLORATORY_COMPLETE_D_ROW_LEVEL_UNAVAILABLE','cohorts':summary,'adaptive_policy':'ADAPTIVE_M4_BLOCKER_AWARE; reference-only blocker logic, max one off-task FP deletion per task repair pair; outcomes not inputs',
  'target_sensitivity':{'targets':list(DELTAS),'action_grid':'same five existing C training-frame actions','graph_free':'NOT_APPLICABLE: no approved C graph-free baseline; D unit-level data unavailable'},
  'D':'Not run: raw D rows/artifacts unavailable; do not infer C-like SCM units from D aggregate means.',
  'elapsed_seconds':time.perf_counter()-start,'new_scm_or_g0_count':0,'new_intervention_rows':0}
 (OUT/'e3_summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8');print(json.dumps(summary,indent=2))
if __name__=='__main__':main()

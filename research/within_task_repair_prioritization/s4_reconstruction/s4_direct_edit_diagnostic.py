"""Retrospective unit-level direct correction diagnostic; no data are sampled."""
from __future__ import annotations
import argparse,csv,json,hashlib
from collections import defaultdict
from pathlib import Path
import numpy as np
from research.budget_aware_refinement.step3_adapter import prepare,evaluate
from research.budget_aware_refinement.step4c1_gt import analytic_response
from research.original_objective import policy_engine as pe
from research.within_task_repair_prioritization.s4_completion import run_s4_pilot as base
from src.integrated_pilot import fit_model
from src.decision_mvp import static_mean_response

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def run(path,cohort):
 units=json.loads(Path(path).read_text(encoding='utf-8')); cfg=base.make_config();out=[]
 for u in units:
  p=u['proposal'];truth=pe.state(p['topology_edges']);g0=pe.state(u['initial_graph']['directed_edges'],unresolved=u['initial_graph']['unresolved_pairs']);data=np.asarray(u['observations'],dtype=np.float64);nodes=list(p['nodes']);req={'node_ids':nodes,'action':p['action'],'target':p['target']};delta=int(u['delta'])
  def score(g):
   graph={'final_graph':sorted([list(e) for e in g.values() if e!=pe.UNRES])}
   _,sel=prepare(req,data,nodes,nodes,delta,fit_model,static_mean_response,graph_result=graph)
   ev=evaluate(sel,u['truth_spec'],analytic_response)
   return float(ev['regret']),float(sel['selected_k'])
  before=score(g0);events=pe.metrics(truth,g0,p['action'],p['target'],cfg)['events']
  candidates=pe.candidates(truth,g0,p['action'],p['target'],cfg)
  if len(events)!=len(candidates):raise ValueError(f'candidate/event mismatch for {u["scm_id"]}')
  for e in candidates:
   if events.get(e.pair)!=(e.metric,e.kind):raise ValueError('candidate does not match reference-relative error')
   after=pe.apply(g0,e);legal=pe.dag(after)
   row={'cohort':cohort,'scm_id':u['scm_id'],'candidate_metric':e.metric,'error_type':e.kind,'role':'task_zone' if e.metric=='M4' else 'outside_task_zone','pair':list(e.pair),'operation':e.operation,'cost':1,'before_graph_sha256':pe.graph_hash(g0),'after_graph_sha256':pe.graph_hash(after) if legal else None,'dag_legal':bool(legal),'before_regret':before[0],'before_action_k':before[1]}
   if legal:
    post=score(after);row.update({'after_regret':post[0],'after_action_k':post[1],'regret_reduction':before[0]-post[0],'action_changed':before[1]!=post[1]})
   else:row.update({'after_regret':None,'after_action_k':None,'regret_reduction':None,'action_changed':None})
   out.append(row)
 return out
def main():
 p=argparse.ArgumentParser();p.add_argument('--development',type=Path,required=True);p.add_argument('--confirmation',type=Path,required=True);p.add_argument('--old-pilot',type=Path,required=True);p.add_argument('--private-output',type=Path,required=True);p.add_argument('--public-output',type=Path,required=True);a=p.parse_args()
 for x in (a.private_output,a.public_output):
  if x.exists():raise FileExistsError(f'refusing overwrite: {x}')
 allrows=[]
 allrows+=run(a.development,'reconstructed_development')
 allrows+=run(a.confirmation,'independent_confirmation')
 allrows+=run(a.old_pilot,'historical_s4_pilot')
 a.private_output.mkdir(parents=True);(a.private_output/'direct_edit_unit_results.json').write_text(json.dumps(allrows,sort_keys=True,indent=2,allow_nan=False)+'\n',encoding='utf-8')
 groups=defaultdict(list)
 for r in allrows:
  if r['dag_legal'] and r['regret_reduction'] is not None:groups[(r['cohort'],r['role'],r['error_type'])].append(r)
 agg=[]
 for (cohort,role,kind),rows in sorted(groups.items()):
  vals=np.array([x['regret_reduction'] for x in rows]);
  agg.append({'cohort':cohort,'role':role,'error_type':kind,'n_legal_direct_edits':len(rows),'n_scms':len({r['scm_id'] for r in rows}),'mean_regret_reduction':float(vals.mean()),'median_regret_reduction':float(np.median(vals)),'positive':int((vals>1e-12).sum()),'negative':int((vals< -1e-12).sum()),'zero':int((np.abs(vals)<=1e-12).sum()),'action_change_rate':float(np.mean([x['action_changed'] for x in rows]))})
 a.public_output.mkdir(parents=True)
 with (a.public_output/'direct_edit_aggregate.csv').open('w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=list(agg[0]));w.writeheader();w.writerows(agg)
 summary={'schema':'S4_DIRECT_EDIT_DIAGNOSTIC_V1','n_unit_edits':len(allrows),'n_dag_legal':sum(x['dag_legal'] for x in allrows),'n_dag_illegal':sum(not x['dag_legal'] for x in allrows),'n_task_zone':sum(x['role']=='task_zone' for x in allrows),'n_outside_task_zone':sum(x['role']=='outside_task_zone' for x in allrows),'interpretation':'retrospective direct single-edit response/recommendation replay on saved units; illegal edits have no observed value and are not assigned zero','source_hashes':{'development_inputs':sha(a.development),'confirmation_inputs':sha(a.confirmation),'old_pilot_inputs':sha(a.old_pilot)}}
 (a.public_output/'summary.json').write_text(json.dumps(summary,sort_keys=True,indent=2)+'\n',encoding='utf-8');print(json.dumps(summary,sort_keys=True))
if __name__=='__main__':main()

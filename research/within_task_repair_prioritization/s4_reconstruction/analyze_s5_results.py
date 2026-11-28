"""Independent aggregate and paired two-source analysis of saved S5 responses."""
from __future__ import annotations
import argparse,csv,json,hashlib
from collections import defaultdict
from pathlib import Path
import numpy as np

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def loss(y,target,scale):return ((float(np.mean(y))-target)**2-float(np.var(y,ddof=1))/len(y))/(scale**2)
def main():
 p=argparse.ArgumentParser();p.add_argument('--private',type=Path,required=True);p.add_argument('--evaluator',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 rec=json.loads((a.private/'recommendation_manifest.json').read_text()); ev=json.loads((a.evaluator/'evaluation_manifest.json').read_text()); rows=json.loads((a.evaluator/'unit_policy_losses_private.json').read_text()); target=float(rec['task']['target_value']);scale=float(rec['task']['scale']);n=int(ev['rows_per_action'])
 vectors=[]
 for r in ev['action_records']:
  path=a.evaluator/r['filename']; assert sha(path)==r['sha256']; v=np.load(path,allow_pickle=False); assert len(v)==n and np.isfinite(v).all(); vectors.append(v)
 actions=[float(x) for x in rec['actions']]; amap={v:i for i,v in enumerate(actions)}; by={(r['g0_seed_id'],r['budget'],r['policy_id']):r for r in rows}; gids=rec['g0_seed_ids']; assert len(gids)==200 and len(by)==len(rows)
 for sid in gids:
  for b in range(5):
   if sum(1 for k in by if k[0]==sid and k[1]==b)!=22: raise ValueError('incomplete G0/policy/budget grid')
 aggregate=[]; groups=defaultdict(list)
 for r in rows: groups[(r['policy_id'],r['budget'])].append(r)
 for (policy,b),rs in sorted(groups.items()):
  v=np.array([r['loss'] for r in rs]);cost=np.array([r['edit_count'] for r in rs]); act=np.array([r['recommended_action'] for r in rs]);
  aggregate.append({'policy_id':policy,'budget':b,'n_g0':len(rs),'mean_loss':float(v.mean()),'median_loss':float(np.median(v)),'sd_loss':float(v.std(ddof=1)),'mean_edit_count':float(cost.mean()),'mean_unused_budget':float(np.mean([r['unused_budget'] for r in rs])),'action_change_rate_from_no_repair':float(np.mean([act[i]!=by[(gids[i],0,'S0')]['recommended_action'] for i in range(len(gids))]))})
 # Primary action choices indexed by G0, preserving common action losses.
 s0=np.array([amap[by[(sid,2,'S0')]['recommended_action']] for sid in gids]);m4=np.array([amap[by[(sid,2,'M4')]['recommended_action']] for sid in gids]);n_g=len(gids)
 point_losses=np.array([loss(v,target,scale) for v in vectors]); g0_d=np.array([point_losses[s0[i]]-point_losses[m4[i]] for i in range(n_g)])
 boot_n=10000; chunk=128; interval={}; seedbase=221704811
 # Shared action bootstrap table: each replicate's same action losses are used for every policy/G0.
 for method,seed in [('G0_only',seedbase),('action_MC_only',seedbase+1),('two_source',seedbase+2)]:
  rng=np.random.default_rng(seed); estimates=[]
  for st in range(0,boot_n,chunk):
   m=min(chunk,boot_n-st)
   if method=='G0_only':
    ig=rng.integers(0,n_g,size=(m,n_g)); d=g0_d[ig].mean(axis=1)
   else:
    action_loss=np.empty((m,len(actions)),dtype=float)
    for j,v in enumerate(vectors):
     ix=rng.integers(0,n,size=(m,n)); sample=v[ix]; means=sample.mean(axis=1); vars_=sample.var(axis=1,ddof=1)
     action_loss[:,j]=((means-target)**2-vars_/n)/(scale**2)
    if method=='action_MC_only': d=(action_loss[:,s0]-action_loss[:,m4]).mean(axis=1)
    else:
     ig=rng.integers(0,n_g,size=(m,n_g)); aa=s0[ig];bb=m4[ig];rr=np.arange(m)[:,None]
     d=(action_loss[rr,aa]-action_loss[rr,bb]).mean(axis=1)
   estimates.extend(d.tolist())
  vals=np.asarray(estimates); interval[method]={'low':float(np.quantile(vals,.025)),'high':float(np.quantile(vals,.975)),'half_width':float((np.quantile(vals,.975)-np.quantile(vals,.025))/2),'seed':seed,'replicates':boot_n,'unit':'paired G0; shared action-loss table' if method!='G0_only' else 'paired G0'}
 primary={'contrast':'loss(No-repair)-loss(Frozen M4), B=2, gamma=0; positive favors M4','mean':float(g0_d.mean()),'median':float(np.median(g0_d)),'better_m4':int((g0_d>1e-12).sum()),'worse_m4':int((g0_d< -1e-12).sum()),'tie':int((np.abs(g0_d)<=1e-12).sum()),'n_g0':n_g,'intervals_95':interval}
 opp=[]
 g0records=json.loads((a.private/'g0_records_private.json').read_text()) if (a.private/'g0_records_private.json').is_file() else []
 for r in g0records:
  rec0=r['record'];from collections import Counter
  kinds=Counter(e.get('kind') for e in rec0.get('attempted_events',[]) if e.get('acceptance_status')=='accepted')
  opp.append({'seed_id':r['seed_id'],'accepted_error_events':sum(kinds.values()),'error_type_counts':dict(kinds)})
 summary={'schema':'S5_INDEPENDENT_ANALYSIS_V1','run_id':rec['run_id'],'classification':'conditional external semisynthetic reconstruction; fixed one-DGP graph draws','primary':primary,'action_summary':[{'action':a,'mean':float(v.mean()),'sd':float(v.std(ddof=1)),'bias_corrected_loss':point_losses[i]} for i,(a,v) in enumerate(zip(actions,vectors))],'policy_budget_aggregates':aggregate,'opportunity_summary':{'n_g0_records':len(opp),'accepted_error_event_mean':float(np.mean([r['accepted_error_events'] for r in opp])) if opp else None,'accepted_error_event_median':float(np.median([r['accepted_error_events'] for r in opp])) if opp else None,'accepted_error_event_histogram':{str(k):sum(r['accepted_error_events']==k for r in opp) for k in sorted({r['accepted_error_events'] for r in opp})}},'recommendation_sha256':sha(a.private/'recommendation_manifest.json'),'response_sha256':[r['sha256'] for r in ev['action_records']],'policy_loss_table_sha256':sha(a.evaluator/'unit_policy_losses_private.json'),'evaluation_manifest_sha256':sha(a.evaluator/'evaluation_manifest.json'),'precision_targets':{'action_MC_halfwidth_max':.020,'two_source_halfwidth_max':.025,'action_MC_met':interval['action_MC_only']['half_width']<=.020,'two_source_met':interval['two_source']['half_width']<=.025}}
 a.output.mkdir(parents=True,exist_ok=False)
 (a.output/'summary.json').write_text(json.dumps(summary,sort_keys=True,indent=2,allow_nan=False)+'\n',encoding='utf-8')
 with (a.output/'policy_budget_aggregates.csv').open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=list(aggregate[0]));w.writeheader();w.writerows(aggregate)
 print(json.dumps({'primary':primary,'precision_targets':summary['precision_targets'],'policy_rows':len(rows),'aggregate_rows':len(aggregate)},sort_keys=True))
if __name__=='__main__':main()

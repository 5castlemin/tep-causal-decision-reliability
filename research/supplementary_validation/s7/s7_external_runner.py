"""Two-stage, locked S7 evaluation on official causalAssembly station tasks."""
from __future__ import annotations
import argparse, hashlib, json, math, os, subprocess, sys, time
from pathlib import Path

import networkx as nx
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
CONTRACT=HERE/'RESEARCH_S7_CONTRACT.json'
LOCK=HERE/'RESEARCH_S7_EXECUTION_LOCK.json'
SOURCE_COMMIT='8da3729e6383f0e1cbe7740bb6ab7ac4977ac7f9'
TASKS={'Station2':('Station2_mp_13','Station2_mp_33'),'Station3':('Station3_mp_43','Station3_mp_45')}
POLICIES=('S0','M1','M2','M3','M4','FULL_GREEDY','T5_GUIDED_M4','FULL_T_GUIDED_M4','RANDOM_M4','TYPE_RANKED_M4','GRAPH_FREE_ASSOCIATION','REFERENCE_GRAPH_LEARNER')
TYPE_ORDER=('REV','FN','UNRES','FP'); TOL=1e-12

def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def canon(x):return json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def write(path,obj):
 p=Path(path)
 if p.exists():raise FileExistsError(f'refusing overwrite: {p}')
 p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(json.dumps(obj,sort_keys=True,indent=2,allow_nan=False).encode()+b'\n')
def verify_lock(lock_path,lock_digest,contract_path,source_root):
 if sha(lock_path)!=lock_digest:raise ValueError('S7 lock hash mismatch')
 lock=json.loads(Path(lock_path).read_text(encoding='utf-8')); c=json.loads(Path(contract_path).read_text(encoding='utf-8'))
 if sha(contract_path)!=lock['contract_sha256']:raise ValueError('S7 contract digest mismatch')
 commit=subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD'],text=True).strip()
 if lock['execution_code_commit'] not in subprocess.check_output(['git','-C',str(ROOT),'rev-list','HEAD'],text=True).splitlines():raise ValueError('S7 execution revision is not in current ancestry')
 if subprocess.check_output(['git','-C',str(ROOT),'status','--porcelain'],text=True).strip():raise ValueError('S7 requires a clean checkout')
 for rel,digest in lock['code_sha256'].items():
  if sha(ROOT/rel)!=digest:raise ValueError(f'S7 code changed since lock: {rel}')
 src=Path(source_root)
 upstream=subprocess.check_output(['git','-C',str(src),'rev-parse','HEAD'],text=True).strip()
 if upstream!=SOURCE_COMMIT:raise ValueError('causalAssembly source commit mismatch')
 for rel,digest in lock['source_sha256'].items():
  if sha(src/rel)!=digest:raise ValueError(f'S7 pinned source asset changed: {rel}')
 return c,lock,commit
def load_source(source_root):
 root=Path(source_root).resolve()
 sys.path.insert(0,str(root))
 sys.modules.pop('causalAssembly',None)
 from causalAssembly import models_dag
 import causalAssembly
 if not Path(causalAssembly.__file__).resolve().is_relative_to(root):raise ValueError('causalAssembly import is not from pinned source checkout')
 ref=root/'data/ground_truth/ground_truth.json'; data=root/'data/data_sets/n_500_synthdata/assembly_line_500.csv'
 class LocalResponse:
  def __init__(self,text):self.text=text
 old_get,old_data=models_dag.requests.get,models_dag.DATA_DATASET
 models_dag.requests.get=lambda *_a,**_k:LocalResponse(ref.read_text(encoding='utf-8'))
 models_dag.DATA_DATASET=str(data)
 try: model=models_dag.ProductionLineGraph.get_ground_truth(); frame=models_dag.ProductionLineGraph.get_data()
 finally:models_dag.requests.get,models_dag.DATA_DATASET=old_get,old_data
 if not nx.is_directed_acyclic_graph(model.graph) or set(model.nodes)!=set(frame.columns):raise ValueError('official full graph and source data mismatch')
 if frame.isna().any().any() or not np.isfinite(frame.to_numpy(float)).all():raise ValueError('official source sample invalid')
 return model,frame
def fit_model(source_root,seed):
 from causalAssembly.drf_fitting import fit_drf
 from rpy2.robjects import r
 model,frame=load_source(source_root)
 r(f'set.seed({int(seed)})'); start=time.perf_counter(); model.drf=fit_drf(model,data=frame.loc[:,list(model.nodes)])
 secs=time.perf_counter()-start
 if set(model.drf)!=set(model.nodes):raise ValueError('full assembly DRF fit incomplete')
 return model,frame,secs
def task_metrics(graph,station,x,y):
 # Task pair is locked from the official station DAG; validate strict indirect status in full graph.
 if x==y or graph.has_edge(x,y) or not nx.has_path(graph,x,y):raise ValueError(f'locked task is not strict indirect: {station}')
 cut=graph.copy();cut.remove_edges_from(list(cut.out_edges(x)))
 backdoor=any(nx.has_path(cut,p,y) for p in graph.predecessors(x))
 return {'station':station,'action':x,'target':y,'shortest_directed_path_length':nx.shortest_path_length(graph,x,y),'full_graph_backdoor_support':bool(backdoor)}
def validate_locked_tasks(model):
 result={}
 for station in ('Station2','Station3'):
  local=getattr(model,station).graph; candidates=[]
  for x in sorted(local.nodes):
   for y in sorted(local.nodes):
    if x==y or local.has_edge(x,y) or not nx.has_path(local,x,y):continue
    details=task_metrics(model.graph,station,x,y)
    candidates.append((details['full_graph_backdoor_support'],details['shortest_directed_path_length'],x,y))
  if not candidates:raise ValueError(f'no strict-indirect task in {station}')
  chosen=sorted(candidates)[0]
  if (chosen[2],chosen[3])!=TASKS[station]:raise ValueError(f'locked task violates structural selection rule for {station}: {chosen}')
  result[station]={'strict_indirect_task_count':len(candidates),'selected_action':chosen[2],'selected_target':chosen[3],'shortest_path_length':chosen[1],'backdoor_support':chosen[0],'selection_rule':'minimize full-graph backdoor support, then directed station-local path length, then lexical X,Y'}
 return result
def graph_hash(pe,g):return pe.graph_hash(g)
def edges_from_policy(pe,p):
 g=pe.state([tuple(e) for e in p['final_edges']],unresolved=[tuple(e) for e in p.get('final_unresolved',[])])
 return g
def selected_action(train,nodes,edges,x,y,actions,target,scale):
 sys.path[:0]=[str(ROOT),str(ROOT/'src')]
 from integrated_pilot import fit_model as fit_graph
 from decision_mvp import static_mean_response
 arr=train.loc[:,nodes].to_numpy(float); m=fit_graph(arr,nodes,set(edges),1.0); mid=float(np.median(actions)); choices=[]
 for a in actions:
  pred=float(static_mean_response(m,x,float(a))[y]);loss=((pred-target)/scale)**2
  if not math.isfinite(loss):raise ValueError('nonfinite S7 predicted loss')
  choices.append((loss,abs(a-mid),a))
 return float(min(choices)[2])
def graph_free_action(train,x,y,actions,target,scale):
 sys.path[:0]=[str(ROOT),str(ROOT/'src')]
 from pilot_fit import fit_ridge
 xv=train[x].to_numpy(float);yv=train[y].to_numpy(float);mx,sx,my,sy=map(float,(xv.mean(),xv.std(ddof=0),yv.mean(),yv.std(ddof=0)))
 if min(sx,sy)<=0:raise ValueError('constant task variable')
 beta,intercept=fit_ridge(((xv-mx)/sx)[:,None],(yv-my)/sy,1.0);mid=float(np.median(actions))
 return float(min(((((intercept+beta[0]*((a-mx)/sx))*sy+my-target)/scale)**2,abs(a-mid),a) for a in actions)[2])
def custom_m4(pe,truth,g0,x,y,cfg,budget,kind):
 from research.within_task_repair_prioritization import s3_analysis as s3
 state=dict(g0);logs=[];initial=pe.metrics(truth,g0,x,y,cfg);pool=[e for e in pe.candidates(truth,g0,x,y,cfg) if e.metric=='M4']
 import random
 random_rng=random.Random(int.from_bytes(hashlib.sha256(f'S7-RANDOM-M4-v1|{x}|{y}'.encode()).digest()[:8],'big'))
 for _ in range(budget):
  edits=[e for e in pool if pe.dag(pe.apply(state,e))]
  if not edits:break
  if kind=='type':
   gains={e:s3.m4_gain(e,truth,state,initial,x,y,cfg) for e in edits};edits=[e for e in edits if gains[e]>TOL]
   if not edits:break
   chosen=None
   for typ in TYPE_ORDER:
    sub=[e for e in edits if e.kind==typ]
    if sub:
     best=max(gains[e] for e in sub); tied=[e for e in sub if best-gains[e]<=TOL]; chosen=min(tied,key=lambda e:(e.pair,e.operation));break
   if chosen is None:
    best=max(gains[e] for e in edits);chosen=min([e for e in edits if best-gains[e]<=TOL],key=lambda e:(e.pair,e.operation))
  else:
   chosen=edits[random_rng.randrange(len(edits))]
  state=pe.apply(state,chosen);logs.append(chosen);pool=[e for e in pool if e.key!=chosen.key]
 return state,logs
def make_g0(pe,truth,nodes,x,y,env,seedid,master):
 from research.original_objective.g0_candidate import corrupt_graph_candidate
 rec=corrupt_graph_candidate(truth,nodes=nodes,action=x,target=y,master_seed=int(master),task_id=f'S7-final-{env}-{seedid}',true_corruption_rate=.15,false_adjacency_rate=.05)
 ig=rec['initial_graph'];g=pe.state([tuple(e) for e in ig['edges']],unresolved=[tuple(e) for e in ig['unresolved']])
 if not pe.dag(g):raise ValueError('G0 cycle')
 return rec,g
def recommendation_stage(a,c,lock):
 from research.original_objective import policy_engine as pe
 from research.within_task_repair_prioritization import s3_analysis as s3
 from research.external_validation.semisynthetic_adapter.float_hard_do_adapter import sample_hard_do
 model,source,fitsecs=fit_model(a.source_root,c['fit_seed']);nodes=list(model.nodes);truth=pe.state([tuple(e) for e in model.graph.edges]);cfg=pe.Config(fp_rule='A',normalization='fixed_opportunity')
 task_selection=validate_locked_tasks(model)
 out=Path(a.private_root);out.mkdir(parents=True,exist_ok=False)
 model.random_state=np.random.default_rng(c['training_seed']);train=model.sample_from_drf(size=c['training_rows'],smoothed=True).loc[:,nodes]
 vals=train.to_numpy(float)
 if train.shape!=(c['training_rows'],len(nodes)) or not np.isfinite(vals).all():raise ValueError('invalid S7 training frame')
 train_path=out/'training.csv';train.to_csv(train_path,index=False,lineterminator='\n');trainhash=sha(train_path);trainnum=hashlib.sha256(vals.tobytes(order='C')).hexdigest()
 y_tasks={};
 for station,(x,y) in TASKS.items():
  target=float(train[y].mean()+train[y].std(ddof=1));scale=float(train[y].std(ddof=1));actions=np.quantile(train[x].to_numpy(float),[.1,.3,.5,.7,.9],method='linear').astype(float).tolist()
  if not scale>0 or len(set(actions))!=5:raise ValueError(f'invalid locked action/target for {station}')
  y_tasks[station]={'x':x,'y':y,'target':target,'scale':scale,'actions':actions}
 recs=[];g0_public=[]; learner_cache={};g0hashes={}
 for station,t in y_tasks.items():
  x,y=t['x'],t['y']; rows=[]
  for i in range(c['g0_count']):
   sid=c['g0_seed_start']+i; master=int.from_bytes(hashlib.sha256(f"{c['seed_namespace']}|{station}|{sid}".encode()).digest()[:4],'big')
   rec,g=make_g0(pe,truth,nodes,x,y,station,sid,master);gh=graph_hash(pe,g);g0hashes[f'{station}:{sid}']=gh;rows.append((sid,g,rec,gh))
   cand=[e for e in pe.candidates(truth,g,x,y,cfg) if e.metric=='M4'];legal=sum(pe.dag(pe.apply(g,e)) for e in cand)
   g0_public.append({'station':station,'g0_id':sid,'master_seed':master,'graph_sha256':gh,'realized_error_counts_by_metric':rec['realized_error_counts_by_metric'],'task_zone_pairs':rec['task_zone_pairs'],'initial_task_error_count':sum(rec['realized_error_counts_by_metric']['M4'].values()),'initial_m4_candidate_count':len(cand),'initial_legal_m4_candidate_count':legal})
  for sid,g0,grec,g0h in rows:
   trajectories={}
   for budget in range(5):
    cat=pe.run_catalog(truth,g0,x,y,budget,cfg); lookup={p['policy_id']:p for p in cat['strategies']+[cat['canonical_oracle']]}
    wanted={'S0':'S0','M1':'M1','M2':'M2','M3':'M3','M4':'M4','FULL_GREEDY':'M1+M2+M3+M4'}
    for pid,catalog_id in wanted.items():
     p=lookup[catalog_id];state=edges_from_policy(pe,p);trajectories[(pid,budget)]=(state,int(p['total_cost']),int(p['unused_budget']))
    for pid,metrics in [('T5_GUIDED_M4',('T5',)),('FULL_T_GUIDED_M4',s3.T)]:
     if budget==0:state=dict(g0);edits=[]
     else:state,edits=s3.greedy(truth,g0,x,y,cfg,metrics,budget)
     trajectories[(pid,budget)]=(state,len(edits),max(0,budget-len(edits)))
    for pid,kind in [('RANDOM_M4','random'),('TYPE_RANKED_M4','type')]:
     state,edits=custom_m4(pe,truth,g0,x,y,cfg,budget,kind);trajectories[(pid,budget)]=(state,len(edits),max(0,budget-len(edits)))
    trajectories[('GRAPH_FREE_ASSOCIATION',budget)]=(None,0,budget)
    trajectories[('REFERENCE_GRAPH_LEARNER',budget)]=(truth,0,budget)
   free=graph_free_action(train,x,y,t['actions'],t['target'],t['scale'])
   for (pid,b),(g,cost,unused) in trajectories.items():
    if g is None: action=free;gh='GRAPH_FREE'
    else:
     gh=graph_hash(pe,g)
     key=(station,gh)
     if key not in learner_cache:learner_cache[key]=selected_action(train,nodes,[e for e,v in g.items() if v!=pe.UNRES],x,y,t['actions'],t['target'],t['scale'])
     action=learner_cache[key]
    recs.append({'station':station,'g0_id':sid,'budget':b,'policy_id':pid,'g0_sha256':g0h,'recommended_graph_sha256':gh,'action':action,'edit_count':cost,'unused_budget':unused})
  if len(rows)!=c['g0_count']:raise ValueError('S7 G0 row count mismatch')
 expected=len(TASKS)*c['g0_count']*5*len(POLICIES)
 if len(recs)!=expected or len({(r['station'],r['g0_id'],r['budget'],r['policy_id']) for r in recs})!=expected:raise ValueError('S7 recommendation grid incomplete or duplicated')
 obj={'schema':'S7_SEALED_RECOMMENDATION_MANIFEST_V1','contract_sha256':sha(CONTRACT),'training_sha256':trainhash,'training_numeric_sha256':trainnum,'training_rows':len(train),'node_count':len(nodes),'full_graph_edges':model.graph.number_of_edges(),'task_settings':y_tasks,'g0_graph_hashes':g0hashes,'recommendations':recs,'recommendation_count':len(recs),'outcomes_read':False}
 digest=hashlib.sha256(canon(obj)).hexdigest();obj['content_sha256']=digest;write(out/'recommendations.json',obj)
 write(out/'generation_manifest.json',{'fit_seconds':fitsecs,'source_commit':SOURCE_COMMIT,'source_hashes':lock['source_sha256'],'full_nodes':nodes,'full_graph_edges':model.graph.number_of_edges(),'task_selection_diagnostics':task_selection,'training_csv_sha256':trainhash,'training_numeric_sha256':trainnum,'recommendation_sha256':sha(out/'recommendations.json'),'g0_count_per_station':c['g0_count'],'policy_budget_rows':len(recs),'policies':list(POLICIES),'g0_records':g0_public,'recommendations_sealed_before_sampling':True})
 print(json.dumps({'stage':'recommendation','g0_per_station':c['g0_count'],'recommendation_rows':len(recs),'fit_seconds':fitsecs,'recommendation_sha256':sha(out/'recommendations.json')},sort_keys=True))
def evaluation_stage(a,c,lock):
 from research.external_validation.semisynthetic_adapter.float_hard_do_adapter import sample_hard_do
 out=Path(a.private_root);recpath=out/'recommendations.json';rec=json.loads(recpath.read_text(encoding='utf-8'))
 if rec.get('content_sha256')!=sha_value(rec):raise ValueError('sealed recommendation digest mismatch')
 if rec.get('content_sha256')!=hashlib.sha256(canon({k:v for k,v in rec.items() if k!='content_sha256'})).hexdigest() or rec['outcomes_read'] is not False:raise ValueError('recommendation content seal invalid')
 model,source,fitsecs=fit_model(a.source_root,c['fit_seed']);nodes=list(model.nodes);train=pd.read_csv(out/'training.csv')
 if sha(out/'training.csv')!=rec['training_sha256'] or list(train.columns)!=nodes or len(train)!=c['training_rows']:raise ValueError('locked training frame mismatch')
 if hashlib.sha256(train.to_numpy(float).tobytes(order='C')).hexdigest()!=rec['training_numeric_sha256']:raise ValueError('training numeric digest mismatch')
 evaldir=out/'response_vectors';evaldir.mkdir(exist_ok=False); losses={};action_meta={}
 for station,t in rec['task_settings'].items():
  for ai,action in enumerate(t['actions']):
   seed=int.from_bytes(hashlib.sha256(f"{c['seed_namespace']}|response|{station}|{ai}".encode()).digest()[:4],'big')
   frame=sample_hard_do(model,t['x'],float(action),size=c['response_rows_per_action'],rng=np.random.default_rng(seed),smoothed=True)
   yv=frame[t['y']].to_numpy(float)
   if len(yv)!=c['response_rows_per_action'] or not np.isfinite(yv).all() or not np.all(frame[t['x']].to_numpy(float)==float(action)):raise ValueError('S7 hard-do response validation failed')
   f=evaldir/f'{station}_action_{ai:02d}.npy'
   with f.open('xb') as s:np.save(s,yv,allow_pickle=False)
   loss=float(((yv.mean()-t['target'])**2-yv.var(ddof=1)/len(yv))/(t['scale']**2));losses[(station,float(action))]=loss
   action_meta[f'{station}:{ai}']={'seed':seed,'rows':len(yv),'sha256':sha(f),'mean':float(yv.mean()),'variance':float(yv.var(ddof=1)),'bias_corrected_loss':loss}
 recs=rec['recommendations']; unit=[]
 for row in recs:
  unit.append({**row,'loss':losses[(row['station'],float(row['action']))]})
 write(evaldir/'unit_policy_losses_private.json',unit)
 agg=[];by={}
 for station in rec['task_settings']:
  srows=[r for r in unit if r['station']==station]
  for b in range(5):
   for p in POLICIES:
    rr=[r for r in srows if r['budget']==b and r['policy_id']==p];arr=np.asarray([r['loss'] for r in rr]);ed=np.asarray([r['edit_count'] for r in rr]);unused=np.asarray([r['unused_budget'] for r in rr])
    agg.append({'station':station,'n_g0':len(rr),'budget':b,'policy_id':p,'mean_loss':float(arr.mean()),'median_loss':float(np.median(arr)),'mean_edit_count':float(ed.mean()),'mean_unused_budget':float(unused.mean()),'no_op_rate':float((ed==0).mean())})
 contrasts=[];unc=[];bootstrap(c,rec,unit,losses,evaldir,contrasts,unc)
 g0manifest=json.loads((out/'generation_manifest.json').read_text(encoding='utf-8'));opportunity=[]
 for station in rec['task_settings']:
  gr=[r for r in g0manifest['g0_records'] if r['station']==station];ks=np.asarray([r['initial_legal_m4_candidate_count'] for r in gr]);errs=np.asarray([r['initial_task_error_count'] for r in gr])
  opportunity.append({'station':station,'n_g0':len(gr),'mean_initial_task_errors':float(errs.mean()),'mean_initial_legal_m4_candidates':float(ks.mean()),'k0':int((ks==0).sum()),'k1':int((ks==1).sum()),'k_ge_2':int((ks>=2).sum()),'k_gt_b1':int((ks>1).sum()),'k_gt_b2':int((ks>2).sum()),'k_gt_b3':int((ks>3).sum()),'k_gt_b4':int((ks>4).sum()),'recommendation_action_disagreement_g0_budget2':sum(len({r['action'] for r in unit if r['station']==station and r['g0_id']==sid and r['budget']==2})>1 for sid in {r['g0_id'] for r in unit if r['station']==station})})
 write(Path(a.public_output)/'environment_policy_budget_aggregates.csv',agg)
 write(Path(a.public_output)/'environment_paired_contrasts.csv',contrasts)
 write(Path(a.public_output)/'environment_uncertainty.csv',unc)
 write(Path(a.public_output)/'environment_opportunity_summary.csv',opportunity)
 write(Path(a.public_output)/'execution_manifest.json',{'schema':'S7_PUBLIC_EXECUTION_MANIFEST_V1','run_id':c['run_id'],'classification':c['classification'],'execution_code_commit':lock['execution_code_commit'],'source_commit':SOURCE_COMMIT,'contract_sha256':sha(CONTRACT),'recommendation_sha256':sha(recpath),'training_sha256':rec['training_sha256'],'response_rows_per_station':5*c['response_rows_per_action'],'total_response_rows':len(rec['task_settings'])*5*c['response_rows_per_action'],'g0_draws_per_station':c['g0_count'],'action_response_hashes':action_meta,'fit_seconds_evaluation_refit':fitsecs,'intervals':'G0-only, action-MC-only, two-source percentile paired 95% pointwise; common indices/shared action table'})
 print(json.dumps({'stage':'evaluation','total_response_rows':len(rec['task_settings'])*5*c['response_rows_per_action'],'public_aggregate_rows':len(agg),'resource_limits':c['resource_limits']},sort_keys=True))
def sha_value(obj):return hashlib.sha256(canon({k:v for k,v in obj.items() if k!='content_sha256'})).hexdigest()
def bootstrap(c,rec,unit,base_losses,outdir,contrasts,unc):
 rng=np.random.default_rng(c['bootstrap_seed']);B=c['bootstrap_replicates']; chunk=100
 policies=[('S0','M4','S0_MINUS_M4'),('M4','FULL_GREEDY','M4_MINUS_FULL_GREEDY'),('M4','GRAPH_FREE_ASSOCIATION','M4_MINUS_GRAPH_FREE'),('T5_GUIDED_M4','M4','T5_MINUS_M4'),('FULL_T_GUIDED_M4','M4','FULL_T_MINUS_M4')]
 for station in rec['task_settings']:
  rows=[r for r in unit if r['station']==station]
  ids=sorted({r['g0_id'] for r in rows}); actions=rec['task_settings'][station]['actions']; aidx={float(a):i for i,a in enumerate(actions)}
  n=len(ids); common_g0_ix=rng.integers(0,n,size=(B,n)); two_g0_ix=np.empty((B,n),dtype=np.int32)
  y_arrays=[np.load(outdir/'response_vectors'/f'{station}_action_{i:02d}.npy',allow_pickle=False) for i in range(5)]
  shared_loss=np.empty((B,5),dtype=float)
  for st in range(0,B,chunk):
   m=min(chunk,B-st); two_g0_ix[st:st+m]=rng.integers(0,n,size=(m,n))
   for j,yv in enumerate(y_arrays):
    ix=rng.integers(0,len(yv),size=(m,len(yv)));sample=yv[ix];means=sample.mean(axis=1);vars=sample.var(axis=1,ddof=1);target=rec['task_settings'][station]['target'];scale=rec['task_settings'][station]['scale'];shared_loss[st:st+m,j]=((means-target)**2-vars/len(yv))/(scale**2)
  for b in range(5):
   by={(r['g0_id'],r['policy_id']):r for r in rows if r['budget']==b}
   for lp,rp,label in policies:
    left=np.asarray([aidx[float(by[(sid,lp)]['action'])] for sid in ids]);right=np.asarray([aidx[float(by[(sid,rp)]['action'])] for sid in ids])
    d0=np.asarray([base_losses[(station,float(by[(sid,lp)]['action']))]-base_losses[(station,float(by[(sid,rp)]['action']))] for sid in ids]);boot0=d0[common_g0_ix].mean(axis=1)
    contrasts.append({'station':station,'budget':b,'contrast':label,'left_policy':lp,'right_policy':rp,'estimand':'mean loss(left)-loss(right)','mean_difference':float(d0.mean()),'median_difference':float(np.median(d0)),'left_better_count':int((d0< -1e-12).sum()),'right_better_count':int((d0>1e-12).sum()),'tie':int((np.abs(d0)<=1e-12).sum()),'m4_better_count':int((d0>1e-12).sum()) if label=='S0_MINUS_M4' else None,'g0_only_ci95_low':float(np.quantile(boot0,.025)),'g0_only_ci95_high':float(np.quantile(boot0,.975)),'bootstrap_replicates':B,'interval_type':'pointwise'})
    mc=(shared_loss[:,left]-shared_loss[:,right]).mean(axis=1);rr=np.arange(B)[:,None]
    two=(shared_loss[rr,left[two_g0_ix]]-shared_loss[rr,right[two_g0_ix]]).mean(axis=1)
    unc.append({'station':station,'budget':b,'contrast':label,'action_mc_ci95_low':float(np.quantile(mc,.025)),'action_mc_ci95_high':float(np.quantile(mc,.975)),'two_source_ci95_low':float(np.quantile(two,.025)),'two_source_ci95_high':float(np.quantile(two,.975)),'bootstrap_replicates':B,'bootstrap_seed':c['bootstrap_seed'],'interval_type':'pointwise','shared_action_table_per_replicate':True,'common_g0_and_action_indices_across_contrasts':True})
def main():
 p=argparse.ArgumentParser();p.add_argument('--stage',choices=['recommendation','evaluation'],required=True);p.add_argument('--lock-sha256',required=True);p.add_argument('--source-root',type=Path,required=True);p.add_argument('--private-root',type=Path,required=True);p.add_argument('--public-output',type=Path,required=True);a=p.parse_args()
 c,lock,_=verify_lock(LOCK,a.lock_sha256,CONTRACT,a.source_root)
 if a.stage=='recommendation':recommendation_stage(a,c,lock)
 else:evaluation_stage(a,c,lock)
if __name__=='__main__':main()

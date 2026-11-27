"""Post-hoc S3 analysis on hash-verified Research C inputs; never writes source data."""
from __future__ import annotations

import csv, hashlib, itertools, json, os, sqlite3, sys, time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "src")]
from research.budget_aware_refinement.step4c1_scm import generate_scm_parameters, generate_observations
from research.budget_aware_refinement.step3_adapter import prepare, evaluate
from research.budget_aware_refinement.step4c1_gt import analytic_response
from research.original_objective import policy_engine as pe
from integrated_pilot import fit_model
from decision_mvp import static_mean_response

DATA = Path(os.environ.get("DAT_RESEARCH_ROOT", "C:/DAT_RESEARCH"))
OUT = Path(__file__).resolve().parent / "outputs_v6"
EXPECTED = {
 "C_DEVELOPMENT:cohort": "dd4264d5085adbabe9510bf99b564ec6c2b33e35d4eeb346a079cc4ccfb9b716",
 "C_DEVELOPMENT:proposals": "1d00d1790788c342e15a81a0c405768e5e2a3e46ee75c57c0bbe34f8c0fcb584",
 "C_HELDOUT:cohort": "37b3c265ecb65b09a97eda91d29411844c3a3851c9fbff6cfa06445f919a3eba",
 "C_HELDOUT:proposals": "59f1abcf5661a5b3d0658d0db0f7e6afe601ebd09997035228df0716800538d6",
}
SOURCES = [
 ("C_DEVELOPMENT", DATA/"research-c/development/development-20261123-seed-2026112301-v1/research_c_cohort.sqlite", DATA/"research-c/development/development-20261123-seed-2026112301-v1/research_c_proposal_stage.sqlite"),
 ("C_HELDOUT", DATA/"research-c/heldout/independent-evaluation-20261123-seed-2026112303-v1/research_c_cohort.sqlite", DATA/"research-c/heldout/independent-evaluation-20261123-seed-2026112303-v1/research_c_proposal_stage.sqlite"),
]
T = tuple(f"T{i}" for i in range(1, 7))
SETS = tuple(s for n in range(1, 7) for s in itertools.combinations(T, n))
BOOT_N, BOOT_SEED = 10_000, 2026112701
GAIN_TOL = 1e-12
LOOKAHEAD_SETS = tuple((t,) for t in T) + (T,) + tuple((a,b) for a,b in (("T3","T4"),("T3","T5"),("T3","T6"),("T4","T5"),("T4","T6"),("T5","T6")))

def sha(path: Path) -> str:
 h=hashlib.sha256()
 with path.open("rb") as f:
  for b in iter(lambda:f.read(1<<20),b""): h.update(b)
 return h.hexdigest()

def cfg_from(payload):
 c=dict(payload['config']['repair_config']); c['costs']=tuple(tuple(x) for x in c['costs']); c['beta']=tuple(c['beta']); c['weights']=tuple(c['weights']); c['route_relevant_fp']=tuple(tuple(x) for x in c['route_relevant_fp']); return pe.Config(**c)

def ancestors(g, nodes):
 edges=[e for e in g.values() if e != pe.UNRES]; out={n:set() for n in (set(nodes)|{z for e in edges for z in e})}
 for a,b in edges:
  out[a].add(b)
 # Compute reachability over every directed graph node. The `nodes` argument
 # only adds isolated task nodes; it never truncates traversal intermediates.
 for source in out:
  frontier=list(out[source])
  while frontier:
   nxt=frontier.pop()
   for child in out[nxt]:
    if child not in out[source]:
     out[source].add(child); frontier.append(child)
 return out

def path_edges(g, x, y):
 edges={e for e in g.values() if e != pe.UNRES}
 res=set()
 def dfs(node, seen, path):
  if node==y:
   res.update(zip(path,path[1:])); return
  for a,b in sorted(edges):
   if a==node and b not in seen: dfs(b,seen|{b},path+[b])
 dfs(x,{x},[x]); return res

def structural_sets(truth, action, target, config):
 zone,nodes=pe.task_zone(truth,action,target); nodes=sorted(nodes)
 # Directed causal paths and open, unconditioned backdoor paths are derived from the frozen task-zone definition.
 p_edges=path_edges(truth,action,target)
 edges={e for e in truth.values() if e != pe.UNRES}
 adj={n:set() for n in {z for e in edges for z in e}}
 for a,b in edges: adj[a].add(b); adj[b].add(a)
 bd=set()
 def visit(path):
  u=path[-1]
  if u==target:
   if len(path)>1 and (path[1],action) in edges and all(not ((path[i-1],path[i]) in edges and (path[i+1],path[i]) in edges) for i in range(1,len(path)-1)):
    bd.update((a,b) if (a,b) in edges else (b,a) for a,b in zip(path,path[1:]))
   return
  for v in sorted(adj.get(u,set())-set(path)): visit(path+[v])
 visit([action])
 return nodes, zone, p_edges, bd

def f1(tp, pred, ref):
 den=len(pred)+len(ref)
 return (2*len(tp)/den) if den else 0.0

def q_metrics(g, context):
 truth,action,target,nodes,zone,pedges,bdes=context
 universe=set(itertools.combinations(nodes,2))
 t_adj={p for p in universe if p in truth}
 p_adj={p for p in universe if p in g}
 tp_adj=t_adj&p_adj
 t1=f1(tp_adj,p_adj,t_adj)
 # Direction score over fixed task-zone pair universe; unresolved is present but never a correct orientation.
 trued={(a,b) for a,b in truth.values() if pe.pair(a,b) in universe}
 pred={e for e in g.values() if e != pe.UNRES and pe.pair(*e) in universe}
 t2=f1(trued&pred,pred,trued)
 directed={e for e in g.values() if e != pe.UNRES}
 t3=len(pedges&directed)/len(pedges) if pedges else 0.0
 gnodes={z for e in g.values() if e != pe.UNRES for z in e}
 t4=float(target in ancestors(g,gnodes|{action,target}).get(action,set()))
 refanc=ancestors(truth,nodes); predanc=ancestors(g,nodes)
 allanc={(a,b) for a in nodes for b in nodes if a!=b and b in refanc[a]}
 gotanc={(a,b) for a in nodes for b in nodes if a!=b and b in predanc[a]}
 t5=f1(allanc&gotanc,gotanc,allanc)
 t6=len(bdes&directed)/len(bdes) if bdes else 0.0
 return dict(zip(T,(t1,t2,t3,t4,t5,t6)))

def direct_task_edit(e, truth, g, action,target,config):
 before=pe.metrics(truth,g,action,target,config); trial=pe.apply(g,e)
 after=pe.metrics(truth,trial,action,target,config)
 return before['events'].get(e.pair)==(e.metric,e.kind) and e.pair not in after['events']

def m4_gain(e, truth,g,initial,action,target,config):
 before=pe.metrics(truth,g,action,target,config); after=pe.metrics(truth,pe.apply(g,e),action,target,config)
 return pe.burden(before,initial,('M4',),config)-pe.burden(after,initial,('M4',),config)

def select_greedy_option(options, costs):
 """Select by T gain/cost, then M4 gain/cost, then canonical IDs.

 `options` rows are (edit, resulting_graph, T_gain, M4_gain). Tolerance is
 absolute in normalized gain-per-cost units and fixed by GAIN_TOL.
 """
 eligible=[r for r in options if r[2]>GAIN_TOL or r[3]>GAIN_TOL]
 if not eligible: return None
 best_t=max(r[2]/costs[r[0].operation] for r in eligible)
 tied=[r for r in eligible if abs(r[2]/costs[r[0].operation]-best_t)<=GAIN_TOL]
 best_m=max(r[3]/costs[r[0].operation] for r in tied)
 tied=[r for r in tied if abs(r[3]/costs[r[0].operation]-best_m)<=GAIN_TOL]
 return min(tied,key=lambda r:(pe.METRICS.index(r[0].metric),r[0].pair,r[0].operation))

def greedy(truth,g0,action,target,config,metric_set,budget,initial=None):
 initial=initial or pe.metrics(truth,g0,action,target,config); g=dict(g0); pool=[e for e in pe.candidates(truth,g0,action,target,config) if e.metric=='M4']; log=[]
 for _ in range(budget):
  options=[]
  for e in pool:
   if not direct_task_edit(e,truth,g,action,target,config): continue
   trial=pe.apply(g,e)
   if not pe.dag(trial): continue
   before=q_metrics(g,(truth,action,target,*structural_sets(truth,action,target,config)))
   after=q_metrics(trial,(truth,action,target,*structural_sets(truth,action,target,config)))
   qgain=sum(after[t]-before[t] for t in metric_set)/len(metric_set)
   mgain=m4_gain(e,truth,g,initial,action,target,config)
   options.append((e,trial,qgain,mgain))
  if not options: break
  selected=select_greedy_option(options,dict(config.costs))
  if selected is None: break
  e,trial,qgain,mgain=selected
  log.append({'kind':e.kind,'pair':list(e.pair),'operation':e.operation,'q_gain':qgain,'m4_gain':mgain,'fallback':False,'before_hash':pe.graph_hash(g),'after_hash':pe.graph_hash(trial)})
  g=trial; pool=[x for x in pool if x.key!=e.key]
 return g,log

def sequence2(truth,g0,action,target,config,metric_set):
 initial=pe.metrics(truth,g0,action,target,config); pool=[e for e in pe.candidates(truth,g0,action,target,config) if e.metric=='M4']; ctx=(truth,action,target,*structural_sets(truth,action,target,config)); q0=sum(q_metrics(g0,ctx)[t] for t in metric_set)/len(metric_set); seqs=[]
 for e1 in pool:
  g1=pe.apply(g0,e1)
  if not pe.dag(g1) or not direct_task_edit(e1,truth,g0,action,target,config): continue
  for e2 in pool:
   if e2.key==e1.key or not direct_task_edit(e2,truth,g1,action,target,config): continue
   g2=pe.apply(g1,e2)
   if not pe.dag(g2): continue
   q2=sum(q_metrics(g2,ctx)[t] for t in metric_set)/len(metric_set)
   gain=(q2-q0)/2
   seqs.append((gain,e1,e2,g1,g2))
 if not seqs:
  # No legal two-edit sequence: use the exact same one-step T/M4/canonical
  # selector as greedy for this metric subset.
  sg,slog=greedy(truth,g0,action,target,config,metric_set,1,initial)
  if not slog: return None
  pair=tuple(slog[0]['pair']); operation=slog[0]['operation']
  e=next(e for e in pool if e.pair==pair and e.operation==operation)
  return (0.0,e,None,sg,sg)
 # If no two-step sequence improves the selected structural potential, fallback ranks the full sequence by the frozen M4 gain before canonical IDs.
 fallback=not any(r[0]>GAIN_TOL for r in seqs)
 def key(r):
  mg1=m4_gain(r[1],truth,g0,initial,action,target,config)
  mg2=m4_gain(r[2],truth,r[3],initial,action,target,config)
  return (-(mg1+mg2 if fallback else r[0]),-mg1,r[1].pair,r[2].pair)
 seqs.sort(key=key)
 # Prefer the shortest improving sequence, then its per-edit T gain, existing
 # M4 gain, and canonical sequence order. A positive two-step sequence may
 # start with a zero-gain edit when the cumulative gain is positive.
 improving=[r for r in seqs if r[0]>GAIN_TOL]
 if improving:
  improving.sort(key=lambda r:(-2,-r[0],-(m4_gain(r[1],truth,g0,initial,action,target,config)+m4_gain(r[2],truth,r[3],initial,action,target,config)),r[1].pair,r[1].operation,r[2].pair,r[2].operation))
  return improving[0]
 seqs.sort(key=lambda r:(-2,-(m4_gain(r[1],truth,g0,initial,action,target,config)+m4_gain(r[2],truth,r[3],initial,action,target,config)),-m4_gain(r[1],truth,g0,initial,action,target,config),r[1].pair,r[1].operation,r[2].pair,r[2].operation))
 return seqs[0]

def load_cohort(cohort, cp, pp):
 actual={'cohort':sha(cp),'proposals':sha(pp)}
 assert actual['cohort']==EXPECTED[f'{cohort}:cohort'] and actual['proposals']==EXPECTED[f'{cohort}:proposals'],(cohort,actual)
 con=sqlite3.connect(f'file:{cp}?mode=ro',uri=True); con.execute('pragma query_only=on')
 prop=sqlite3.connect(f'file:{pp}?mode=ro',uri=True); prop.execute('pragma query_only=on')
 props={}
 for raw, in prop.execute("select proposal_json from proposal_attempts where status='ELIGIBLE'"):
  p=json.loads(raw); props[p['scm_id']]=p
 rows=[]
 for sid,status,raw in con.execute('select scm_id,status,result_json from scms order by ordinal'):
  assert status=='COMPLETED' and sid in props
  payload=json.loads(raw)['payload']; proposal=props[sid]
  scm=generate_scm_parameters(proposal); obs=generate_observations(proposal,scm); bind=payload['input_binding']
  assert scm['equation_signature_sha256']==bind['truth_spec_sha256'] and obs['data_sha256']==bind['observations_sha256']
  assert (proposal['action'],proposal['target'])==(bind['action'],bind['target'])
  truth=pe.state([tuple(e) for e in scm['truth_spec']['edges']]); initj=payload['g0_generation']['initial_graph']; g0=pe.state([tuple(e) for e in initj['edges']],unresolved=[tuple(e) for e in initj['unresolved']]); config=cfg_from(payload)
  assert pe.graph_hash(g0)==bind['initial_structural_graph_sha256']
  rows.append((sid,proposal,payload,scm,obs,truth,g0,config))
 con.close();prop.close()
 assert sha(cp)==actual['cohort'] and sha(pp)==actual['proposals']
 return actual,rows

def main():
 if OUT.exists() and any(OUT.iterdir()): raise FileExistsError(f"Refusing to overwrite {OUT}")
 OUT.mkdir(parents=True,exist_ok=True)
 start=time.perf_counter(); provenance={}; aggregate=[]; unit_private=[]; phase1=[]; candidate_private=[]; role_counts=[]
 for cohort,cp,pp in SOURCES:
  hashes,rows=load_cohort(cohort,cp,pp); provenance[cohort]=hashes
  # Validate frozen C trajectories before evaluating S3 policies.
  for sid,proposal,payload,scm,obs,truth,g0,cfg in rows:
   oldbud=payload['e2e_result']['budgets']
   for b in range(5):
    saved=oldbud[b]['policies']
    for pid,subset,canon in [('S0',(),False),('M4',('M4',),False),('M1+M2+M3+M4',pe.METRICS,False)]:
     got=pe.run(truth,g0,proposal['action'],proposal['target'],b,subset,cfg,canonical=canon)
     old=next(x for x in saved if x['policy_id']==pid)
     assert got['final_hash']==old['final_graph_sha256'] and json.dumps(got['edits'],sort_keys=True)==json.dumps(old['edit_log'],sort_keys=True)
   initial=pe.metrics(truth,g0,proposal['action'],proposal['target'],cfg); candidates=[e for e in pe.candidates(truth,g0,proposal['action'],proposal['target'],cfg) if e.metric=='M4']
   feasible=[e for e in candidates if pe.dag(pe.apply(g0,e))]
   phase1.append({'cohort':cohort,'scm':sid,'m4_candidates':len(candidates),'m4_feasible':len(feasible),'kinds':','.join(sorted(e.kind for e in feasible))})
   ctx=(truth,proposal['action'],proposal['target'],*structural_sets(truth,proposal['action'],proposal['target'],cfg))
   # Reference result for all policies is calculated from the exact existing observations and analytic truth response.
   cache={}
   def get_loss(g):
    h=pe.graph_hash(g)
    if h not in cache:
     req={'node_ids':proposal['nodes'],'action':proposal['action'],'target':proposal['target']}
     _,sel=prepare(req,np.asarray(obs['rows'],dtype=np.float64),proposal['nodes'],proposal['nodes'],payload['input_binding']['delta'],fit_model,static_mean_response,graph_result={'final_graph':[list(e) for e in sorted(x for x in g.values() if x!=pe.UNRES)]})
     ev=evaluate(sel,scm['truth_spec'],analytic_response)
     selected=float(next(r['action'] for r in sel['candidates'] if r['k']==sel['selected_k']))
     cache[h]=(float(ev['regret']),selected)
    return cache[h]
   base_loss,base_action=get_loss(g0)
   for b in (0,2):
    for pid,subset in [('S0',()),('M4',('M4',)),('M1+M2+M3+M4',pe.METRICS)]:
     rr=pe.run(truth,g0,proposal['action'],proposal['target'],b,subset,cfg)
     old=next(x for x in oldbud[b]['policies'] if x['policy_id']==pid)
     loss,action=get_loss(pe.state(rr['final_edges'],unresolved=rr['final_unresolved']))
     assert action==float(old['evaluation']['selected_action']) and abs(loss-float(old['evaluation']['regret']))<1e-12,(cohort,sid,pid,b,'action/regret reproduction')
   for b in (1,2,3,4):
    oldm4=pe.run(truth,g0,proposal['action'],proposal['target'],b,('M4',),cfg); oldloss,oldaction=get_loss(pe.state(oldm4['final_edges'],unresolved=oldm4['final_unresolved']))
    unit_private.append({'cohort':cohort,'scm':sid,'policy':'M4_ORIGINAL','budget':b,'loss':oldloss,'cost':oldm4['total_cost'],'action':oldaction,'same_as_s0':oldaction==base_action,'graph_hash':oldm4['final_hash'],'edits':len(oldm4['edits']),'first_edit':json.dumps([oldm4['edits'][0]['pair'],oldm4['edits'][0]['operation']]) if oldm4['edits'] else None,'fallbacks':0})
    for combo in SETS:
     g,log=greedy(truth,g0,proposal['action'],proposal['target'],cfg,combo,b)
     loss,action=get_loss(g)
     rec={'cohort':cohort,'scm':sid,'policy':'+'.join(combo),'budget':b,'loss':loss,'cost':len(log),'action':action,'same_as_s0':action==base_action,'graph_hash':pe.graph_hash(g),'edits':len(log),'first_edit':json.dumps([log[0]['pair'],log[0]['operation']]) if log else None,'fallbacks':sum(x['fallback'] for x in log)}
     unit_private.append(rec)
   # Lookahead prioritization subset selected before outcome use: T4, T3+T4; compare B2 trajectory.
   for combo in LOOKAHEAD_SETS:
    choice=sequence2(truth,g0,proposal['action'],proposal['target'],cfg,combo)
    if choice is None: lg=g0; llog=[]
    else:
     _,e1,e2,g1,g2=choice; lg=g2; llog=[e1]+([e2] if e2 is not None else [])
    lloss,lact=get_loss(lg)
    g1,grlog=greedy(truth,g0,proposal['action'],proposal['target'],cfg,combo,2)
    gloss,gact=get_loss(g1)
    unit_private.append({'cohort':cohort,'scm':sid,'policy':'+'.join(combo)+'_LOOKAHEAD2','budget':2,'loss':lloss,'cost':len(llog),'action':lact,'same_as_s0':lact==base_action,'graph_hash':pe.graph_hash(lg),'edits':len(llog),'first_edit':json.dumps([list(llog[0].pair),llog[0].operation]) if llog else None,'fallbacks':0})
    unit_private.append({'cohort':cohort,'scm':sid,'policy':'+'.join(combo)+'_GREEDY2','budget':2,'loss':gloss,'cost':len(grlog),'action':gact,'same_as_s0':gact==base_action,'graph_hash':pe.graph_hash(g1),'edits':len(grlog),'first_edit':json.dumps([grlog[0]['pair'],grlog[0]['operation']]) if grlog else None,'fallbacks':sum(x['fallback'] for x in grlog)})
   # One-edit value heterogeneity. Per-candidate rows remain in memory; public file is cohort-level aggregate only.
   vals=[]; _,zone,pedges,bdes=structural_sets(truth,proposal['action'],proposal['target'],cfg)
   for e in feasible:
    trial=pe.apply(g0,e); rr,aa=get_loss(trial); vals.append({'kind':e.kind,'pair':list(e.pair),'regret_gain':base_loss-rr,'action_changed':aa!=base_action,'metric':e.metric})
    pair=pe.pair(*e.pair); onpath=pair in {pe.pair(*x) for x in pedges}; onbd=pair in {pe.pair(*x) for x in bdes}
    role=('path_and_backdoor' if onpath and onbd else 'path' if onpath else 'backdoor' if onbd else 'other_task_fp' if e.kind=='FP' else 'other_task')
    candidate_private.append({'cohort':cohort,'scm':sid,'kind':e.kind,'role':role,'pair':list(pair),'m4_gain':m4_gain(e,truth,g0,initial,proposal['action'],proposal['target'],cfg),'regret_gain':base_loss-rr,'action_changed':aa!=base_action})
    role_counts.append({'cohort':cohort,'scm':sid,'kind':e.kind,'role':role})
   if feasible:
    single=[get_loss(pe.apply(g0,e)) for e in feasible]
    exp_loss=float(np.mean([x[0] for x in single])); stay=float(np.mean([x[1]==base_action for x in single]))
    unit_private.append({'cohort':cohort,'scm':sid,'policy':'M4_RANDOM_EXPECTATION','budget':1,'loss':exp_loss,'cost':1.0,'action':float('nan'),'same_as_s0':stay,'graph_hash':'expected_over_single_edit_candidates','edits':1,'fallbacks':0})
   else:
    unit_private.append({'cohort':cohort,'scm':sid,'policy':'M4_RANDOM_EXPECTATION','budget':1,'loss':base_loss,'cost':0.0,'action':base_action,'same_as_s0':1.0,'graph_hash':pe.graph_hash(g0),'edits':0,'fallbacks':0})
   phase1[-1]['loss_gain_min']=min((v['regret_gain'] for v in vals),default=None); phase1[-1]['loss_gain_max']=max((v['regret_gain'] for v in vals),default=None)
   phase1[-1]['positive_candidate_count']=sum(v['regret_gain']>1e-12 for v in vals); phase1[-1]['negative_candidate_count']=sum(v['regret_gain']<-1e-12 for v in vals)
  # aggregate completed rows; no unit-level data are written publicly.
  keys=sorted({(x['policy'],x['budget']) for x in unit_private if x['cohort']==cohort})
  for pid,b in keys:
   rs=[x for x in unit_private if x['cohort']==cohort and x['policy']==pid and x['budget']==b]
   m4={x['scm']:x for x in unit_private if x['cohort']==cohort and x['policy']=='M4_ORIGINAL' and x['budget']==b}
   comparable=[x for x in rs if x.get('first_edit') is not None and x['scm'] in m4 and m4[x['scm']].get('first_edit') is not None]
   aggregate.append({'cohort':cohort,'policy':pid,'budget':b,'n':len(rs),'mean_regret':float(np.mean([x['loss'] for x in rs])),'median_regret':float(np.median([x['loss'] for x in rs])),'mean_edit_count':float(np.mean([x['cost'] for x in rs])),'action_change_rate':float(1-np.mean([x['same_as_s0'] for x in rs])),'first_edit_diff_vs_m4_rate':float(np.mean([x['first_edit']!=m4[x['scm']]['first_edit'] for x in comparable])) if comparable else None,'unique_final_graphs':len({x['graph_hash'] for x in rs}),'mean_fallbacks':float(np.mean([x['fallbacks'] for x in rs]))})
 # Common-index paired SCM bootstrap over the primary cohort-specific rows.
 rng=np.random.default_rng(BOOT_SEED); intervals=[]
 for cohort,_,_ in SOURCES:
  ids=sorted({x['scm'] for x in unit_private if x['cohort']==cohort})
  index=rng.integers(0,len(ids),size=(BOOT_N,len(ids)))
  lookup={(x['policy'],x['budget'],x['scm']):x for x in unit_private if x['cohort']==cohort}
  contrasts=[('M4_ORIGINAL','M4_RANDOM_EXPECTATION',1),('T3','M4_ORIGINAL',1),('T1+T2+T3+T4+T5+T6','M4_ORIGINAL',1)]+[('+'.join(s)+'_LOOKAHEAD2','+'.join(s)+'_GREEDY2',2) for s in LOOKAHEAD_SETS]
  for a,b,bdgt in contrasts:
   av=np.array([lookup[(a,bdgt,i)]['loss'] for i in ids]); bv=np.array([lookup[(b,bdgt,i)]['loss'] for i in ids]); d=av-bv
   draws=d[index].mean(axis=1); intervals.append({'cohort':cohort,'contrast':f'{a} - {b}','budget':bdgt,'mean_difference':float(d.mean()),'ci95_low':float(np.quantile(draws,.025)),'ci95_high':float(np.quantile(draws,.975)),'better':int(np.sum(d< -1e-12)),'worse':int(np.sum(d>1e-12)),'tie':int(np.sum(np.abs(d)<=1e-12)),'n':len(ids)})
 # summaries
 def write_csv(path, rows):
  if rows:
   with path.open('w',newline='',encoding='utf-8') as f: w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 write_csv(OUT/'s3_policy_aggregates.csv',aggregate)
 # Candidate outcomes are aggregated within SCM before cohort means so the independent unit stays SCM.
 by_kind_role={}; candidate_rows=[]
 for cohort,_,_ in SOURCES:
  for kind in ('FN','FP','REV','UNRES'):
   for role in ('path_and_backdoor','path','backdoor','other_task_fp','other_task'):
    rs=[r for r in candidate_private if r['cohort']==cohort and r['kind']==kind and r['role']==role]
    scms=sorted({r['scm'] for r in rs})
    means=[float(np.mean([r['regret_gain'] for r in rs if r['scm']==s])) for s in scms]
    if means:
     rngc=np.random.default_rng(2026112702); idx=rngc.integers(0,len(means),size=(BOOT_N,len(means))); boot=np.asarray(means)[idx].mean(axis=1)
     lo,hi=float(np.quantile(boot,.025)),float(np.quantile(boot,.975)); mean=float(np.mean(means))
    else: lo=hi=mean=None
    candidate_rows.append({'cohort':cohort,'kind':kind,'role':role,'candidate_count':len(rs),'scm_count':len(scms),'mean_within_scm_regret_gain':mean,'scm_cluster_bootstrap95_low':lo,'scm_cluster_bootstrap95_high':hi})
 write_csv(OUT/'s3_candidate_value_aggregates.csv',candidate_rows)
 write_csv(OUT/'s3_error_role_counts.csv',[{'kind':k,'role':r,'candidate_count':sum(x['kind']==k and x['role']==r for x in role_counts),'scm_count':len({x['scm'] for x in role_counts if x['kind']==k and x['role']==r})} for k in ('FN','FP','REV','UNRES') for r in ('path_and_backdoor','path','backdoor','other_task_fp','other_task')])
 write_csv(OUT/'s3_m4_opportunity_summary.csv',phase1)
 write_csv(OUT/'s3_primary_paired_intervals.csv',intervals)
 feasibility={}
 for c,_,_ in SOURCES:
  rr=[x for x in phase1 if x['cohort']==c]
  feasibility[c]={'n':len(rr),'two_or_more_feasible':sum(x['m4_feasible']>=2 for x in rr),'any_feasible':sum(x['m4_feasible']>=1 for x in rr),'candidate_opportunity_pass_threshold':sum(x['m4_feasible']>=2 for x in rr)>=(10 if c=='C_DEVELOPMENT' else 25)}
 unit_lookup={(x['cohort'],x['scm'],x['policy'],x['budget']):x for x in unit_private}
 for c,_,_ in SOURCES:
  ids=sorted(x['scm'] for x in phase1 if x['cohort']==c)
  for p in ('T3','T1+T2+T3+T4+T5+T6'):
   differing=sum(unit_lookup[(c,i,p,1)]['first_edit']!=unit_lookup[(c,i,'M4_ORIGINAL',1)]['first_edit'] for i in ids if unit_lookup[(c,i,p,1)]['first_edit'] is not None and unit_lookup[(c,i,'M4_ORIGINAL',1)]['first_edit'] is not None)
   feasibility[c][f'{p}_different_first_edit_count']={'n_with_two_edits':sum(unit_lookup[(c,i,p,1)]['first_edit'] is not None and unit_lookup[(c,i,'M4_ORIGINAL',1)]['first_edit'] is not None for i in ids),'different_first_edit':differing}
 (OUT/'s3_summary.json').write_text(json.dumps({'gate':'S3_GREEDY_AND_LOOKAHEAD_COMPLETED_WITH_LIMITATIONS','cohorts':provenance,'m4_opportunity':feasibility,'policy_count':63,'budget_scope':[1,2,3,4],'lookahead_sets':['+'.join(s) for s in LOOKAHEAD_SETS],'bootstrap_replicates':BOOT_N,'bootstrap_seed':BOOT_SEED,'candidate_bootstrap_seed':2026112702,'new_scm':0,'new_g0':0,'deterministic_original_observation_matrices_reconstructed_in_memory':264,'new_independent_observational_draws':0,'new_intervention_rows':0,'source_integrity_after':provenance,'elapsed_seconds':time.perf_counter()-start,'unit_rows_written_publicly':False,'analysis_status':'post-hoc exploratory; definitions and runner were not committed before the first S3 exploratory calculation; no confirmatory interpretation'},indent=2),encoding='utf-8')
 print((OUT/'s3_summary.json').read_text(encoding='utf-8'))

if __name__=='__main__': main()

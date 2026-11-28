"""New, outcome-blind S4 Development/replication execution using frozen engines."""
from __future__ import annotations
import argparse, hashlib, json, os, platform, subprocess, sys, time
from dataclasses import asdict
from pathlib import Path
import numpy as np

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'src')]
from research.within_task_repair_prioritization.s4_completion import run_s4_pilot as base
from research.within_task_repair_prioritization import s3_analysis as s3
from research.original_objective import policy_engine as pe

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def canonical(v): return json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def derive(ns,*parts): return int.from_bytes(hashlib.sha256('|'.join((ns,*map(str,parts))).encode()).digest()[:8],'big')
def add_t5_state(unit,cohort,states,policies):
    truth=pe.state(unit['proposal']['topology_edges']); g0=unit['initial_graph']; action=unit['proposal']['action']; target=unit['proposal']['target']; cfg=unit['config']
    for combo in s3.SETS:
        graph,log=s3.greedy(truth,g0,action,target,cfg,combo,1)
        h=pe.graph_hash(graph); name='T_GREEDY_B1:'+'+'.join(combo)
        states.setdefault(h,base.state_record(graph,[x['pair'] for x in log],name,1))
        policies.append({'cohort':cohort,'scm_id':unit['scm_id'],'policy':name,'budget':1,'graph_hash':h,'cost':len(log)})
        if combo==('T5',):
            policies.append({'cohort':cohort,'scm_id':unit['scm_id'],'policy':'T5_GUIDED_M4','budget':1,'graph_hash':h,'cost':len(log)})
    return states,policies

def serializable_unit(u):
    return {**{k:v for k,v in u.items() if k not in ('config','initial_graph')},
        'config':asdict(u['config']),
        'initial_graph':{'directed_edges':[list(e) for e in sorted(x for x in u['initial_graph'].values() if x!=pe.UNRES)],
                         'unresolved_pairs':[list(p) for p,x in sorted(u['initial_graph'].items()) if x==pe.UNRES]}}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--lock',type=Path,required=True); ap.add_argument('--lock-sha256',required=True); ap.add_argument('--private-root',type=Path,required=True); ap.add_argument('--public-output',type=Path,required=True); a=ap.parse_args()
    lock=json.loads(a.lock.read_text(encoding='utf-8')); phase=lock['phase']; ns=lock['seed_namespace']
    if lock['status']!='LOCKED_BEFORE_GENERATION' or phase not in ('development','confirmation'): raise ValueError('invalid S4 lock')
    head=subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD'],text=True).strip()
    if subprocess.run(['git','-C',str(ROOT),'merge-base','--is-ancestor',lock['execution_commit'],'HEAD']).returncode: raise ValueError('locked execution source commit is not an ancestor of HEAD')
    tree=subprocess.check_output(['git','-C',str(ROOT),'rev-parse',f"{lock['execution_commit']}^{{tree}}"],text=True).strip()
    if tree!=lock['execution_tree']: raise ValueError('locked execution source tree mismatch')
    if subprocess.check_output(['git','-C',str(ROOT),'status','--porcelain'],text=True).strip(): raise ValueError('dirty checkout')
    if sha(__file__)!=lock['runner_sha256'] or sha(a.lock)!=a.lock_sha256: raise ValueError('runner/lock digest mismatch')
    for rel,digest in lock['source_sha256'].items():
        if sha(ROOT/rel)!=digest: raise ValueError(f'source hash mismatch {rel}')
    if a.private_root.exists() and any(a.private_root.iterdir()): raise FileExistsError('private run output exists')
    if a.public_output.exists() and any(a.public_output.iterdir()): raise FileExistsError('public output exists')
    a.private_root.mkdir(parents=True,exist_ok=True); a.public_output.mkdir(parents=True,exist_ok=True)
    started=time.perf_counter(); seed=int(lock['master_seed']); cap=int(lock['proposal_cap']); target=int(lock['target_scm'])
    cfg=base.make_config(); units=[]; attempts=[]; chosen=0
    journal=a.private_root/'generation_journal.jsonl'
    # The proposal screen is outcome-blind; SCM coefficients and observations are drawn only after admission.
    for ix in range(cap):
        base.guard(started)
        pid=f"{lock['proposal_prefix']}-{ix:06d}"
        proposal=base.build_structural_proposal(cohort='development',master_seed=seed,proposal_id=pid,attempt=0)
        row={'proposal_id':pid,'accepted':bool(proposal.get('accepted')),'reason':proposal.get('reason')}
        if proposal.get('accepted'):
            truth=pe.state([tuple(e) for e in proposal['topology_edges']]); gseed=derive(ns,pid,'g0')
            corruption=base.corrupt_graph_candidate(truth,nodes=proposal['nodes'],action=proposal['action'],target=proposal['target'],master_seed=gseed,task_id=f'{ns}:{pid}')
            g0=pe.state(corruption['initial_graph']['edges'],unresolved=corruption['initial_graph']['unresolved'])
            eligible=True
            row.update({'g0_generated':True,'g0_seed':gseed,'g0_hash':pe.graph_hash(g0),'eligible':eligible})
            if eligible and chosen<target:
                sid=f"{lock['run_id']}-{chosen:04d}"; gen=dict(proposal); gen['scm_id']=f'dev-scm-{sid}'; gen['master_seed']=seed
                scm=base.generate_scm_parameters(gen); obs=base.generate_observations(gen,scm); delta=1 if derive(ns,'delta',sid)&1 else -1
                unit={'cohort':'general' if phase=='development' else 'opportunity_rich_diagnostic','scm_id':sid,'proposal_id':pid,'proposal':proposal,'truth_spec':scm['truth_spec'],'truth_equation_sha256':scm['equation_signature_sha256'],'observations':obs['rows'],'observation_sha256':obs['data_sha256'],'observation_rows':obs['n_rows'],'initial_graph':g0,'initial_graph_sha256':pe.graph_hash(g0),'corruption':corruption,'g0_seed':gseed,'initial_m4_feasible_count':len(base.feasible_m4(truth,g0,proposal['action'],proposal['target'],cfg)),'delta':delta,'config':cfg}
                units.append(unit); chosen+=1; row.update({'selected':True,'scm_id':sid,'observation_sha256':obs['data_sha256']})
        attempts.append(row)
        with journal.open('ab') as stream: stream.write(canonical(row)+b'\n'); stream.flush(); os.fsync(stream.fileno())
        if chosen==target: break
    if len(units)!=target: raise RuntimeError(f'proposal cap shortfall {len(units)}/{target}; no replacement allowed')
    base.write_json(a.private_root/'inputs_private.json',[serializable_unit(u) for u in units])
    old_builder=base.build_states
    def builder(unit,cohort):
        st,pol,diag=old_builder(unit,cohort); st,pol=add_t5_state(unit,cohort,st,pol); return st,pol,diag
    base.build_states=builder
    packed,binding,manifest=base.recommendation_stage(units,started,a.private_root)
    if not binding['recommendation_manifest_sha256'] or binding['truth_response_accessed']: raise ValueError('recommendation seal invalid')
    unit_rows,candidate_rows,interactions,policy_rows=base.evaluator_stage(packed,binding,a.private_root,started)
    base.write_json(a.private_root/'unit_results_private.json',unit_rows); base.write_json(a.private_root/'candidate_values_private.json',candidate_rows); base.write_json(a.private_root/'policy_results_private.json',policy_rows); base.write_json(a.private_root/'attempts_private.json',attempts)
    # Public cohort-level estimates only; paired unit rows remain in the external private root.
    summaries=[]
    by={(r['policy'],r['budget']):[] for r in policy_rows}
    for r in policy_rows: by.setdefault((r['policy'],r['budget']),[]).append(r)
    import csv
    for (p,b),rows in sorted(by.items()):
        vals=np.asarray([x['regret'] for x in rows],dtype=float); costs=np.asarray([x['cost'] for x in rows],dtype=float)
        summaries.append({'phase':phase,'policy':p,'budget':b,'n_scm':len(rows),'mean_regret':float(vals.mean()),'median_regret':float(np.median(vals)),'sd_regret':float(vals.std(ddof=1)),'mean_edit_cost':float(costs.mean()),'action_change_rate':float(np.mean([x['action_changed_from_s0'] for x in rows]))})
    with (a.public_output/'policy_aggregates.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(summaries[0])); w.writeheader(); w.writerows(summaries)
    pairs={(r['scm_id'],r['policy'],int(r['budget'])):r for r in policy_rows}
    names=(('T5_GUIDED_M4','M4',1),('T_GREEDY_B1:T1+T2+T3+T4+T5+T6','M4',1),('M4','S0',2),('FULL_GREEDY','S0',2))
    n=len(units); ix=np.random.default_rng(int(lock['bootstrap_seed'])).integers(0,n,size=(10_000,n)); contrasts=[]
    for lhs,rhs,b in names:
        if (lhs,rhs,b)==('T5_GUIDED_M4','M4',1): left=lhs; right=rhs
        elif lhs.startswith('T_GREEDY'): left=lhs; right=rhs
        else: left=lhs; right=rhs
        leftvals=[]; rightvals=[]
        for u in units:
            leftvals.append(float(pairs[(u['scm_id'],left,b)]['regret']))
            rightvals.append(float(pairs[(u['scm_id'],right,b)]['regret']))
        d=np.asarray(leftvals)-np.asarray(rightvals); boot=d[ix].mean(axis=1)
        contrasts.append({'phase':phase,'contrast':f'{left}-{right}_B{b}','n_scm':n,'mean_difference':float(d.mean()),'median_difference':float(np.median(d)),'ci95_low':float(np.quantile(boot,.025)),'ci95_high':float(np.quantile(boot,.975)),'better_left':int((d< -1e-12).sum()),'worse_left':int((d>1e-12).sum()),'tie':int((np.abs(d)<=1e-12).sum()),'seed':int(lock['bootstrap_seed']),'replicates':10000})
    with (a.public_output/'paired_contrasts.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(contrasts[0])); w.writeheader(); w.writerows(contrasts)
    result={'schema':'S4_RECONSTRUCTION_RESULT_V1','phase':phase,'run_id':lock['run_id'],'status':'COMPLETED','classification':'post-hoc development' if phase=='development' else 'new independent replication','n_scm':len(units),'observational_rows':len(units)*512,'new_g0_analysis_draws':len(units),'new_intervention_rows':0,'proposal_attempts':len(attempts),'candidate_rows':len(candidate_rows),'recommendation_rows':len(manifest),'recommendation_sha256':binding['recommendation_manifest_sha256'],'private_inputs_sha256':sha(a.private_root/'inputs_private.json'),'unit_results_sha256':sha(a.private_root/'unit_results_private.json'),'policy_results_sha256':sha(a.private_root/'policy_results_private.json'),'execution_head':head,'runtime_seconds':time.perf_counter()-started,'runtime':{'python':platform.python_version(),'numpy':np.__version__},'limitations':['Q-common-admitted strict-indirect population; not unconditional C population','analytic true-SCM evaluator; no sampled intervention rows','post-hoc analysis; not scientific confirmation of general superiority']}
    base.write_json(a.public_output/'summary.json',result)
    print(json.dumps(result,sort_keys=True))
if __name__=='__main__': main()

"""Locked, two-stage S5 Station1 reconstruction; raw artifacts stay external."""
from __future__ import annotations
import argparse, hashlib, json, os, platform, subprocess, sys, time
from pathlib import Path
import numpy as np
import pandas as pd

HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'src')]
from research.external_validation.semisynthetic_evaluation import pipeline as d
from research.external_validation.semisynthetic_evaluation import reproducibility as repro
from research.external_validation.semisynthetic_final import final_pipeline as fp
from research.external_validation.semisynthetic_adapter.float_hard_do_adapter import sample_hard_do

CONTRACT=HERE/'s5_reconstruction_contract.json'; X=d.TASK_X; Y=d.TASK_Y
def sha(p): return d.file_sha256(Path(p))
def canon(x): return json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def seed(ns,label): return int.from_bytes(hashlib.sha256(f'{ns}|{label}'.encode()).digest()[:4],'big')
def load_resumed_training(path,node_order,expected_raw_sha256,expected_numeric_sha256):
    path=Path(path)
    if sha(path)!=expected_raw_sha256: raise ValueError('resumed S5 training CSV raw hash mismatch')
    return repro.read_training_frame(path,node_order=list(node_order),rows=512,expected_numeric_sha256=expected_numeric_sha256)
def write(path,obj):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists(): raise FileExistsError(f'refusing overwrite: {path.name}')
    path.write_bytes(json.dumps(obj,sort_keys=True,indent=2,allow_nan=False).encode()+b'\n')
def lock_guard(lock_path,lock_sha,stage):
    c=json.loads(CONTRACT.read_text(encoding='utf-8')); lock=json.loads(Path(lock_path).read_text(encoding='utf-8'))
    if sha(lock_path)!=lock_sha or lock.get('status')!='LOCKED_BEFORE_GENERATION': raise ValueError('S5 run lock invalid')
    if lock.get('run_id')!=c['run_id'] or lock.get('stage')!=stage: raise ValueError('S5 run/stage mismatch')
    head=subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD'],text=True).strip()
    if lock.get('execution_commit')!=head: raise ValueError('S5 code revision changed since lock')
    tree=subprocess.check_output(['git','-C',str(ROOT),'rev-parse',f'{head}^{{tree}}'],text=True).strip()
    if lock.get('execution_tree')!=tree: raise ValueError('S5 execution tree differs from locked source')
    if subprocess.check_output(['git','-C',str(ROOT),'status','--porcelain'],text=True).strip(): raise ValueError('S5 requires clean source checkout')
    for rel,expected in lock['source_sha256'].items():
        if sha(ROOT/rel)!=expected: raise ValueError(f'S5 source digest mismatch: {rel}')
    if sha(CONTRACT)!=lock['contract_sha256']: raise ValueError('S5 contract changed')
    if lock.get('classification')!=c['classification']: raise ValueError('S5 classification mismatch')
    return c,lock
def ensure_root_external(path):
    root=Path(path).resolve()
    if root==ROOT or ROOT in root.parents: raise ValueError('private output must be outside repository')
    if root.exists() and any(root.iterdir()): raise FileExistsError('S5 run directory already contains data')
    root.mkdir(parents=True,exist_ok=True); return root
def training_actions(train,model):
    actions=np.quantile(train[X].to_numpy(float),[.1,.3,.5,.7,.9],method='linear').astype(float).tolist()
    if len(set(actions))!=5 or np.diff(actions).min()<=0: raise ValueError('invalid training-only S5 action grid')
    for action in actions:
        if action<float(train[X].min()) or action>float(train[X].max()): raise ValueError('action outside training marginal support')
    topo={n:i for i,n in enumerate(__import__('networkx').topological_sort(model.graph))}
    for node in sorted(__import__('networkx').descendants(model.graph,X),key=topo.__getitem__):
        xtrain=getattr(model.drf[node],'X_train',None)
        if xtrain is not None and X in xtrain:
            if min(actions)<float(xtrain[X].min()) or max(actions)>float(xtrain[X].max()): raise ValueError(f'action outside fitted support for {node}')
    return actions
def graph_edges(g):
    from research.original_objective import policy_engine as pe
    return sorted([list(e) for e in g.values() if e!=pe.UNRES])
def as_graph(edges,unresolved=()):
    from research.original_objective import policy_engine as pe
    return pe.state([tuple(e) for e in edges],unresolved=[tuple(p) for p in unresolved])
def truth_graph_digest(graph):
    payload=repr(sorted((p,e) for p,e in graph.items())).encode()
    return hashlib.sha256(payload).hexdigest()
def public_g0_rows(rows):
    return [{'seed_id':r['seed_id'],'master_seed':r['master_seed'],'record':r['record'],'graph_sha256':r['graph_hash']} for r in rows]
def load_g0_checkpoint(path,truth,nodes,c):
    from research.original_objective import policy_engine as pe
    from research.original_objective.g0_candidate import corrupt_graph_candidate
    path=Path(path); payload=json.loads(path.read_text(encoding='utf-8'))
    digest_body={k:v for k,v in payload.items() if k!='file_sha256'}
    if payload.get('schema')!='S5_G0_CHECKPOINT_V1' or hashlib.sha256(canon(digest_body)).hexdigest()!=payload.get('file_sha256'):
        raise ValueError('S5 G0 checkpoint schema or file hash mismatch')
    rows=payload.get('rows',[]); expected=list(range(c['g0']['id_start'],c['g0']['id_start']+c['g0']['count']))
    if [r.get('seed_id') for r in rows]!=expected: raise ValueError('S5 G0 checkpoint ID grid mismatch')
    digest=truth_graph_digest(truth)
    for r in rows:
        sid=r['seed_id']; master=seed(c['g0']['namespace'],f'g0|{sid}')
        if r.get('master_seed')!=master: raise ValueError('S5 G0 checkpoint seed mismatch')
        regenerated=corrupt_graph_candidate(truth,nodes=list(nodes),action=X,target=Y,master_seed=master,task_id=f"{c['run_id']}:{sid}",true_corruption_rate=.15,false_adjacency_rate=.05)
        if regenerated!=r['record']: raise ValueError(f'S5 G0 checkpoint deterministic provenance mismatch: {sid}')
        graph=as_graph(regenerated['initial_graph']['edges'],regenerated['initial_graph']['unresolved'])
        if pe.graph_hash(graph)!=r.get('graph_sha256'): raise ValueError(f'S5 G0 checkpoint graph hash mismatch: {sid}')
        if regenerated.get('truth_graph_sha256')!=digest: raise ValueError(f'S5 G0 checkpoint truth binding mismatch: {sid}')
        r['graph_hash']=r['graph_sha256']; r['graph']=graph
    return rows
def write_g0_checkpoint(path,rows):
    body={'schema':'S5_G0_CHECKPOINT_V1','rows':public_g0_rows(rows)}
    body['file_sha256']=hashlib.sha256(canon(body)).hexdigest()
    write(path,body)
def recommend_stage(args):
    from research.original_objective import policy_engine as pe
    from research.within_task_repair_prioritization import s3_analysis as s3
    c,lock=lock_guard(args.run_lock,args.run_lock_sha256,'recommendation'); out=ensure_root_external(args.private_root)
    sr=Path(args.source_root).resolve(); dr=Path(args.data_root).resolve(); verify=d.verify_sources(sr,dr)
    if verify['source_commit']!=c['source']['commit']: raise ValueError('pinned upstream commit mismatch')
    mpath=Path(subprocess.check_output([sys.executable,'-c','import causalAssembly,pathlib;print(pathlib.Path(causalAssembly.__file__).resolve())'],text=True).strip())
    try: mpath.relative_to(sr)
    except ValueError as e: raise ValueError('causalAssembly did not import from pinned checkout') from e
    model,source,fitinfo=d.load_fit_station1(sr,dr,c['generator']['fit_seed'])
    if args.resume_training_csv is not None:
        expected=lock.get('reused_training',{})
        src=Path(args.resume_training_csv).resolve()
        if not expected: raise ValueError('missing S5 training resume binding')
        train=load_resumed_training(src,list(model.nodes),expected['raw_sha256'],expected['numeric_sha256'])
        training_reused=True; training_source_sha=sha(src)
    else:
        model.random_state=np.random.default_rng(c['training']['seed']); train=model.sample_from_drf(size=512,smoothed=True).loc[:,list(model.nodes)]
        training_reused=False; training_source_sha=None
    vals=train.to_numpy(dtype=np.float64)
    if train.shape!=(512,6) or list(train.columns)!=list(model.nodes) or not np.isfinite(vals).all(): raise ValueError('S5 training sample schema/finite check failed')
    target=float(train[Y].mean()+train[Y].std(ddof=1)); scale=float(train[Y].std(ddof=1)); actions=training_actions(train,model)
    training_path=out/'training.csv'
    with training_path.open('xb') as stream:
        stream.write(src.read_bytes() if training_reused else repro.serialize_training_frame(train))
        stream.flush(); os.fsync(stream.fileno())
    train_sha=sha(training_path); numeric_sha=hashlib.sha256(vals.tobytes(order='C')).hexdigest()
    truth=pe.state([tuple(e) for e in model.graph.edges]); cfg=pe.Config(fp_rule='A',normalization='fixed_opportunity')
    if args.resume_g0_records is not None:
        g0_rows=load_g0_checkpoint(args.resume_g0_records,truth,list(model.nodes),c)
        checkpoint_source_sha=sha(args.resume_g0_records)
    else:
        from research.original_objective.g0_candidate import corrupt_graph_candidate
        g0_rows=[]
        for sid in range(c['g0']['id_start'],c['g0']['id_start']+c['g0']['count']):
            master=seed(c['g0']['namespace'],f'g0|{sid}')
            rec=corrupt_graph_candidate(truth,nodes=list(model.nodes),action=X,target=Y,master_seed=master,task_id=f"{c['run_id']}:{sid}",true_corruption_rate=.15,false_adjacency_rate=.05)
            g=as_graph(rec['initial_graph']['edges'],rec['initial_graph']['unresolved'])
            g0_rows.append({'seed_id':sid,'master_seed':master,'record':rec,'graph_hash':pe.graph_hash(g),'graph':g})
        write_g0_checkpoint(out/'g0_checkpoint.json',g0_rows)
        checkpoint_source_sha=None
    if len(g0_rows)!=200 or len({r['seed_id'] for r in g0_rows})!=200: raise ValueError('incomplete or duplicate S5 G0 grid')
    action_seeds=[seed(c['g0']['namespace'],f"action|{i}|{repr(float(v))}") for i,v in enumerate(actions)]
    random_policy_seeds=[seed(c['g0']['namespace'],f'random-m4|{sid}') for sid in range(c['g0']['id_start'],c['g0']['id_start']+c['g0']['count'])]
    rng_values=[int(c['generator']['fit_seed']),int(c['training']['seed']),*[r['master_seed'] for r in g0_rows],*action_seeds,*random_policy_seeds,int(c['evaluation']['bootstrap_seed_g0_only']),int(c['evaluation']['bootstrap_seed_action_mc_only']),int(c['evaluation']['bootstrap_seed_two_source'])]
    if len(rng_values)!=len(set(rng_values)): raise ValueError('S5 RNG stream collision within locked run')
    # Seal all graph/task/training-derived recommendations before evaluator access.
    recommendations=[]; cache={}; action_mid=float(np.median(actions));
    for unit in g0_rows:
        g0=unit['graph']; sid=unit['seed_id']; edges=graph_edges(g0)
        for b in range(5):
            result=pe.run_catalog(truth,g0,X,Y,b,cfg)
            rows=result['strategies']+[result['canonical_oracle']]
            for p in rows:
                pid=p['policy_id']; g=as_graph(p['final_edges'],p['final_unresolved']); recommendations.append((sid,b,pid,g, int(p['total_cost']), int(p['unused_budget'])))
            for pid,comb in [('T5_GUIDED_M4',('T5',)),('FULL_T1_T6',s3.T)]:
                if b==0: g=dict(g0); cost=0
                else: g,log=s3.greedy(truth,g0,X,Y,cfg,comb,b); cost=len(log)
                recommendations.append((sid,b,pid,g,cost,max(0,b-cost)))
            # One preseeded uniform feasible M4 trajectory; each budget is a prefix.
            if b==0: rg=dict(g0); rlog=[]
            else:
                # deterministic trajectory is recomputed for prefix consistency using its own RNG stream
                rng=np.random.default_rng(seed(c['g0']['namespace'],f'random-m4|{sid}'))
                pool=[e for e in pe.candidates(truth,g0,X,Y,cfg) if e.metric=='M4']; rg=dict(g0); rlog=[]
                for step in range(b):
                    legal=[]
                    for e in pool:
                        if not s3.direct_task_edit(e,truth,rg,X,Y,cfg): continue
                        trial=pe.apply(rg,e)
                        if pe.dag(trial): legal.append((e,trial))
                    if not legal: break
                    e,trial=legal[int(rng.integers(0,len(legal)))]; rg=trial; rlog.append(e); pool=[x for x in pool if x.key!=e.key]
            recommendations.append((sid,b,'RANDOM_M4',rg,len(rlog),max(0,b-len(rlog))))
            for pid,graph in [('GRAPH_FREE_ASSOCIATION',None),('REFERENCE_GRAPH_LEARNER',truth)]:
                g=g0 if graph is None else graph; cost=0
                recommendations.append((sid,b,pid,g,cost,b))
    # Avoid duplicate policy ids from the standard catalog and verify exact complete key grid.
    keys=[(r[0],r[1],r[2]) for r in recommendations]
    if len(keys)!=len(set(keys)): raise ValueError('duplicate recommendation keys')
    expected=200*5*(17+5)
    if len(recommendations)!=expected: raise ValueError(f'S5 recommendation grid incomplete {len(recommendations)}/{expected}')
    for sid,b,pid,g,cost,unused in recommendations:
        h=pe.graph_hash(g)
        if h not in cache:
            if pid=='GRAPH_FREE_ASSOCIATION': action,_=d.graph_free_recommendation(train,actions,target,scale)
            else:
                ed=graph_edges(g)
                action,_=d.learner_recommendation(train,list(model.nodes),{tuple(e) for e in ed},actions,target,scale)
            cache[h]=float(action)
        # Graph-free has graph-free prediction but its graph hash is the no-repair graph.
    rec_rows=[]
    for sid,b,pid,g,cost,unused in recommendations:
        h=pe.graph_hash(g)
        if pid=='GRAPH_FREE_ASSOCIATION': act,_=d.graph_free_recommendation(train,actions,target,scale)
        else: act=cache[h]
        rec_rows.append({'g0_seed_id':sid,'budget':b,'policy_id':pid,'g0_sha256':next(x['graph_hash'] for x in g0_rows if x['seed_id']==sid),'graph_sha256':h,'recommended_action':float(act),'edit_count':cost,'unused_budget':unused})
    if len({r['recommended_action'] for r in rec_rows})>5: raise ValueError('invalid S5 action value')
    rec_path=out/'recommendation_manifest.json'; rec_obj={'schema':'S5_RECOMMENDATION_LOCK_V1','run_id':c['run_id'],'contract_sha256':sha(CONTRACT),'training_csv_sha256':train_sha,'training_numeric_sha256':numeric_sha,'task':{'action':X,'target':Y,'target_value':target,'scale':scale},'actions':actions,'g0_seed_ids':[r['seed_id'] for r in g0_rows],'g0_hashes':{str(r['seed_id']):r['graph_hash'] for r in g0_rows},'recommendation_rows':len(rec_rows),'policies_per_budget':22,'rows':rec_rows,'truth_or_evaluator_outcomes_accessed':False}
    digest=hashlib.sha256(canon(rec_obj)).hexdigest(); rec_obj['content_sha256']=digest; write(rec_path,rec_obj)
    execution={'schema':'S5_RECOMMENDATION_EXECUTION_MANIFEST_V1','run_id':c['run_id'],'attempt_id':lock.get('attempt_id','attempt-01'),'classification':c['classification'],'contract_sha256':sha(CONTRACT),'run_lock_sha256':args.run_lock_sha256,'source_verification':verify,'imported_causalAssembly':str(mpath),'fit':fitinfo,'runtime':fp.expected_env(),'training':{'rows':512,'raw_sha256':train_sha,'numeric_sha256':numeric_sha,'target':target,'scale':scale,'sample_seed':c['training']['seed'],'reused_existing_sample':training_reused,'resume_source_sha256':training_source_sha},'task':{'action':X,'target':Y,'actions':actions},'g0_count':200,'g0_checkpoint_sha256':sha(out/'g0_checkpoint.json'),'g0_checkpoint_reused':args.resume_g0_records is not None,'g0_checkpoint_source_sha256':checkpoint_source_sha,'g0_seed_ids':[r['seed_id'] for r in g0_rows],'g0_hashes':{str(r['seed_id']):r['graph_hash'] for r in g0_rows},'rng_streams':{'g0_master_seeds':[r['master_seed'] for r in g0_rows],'action_seeds':action_seeds,'random_m4_seeds':random_policy_seeds,'bootstrap_seeds':[c['evaluation'][x] for x in ('bootstrap_seed_g0_only','bootstrap_seed_action_mc_only','bootstrap_seed_two_source')],'within_run_collision_count':0},'recommendation_rows':len(rec_rows),'recommendation_sha256':sha(rec_path),'recommendations_sealed_before_evaluator':True,'new_intervention_rows':0,'source_commit':lock['execution_commit'],'source_tree':lock['execution_tree']}
    write(out/'execution_manifest.json',execution); write(out/'g0_manifest.json',{'count':200,'rows':[{'seed_id':r['seed_id'],'master_seed':r['master_seed'],'graph_sha256':r['graph_hash']} for r in g0_rows]})
    write(out/'g0_records_private.json',public_g0_rows(g0_rows))
    print(json.dumps({'stage':'recommendation','status':'PASS_SEALED','g0_count':200,'recommendation_rows':len(rec_rows),'recommendation_sha256':sha(rec_path),'training_sha256':train_sha,'target':target,'scale':scale,'actions':actions},sort_keys=True))

def evaluation_stage(args):
    c,lock=lock_guard(args.run_lock,args.run_lock_sha256,'evaluation'); out=Path(args.private_root).resolve()
    rec_path=out/'recommendation_manifest.json'; execution_path=out/'execution_manifest.json'
    repro.require_external_outputs(ROOT,[args.evaluator_output,args.public_summary])
    if Path(args.public_summary).exists(): raise FileExistsError('public aggregate output already exists')
    if not rec_path.is_file() or not execution_path.is_file(): raise FileNotFoundError('sealed recommendation artifacts missing')
    rec=json.loads(rec_path.read_text()); execution=json.loads(execution_path.read_text())
    if any(name.startswith('research.original_objective') for name in sys.modules): raise RuntimeError('evaluator imported repair-policy code')
    if sha(rec_path)!=execution['recommendation_sha256'] or rec.get('truth_or_evaluator_outcomes_accessed') is not False: raise ValueError('recommendation seal invalid')
    if rec.get('content_sha256')!=hashlib.sha256(canon({k:v for k,v in rec.items() if k!='content_sha256'})).hexdigest(): raise ValueError('recommendation internal digest invalid')
    if args.evaluator_output.exists(): raise FileExistsError('S5 evaluator directory exists; no overwrite')
    ev=args.evaluator_output.resolve(); ev.mkdir(parents=True,exist_ok=False)
    source=Path(args.source_root).resolve(); data=Path(args.data_root).resolve()
    model,_source,fitinfo=d.load_fit_station1(source,data,c['generator']['fit_seed'])
    if fitinfo['graph_sha256']!=execution['fit']['graph_sha256']: raise ValueError('Station1 fitted graph differs from recommendation run')
    records=[]; started=time.perf_counter(); rows_per=c['evaluation']['rows_per_action']; action_records=[]
    state_path=ev/'sampling_state.json'
    write(state_path,{'schema':'S5_SAMPLING_STATE_V1','status':'SAMPLING_STARTED','completed_action_indices':[],'rows_completed':0,'active_action_index':None,'retry_allowed':False})
    for i,action in enumerate(rec['actions']):
        action_seed=execution['rng_streams']['action_seeds'][i]
        state=json.loads(state_path.read_text(encoding='utf-8')); state['active_action_index']=i; state['active_seed']=action_seed; state['active_call_rows']=rows_per
        state_path.write_text(json.dumps(state,indent=2,sort_keys=True)+'\n',encoding='utf-8')
        frame=sample_hard_do(model,X,float(action),size=rows_per,rng=np.random.default_rng(action_seed),smoothed=True)
        if list(frame.columns)!=execution['fit']['nodes'] or frame.shape!=(rows_per,6): raise ValueError('S5 hard-do output schema/shape mismatch')
        vals=frame.to_numpy(dtype=np.float64)
        if not np.isfinite(vals).all() or not np.all(vals[:,execution['fit']['nodes'].index(X)]==action): raise ValueError('S5 hard-do finite/value check failed')
        y=vals[:,execution['fit']['nodes'].index(Y)].copy(); path=ev/f'action_{i:02d}.npy'
        with path.open('xb') as f: np.save(f,y,allow_pickle=False); f.flush(); os.fsync(f.fileno())
        action_records.append({'index':i,'action':float(action),'seed':action_seed,'rows':len(y),'sha256':sha(path),'filename':path.name})
        state=json.loads(state_path.read_text(encoding='utf-8')); state['completed_action_indices'].append(i); state['rows_completed']+=len(y); state['active_action_index']=None; state['active_seed']=None; state['active_call_rows']=0
        state_path.write_text(json.dumps(state,indent=2,sort_keys=True)+'\n',encoding='utf-8')
        del frame,vals,y
    vectors=[np.load(ev/r['filename'],allow_pickle=False) for r in action_records]
    target=float(rec['task']['target_value']); scale=float(rec['task']['scale']); loss=[]
    for r,v in zip(action_records,vectors):
        loss.append(float(((v.mean()-target)**2-v.var(ddof=1)/len(v))/(scale**2)))
    action_loss={float(a):loss[i] for i,a in enumerate(rec['actions'])}
    unit_losses=[]
    for row in rec['rows']:
        unit_losses.append({**row,'loss':action_loss[float(row['recommended_action'])]})
    by={(r['g0_seed_id'],r['budget'],r['policy_id']):r for r in unit_losses}
    if len(by)!=len(unit_losses): raise ValueError('duplicate unit recommendation/evaluation key')
    for sid in rec['g0_seed_ids']:
        for budget in c['budgets']:
            ids=[k for k in by if k[0]==sid and k[1]==budget]
            if len(ids)!=22: raise ValueError('incomplete S5 evaluator policy grid')
    # Save private evaluator data immediately; public outputs contain only aggregate estimates.
    write(ev/'unit_policy_losses_private.json',unit_losses)
    write(ev/'evaluation_manifest.json',{'schema':'S5_RESPONSE_MANIFEST_V1','run_id':c['run_id'],'recommendation_sha256':sha(rec_path),'execution_manifest_sha256':sha(execution_path),'action_records':action_records,'rows_per_action':rows_per,'total_rows':rows_per*len(action_records),'action_means':[float(v.mean()) for v in vectors],'action_variances':[float(v.var(ddof=1)) for v in vectors],'bias_corrected_losses':loss,'sampling_seconds':time.perf_counter()-started,'outcomes_used_to_change_contract_or_recommendations':False})
    state=json.loads(state_path.read_text(encoding='utf-8')); state['status']='ALL_ACTION_VECTORS_SAVED'; state['completed_action_count']=len(action_records); state_path.write_text(json.dumps(state,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    write(args.public_summary,{'schema':'S5_PUBLIC_AGGREGATE_V1','run_id':c['run_id'],'classification':c['classification'],'g0_count':200,'policy_rows':len(unit_losses),'training_rows':512,'intervention_rows':rows_per*5,'response_vector_sha256':[r['sha256'] for r in action_records],'recommendation_sha256':sha(rec_path),'primary':primary_result(by,rec,c),'action_summary':[{'action':float(a),'mean':float(v.mean()),'sd':float(v.std(ddof=1)),'bias_corrected_loss':loss[i]} for i,(a,v) in enumerate(zip(rec['actions'],vectors))],'sampling_seconds':time.perf_counter()-started})
    print(json.dumps({'stage':'evaluation','status':'PASS','intervention_rows':rows_per*5,'response_hashes':[r['sha256'] for r in action_records],'sampling_seconds':time.perf_counter()-started},sort_keys=True))

def primary_result(by,rec,c):
    left=[]; right=[]
    for sid in rec['g0_seed_ids']:
        left.append(by[(sid,2,'S0')]['loss']); right.append(by[(sid,2,'M4')]['loss'])
    dlt=np.asarray(left)-np.asarray(right); rng=np.random.default_rng(c['evaluation']['bootstrap_seed_g0_only']); n=len(dlt); boots=[]
    for start in range(0,c['evaluation']['bootstrap_replicates'],c['evaluation']['chunk_size']):
        m=min(c['evaluation']['chunk_size'],c['evaluation']['bootstrap_replicates']-start); ix=rng.integers(0,n,size=(m,n)); boots.extend(dlt[ix].mean(axis=1).tolist())
    return {'contrast':'loss(No-repair)-loss(Frozen M4), B=2, gamma=0','mean_difference':float(dlt.mean()),'median_difference':float(np.median(dlt)),'ci95_low':float(np.quantile(boots,.025)),'ci95_high':float(np.quantile(boots,.975)),'better_m4':int((dlt>1e-12).sum()),'worse_m4':int((dlt< -1e-12).sum()),'tie':int((np.abs(dlt)<=1e-12).sum()),'n_g0':n,'bootstrap_replicates':len(boots),'bootstrap_seed':c['evaluation']['bootstrap_seed_g0_only'],'unit':'paired G0 draw within one fixed fitted DGP'}

def main():
    p=argparse.ArgumentParser(); p.add_argument('--stage',choices=['recommendation','evaluation'],required=True); p.add_argument('--run-lock',type=Path,required=True); p.add_argument('--run-lock-sha256',required=True); p.add_argument('--private-root',type=Path,required=True); p.add_argument('--source-root',type=Path,required=True); p.add_argument('--data-root',type=Path,required=True); p.add_argument('--resume-training-csv',type=Path); p.add_argument('--resume-g0-records',type=Path); p.add_argument('--evaluator-output',type=Path); p.add_argument('--public-summary',type=Path)
    a=p.parse_args()
    if a.stage=='recommendation': recommend_stage(a)
    else:
        if a.evaluator_output is None or a.public_summary is None: p.error('evaluation requires evaluator-output and public-summary')
        evaluation_stage(a)
if __name__=='__main__': main()

"""New do draws on old development structures: implementation/precision only."""
import argparse,gzip,hashlib,importlib.metadata,json,math,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from path_metric_incremental import load,linear_moments
from fcm_acceptance_adapter import load_pinned_module,PIN_SHA
from diverse_structure_pilot import draw_structure,reference_edges
from run_diverse_structure_pilot import save

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--output',required=True);a=p.parse_args()
    out=Path(a.output);out.mkdir(parents=True,exist_ok=False)
    design_path=ROOT/'research_runs/path_metric_incremental_validation/DESIGN_GATE_PLAN_v1.json';design=load(design_path);cfg=design['mc_calibration']
    specs={s['structure_id']:s for f in ['diverse_structure_pilot','independent_confirmation'] for s in load(ROOT/'research_runs'/f/'PLAN_v1.json')['structures']}
    module=load_pinned_module(a.source);cases=[]
    for si,sid in enumerate(cfg['structures']):
        s=specs[sid];actions=list(dict.fromkeys(t['action'] for t in s['tasks'] if t['task_id'] in ['direct','path']))
        for ai,action in enumerate(actions):
            tasks=[t for t in s['tasks'] if t['task_id'] in ['direct','path'] and t['action']==action]
            var=linear_moments(s,action,0)[1];worst=max(var[t['target']] for t in tasks)
            n=next((n for n in cfg['prefix_n'] if 1.96*math.sqrt(worst/n)<=cfg['absolute_mean_95_halfwidth_target']),cfg['max_n'])
            for vi,value in enumerate(cfg['values']):
                cases.append(dict(case_id=f'{sid}_{ai}_{vi}',structure_id=sid,action=action,value=value,n=n,seed=cfg['seed_base']+si*100000+ai*1000+vi*10,
                    target_tasks=tasks,expected_worst_halfwidth=1.96*math.sqrt(worst/n),precision_target_met=1.96*math.sqrt(worst/n)<=cfg['absolute_mean_95_halfwidth_target']))
    plan=dict(protocol='PATH-MC-CALIBRATION-v1',utc=datetime.now(timezone.utc).isoformat(),role='new do samples on OLD development structures; not independent structural confirmation',
        design_sha256=sha(design_path),source_commit='8da3729e6383f0e1cbe7740bb6ab7ac4977ac7f9',source_sha256=PIN_SHA,
        code_sha256={str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in [Path(__file__),ROOT/'src/path_metric_incremental.py',ROOT/'src/diverse_structure_pilot.py']},
        versions={n:importlib.metadata.version(n) for n in ['numpy','pandas','sympy','networkx']},structures=[specs[s] for s in cfg['structures']],cases=cases)
    save(out/'PLAN_v1.json',plan);(out/'PLAN_v1.sha256').write_text(sha(out/'PLAN_v1.json')+'\n',encoding='utf-8')
    save(out/'EXECUTION_START.json',dict(utc=datetime.now(timezone.utc).isoformat(),plan_sha256=sha(out/'PLAN_v1.json')))
    statistics=[];checks=[];failures=[]
    for c in cases:
        folder=out/c['case_id'];folder.mkdir();s=specs[c['structure_id']]
        try:
            frame,noise,meta=draw_structure(module,s,c['seed'],c['n'],c['action'],c['value'])
            twin,_,_=draw_structure(module,s,c['seed'],c['n'],c['action'],c['value'])
            g=meta['intervention'];ok=dict(returned_gt=set(map(tuple,meta['returned_edges']))==reference_edges(s),equations=max(meta['reconstruction_errors'].values())<1e-10,
                exact_repeat=frame.equals(twin),action_constant=bool((frame[c['action']]==c['value']).all()),removed_parents=g['parents']==[],
                other_equations_unchanged=g['other_equations_unchanged'],removed_noise='u_'+c['action'] not in noise,
                replaced_equation=float(g['term'])==c['value'],mutilated_edges=set(map(tuple,g['edges']))=={e for e in reference_edges(s) if e[1]!=c['action']})
            assert all(ok.values()),ok
            import pandas as pd
            for name,data in [('samples',frame),('noise',pd.DataFrame(noise))]:
                (folder/(name+'.csv.gz')).write_bytes(gzip.compress(data.to_csv(index=False,float_format='%.17g').encode(),mtime=0))
            save(folder/'metadata.json',dict(case=c,checks=ok,metadata=meta));checks.append(dict(case_id=c['case_id'],checks=ok))
            means,var=linear_moments(s,c['action'],c['value'])
            for t in c['target_tasks']:
                for n in cfg['prefix_n']:
                    if n>c['n']:continue
                    x=frame[t['target']].iloc[:n];m=float(x.mean());se=float(x.std(ddof=1))/math.sqrt(n);theory=means[t['target']]
                    statistics.append(dict(case_id=c['case_id'],structure_id=c['structure_id'],task_id=t['task_id'],action=c['action'],value=c['value'],n=n,
                        analytic_mean=theory,sample_mean=m,error=m-theory,standard_error=se,expected_se=math.sqrt(var[t['target']]/n),
                        analytic_loss=(theory-t['target_value'])**2+t['cost_weight']*(c['value']-t['reference_action'])**2,
                        sample_loss=(m-t['target_value'])**2+t['cost_weight']*(c['value']-t['reference_action'])**2,
                        mean_95_interval_contains_theory=abs(m-theory)<=1.96*se))
        except Exception as e:
            failures.append(dict(case_id=c['case_id'],type=type(e).__name__,message=str(e)));save(out/'FAILURES.json',failures);raise
    rankings=[]
    for sid in cfg['structures']:
        for task in ['direct','path']:
            for n in cfg['prefix_n']:
                r=[r for r in statistics if r['structure_id']==sid and r['task_id']==task and r['n']==n]
                if len(r)!=len(cfg['values']):continue
                key=lambda x,k:(x[k],abs(x['value']),x['value'])
                empirical=min(r,key=lambda x:key(x,'sample_loss'))['value'];analytic=min(r,key=lambda x:key(x,'analytic_loss'))['value']
                rankings.append(dict(structure_id=sid,task_id=task,n=n,analytic_best=analytic,sample_best=empirical,mismatch=analytic!=empirical,scope='restricted predeclared three-value calibration grid, NOT full five-value recommendation oracle'))
    save(out/'statistics.json',statistics);save(out/'restricted_grid_rankings.json',rankings);save(out/'checks.json',checks);save(out/'FAILURES.json',failures)
    summary=dict(status='PASS_IMPLEMENTATION_ONLY',cases=len(cases),unique_generated_samples=sum(c['n'] for c in cases),repeat_verification_samples=sum(c['n'] for c in cases),
        precision_unmet_cases=sum(not c['precision_target_met'] for c in cases),rank_mismatches=sum(r['mismatch'] for r in rankings),rank_comparisons=len(rankings),
        new_independent_reference_structures=0,new_discovery_learning_calls=0,independent_hypothesis_confirmation='NOT_RUN_PRECISION_RESOURCE_GATE',
        note='prefixes correlated; sample error need not decrease monotonically; no row-paired counterfactual or manufacturing claim')
    save(out/'SUMMARY.json',summary)
    save(out/'SHA256.json',{str(f.relative_to(out)).replace('\\','/'):sha(f) for f in sorted(out.rglob('*')) if f.is_file() and f.name!='SHA256.json'})
    print(json.dumps(summary))

if __name__=='__main__':main()

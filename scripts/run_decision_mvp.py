"""Reuse frozen assets; separate benchmark dry recommendations from simulator smoke."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from decision_mvp import recommend_grid, require_research_environment, task_metrics

ALGOS={'pc':'PC-stable','boss':'BOSS','directlingam':'DirectLiNGAM','dagma':'DAGMA',
       'pcmciplus':'PCMCI+','varlingam':'VarLiNGAM','dynotears':'DYNOTEARS'}


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')


def matrix(path,names):
    with path.open(encoding='utf-8-sig',newline='') as f:rows=list(csv.reader(f))
    assert rows[0][1:]==names and [r[0] for r in rows[1:]]==names
    return {(names[i],names[j]) for i,row in enumerate(rows[1:]) for j,v in enumerate(row[1:]) if int(v)==1}


def run(args,out):
    import numpy as np
    plan_path=ROOT/'research_runs/decision_mvp/PLAN_v1.json';plan=read(plan_path)
    if args.mode=='research':
        require_research_environment(plan['structure_environment'],plan['outcome_environment'],{})
    write(out/'plan.json',plan)
    names=[r['variable'] for r in csv.DictReader((ROOT/'graphs/final/variables.csv').open(encoding='utf-8'))]
    tasks=read(ROOT/'docs/tasks/structural_task_candidates_v1_1.json')
    selected=next(t for t in tasks if t['task_id']==plan['task_id'])
    assert selected['action']==plan['action'] and selected['target']==plan['target']
    gt_path=ROOT/'data/local/TEGroundTruth.txt'
    assert sha(gt_path)=='238542dbdde50887b5944fb3acc64a792b19a0c56bbfa06e3b267261f2fe6c43'
    raw=np.loadtxt(gt_path,dtype=int);keep=[int(v[1:])-1 for v in names]
    gt=raw[np.ix_(keep,keep)];assert gt.shape==(31,31) and gt.sum()==28
    gt_edges={(names[i],names[j]) for i,j in zip(*np.nonzero(gt))}
    old_table=ROOT/'docs/audit/step6_main_table.csv'
    step6=list(csv.DictReader(old_table.open(encoding='utf-8-sig')))
    metrics=[];global_rows=[]
    for algo,label in ALGOS.items():
        edges=matrix(ROOT/f'graphs/final/graphs/{algo}/A_dir.csv',names)
        unresolved={frozenset(e) for e in matrix(ROOT/f'graphs/final/graphs/{algo}/A_unres.csv',names)}
        row=next(x for x in step6 if x['algo']==label and x['stage']=='final')
        global_rows.append(dict(graph_id=algo,skeleton_f1=float(row['sk_F1']),strict_directed_f1=float(row['dS_F1']),
            shd=int(row['SHD_S']),confirmed_edges=int(row['n_dir']),unresolved_pairs=int(row['n_unres']),
            environment=plan['structure_environment'],temporal_projection_only=algo in {'pcmciplus','varlingam','dynotears'}))
        for task in tasks:metrics.append(dict(graph_id=algo,**task_metrics(task,edges,gt_edges,unresolved)))
    write(out/'benchmark_task_metrics.json',dict(environment=plan['structure_environment'],rows=metrics,
        definition='미확정 간선 제외. GT 경로 edge recall·완전 경로 비율·confirmed 도달성·직접XY를 별도 기록. task 선정에 사용하지 않음.'))
    write(out/'global_metrics_reused.json',dict(source_sha256=sha(old_table),rows=global_rows,recomputed=False))
    process_flow='NOT_IMPORTED'
    if args.step6_archive:
        assert sha(args.step6_archive)=='28824bc2a98acb77ce8fc5f56439ea4910f7dc9f22ed45b7d1391f7f703f6b22'
        with zipfile.ZipFile(args.step6_archive) as archive:data=archive.read('results/eval/loop_vs_flow.csv')
        assert hashlib.sha256(data).hexdigest()=='287b86c3cc2942fdb6fc98250ad0281aa159a2499fa1487eaad1d9f05b25ccd2'
        (out/'step6_loop_vs_flow_original.csv').write_bytes(data)
        process_flow='REUSED_ORIGINAL_BYTES_NOT_RECOMPUTED'

    summary_path=ROOT/'experiments/pilot/logs/normal_fit_summary.json';fit=read(summary_path)
    artifacts={};artifact_hashes={}
    for algo in plan['primary_graphs']:
        path=ROOT/f'experiments/pilot/results/{algo}__STATIC_CONFIRMED__LINEAR_RIDGE__COMMON_TARGET_ROWS_V1.json'
        if not path.exists():raise RuntimeError('EXISTING_FIT_MISSING_NO_AUTOMATIC_REFIT')
        assert sha(path)==fit['results'][algo]['artifact_sha256']
        artifact_hashes[algo]=sha(path);a=read(path)
        assert a['alpha']==fit['selected_alpha'] and a['train_rows']==[5,1199] and a['validation_rows']==[1200,1498]
        assert {(p['source'],e['target']) for e in a['equations'] for p in e['parents']}==matrix(ROOT/f'graphs/final/graphs/{algo}/A_dir.csv',names)
        artifacts[algo]=a
    first=artifacts[plan['primary_graphs'][0]]
    assert all(a['scaler_mean']==first['scaler_mean'] and a['scaler_std']==first['scaler_std'] for a in artifacts.values())
    debug_target=first['scaler_mean'][plan['target']]+plan['dry_run']['target_offset_c']
    recommendations={algo:recommend_grid(a,plan['action'],plan['target'],plan['dry_run']['delta_grid_pp'],
                        debug_target,plan['dry_run']['cost_weight']) for algo,a in artifacts.items()}
    write(out/'recommendations_dry_run.json',dict(environment=plan['structure_environment'],debug_target=debug_target,
        artifact_sha256=artifact_hashes,common_alpha=fit['selected_alpha'],new_fit=False,
        baseline='각 식의 저장된 intercept와 계수·잔차0으로 평균 전개. strict factual abduction 아님',rows=recommendations))

    # Direct benchmark→simulator performance joins must fail before any research evaluation.
    try:require_research_environment(plan['structure_environment'],plan['outcome_environment'],{})
    except ValueError as exc:gate1_rejection=str(exc)
    else:raise AssertionError('연구 Gate가 잘못 열림')
    source=plan['simulator']['source_commit']
    assert subprocess.check_output(['git','-C',str(args.source),'rev-parse','HEAD'],text=True).strip()==source
    previous=read(ROOT/'docs/research_design/track_b_evidence/source_probe.json')
    source_hashes={name:sha(args.source/name) for name in previous['source_sha256']}
    assert source_hashes==previous['source_sha256']
    sys.path.insert(0,str(args.source/'src'))
    from tep.simulator import TEPSimulator,ControlMode
    raw_dir=out/'raw';raw_dir.mkdir()
    cases=[]
    for seed in plan['simulator']['seeds']:
        for delta in plan['simulator']['predefined_delta_pp']:
            for repeat in range(plan['simulator']['repeats']):
                tag=f'seed{seed}__delta{delta:+.1f}__repeat{repeat}'
                sim=TEPSimulator(random_seed=seed,control_mode=ControlMode.MANUAL,backend='python');sim.initialize()
                assert abs(sim.dt*3600-1)<1e-12
                initial=sim.get_states().tolist();initial_rng=float(sim.process._g)
                initial_command=float(sim.get_manipulated_vars()[9]);command=initial_command+delta
                assert 0<=command<=100
                rows=[];failure=None
                for step in range(plan['simulator']['horizon_seconds']):
                    if step==plan['simulator']['action_time_seconds'] and delta!=0:sim.set_mv(10,command)
                    evaluation_seconds=float(sim.time*3600)
                    running=bool(sim.step());obs=sim.get_measurements();mv=sim.get_manipulated_vars();state=sim.get_states()
                    finite=bool(np.isfinite(state).all() and np.isfinite(obs).all())
                    row=dict(step_index=step,state_seconds=float(sim.time*3600),observation_seconds=evaluation_seconds,rng=float(sim.process._g),v10=float(state[47]),
                             step_running=running,finite=finite,idv4=int(sim.get_disturbances()[3]))
                    row.update({f'XMEAS{i+1}':float(x) for i,x in enumerate(obs)})
                    row.update({f'XMV{i+1}':float(x) for i,x in enumerate(mv)})
                    rows.append(row)
                    if not running or not finite:failure='STEP_FALSE_OR_NONFINITE';break
                path=raw_dir/f'{tag}.csv'
                with path.open('w',encoding='utf-8',newline='') as f:
                    writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
                applied=all(abs(r['XMV10']-command)<1e-12 for r in rows if r['step_index']>=plan['simulator']['action_time_seconds'])
                cases.append(dict(case=tag,seed=seed,repeat=repeat,delta_pp=delta,initial_state=initial,
                    initial_rng=initial_rng,initial_command=initial_command,applied_command=command,steps=len(rows),
                    failure=failure,command_followed=applied,raw_file='raw/'+path.name,sha256=sha(path)))
    repeat_checks=[]
    for seed in plan['simulator']['seeds']:
        for delta in plan['simulator']['predefined_delta_pp']:
            group=[x for x in cases if x['seed']==seed and x['delta_pp']==delta]
            repeat_checks.append(dict(seed=seed,delta_pp=delta,exact_raw_equal=group[0]['sha256']==group[1]['sha256']))
    technical_ok=all(x['failure'] is None and x['steps']==60 and x['command_followed'] for x in cases) and all(x['exact_raw_equal'] for x in repeat_checks)
    final=dict(protocol=plan['protocol'],classification='INDEPENDENT_TECHNICAL_PILOT_NOT_HYPOTHESIS_TEST',
        plan_sha256=sha(plan_path),python=platform.python_version(),numpy=np.__version__,
        source_commit=source,source_sha256=source_hashes,existing_fit_summary_sha256=sha(summary_path),
        gates={'G1':'BLOCKED','G2':'PASS_TECHNICAL' if technical_ok else 'FAILED_TECHNICAL',
               'G3':'PARTIAL_TECHNICAL_ONLY','G4':'NOT_RUN_RESEARCH','G5':'BLOCKED'},
        research_join_rejection=gate1_rejection,technical_ok=technical_ok,cases=cases,repeat_checks=repeat_checks,
        path_metric_rows=len(metrics),process_flow=process_flow,recommendations_executed=False,
        simulator_policies='사전 지정 baseline/+0.1pp, graph별 추천과 독립',
        clock_contract='실제 evaluate 직전/적분 직후 source 시계와 step_index를 분리',
        effect_prediction_error=None,goal_achievement=None,recovery=None,safety=None,
        metric_performance_relation=None,new_environment_adopted=False,new_fit=False)
    write(out/'summary.json',final)
    write(out/'SHA256.json',{str(p.relative_to(out)).replace('\\','/'):sha(p) for p in out.rglob('*') if p.is_file()})
    print(json.dumps(dict(technical_ok=technical_ok,gates=final['gates'],runs=len(cases),path_metric_rows=len(metrics),
                         dry_recommendations={a:r['selected']['delta_pp'] for a,r in recommendations.items()}),ensure_ascii=False))
    if not technical_ok:raise RuntimeError('TECHNICAL_CHECK_FAILED')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--step6-archive',type=Path);p.add_argument('--mode',choices=['technical','research'],default='technical')
    args=p.parse_args();args.output.mkdir(parents=True,exist_ok=False)
    try:run(args,args.output)
    except Exception as exc:
        write(args.output/'FAILURE.json',dict(status='FAILED',error_type=type(exc).__name__,message='실행 중단. 도구 console과 입력 hash를 확인. 미실행 결과는 통과 아님.'))
        raise

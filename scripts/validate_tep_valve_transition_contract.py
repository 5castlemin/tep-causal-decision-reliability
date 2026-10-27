"""Default: recompute stored evidence. --source/--output: four real Euler steps.

The old PR18 records did NOT measure applied cache c. Do not recover that
missing observation from the same equation being validated.
"""
import argparse
from copy import deepcopy
from hashlib import sha256
import json
import math
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.tep_valve_transition_contract import validate_transition
from src.tep_technical_adapter import plain

BASE=ROOT/'research_runs/tep_valve_transition'
PIN='9a6c8e5fcef4a2850778704e7793c87b0a187005'
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def digest(p):return sha256(p.read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')


def check_source(source):
    commit=subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True).strip()
    if commit!=PIN:raise ValueError('SOURCE_COMMIT_MISMATCH')
    if subprocess.check_output(['git','-C',str(source),'status','--porcelain','--untracked-files=no'],text=True).strip():
        raise ValueError('SOURCE_DIRTY')
    expected=load(ROOT/'docs/research_design/track_b_evidence/source_probe.json')['source_sha256']
    actual={p:digest(source/p) for p in expected}
    if actual!=expected:raise ValueError('SOURCE_HASH_MISMATCH')
    # Full-file pin is primary; selected line anchors expose the relevant branch.
    snippets={}
    for file,lo,hi in [('src/tep/python_backend.py',1241,1260),('src/tep/simulator.py',308,334)]:
        lines=(source/file).read_text().splitlines()
        snippets[file]=dict(start_line=lo,end_line=hi,
                            excerpt_sha256=sha256('\n'.join(lines[lo-1:hi]).encode()).hexdigest())
    return dict(commit=commit,source_sha256=actual,tracked_source_clean=True,anchors=snippets)


def execute(source,output):
    if output.exists():raise FileExistsError('Fresh output directory required')
    output.mkdir(parents=True)
    try:
        identity=check_source(source)
        plan=load(BASE/'PLAN_v1.json')
        assert digest(BASE/'PLAN_v1.json')==(BASE/'PLAN_v1.sha256').read_text().strip()
        sys.path.insert(0,str(source/'src'))
        import numpy as np
        import platform
        from tep.simulator import TEPSimulator,ControlMode
        identity.update(python=platform.python_version(),numpy=np.__version__,plan_sha256=digest(BASE/'PLAN_v1.json'))
        save(output/'SOURCE_IDENTITY.json',identity)
        rows=[]
        for arm in plan['arms']:
            sim=TEPSimulator(random_seed=plan['seed'],control_mode=ControlMode.MANUAL,backend='python');sim.initialize()
            base=float(sim.get_manipulated_vars()[9])
            captured={};original=sim.process.evaluate
            def observe(time,state):
                before=dict(cache_before_pp=float(sim.process._teproc.vcv[9]),
                            evaluated_u_pp=float(sim.process.get_xmv()[9]),v_before_pp=float(state[47]),
                            evaluation_hours=float(time),rng_before=float(sim.process._g))
                yp=original(time,state)
                captured.clear();captured.update(before)
                captured.update(applied_c_pp=float(sim.process._teproc.vcv[9]),
                    derivative_pp_per_hour=float(yp[47]),tau_hours=float(sim.process._teproc.vtau[9]),
                    ivst14=int(sim.process._teproc.ivst[9]),
                    stiction_threshold_pp=float(sim.process._teproc.vst[9]),rng_after=float(sim.process._g))
                return yp
            sim.process.evaluate=observe
            for i in range(plan['steps_per_arm']):
                requested=base+(arm['delta_pp_at_step1'] if i==1 else 0)
                sim.set_mv(10,requested)
                ctrl_before=plain(sim.controller);shutdown=bool(sim.is_shutdown())
                running=bool(sim.step());state=sim.get_states()
                row=dict(captured,arm=arm['name'],step=i,requested_u_pp=requested,
                    v_after_pp=float(state[47]),state_after_hours=float(sim.time),dt_hours=float(sim.dt),
                    dt_unit='hour',tau_unit='hour',mode='MANUAL',source_verified=True,
                    controller_overwrite=not math.isclose(requested,captured['evaluated_u_pp'],abs_tol=1e-12),
                    clipping_active=not 0<requested<100,idv=sim.get_disturbances().tolist(),
                    shutdown_before=shutdown,shutdown_after=bool(sim.is_shutdown()),step_running=running,
                    finite_state=bool(np.isfinite(state).all()),controller_before=ctrl_before,
                    controller_after=plain(sim.controller),state50=state.tolist(),
                    evidence='Actual evaluate call, not inferred applied command')
                row['comparison']=validate_transition(row,tolerance=plan['tolerance_absolute'])
                rows.append(row);save(output/'TRANSITIONS.json',rows)
                if row['comparison']['status']!='VERIFIED_NARROW_TRANSITION':raise ValueError('TRANSITION_REJECTED')
        assert len(rows)==4 and all(math.isclose(r['tau_hours']*3600,5,abs_tol=1e-12) for r in rows)
        save(output/'SUMMARY.json',dict(real_arms=2,real_euler_steps=4,fault_runs=0,all_steps_verified=True,
            max_step_error_pp=max(r['comparison']['step_absolute_error_pp'] for r in rows),
            max_derivative_error=max(r['comparison']['derivative_absolute_error'] for r in rows),
            source_modified=False,official_gt=False,global_f1=False))
        print('[PASS_LOCAL_SOURCE] two manual arms/four real Euler steps; actual cache and derivative captured; no Fault/GT/F1')
    except Exception as error:
        save(output/'FAILURE.json',dict(type=type(error).__name__,message=str(error)));raise
    finally:save(output/'SHA256.json',{p.name:digest(p) for p in sorted(output.iterdir()) if p.name!='SHA256.json'})


def reject_cases(normal):
    changes=[('stiction',{'ivst14':1},'STICTION_OR_UNKNOWN'),
      ('clipping',{'clipping_active':True},'CLIPPING_OR_BOUNDARY_UNKNOWN'),
      ('boundary_unknown',{'clipping_active':None},'CLIPPING_OR_BOUNDARY_UNKNOWN'),
      ('closed_controller',{'mode':'CLOSED_LOOP'},'CONTROLLER_MODE_UNSUPPORTED'),
      ('overwritten',{'controller_overwrite':True},'CONTROLLER_OVERWRITE_OR_UNKNOWN'),
      ('cache_unknown',{'applied_c_pp':None},'CACHE_UNKNOWN'),
      ('unit_mismatch',{'tau_unit':'second'},'TIME_UNIT_MISMATCH'),
      ('shutdown',{'shutdown_after':True},'SHUTDOWN_OR_UNKNOWN'),
      ('nonfinite',{'v_after_pp':float('nan')},'MISSING_OR_NONFINITE'),
      ('source_hash_mismatch',{'source_verified':False},'SOURCE_UNVERIFIED'),
      ('cache_wrong',{'applied_c_pp':normal['applied_c_pp']+0.01},'CACHE_RULE_MISMATCH'),
      ('clock_wrong',{'state_after_hours':9},'STATE_CLOCK_MISMATCH')]
    output=[]
    for name,update,expected in changes:
        row=deepcopy(normal);row.update(update);r=validate_transition(row)
        assert r['status']=='REJECTED' and expected in r['reasons'],name
        output.append(dict(case=name,input_kind='MOCK_ONLY_NOT_SIMULATED',changed_fields=list(update),result=r))
    return output


def validate_records():
    folder=BASE/'run_v1'
    for name,h in load(folder/'SHA256.json').items():assert digest(folder/name)==h,name
    identity=load(folder/'SOURCE_IDENTITY.json')
    assert identity['commit']==PIN and identity['source_sha256']==load(ROOT/'docs/research_design/track_b_evidence/source_probe.json')['source_sha256']
    assert digest(BASE/'PLAN_v1.json')==identity['plan_sha256']==(BASE/'PLAN_v1.sha256').read_text().strip()
    rows=load(folder/'TRANSITIONS.json')
    assert len(rows)==4
    for row in rows:
        assert len(row['state50'])==50 and all(math.isfinite(x) for x in row['state50'])
        assert row['state50'][47]==row['v_after_pp']
        assert row['controller_before']['mv_values'][9]==row['requested_u_pp']
        assert row['controller_after']['mv_values'][9]==row['evaluated_u_pp']
        assert validate_transition(row)==row['comparison']
        assert row['comparison']['status']=='VERIFIED_NARROW_TRANSITION'
        assert math.isclose(row['dt_hours']*3600,1,abs_tol=1e-12)
        assert math.isclose(row['tau_hours']*3600,5,abs_tol=1e-12)
    assert rows[0]['state50']==rows[2]['state50']
    summary=load(folder/'SUMMARY.json')
    assert summary['real_arms']==2 and summary['real_euler_steps']==4
    assert summary['max_step_error_pp']==max(r['comparison']['step_absolute_error_pp'] for r in rows)
    assert summary['max_derivative_error']==max(r['comparison']['derivative_absolute_error'] for r in rows)
    assert summary['all_steps_verified'] and summary['fault_runs']==0 and not summary['official_gt']
    # Existing PR18 manual records: algebraic relation only, cache NOT measured.
    prior=ROOT/'research_runs/tep_environment_bridge/technical_v1'
    old=[]
    for name in ('manual_reference','manual_action','manual_reference_repeat','manual_action_repeat'):
        run=load(prior/(name+'.json'));rs=[r['core'] for r in run['rows']]
        for a,b in zip(rs,rs[1:]):
            expected=a['valve10_state']+(a['xmv10_command']-a['valve10_state'])/5
            error=abs(expected-b['valve10_state']);assert error<1e-12
            old.append(dict(file=name+'.json',step=a['step'],state_seconds=a['state_seconds'],
                algebraic_error_pp=error,applied_c='NOT_RECORDED',
                full_contract='BLOCKED_CACHE_UNKNOWN',evidence_sha256=digest(prior/(name+'.json'))))
    closure_path=ROOT/'research_runs/tep_environment_bridge/closure_v1/RESULT.json'
    closure=load(closure_path)['rows'];center=closure[1]
    differences=[]
    for r in closure:
        observed=r['derivative50'][47]-center['derivative50'][47]
        expected=-r['delta_valve_state_pp']/(5/3600)
        assert math.isclose(observed,expected,abs_tol=1e-7)
        differences.append(dict(delta_v_pp=r['delta_valve_state_pp'],delta_derivative_pp_per_hour=observed,
            expected=expected,absolute_error=abs(observed-expected),cache='NOT_RECORDED',
            interpretation='existing local difference check; not applied-cache observation'))
    result=dict(old_algebraic_rechecks=old,old_fixed_point_differences=differences,
        closure_input_sha256=digest(closure_path),mock_rejections=reject_cases(rows[-1]),
        levels={'L1':'VERIFIED','L2':'PARTIAL','L3':'BLOCKED','L4':'BLOCKED'},
        actual_new_source_steps=4,new_faults=0,new_gt=False,new_discovery=0,global_f1=False)
    target=BASE/'RECHECKS.json'
    if target.exists():assert load(target)==result
    print('[PASS_RECORDS] 4 actual cache-aware steps;24 existing algebraic steps;3 existing local differences;12 mock rejection cases. No source execution in this mode.')
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path);p.add_argument('--output',type=Path)
    p.add_argument('--record',type=Path);a=p.parse_args()
    if a.source or a.output:
        if not (a.source and a.output):p.error('--source and --output together required')
        execute(a.source,a.output)
    else:
        r=validate_records()
        if a.record:
            if a.record.exists():raise FileExistsError('Fresh record required')
            save(a.record,r)

"""Execute only the predeclared six-step technical contract, external source required."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import platform
import subprocess
import sys
import traceback

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.tep_technical_adapter import run_technical_arm, fingerprint


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--source',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    if a.output.exists():raise FileExistsError('Fresh output directory required')
    a.output.mkdir(parents=True)
    def save(name,data):
        (a.output/name).write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')
    try:
        plan_path=ROOT/'research_runs/tep_environment_bridge/PLAN_v1.json'
        plan=json.loads(plan_path.read_text(encoding='utf-8'))
        plan_hash=sha256(plan_path.read_bytes()).hexdigest()
        expected=(plan_path.with_suffix('.sha256')).read_text().strip()
        if plan_hash!=expected:raise ValueError('Plan hash mismatch')
        pin=plan['source_commit']
        commit=subprocess.check_output(['git','-C',str(a.source),'rev-parse','HEAD'],text=True).strip()
        if commit!=pin:raise ValueError('Source commit mismatch')
        dirty=subprocess.check_output(['git','-C',str(a.source),'status','--porcelain','--untracked-files=no'],text=True)
        if dirty.strip():raise ValueError('External tracked source changed')
        prior=json.loads((ROOT/'docs/research_design/track_b_evidence/source_probe.json').read_text())
        files={name:sha256((a.source/name).read_bytes()).hexdigest() for name in prior['source_sha256']}
        if files!=prior['source_sha256']:raise ValueError('Pinned file hash mismatch')
        all_py=sorted((a.source/'src/tep').rglob('*.py'))
        source_hashes={x.relative_to(a.source).as_posix():sha256(x.read_bytes()).hexdigest() for x in all_py}
        save('EXECUTION_IDENTITY.json',dict(source_commit=commit,source_sha256=source_hashes,
             pinned_four_match=True,python=platform.python_version(),plan_sha256=plan_hash,
             scope='TECHNICAL_ONLY_NOT_TRAINING_OR_EFFECT_ESTIMATION'))
        sys.path.insert(0,str(a.source/'src'))
        import numpy as np
        from tep.simulator import TEPSimulator,ControlMode
        from tep.constants import MEASUREMENT_NAMES,MEASUREMENT_UNITS,MANIPULATED_VAR_NAMES
        def factory(mode,seed):
            return TEPSimulator(random_seed=seed,control_mode=getattr(ControlMode,mode),backend='python')
        runs={}
        for arm in plan['arms']:
            run=run_technical_arm(factory,mode=arm['mode'],seed=plan['seed'],
                  delta_pp=arm['delta_pp'],steps=plan['steps'],observe_rng=arm['observe_rng'])
            save(arm['name']+'.json',run)
            runs[arm['name']]=run
            print(arm['name'],run['status'],run['steps_completed'],flush=True)
        core=lambda name:[r['core'] for r in runs[name]['rows'] if 'core' in r]
        checks={}
        for name in ('manual_reference','manual_action','closed_reference','closed_action'):
            checks[name+'_uninstrumented_repeat_exact']=core(name)==core(name+'_repeat')
        for mode in ('manual','closed'):
            base,act=runs[mode+'_reference'],runs[mode+'_action']
            b,c=core(mode+'_reference'),core(mode+'_action')
            checks[mode+'_fresh_initial_equal']=base['initialization_sha256']==act['initialization_sha256']
            checks[mode+'_clock_equal']=[(r['state_seconds'],r['sensor_evaluation_seconds']) for r in b]==[(r['state_seconds'],r['sensor_evaluation_seconds']) for r in c]
            checks[mode+'_rng_call_counts_equal']=[r['rng_calls_cumulative'] for r in base['rows']]==[r['rng_calls_cumulative'] for r in act['rows']]
            checks[mode+'_rng_draw_sequences_equal']=[r['rng_draw_sequence_sha256'] for r in base['rows']]==[r['rng_draw_sequence_sha256'] for r in act['rows']]
        checks['manual_command_held']=all(r['xmv10_command']==runs['manual_action']['requested_command'] for r in core('manual_action'))
        checks['manual_command_not_valve_at_t0']=core('manual_action')[0]['xmv10_command']!=core('manual_action')[0]['valve10_state']
        checks['closed_external_command_overwritten']=core('closed_action')[1]['xmv10_command']!=runs['closed_action']['requested_command']
        checks['sensor_clock_lags_integrated_state']=all(abs(r['state_seconds']-r['sensor_evaluation_seconds']-1)<1e-12 for n in runs for r in core(n)[1:])
        checks['all_arms_finite_no_shutdown']=all(r['failure'] is None for r in runs.values())
        summary=dict(checks=checks,all_checks_pass=all(checks.values()),runs=len(runs),
             integration_steps=sum(r['steps_completed'] for r in runs.values()),
             baseline_manual_xmv10_range=float(np.ptp([r['xmv10_command'] for r in core('manual_reference')])),
             sensor_delta_last_xmeas9=core('manual_action')[-1]['xmeas9']-core('manual_reference')[-1]['xmeas9'],
             numpy=np.__version__,same_seed_general_noise_guarantee=False,
             noise_alignment_scope='Observed RNG call sequences of these six-step no-fault pairs only',
             training_holdout_generated=False,new_reference_gt=False,recovery_safety='NOT_RUN',
             structure_effect_research='NO-GO_REFERENCE_UNRESOLVED')
        save('VARIABLE_SCHEMA.json',dict(measurements=MEASUREMENT_NAMES,units=MEASUREMENT_UNITS,
             manipulated_names=MANIPULATED_VAR_NAMES,command_unit='percent command, not actual flow',
             internal_diagnostics=dict(valve10_state='yy47 percent',coolant_state36='yy36 degC',
                  energy_state8='yy8 model energy coordinate; not temperature'),
             clock='cache from evaluate(t,state_t); returned state_t+dt; initialization both t0'))
        save('SUMMARY.json',summary)
        if not summary['all_checks_pass']:raise AssertionError('Technical checks failed; raw preserved')
    except Exception as e:
        save('FAILURE.json',dict(status='FAIL_OR_BLOCKED',error_type=type(e).__name__,message=str(e),
                                  traceback=traceback.format_exc().replace(str(a.source),'<external-source>')))
        raise
    finally:
        save('SHA256.json',{x.name:sha256(x.read_bytes()).hexdigest() for x in sorted(a.output.iterdir()) if x.name!='SHA256.json'})


if __name__=='__main__':main()

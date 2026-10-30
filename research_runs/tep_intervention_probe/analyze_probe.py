"""Describe one technical intervention pair; not an identified mean effect."""
from pathlib import Path
import hashlib,json,re
import numpy as np
import pandas as pd

def main():
    out=Path('research_runs/tep_intervention_probe');raw=Path('data/local/tep_intervention_probe/run_v1')
    contract=json.loads((out/'TASK_CONTRACT.json').read_text())
    a,b=[np.loadtxt(raw/f'probe_{i}_simout.csv',delimiter=',') for i in (0,1)]
    t0,t=[np.loadtxt(raw/f'probe_{i}_tout.csv',delimiter=',').ravel() for i in (0,1)]
    assert np.max(np.abs(t-t0))<1e-12
    u0,u1=[np.loadtxt(raw/f'probe_{i}_xmv.csv',delimiter=',') for i in (0,1)]
    g0,g1=[np.loadtxt(raw/f'probe_{i}_guard.csv',delimiter=',') for i in (0,1)]
    assert np.all(np.diff(g0[:,0])>=0) and np.all(np.diff(g1[:,0])>=0)
    j=np.maximum(0,np.searchsorted(g0[:,0],g1[:,0],side='right')-1)
    pulse=(g1[:,0]>.05+1e-9)&(g1[:,0]<.1-1e-9)
    # CSV schema: time,41 sensors,12 cached commands,50 physical states,guard.
    command=g1[:,51] # time +41 + command10 zero-based index9
    valve=g1[:,101] # physical state index47: actual valve10, not cache
    summary={'type':'SINGLE_PAIR_ASSUMPTION_BASED_TECHNICAL_PROBE','original_effect_gate':'NOT_PASSED',
     'same_seed_common_noise':'NOT_VERIFIED, action can change adaptive solver/RNG call ordering',
     'end_hours':[float(g0[-1,0]),float(g1[-1,0])],
     'max_guard':[float(g0[:,-1].max()),float(g1[:,-1].max())],
     'max_pulse_cache_error_percent':float(np.abs(command[pulse]-contract['value_percent']).max()),
     'max_actual_valve_difference_percent':float(np.abs(valve-g0[j,101]).max()),
     'valve_comparison_clock':'baseline last major output held at intervention major times; may differ in solver grids',
     'max_controller_command_difference_percent':float(np.abs(u1[:,9]-u0[:,9]).max()),
     'pre_pulse_sensor_max_abs':float(np.abs(b[t<.05]-a[t<.05]).max()),
     'temperature_difference_intervention_minus_baseline_degC':{},
     'numerical_effect_vs_noise':'one pair cannot separate policy mean effect from measurement/process noise differences; no CI or ATE',
     'SCM_prediction':'NOT_RUN: observational identification and same-environment contract remain unverified',
     'graph_metric_comparison':'NOT_RUN: no modeled predictions/selection losses; no metric superiority inference',
     'safety_scope':'same native shutdown, sensor bounds, command0..100 and all50 states finite; not certified industrial safety',
     'runs':re.findall(r'PROBE=([^\r\n]+)',(raw/'probe.log').read_text(encoding='utf8',errors='replace'))}
    for name,m in [('pulse',(t>=.05)&(t<.1)),('post',(t>=.1)),('all',np.ones(t.shape,dtype=bool))]:
        d=b[m,8]-a[m,8];summary['temperature_difference_intervention_minus_baseline_degC'][name]={'mean':float(d.mean()),'min':float(d.min()),'max':float(d.max())}
    pd.DataFrame({'time_hours':t,'baseline_temperature_degC':a[:,8],'intervention_temperature_degC':b[:,8],
      'difference_degC':b[:,8]-a[:,8],'baseline_controller_command10_percent':u0[:,9],
      'intervention_controller_command10_percent':u1[:,9]}).to_csv(out/'RESPONSE_DIAGNOSTIC.csv',index=False)
    summary['raw_artifacts']=[{'path':p.as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(raw.iterdir()) if p.is_file()]
    summary['reproduction_scripts']=[{'path':p.as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(out.glob('*.m'))]
    summary['runner_version_note']='Current reproduction scripts include post-run refusal to overwrite existing trajectories; process/controller equations unchanged. Failed dimension attempts retained in raw logs; exact earlier runner hashes were not separately captured.'
    summary['commands']=['matlab -batch "addpath(<absolute dynamics runner path>);addpath(<absolute probe runner path>);run_probe(<fresh isolated model directory>,<absolute TASK_CONTRACT.json>)"']
    (out/'RESULT.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:v for k,v in summary.items() if k!='raw_artifacts'},indent=2))

if __name__=='__main__':main()

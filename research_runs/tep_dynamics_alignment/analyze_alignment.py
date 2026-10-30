"""Reanalyze saved raw trajectories; no simulator calls or fitted models."""
from pathlib import Path
import hashlib,json,re
import numpy as np
import pandas as pd

OUT=Path('research_runs/tep_dynamics_alignment')
RAW=Path('data/local/tep_dynamics_alignment/run_v1')

def sampled(data,t,mode='hold'):
    # Select last emitted value at duplicate times, then sort by time.
    _,rev=np.unique(data[::-1,0],return_index=True)
    a=data[np.sort(len(data)-1-rev)]
    a=a[np.argsort(a[:,0],kind='stable')]
    if mode=='linear':return np.column_stack([np.interp(t,a[:,0],a[:,i]) for i in range(1,54)])
    return a[np.maximum(0,np.searchsorted(a[:,0],t,side='right')-1),1:54]

def main():
    early=[]
    for run,seed in [(1,None),(2,24121989),(3,12101992)]:
        z=np.load(f'data/local/tep_original_data_recovery/normal_{run}.npz')
        name='A3.csv' if seed is None else f'seed_{seed}.csv'
        a=np.loadtxt(Path('data/local/tep_official_validation/run_v1')/name,delimiter=',')
        t=z['TOUT'].ravel();m=t<=6+1e-9;t=t[m]
        o=np.column_stack([z['SIMOUT'][m,:41],z['XMV'][m]])
        held=sampled(a,t);linear=sampled(a,t,'linear')
        for i in range(53):
            ix=np.flatnonzero(np.abs(o[:,i]-held[:,i])>1e-6)
            early.append({'run':run,'variable':f'XMEAS{i+1}' if i<41 else f'XMV{i-40}',
              'first_difference_seconds':float(t[ix[0]]*3600) if len(ix) else None,
              'threshold':'1e-6 native unit diagnostic, not noise/significance threshold',
              'original_t0':o[0,i],'cache_or_sensor_t0':held[0,i],
              'original_at10s':o[1,i],'held_at10s':held[1,i],'linear_at10s':linear[1,i],
              'max_held_linear_gap':np.abs(held[:,i]-linear[:,i]).max(),
              'phase_warning':'command cache at outputs is not same event as original controller ToWorkspace; t0 cache differs'})
    pd.DataFrame(early).to_csv(OUT/'FIRST_DIVERGENCE.csv',index=False)
    ref=np.loadtxt(RAW/'reference_observer.csv',delimiter=',')
    mon=np.loadtxt(RAW/'monitored_observer.csv',delimiter=',')
    monitor={'shape_reference':list(ref.shape),'shape_monitored':list(mon.shape),
      'max_abs':float(np.max(np.abs(ref-mon))) if ref.shape==mon.shape else None,
      'scope':'60s native outputs41 and input40 at same PostOutputs callback; internal states not observed in reference',
      'injected_stop':float(np.loadtxt(RAW/'inject_observer.csv',delimiter=',')[:,-1].max())}
    results=[];z=np.load('data/local/tep_original_data_recovery/normal_1.npz')
    for label in ['f0_s36','f225_s36','f0_s10','f225_s10']:
        t=np.loadtxt(RAW/f'{label}_tout.csv',delimiter=',').ravel()
        y=np.loadtxt(RAW/f'{label}_simout.csv',delimiter=',');u=np.loadtxt(RAW/f'{label}_xmv.csv',delimiter=',')
        original_y=np.column_stack([np.interp(t,z['TOUT'].ravel(),z['SIMOUT'][:,i]) for i in range(y.shape[1])])
        original_u=np.column_stack([np.interp(t,z['TOUT'].ravel(),z['XMV'][:,i]) for i in range(12)])
        for i in range(y.shape[1]+12):
            a,b=(y[:,i],original_y[:,i]) if i<y.shape[1] else (u[:,i-y.shape[1]],original_u[:,i-y.shape[1]])
            difference=np.abs(a-b);ix=np.flatnonzero(difference>1e-6)
            results.append({'condition':label,'variable':f'XMEAS{i+1}' if i<y.shape[1] else f'XMV{i-y.shape[1]+1}',
              'max_abs':difference.max(),'mae':difference.mean(),
              'first_difference_seconds':float(t[ix[0]]*3600) if len(ix) else None,
              'comparison':'direct shared10s grid' if label.endswith('s10') else 'original interpolated to36s, diagnostic only'})
    pd.DataFrame(results).to_csv(OUT/'FACTORIAL_COMPARISON.csv',index=False)
    t36=np.loadtxt(RAW/'f225_s36_tout.csv',delimiter=',').ravel()
    t10=np.loadtxt(RAW/'f225_s10_tout.csv',delimiter=',').ravel()
    common,i36,i10=np.intersect1d(np.round(t36,12),np.round(t10,12),return_indices=True)
    y36=np.loadtxt(RAW/'f225_s36_simout.csv',delimiter=',')[i36]
    y10=np.loadtxt(RAW/'f225_s10_simout.csv',delimiter=',')[i10]
    clock={'same_flags_seed_and_equations':True,'common_seconds':(common*3600).tolist(),
      'interpolation':False,'max_gap_pressure_kPa':float(np.abs(y36[:,6]-y10[:,6]).max()),
      'max_gap_X20_kW':float(np.abs(y36[:,19]-y10[:,19]).max()),
      'max_gap_X21_degC':float(np.abs(y36[:,20]-y10[:,20]).max()),
      'interpretation':'Changing active save clock alters trajectory, not only retrospective interpolation. RNG callback mechanism supported by source; individual callback stream not independently instrumented.'}
    (OUT/'CLOCK_DIAGNOSTIC.json').write_text(json.dumps(clock,indent=2)+'\n',encoding='utf8')
    extension=RAW/'f225_s10_30min_simout.csv'
    if extension.exists():
        y=np.loadtxt(extension,delimiter=',');u=np.loadtxt(RAW/'f225_s10_30min_xmv.csv',delimiter=',')
        t=np.loadtxt(RAW/'f225_s10_30min_tout.csv',delimiter=',').ravel()
        assert np.max(np.abs(t-z['TOUT'][:len(t)].ravel()))<1e-10
        e=[]
        for i in range(73):
            delta=np.abs(y[:,i]-z['SIMOUT'][:len(t),i]);ix=np.flatnonzero(delta>1e-6)
            e.append({'variable':f'XMEAS{i+1}','max_abs':delta.max(),'mae':delta.mean(),
              'first_difference_seconds':float(t[ix[0]]*3600) if len(ix) else None})
        for i in range(12):
            delta=np.abs(u[:,i]-z['XMV'][:len(t),i]);ix=np.flatnonzero(delta>1e-6)
            e.append({'variable':f'XMV{i+1}','max_abs':delta.max(),'mae':delta.mean(),
              'first_difference_seconds':float(t[ix[0]]*3600) if len(ix) else None})
        pd.DataFrame(e).to_csv(OUT/'EXTENSION_30MIN_COMPARISON.csv',index=False)
    artifacts=[{'path':p.as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(RAW.iterdir()) if p.is_file()]
    log=(RAW/'alignment.log').read_text(encoding='utf8',errors='replace')
    summary={'monitor':monitor,'runs':re.findall(r'RUN=([^\r\n]+)',log),'compile_failures':log.count('ERROR='),
      'artifacts':artifacts,'historical_initial_command_check':
      'Manca t0 XMV matches previous model cache at1.8s to floating tolerance, not initial cache at0s',
      'independence':'factorial runs share one topology and initial seed, not independent process samples'}
    summary['reproduction_scripts']=[{'path':p.as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(OUT.glob('*.m'))]
    summary['runner_version_note']='Current reproduction scripts include post-run refusal to overwrite existing trajectories; process/controller equations unchanged. Failed dimension attempts retained in raw logs; exact earlier runner hashes were not separately captured.'
    summary['commands']=['matlab -batch "addpath(<absolute research_runs/tep_dynamics_alignment>);run_alignment(<fresh isolated model directory>)"']
    (OUT/'RUN_RESULTS.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf8')
    print(json.dumps(monitor,indent=2));print(pd.DataFrame(results).query('variable in ["XMEAS7","XMEAS20","XMEAS21"]')[['condition','variable','max_abs','mae','first_difference_seconds']].to_string(index=False))

if __name__=='__main__':main()

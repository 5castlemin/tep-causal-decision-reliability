"""Bounded isolated TEP observation diagnostic. No interventions or training."""
import dataclasses,json,time,traceback
from pathlib import Path
import numpy as np
from tep_studio.simulation.core import TennesseeEastmanProcess
from tep_studio.control.controller import RickerMultiLoopController

out=Path('tep_operating_output');out.mkdir(exist_ok=True)
expected={'A':np.array([2705.966905570086,74.62374791713786,120.39914610371079]),'B':np.array([2615.105063423149,62.32490995879087,122.89255457683878])}
summary=[]
def save(): (out/'results.json').write_text(json.dumps(summary,indent=2,allow_nan=False),encoding='utf8')
try:
 for horizon in (2,6,24):
  for condition in ('A','B'):
   started=time.monotonic();controller=RickerMultiLoopController();p=TennesseeEastmanProcess();meas,_=p.reset(mode='mode1',seed=465120799)
   if condition=='B':
    controller.reset(meas,time=0.0);controller.setpoints=dataclasses.replace(controller.setpoints,reactor_pressure=2800.,reactor_level=65.,reactor_temperature=122.9)
   controller.reset(meas,time=0.0); initial=meas.copy(); steps=round(horizon/.0005); records=[]; pv_sum=np.zeros(3); min_margin=float('inf'); saturation=np.zeros(12,dtype=int);stop=None
   try:
    for i in range(steps):
     action,diag=controller.compute_action(meas,time=p.time)
     if not np.isfinite(action).all() or np.any(action<0) or np.any(action>100): raise RuntimeError('illegal or nonfinite action')
     res=p.advance(action,control_interval=.0005);meas=res.measurements
     if not np.isfinite(meas).all() or not np.isfinite(res.state).all():raise RuntimeError('nonfinite output or state')
     pv_sum+=meas[[6,7,8]];min_margin=min(min_margin,min(res.constraint_margins.values()));saturation+=(action<=1e-9)|(action>=100-1e-9)
     if i%6==0 or i==steps-1 or res.shutdown_status['terminated'] or min_margin<=0:records.append((res.time,meas.copy(),res.implemented_action.copy(),res.state.copy(),diag.ratios['r5'],diag.fp))
     if res.shutdown_status['terminated'] or min_margin<=0:raise RuntimeError('shutdown or terminal constraint violation: '+str(res.shutdown_status))
   except Exception as exc:stop=str(exc)
   if records:
    np.savez_compressed(out/f'{condition}_{horizon}h.npz',time=np.array([r[0] for r in records]),measurements=np.array([r[1] for r in records]),actions=np.array([r[2] for r in records]),states=np.array([r[3] for r in records]),r5=np.array([r[4] for r in records]),fp=np.array([r[5] for r in records]))
   n=i+1;mean=pv_sum/n
   replay=bool(np.all(np.abs(mean-expected[condition])<=1e-6)) if horizon==2 and not stop else None
   row={'condition':condition,'horizon_h':horizon,'reached_h':float(p.time),'steps':n,'stop':stop,'initial_X7_X8_X9':initial[[6,7,8]].tolist(),'mean_X7_X8_X9':mean.tolist(),'final_X7_X8_X9':meas[[6,7,8]].tolist(),'minimum_constraint_margin_mixed_units':min_margin,'action_saturation_fraction':(saturation/n).tolist(),'setpoints':dataclasses.asdict(controller.setpoints),'replay_previous_2h':replay,'seconds':time.monotonic()-started}
   summary.append(row);save();print('RUN_RESULT '+json.dumps(row),flush=True)
   if stop or replay is False: raise RuntimeError('stopping all subsequent horizons')
except Exception:
 (out/'error.txt').write_text(traceback.format_exc(),encoding='utf8'); print(traceback.format_exc(),flush=True);raise

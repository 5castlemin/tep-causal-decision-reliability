"""Run pinned TEP Studio technical probes in an isolated Linux runner.
No research inference, fitting or interventions. Each run has a fresh process.
"""
import dataclasses, json, time, traceback
from pathlib import Path
import numpy as np
from tep_studio.simulation.core import TennesseeEastmanProcess
from tep_studio.control.controller import RickerMultiLoopController
from tep_studio.control.runner import ClosedLoopSimulation

out = Path('tep_probe_output'); out.mkdir(exist_ok=True)
records = []
try:
    for horizon in (0.1665, 0.5, 2.0):
        for condition in ('A', 'B'):
            started = time.monotonic()
            controller = RickerMultiLoopController()
            if condition == 'B':
                init = TennesseeEastmanProcess()
                measurement, _ = init.reset(mode='mode1', seed=465120799)
                controller.reset(measurement, time=init.time)
                controller.setpoints = dataclasses.replace(controller.setpoints, reactor_pressure=2800., reactor_level=65., reactor_temperature=122.9)
            process = TennesseeEastmanProcess()
            result = ClosedLoopSimulation(simulator=process, controller=controller, control_interval=.0005, horizon=horizon).run(seed=465120799, mode='mode1', record_every=1)
            m = np.array([x.measurements for x in result.results]); u = np.array([x.implemented_action for x in result.results]); t = np.array([x.time_end for x in result.results])
            finite = bool(np.isfinite(m).all() and np.isfinite(u).all() and np.isfinite(t).all())
            np.savez_compressed(out / f'{condition}_{horizon}.npz', t=t, measurements=m, actions=u)
            row = {'condition':condition,'horizon_hours':horizon,'time_final_hours':result.final_time,'n_steps':result.n_steps,'shutdown':result.terminated,'finite':finite,'runtime_seconds':time.monotonic()-started,'setpoints':dataclasses.asdict(controller.setpoints),'pressure_level_temperature_mean':m[:,[6,7,8]].mean(axis=0).tolist(),'pressure_level_temperature_final':m[-1,[6,7,8]].tolist()}
            records.append(row); print('PROBE_RESULT '+json.dumps(row), flush=True)
            (out/'results.json').write_text(json.dumps(records,indent=2),encoding='utf8')
            if result.terminated or not finite: raise RuntimeError('stop gate: shutdown or nonfinite')
except Exception:
    (out/'error.txt').write_text(traceback.format_exc(),encoding='utf8')
    print(traceback.format_exc(), flush=True)
    raise

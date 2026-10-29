"""Read-only diagnostics around the pinned external TEP; no GT/effect certifier.

Private-state access is deliberate and pin-specific. State and cached sensor
timestamps stay separate. A draw observer returns each original RNG draw
unchanged; an uninstrumented repeat checks that observation did not affect it.
"""
from hashlib import sha256
import json


def plain(value):
    if hasattr(value, 'tolist'):
        return value.tolist()
    if isinstance(value, dict):
        return {str(k):plain(v) for k,v in value.items()}
    if isinstance(value, (list,tuple)):
        return [plain(v) for v in value]
    if hasattr(value, '__dict__'):
        return plain(vars(value))
    if value is None or isinstance(value, (str,int,float,bool)):
        return value
    raise TypeError(f'Unsupported diagnostic value type {type(value).__name__}')


def fingerprint(value):
    return sha256(json.dumps(plain(value),sort_keys=True,allow_nan=False,
                             separators=(',', ':')).encode()).hexdigest()


def run_technical_arm(factory, *, mode, seed, delta_pp, steps=6, observe_rng=True):
    """Returns raw diagnostics; no post-step evaluate call (would consume noise)."""
    import numpy as np
    sim=factory(mode,seed)
    sim.initialize()
    initial=dict(state=plain(sim.get_states()),sensor=plain(sim.get_measurements()),
                 command=plain(sim.get_manipulated_vars()),rng=float(sim.process._g),
                 controller=plain(sim.controller),idv=plain(sim.process._idv))
    start_fingerprint=fingerprint(initial)
    draws=[]
    if observe_rng:
        original=sim.process._tesub7
        def draw(i):
            value=original(i)
            draws.append((int(i),float(value)))
            return value
        sim.process._tesub7=draw
    command=float(sim.get_manipulated_vars()[9])+delta_pp
    sim.set_mv(10,command)
    rows=[]
    failure=None
    for index in range(steps+1):
        state=sim.get_states();sensor=sim.get_measurements();mv=sim.get_manipulated_vars()
        core=dict(step=index,state_seconds=float(sim.time*3600),
                  sensor_evaluation_seconds=0.0 if index==0 else float((sim.time-sim.dt)*3600),
                  xmv10_command=float(mv[9]),valve10_state=float(state[47]),
                  coolant_state36=float(state[36]),energy_state8=float(state[8]),
                  xmeas9=float(sensor[8]),xmeas21=float(sensor[20]),
                  state=plain(state),measurements=plain(sensor),commands=plain(mv),
                  rng=float(sim.process._g),controller=plain(sim.controller),
                  idv=plain(sim.process._idv),shutdown=bool(sim.is_shutdown()),
                  finite=bool(np.isfinite(state).all() and np.isfinite(sensor).all() and np.isfinite(mv).all()))
        rows.append(dict(core=core,rng_calls_cumulative=len(draws) if observe_rng else None,
                         rng_draw_sequence_sha256=fingerprint(draws) if observe_rng else None))
        if not core['finite'] or core['shutdown']:
            failure='NONFINITE_OR_SHUTDOWN';break
        if index==steps:break
        if not sim.step():
            # Do not lose terminal internal state on a failed step.
            failure='STEP_RETURNED_FALSE'
            rows.append(dict(terminal_failure=dict(state=plain(sim.get_states()),
                measurements=plain(sim.get_measurements()),time_seconds=float(sim.time*3600),
                shutdown=bool(sim.is_shutdown()),rng=float(sim.process._g))))
            break
    return dict(mode=mode,seed=seed,delta_pp=delta_pp,requested_command=command,
                initialization=initial,initialization_sha256=start_fingerprint,
                steps_requested=steps,steps_completed=int(sim.step_count),rows=rows,
                failure=failure,status='PASS_TECHNICAL_ONLY' if failure is None else 'FAIL',
                observation_training_data=False,independent_effect_evaluation=False,
                reference_graph_generated=False)

"""Bounded, paired normal-operation diagnostic; never a TEP equivalence claim."""
import argparse, hashlib, json, sys, time
from pathlib import Path
import numpy as np

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--source',required=True,type=Path);ap.add_argument('--output',required=True,type=Path)
    args=ap.parse_args(); root=Path(__file__).resolve().parents[1]
    if args.output.exists():raise FileExistsError('fresh output required')
    record=json.loads((root/'docs/research_design/track_b_evidence/source_probe.json').read_text())
    for name,h in record['source_sha256'].items():
        assert hashlib.sha256((args.source/name).read_bytes()).hexdigest()==h, name
    sys.path.insert(0,str(args.source/'src'))
    from tep.simulator import TEPSimulator, ControlMode
    args.output.mkdir(parents=True)
    runs=[]
    for variant in ('default','documented_setpoints'):
        t=time.monotonic(); sim=TEPSimulator(random_seed=465120799,control_mode=ControlMode.CLOSED_LOOP,backend='python');sim.initialize()
        if variant=='documented_setpoints':
            sim.controller.ctrl17.setpoint=65.0;sim.controller.ctrl18.setpoint=122.9
        rows=[];error=None
        for step in range(601):
            m=sim.get_measurements();u=sim.get_manipulated_vars()
            rows.append({'seconds':step,'measurements':m.tolist(),'commands':u.tolist(),'shutdown':bool(sim.is_shutdown())})
            if sim.is_shutdown() or not np.isfinite(m).all() or not np.isfinite(u).all():error='SHUTDOWN_OR_NONFINITE';break
            if step<600 and not sim.step():error='STEP_RETURNED_FALSE';break
        z={'variant':variant,'seed':465120799,'seconds_requested':600,'seconds_completed':rows[-1]['seconds'],
           'level_setpoint':float(sim.controller.ctrl17.setpoint),'temperature_setpoint':float(sim.controller.ctrl18.setpoint),
           'pressure_setpoint':'NO_EQUIVALENT_IDENTIFIED','wall_seconds':time.monotonic()-t,'failure':error,'rows':rows}
        path=args.output/(variant+'.json');path.write_text(json.dumps(z,indent=2,allow_nan=False)+'\n',encoding='utf-8');runs.append(z)
        if error:break
    print(json.dumps({'completed':len(runs),'durations':[r['seconds_completed'] for r in runs], 'failures':[r['failure'] for r in runs]}))

if __name__=='__main__':main()

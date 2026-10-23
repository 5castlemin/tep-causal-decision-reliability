"""Pinned-source numerical/reset experiments; read-only upstream source."""
import argparse
import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path

import numpy as np

COMMIT = "9a6c8e5fcef4a2850778704e7793c87b0a187005"


def serial(x):
    if isinstance(x, np.ndarray):
        return x.tolist()
    if isinstance(x, np.generic):
        return x.item()
    if isinstance(x, dict):
        return {k: serial(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [serial(v) for v in x]
    if hasattr(x, "__dict__"):
        return serial(vars(x))
    return x


def snapshot(sim):
    p = sim.process
    return serial(dict(time=sim.time, step_count=sim.step_count, yy=sim.get_states(),
                       xmeas=sim.get_measurements(), xmv=sim.get_manipulated_vars(),
                       rng=p._g, idv=p._idv, cache=p._teproc, walk=p._wlk,
                       controller=vars(sim.controller)))


def diff(a, b, prefix=""):
    if isinstance(a, dict) and isinstance(b, dict):
        out = {}
        for key in a:
            out.update(diff(a[key], b[key], prefix + "." + key))
        return out
    try:
        aa, bb = np.asarray(a), np.asarray(b)
        if np.array_equal(aa, bb):
            return {}
        return {prefix: dict(max_abs=float(np.max(np.abs(aa.astype(float)-bb.astype(float)))))}
    except (TypeError, ValueError):
        return {} if a == b else {prefix: dict(changed=True)}


def observation(sim):
    p, tp = sim.process, sim.process._teproc
    values = [float((tp.ptr-760)/760*101.325), float(tp.tcr), float(tp.vlr/35.3145),
              float(tp.vls/35.3145), float(tp.vlc/35.3145)]
    pressure, temp, reactor, separator, stripper = values
    flags = dict(pressure_high=pressure>3000, temperature_high=temp>175,
                 reactor_high=reactor>24, reactor_low=reactor<2,
                 separator_high=separator>12, separator_low=separator<1,
                 stripper_high=stripper>8, stripper_low=stripper<1)
    return dict(state_seconds=float(sim.time*3600), observation_seconds=float(p.time*3600),
                physical=values, flags=flags, shutdown=bool(sim.is_shutdown()),
                backend_shutdown=bool(p._shutdown), finite_state=bool(np.isfinite(sim.get_states()).all()),
                finite_derivative=bool(np.isfinite(p.yp).all()), rng=float(p._g))


def save_csv(path, rows):
    header = ["state_seconds", "observation_seconds"]+[f"XMEAS{i}" for i in range(1,42)]+[f"XMV{i}" for i in range(1,13)]+[f"state{i}" for i in range(1,51)]
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        np.savetxt(handle, np.asarray(rows), delimiter=",", header=",".join(header), comments="")


def run(sim, dt, delta, seconds, name, out):
    sim.dt = dt/3600
    initial = sim.get_states().copy()
    initial_mv = float(sim.get_manipulated_vars()[9])
    rows, terminals, approach = [], [], None
    for step in range(round(seconds/dt)+1):
        elapsed = step*dt
        if elapsed == 600 and delta:
            sim.set_mv(10, initial_mv+delta)
        obs = observation(sim)
        # Save both clock grids without an extra model evaluation/RNG draw.
        if elapsed % 30 == 0 or (step > 0 and ((step-1)*dt) % 30 == 0) or obs["shutdown"]:
            rows.append(np.r_[sim.time*3600,sim.process.time*3600,sim.get_measurements(),sim.get_manipulated_vars(),sim.get_states()])
        if elapsed >= 1500 or obs["shutdown"]:
            if elapsed % 1 == 0 or obs["shutdown"]:
                terminals.append(obs)
        if approach is None and any([obs["physical"][2]<2.2,obs["physical"][3]<1.1,obs["physical"][4]<1.1,obs["physical"][0]>2850,obs["physical"][1]>166.25]):
            approach=obs
        if obs["shutdown"] or elapsed == seconds:
            break
        running = sim.step()
        if not running and not sim.is_shutdown():
            raise RuntimeError("non-shutdown solver failure")
    save_csv(out/(name+".csv"),rows)
    (out/(name+"_terminal.json")).write_text(json.dumps(terminals,indent=2),encoding="utf-8")
    return dict(terminal=observation(sim), approach=approach, initial_state=initial.tolist(), rows=len(rows))


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--source",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    if subprocess.check_output(["git","-C",str(args.source),"rev-parse","HEAD"],text=True).strip()!=COMMIT:
        raise ValueError("source commit mismatch")
    if args.output.exists():
        raise FileExistsError("output exists")
    out=args.output;out.mkdir(parents=True)
    plan=dict(source_commit=COMMIT,seed=42,backend="python",solver="upstream Euler sim.dt",dt_seconds=[1,.5,.25],
              horizon_seconds=1800,intervention_seconds=600,mv10_delta_percentage_points=[0,1],mode="MANUAL",
              noise_conditions=["upstream","zero_xns_diagnostic"],record_seconds=30,
              recording_rule="state and original evaluation 30-second grids; no extra evaluate call",
              noise_note="dt 변경은 RNG 소비도 변경한다. zero_xns는 관측 잡음 표준편차만 실행 중 0으로 설정하며 원본 source 수정과 Fault 주입은 없다.",
              convergence_policy="report 1->.5 and .5->.25 differences; no arbitrary accuracy PASS",
              reset_plan=["fresh twins","initialize twice","run60->initialize","IDV4 run600->clear->initialize"],
              supplemental_closed_normal_seconds=7200,
              physical_thresholds=dict(pressure_kpa=3000,temperature_degC=175,reactor_m3=[2,24],separator_m3=[1,12],stripper_m3=[1,8]))
    (out/"plan.json").write_text(json.dumps(plan,ensure_ascii=False,indent=2),encoding="utf-8")
    sys.path.insert(0,str(args.source/"src"))
    from tep import TEPSimulator,ControlMode,is_fortran_available
    def new(mode=ControlMode.MANUAL):
        sim=TEPSimulator(random_seed=42,control_mode=mode,backend="python");sim.initialize();return sim
    results={}
    for noise in ("upstream","zero_xns_diagnostic"):
        for dt in (1,.5,.25):
            for delta in (0,1):
                sim=new()
                if noise!="upstream":
                    sim.process._teproc.xns.fill(0)
                name=f"{noise}_dt{dt}_delta{delta}"
                results[name]=run(sim,dt,delta,1800,name,out)
                print(name,results[name]["terminal"],flush=True)
    results["closed_normal_7200"]=run(new(ControlMode.CLOSED_LOOP),1,0,7200,"closed_normal_7200",out)
    resets={}
    for mode in (ControlMode.MANUAL,ControlMode.CLOSED_LOOP):
        cases={}
        for case in ("fresh1","fresh2","initialize_twice","run60_reset","fault600_reset"):
            sim=new(mode)
            baseline=snapshot(sim)
            if case=="initialize_twice":
                sim.initialize()
            elif case in ("run60_reset","fault600_reset"):
                if case=="fault600_reset":sim.set_disturbance(4,1)
                sim.step(600 if case=="fault600_reset" else 60)
                (out/f"reset_{mode.value}_{case}_before.json").write_text(json.dumps(snapshot(sim),indent=2),encoding="utf-8")
                sim.clear_disturbances();sim.initialize()
            after=snapshot(sim)
            (out/f"reset_{mode.value}_{case}_after.json").write_text(json.dumps(after,indent=2),encoding="utf-8")
            cases[case]=dict(difference_from_fresh=diff(baseline,after),trajectory=run(sim,1,0,60,f"reset_{mode.value}_{case}",out))
        resets[mode.value]=cases
    source_hashes={str(p.relative_to(args.source)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in (args.source/"src/tep").glob("*.py")}
    result=dict(environment=dict(python=platform.python_version(),numpy=np.__version__),source_commit=COMMIT,
                source_sha256=source_hashes,fortran_available=is_fortran_available(),runs=results,resets=resets)
    (out/"results.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir() if p.is_file()}
    (out/"SHA256.json").write_text(json.dumps(hashes,indent=2),encoding="utf-8")


if __name__=="__main__":main()

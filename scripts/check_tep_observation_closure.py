"""Local counterexample probe; not an observed-variable GT or a new do experiment."""
import argparse
import copy
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    if args.output.exists():raise FileExistsError('Fresh output required')
    prior=json.loads((ROOT/'docs/research_design/track_b_evidence/source_probe.json').read_text())
    assert subprocess.check_output(['git','-C',str(args.source),'rev-parse','HEAD'],text=True).strip()==prior['source_commit']
    assert not subprocess.check_output(['git','-C',str(args.source),'status','--porcelain','--untracked-files=no'],text=True).strip()
    for name,digest in prior['source_sha256'].items():assert sha256((args.source/name).read_bytes()).hexdigest()==digest
    plan_path=ROOT/'research_runs/tep_environment_bridge/CLOSURE_PLAN_v1.json'
    plan=json.loads(plan_path.read_text())
    assert sha256(plan_path.read_bytes()).hexdigest()==plan_path.with_suffix('.sha256').read_text().strip()
    args.output.mkdir(parents=True)
    def save(name,x):(args.output/name).write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n',encoding='utf-8',newline='\n')
    try:
        sys.path.insert(0,str(args.source/'src'))
        import numpy as np
        from tep.simulator import TEPSimulator,ControlMode
        sim=TEPSimulator(random_seed=plan['seed'],control_mode=ControlMode.MANUAL,backend='python');sim.initialize()
        base=copy.deepcopy(sim.process)
        rows=[]
        for delta in plan['valve_state_delta_pp']:
            process=copy.deepcopy(base);state=process.yy.copy();state[47]+=delta
            g_before=float(process._g);derivative=process.evaluate(0.0,state)
            rows.append(dict(delta_valve_state_pp=delta,state=state.tolist(),command=process.get_xmv().tolist(),
                 sensors41=process.get_xmeas().tolist(),derivative50=derivative.tolist(),
                 rng_before=g_before,rng_after=float(process._g),
                 shutdown=bool(process.is_shutdown()),finite=bool(np.isfinite(derivative).all()),
                 fwr=float(process._teproc.fwr)))
        same_sensor=all(np.array_equal(rows[0]['sensors41'],r['sensors41']) for r in rows)
        same_command=all(np.array_equal(rows[0]['command'],r['command']) for r in rows)
        rng_equal=len({r['rng_before'] for r in rows})==len({r['rng_after'] for r in rows})==1
        distinct_dW=len({r['derivative50'][36] for r in rows})==len(rows)
        result=dict(source_commit=prior['source_commit'],source_sha256=prior['source_sha256'],
                    plan_sha256=sha256(plan_path.read_bytes()).hexdigest(),rows=rows,
                    sensors41_exact_equal=same_sensor,commands12_exact_equal=same_command,
                    rng_before_after_equal=rng_equal,coolant_derivative_distinct=distinct_dW,
                    all_finite_no_shutdown=all(r['finite'] and not r['shutdown'] for r in rows),
                    scope='LOCAL_INITIAL_STATE_COUNTEREXAMPLE_NOT_GLOBAL_GT',
                    conclusion='Current 41 sensors plus 12 commands do not uniquely determine coolant state derivative at this point; unobserved valve state matters. This does NOT rule out history-based/latent-variable models or define sensor edges.',
                    new_gt=False,global_f1=False,plant_rollout_steps=0)
        save('RESULT.json',result)
        assert same_sensor and same_command and rng_equal and distinct_dW and result['all_finite_no_shutdown']
        print('[PASS_LOCAL_COUNTEREXAMPLE] 3 fixed-state evaluations; same41sensors/12commands/RNG; different coolant derivative; no rollout or GT')
    except Exception as error:
        save('FAILURE.json',dict(error_type=type(error).__name__,message=str(error)));raise
    finally:
        save('SHA256.json',{x.name:sha256(x.read_bytes()).hexdigest() for x in args.output.iterdir() if x.name!='SHA256.json'})


if __name__=='__main__':main()

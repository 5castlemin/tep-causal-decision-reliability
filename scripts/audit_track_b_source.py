"""Optional bounded API/RNG probe; external source required, never produces GT."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

PIN = '9a6c8e5fcef4a2850778704e7793c87b0a187005'
ROOT = Path(__file__).resolve().parents[1]


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists(), '새 출력 위치 필요'
    assert subprocess.check_output(['git', '-C', str(args.source), 'rev-parse', 'HEAD'], text=True).strip() == PIN
    prior = json.loads((ROOT/'experiments/simulator/diagnostics/run_20261023_aligned/results.json').read_text(encoding='utf-8'))
    hashes = {}
    for name in ['src/tep/simulator.py', 'src/tep/python_backend.py', 'src/tep/controllers.py', 'src/tep/constants.py']:
        hashes[name] = hashlib.sha256((args.source/name).read_bytes()).hexdigest()
        assert hashes[name] == prior['source_sha256'][name], name
    sys.path.insert(0, str(args.source/'src'))
    import numpy as np
    from tep.simulator import TEPSimulator, ControlMode
    modes = {}
    for mode in [ControlMode.MANUAL, ControlMode.CLOSED_LOOP]:
        pair = [TEPSimulator(random_seed=465120799, control_mode=mode, backend='python') for _ in range(2)]
        for sim in pair:
            sim.initialize()
        initial_equal = bool(np.array_equal(pair[0].get_states(), pair[1].get_states()))
        draws = [[], []]
        noise = [[], []]
        for k, sim in enumerate(pair):
            proc = sim.process
            original = proc._tesub7
            original_noise = proc._tesub6
            def tap(i, original=original, sink=draws[k]):
                value = original(i)
                sink.append([int(i), float(value)])
                return value
            def noise_tap(std, original=original_noise, sink=noise[k]):
                value = original(std)
                sink.append([float(std), float(value)])
                return value
            proc._tesub7 = tap
            proc._tesub6 = noise_tap
        initial_command = float(pair[1].get_manipulated_vars()[9])
        records = []
        for step in range(30):
            if step == 6:
                pair[1].set_mv(10, initial_command+0.1)
            before = [len(x) for x in draws]
            success = [bool(sim.step()) for sim in pair]
            records.append(dict(step=step, evaluation_seconds=step, state_seconds=step+1,
                running=success, rng_draw_counts=[len(draws[k])-before[k] for k in range(2)],
                rng_equal=draws[0] == draws[1], measurement_noise_equal=noise[0] == noise[1],
                xmv10_after_step=[float(sim.get_manipulated_vars()[9]) for sim in pair],
                finite_state=[bool(np.isfinite(sim.get_states()).all()) for sim in pair]))
            if not all(success):
                break
        modes[mode.value] = dict(initial_state_equal=initial_equal, initial_xmv10=initial_command,
            command_step=6, commanded_xmv10=initial_command+0.1, records=records,
            rng_digest=[digest(x) for x in draws], noise_digest=[digest(x) for x in noise],
            scope='이 30초/seed/동일 dt/IDV=0에 한정; 효과 정답·장기 재현·안전성 검증 아님')
    result = dict(protocol='TRACK-B-SOURCE-PROBE-v1', source_commit=PIN, source_sha256=hashes,
                  python=sys.version.split()[0], numpy=np.__version__, seed=465120799, dt_seconds=1,
                  modes=modes, reference_graph_created=False, model_fitted=False,
                  recovery_safety_computed=False)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8', newline='\n')
    print(json.dumps({mode:dict(steps=len(x['records']), rng_equal=x['rng_digest'][0] == x['rng_digest'][1],
                              noise_equal=x['noise_digest'][0] == x['noise_digest'][1]) for mode,x in modes.items()}))


if __name__ == '__main__':
    main()

"""Post-run clock-aware diagnostics; descriptive comparisons, no effect oracle."""
import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def read_csv(path):
    return np.loadtxt(path, delimiter=",", skiprows=1, ndmin=2)


def clock_grid(data, clock, end=1770):
    """Match physical evaluation time or state time, never row position."""
    result = {}
    for row in data:
        t = round(row[clock])
        if abs(row[clock]-t) < 1e-6 and t % 30 == 0 and t <= end:
            result.setdefault(t, row)
    return result


def difference(a, b, clock, columns):
    aa, bb = clock_grid(a, clock), clock_grid(b, clock)
    times = sorted(aa.keys() & bb.keys())
    if not times:
        raise ValueError("공통 시점 없음")
    return dict(count=len(times), start_seconds=times[0], end_seconds=times[-1],
                max_abs=float(np.max(np.abs(np.array([aa[t][columns] for t in times])-
                                            np.array([bb[t][columns] for t in times])))))


def analyze(run_dir, dataset=None):
    r = json.loads((run_dir/'results.json').read_text(encoding='utf-8'))
    convergence = []
    for delta in (0, 1):
        for d1, d2 in ((1, .5), (.5, .25)):
            a, b = [read_csv(run_dir/f'zero_xns_diagnostic_dt{d}_delta{delta}.csv') for d in (d1,d2)]
            convergence.append(dict(delta=delta, dt_pair=[d1,d2],
                                    state=difference(a,b,0,slice(55,105)),
                                    pressure=difference(a,b,1,8),
                                    temperature=difference(a,b,1,10),
                                    reactor_level=difference(a,b,1,9)))
    resets = {}
    for mode, cases in r['resets'].items():
        base = read_csv(run_dir/f'reset_{mode}_fresh1.csv')
        resets[mode] = {}
        for case, value in cases.items():
            a = read_csv(run_dir/f'reset_{mode}_{case}.csv')
            resets[mode][case] = dict(initial_differences=value['difference_from_fresh'],
                trajectory_exact=bool(np.array_equal(a,base)),
                state_max_abs=float(np.max(np.abs(a[:,55:]-base[:,55:]))),
                measurement_max_abs=float(np.max(np.abs(a[:,2:43]-base[:,2:43]))),
                mv_max_abs=float(np.max(np.abs(a[:,43:55]-base[:,43:55]))))
    trips = {}
    for name, v in r['runs'].items():
        last = read_csv(run_dir/f'{name}.csv')[-1]
        trips[name] = dict(**v['terminal'], measured_pressure_kpa=float(last[8]),
                           measured_temperature_degC=float(last[10]))
    responses = {}
    for dt in (1,.5,.25):
        reference, intervention = [clock_grid(read_csv(run_dir/f'zero_xns_diagnostic_dt{dt}_delta{d}.csv'),1) for d in (0,1)]
        responses[str(dt)] = [dict(observation_seconds=t,pressure_difference_kpa=float(intervention[t][8]-reference[t][8]),
                                  temperature_difference_degC=float(intervention[t][10]-reference[t][10]),
                                  level_difference_percentage_points=float(intervention[t][9]-reference[t][9])) for t in sorted(reference.keys() & intervention.keys())]
    result = dict(convergence=convergence, responses=responses, resets=resets, terminals=trips,
                  independent_reference=dict(status='NOT_RUN', reason='Fortran backend 미설치, gfortran/flang/cl 명령 미확보'),
                  reset_tolerance=dict(atol=1e-9, rtol=1e-12, timing='첫 진단 결과 확인 후 보고용으로 설정; 사전 합격 기준 아님'),
                  decision=dict(within_candidate='CONDITIONAL', original_benchmark_effect_oracle='NO-GO'))
    stats = []
    if dataset:
        with dataset.open(encoding='utf-8-sig',newline='') as f:
            reader = csv.reader(f)
            names = next(reader)[1:]
            bench = np.asarray([[float(x) for x in row[1:]] for row in reader])
        mapping = {x['benchmark_variable_name']:x['original_tep_variable'] for x in csv.DictReader((HERE.parent/'benchmark_reference_mapping.csv').open(encoding='utf-8-sig'))}
        sim = read_csv(run_dir/'closed_normal_7200.csv')
        grid = clock_grid(sim,1,7200)
        sim = np.array([grid[t] for t in sorted(grid)])
        indices = []
        for name in names:
            mapped = mapping[name]
            i = int(mapped.split('(')[1].rstrip(')'))
            indices.append(i+1 if mapped.startswith('XMEAS') else i+42)
        values = sim[:,indices]
        windows = np.array([np.median(values[(sim[:,1]>=t-1e-6)&(sim[:,1]<t+180-1e-6)],axis=0) for t in range(0,7200,180)])
        for i,name in enumerate(names):
            b,s,w = bench[:,i],values[:,i],windows[:,i]
            stats.append(dict(variable=name, simulator_variable=mapping[name],benchmark_n=len(b),simulator_n=len(s),diagnostic_window_n=len(w),
                              benchmark_mean=float(b.mean()),benchmark_std=float(b.std(ddof=1)),benchmark_min=float(b.min()),benchmark_max=float(b.max()),
                              simulator_mean=float(s.mean()),simulator_std=float(s.std(ddof=1)),simulator_min=float(s.min()),simulator_max=float(s.max()),
                              diagnostic_window_mean=float(w.mean()),mean_gap_in_benchmark_sd=float((w.mean()-b.mean())/b.std(ddof=1))))
        result['compatibility'] = dict(dataset_sha256=hashlib.sha256(dataset.read_bytes()).hexdigest(),rows=len(bench),variables=list(names),
            simulator_horizon_seconds=7200,simulator_record_interval_seconds=30,diagnostic_windows_seconds=180,
            warning='30초 관측 6개를 180초 비중첩 중앙값으로 요약한 진단용 근사. benchmark 원자료 0.1Hz/75시간/슬라이딩 처리의 재현이 아님. 초기 구간 제거 없음.',
            level1='VERIFIED_MAPPING_ONLY', level2='DESCRIPTIVE_ONLY',level3='UNVERIFIED',level4='UNVERIFIED',level5='NO-GO_DIRECT_ORACLE')
    return result, stats


def main():
    p=argparse.ArgumentParser();p.add_argument('--run',type=Path,default=HERE/'run_20261023_aligned');p.add_argument('--dataset',type=Path);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    args.output.mkdir(exist_ok=False)
    result, stats = analyze(args.run,args.dataset)
    (args.output/'analysis.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    if stats:
        with (args.output/'compatibility_statistics.csv').open('w',encoding='utf-8',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(stats[0]));w.writeheader();w.writerows(stats)
    hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in args.output.iterdir() if p.is_file()}
    (args.output/'SHA256.json').write_text(json.dumps(hashes,indent=2),encoding='utf-8')


if __name__=='__main__':main()

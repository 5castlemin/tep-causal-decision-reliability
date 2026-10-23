"""CI verifies retained evidence without fetching/executing external simulator."""
import hashlib
import json
from pathlib import Path

import numpy as np

from analyze_diagnostics import HERE, analyze, read_csv


def main():
    for name in ('run_20261023','run_20261023_aligned','analysis_20261023_v2','analysis_20261023_v3','execution_logs'):
        folder=HERE/name
        manifest=json.loads((folder/'SHA256.json').read_text(encoding='utf-8'))
        for path,sha in manifest.items():
            assert hashlib.sha256((folder/path).read_bytes()).hexdigest()==sha,(name,path)
    folder=HERE/'run_20261023_aligned'
    result=json.loads((folder/'results.json').read_text(encoding='utf-8'))
    assert result['source_commit']=='9a6c8e5fcef4a2850778704e7793c87b0a187005'
    plan=json.loads((folder/'plan.json').read_text(encoding='utf-8'))
    assert plan['dt_seconds']==[1,.5,.25] and plan['mode']=='MANUAL'
    initial=result['runs']['upstream_dt1_delta0']['initial_state']
    assert all(r['initial_state']==initial for r in result['runs'].values())
    for name,r in result['runs'].items():
        a=read_csv(folder/f'{name}.csv')
        assert a.shape[1]==105 and np.isfinite(a).all()
        assert np.all(np.diff(a[:,0])>0)
        dt=1 if name=='closed_normal_7200' else float(name.split('_dt')[1].split('_')[0])
        assert np.allclose(a[1:,0]-a[1:,1],dt,atol=1e-6,rtol=0)
        assert np.isclose(a[-1,0],r['terminal']['state_seconds'])
        assert r['terminal']['finite_state'] and r['terminal']['finite_derivative']
    got,_=analyze(folder)
    saved=json.loads((HERE/'analysis_20261023_v3/analysis.json').read_text(encoding='utf-8'))
    for key in ('convergence','responses','resets','terminals','decision'):
        assert got[key]==saved[key],key
    for mode,cases in got['resets'].items():
        assert cases['fresh2']['trajectory_exact'],mode
        assert cases['initialize_twice']['trajectory_exact'],mode
        for name in ('run60_reset','fault600_reset'):
            differences=cases[name]['initial_differences']
            assert not any(key.startswith(('.yy','.xmv','.rng','.idv','.controller','.walk')) for key in differences)
            assert cases[name]['measurement_max_abs']<1e-9
            assert cases[name]['state_max_abs']<1e-9
    assert got['terminals']['upstream_dt1_delta1']['flags']['pressure_high']
    noisy=got['terminals']['upstream_dt0.25_delta1']
    assert noisy['measured_pressure_kpa']>3000>noisy['physical'][0]
    assert not noisy['backend_shutdown'] and noisy['shutdown']
    assert not got['terminals']['closed_normal_7200']['shutdown']
    for old_name,delta in (('manual_reference',0),('manual_intervention',1)):
        old=read_csv(HERE.parent/'run_20261023_v3'/f'{old_name}.csv')
        new=read_csv(folder/f'upstream_dt1_delta{delta}.csv')
        matching=np.array([row for row in new if np.any(np.abs(old[:,0]*3600-row[0])<1e-6)])
        assert len(matching)==len(old)
        assert np.array_equal(old[:,1:],matching[:,2:55]),old_name
    print('[PASS] 원시 hash·105열·두 시계·12개 수동 조건·2시간 정상·reset·분석 재계산')
    print('SIM-03 PARTIAL; SIM-04 VERIFIED(새 객체 계약); COMPAT-01 PARTIAL; 직접 효과 정답 NO-GO')


if __name__=='__main__':main()

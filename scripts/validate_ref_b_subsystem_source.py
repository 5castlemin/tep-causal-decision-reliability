"""Optional frozen-source, fixed-condition local checks; not a GT generator."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
PIN = '9a6c8e5fcef4a2850778704e7793c87b0a187005'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists(), '새 출력 경로 필요'
    assert subprocess.check_output(['git','-C',str(args.source),'rev-parse','HEAD'],text=True).strip() == PIN
    prior = json.loads((ROOT/'docs/research_design/track_b_evidence/source_probe.json').read_text(encoding='utf-8'))
    hashes = {}
    for name, expected in prior['source_sha256'].items():
        hashes[name] = hashlib.sha256((args.source/name).read_bytes()).hexdigest()
        assert hashes[name] == expected, name
    sys.path.insert(0,str(args.source/'src'))
    import numpy as np
    from tep.simulator import TEPSimulator, ControlMode
    sim = TEPSimulator(random_seed=465120799,control_mode=ControlMode.MANUAL,backend='python')
    sim.initialize()
    baseline = copy.deepcopy(sim.process)

    def evaluate(variable=None, delta=0):
        p = copy.deepcopy(baseline)
        y = p.yy.copy()
        if variable == 'u':p.set_xmv(10,p.get_xmv()[9]+delta)
        if variable in {'v','W','E'}:y[{'v':47,'W':36,'E':8}[variable]] += delta
        g_before = p._g
        yp = p.evaluate(0.0,y)
        tp = p._teproc
        assert not p.is_shutdown() and np.isfinite(yp).all()
        return dict(u=float(p.get_xmv()[9]),v=float(y[47]),W=float(y[36]),E=float(y[8]),
            f=float(tp.fwr),q=float(tp.qur),T=float(tp.tcr),Y9=float(p.get_xmeas()[8]),
            Y21=float(p.get_xmeas()[20]),dv=float(yp[47]),dW=float(yp[36]),dE=float(yp[8]),
            g_before=float(g_before),g_after=float(p._g))

    base = evaluate()
    tp = baseline._teproc
    tau = float(tp.vtau[9])
    vrng = float(tp.vrng[9])
    hwr = float(tp.hwr)
    # IDV=0 at this fixed initial point: the heat-transfer disturbance is zero.
    ua = float(tp.uar)
    inlet = float(tp.tcwr)
    liquid = baseline.yy[3:8].copy()
    total = float(liquid.sum())
    z = np.zeros(8)
    z[3:8] = liquid/total
    c = baseline._const
    def enthalpy(t):
        # Independently written polynomial; no call to source TESUB1/2/3.
        return float(np.sum(z*c.xmw*1.8*(c.ah*t+c.bh*t*t/2+c.ch*t*t*t/3)))
    def bisect_temperature(specific_energy):
        lo,hi=0.0,250.0
        assert enthalpy(lo) <= specific_energy <= enthalpy(hi)
        for _ in range(80):
            mid=(lo+hi)/2
            if enthalpy(mid) < specific_energy:lo=mid
            else:hi=mid
        return (lo+hi)/2
    independent_t = bisect_temperature(base['E']/total)
    assert abs(independent_t-base['T']) < 1e-9
    capacity = float(np.sum(z*c.xmw*1.8*(c.ah+c.bh*base['T']+c.ch*base['T']**2)))
    expected = {'u':{'dv':1/tau},
                'v':{'f':vrng/100,'dv':-1/tau,'dW':vrng/100*500.53*(inlet-base['W'])/hwr},
                'W':{'q':ua,'dE':ua,'Y21':1.0},
                'E':{'Y9':1/(total*capacity)}}
    checks=[]
    for variable, eps in [('u',0.001),('v',0.001),('W',0.001),('E',0.00001)]:
        for epsilon in [eps,eps/2]:
            plus,minus = evaluate(variable,epsilon),evaluate(variable,-epsilon)
            assert plus['g_before'] == minus['g_before'] and plus['g_after'] == minus['g_after']
            finite_difference={key:(plus[key]-minus[key])/(2*epsilon) for key in ['f','q','T','Y9','Y21','dv','dW','dE']}
            comparisons={key:bool(np.isclose(finite_difference[key],value,rtol=1e-4,atol=1e-7)) for key,value in expected[variable].items()}
            assert all(comparisons.values()), (variable,epsilon,finite_difference,expected[variable])
            checks.append(dict(variable=variable,epsilon=epsilon,plus=plus,minus=minus,
                               central_difference=finite_difference,analytic_expected=expected[variable],checks=comparisons))

    # Freeze the controller inputs and memory; no plant rollout in these checks.
    closed = TEPSimulator(random_seed=465120799,control_mode=ControlMode.CLOSED_LOOP,backend='python')
    closed.initialize()
    y0=closed.get_measurements();u0=closed.get_manipulated_vars()
    controller0=copy.deepcopy(closed.controller)
    def controller_trace(index,delta,first_step):
        ctl=copy.deepcopy(controller0);y=y0.copy();y[index]+=delta
        out=ctl.calculate(y,u0.copy(),first_step)
        first=dict(u10=float(out[9]),cw_setpoint=float(ctl.ctrl10.setpoint),
                   inner_previous_error=float(ctl.ctrl10.err_old),outer_previous_error=float(ctl.ctrl18.err_old))
        second=ctl.calculate(y,out.copy(),3)
        return dict(first=first,second=dict(u10=float(second[9]),cw_setpoint=float(ctl.ctrl10.setpoint)))
    inner_plus=controller_trace(20,0.001,0);inner_minus=controller_trace(20,-0.001,0)
    inner_fd=(inner_plus['first']['u10']-inner_minus['first']['u10'])/0.002
    inner=controller0.ctrl10;outer=controller0.ctrl18
    inner_expected=-inner.gain*inner.scale*(1+(3/3600)/inner.taui)
    assert np.isclose(inner_fd,inner_expected,rtol=1e-4,atol=1e-7)
    outer_plus=controller_trace(8,0.001,0);outer_minus=controller_trace(8,-0.001,0)
    outer_sp_fd=(outer_plus['first']['cw_setpoint']-outer_minus['first']['cw_setpoint'])/0.002
    outer_expected=-outer.gain*outer.scale*(1+(3/3600)/outer.taui)*1.5
    assert np.isclose(outer_sp_fd,outer_expected,rtol=1e-4,atol=1e-7)
    assert outer_plus['first']['u10'] == outer_minus['first']['u10']
    assert outer_plus['second']['u10'] != outer_minus['second']['u10']
    off_plus=controller_trace(20,0.001,1);off_minus=controller_trace(20,-0.001,1)
    assert off_plus['first']['u10'] == off_minus['first']['u10']

    pair=[TEPSimulator(random_seed=465120799,control_mode=ControlMode.MANUAL,backend='python') for _ in range(2)]
    for s in pair:s.initialize()
    pair[1].set_mv(10,pair[1].get_manipulated_vars()[9]+0.1)
    rows=[]
    for n in range(6):
        running=[bool(s.step()) for s in pair]
        assert all(running)
        arms=[]
        for s in pair:
            arms.append(dict(u10=float(s.get_manipulated_vars()[9]),v10=float(s.get_states()[47]),
                W=float(s.get_states()[36]),E=float(s.get_states()[8]),
                measured_Y9=float(s.get_measurements()[8]),measured_Y21=float(s.get_measurements()[20]),
                rng=float(s.process._g)))
        assert arms[0]['rng'] == arms[1]['rng']
        rows.append(dict(evaluation_seconds=n,state_seconds=n+1,arms=arms))
    assert rows[0]['arms'][0]['v10'] != rows[0]['arms'][1]['v10']
    result=dict(protocol='REF-B-MINIMAL-SUBSYSTEM-v1',status='PASS_LOCAL_IMPLEMENTATION_CHECKS',
        checked_at='2026-10-24',source_commit=PIN,source_sha256=hashes,
        python=sys.version.split()[0],numpy=np.__version__,seed=465120799,
        classification='CANDIDATE_NOT_OFFICIAL_GT',
        scope='한 초기점·t=0·IDV=0 국소 편미분/엔탈피 역산/제어기·6step 시간 순서 확인; 비간선 정답/전역 물리 검증 아님',
        baseline=base,constants=dict(valve_tau_hours=tau,valve_range=vrng,hwr=hwr,ua=ua,inlet=inlet,liquid_holdup=total),
        enthalpy_check=dict(independent_temperature=independent_t,source_temperature=base['T'],capacity=capacity,
                            method='액체 엔탈피 다항식·80회 이분법; 동일 상수 사용, 별도 방정식/실물 검증 아님'),
        fixed_condition_checks=checks,controller=dict(inner_fd=inner_fd,inner_expected=inner_expected,
            outer_setpoint_fd=outer_sp_fd,outer_setpoint_expected=outer_expected,
            inner_plus=inner_plus,inner_minus=inner_minus,outer_plus=outer_plus,outer_minus=outer_minus,
            off_schedule_plus=off_plus,off_schedule_minus=off_minus),six_step_trace=rows,
        official_gt_created=False,precision_f1_computed=False,discovery_or_scm_fitted=False,recovery_safety_computed=False)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(status=result['status'],fixed_evaluations=1+2*len(checks),
        independent_temperature=independent_t,inner_fd=inner_fd,outer_setpoint_fd=outer_sp_fd,
        trajectory_steps=6,classification=result['classification']),ensure_ascii=False))


if __name__=='__main__':main()

"""CI: recompute contract rejections and stored technical traces, no external TEP run."""
import argparse
from copy import deepcopy
from hashlib import sha256
import json
import math
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.environment_contract import compare_environment_contracts, require_environment_contract

BASE=ROOT/'research_runs/tep_environment_bridge'
def load(path):return json.loads(path.read_text(encoding='utf-8'))


def validate():
    fixtures=BASE/'contracts'
    synthetic=load(fixtures/'software_fixture.json')
    python=load(fixtures/'python_tep_partial.json')
    cpcad=load(fixtures/'cpcad_unresolved.json')
    results=[]
    def case(name,left,right,expected,reason=None,purpose='structure_effect_research'):
        result=compare_environment_contracts(left,right,evidence_root=ROOT,purpose=purpose)
        assert result['metadata_consistent'] is expected,name
        assert not any(result[k] for k in ['scientific_equivalence_proven','manufacturing_adopted','execution_authorized'])
        if reason:assert reason in {r['code'] for r in result['reasons']},name
        results.append(dict(case=name,result=result))
    case('software_fixture_metadata_only',synthetic,synthetic,True)
    require_environment_contract(synthetic,synthetic,evidence_root=ROOT)
    for section,key,value in [('controller','mode','manual'),('clock','sampling_seconds',3),
        ('clock','aggregation','median'),('intervention','kind','setpoint'),
        ('observation','nodes',list(reversed(synthetic['observation']['nodes'])))]:
        other=deepcopy(synthetic);other[section][key]=value
        case('same_label_'+section+'_'+key,synthetic,other,False,'METADATA_MISMATCH')
    for level in ['REPORTED','UNKNOWN']:
        other=deepcopy(synthetic);other['evidence']['fixture']['level']=level
        case(level+'_not_verified',synthetic,other,False,'EVIDENCE_NOT_VERIFIED')
    other=deepcopy(synthetic);other['controller']['evidence_refs']=[]
    case('missing_evidence',synthetic,other,False,'MISSING_EVIDENCE')
    other=deepcopy(synthetic);other['reference']['negative_pairs']=[]
    case('positive_only_cannot_score_full_f1',other,other,False,'INCOMPLETE_NEGATIVE_COVERAGE')
    other=deepcopy(synthetic);other['reference']['representation']='internal_state_dependencies'
    case('internal_reference_not_sensor_direct_gt',other,other,False,'REFERENCE_OBSERVATION_MISMATCH')
    case('fixture_interface_not_research',synthetic,synthetic,True,purpose='interface_only')
    case('CPCAD_vs_PYTHON_research_join',cpcad,python,False,'ENVIRONMENT_ID_MISMATCH')
    same_label=deepcopy(cpcad);same_label['environment_id']=python['environment_id']
    case('CPCAD_relabelled_PYTHON_still_reject',same_label,python,False,'METADATA_MISMATCH')
    case('PYTHON_self_partial_reference_reject',python,python,False,'INCOMPLETE_NEGATIVE_COVERAGE')
    trace=BASE/'technical_v1'
    for name,h in load(trace/'SHA256.json').items():
        assert sha256((trace/name).read_bytes()).hexdigest()==h,name
    assert sha256((BASE/'PLAN_v1.json').read_bytes()).hexdigest()==(BASE/'PLAN_v1.sha256').read_text().strip()
    plan=load(BASE/'PLAN_v1.json');summary=load(trace/'SUMMARY.json')
    assert summary['runs']==8 and summary['integration_steps']==48
    assert summary['training_holdout_generated'] is False and summary['new_reference_gt'] is False
    assert summary['same_seed_general_noise_guarantee'] is False
    runs={arm['name']:load(trace/(arm['name']+'.json')) for arm in plan['arms']}
    core=lambda name:[row['core'] for row in runs[name]['rows']]
    for name,run in runs.items():
        rows=core(name)
        assert len(rows)==7 and run['steps_completed']==6 and run['failure'] is None
        for i,row in enumerate(rows):
            assert math.isclose(row['state_seconds'],i,abs_tol=1e-12)
            assert math.isclose(row['sensor_evaluation_seconds'],max(0,i-1),abs_tol=1e-12)
            assert all(math.isfinite(x) for x in row['state']+row['measurements']+row['commands'])
            assert row['finite'] and not row['shutdown'] and all(x==0 for x in row['idv'])
        if 'manual' in name:
            for a,b in zip(rows,rows[1:]):
                # Independent Euler valve update check: tau=5 seconds.
                expected=a['valve10_state']+(a['xmv10_command']-a['valve10_state'])/5
                assert math.isclose(b['valve10_state'],expected,abs_tol=1e-12)
            assert all(r['xmv10_command']==run['requested_command'] for r in rows)
    for name in ('manual_reference','manual_action','closed_reference','closed_action'):
        assert core(name)==core(name+'_repeat'),name
    for mode in ('manual','closed'):
        left,right=runs[mode+'_reference'],runs[mode+'_action']
        assert left['initialization_sha256']==right['initialization_sha256']
        for a,b in zip(left['rows'],right['rows']):
            assert a['rng_calls_cumulative']==b['rng_calls_cumulative']
            assert a['rng_draw_sequence_sha256']==b['rng_draw_sequence_sha256']
    assert core('manual_action')[0]['xmv10_command']!=core('manual_action')[0]['valve10_state']
    assert core('closed_action')[1]['xmv10_command']!=runs['closed_action']['requested_command']
    assert max(r['xmv10_command'] for r in core('manual_reference'))-min(r['xmv10_command'] for r in core('manual_reference'))==0
    assert summary['all_checks_pass'] and all(summary['checks'].values())
    closure=BASE/'closure_v1'
    for name,h in load(closure/'SHA256.json').items():
        assert sha256((closure/name).read_bytes()).hexdigest()==h,name
    closure_plan=BASE/'CLOSURE_PLAN_v1.json'
    assert sha256(closure_plan.read_bytes()).hexdigest()==closure_plan.with_suffix('.sha256').read_text().strip()
    c=load(closure/'RESULT.json');rows=c['rows']
    assert len(rows)==3 and c['plant_rollout_steps']==0 and not c['global_f1'] and not c['new_gt']
    prior=load(ROOT/'docs/research_design/ref_b_minimal_evidence/local_checks.json')
    constants=prior['constants']
    gradient=10*500.53*(constants['inlet']-rows[1]['state'][36])/constants['hwr']
    for r in rows:
        assert r['sensors41']==rows[0]['sensors41'] and r['command']==rows[0]['command']
        assert r['rng_before']==rows[0]['rng_before'] and r['rng_after']==rows[0]['rng_after']
        assert all(math.isfinite(x) for x in r['derivative50']) and not r['shutdown']
        assert math.isclose(r['derivative50'][36]-rows[1]['derivative50'][36],
                            r['delta_valve_state_pp']*gradient,abs_tol=1e-7)
    assert len({r['derivative50'][36] for r in rows})==3
    record=BASE/'CONTRACT_RESULTS.json'
    if record.exists():assert load(record)==results,'Stored contract rejection reasons changed'
    print(f'[PASS] {len(results)} contract cases; current CPCaD/Python and partial-reference joins rejected; stored 8x6 technical steps/hash/clock/repeats/valve recurrence. No external simulation in this validation.')
    return results


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--record',type=Path)
    a=p.parse_args();result=validate()
    if a.record:
        if a.record.exists():raise FileExistsError('Fresh record required')
        a.record.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')

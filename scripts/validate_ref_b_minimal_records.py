"""CI record consistency only; external physical/GT approval is not inferred."""
import hashlib
import json
import math
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from asset_preservation import assert_protected_preserved
import subprocess

ROOT=Path(__file__).resolve().parents[1]


def main():
    folder=ROOT/'docs/research_design/ref_b_minimal_evidence'
    read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
    for name,expected in read(folder/'SHA256.json').items():
        assert hashlib.sha256((folder/name).read_bytes()).hexdigest()==expected,name
    result=read(folder/'local_checks.json');decision=read(folder/'decision.json')
    assert result['classification']==decision['classification']=='CANDIDATE_NOT_OFFICIAL_GT'
    assert decision['stopping_rule_triggered'] and decision['overall_q2']=='BLOCKED'
    assert decision['track_b_adoption']=='NO-GO' and not decision['track_b_adopted']
    assert decision['questions']==dict(direct_structure='PARTIAL',local_independent_calculation='VERIFIED',
        matching_discovery_semantics='BLOCKED',observational_structure_metric='BLOCKED',structure_effect_comparison='BLOCKED')
    for key in ['official_gt_created','precision_f1_computed','discovery_or_scm_fitted','recovery_safety_computed']:
        assert result[key] is decision[key] is False,key
    prior=read(ROOT/'docs/research_design/track_b_evidence/source_probe.json')
    assert result['source_sha256']==prior['source_sha256']
    assert result['source_commit']==prior['source_commit']
    assert len(result['fixed_condition_checks'])==8
    for row in result['fixed_condition_checks']:
        assert row['plus']['g_before']==row['minus']['g_before']
        assert row['plus']['g_after']==row['minus']['g_after']
        for key,value in row['analytic_expected'].items():
            fd=(row['plus'][key]-row['minus'][key])/(2*row['epsilon'])
            assert fd==row['central_difference'][key]
            assert math.isclose(fd,value,rel_tol=1e-4,abs_tol=1e-7)
    enthalpy=result['enthalpy_check']
    assert abs(enthalpy['independent_temperature']-enthalpy['source_temperature'])<1e-9
    ctl=result['controller']
    assert math.isclose(ctl['inner_fd'],ctl['inner_expected'],rel_tol=1e-4,abs_tol=1e-7)
    assert math.isclose(ctl['outer_setpoint_fd'],ctl['outer_setpoint_expected'],rel_tol=1e-4,abs_tol=1e-7)
    assert ctl['outer_plus']['first']['u10']==ctl['outer_minus']['first']['u10']
    assert ctl['outer_plus']['second']['u10']!=ctl['outer_minus']['second']['u10']
    assert ctl['off_schedule_plus']['first']['u10']==ctl['off_schedule_minus']['first']['u10']
    assert len(result['six_step_trace'])==6
    for index,row in enumerate(result['six_step_trace']):
        assert row['evaluation_seconds']==index and row['state_seconds']==index+1
        assert row['arms'][0]['rng']==row['arms'][1]['rng']
    state=read(ROOT/'docs/research_state.json')
    assert state['ref_b_minimal']==decision
    assert {x['id']:x for x in state['workstreams']}['REF-B']['status']=='PARTIAL'
    protected=['graphs/final','experiments','data','docs/audit/step6_main_table.csv','RESEARCH_DESIGN.md',
               'docs/research_design/evidence','docs/research_design/track_a_evidence',
               'docs/research_design/track_b_evidence','docs/reproducibility/GRAPH_REPRODUCIBILITY.json']
    assert_protected_preserved(ROOT, decision['dependency']['pr7_head'], protected)
    for path in folder.glob('*.json'):
        text=path.read_text(encoding='utf-8')
        assert 'X-Amz-' not in text and 'C:\\Users\\' not in text
    print('[PASS] 국소 차분·독립 역산·제어 순서·시간 기록·CANDIDATE·중단·동결 자료 보존')


if __name__=='__main__':main()

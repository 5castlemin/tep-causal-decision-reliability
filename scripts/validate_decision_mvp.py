"""Verify recorded technical evidence and prevent an invalid performance join."""
import csv
import hashlib
import json
import math
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]


def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    folder=ROOT/'research_runs/decision_mvp'
    for version in ['v1','v2']:
        run=folder/f'run_20261024_{version}'
        for name,expected in read(run/'SHA256.json').items():assert sha(run/name)==expected,name
        s=read(run/'summary.json')
        assert s['technical_ok'] and len(s['cases'])==8 and s['path_metric_rows']==84
        assert s['gates']==dict(G1='BLOCKED',G2='PASS_TECHNICAL',G3='PARTIAL_TECHNICAL_ONLY',G4='NOT_RUN_RESEARCH',G5='BLOCKED')
        assert s['recommendations_executed'] is s['new_fit'] is s['new_environment_adopted'] is False
        for key in ['effect_prediction_error','goal_achievement','recovery','safety','metric_performance_relation']:assert s[key] is None
        assert s['research_join_rejection'].startswith('GATE1_BLOCKED')
        assert s['plan_sha256']==sha(folder/'PLAN_v1.json')
        for case in s['cases']:
            assert case['failure'] is None and case['command_followed'] and case['steps']==60
            assert sha(run/case['raw_file'])==case['sha256']
            rows=list(csv.DictReader((run/case['raw_file']).open(encoding='utf-8')))
            assert len(rows)==60
            for index,row in enumerate(rows):
                assert abs(float(row['state_seconds'])-(index+1))<1e-8
                assert abs(float(row['observation_seconds'])-index)<1e-8
                assert row['step_running']==row['finite']=='True' and row['idv4']=='0'
                assert all(math.isfinite(float(row[f'XMEAS{i}'])) for i in range(1,42))
                assert all(math.isfinite(float(row[f'XMV{i}'])) for i in range(1,13))
                if version=='v2':assert int(row['step_index'])==index
                expected=case['applied_command'] if index>=10 else case['initial_command']
                assert abs(float(row['XMV10'])-expected)<1e-12
        assert all(x['exact_raw_equal'] for x in s['repeat_checks'])
        for seed in [465120799,465120800]:
            for delta in [0.0,0.1]:
                cases=[c for c in s['cases'] if c['seed']==seed and c['delta_pp']==delta]
                assert len(cases)==2 and cases[0]['sha256']==cases[1]['sha256']
        metrics=read(run/'benchmark_task_metrics.json')['rows']
        assert len({(r['graph_id'],r['task_id']) for r in metrics})==84
        assert all(0<=r['gt_path_edge_recall']<=1 and 0<=r['complete_gt_path_fraction']<=1 for r in metrics)
        assert all(r['direct_xy_correct'] is None for r in metrics if r['direct_xy_state']=='UNRESOLVED')
        old=list(csv.DictReader((ROOT/'docs/audit/step6_main_table.csv').open(encoding='utf-8-sig')))
        globals_=read(run/'global_metrics_reused.json')
        assert not globals_['recomputed'] and globals_['source_sha256']==sha(ROOT/'docs/audit/step6_main_table.csv')
        assert len(globals_['rows'])==7
        for row in globals_['rows']:
            candidates=[r for r in old if r['stage']=='final' and float(r['sk_F1'])==row['skeleton_f1'] and float(r['dS_F1'])==row['strict_directed_f1'] and int(r['SHD_S'])==row['shd']]
            assert len(candidates)==1
        fit=read(ROOT/'experiments/pilot/logs/normal_fit_summary.json')
        dry=read(run/'recommendations_dry_run.json')
        assert dry['common_alpha']==fit['selected_alpha'] and not dry['new_fit']
        assert set(dry['rows'])=={'pc','boss','directlingam'}
        assert all(dry['artifact_sha256'][a]==fit['results'][a]['artifact_sha256'] for a in dry['rows'])
        assert all(not x['simulator_execution_allowed'] and len(x['candidates'])==3 for x in dry['rows'].values())
        assert sha(run/'step6_loop_vs_flow_original.csv')=='287b86c3cc2942fdb6fc98250ad0281aa159a2499fa1487eaad1d9f05b25ccd2'
    provenance=read(folder/'MVP_STATUS.json')
    state=read(ROOT/'docs/research_state.json')
    assert state['decision_mvp']==provenance
    assert provenance['hypothesis_gate']=='NO-GO' and not provenance['new_environment_adopted']
    protected=['graphs/final','experiments','data','docs/audit/step6_main_table.csv','RESEARCH_DESIGN.md',
               'docs/research_design/evidence','docs/research_design/track_a_evidence',
               'docs/research_design/track_b_evidence','docs/research_design/ref_b_minimal_evidence']
    changes=subprocess.check_output(['git','-C',str(ROOT),'diff','--name-only',provenance['base_commit'],'--',*protected],text=True)
    assert not changes.strip(),changes
    print('[PASS] 기존 자산 재사용·84행·8회×2버전 raw/hash·Gate 거부·성능 null·상태 동기화·원본 보존')


if __name__=='__main__':main()

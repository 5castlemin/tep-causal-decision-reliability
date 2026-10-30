"""CI rechecks recorded graph/mechanism/do evidence without running the candidate."""
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from asset_preservation import assert_protected_preserved

ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def table(p):return list(csv.DictReader(p.open(encoding='utf-8')))


def main():
    folder=ROOT/'research_runs/env_acceptance';out=folder/'run_20261024_v1'
    for name,expected in read(out/'SHA256.json').items():assert sha(out/name)==expected,name
    plan=read(folder/'PLAN_v1.json');r=read(out/'result.json');status=read(folder/'ACCEPTANCE_STATUS.json')
    assert r['status']==status['status']=='PASS_EXAMPLE_IID_FCM_ONLY'
    assert r['source_sha256']==r['source_hash_after']==plan['module_sha256']
    assert r['source_commit']==plan['source_commit'] and not r['source_modified']
    assert r['plan_sha256']==sha(folder/'PLAN_v1.json')
    assert set(plan['train_seeds']).isdisjoint(plan['holdout_seeds'])
    assert len(r['records'])==18 and r['sampler_calls_including_unhooked_controls']==27
    assert len(r['repeat_checks'])==len(r['hook_controls'])==9
    assert all(x['data_exact'] and x['noise_exact'] for x in r['repeat_checks'])
    assert all(x['exact'] for x in r['hook_controls']) and r['new_seed_observations_distinct']
    gt=table(out/'declared_fixture_reference.csv');nodes=plan['nodes'];truth={tuple(e) for e in plan['expected_direct_edges']}
    assert len(gt)==4
    for i,row in enumerate(gt):
        assert row['']==nodes[i]
        for node in nodes:assert bool(float(row[node]))==((nodes[i],node) in truth)
    seen={}
    for batch in r['records']:
        assert sha(out/batch['data_file'])==batch['data_sha256']
        assert sha(out/batch['noise_file'])==batch['noise_sha256']
        data=table(out/batch['data_file']);noise=table(out/batch['noise_file'])
        assert len(data)==len(noise)==64
        assert list(data[0])==['sample_id',*nodes]
        for index,(values,u) in enumerate(zip(data,noise)):
            assert int(values['sample_id'])==int(u['sample_id'])==index
            R,A,M,Y=[float(values[n]) for n in nodes]
            expected_A=2*R+float(u['u_A']) if batch['action'] is None else batch['action']
            assert max(abs(R-float(u['u_R'])),abs(A-expected_A),abs(M-3*A-float(u['u_M'])),abs(Y-M-R-float(u['u_Y'])))<=1e-10
        if batch['action'] is not None:
            meta=batch['metadata']['mutilated']
            assert not meta['action_parents'] and float(meta['action_term'])==batch['action']
            assert {tuple(e) for e in meta['edges']}==truth-{('R','A')}
            assert meta['nonaction_terms_unchanged']
        assert {tuple(e) for e in batch['metadata']['original_edges']}==truth
        expected_split='train' if batch['seed'] in plan['train_seeds'] else 'holdout'
        assert batch['split']==expected_split
        key=(batch['seed'],batch['condition'])
        if key in seen:assert seen[key]==(batch['data_sha256'],batch['noise_sha256'])
        seen[key]=(batch['data_sha256'],batch['noise_sha256'])
    assert r['checks']['same_variables_axis']=='PASS_IID_SCHEMA_PHYSICAL_TIME_NOT_APPLICABLE'
    assert all(not any(x['per_noise_equal'].values()) and x['removed_noise']==['u_A'] for x in r['common_noise_checks'])
    assert r['pr9_reuse']['same_fixture_guard_accepted'] and r['pr9_reuse']['cross_environment_rejected']
    for key in ['strict_counterfactual_ready','manufacturing_generator_validated','track_b_adopted',
                'discovery_trained','scm_fitted','recovery_safety_computed']:assert r[key] is False
    negative=read(folder/'negative_no_approval_v1/FAILURE.json')
    assert negative['error_type']=='PermissionError' and negative['source_sha256']==plan['module_sha256']
    assert negative['plan_sha256']==sha(folder/'PLAN_v1.json')
    assert not read(folder/'environment_probe.json')['include_system_site_packages']
    state=read(ROOT/'docs/research_state.json');assert state['env_acceptance']==status
    protected=['graphs/final','experiments','data','docs/audit/step6_main_table.csv','RESEARCH_DESIGN.md',
        'docs/research_design/evidence','docs/research_design/track_a_evidence','docs/research_design/track_b_evidence',
        'docs/research_design/ref_b_minimal_evidence','research_runs/decision_mvp']
    assert_protected_preserved(ROOT,status['base_commit'],protected)
    print('[PASS] 예제 direct GT·행별 관측/do·seed/배치·음성 guard·범위·원본 보존. 제조 검증 아님')


if __name__=='__main__':main()

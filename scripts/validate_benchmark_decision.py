"""Check decision provenance/preservation; does not certify model equivalence."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
PR4='71c5448ed9a82548d86f40f60be842020f69538d'


def main():
    folder=ROOT/'docs/research_design/evidence'
    local=folder/'local_20261023_v2'
    for name,sha in json.loads((local/'SHA256.json').read_text(encoding='utf-8')).items():
        assert hashlib.sha256((local/name).read_bytes()).hexdigest()==sha,name
    audit=json.loads((local/'local_audit.json').read_text(encoding='utf-8'))
    assert audit['input_hashes']['dataset_csv']=='52ae445b4355201db9591822282381c8de861afe49bdbc9452db08b01e7d3711'
    assert audit['input_hashes']['gt_txt']=='238542dbdde50887b5944fb3acc64a792b19a0c56bbfa06e3b267261f2fe6c43'
    assert audit['dataset']['shape']==audit['dataset']['numpy_shape']==[1499,31]
    assert audit['dataset']['numpy_csv_exact'] and audit['dataset']['finite']
    prior=json.loads((ROOT/'experiments/simulator/diagnostics/run_20261023_aligned/results.json').read_text(encoding='utf-8'))
    assert audit['candidate']['commit']==prior['source_commit']
    assert audit['candidate']['source_clean']
    assert audit['candidate']['controller_sha256']==prior['source_sha256']['src/tep/controllers.py']
    points={x['input_name']:x['value'] for x in audit['official_archive']['setpoints']}
    assert points=={'Reactor Level Setpoint':65,'Reactor Press Setpoint':2800,'Reactor Temp Setpoint':122.9}
    assert audit['official_archive']['execution']==audit['original_fortran_archive']['execution']=='NOT_RUN'
    assert audit['new_simulator_experiment']=='NOT_RUN'
    review=json.loads((local/'pr4_asset_review.json').read_text(encoding='utf-8'))
    assert len(review['files'])==review['changed_files']==156
    assert sum(x['change']=='A' for x in review['files'])==review['added_files']==145
    for record in review['files']:
        data=subprocess.check_output(['git','-C',str(ROOT),'cat-file','blob',PR4+':'+record['path']])
        assert len(data)==record['bytes'] and hashlib.sha256(data).hexdigest()==record['sha256']
    claims=json.loads((folder/'provenance_claims.json').read_text(encoding='utf-8'))['claims']
    assert len({x['id'] for x in claims})==len(claims)
    assert all(x['status'] in {'VERIFIED','REPORTED','INFERRED','UNKNOWN'} and x['source'] and x['location'] for x in claims)
    decision=json.loads((folder/'decision.json').read_text(encoding='utf-8'))
    assert decision['overall_hypothesis_gate']=='INSUFFICIENT_EVIDENCE'
    assert not decision['primary_research_changed'] and not decision['secondary_track_adopted']
    assert decision['benchmark_direct_effect_oracle']=='NO-GO'
    original_design=subprocess.check_output(['git','-C',str(ROOT),'show',PR4+':RESEARCH_DESIGN.md'])
    assert hashlib.sha256(original_design).hexdigest()==decision['research_design_git_blob_sha256']
    state=json.loads((ROOT/'docs/research_state.json').read_text(encoding='utf-8'))
    assert state['compatibility_decision']==decision
    unchanged=['graphs/final','experiments/simulator','docs/audit/step6_main_table.csv','RESEARCH_DESIGN.md']
    changed=subprocess.check_output(['git','-C',str(ROOT),'diff','--name-only',PR4,'--',*unchanged]).decode().strip()
    assert not changed,changed
    print('[PASS] 156개 PR4 파일 원본 hash·회수 코드 정적 근거·주장 수준·설계 보류·상태 동기화·원시 산출물 불변')
    print('BENCHMARK COMPATIBILITY: PARTIAL; HYPOTHESIS GATE: INSUFFICIENT_EVIDENCE; 새 실험 NOT_RUN')


if __name__=='__main__':main()

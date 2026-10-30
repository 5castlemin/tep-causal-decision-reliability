"""Validate audit scope and recorded bytes, not scientific GT validity."""
import hashlib
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from asset_preservation import assert_protected_preserved
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def main():
    folder = ROOT/'docs/research_design/track_b_evidence'
    read = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
    for name, expected in read(folder/'SHA256.json').items():
        assert hashlib.sha256((folder/name).read_bytes()).hexdigest() == expected, name
    decision = read(folder/'decision.json')
    assert decision['questions'] == {'Q1':'PARTIAL','Q2':'BLOCKED','Q3':'BLOCKED','Q4':'UNKNOWN','Q5':'VERIFIED'}
    assert decision['recommendation'] == 'NO-GO'
    for key in ['track_b_adopted','research_question_changed','reference_graph_created',
                'new_discovery_or_scm_fitted','recovery_safety_computed']:
        assert decision[key] is False, key
    probe = read(folder/'source_probe.json')
    old = read(ROOT/'experiments/simulator/diagnostics/run_20261023_aligned/results.json')
    assert probe['source_commit'] == old['source_commit']
    assert all(old['source_sha256'][name] == value for name,value in probe['source_sha256'].items())
    assert probe['reference_graph_created'] is probe['model_fitted'] is probe['recovery_safety_computed'] is False
    for mode in ['manual','closed_loop']:
        row = probe['modes'][mode]
        assert row['initial_state_equal'] and len(row['records']) == 30
        assert row['rng_digest'][0] == row['rng_digest'][1]
        assert row['noise_digest'][0] == row['noise_digest'][1]
        for index, record in enumerate(row['records']):
            assert record['step'] == index and record['evaluation_seconds'] == index
            assert record['state_seconds'] == index+1
            assert all(record['running']) and all(record['finite_state'])
            assert record['rng_equal'] and record['measurement_noise_equal']
        if mode == 'manual':
            assert row['records'][6]['xmv10_after_step'][1] == row['commanded_xmv10']
        else:
            assert row['records'][6]['xmv10_after_step'][1] != row['commanded_xmv10']
    inventory = read(folder/'source_inventory.json')
    assert len(inventory['rieth']['files']) == 4
    assert all(not x['bytes_recovered'] and x['local_sha256'] is None for x in inventory['rieth']['files'])
    assert inventory['rieth']['license_status'] == 'VERIFIED_METADATA_CUSTOM_TERMS'
    state = read(ROOT/'docs/research_state.json')
    assert state['track_b_audit'] == decision
    # Past audit IDs remain; a later authorized task may change current priorities.
    assert {'REF-B','SIM-B','DESIGN-B'} <= {x['id'] for x in state['workstreams']}
    protected = ['graphs/final','experiments','data','docs/audit/step6_main_table.csv',
                 'RESEARCH_DESIGN.md','docs/research_design/track_a_evidence',
                 'docs/research_design/evidence','docs/reproducibility/GRAPH_REPRODUCIBILITY.json']
    assert_protected_preserved(ROOT, decision['dependency']['head'], protected)
    for p in folder.glob('*.json'):
        content = p.read_text(encoding='utf-8')
        assert 'X-Amz-' not in content and 'C:\\Users\\' not in content
    print('[PASS] Q1~Q5·미채택·30초 범위·metadata/원본 구분·hash·동결 자료 보존')


if __name__ == '__main__':main()

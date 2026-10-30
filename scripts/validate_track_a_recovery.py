"""Validate recorded evidence, not the existence of a licensed MATLAB engine."""
import hashlib
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from asset_preservation import assert_protected_preserved
import subprocess

from track_a_gate import evaluate

ROOT = Path(__file__).resolve().parents[1]


def main():
    folder = ROOT / 'docs/research_design/track_a_evidence'
    read = lambda path: json.loads(path.read_text(encoding='utf-8'))
    for name, expected in read(folder / 'SHA256.json').items():
        assert hashlib.sha256((folder / name).read_bytes()).hexdigest() == expected, name
    e = read(folder / 'gate_evidence.json')
    assert evaluate(e) == e['gate_decision']
    assert not e['raw_data']['acquired'] and e['dataset_listing']['raw_package_sha256'] is None
    assert e['dataset_listing']['download_access'] == 'LOGIN_REQUIRED'
    assert e['technical_report']['status'] == 'RETRIEVED_DOCUMENT_NOT_RAW_DATA'
    assert e['execution_environment']['license_test_status'] == 'NOT_RUN'
    assert e['normal_runs'] == [] and e['gate_decision']['A3'] == 'NOT_RUN'
    assert set(e['levels']) == {f'L{i}' for i in range(1, 8)}
    assert e['no_new_discovery_or_scm'] and not e['research_design_changed']
    assert not e['external_contact_sent']
    prior = read(ROOT / 'docs/research_design/evidence/local_20261023_v2/local_audit.json')
    assert e['source_hashes']['temexd_mod.zip'] == prior['official_archive']['sha256']
    assert e['source_hashes']['tecode.zip'] == prior['original_fortran_archive']['sha256']
    protected = ['graphs/final', 'results', 'experiments', 'RESEARCH_DESIGN.md',
                 'docs/research_design/evidence']
    assert_protected_preserved(ROOT, e['base_main'], protected)
    for path in folder.glob('*.json'):
        text = path.read_text(encoding='utf-8')
        assert 'X-Amz-' not in text and 'C:\\Users\\' not in text
    state = read(ROOT / 'docs/research_state.json')
    assert state['track_a_gate'] == e['gate_decision']
    assert state['github_current']['pr5_status'] == 'MERGED'
    assert (ROOT / 'docs/research_design/TRACK_A_RECOVERY_GATE.md').is_file()
    print('[PASS] 출처 hash·Gate·A3 미실행·L1~L7·상태·동결 산출물 보존')


if __name__ == '__main__':
    main()

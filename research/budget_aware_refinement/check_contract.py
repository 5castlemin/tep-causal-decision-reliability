"""Static completeness check only; never executes research or establishes validity."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REQUIRED = ('README.md','RESEARCH_PROTOCOL.md','ROADMAP.md','RESEARCH_STATUS.md',
            'DECISION_LOG.md','EXPERIMENT_REGISTRY.md','RISKS_AND_LIMITATIONS.md','MERGE_CHECKLIST.md')

def main():
    docs = {name:(ROOT/name).read_text(encoding='utf-8') for name in REQUIRED}
    assert all(docs.values())
    assert all(f'RQ{i}' in docs['README.md'] for i in range(1,5))
    assert all(f'Phase {i}' in docs['README.md'] for i in range(1,6))
    assert all(f'BAR-0{i}' in docs['EXPERIMENT_REGISTRY.md'] for i in range(1,4))
    assert 'PLANNED' in docs['EXPERIMENT_REGISTRY.md'] and 'BLOCKED' in docs['EXPERIMENT_REGISTRY.md']
    assert 'NOT_RUN' in docs['RESEARCH_STATUS.md'] and 'PROPOSED_FOR_REVIEW' in docs['RESEARCH_PROTOCOL.md']
    assert '15개' in docs['RESEARCH_PROTOCOL.md'] and '16개' in docs['RESEARCH_PROTOCOL.md']
    print('PASS: document presence and declared scope; not a scientific validation')

if __name__ == '__main__':
    main()

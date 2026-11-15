"""Predeclared structural recipes and gates for the exploratory supplement."""
import hashlib
import json
from pathlib import Path
from .policy_engine import _acyclic, _candidates, refine
from .run_step3_pilot import sample

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT/'research/budget_aware_refinement'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def initial_graph(spec, condition):
    truth={(e['source'],e['target']) for e in spec['edges']}
    key=('A','M' if spec['structure_id']=='S1' else 'M1')
    last=('M','Y') if spec['structure_id']=='S1' else ('M3','Y')
    if condition=='single_fn': return truth-{key}
    if condition=='mixed': return (truth-{key,last,('S','T')})|{('T','S'),('Y','A')}
    raise ValueError('unknown condition')

def validate():
    plan=json.loads((ROOT/'research_runs/diverse_structure_pilot/run_v1/plan.json').read_text(encoding='utf8'))
    manifest=json.loads((BASE/'step3_results/manifest.json').read_text(encoding='utf8'))
    original=json.loads((BASE/'step3_results/raw.json').read_text(encoding='utf8'))
    for f,k in [('raw.json','raw_sha256'),('summary.json','summary_sha256')]:
        content=(BASE/'step3_results'/f).read_bytes()
        # Git may check out the previously recorded Windows CRLF text as LF.
        # Reconstruct only that byte representation, not the JSON values.
        windows_bytes=content.replace(b'\r\n',b'\n').replace(b'\n',b'\r\n')
        if manifest[k] not in (hashlib.sha256(content).hexdigest(),hashlib.sha256(windows_bytes).hexdigest()):
            raise ValueError('original result hash mismatch '+f)
    if len(original)!=114: raise ValueError('original run count mismatch')
    results=[]
    for sid,seed in [('S1',3101),('S7',3107)]:
        s=next(s for s in plan['structures'] if s['structure_id']==sid)
        if len(s['nodes'])!=len(set(s['nodes'])): raise ValueError('duplicate node')
        data=sample(s,seed); dh=hashlib.sha256(data.tobytes()).hexdigest()
        if {r['data_hash'] for r in original if r['scm']==sid}!={dh}:raise ValueError('training data hash mismatch')
        truth={(e['source'],e['target']) for e in s['edges']}
        for condition in ('single_fn','mixed'):
            graph=initial_graph(s,condition)
            if not _acyclic(s['nodes'],graph):raise ValueError('initial graph cycle')
            candidates=_candidates(s['nodes'],truth,graph,('FN','FP','REV'))
            counts={k:sum(x[0]==k for x in candidates) for k in ('FN','FP','REV')}
            if counts != ({'FN':1,'FP':0,'REV':0} if condition=='single_fn' else {'FN':2,'FP':1,'REV':1}):raise ValueError('unexpected errors')
            for task in s['tasks'][:2]:
                common=dict(node_ids=s['nodes'],initial_edges=sorted(graph),reference_edges=sorted(truth),allowed_types=['FN','FP','REV'],budget=2,gamma=1,action=task['action'],target=task['target'],seed=0)
                g=refine(policy_id='G-FN-FP-REV',**common);t=refine(policy_id='T-FN-FP-REV',**common)
                if g['type_schedule']!=t['type_schedule']:raise ValueError('schedule mismatch')
                if not g['edit_sequence'] or not t['edit_sequence']:raise ValueError('no edit opportunity')
            results.append(dict(scm=sid,condition=condition,data_hash=dh,counts=counts,candidates=candidates))
    return results

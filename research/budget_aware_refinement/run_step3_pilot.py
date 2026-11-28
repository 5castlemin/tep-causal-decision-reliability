"""Bounded, prespecified development pilot; no confirmation SCMs."""
import hashlib,itertools,json,platform,sys,time,traceback
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'src'))
from research.budget_aware_refinement.step3_adapter import prepare,evaluate
from research.budget_aware_refinement.policy_engine import compare_edits
from diverse_structure_pilot import reference_edges,controlled_graphs,analytic_response
from integrated_pilot import fit_model
from decision_mvp import static_mean_response,reachable

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def sample(spec,seed):
    rng=np.random.default_rng(seed); values={};pending=set(spec['nodes'])
    while pending:
        ready=sorted(n for n in pending if all(e['source'] in values for e in spec['edges'] if e['target']==n))
        if not ready:raise ValueError('cyclic SCM')
        for n in ready:
            width=np.sqrt(3)*spec['noise_sd'][n]
            values[n]=rng.uniform(-width,width,256)+sum((e['coefficient']*values[e['source']] for e in spec['edges'] if e['target']==n),np.zeros(256))
            pending.remove(n)
    return np.column_stack([values[n] for n in spec['nodes']])

def main():
    out=ROOT/'research/budget_aware_refinement/step3_results';out.mkdir(exist_ok=True)
    planpath=ROOT/'research_runs/diverse_structure_pilot/run_v1/plan.json';plan=json.loads(planpath.read_text(encoding='utf8'))
    started=time.monotonic(); rows=[]; seeds={'S1':3101,'S7':3107};types=('FN','FP','REV')
    ids=[(list(c),mode+'-'+'-'.join(c),0) for r in (1,2,3) for c in itertools.combinations(types,r) for mode in ('G','T')]
    ids += [(list(types),'NO-EDIT',0),(list(types),'PATH-F1',0)]+[(list(types),'RANDOM',s) for s in (0,1,2)]
    for spec in [s for s in plan['structures'] if s['structure_id'] in seeds]:
        sid=spec['structure_id'];task=spec['tasks'][0];data=sample(spec,seeds[sid]);truth=reference_edges(spec)
        initial=controlled_graphs(spec,plan)['remove_key'];dh=hashlib.sha256(data.tobytes()).hexdigest()
        for budget in (0,2,4):
            for allowed,policy,seed in ids:
                t=time.monotonic();row=dict(scm=sid,task=task['task_id'],budget=budget,policy=policy,seed=seed,data_hash=dh,status='FAILED')
                try:
                    if time.monotonic()-started>300:raise TimeoutError('pilot runtime cap')
                    req=dict(node_ids=spec['nodes'],initial_edges=sorted(initial),reference_edges=sorted(truth),allowed_types=allowed,policy_id=policy,budget=budget,gamma=1,action=task['action'],target=task['target'],seed=seed)
                    graph,selection=prepare(req,data,list(spec['nodes']),list(spec['nodes']),1 if sid=='S1' else -1,fit_model,static_mean_response)
                    result=evaluate(selection,spec,analytic_response)
                    row.update(status='OK',graph=graph,selection=selection,evaluation=result,has_path=reachable({tuple(e) for e in graph['final_graph']},task['action'],task['target']))
                except Exception as exc:row.update(error=type(exc).__name__+': '+str(exc),traceback=traceback.format_exc())
                row['seconds']=time.monotonic()-t;rows.append(row)
                if isinstance(locals().get('exc'),TimeoutError):break
    (out/'raw.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf8')
    groups=[]
    for sid,b in itertools.product(seeds,(0,2,4)):
        subset=[r for r in rows if r['scm']==sid and r['budget']==b and r['status']=='OK']
        baseline=next((r for r in subset if r['policy']=='NO-EDIT'),None)
        for r in subset:
            r['regret_change_vs_no_edit']=r['evaluation']['regret']-baseline['evaluation']['regret']
            r['recommendation_changed']=r['selection']['selected_k']!=baseline['selection']['selected_k']
        comparisons=[]
        for r in subset:
            if r['policy'].startswith('G-'):
                mate=next(x for x in subset if x['policy']=='T-'+r['policy'][2:])
                comparisons.append(dict(pair=r['policy'][2:],**compare_edits(r['graph']['edit_sequence'],mate['graph']['edit_sequence'])))
        groups.append(dict(scm=sid,budget=b,successful=len(subset),distinct_graphs=len({r['graph']['final_hash'] for r in subset}),distinct_recommendations=len({r['selection']['selected_k'] for r in subset}),pairs=comparisons))
    (out/'raw.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf8')
    (out/'summary.json').write_text(json.dumps(groups,indent=2),encoding='utf8')
    manifest=dict(plan_sha256=sha(ROOT/'research/budget_aware_refinement/STEP3_PILOT_PLAN.md'),source_plan_sha256=sha(planpath),adapter_sha256=sha(ROOT/'research/budget_aware_refinement/step3_adapter.py'),runner_sha256=sha(Path(__file__)),python=sys.version,numpy=np.__version__,platform=platform.platform(),raw_sha256=sha(out/'raw.json'),summary_sha256=sha(out/'summary.json'),n=len(rows),failed=sum(r['status']!='OK' for r in rows),seconds=time.monotonic()-started)
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
    print(json.dumps(manifest,indent=2))
if __name__=='__main__':main()

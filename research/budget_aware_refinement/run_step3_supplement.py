"""Prespecified Step 3 supplement; writes only a separate result directory."""
import hashlib,itertools,json,platform,sys,time,traceback
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'src')]
from research.budget_aware_refinement.step3_supplement import validate,initial_graph,sha,BASE
from research.budget_aware_refinement.run_step3_pilot import sample
from research.budget_aware_refinement.step3_adapter import prepare,evaluate
from research.budget_aware_refinement.policy_engine import compare_edits
from diverse_structure_pilot import analytic_response
from integrated_pilot import fit_model
from decision_mvp import static_mean_response,reachable

def main():
    gate=validate() # No result creation if the pre-run gate fails.
    planpath=BASE/'STEP3_SUPPLEMENT_PLAN.md'; planhash=sha(planpath)
    source=ROOT/'research_runs/diverse_structure_pilot/run_v1/plan.json'
    plan=json.loads(source.read_text(encoding='utf8'));types=('FN','FP','REV')
    ids=[(list(c),mode+'-'+'-'.join(c),0) for n in (1,2,3) for c in itertools.combinations(types,n) for mode in ('G','T')]
    ids += [(list(types),'NO-EDIT',0),(list(types),'PATH-F1',0)]+[(list(types),'RANDOM',s) for s in (0,1,2)]
    out=BASE/'step3_supplement_results'
    if out.exists():raise FileExistsError('preserve previous supplement output')
    out.mkdir(); (out/'gate.json').write_text(json.dumps(gate,indent=2),encoding='utf8')
    rows=[];start=time.monotonic(); stopped=False
    for s in [x for x in plan['structures'] if x['structure_id'] in ('S1','S7')]:
      sid=s['structure_id'];data=sample(s,3101 if sid=='S1' else 3107);truth={(e['source'],e['target']) for e in s['edges']}
      for task,cond,budget,(allowed,policy,seed) in itertools.product(s['tasks'][:2],('single_fn','mixed'),(0,2,4),ids):
        if time.monotonic()-start>300:stopped=True;break
        t=time.monotonic();row=dict(scm=sid,task=task['task_id'],condition=cond,budget=budget,policy=policy,seed=seed,status='FAILED',data_hash=hashlib.sha256(data.tobytes()).hexdigest())
        try:
            initial=initial_graph(s,cond)
            req=dict(node_ids=s['nodes'],initial_edges=sorted(initial),reference_edges=sorted(truth),allowed_types=allowed,policy_id=policy,budget=budget,gamma=1,action=task['action'],target=task['target'],seed=seed)
            graph,selection=prepare(req,data,list(s['nodes']),list(s['nodes']),1 if sid=='S1' else -1,fit_model,static_mean_response)
            result=evaluate(selection,s,analytic_response)
            row.update(status='OK',graph=graph,selection=selection,evaluation=result,has_path=reachable({tuple(e) for e in graph['final_graph']},task['action'],task['target']))
        except Exception as exc:row.update(error=repr(exc),traceback=traceback.format_exc())
        row['seconds']=time.monotonic()-t;rows.append(row)
      if stopped:break
    for row in rows:
        if row['status']!='OK':continue
        baseline=next((r for r in rows if r['scm']==row['scm'] and r['task']==row['task'] and r['condition']==row['condition'] and r['budget']==row['budget'] and r['policy']=='NO-EDIT' and r['status']=='OK'),None)
        if baseline:
            row['regret_change_vs_no_edit']=row['evaluation']['regret']-baseline['evaluation']['regret']
            row['recommendation_changed']=row['selection']['selected_k']!=baseline['selection']['selected_k']
            row['prediction_changed']=any(abs(a['predicted_y']-b['predicted_y'])>1e-12 for a,b in zip(row['selection']['candidates'],baseline['selection']['candidates']))
    summaries=[]
    for sid,task,cond,budget in itertools.product(('S1','S7'),('direct','path'),('single_fn','mixed'),(0,2,4)):
        rs=[r for r in rows if (r['scm'],r['task'],r['condition'],r['budget'])==(sid,task,cond,budget) and r['status']=='OK']
        pairs=[]
        for r in rs:
            if r['policy'].startswith('G-'):
                mate=next((x for x in rs if x['policy']=='T-'+r['policy'][2:]),None)
                if mate:pairs.append(dict(policy=r['policy'],**compare_edits(r['graph']['edit_sequence'],mate['graph']['edit_sequence'])))
        summaries.append(dict(scm=sid,task=task,condition=cond,budget=budget,n=len(rs),graphs=len({r['graph']['final_hash'] for r in rs}),actions=len({r['selection']['selected_k'] for r in rs}),regrets=sorted({r['evaluation']['regret'] for r in rs}),prediction_changed=sum(r['prediction_changed'] for r in rs),recommendation_changed=sum(r['recommendation_changed'] for r in rs),pairs=pairs,cycle_rejections=sum(sum(x['reason']=='cycle' for x in r['graph']['rejected_operations']) for r in rs)))
    raw=out/'raw.jsonl';raw.write_text(''.join(json.dumps(r,ensure_ascii=False,allow_nan=False)+'\n' for r in rows),encoding='utf8')
    summ=out/'summary.json';summ.write_text(json.dumps(summaries,indent=2),encoding='utf8')
    manifest=dict(plan_sha256=planhash,source_plan_sha256=sha(source),original_raw_sha256=sha(BASE/'step3_results/raw.json'),code_sha256=sha(Path(__file__)),gate_code_sha256=sha(BASE/'step3_supplement.py'),adapter_sha256=sha(BASE/'step3_adapter.py'),raw_sha256=sha(raw),summary_sha256=sha(summ),python=sys.version,numpy=np.__version__,platform=platform.platform(),elapsed=time.monotonic()-start,planned=456,actual=len(rows),failed=sum(r['status']!='OK' for r in rows),stopped=stopped)
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8');print(json.dumps(manifest,indent=2))
if __name__=='__main__':main()

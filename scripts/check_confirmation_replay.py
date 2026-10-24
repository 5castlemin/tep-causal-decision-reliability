"""Compare a real full replay, with exact discrete and predeclared numeric checks."""
import argparse,csv,hashlib,json,math,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def main():
    p=argparse.ArgumentParser();p.add_argument('--replay',required=True);p.add_argument('--analysis',required=True);p.add_argument('--output',required=True);a=p.parse_args()
    old=ROOT/'research_runs/diverse_structure_pilot';new=Path(a.replay);analysis=Path(a.analysis)
    assert read(new/'environment.json')['versions']==read(old/'run_v1/environment.json')['versions']
    for key in ['python','source_commit','upstream_source_sha256','plan_sha256','code_sha256']:
        assert read(new/'environment.json')[key]==read(old/'run_v1/environment.json')[key],key
    mismatches=[];checked=[];max_difference=[0.]
    excluded={'seconds','utc','run_wall_seconds','analysis_code_sha256','input_summary_sha256'}
    def compare(x,y,path):
        if isinstance(x,dict) and isinstance(y,dict):
            if set(x)-excluded!=set(y)-excluded:mismatches.append(path+':KEYS');return
            for k in x:
                if k not in excluded:compare(x[k],y[k],path+'/'+k)
        elif isinstance(x,list) and isinstance(y,list):
            if len(x)!=len(y):mismatches.append(path+':LENGTH');return
            for i,(v,w) in enumerate(zip(x,y)):compare(v,w,path+'/'+str(i))
        elif path.endswith('/recommended_action') or path.endswith('/selected/action'):
            if x!=y:mismatches.append(path+':DISCRETE_ACTION')
        elif isinstance(x,(int,float)) and not isinstance(x,bool) and isinstance(y,(int,float)) and not isinstance(y,bool):
            max_difference[0]=max(max_difference[0],abs(x-y))
            if not math.isclose(x,y,rel_tol=1e-9,abs_tol=1e-9):mismatches.append(path+':NUMERIC')
        elif x!=y:mismatches.append(path+':EXACT')
    names=['graph_inventory.json','structural_metrics.json','recommendations_frozen.json','controlled_recommendations_frozen.json',
        'intervention_evaluation.json','comparison.json','controlled_comparison.json','policy_blocks.json','failures.json']
    names += [p.relative_to(old/'run_v1').as_posix() for p in (old/'run_v1/datasets').glob('*/*_models.json')]
    names += [p.relative_to(old/'run_v1').as_posix() for p in (old/'run_v1/datasets').glob('*/controlled_*_model.json')]
    names += [p.relative_to(old/'run_v1').as_posix() for p in (old/'run_v1/datasets').glob('*/alpha_selection.json')]
    # Check exact all edge/native/column-order records via inventory above; native coefficients numeric tolerance.
    for name in names:compare(read(old/'run_v1'/name),read(new/name),name);checked.append(dict(path=name,old_sha256=sha(old/'run_v1'/name),replay_sha256=sha(new/name)))
    data_files=list((old/'run_v1/datasets').glob('*/*.csv'))+list((old/'run_v1/do_evaluation').glob('*.csv'))
    for f in data_files:
        rel=f.relative_to(old/'run_v1');g=new/rel
        if f.read_bytes()!=g.read_bytes():
            with f.open(encoding='utf-8-sig') as h:x=list(csv.DictReader(h))
            with g.open(encoding='utf-8-sig') as h:y=list(csv.DictReader(h))
            compare([{k:float(v) for k,v in r.items()} for r in x],[{k:float(v) for k,v in r.items()} for r in y],str(rel))
        checked.append(dict(path=rel.as_posix(),old_sha256=sha(f),replay_sha256=sha(g)))
    for f in (old/'analysis_v1').glob('*.json'):
        if f.name in {'SHA256.json'}:continue
        compare(read(f),read(analysis/f.name),'analysis/'+f.name);checked.append(dict(path='analysis/'+f.name,old_sha256=sha(f),replay_sha256=sha(analysis/f.name)))
    result=dict(status='PASS' if not mismatches else 'FAIL',graph_attempts=144,checked_records=len(checked),max_numeric_difference=max_difference[0],
        tolerance=dict(atol=1e-9,rtol=1e-9),exact_discrete_fields=['edges','unresolved_pairs','status','recommended_action'],
        mismatches=mismatches,comparisons=checked,runtime_and_metadata_excluded=sorted(excluded),
        input_versions_verified=True,actual_reexecution=True)
    Path(a.output).write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(result['status'],len(checked),'records',len(mismatches),'mismatches')
    return 0 if not mismatches else 2
if __name__=='__main__':sys.exit(main())

"""Remove synonymous old control pairs; report repeats as dependent development evidence."""
import argparse,hashlib,json,statistics,sys
from collections import Counter,defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from path_metric_incremental import load
from run_diverse_structure_pilot import save

def unique_pairs(pairs,rows):
    lookup={(r['dataset_id'],r['task_id'],r['variant']):r for r in rows};unique=[];seen=set()
    for p in pairs:
        l=lookup[p['dataset_id'],p['task_id'],p['left']];r=lookup[p['dataset_id'],p['task_id'],p['right']]
        identity=json.dumps([p['dataset_id'],p['task_id'],l['removed_edges'],l['added_edges'],r['removed_edges'],r['added_edges']],sort_keys=True)
        if identity in seen:continue
        seen.add(identity);unique.append(p)
    return unique

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--input',required=True);ap.add_argument('--output',required=True);a=ap.parse_args()
    source=Path(a.input);out=Path(a.output);out.mkdir(parents=True,exist_ok=False)
    original=load(source/'A_matched_pairs.json');controlled=load(source/'A_controlled_outcomes.json');pairs=unique_pairs(original,controlled)
    save(out/'A_unique_pairs.json',pairs);summary=[]
    for scope in ['all','task_specific_key_vs_peripheral','both_paths_key_vs_peripheral']:
        x=[p for p in pairs if scope=='all' or p['task_specific_key_vs_peripheral'] and (scope!='both_paths_key_vs_peripheral' or p['both_paths_preserved'])]
        summary.append(dict(scope=scope,pairs=len(x),structures=len({p['structure_id'] for p in x}),left_worse=sum(p['loss_left_minus_right']>1e-10 for p in x),left_better=sum(p['loss_left_minus_right']< -1e-10 for p in x),ties=sum(abs(p['loss_left_minus_right'])<=1e-10 for p in x)))
    save(out/'A_unique_summary.json',summary)
    # Structure-average differences prevent a large family from winning through row count.
    effects=defaultdict(list)
    for p in pairs:
        if p['task_specific_key_vs_peripheral']:effects[p['left'],p['structure_id']].append(p['loss_left_minus_right'])
    save(out/'A_structure_differences.json',[dict(error=k[0],structure_id=k[1],mean_difference=statistics.mean(v),dependent_pairs=len(v)) for k,v in sorted(effects.items())])
    types=[]
    for name in sorted({r['variant'] for r in controlled}):
        x=[r for r in controlled if r['variant']==name]
        types.append(dict(variant=name,rows=len(x),worsened=sum(r['worsened'] for r in x),large=sum(r['large_deterioration'] for r in x),
            improved=sum(r['improvement']>1e-10 for r in x),unchanged=sum(abs(r['improvement'])<=1e-10 for r in x),max_loss=max(r['analytic_loss'] for r in x)))
    save(out/'A_variant_outcomes.json',types)
    # Check C07 perfect-knowledge response controls against the actual stored BOSS policy.
    discovery=load(source/'B_discovery_outcomes.json');c7=load(source/'B_C07_response_controls.json')
    for r in c7:
        if r['mode']=='original_boss':
            old=next(x for x in discovery if x['dataset_id']==r['dataset_id'] and x['task_id']==r['task_id'] and x['algorithm']=='boss')
            assert old['recommended_action']==r['recommended_action'] and abs(old['analytic_loss']-r['analytic_loss'])<1e-10
    pred=load(source/'C_nested_cv.json')
    save(out/'SUMMARY.json',dict(raw_pairs=len(original),unique_actual_graph_pairs=len(pairs),synonymous_repeats=len(original)-len(pairs),nested_model_choices=dict(Counter(x['selected'] for x in pred['folds'])),c07_original_policy_replayed=True,new_independent_evidence=False,
        note='Deduplication is a transparent audit correction, not new outcome-based graph selection. All original comparisons retained.'))
    save(out/'SHA256.json',{p.relative_to(out).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in out.rglob('*') if p.is_file() and p.name!='SHA256.json'})
    print(json.dumps(load(out/'SUMMARY.json')))
if __name__=='__main__':main()

"""Run only the comparison procedures fixed before the new data were generated."""
from collections import Counter,defaultdict
import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import statistics
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from diverse_metric_analysis import correlations,collinearity,loso,primary_rows
sys.path.insert(0,str(ROOT/'scripts'))
from run_diverse_structure_pilot import save,table


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',default=str(ROOT/'research_runs/diverse_structure_pilot/run_v1'))
    parser.add_argument('--output',default=str(ROOT/'research_runs/diverse_structure_pilot/analysis_v1'));args=parser.parse_args()
    run=Path(args.run).resolve();out=Path(args.output).resolve()
    if out.exists():raise ValueError('NEW_ANALYSIS_DIRECTORY_REQUIRED')
    out.mkdir();plan=json.loads((run/'plan.json').read_text(encoding='utf-8'))
    rows=json.loads((run/'comparison.json').read_text(encoding='utf-8'));controlled=json.loads((run/'controlled_comparison.json').read_text(encoding='utf-8'))
    groups=defaultdict(list)
    for r in rows:groups[r['structure_id'],r['task_id'],r['policy'],r['algorithm']].append(r)
    summary=[]
    for (sid,task,mode,alg),items in sorted(groups.items()):
        valid=[r for r in items if r['row_status']=='EVALUATED']
        summary.append(dict(structure_id=sid,task_id=task,policy=mode,algorithm=alg,attempted=len(items),evaluated=len(valid),
            blocked=len(items)-len(valid),mean_scale_regret=statistics.mean(r['scale_normalized_regret'] for r in valid) if valid else None,
            mean_effect_error=statistics.mean(r['effect_prediction_absolute_error'] for r in valid) if valid else None,
            recommendation_status_counts=dict(Counter(r['recommendation_status'] for r in valid))))
    save(out/'performance_summary.json',summary)
    table(out/'performance_summary.csv',[dict(r,recommendation_status_counts=json.dumps(r['recommendation_status_counts'])) for r in summary])
    primary={(r['graph_id'],r['task_id']):r for r in rows if r['policy']=='confirmed_only' and r['row_status']=='EVALUATED'}
    changes=[]
    for spec in plan['structures']:
        for mode in ['mec_minimax','abstain_on_disagreement']:
            all_items=[r for r in rows if r['structure_id']==spec['structure_id'] and r['policy']==mode]
            valid=[r for r in all_items if r['row_status']=='EVALUATED' and (r['graph_id'],r['task_id']) in primary]
            delta=[r['target_mean_loss']-primary[r['graph_id'],r['task_id']]['target_mean_loss'] for r in valid]
            changes.append(dict(structure_id=spec['structure_id'],policy=mode,attempted=len(all_items),matched_evaluated=len(valid),blocked=len(all_items)-len(valid),
                changed_actions=sum(r['recommended_action']!=primary[r['graph_id'],r['task_id']]['recommended_action'] for r in valid),
                improved=sum(d<-1e-12 for d in delta),worsened=sum(d>1e-12 for d in delta),unchanged=sum(abs(d)<=1e-12 for d in delta)))
    save(out/'policy_paired_changes.json',changes);table(out/'policy_paired_changes.csv',changes)
    corr=correlations(rows,plan);save(out/'correlations.json',corr);table(out/'correlations.csv',corr)
    overlap=collinearity(rows,plan['analysis']['metric_candidates']);save(out/'metric_overlap.json',overlap);table(out/'metric_overlap.csv',overlap)
    predict=loso(rows,plan)
    for key,value in predict.items():
        save(out/('loso_'+key+'.json'),value)
        if isinstance(value,list) and value and isinstance(value[0],dict):table(out/('loso_'+key+'.csv'),value)
    controlled_pairs=[]
    for spec in plan['structures']:
        for cell in spec['datasets']:
            for task in spec['tasks']:
                items=[r for r in controlled if r['dataset_id']==cell['dataset_id'] and r['task_id']==task['task_id'] and r['row_status']=='EVALUATED']
                variants={r['variant']:r for r in items}
                if 'remove_key' in variants and 'remove_peripheral' in variants:
                    a,b=variants['remove_key'],variants['remove_peripheral']
                    controlled_pairs.append(dict(structure_id=spec['structure_id'],dataset_id=cell['dataset_id'],task_id=task['task_id'],
                        identical_skeleton_f1=a['skeleton_f1']==b['skeleton_f1'],identical_direction_f1=a['strict_directed_f1']==b['strict_directed_f1'],
                        key_removed_loss=a['target_mean_loss'],peripheral_removed_loss=b['target_mean_loss'],
                        loss_difference=a['target_mean_loss']-b['target_mean_loss'],scope='artificial fixed graph changes, not learned algorithm output'))
    save(out/'controlled_error_pairs.json',controlled_pairs);table(out/'controlled_error_pairs.csv',controlled_pairs)
    negative=[r for r in rows if r['task_kind']=='negative_control'];save(out/'negative_controls.json',negative)
    inventory=json.loads((run/'graph_inventory.json').read_text(encoding='utf-8'));ledger=json.loads((run/'execution_ledger.json').read_text(encoding='utf-8'))
    summary=dict(structures=8,datasets=48,learning_attempts=len(inventory),learned_graphs=sum(g['status']=='LEARNED' for g in inventory),
        discovery_comparison_rows=len(rows),discovery_evaluated=sum(r['row_status']=='EVALUATED' for r in rows),primary_positive_evaluated=len(primary_rows(rows)),
        controlled_rows=len(controlled),reference_structures_are_hand_designed=True,
        run_wall_seconds=(datetime.fromisoformat(ledger[-1]['utc'])-datetime.fromisoformat(ledger[0]['utc'])).total_seconds(),
        recommendation_failures=dict(Counter(r['row_status'] for r in rows)),correlation_status_counts=dict(Counter(r['status'] for r in corr)),
        loso_rank_status_counts=dict(Counter(r['rank_status'] for r in predict['artifacts'])),
        analysis_code_sha256={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in ['scripts/analyze_diverse_structure_pilot.py','src/diverse_metric_analysis.py']},
        input_summary_sha256=hashlib.sha256((run/'comparison.json').read_bytes()).hexdigest(),
        manufacturing_validated=False,formal_metric_winner=False,analysis_settings_selected_from_holdout=False)
    save(out/'analysis_summary.json',summary)
    save(out/'SHA256.json',{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.iterdir()) if p.is_file() and p.name!='SHA256.json'})
    print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__':main()

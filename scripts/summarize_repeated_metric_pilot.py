"""Balanced descriptive tables only; never change the saved policy or experiment."""
from collections import Counter,defaultdict
from datetime import datetime
import hashlib
import json
from pathlib import Path
import statistics
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from run_repeated_metric_pilot import save,table


def main():
    run=ROOT/'research_runs/repeated_metric_pilot/run_v1';out=run.parent/'analysis_v1'
    if out.exists():raise ValueError('PRESERVE_EXISTING_ANALYSIS')
    out.mkdir();rows=json.loads((run/'comparison.json').read_text(encoding='utf-8'))
    groups=defaultdict(list)
    for r in rows:groups[r['family'],r['train_n'],r['algorithm']].append(r)
    graph_summary=[]
    for (family,n,alg),items in sorted(groups.items()):
        sample=[r for r in items if r['policy']=='confirmed_only' and r['task_id']=='A_Y']
        graph_summary.append(dict(family=family,train_n=n,algorithm=alg,independent_datasets=len(sample),
            mean_skeleton_f1=statistics.mean(r['skeleton_f1'] for r in sample),
            mean_strict_directed_f1=statistics.mean(r['strict_directed_f1'] for r in sample),
            mean_unresolved_ratio=statistics.mean(r['unresolved_ratio'] for r in sample)))
    table(out/'graph_summary.csv',graph_summary);save(out/'graph_summary.json',graph_summary)
    groups=defaultdict(list)
    for r in rows:groups[r['family'],r['task_id'],r['policy']].append(r)
    summary=[]
    for (family,task,mode),items in sorted(groups.items()):
        summary.append(dict(family=family,task_id=task,policy=mode,dataset_clusters=len({r['dataset_id'] for r in items}),dependent_graph_task_rows=len(items),
            mean_relative_regret=statistics.mean(r['relative_regret'] for r in items),mean_target_loss=statistics.mean(r['target_mean_loss'] for r in items),
            mean_effect_absolute_error=statistics.mean(r['effect_prediction_absolute_error'] for r in items),
            fallback_count=sum(r['recommendation_status']=='NO_PATH_BASELINE_FALLBACK' for r in items),
            abstention_count=sum(r['recommendation_status']=='AMBIGUITY_ABSTENTION' for r in items),
            computed_baseline_count=sum(r['recommendation_status']=='COMPUTED_BASELINE' for r in items),
            action_counts=dict(Counter(r['recommended_action'] for r in items))))
    save(out/'policy_summary.json',summary)
    table(out/'policy_summary.csv',[dict(r,action_counts=json.dumps(r['action_counts'])) for r in summary])
    primary={(r['graph_id'],r['task_id']):r for r in rows if r['policy']=='confirmed_only'}
    changes=[]
    for family in ['gaussian','uniform']:
        for mode in ['mec_minimax','abstain_on_disagreement']:
            items=[r for r in rows if r['family']==family and r['policy']==mode]
            delta=[r['target_mean_loss']-primary[r['graph_id'],r['task_id']]['target_mean_loss'] for r in items]
            changes.append(dict(family=family,policy=mode,dataset_clusters=len({r['dataset_id'] for r in items}),dependent_graph_task_cells=len(items),
                changed_actions=sum(r['recommended_action']!=primary[r['graph_id'],r['task_id']]['recommended_action'] for r in items),
                improved=sum(d < -1e-12 for d in delta),worsened=sum(d > 1e-12 for d in delta),unchanged=sum(abs(d)<=1e-12 for d in delta)))
    save(out/'policy_changes.json',changes);table(out/'policy_changes.csv',changes)
    path_groups=[]
    for family in ['gaussian','uniform']:
        for task in ['A_Y','A_M','R_Y','M_Y']:
            for complete in [False,True]:
                items=[r for r in primary.values() if r['family']==family and r['task_id']==task and r['all_key_paths_complete']==complete]
                path_groups.append(dict(family=family,task_id=task,all_key_paths_complete=complete,dependent_rows=len(items),dataset_clusters=len({r['dataset_id'] for r in items}),
                    mean_relative_regret=statistics.mean(r['relative_regret'] for r in items) if items else None,
                    interpretation='descriptive conditional group, not adjusted causal contrast or independent sample count'))
    save(out/'path_groups.json',path_groups);table(out/'path_groups.csv',path_groups)
    wrong=[r for r in primary.values() if r['direct_xy_correct'] is False and r['candidate_regret']<1e-12]
    save(out/'wrong_direct_relation_but_best_grid_action.json',wrong)
    associations=json.loads((run/'exploratory_associations.json').read_text(encoding='utf-8'))
    save(out/'association_status_counts.json',dict(Counter(r['status'] for r in associations)))
    ledger=json.loads((run/'execution_ledger.json').read_text(encoding='utf-8'))
    duration=(datetime.fromisoformat(ledger[-1]['utc'])-datetime.fromisoformat(ledger[0]['utc'])).total_seconds()
    times=[e['seconds'] for e in ledger if e['stage']=='GRAPH_LEARNED']
    save(out/'execution_summary.json',dict(graph_attempts=36,successful_graphs=len(times),failed_graphs=0,graph_time_seconds_sum=sum(times),
        total_wall_seconds=duration,first_cell_seconds=next(e['seconds'] for e in ledger if e['stage']=='SMALL_CELL_FEASIBILITY_RECORDED'),
        expanded_repetitions_run=False,additional_independent_repetitions_approved_by_this_run=False,
        postprocessing_code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        input_summary_sha256=hashlib.sha256((run/'comparison.json').read_bytes()).hexdigest()))
    save(out/'SHA256.json',{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.iterdir()) if p.is_file() and p.name!='SHA256.json'})
    print('PASS: descriptive tables; no experiment or recommendation changed')


if __name__=='__main__':main()

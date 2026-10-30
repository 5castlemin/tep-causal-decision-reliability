"""Verify generic FCM records, no truth leakage, and whole-structure holdouts."""
import csv
import hashlib
import json
import math
from pathlib import Path
import statistics
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from asset_preservation import assert_protected_preserved
from diverse_structure_pilot import reference_edges,score_graph,analytic_response
from diverse_metric_analysis import loso,primary_rows
from repeated_metric_pilot import recommend_policy,acyclic,colliders

BASE=ROOT/'research_runs/diverse_structure_pilot';RUN=BASE/'run_v1'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def close(a,b):assert math.isclose(a,b,rel_tol=1e-9,abs_tol=1e-9),(a,b)
def raw(p):
    with p.open(encoding='utf-8-sig',newline='') as f:return [{k:float(v) for k,v in r.items()} for r in csv.DictReader(f)]
def code_matches(path,expected):
    b=path.read_bytes();lf=b.replace(b'\r\n',b'\n')
    return expected in {hashlib.sha256(x).hexdigest() for x in [b,lf,lf.replace(b'\n',b'\r\n')]}
def check_rows(data,noise,spec,action=None,value=None):
    assert len(data)==len(noise)
    for x,u in zip(data,noise):
        if action is not None:
            assert 'u_'+action not in u
            for tag in ['seed','batch','sample_id']:assert x[tag]==u[tag]
        for node in spec['nodes']:
            expected=value if node==action else u['u_'+node]+sum(e['coefficient']*x[e['source']] for e in spec['edges'] if e['target']==node)
            close(x[node],expected)


def validate():
    plan=read(BASE/'PLAN_v1.json');assert plan==read(RUN/'plan.json');specs={s['structure_id']:s for s in plan['structures']}
    assert len(specs)==8 and sum(len(s['datasets']) for s in specs.values())==48
    env=read(RUN/'environment.json');assert env['plan_sha256']==sha(BASE/'PLAN_v1.json')
    assert env['source_commit']==plan['source_commit'] and env['upstream_source_sha256']==plan['source_sha256']
    for name,digest in env['code_sha256'].items():assert code_matches(ROOT/name,digest),name
    for name,digest in read(RUN/'SHA256.json').items():assert sha(RUN/name)==digest,name
    for directory in ['reference_graphs_v1','figures_v1','analysis_v1']:
        for name,digest in read(BASE/directory/'SHA256.json').items():assert sha(BASE/directory/name)==digest,name
    protected=['graphs/final','experiments','data','RESEARCH_DESIGN.md','docs/audit/step6_main_table.csv',
        'research_runs/first_integrated_pilot','research_runs/repeated_metric_pilot','research_runs/env_acceptance','research_runs/decision_mvp',
        'src/integrated_pilot.py','src/repeated_metric_pilot.py','src/decision_mvp.py','src/fcm_acceptance_adapter.py','src/pilot_fit.py']
    assert_protected_preserved(ROOT, plan['base_commit'], protected)
    ledger=read(RUN/'execution_ledger.json');first=next(e for e in ledger if e['stage']=='FIRST_TWO_GENERATORS_PASSED')
    all_eight=next(e for e in ledger if e['stage']=='ALL_EIGHT_GENERATORS_PASSED')
    assert first['sequence']<all_eight['sequence']<min(e['sequence'] for e in ledger if e['stage']=='GRAPH_ATTEMPT_STARTED')
    freeze=next(e for e in ledger if e['stage']=='ALL_RECOMMENDATIONS_FROZEN')
    assert freeze['sha256']==sha(RUN/'recommendations_frozen.json')
    assert freeze['controlled_sha256']==sha(RUN/'controlled_recommendations_frozen.json')
    assert freeze['sequence']<min(e['sequence'] for e in ledger if e['stage']=='ACTION_HOLDOUT_GENERATED')
    seeds=set();datasets={};model_cache={}
    for sid,spec in specs.items():
        a=read(RUN/'acceptance'/sid/'acceptance.json');assert a['status']=='PASS'
        assert all(all(r['checks'].values()) for r in a['records'])
        assert {tuple(e) for e in a['records'][0]['metadata']['returned_edges']}==reference_edges(spec)
        assert 5<=len(spec['nodes'])<=8 and acyclic(spec['nodes'],reference_edges(spec))
        for cell in spec['datasets']:
            folder=RUN/'datasets'/cell['dataset_id'];datasets[cell['dataset_id']]=(spec,cell,folder)
            for split in ['train','validation']:
                assert cell[split+'_seed'] not in seeds;seeds.add(cell[split+'_seed'])
                data=raw(folder/f'{split}.csv');noise=raw(folder/f'{split}_noise.csv')
                assert len(data)==cell[split+'_n'];check_rows(data,noise,spec)
            selection=read(folder/'alpha_selection.json')
            if selection['scores']:
                assert selection['selected_alpha']==min(selection['scores'],key=lambda r:(r['mean_mse'],-r['alpha']))['alpha']
    graphs=read(RUN/'graph_inventory.json');assert len(graphs)==144
    graphmap={g['graph_id']:g for g in graphs};assert len(graphmap)==144
    assert sum(e['stage']=='GRAPH_ATTEMPT_STARTED' for e in ledger)==144
    for gid,g in graphmap.items():
        spec,cell,folder=datasets[g['dataset_id']];cfg=read(folder/f"{g['algorithm']}_learner_config.json")
        assert set(cfg)=={'algorithm','seed','names','algorithms','families','train_sha256'}
        assert cfg['train_sha256']==sha(folder/'train.csv') and cfg['names']==spec['algorithm_column_order']
        assert cfg['seed']==cell['algorithm_seed'] and cfg['algorithm']==g['algorithm']
        if g['status']!='LEARNED':continue
        edges={tuple(e) for e in g['confirmed_edges']};unknown={frozenset(e) for e in g['unresolved_pairs']}
        native=g['native'];names=g['column_order']
        if g['algorithm']=='directlingam':
            derived={(names[j],names[i]) for i in range(len(names)) for j in range(len(names)) if i!=j and abs(native['adjacency_child_parent'][i][j])>=plan['algorithms']['directlingam']['edge_abs_threshold']}
            assert derived==edges and not unknown
        else:
            derived=set();unresolved=set()
            for edge in native['native_edges']:
                a,b=edge['node1'],edge['node2'];ends=edge['endpoint1'],edge['endpoint2']
                if ends==('TAIL','ARROW'):derived.add((a,b))
                elif ends==('ARROW','TAIL'):derived.add((b,a))
                else:unresolved.add(frozenset((a,b)))
            assert derived==edges and unresolved==unknown
        path=folder/f"{g['algorithm']}_models.json"
        if not path.exists():continue
        models=read(path);model_cache[gid]=models
        assert models['primary']['alpha']==read(folder/'alpha_selection.json')['selected_alpha']
        assert {(p['source'],eq['target']) for eq in models['primary']['equations'] for p in eq['parents']}==edges
        pairs={frozenset(e) for e in edges}|unknown
        if models['auxiliary_block']:assert models['extensions']==[]
        else:
            assert 1<=len(models['extensions'])<=plan['policy']['mec_max_extensions']
            for extension in models['extensions']:
                e={tuple(e) for e in extension['edges']}
                assert edges<=e and {frozenset(x) for x in e}==pairs and len(e)==len(pairs)
                assert acyclic(spec['nodes'],e) and colliders(e,pairs)==colliders(edges,pairs)
                assert extension['model']['alpha']==models['primary']['alpha']
    evaluation=read(RUN/'intervention_evaluation.json');expected_conditions=sum(len({t['action'] for t in s['tasks']})*6 for s in specs.values())
    assert len(evaluation)==expected_conditions;total=0
    for tag,record in evaluation.items():
        spec=specs[record['structure_id']];data=raw(RUN/'do_evaluation'/f'{tag}.csv');noise=raw(RUN/'do_evaluation'/f'{tag}_noise.csv')
        assert len(data)==768;total+=len(data);check_rows(data,noise,spec,record['action'],record['value'])
        for batch in record['batches']:
            assert batch['seed'] not in seeds;seeds.add(batch['seed'])
            assert sum(r['seed']==batch['seed'] for r in data)==256
        oracle=analytic_response(spec,record['action'],record['value']);assert oracle==record['post_freeze_analytic_mean']
        for node,stat in record['statistics'].items():
            vals=[r[node] for r in data];close(stat['mean'],statistics.mean(vals));close(stat['se'],statistics.stdev(vals)/math.sqrt(len(vals)))
            close(stat['ci_low'],stat['mean']-1.96*stat['se']);close(stat['ci_high'],stat['mean']+1.96*stat['se'])
    assert total==78336
    rows=read(RUN/'comparison.json');controlled=read(RUN/'controlled_comparison.json')
    assert len(rows)==sum(len(s['datasets'])*3*len(s['tasks'])*3 for s in specs.values())==918
    expected_controls=sum(len(s['datasets'])*5*sum(t['task_kind']!='negative_control' for t in s['tasks']) for s in specs.values() if s['structure_id'] in plan['controlled_errors']['structures'])
    assert len(controlled)==expected_controls==120
    frozen=read(RUN/'recommendations_frozen.json')+read(RUN/'controlled_recommendations_frozen.json')
    frozen_map={(r['graph_id'],r['task_id'],r['policy']):r for r in frozen}
    for row in rows+controlled:
        key=row['graph_id'],row['task_id'],row['policy'];original=frozen_map[key]
        if row['row_status']!='EVALUATED':assert original['row_status']!='FROZEN';continue
        spec=specs[row['structure_id']];task=next(t for t in spec['tasks'] if t['task_id']==row['task_id'])
        if row['source_type']=='discovery':
            g=graphmap[row['graph_id']];edges={tuple(e) for e in g['confirmed_edges']};unknown={frozenset(e) for e in g['unresolved_pairs']};models=model_cache[row['graph_id']]
            primary=row['policy']=='confirmed_only'
            m=[models['primary']] if primary else [x['model'] for x in models['extensions']]
            es=[edges] if primary else [{tuple(e) for e in x['edges']} for x in models['extensions']]
        else:
            folder=datasets[row['dataset_id']][2];record=read(folder/f"controlled_{row['variant']}_model.json")
            assert record['source_type']=='controlled_error';edges={tuple(e) for e in record['edges']};unknown=set();m=[record['model']];es=[edges]
        scores=score_graph(edges,unknown,spec,task)
        for name,expected in scores.items():assert row[name]==expected,name
        rec=recommend_policy(m,es,task,dict(plan['policy'],**{k:task[k] for k in ['action_values','reference_action','cost_weight']}),row['policy'])
        assert rec==original['recommendation']
        assert row['recommendation_status']==rec['status'] and row['recommended_action']==rec['selected']['action']
        prefix=row['structure_id']+'__'+row['action']+'__';i=task['action_values'].index(row['recommended_action']);target=row['target']
        actual=evaluation[prefix+str(i)]['statistics'][target];baseline=evaluation[prefix+'reference']['statistics'][target]
        losses=[(evaluation[prefix+str(j)]['statistics'][target]['mean']-task['target_value'])**2+task['cost_weight']*(v-task['reference_action'])**2 for j,v in enumerate(task['action_values'])]
        close(row['target_mean_loss'],losses[i]);close(row['candidate_regret'],losses[i]-min(losses));close(row['scale_normalized_regret'],row['candidate_regret']/task['loss_scale']**2)
        floor=.01*task['loss_scale']**2;ref=(baseline['mean']-task['target_value'])**2
        assert (row['relative_regret'] is None)==(ref<floor)
        if ref>=floor:close(row['relative_regret'],row['candidate_regret']/ref)
        close(row['actual_effect'],actual['mean']-baseline['mean']);close(row['effect_se'],math.hypot(actual['se'],baseline['se']))
        close(row['effect_prediction_absolute_error'],abs(row['predicted_effect']-row['actual_effect']))
        assert not row['squared_individual_error_mean_computed']
    analysis=BASE/'analysis_v1';summary=read(analysis/'analysis_summary.json')
    assert summary['learning_attempts']==144 and not summary['formal_metric_winner']
    for path,digest in summary['analysis_code_sha256'].items():assert code_matches(ROOT/path,digest)
    artifacts=read(analysis/'loso_artifacts.json');predictions=read(analysis/'loso_predictions.json')
    for artifact in artifacts:
        held=artifact['held_out_structure'];assert held not in artifact['training_structures']
        assert set(artifact['training_structures'])==set(specs)-{held}
        assert artifact['alpha']==.01 and artifact['structure_equal_weights']
    assert all(r['structure_id']==r['held_out_structure'] for r in predictions)
    recalculated=loso(rows,plan)['macro_scores'];recorded=read(analysis/'loso_macro_scores.json')
    for a,b in zip(recalculated,recorded):
        assert a['model']==b['model'] and a['heldout_structures']==8
        close(a['macro_mae'],b['macro_mae']);close(a['macro_rmse'],b['macro_rmse'])
    assert all(r['task_kind']!='negative_control' and r['source_type']=='discovery' for r in primary_rows(rows))
    state=read(ROOT/'docs/research_state.json')['diverse_structure_pilot']
    assert state['structures']==8 and state['learned_graphs']==144 and state['evaluated_rows']==918
    assert not state['manufacturing_validated'] and not state['research_design_changed']
    print('[PASS] 8 FCM source/observed/do contracts;144 attempts;48 datasets;native graph/MEC/policy freeze;78336 raw do;denominator guards;controlled graphs separated;8 whole-structure folds;old assets unchanged')

if __name__=='__main__':validate()

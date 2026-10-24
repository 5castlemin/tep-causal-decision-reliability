"""Check preserved raw data and every recommendation/evaluation, not just status labels."""
import csv
import hashlib
import json
import math
from pathlib import Path
import statistics
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from repeated_metric_pilot import (acyclic,colliders,recommend_policy,quality,exploratory_associations)

RUN=ROOT/'research_runs/repeated_metric_pilot/run_v1'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def close(a,b):assert math.isclose(a,b,rel_tol=1e-10,abs_tol=1e-10),(a,b)
def csvrows(p):
    with p.open(encoding='utf-8-sig',newline='') as f:return [{k:float(v) for k,v in r.items()} for r in csv.DictReader(f)]


def check_equations(data,noise,action=None,value=None):
    assert len(data)==len(noise)
    for x,u in zip(data,noise):
        if action is not None:
            close(x[action],value);assert 'u_'+action not in u
            for key in ['batch','seed','sample_id']:assert x[key]==u[key]
        expected=dict(R=value if action=='R' else u['u_R'],
            A=value if action=='A' else 2*x['R']+u['u_A'],
            M=value if action=='M' else 3*x['A']+u['u_M'],
            Y=x['M']+x['R']+u['u_Y'])
        for node,target in expected.items():close(x[node],target)


def validate():
    plan=read(RUN/'plan.json');assert plan==read(ROOT/'research_runs/repeated_metric_pilot/PLAN_v1.json')
    env=read(RUN/'environment.json');assert env['base_main']==plan['base_main']
    assert digest(ROOT/'research_runs/repeated_metric_pilot/PLAN_v1.json')==env['plan_sha256']
    assert env['upstream_source_sha256']==plan['source_sha256']
    for name,expected in read(RUN/'SHA256.json').items():assert digest(RUN/name)==expected,name
    for name,expected in env['code_sha256'].items():
        content=(ROOT/name).read_bytes();lf=content.replace(b'\r\n',b'\n')
        assert expected in {hashlib.sha256(v).hexdigest() for v in [content,lf,lf.replace(b'\n',b'\r\n')]},name
    integration=ROOT/'research_runs/repeated_metric_pilot/integration'
    merges=read(integration/'merge_commits.json');previous=merges['baseline_main']
    for entry in merges['merges']:
        parents=subprocess.check_output(['git','show','-s','--format=%P',entry['merge_commit']],cwd=ROOT,text=True).split()
        assert parents==[previous,entry['head']]
        previous=entry['merge_commit']
    assert previous==plan['base_main']==merges['final_main']
    assert read(integration/'main_validation.json')['protected_assets_preserved']
    protected=['graphs/final','experiments','data','RESEARCH_DESIGN.md','docs/audit/step6_main_table.csv',
        'research_runs/first_integrated_pilot','research_runs/env_acceptance','research_runs/decision_mvp']
    assert not subprocess.check_output(['git','diff',plan['base_main'],'--name-only','--',*protected],cwd=ROOT,text=True).strip()
    acceptance=read(RUN/'api_acceptance/api_acceptance.json');assert acceptance['status']=='PASS'
    assert len(acceptance['records'])==12 and all(all(r['checks'].values()) for r in acceptance['records'])
    ledger=read(RUN/'execution_ledger.json');assert ledger[0]['stage']=='PLAN_FROZEN'
    freeze=next(e for e in ledger if e['stage']=='ALL_RECOMMENDATIONS_FROZEN')
    assert freeze['sha256']==digest(RUN/'recommendations_frozen.json')
    assert all(e['sequence']>freeze['sequence'] for e in ledger if e['stage']=='ACTION_HOLDOUT_GENERATED')
    assert read(RUN/'failures.json')==[]
    graphs=read(RUN/'graph_inventory.json');assert len(graphs)==36 and all(g['status']=='LEARNED' for g in graphs)
    graphmap={g['graph_id']:g for g in graphs};seeds=set();models={}
    for cell in plan['datasets']:
        folder=RUN/'datasets'/cell['dataset_id']
        for split in ['train','validation']:
            assert cell[split+'_seed'] not in seeds;seeds.add(cell[split+'_seed'])
            data=csvrows(folder/f'{split}.csv');noise=csvrows(folder/f'{split}_noise.csv')
            assert len(data)==cell[split+'_n'];check_equations(data,noise)
        selection=read(folder/'alpha_selection.json')
        best=min(selection['scores'],key=lambda r:(r['mean_validation_mse'],-r['alpha']))['alpha']
        assert selection['selected_alpha']==best
        if cell['family']=='gaussian':assert 'directlingam' not in selection['selection_algorithms']
        for alg in ['pc','boss','directlingam']:
            g=graphmap[cell['dataset_id']+'__'+alg];edges={tuple(e) for e in g['confirmed_edges']};unresolved={frozenset(e) for e in g['unresolved_pairs']}
            record=read(folder/f'{alg}_models.json');assert record['extension_failure'] is None
            assert record['primary']['alpha']==best
            assert {(p['source'],eq['target']) for eq in record['primary']['equations'] for p in eq['parents']}==edges
            pairs={frozenset(e) for e in edges}|unresolved
            for extension in record['extensions']:
                dag={tuple(e) for e in extension['edges']}
                assert edges<=dag and {frozenset(e) for e in dag}==pairs and len(dag)==len(pairs)
                assert acyclic(plan['nodes'],dag) and colliders(dag,pairs)==colliders(edges,pairs)
                assert extension['model']['alpha']==best
            models[g['graph_id']]=record
    evaluation=read(RUN/'intervention_evaluation.json');assert len(evaluation)==36
    total=0
    for tag,entry in evaluation.items():
        data=csvrows(RUN/'do_evaluation'/f'{tag}.csv');noise=csvrows(RUN/'do_evaluation'/f'{tag}_noise.csv')
        assert len(data)==1536;total+=len(data);check_equations(data,noise,entry['action'],entry['value'])
        for batch in entry['batches']:
            assert batch['seed'] not in seeds;seeds.add(batch['seed'])
            assert sum(r['seed']==batch['seed'] for r in data)==512
        for node,stats in entry['statistics'].items():
            values=[r[node] for r in data];close(stats['mean'],statistics.mean(values));close(stats['se'],statistics.stdev(values)/math.sqrt(len(values)))
            close(stats['ci_low'],stats['mean']-1.96*stats['se']);close(stats['ci_high'],stats['mean']+1.96*stats['se'])
    assert total==55296
    rows=read(RUN/'comparison.json');frozen=read(RUN/'recommendations_frozen.json');assert len(rows)==len(frozen)==432
    bykey={(r['graph_id'],r['task_id'],r['policy']):r for r in frozen}
    taskmap={t['task_id']:t for t in plan['tasks']}
    for row in rows:
        graph=graphmap[row['graph_id']];task=taskmap[row['task_id']];record=models[row['graph_id']]
        edges={tuple(e) for e in graph['confirmed_edges']};unresolved={frozenset(e) for e in graph['unresolved_pairs']}
        expected=quality(edges,unresolved,plan['reference_edges'],task)
        for key,value in expected.items():assert row[key]==value,key
        primary=row['policy']=='confirmed_only'
        m=[record['primary']] if primary else [e['model'] for e in record['extensions']]
        es=[edges] if primary else [{tuple(e) for e in ext['edges']} for ext in record['extensions']]
        rec=recommend_policy(m,es,task,plan['policy'],row['policy'])
        assert rec==bykey[row['graph_id'],row['task_id'],row['policy']]['recommendation']
        assert row['recommended_action']==rec['selected']['action'] and row['recommendation_status']==rec['status']
        prefix=row['family']+'__'+row['action']+'__';target=row['target'];grid=plan['policy']['action_values']
        actual=evaluation[prefix+str(grid.index(row['recommended_action']))]['statistics'][target]
        base=evaluation[prefix+'independent_reference']['statistics'][target]
        losses=[(evaluation[prefix+str(i)]['statistics'][target]['mean']-task['target_value'])**2+plan['policy']['cost_weight']*v**2 for i,v in enumerate(grid)]
        loss=(actual['mean']-task['target_value'])**2+plan['policy']['cost_weight']*row['recommended_action']**2
        close(row['actual_target_mean'],actual['mean']);close(row['target_mean_loss'],loss)
        close(row['candidate_regret'],loss-min(losses));close(row['relative_regret'],(loss-min(losses))/max((base['mean']-task['target_value'])**2,1e-12))
        close(row['effect_se'],math.hypot(actual['se'],base['se']));close(row['actual_effect'],actual['mean']-base['mean'])
        close(row['effect_prediction_absolute_error'],abs(row['predicted_effect']-row['actual_effect']))
        assert row['squared_individual_error_mean_not_computed']
    recorded=read(RUN/'exploratory_associations.json');recomputed=exploratory_associations(rows,plan)
    assert len(recorded)==len(recomputed)
    for a,b in zip(recorded,recomputed):
        assert set(a)==set(b)
        for key in a:
            if isinstance(a[key],float):close(a[key],b[key])
            else:assert a[key]==b[key],key
    assert read(RUN/'analysis_scope.json')['status']=='INSUFFICIENT_INDEPENDENT_REPETITIONS'
    analysis=RUN.parent/'analysis_v1'
    for name,expected in read(analysis/'SHA256.json').items():assert digest(analysis/name)==expected,name
    state=read(ROOT/'docs/research_state.json')
    assert all(state['github_current'][f'pr{n}_status']=='MERGED' for n in range(6,12))
    assert state['repeated_metric_pilot']['learned_graphs']==36 and not state['repeated_metric_pilot']['manufacturing_validated']
    print('[PASS] ordered merge lineage; original assets; 12 independent datasets/36 learned graphs; 432 policies; 55296 raw do samples; no GT orientation; policy freeze; losses/SE/cluster-aware descriptive records')


if __name__=='__main__':validate()

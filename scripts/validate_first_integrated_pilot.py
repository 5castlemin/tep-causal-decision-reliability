"""Offline record checks: raw data, independent evaluation, policy and provenance."""
import csv
import hashlib
import json
import math
import statistics
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/'research_runs/first_integrated_pilot/run_v1'
def read(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def close(a,b):assert math.isclose(a,b,rel_tol=1e-11,abs_tol=1e-11),(a,b)
def raw(path):
    with path.open(encoding='utf-8-sig',newline='') as f:return [{k:float(v) for k,v in r.items()} for r in csv.DictReader(f)]


def validate():
    plan=read(RUN/'plan.json');assert plan==read(ROOT/'research_runs/first_integrated_pilot/PLAN_v1.json')
    manifest=read(RUN/'SHA256.json')
    for name,digest in manifest.items():assert hashlib.sha256((RUN/name).read_bytes()).hexdigest()==digest,name
    env=read(RUN/'environment.json')
    assert env['upstream_module_sha256']==plan['source_sha256']
    assert env['source_commit']==plan['source_commit']
    for name,digest in env['code_sha256'].items():
        content=(ROOT/name).read_bytes();lf=content.replace(b'\r\n',b'\n')
        # Legacy shared source checkout may normalize LF/CRLF. No other source difference is accepted.
        assert digest in {hashlib.sha256(v).hexdigest() for v in [content,lf,lf.replace(b'\n',b'\r\n')]},name
    ledger=read(RUN/'execution_ledger.json');assert ledger[0]['stage']=='PLAN_FROZEN'
    summary=read(RUN/'summary.json');assert len(summary)==6 and read(RUN/'failures.json')==[]
    seeds=set()
    for family in ['gaussian','uniform']:
        folder=RUN/family;acc=read(folder/'acceptance/acceptance.json');assert acc['status']=='PASS'
        assert all(all(r['checks'].values()) for r in acc['records'])
        events={e['stage']:e for e in ledger if e.get('family')==family}
        assert events['ACCEPTANCE']['sequence']<events['GRAPH_LEARNED']['sequence']<events['RECOMMENDATIONS_FROZEN']['sequence']<events['HOLDOUT_EVALUATED']['sequence']
        frozen=folder/'recommendations_frozen.json';digest=hashlib.sha256(frozen.read_bytes()).hexdigest()
        assert digest==events['RECOMMENDATIONS_FROZEN']['sha256']==events['HOLDOUT_EVALUATED']['recommendations_sha256']
        for split in ['train','validation']:
            rows=raw(folder/f'{split}.csv');assert len(rows)==plan['data'][split+'_n']
            seed=read(folder/f'{split}_generation.json')['seed'];assert seed not in seeds;seeds.add(seed)
        evaluation=read(folder/'intervention_evaluation.json')
        for tag,entry in evaluation.items():
            values=[]
            for j,batch in enumerate(entry['batches']):
                seed=batch['seed'];assert seed not in seeds;seeds.add(seed)
                data=raw(folder/f'{tag}_batch{j}.csv');noise=raw(folder/f'{tag}_batch{j}_noise.csv')
                assert len(data)==len(noise)==plan['evaluation']['n_per_batch']
                for row,u in zip(data,noise):
                    assert list(row)==plan['nodes']
                    close(row['A'],entry['action']);close(row['R'],u['u_R']);close(row['M'],3*row['A']+u['u_M'])
                    close(row['Y'],row['M']+row['R']+u['u_Y']);assert 'u_A' not in u
                values.extend(r['Y'] for r in data)
            s=entry['statistics'];assert s['n']==len(values)==3072
            close(s['mean'],statistics.mean(values));close(s['se'],statistics.stdev(values)/math.sqrt(len(values)))
            # Analytic E[Y|do(A=a)]=3a is an independent post-run equation check, never learner input.
            assert abs(s['mean']-3*entry['action'])<0.15
        recommendations=read(frozen);metrics=read(folder/'structural_metrics.json')
        reference=evaluation['independent_reference']['statistics'];p=plan['policy']
        losses={k:(v['statistics']['mean']-p['target_value'])**2+p['cost_weight']*v['action']**2 for k,v in evaluation.items() if k!='independent_reference'}
        for row in [r for r in summary if r['family']==family]:
            alg=row['algorithm'];rec=recommendations[alg];g=read(folder/f'{alg}_graph.json')
            edges={tuple(e) for e in g['confirmed_edges']};unres={frozenset(e) for e in g['unresolved_pairs']}
            native=g['native'];names=g['column_order']
            if alg=='directlingam':
                derived={(names[j],names[i]) for i in range(4) for j in range(4) if i!=j and abs(native['adjacency_child_parent'][i][j])>=plan['algorithms'][alg]['edge_abs_threshold']}
                assert derived==edges and not unres
            else:
                derived=set();ambiguous=set()
                for e in native['native_edges']:
                    a,b=e['node1'],e['node2'];ends=e['endpoint1'],e['endpoint2']
                    if ends==('TAIL','ARROW'):derived.add((a,b))
                    elif ends==('ARROW','TAIL'):derived.add((b,a))
                    else:ambiguous.add(frozenset((a,b)))
                assert derived==edges and ambiguous==unres
            truth={tuple(e) for e in plan['reference_edges']};pairs={frozenset(e) for e in edges}|unres
            close(row['skeleton_f1'],2*len(pairs&{frozenset(e) for e in truth})/(len(pairs)+len(truth)))
            close(row['strict_directed_f1'],2*len(edges&truth)/(len(pairs)+len(truth)))
            path=list(zip(plan['metrics']['key_path'],plan['metrics']['key_path'][1:]))
            close(row['key_path_edge_recall'],sum(e in edges for e in path)/len(path))
            model=read(folder/f'{alg}_model.json')
            assert model['alpha']==read(folder/'alpha_selection.json')['selected_alpha']
            assert {(p['source'],eq['target']) for eq in model['equations'] for p in eq['parents']}==edges
            # Independently propagate structural means, replacing A's equation.
            for candidate in rec['candidates']:
                pending={eq['target']:eq for eq in model['equations']};z={}
                while pending:
                    ready=[n for n,eq in pending.items() if n=='A' or all(p['source'] in z for p in eq['parents'])]
                    assert ready,'CYCLIC_MODEL'
                    for n in ready:
                        eq=pending.pop(n)
                        z[n]=((candidate['action']-model['scaler_mean']['A'])/model['scaler_std']['A'] if n=='A' else eq['intercept_standardized']+sum(p['coefficient_standardized']*z[p['source']] for p in eq['parents']))
                predicted=z['Y']*model['scaler_std']['Y']+model['scaler_mean']['Y']
                close(candidate['predicted_y'],predicted)
                close(candidate['objective'],(predicted-p['target_value'])**2+p['cost_weight']*candidate['action']**2)
            if row['recommendation_status']=='RECOMMENDED':
                assert rec['selected']==min(rec['candidates'],key=lambda c:(c['objective'],abs(c['action']),c['action']))
            assert row['recommended_a']==rec['selected']['action']
            assert row['skeleton_f1']==metrics[alg]['skeleton_f1']
            if row['recommendation_status']=='NO_CONFIRMED_PATH_BASELINE_FALLBACK':assert row['recommended_a']==0 and not row['action_target_reachable']
            i=p['action_values'].index(row['recommended_a']);actual=evaluation[f'action_{i}']['statistics']
            close(row['actual_mean_y'],actual['mean']);close(row['actual_effect'],actual['mean']-reference['mean'])
            close(row['effect_se'],math.hypot(actual['se'],reference['se']))
            close(row['absolute_effect_prediction_error'],abs(row['predicted_effect']-row['actual_effect']))
            close(row['actual_goal_loss'],losses[f'action_{i}']);close(row['empirical_candidate_regret'],losses[f'action_{i}']-min(losses.values()))
            assert set(row).isdisjoint({'p_value','correlation','recovery','safety'})
            assert g['column_order']==plan['algorithm_column_order']
    print('[PASS] 6 learned graphs; raw do/noise reconstruction; seed separation; freeze-before-holdout; metrics/loss/SE; code/data hashes')


if __name__=='__main__':validate()

"""Validate stored evidence. This does not re-run external discovery libraries."""
import csv,gzip,hashlib,io,json,math,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'));sys.path.insert(0,str(ROOT/'scripts'))
from asset_preservation import assert_protected_preserved
from independent_confirmation import freeze_models,predict_frozen,clustered_comparison,select_controls
from diverse_structure_pilot import reference_edges,score_graph
from repeated_metric_pilot import recommend_policy,consistent_extensions

BASE=ROOT/'research_runs/independent_confirmation';RUN=BASE/'run_v1';ANALYSIS=BASE/'analysis_v1'
def raw(p):
    return p.read_bytes() if p.exists() else gzip.decompress(Path(str(p)+'.gz').read_bytes())
def read(p):return json.loads(raw(p).decode('utf-8-sig'))
def sha(p):return hashlib.sha256(raw(p)).hexdigest()
def close(x,y):assert math.isclose(x,y,abs_tol=1e-9,rel_tol=1e-9),(x,y)
def compare(a,b):
    if isinstance(a,dict):
        assert set(a)==set(b)
        for k in a:compare(a[k],b[k])
    elif isinstance(a,list):
        assert len(a)==len(b)
        for x,y in zip(a,b):compare(x,y)
    elif isinstance(a,(float,int)) and not isinstance(a,bool):close(a,b)
    else:assert a==b,(a,b)
def rows(p):return list(csv.DictReader(io.StringIO(raw(p).decode('utf-8-sig'))))
def validate():
    if (BASE/'FINAL_SHA256.json').exists():
        for path,digest in read(BASE/'FINAL_SHA256.json').items():assert hashlib.sha256((BASE/path).read_bytes()).hexdigest()==digest,path
    for record in read(RUN/'COMPRESSION.json'):
        compressed=(RUN/record['compressed']).read_bytes();uncompressed=gzip.decompress(compressed)
        assert hashlib.sha256(compressed).hexdigest()==record['compressed_sha256']
        assert hashlib.sha256(uncompressed).hexdigest()==record['original_sha256']
        assert len(uncompressed)==record['original_bytes'] and len(compressed)==record['compressed_bytes']
    replay=read(BASE/'REPLAY_COMPARISON.json');assert replay['status']=='PASS' and replay['graph_attempts']==144 and not replay['mismatches']
    plan=read(BASE/'PLAN_v1.json');freeze=read(BASE/'FREEZE.json');assert sha(BASE/'PLAN_v1.json')==freeze['plan_sha256']
    assert plan==read(RUN/'plan.json') and len(plan['structures'])==12
    for name,h in plan['frozen_code_sha256'].items():assert sha(ROOT/name)==h,name
    models=read(BASE/plan['confirmation_analysis']['frozen_models']);assert sha(BASE/plan['confirmation_analysis']['frozen_models'])==plan['frozen_models_sha256']
    compare(models,freeze_models(read(ROOT/'research_runs/diverse_structure_pilot/run_v1/comparison.json')))
    assert all(m['training_structures']==['S'+str(i) for i in range(1,9)] for m in models.values())
    for folder in [RUN,ANALYSIS,BASE/'exploratory_diagnostics_v1']:
        for path,h in read(folder/'SHA256.json').items():assert sha(folder/path)==h,path
    ledger=read(RUN/'execution_ledger.json');completed=next(x for x in ledger if x['stage']=='COMPLETED')
    from datetime import datetime
    assert datetime.fromisoformat(freeze['utc'])<=datetime.fromisoformat(ledger[0]['utc'])
    assert completed['graph_attempts']==216
    assert next(x['sequence'] for x in ledger if x['stage']=='ALL_TWELVE_GENERATORS_PASSED')<min(x['sequence'] for x in ledger if x['stage']=='GRAPH_ATTEMPT_STARTED')
    frozen=next(x for x in ledger if x['stage']=='ALL_RECOMMENDATIONS_FROZEN')
    assert frozen['sha256']==sha(RUN/'recommendations_frozen.json') and frozen['controlled_sha256']==sha(RUN/'controlled_recommendations_frozen.json')
    assert frozen['sequence']<min(x['sequence'] for x in ledger if x['stage']=='ACTION_HOLDOUT_GENERATED')
    assert read(RUN/'environment.json')['plan_sha256']==sha(BASE/'PLAN_v1.json')
    assert read(RUN/'environment.json')['versions']==read(ROOT/'research_runs/diverse_structure_pilot/run_v1/environment.json')['versions']
    tasks={};specs={};datasets={};seeds=set()
    for spec in plan['structures']:
        sid=spec['structure_id'];specs[sid]=spec
        assert 6<=len(spec['nodes'])<=10
        acceptance=read(RUN/'acceptance'/sid/'acceptance.json');assert acceptance['status']=='PASS'
        assert all(all(x['checks'].values()) for x in acceptance['records'])
        compare(spec['controlled_variants'],{k:[list(e) for e in v] for k,v in select_controls(spec)[0].items()})
        for t in spec['tasks']:tasks[sid,t['task_id']]=t
        for cell in spec['datasets']:
            datasets[cell['dataset_id']]=(spec,cell)
            folder=RUN/'datasets'/cell['dataset_id']
            for split in ['train','validation']:
                seed=cell[split+'_seed'];assert seed not in seeds;seeds.add(seed)
                x,u=rows(folder/(split+'.csv')),rows(folder/(split+'_noise.csv'));assert len(x)==cell[split+'_n']
                for r,n in zip(x,u):
                    for v in spec['nodes']:close(float(r[v]),float(n['u_'+v])+sum(e['coefficient']*float(r[e['source']]) for e in spec['edges'] if e['target']==v))
            for alg in ['pc','boss','directlingam']:
                c=read(folder/(alg+'_learner_config.json'));assert set(c)=={'algorithm','seed','names','algorithms','families','train_sha256'}
                assert c['train_sha256']==sha(folder/'train.csv')
    # Regenerate structure selection from the frozen rule/seed without drawing data.
    from prepare_independent_confirmation import generate
    expected,records=generate(read(ROOT/'research_runs/diverse_structure_pilot/PLAN_v1.json'))
    expected=json.loads(json.dumps(expected));records=json.loads(json.dumps(records))
    compare(expected,plan['structures']);compare(records,read(BASE/'generation_acceptance_records.json'))
    evaluation=read(RUN/'intervention_evaluation.json');samples=0
    holdout_seeds=[b['seed'] for c in evaluation.values() for b in c['batches']]
    assert len(holdout_seeds)==len(set(holdout_seeds))==720
    assert set(holdout_seeds).isdisjoint(seeds)
    for tag,condition in evaluation.items():
        spec=specs[condition['structure_id']];action=condition['action'];v=condition['value']
        x,u=rows(RUN/'do_evaluation'/(tag+'.csv')),rows(RUN/'do_evaluation'/(tag+'_noise.csv'));samples+=len(x)
        assert len(x)==len(u)==plan['evaluation']['batches']*plan['evaluation']['n_per_batch']
        for r,n in zip(x,u):
            assert 'u_'+action not in n
            for node in spec['nodes']:
                expected=v if node==action else float(n['u_'+node])+sum(e['coefficient']*float(r[e['source']]) for e in spec['edges'] if e['target']==node)
                close(float(r[node]),expected)
        for node,stats in condition['statistics'].items():
            vals=[float(r[node]) for r in x]
            import statistics
            close(stats['mean'],statistics.mean(vals));close(stats['se'],statistics.stdev(vals)/math.sqrt(len(vals)))
    learned=read(RUN/'graph_inventory.json');assert len(learned)==216
    graphs={g['graph_id']:g for g in learned};comparison=read(RUN/'comparison.json')
    by_frozen={(r['graph_id'],r['task_id'],r['policy']):r for r in read(RUN/'recommendations_frozen.json')}
    cache={}
    for g in learned:
        if g['status']!='LEARNED':continue
        f=RUN/'datasets'/g['dataset_id']/(g['algorithm']+'_models.json')
        if not f.exists() and not Path(str(f)+'.gz').exists():continue
        saved=read(f);e=set(map(tuple,g['confirmed_edges']));u=set(map(frozenset,g['unresolved_pairs']))
        cache[g['graph_id']]=(saved,e)
        if saved['auxiliary_block'] is None:
            ext=consistent_extensions(g['column_order'],e,u,g['native'],plan['policy']['mec_max_unresolved'])
            assert [sorted(x) for x in ext]==[sorted(map(tuple,x['edges'])) for x in saved['extensions']]
    for r in comparison:
        if r['row_status']!='EVALUATED':continue
        g=graphs[r['graph_id']];task=tasks[r['structure_id'],r['task_id']];spec=specs[r['structure_id']]
        q=score_graph(set(map(tuple,g['confirmed_edges'])),set(map(frozenset,g['unresolved_pairs'])),spec,task)
        for k,v in q.items():compare(v,r[k])
        f=by_frozen[r['graph_id'],r['task_id'],r['policy']]['recommendation']['selected'];assert f['action']==r['recommended_action']
        saved,edges=cache[r['graph_id']]
        model_list=[saved['primary']] if r['policy']=='confirmed_only' else [x['model'] for x in saved['extensions']]
        edge_list=[edges] if r['policy']=='confirmed_only' else [set(map(tuple,x['edges'])) for x in saved['extensions']]
        rec=recommend_policy(model_list,edge_list,task,dict(plan['policy'],**{k:task[k] for k in ['action_values','reference_action','cost_weight']}),r['policy'])
        compare(rec,by_frozen[r['graph_id'],r['task_id'],r['policy']]['recommendation'])
        grid=plan['evaluation']['candidate_union'];prefix=r['structure_id']+'__'+r['action']+'__'
        losses=[(evaluation[prefix+str(grid.index(v))]['statistics'][r['target']]['mean']-task['target_value'])**2+task['cost_weight']*v*v for v in task['action_values']]
        i=task['action_values'].index(r['recommended_action']);close(losses[i],r['target_mean_loss']);close((losses[i]-min(losses))/task['loss_scale']**2,r['scale_normalized_regret'])
    primary=[r for r in comparison if r['row_status']=='EVALUATED' and r['policy']=='confirmed_only' and '__' not in r['task_id']]
    result=read(ANALYSIS/'CONFIRMATION_RESULT.json');check=clustered_comparison(primary,models)
    for k in ['macro_mae','structure_scores','paired','predictions']:compare(check[k],result[k])
    assert result['judgment']==(check['judgment'] if all(result['evaluability_checks'].values()) else 'NOT_EVALUABLE')
    summary=read(ANALYSIS/'SUMMARY.json');assert summary['do_samples']==samples and not summary['models_updated_on_confirmation']
    protected=['graphs/final','data','experiments','RESEARCH_DESIGN.md','research_runs/diverse_structure_pilot','research_runs/repeated_metric_pilot','research_runs/first_integrated_pilot']
    assert_protected_preserved(ROOT, plan['base_commit'], protected)
    print('[PASS] full144 replay; frozen rules/models/code before216 attempts;12 source/do contracts;raw equations/statistics;metrics/freeze/loss;cluster bootstrap;old assets unchanged')
if __name__=='__main__':validate()

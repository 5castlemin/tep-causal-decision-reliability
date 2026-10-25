"""Stored evidence + analytic/CV replay. External sampler replay is a separate local check."""
import gzip,hashlib,io,json,math,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from path_metric_incremental import load,development_rows,development_cv,precision_gate,linear_moments

def validate():
    import numpy as np
    import pandas as pd
    run=ROOT/'research_runs/path_metric_incremental_validation';dev=run/'development_v1';mc=run/'mc_calibration_v1'
    design=load(run/'DESIGN_GATE_PLAN_v1.json');merges=load(run/'integration/MERGE_RESULTS.json')
    assert merges['main_tree_equals_pr14'] and merges['owner_one_time_exception'] and not merges['independent_approved_review_created']
    assert set(merges['merges'])=={'12','13','14'}
    for folder in [dev,mc]:
        for name,h in load(folder/'SHA256.json').items():assert hashlib.sha256((folder/name).read_bytes()).hexdigest()==h,(folder.name,name)
    rows,_,_=development_rows(ROOT);stored=load(dev/'development_operational.json')
    assert len(rows)==2160 and len({r['structure_id'] for r in rows})==20
    assert sum(r['pipeline_ready'] for r in rows)==2136
    for a,b in zip(rows,stored):
        for k in ['graph_id','policy','task_id','original_attempt_status','failure_type','operational_action','pipeline_ready']:assert a[k]==b[k],k
        for k in ['analytic_loss','analytic_regret','skeleton_f1','key_path_edge_recall','fixed_effect_error']:
            assert (a[k] is None and b[k] is None) or math.isclose(a[k],b[k],abs_tol=1e-9,rel_tol=1e-9),(k,a[k],b[k])
        if not a['pipeline_ready']:assert a['operational_action']==0 and a['conditional_regret'] is None and a['analytic_loss']>0
    result=development_cv(rows);old=load(dev/'macro_mae.json')
    for k,v in result['macro_mae'].items():assert math.isclose(v,old[k],abs_tol=1e-9,rel_tol=1e-9),(k,v,old[k])
    for artifact in result['artifacts']:
        assert artifact['held_out'] not in artifact['training_structures'] and len(artifact['training_structures'])==19
    gate=precision_gate(result,design);old_gate=load(dev/'INDEPENDENT_PRECISION_GATE.json')
    assert gate['required_structures']==old_gate['required_structures']
    for a,b in zip(gate['comparisons'],old_gate['comparisons']):
        assert a['required_structures']==b['required_structures']
        for k in ['development_delta_mean','paired_structure_sd','planning_sd']:
            assert math.isclose(a[k],b[k],abs_tol=1e-9,rel_tol=1e-9)
    assert gate['status']=='BLOCKED_PRECISION_RESOURCE' and gate['required_structures']==150 and gate['new_reference_structures_generated']==0
    plan=load(mc/'PLAN_v1.json');specs={s['structure_id']:s for s in plan['structures']};stats=load(mc/'statistics.json')
    assert hashlib.sha256((mc/'PLAN_v1.json').read_bytes()).hexdigest()==(mc/'PLAN_v1.sha256').read_text().strip()
    assert load(mc/'EXECUTION_START.json')['utc']>=plan['utc']
    for c in plan['cases']:
        folder=mc/c['case_id'];s=specs[c['structure_id']];metadata=load(folder/'metadata.json');assert all(metadata['checks'].values())
        x=pd.read_csv(folder/'samples.csv.gz',float_precision='round_trip');u=pd.read_csv(folder/'noise.csv.gz',float_precision='round_trip')
        assert len(x)==c['n'] and list(x.columns)==s['nodes'] and (x[c['action']]==c['value']).all()
        for node in s['nodes']:
            expected=np.full(c['n'],c['value']) if node==c['action'] else u['u_'+node].to_numpy()+sum((e['coefficient']*x[e['source']].to_numpy() for e in s['edges'] if e['target']==node),np.zeros(c['n']))
            assert np.allclose(x[node],expected,atol=1e-10,rtol=1e-12)
        means,var=linear_moments(s,c['action'],c['value'])
        for r in [r for r in stats if r['case_id']==c['case_id']]:
            t=next(t for t in c['target_tasks'] if t['task_id']==r['task_id']);v=x[t['target']].iloc[:r['n']]
            assert math.isclose(v.mean(),r['sample_mean'],abs_tol=1e-10)
            assert math.isclose(means[t['target']],r['analytic_mean'],abs_tol=1e-10)
            assert math.isclose(math.sqrt(var[t['target']]/r['n']),r['expected_se'],abs_tol=1e-10)
    assert load(mc/'FAILURES.json')==[]
    assert load(mc/'SUMMARY.json')['new_discovery_learning_calls']==0
    print('[PASS] 2160 analytical operational rows, whole-structure CV replay, precision stop, actual do raw/noise equations and hashes; no external sampler rerun claimed')

if __name__=='__main__':validate()

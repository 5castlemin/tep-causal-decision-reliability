"""Replay analytic losses, error matches, six fits and nested feature selection."""
import hashlib,math,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from path_metric_incremental import load,linear_moments
from decision_reliability_next import evaluate,nested_cv
from summarize_decision_reliability_next import unique_pairs
from integrated_pilot import fit_model
from decision_mvp import static_mean_response

def validate():
    import pandas as pd
    b=ROOT/'research_runs/decision_reliability_next';run=b/'run_v1';audit=b/'audit_supplement_v1';plan=b/'PLAN_v1.json'
    assert hashlib.sha256(plan.read_bytes()).hexdigest()==(b/'PLAN_v1.sha256').read_text().strip()
    for folder in [run,audit]:
        for name,h in load(folder/'SHA256.json').items():assert hashlib.sha256((folder/name).read_bytes()).hexdigest()==h,(folder,name)
    for name,h in load(run/'START.json')['code_sha256'].items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==h,name
    specs={s['structure_id']:s for f in ['diverse_structure_pilot','independent_confirmation'] for s in load(ROOT/'research_runs'/f/'PLAN_v1.json')['structures']}
    controls=load(run/'A_controlled_outcomes.json');pairs=load(run/'A_matched_pairs.json');lookup={(r['dataset_id'],r['task_id'],r['variant']):r for r in controls}
    assert len(controls)==1224 and len(pairs)==432
    for p in pairs:
        a=lookup[p['dataset_id'],p['task_id'],p['left']];z=lookup[p['dataset_id'],p['task_id'],p['right']]
        for f in ['skeleton_f1','strict_directed_f1','missing_pairs','added_pairs','reversed_edges','shd']:assert a[f]==z[f]
        assert math.isclose(a['analytic_loss']-z['analytic_loss'],p['loss_left_minus_right'],abs_tol=1e-10)
    unique=unique_pairs(pairs,controls);assert len(unique)==324 and unique==load(audit/'A_unique_pairs.json')
    assert any(p['loss_left_minus_right']< -1e-10 and p['task_specific_key_vs_peripheral'] for p in unique)
    assert any(p['loss_left_minus_right']>1 and p['both_paths_preserved'] and p['task_specific_key_vs_peripheral'] for p in unique)
    for r in controls+load(run/'B_discovery_outcomes.json'):
        s=specs[r['structure_id']];t=next(t for t in s['tasks'] if t['task_id']==r['task_id']);v=evaluate(s,t,r['recommended_action'],r['predicted_reference'],r['predicted_slope'],t['loss_scale'])
        for k in ['analytic_loss','improvement','raw_regret','fixed_effect_error','direction_flip','nonoptimal']:
            assert r[k]==v[k] or isinstance(v[k],float) and math.isclose(r[k],v[k],abs_tol=1e-9,rel_tol=1e-9),(r['dataset_id'],k)
    s=specs['C07'];old=ROOT/'research_runs/independent_confirmation/run_v1/datasets'
    for a in load(run/'B_C07_oracle_fitted_models.json'):
        frame=pd.read_csv(old/a['dataset_id']/'train.csv');edges={(e['source'],e['target']) for e in s['edges']};m=fit_model(frame[s['nodes']].to_numpy(),s['nodes'],edges,a['alpha'])
        for t in [t for t in s['tasks'] if t['task_id'] in ['direct','path']]:
            for value in [-.5,0,.5]:assert math.isclose(static_mean_response(m,t['action'],value)[t['target']],static_mean_response(a['model'],t['action'],value)[t['target']],abs_tol=1e-8,rel_tol=1e-8)
    rows=load(ROOT/'research_runs/path_metric_incremental_validation/development_v1/development_operational.json');cv=nested_cv([r for r in rows if r['policy']=='confirmed_only']);saved=load(run/'C_nested_cv.json')
    for a,z in zip(cv['folds'],saved['folds']):
        assert a['held_out'] not in a['training_structures'] and a['selected']==z['selected']
        assert math.isclose(a['selected_test_mae'],z['selected_test_mae'],abs_tol=1e-8,rel_tol=1e-8)
    for k,v in cv['macro_mae'].items():assert math.isclose(v,saved['macro_mae'][k],abs_tol=1e-8,rel_tol=1e-8)
    assert load(run/'SUMMARY.json')['new_reference_structures']==0 and load(run/'SUMMARY.json')['new_do_samples']==0
    print('[PASS] 1224 reused controls;432 matched/324 unique pairs;analytic loss and counterexamples;six oracle fits;nested whole-structure selection replay;no new discovery/do/manufacturing claim')
if __name__=='__main__':validate()

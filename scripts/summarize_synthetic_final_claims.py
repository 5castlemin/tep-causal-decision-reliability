"""Read-only synthesis of stored results. No simulator, learner or fitter imports.

--check recomputes counts/MAEs/selectors from immutable source records and checks
the saved summary. Existing confidence intervals are copied, never re-estimated.
"""
import argparse
import ast
from collections import Counter, defaultdict
import gzip
import hashlib
import json
import math
from pathlib import Path
import statistics

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'research_runs/synthetic_final_claims'
INPUTS = {}


def read(path):
    p = ROOT / path
    raw = p.read_bytes()
    INPUTS[path] = hashlib.sha256(raw).hexdigest()
    return json.loads((gzip.decompress(raw) if p.suffix == '.gz' else raw).decode('utf-8-sig'))


def features(path, names):
    """Read only simple list/dict feature declarations, without importing code."""
    p = ROOT / path
    INPUTS[path] = hashlib.sha256(p.read_bytes()).hexdigest()
    env = {}
    def value(n):
        if isinstance(n, ast.Name): return env[n.id]
        if isinstance(n, ast.Constant): return n.value
        if isinstance(n, ast.List): return [value(x) for x in n.elts]
        if isinstance(n, ast.Dict): return {value(k): value(v) for k,v in zip(n.keys,n.values)}
        if isinstance(n, ast.BinOp) and isinstance(n.op, ast.Add): return value(n.left)+value(n.right)
        if isinstance(n, ast.Slice): return slice(value(n.lower) if n.lower else None, value(n.upper) if n.upper else None)
        if isinstance(n, ast.Subscript): return value(n.value)[value(n.slice)]
        raise ValueError('Unsupported static feature expression')
    for n in ast.parse(p.read_text(encoding='utf-8-sig')).body:
        if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name):
            try: env[n.targets[0].id]=value(n.value)
            except (ValueError,KeyError,TypeError): pass
    return {k:env[k] for k in names}


def compact_result(path):
    d=read(path)
    # Recompute every stored prediction's absolute error and equal-structure MAE.
    by=defaultdict(list)
    for row in d['predictions']:
        error=abs(row['predicted_loss']-row['actual_loss'])
        assert math.isclose(error,row['absolute_error'],abs_tol=1e-10)
        by[row['model'],row['structure_id']].append(error)
    for model,mae in d['macro_mae'].items():
        scores=[statistics.mean(v) for (m,s),v in by.items() if m==model]
        assert len(scores)==12 and math.isclose(statistics.mean(scores),mae,abs_tol=1e-10)
    for p in d['paired']:
        assert math.isclose(d['macro_mae'][p['left']]-d['macro_mae'][p['right']],p['delta'],abs_tol=1e-10)
        assert len(p['by_structure'])==12
    return {k:d[k] for k in ['macro_mae','paired','judgment','threshold','uncertainty_caveat']} | {
        'rows_per_model':dict(Counter(r['model'] for r in d['predictions'])),
        'source':path,'intervals':'Reused stored 10000 whole-structure bootstrap intervals; conditional on fixed exploratory predictors and selected generator families'}


def summarize():
    INPUTS.clear()
    base='research_runs/'
    conf=base+'independent_confirmation/'
    dev=base+'path_metric_incremental_validation/development_v1/'
    err=base+'decision_reliability_next/run_v1/'
    audit=base+'decision_reliability_next/audit_supplement_v1/'
    plan=read(conf+'PLAN_v1.json'); freeze=read(conf+'FREEZE.json')
    assert freeze['confirmation_data_started'] is False
    assert freeze['plan_sha256']==INPUTS[conf+'PLAN_v1.json']
    learned=read(conf+'analysis_v1/SUMMARY.json')
    observed=compact_result(conf+'analysis_v1/CONFIRMATION_RESULT.json')
    analytic=compact_result(conf+'analysis_v1/ANALYTIC_OUTCOME_SENSITIVITY.json')
    controlled=read(err+'A_controlled_outcomes.json.gz'); pairs=read(err+'A_matched_pairs.json.gz')
    lookup={(x['dataset_id'],x['task_id'],x['variant']):x for x in controlled}
    unique=[];seen=set()
    for i,p in enumerate(pairs):
        l=lookup[p['dataset_id'],p['task_id'],p['left']];r=lookup[p['dataset_id'],p['task_id'],p['right']]
        for key in ['skeleton_f1','strict_directed_f1','shd','edge_count','added_pairs','missing_pairs','reversed_edges','unresolved_count']:
            assert math.isclose(l[key],r[key],abs_tol=1e-12)
        assert math.isclose(l['analytic_loss']-r['analytic_loss'],p['loss_left_minus_right'],abs_tol=1e-10)
        identity=json.dumps([p['dataset_id'],p['task_id'],l['removed_edges'],l['added_edges'],r['removed_edges'],r['added_edges']],sort_keys=True)
        if identity not in seen: seen.add(identity);unique.append(p)
    saved_unique=read(audit+'A_unique_pairs.json')
    assert unique==saved_unique
    def counts(xs):
        return dict(pairs=len(xs),structures=len({x['structure_id'] for x in xs}),
            left_worse=sum(x['loss_left_minus_right']>1e-10 for x in xs),
            left_better=sum(x['loss_left_minus_right']< -1e-10 for x in xs),
            ties=sum(abs(x['loss_left_minus_right'])<=1e-10 for x in xs))
    actual=[x for x in unique if x['task_specific_key_vs_peripheral']]
    retained=[x for x in actual if x['both_paths_preserved']]
    actual_counts=counts(actual);retained_counts=counts(retained)
    old_summary=read(err+'A_summary.json');old_top=read(err+'SUMMARY.json')
    assert len(pairs)==old_top['matched_pairs']==432
    assert sum(x['task_specific_key_vs_peripheral'] for x in pairs)==old_top['meaningful_pairs']==216
    types=read(audit+'A_variant_outcomes.json')
    for t in types:
        xs=[x for x in controlled if x['variant']==t['variant']]
        assert len(xs)==t['rows'] and sum(x['worsened'] for x in xs)==t['worsened']
    examples=[]
    for ds in ['C07_n512_r1','C03_n256_r3','C09_n256_r1']:
        for i,p in enumerate(pairs):
            if p['dataset_id']==ds and p['task_id']=='path' and p['left']=='remove_key_path_retained':
                examples.append(dict(raw_row_index=i,source=err+'A_matched_pairs.json.gz',**p))
    discovered=read(err+'B_discovery_outcomes.json.gz');bs=read(err+'B_summary.json')
    assert len(discovered)==bs['rows']==720
    for key,field in [('availability','pipeline_ready'),('worsened','worsened'),('large','large_deterioration'),('nonoptimal','nonoptimal')]:
        assert sum(bool(x[field]) for x in discovered)==bs[key]
    cases=read(err+'B_cases.json.gz')
    assert {k:len(v) for k,v in cases.items()}==bs['cases']
    response_controls=read(err+'B_C07_response_controls.json')
    c07=[x for x in response_controls if x['dataset_id']=='C07_n512_r3' and x['task_id']=='path']
    outcomes=read(dev+'development_operational.json.gz')
    statuses=dict(Counter(x['recommendation_status'] for x in outcomes))
    policies=read(dev+'paired_policies.json');lu={(x['graph_id'],x['task_id'],x['policy']):x for x in outcomes}
    for pol in policies:
        diffs=[x['analytic_loss']-lu[x['graph_id'],x['task_id'],'confirmed_only']['analytic_loss'] for x in outcomes if x['policy']==pol['policy']]
        assert len(diffs)==pol['cells']==720
        assert sum(d< -1e-10 for d in diffs)==pol['improved']
        assert sum(d>1e-10 for d in diffs)==pol['worsened']
    version_defs={
        'confirmation_v1':features('src/independent_confirmation.py',['MODEL_FEATURES']),
        'incremental_development_v1':features('src/path_metric_incremental.py',['MODELS']),
        'simple_development_v1':features('src/decision_reliability_next.py',['MODELS'])}
    # Keep version-specific bases, loss scales and sample populations separate.
    cv=read(err+'C_nested_cv.json');precision=read(err+'D_precision.json')
    return dict(date='2026-10-29',scope='Existing synthetic results only; no new experiments, model fitting or bootstrap',
        initial_base='18e14d8da8ce3cc494eb680c726a0aa1ef5d3c26',
        cohort_roles=[dict(cohort='4-variable repeated pilot',structures=1,role='exploratory;12 datasets/36 attempts,Gaussian+Uniform kept separate'),
            dict(cohort='S1..S8',structures=8,role='hand-designed exploratory development/training'),
            dict(cohort='C01..C12',structures=12,role='then preregistered independent confirmation; subsequently reused development, never fresh again'),
            dict(cohort='new incremental/error confirmation',structures=0,role='NOT_RUN;precision/resource gate blocked')],
        historical_learning=learned,confirmation_rule=plan['confirmation_analysis'],model_versions=version_defs,
        confirmation_sample_outcome=observed,confirmation_analytic_sensitivity=analytic,
        controlled_error=dict(raw_rows=len(controlled),nominal_pairs=len(pairs),synonymous_repeats=len(pairs)-len(unique),
            distinct_graph_pairs=len(unique),actual_key_vs_peripheral=actual_counts,both_paths=retained_counts,
            per_type_distinct={k:counts([x for x in actual if x['left']==k]) for k in sorted({x['left'] for x in actual})},
            per_type_nominal=old_summary,variant_outcomes=types,examples=examples,
            scope='14 existing development structures;pairs repeat datasets/tasks and are not independent structure samples'),
        discovery_diagnostics=bs,c07_response_controls=c07,
        low_quality_optimal_example=[dict(raw_row_index=i,source=err+'B_discovery_outcomes.json.gz',**x) for i,x in enumerate(discovered) if x['dataset_id']=='C06_n256_r2' and x['algorithm']=='pc' and x['task_id']=='direct'],
        large_loss_cases=[dict(raw_row_index=i,source=err+'B_discovery_outcomes.json.gz',**x) for i,x in enumerate(discovered) if x['large_deterioration']],
        development=dict(summary=read(dev+'SUMMARY.json'),paired=read(dev+'paired_development.json'),
            without_task=read(dev+'without_task_information.json'),overlap=read(dev+'metric_overlap.json'),
            policies=policies,statuses=statuses,recommendation_availability=sum(x['pipeline_ready'] for x in outcomes),
            conditional_pairing=read(dev+'conditional_paired.json'),failure_policy=read(dev+'failure_policy_results.json')),
        simplified_cv=dict(macro_mae=cv['macro_mae'],nested_selected_macro_mae=cv['nested_selected_macro_mae'],
            selected_models=dict(Counter(x['selected'] for x in cv['folds']))),precision=precision,
        historical_replay={k:v for k,v in read(conf+'REPLAY_COMPARISON.json').items() if k!='comparisons'},
        repeated_pilot=dict(execution=read(base+'repeated_metric_pilot/analysis_v1/execution_summary.json'),
            policy_changes=read(base+'repeated_metric_pilot/analysis_v1/policy_changes.json'),
            wrong_direct_but_optimal=read(base+'repeated_metric_pilot/analysis_v1/wrong_direct_relation_but_best_grid_action.json')),
        new_simulations=0,new_discovery_fits=0,new_SCM_fits=0,new_do_samples=0,new_independent_structures=0,
        manufacturing_claim='NOT_TESTED;TEP effect track remains frozen;no cross-environment F1 join',
        next_resource_priority='Prespecify a bounded independent synthetic error-location/response/choice confirmation contract and budget, without executing it in this task')


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');args=ap.parse_args()
    result=summarize()
    manifest=dict(hash_mode='exact bytes of inputs actually read',files=INPUTS)
    if args.check:
        assert json.loads((OUT/'RESULT_SUMMARY.json').read_text(encoding='utf-8'))==result
        assert json.loads((OUT/'INPUT_SHA256.json').read_text(encoding='utf-8'))==manifest
        matrix=json.loads((OUT/'CLAIM_EVIDENCE_MATRIX.json').read_text(encoding='utf-8'))
        claims={c['claim_id']:c for c in matrix['claims']}
        assert set(claims)=={'A','B1','B2','C','D','E','F'}
        assert all(set(c)==set(matrix['columns']) for c in claims.values())
        assert claims['B2']['verdict']=='NOT_ESTABLISHED' and claims['F']['verdict']=='NOT_TESTED'
        assert claims['A']['metrics_and_observations']['matched']==result['controlled_error']['actual_key_vs_peripheral']
        assert claims['B1']['metrics_and_observations']['sample']==result['confirmation_sample_outcome']['paired'][0]
        assert claims['B1']['metrics_and_observations']['analytic']==result['confirmation_analytic_sensitivity']['paired'][0]
        assert claims['C']['metrics_and_observations']['both_paths']==result['controlled_error']['both_paths']
        assert claims['E']['metrics_and_observations']['statuses']==result['development']['statuses']
        allowed={'SUPPORTED_WITHIN_SCOPE','PARTIALLY_SUPPORTED','EXPLORATORY_ONLY','NOT_ESTABLISHED','NOT_TESTED'}
        for claim in claims.values():
            assert claim['verdict'] in allowed
            assert all((ROOT/r['file']).is_file() and r['selector'] for r in claim['raw_evidence_locations'])
        report=(ROOT/'docs/research_design/SYNTHETIC_FINAL_RESULTS_AND_CLAIMS.md').read_text(encoding='utf-8')
        for value in ['0.014264','0.006317','0.005200','0.004642','67.666749','14.182543','0.309796']:
            assert value in report, value
        print('[PASS] source counts/deduplication/equal-structure MAEs/action-policy losses/features/input hashes match; no fits or new samples')
    else:
        OUT.mkdir(parents=True,exist_ok=True)
        for name,d in [('RESULT_SUMMARY.json',result),('INPUT_SHA256.json',manifest)]:
            p=OUT/name
            if p.exists(): raise FileExistsError('Use --check; do not overwrite recorded output: '+str(p))
            p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print('[SYNTHESIS_ONLY] saved summary and input hashes; no new research observations')


if __name__=='__main__': main()

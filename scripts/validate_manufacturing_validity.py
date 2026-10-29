"""CI validates stored calculations/guards; external ZIP and local raw data not required."""
import hashlib,math,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from path_metric_incremental import load
from audit_manufacturing_validity import histogram_summary,guard_probe

def validate():
    import pandas as pd
    b=ROOT/'research_runs/manufacturing_validity_gate/review_v4'
    for name,h in load(b/'SHA256.json').items():assert hashlib.sha256((b/name).read_bytes()).hexdigest()==h,name
    table=pd.read_csv(ROOT/'docs/audit/step6_main_table.csv',float_precision='round_trip')
    from verify_recovery import ALGOS
    for r in load(b/'GLOBAL_METRICS.json'):
        row=table[(table.algo==ALGOS[r['graph_id']])&(table.stage=='final')].iloc[0]
        for key,col in [('skeleton_f1','sk_F1'),('strict_directed_f1','dS_F1'),('shd','SHD_S')]:assert math.isclose(r[key],row[col],abs_tol=1e-12)
    expected=load(ROOT/'research_runs/decision_mvp/run_20261024_v2/benchmark_task_metrics.json')['rows']
    for r in load(b/'TASK_METRICS.json'):
        old=next(v for v in expected if v['graph_id']==r['graph_id'] and v['task_id']==r['task_id'])
        for k in ['gt_path_edge_recall','complete_gt_path_fraction','confirmed_action_target_reachable','direct_xy_correct']:assert r[k]==old[k]
    for r in load(b/'PATH_COVERAGE.json'):
        c=r['all198_reference_reachability'];assert sum(c.values())==198 and c['tp']+c['fn']==65 and c['fp']+c['tn']==133
        assert r['confirmed_reachable']+r['no_confirmed_path']==12
    saved=load(b/'BASELINE_RECHECK.json')['results']
    for h in load(b/'BASELINE_HISTOGRAMS.json'):
        if h['higher_is_better']:
            graph=next(g for g in load(b/'GLOBAL_METRICS.json') if g['graph_id']==h['graph_id']);factor=(graph['pairs']+28)/2
            for raw,canonical,tp in zip(h['values'],h['canonical_values'],h['comparison_values']):
                assert abs(raw*factor-tp)<.001 and math.isclose(canonical,tp/factor,abs_tol=1e-12)
            assert h['comparison_observed']==round(h['observed']*factor)
        r=histogram_summary(h,h['observed'],h['higher_is_better']);s=next(s for s in saved if s['graph_id']==h['graph_id'] and s['metric']==h['metric'])
        assert sum(h['counts'])==10000 and all(math.isclose(r[k],s[k],abs_tol=1e-12) for k in r)
    p=guard_probe();assert p==load(b/'ENVIRONMENT_JOIN_PROBE.json')
    assert p['different_environment_ids_rejected'] and not p['node_clock_controller_reference_hashes_validated']
    s=load(b/'SUMMARY.json');assert s['new_simulator_runs']==s['new_scm_fitting']==s['new_graph_learning']==0
    print('[PASS] 7 frozen scores;84 stored task metrics;198-pair coverage;21 saved10000-draw histogram recomputations;legacy guard limitation retained. No new simulator/SCM/discovery.')
if __name__=='__main__':validate()

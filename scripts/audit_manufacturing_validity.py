"""Read-only frozen evaluation/evidence audit; never runs discovery or changes old results."""
import argparse,hashlib,json,math,sys,zipfile,io
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src')]
from verify_recovery import score,ALGOS,EXPECTED_HASHES
from decision_mvp import task_metrics,reachable,require_research_environment
from path_metric_incremental import load

def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def histogram_summary(hist,observed,higher):
    import numpy as np
    values=np.repeat(hist.get('canonical_values',hist['values']),hist['counts']);assert len(values)==10000
    raw_values=np.repeat(hist['values'],hist['counts'])
    test=np.repeat(hist.get('comparison_values',hist['values']),hist['counts']);obs=hist.get('comparison_observed',observed)
    return dict(n=len(values),mean=float(values.mean()),q025=float(np.quantile(values,.025)),q975=float(np.quantile(values,.975)),
        p=float(((test>=obs if higher else test<=obs).sum()+1)/(len(values)+1)),
        p_raw_csv_float=float(((raw_values>=observed if higher else raw_values<=observed).sum()+1)/(len(raw_values)+1)))

def guard_probe():
    flags={k:True for k in ['model_controller_identity','variable_intervention_alignment','reference_structure_valid','independent_evaluation_contract']}
    rejected=False
    try:require_research_environment('CPCaD','PYTHON_TEP',flags)
    except ValueError:rejected=True
    # Deliberately synthetic software probe: identical labels/booleans do not inspect metadata.
    require_research_environment('same-label','same-label',flags)
    return dict(different_environment_ids_rejected=rejected,same_label_and_all_flags_accepted=True,
        source_checks_only=['two string ids','four Boolean approvals'],node_clock_controller_reference_hashes_validated=False,
        verdict='LEGACY_GUARD_IS_NECESSARY_NOT_SUFFICIENT; NOT_A_SCIENTIFIC_ACCEPTANCE',source='src/decision_mvp.py:require_research_environment')

def main():
    import numpy as np
    import pandas as pd
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--step6-zip');a=p.parse_args();out=Path(a.output);out.mkdir(parents=True,exist_ok=False)
    names=pd.read_csv(ROOT/'graphs/final/variables.csv').variable.tolist();local=ROOT/'data/local'
    for f,h in EXPECTED_HASHES.items():assert sha(local/f)==h
    # Original CSV serializes an unnamed row index, not a 32nd process variable/timestamp.
    data=pd.read_csv(local/'datasetTE.csv',index_col=0);assert data.shape==(1499,31) and list(data.columns)==names
    raw=np.loadtxt(local/'TEGroundTruth.txt',dtype=int);keep=[int(n[1:])-1 for n in names];gt=raw[np.ix_(keep,keep)].astype(bool)
    assert gt.shape==(31,31) and gt.sum()==28
    truth={(names[i],names[j]) for i,j in zip(*np.nonzero(gt))};tasks=load(ROOT/'docs/tasks/structural_task_candidates_v1_1.json');stored=load(ROOT/'research_runs/decision_mvp/run_20261024_v2/benchmark_task_metrics.json')['rows']
    globals_=[];paths=[];coverage=[];settings=[]
    step6=pd.read_csv(ROOT/'docs/audit/step6_main_table.csv',float_precision='round_trip');repro=load(ROOT/'docs/reproducibility/GRAPH_REPRODUCIBILITY.json')
    for key,label in ALGOS.items():
        folder=ROOT/'graphs/final/graphs'/key;ad=pd.read_csv(folder/'A_dir.csv',index_col=0);un=pd.read_csv(folder/'A_unres.csv',index_col=0)
        assert ad.index.tolist()==ad.columns.tolist()==un.index.tolist()==un.columns.tolist()==names
        result=score(ad.to_numpy().astype(bool),un.to_numpy().astype(bool),gt);old=step6[(step6.algo==label)&(step6.stage=='final')].iloc[0]
        for k,v in [('skeleton_f1','sk_F1'),('strict_directed_f1','dS_F1'),('shd','SHD_S')]:assert math.isclose(result[k],float(old[v]),abs_tol=1e-12)
        globals_.append(dict(graph_id=key,algorithm=label,**result));edges={(names[i],names[j]) for i,j in zip(*np.nonzero(ad.to_numpy()))};u={frozenset((names[i],names[j])) for i,j in zip(*np.nonzero(un.to_numpy()))}
        rows=[]
        for task in tasks:
            r=dict(graph_id=key,**task_metrics(task,edges,truth,u));prior=next(v for v in stored if v['graph_id']==key and v['task_id']==task['task_id'])
            for k in ['gt_path_edge_recall','complete_gt_path_fraction','confirmed_action_target_reachable','direct_xy_correct']:assert r[k]==prior[k]
            rows.append(r)
        paths.extend(rows)
        pair_counts=dict(tp=0,fn=0,fp=0,tn=0)
        for action in [n for n in names if int(n[1:])>=23]:
            for target in [n for n in names if int(n[1:])<=22]:
                actual=reachable(truth,action,target);pred=reachable(edges,action,target);pair_counts['tp' if actual and pred else 'fn' if actual else 'fp' if pred else 'tn']+=1
        coverage.append(dict(graph_id=key,tasks=len(rows),confirmed_reachable=sum(r['confirmed_action_target_reachable'] for r in rows),
            no_confirmed_path=sum(not r['confirmed_action_target_reachable'] for r in rows),no_path_reference_fraction=sum(not r['confirmed_action_target_reachable'] for r in rows)/len(rows),
            fraction_scope='conditional structural implication of confirmed-only policy, NOT actually executed12-task recommendations; excludes cyclic/lag fit constraints',
            all198_reference_reachability=pair_counts,negative_pair_scope='discordance against benchmark structural reference only, not physical negative effects'))
        rec=next(g for g in repro['graphs'] if g['graph_id']==key);settings.append(dict(graph_id=key,config=load(folder/'config.json'),generation_code_available=rec['generation_code_bytes_available'],
            random_seed=rec['random_seed'],restarts=rec['restarts'],claim='settings/selection documented, exact Final generation replay not performed'))
    save(out/'GLOBAL_METRICS.json',globals_);save(out/'TASK_METRICS.json',paths);save(out/'PATH_COVERAGE.json',coverage);save(out/'SETTING_AUDIT.json',settings)
    rho=data.corrwith(data.shift(1));ar1={k:None if pd.isna(v) else float(v) for k,v in rho.items()}
    save(out/'OBSERVATIONAL_DIAGNOSTICS.json',dict(rows=1499,variables=31,lag1_correlation=ar1,
        heuristic_ess={k:None if v is None or abs(v)>=1 else max(1.,min(1499.,1499*(1-v)/(1+v))) for k,v in ar1.items()},
        caveat='AR1 marginal heuristic only, not frozen Bartlett effective N or valid multivariate sample size; no hypothesis test for nonlinearity/latent confounding'))
    save(out/'ENVIRONMENT_JOIN_PROBE.json',guard_probe())
    source=load(ROOT/'docs/research_design/ref_b_minimal_evidence/local_checks.json');save(out/'SOURCE_AND_CLOCK_CONTRACT.json',dict(commit=source['source_commit'],sha256=source['source_sha256'],
        evidence_file='docs/research_design/ref_b_minimal_evidence/local_checks.json',sensor_cache='evaluation time index; integrated state is next step',new_simulator_execution=False))
    baseline_status='NOT_RUN_EXTERNAL_ZIP_NOT_PROVIDED'
    if a.step6_zip:
        from reproduce_step6 import reproduce,ZIP_SHA
        archive=Path(a.step6_zip);assert sha(archive)==ZIP_SHA
        save(out/'ORIGINAL_EVALUATOR_REPLAY.json',reproduce(archive,local/'TEGroundTruth.txt'))
        with zipfile.ZipFile(archive) as z:
            b=z.read('evaluation/random_baseline.py');assert hashlib.sha256(b).hexdigest()==load(ROOT/'graphs/final/FREEZE.json')['code']['evaluation/random_baseline.py']
            rawdist=z.read('results/eval/random_distributions.csv');draws=pd.read_csv(io.BytesIO(rawdist),float_precision='round_trip');assert len(draws)==10000
            hist=[];summaries=[]
            for key,label in ALGOS.items():
                old=step6[(step6.algo==label)&(step6.stage=='final')].iloc[0]
                for metric,obs,mean_col,p_col,higher in [('skeleton_F1','sk_F1','rand_skeleton_F1','p_skeleton_F1',True),('dir_strict_F1','dS_F1','rand_dir_strict_F1','p_dir_strict_F1',True),('shd_strict','SHD_S','rand_shd_strict','p_shd_strict',False)]:
                    vals,counts=np.unique(draws[key+'/final|'+metric].to_numpy(),return_counts=True);h=dict(graph_id=key,metric=metric,observed=float(old[obs]),values=vals.tolist(),counts=counts.tolist(),higher_is_better=higher)
                    if higher:
                        # Fixed graph size: F1=2*TP/(m+28). Preserve exact discrete ties after CSV serialization.
                        factor=(float(old.n_pairs)+28)/2;counts_tp=np.rint(vals*factor)
                        # Archived CSV uses lossy decimals. Integer counts remain unambiguous:
                        # observed maximum distance below .001 count, far below half-count.
                        distance=float(np.max(np.abs(vals*factor-counts_tp)));assert distance<.001
                        observed_tp=round(h['observed']*factor);assert abs(h['observed']*factor-observed_tp)<1e-10
                        h.update(canonical_values=(counts_tp/factor).tolist(),max_integer_reconstruction_distance=distance,
                            max_csv_rounding_error=float(np.max(abs(vals-counts_tp/factor))),comparison_values=counts_tp.astype(int).tolist(),comparison_observed=observed_tp,
                            comparison_statistic='integer TP recovered unambiguously from lossy CSV; monotone-equivalent fixed-denominator F1, ties preserved')
                    s=histogram_summary(h,h['observed'],higher);assert math.isclose(s['mean'],float(old[mean_col]),abs_tol=1e-10) and math.isclose(s['p'],float(old[p_col]),abs_tol=1e-10),(key,metric,s['p'],float(old[p_col]))
                    hist.append(h);summaries.append(dict(graph_id=key,metric=metric,observed=h['observed'],**s))
            save(out/'BASELINE_HISTOGRAMS.json',hist);save(out/'BASELINE_RECHECK.json',dict(status='STORED10000_DRAWS_RECALCULATED_NOT_NEW_RANDOM_RUN',source_zip_sha256=sha(archive),random_code_sha256=hashlib.sha256(b).hexdigest(),draw_csv_sha256=hashlib.sha256(rawdist).hexdigest(),
                source_matches_final_random_code=True,selection_assumption='same pair/unresolved counts, uniform465 pairs, random confirmed directions; no DAG/controller/lag constraints; seed reported fixed but config seed bytes unavailable',results=summaries))
            baseline_status='PASS_STORED_DISTRIBUTION_RECALCULATION'
    save(out/'SUMMARY.json',dict(scope='frozen/reference/statistical and saved-interface evidence only',graphs=7,tasks=84,baseline_status=baseline_status,
        track_a='NO-GO_DIRECT_BENCHMARK_EFFECT',track_b='NO-GO_GLOBAL_STRUCTURE_VS_EFFECT; CONDITIONAL_INTERFACE_ONLY',new_graph_learning=0,new_scm_fitting=0,new_simulator_runs=0,recovery_safety='NOT_RUN'))
    save(out/'INPUT_SHA256.json',{p.relative_to(ROOT).as_posix():sha(p) for p in [ROOT/'graphs/final/FREEZE.json',ROOT/'docs/audit/step6_main_table.csv',ROOT/'docs/tasks/structural_task_candidates_v1_1.json',local/'datasetTE.csv',local/'TEGroundTruth.txt']})
    save(out/'SHA256.json',{p.relative_to(out).as_posix():sha(p) for p in out.iterdir() if p.is_file() and p.name!='SHA256.json'})
    print(json.dumps(load(out/'SUMMARY.json')))
if __name__=='__main__':main()

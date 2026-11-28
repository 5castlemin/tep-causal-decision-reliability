"""Independent, sampling-free analysis of the final evaluator-only vectors."""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import os
import threading
import time
from collections import defaultdict
from pathlib import Path

import numpy as np

from research.external_validation.semisynthetic_evaluation import pipeline as d
from research.external_validation.semisynthetic_final import final_pipeline as fp


def bias_corrected_loss(y: np.ndarray, target: float, scale: float) -> float:
    return float(((float(np.mean(y)) - target) ** 2 - float(np.var(y, ddof=1)) / len(y)) / scale**2)


def error_counts_from_report(report: dict) -> dict[str, int]:
    """Recover integer error counts from the locked policy engine's numerator reports."""
    m3_accuracy = report["M3_accuracy"]
    return {"M1_FN": int(report["M1"]["numerator"]),
        "M2_FP": int(report["M2"]["numerator"]),
        "M3_REV": int(m3_accuracy["denominator"]-m3_accuracy["numerator"]),
        "M3_UNRES": int(report["M3_unresolved"]["numerator"]),
        **{f"M4_{kind}":int(report["M4"][kind]["numerator"])
           for kind in ("FN","FP","REV","UNRES")}}


def _losses_from_resampled(y: np.ndarray, target: float, scale: float,
                           rng: np.random.Generator, reps: int) -> np.ndarray:
    n = len(y)
    indices = rng.integers(0, n, size=(reps, n), endpoint=False)
    samples = y[indices]
    means = samples.mean(axis=1)
    variances = samples.var(axis=1, ddof=1)
    return ((means - target) ** 2 - variances / n) / scale**2


def paired_bootstrap(vectors: list[np.ndarray], actions: list[float], rec: dict,
                     target: float, scale: float, *, reps: int, seed: int,
                     chunk: int = 128) -> dict:
    """Shared action-loss-table two-source bootstrap with fixed chunking."""
    by_key = {(r["g0_seed_id"], r["budget"], r["policy_id"]): r
              for r in rec["recommendations"]}
    seeds = list(rec["g0_seed_ids"])
    action_lookup = {float(a): i for i, a in enumerate(actions)}
    s0_ix, fg_ix = [], []
    for sid in seeds:
        s0_ix.append(action_lookup[float(by_key[(sid, 2, "S0")]["recommended_action"])])
        fg_ix.append(action_lookup[float(by_key[(sid, 2, "M1+M2+M3+M4")]["recommended_action"])])
    s0_ix, fg_ix = np.asarray(s0_ix), np.asarray(fg_ix)
    point_losses = np.asarray([bias_corrected_loss(y, target, scale) for y in vectors])
    fixed_delta = point_losses[s0_ix] - point_losses[fg_ix]
    rng = np.random.default_rng(seed)
    g0_only = np.empty(reps, dtype=np.float64)
    mc_only = np.empty(reps, dtype=np.float64)
    combined = np.empty(reps, dtype=np.float64)
    for start in range(0, reps, chunk):
        stop = min(start + chunk, reps)
        m = stop - start
        action_loss = np.column_stack([_losses_from_resampled(y, target, scale, rng, m)
                                       for y in vectors])
        g0_indices = rng.integers(0, len(seeds), size=(m, len(seeds)), endpoint=False)
        rows = np.arange(m)[:, None]
        per_seed = action_loss[rows, s0_ix[g0_indices]] - action_loss[rows, fg_ix[g0_indices]]
        combined[start:stop] = per_seed.mean(axis=1)
        mc_only[start:stop] = (action_loss[:, s0_ix] - action_loss[:, fg_ix]).mean(axis=1)
        fixed_g0 = rng.integers(0, len(seeds), size=(m, len(seeds)), endpoint=False)
        g0_only[start:stop] = fixed_delta[fixed_g0].mean(axis=1)
    q = lambda values: [float(x) for x in np.quantile(values, [0.025, 0.975])]
    return {"replicates": reps, "chunk_replicates": chunk, "seed": seed,
        "g0_only_95": q(g0_only), "action_mc_only_95": q(mc_only),
        "two_source_95": q(combined), "primary_point": float(fixed_delta.mean()),
        "two_source_bootstrap_mean": float(combined.mean()),
        "g0_only_half_width": float((q(g0_only)[1]-q(g0_only)[0])/2),
        "action_mc_only_half_width": float((q(mc_only)[1]-q(mc_only)[0])/2),
        "two_source_half_width": float((q(combined)[1]-q(combined)[0])/2),
        "resampling_unit": "paired G0 seed; independent rows within each action; one shared action-loss table per replicate"}


def summarize(lock: dict, rec: dict, vectors: list[np.ndarray], eval_manifest: dict) -> dict:
    actions = [float(a) for a in lock["task"]["actions"]]
    target, scale = float(lock["task"]["target"]), float(lock["task"]["scale"])
    if len(vectors) != 5 or any(v.shape != (2500,) or not np.isfinite(v).all() for v in vectors):
        raise ValueError("final response vector shape/finite validation failed")
    recs = rec["recommendations"]
    if len(recs) != 17000 or rec.get("row_count") != 17000:
        raise ValueError("recommendation count mismatch")
    losses = {a: bias_corrected_loss(y, target, scale) for a, y in zip(actions, vectors)}
    plugin = {a: float((float(y.mean())-target)**2/scale**2) for a, y in zip(actions, vectors)}
    action_summaries = {str(a): {"n": len(y), "mean": float(y.mean()),
        "sample_variance": float(y.var(ddof=1)),
        "standard_error": float(y.std(ddof=1)/np.sqrt(len(y))),
        "mean_minus_target": float(y.mean()-target),
        "response_sha256": hashlib.sha256(y.astype(np.float64).tobytes(order="C")).hexdigest(),
        "bias_corrected_loss": losses[a], "plug_in_loss": plugin[a],
        "below_target": bool(y.mean() < target)} for a, y in zip(actions, vectors)}
    action_idx = {a: i for i, a in enumerate(actions)}
    evaluated = []
    for row in recs:
        a = float(row["recommended_action"])
        if a not in losses: raise ValueError("recommendation outside common action set")
        evaluated.append({**row, "loss_bc": losses[a], "loss_plugin": plugin[a]})
    by_key = {(r["g0_seed_id"], r["budget"], r["policy_id"]): r for r in evaluated}
    if len(by_key) != 17000: raise ValueError("duplicate recommendation/evaluation key")
    seeds = list(rec["g0_seed_ids"])
    full = "M1+M2+M3+M4"
    primary_rows = [(by_key[(sid,2,"S0")],by_key[(sid,2,full)]) for sid in seeds]
    primary = float(np.mean([a["loss_bc"]-b["loss_bc"] for a,b in primary_rows]))
    secondary = float(np.mean([by_key[(sid,2,"M4")]["loss_bc"]-
                               by_key[(sid,2,full)]["loss_bc"] for sid in seeds]))
    bootstrap = paired_bootstrap(vectors, actions, rec, target, scale, reps=10000,
        seed=fp.derive_final_seed("bootstrap|primary-two-source"), chunk=128)
    # Secondary contrast uses the identical shared evaluator table and the same paired resampling design.
    m4_ix, fg_ix = [], []
    for sid in seeds:
        m4_ix.append(action_idx[float(by_key[(sid,2,"M4")]["recommended_action"])])
        fg_ix.append(action_idx[float(by_key[(sid,2,full)]["recommended_action"])])
    rng = np.random.default_rng(fp.derive_final_seed("bootstrap|m4-vs-fullgreedy"))
    secondary_draws = np.empty(10000, dtype=float)
    for start in range(0, 10000, 128):
        stop = min(start+128,10000); m=stop-start
        action_loss=np.column_stack([_losses_from_resampled(y,target,scale,rng,m) for y in vectors])
        g0_indices=rng.integers(0,len(seeds),size=(m,len(seeds)),endpoint=False)
        rows=np.arange(m)[:,None]
        secondary_draws[start:stop]=(action_loss[rows,np.asarray(m4_ix)[g0_indices]]-
                                     action_loss[rows,np.asarray(fg_ix)[g0_indices]]).mean(axis=1)
    sec_ci=[float(x) for x in np.quantile(secondary_draws,[.025,.975])]
    policies=lock["learner_and_repair"]["policies"]
    budgets=lock["learner_and_repair"]["budgets"]
    curve=[]
    for b in budgets:
        for policy in policies:
            rows=[by_key[(sid,b,policy)] for sid in seeds]
            curve.append({"budget":b,"policy":policy,"n_g0":len(rows),
                "mean_bias_corrected_loss":float(np.mean([x["loss_bc"] for x in rows])),
                "mean_plugin_loss":float(np.mean([x["loss_plugin"] for x in rows])),
                "mean_edit_count":float(np.mean([x["edit_count"] for x in rows])),
                "mean_edit_cost":float(np.mean([x["repair_cost"] for x in rows])),
                "mean_task_zone_edit_count":float(np.mean([x["task_zone_edit_count"] for x in rows])),
                "mean_off_task_edit_count":float(np.mean([x["off_task_edit_count"] for x in rows])),
                "unused_budget_rate":float(np.mean([x["unused_budget"]>0 for x in rows])),
                "no_op_rate":float(np.mean([x["repair_cost"]==0 for x in rows]))})
    b2=[]
    for sid in seeds:
        s0, fg, m4 = (by_key[(sid,2,p)] for p in ("S0",full,"M4"))
        b2.append({"seed_id":sid,"s0_action":s0["recommended_action"],
            "full_action":fg["recommended_action"],"m4_action":m4["recommended_action"],
            "s0_loss":s0["loss_bc"],"full_loss":fg["loss_bc"],"m4_loss":m4["loss_bc"],
            "full_cost":fg["repair_cost"],"m4_cost":m4["repair_cost"],
            "full_task_zone_edits":fg["task_zone_edit_count"],"full_off_task_edits":fg["off_task_edit_count"],
            "m4_task_zone_edits":m4["task_zone_edit_count"],"m4_off_task_edits":m4["off_task_edit_count"],
            "same_action_m4_full":m4["recommended_action"]==fg["recommended_action"],
            "same_repaired_graph_m4_full":m4["repaired_graph_sha256"]==fg["repaired_graph_sha256"],
            "s0_full_action_changed":s0["recommended_action"]!=fg["recommended_action"],
            "full_case":"improved" if fg["loss_bc"]<s0["loss_bc"] else
                ("worsened" if fg["loss_bc"]>s0["loss_bc"] else "tied"),
            "m4_case":"improved" if m4["loss_bc"]<fg["loss_bc"] else
                ("worsened" if m4["loss_bc"]>fg["loss_bc"] else "tied")})
    # Baseline is trained only on the fixed observational frame and stored in the locked recommendation manifest.
    baseline_action=float(rec["graph_free_baseline"]["action"])
    baseline={"recommended_action":baseline_action,"loss_bc":losses[baseline_action],
        "loss_plugin":plugin[baseline_action],"interpretation":"observational association only; not a causal effect estimator"}
    # Prespecified descriptive strata use initial reference-relative M4 task-zone counts.
    g0_rows={int(x["seed_id"]):x for x in lock["g0_records"]}
    task_error_ids=[]; no_task_error_ids=[]; no_error_ids=[]
    from research.original_objective import policy_engine as pe
    truth={pe.pair(a,b): (a,b) for a,b in lock["graph"]["edges"]}
    for sid in seeds:
        g0=d.reconstruct_g0(g0_rows[sid]["record"],truth)
        counts=pe.metrics(truth,g0,"Station1_mp_0","Station1_mp_4",pe.Config(fp_rule="A"))["counts"]
        task_total=sum(counts["M4"].values())
        total=sum(sum(metric.values()) for metric in counts.values())
        if task_total: task_error_ids.append(sid)
        else: no_task_error_ids.append(sid)
        if total==0: no_error_ids.append(sid)
    def group_summary(ids, policy):
        values=[by_key[(sid,2,policy)]["loss_bc"] for sid in ids]
        return {"n_g0":len(ids),"mean_loss_bc":float(np.mean(values)) if values else None}
    improvement_counts={"FullGreedy_vs_S0":{k:sum(x["full_case"]==k for x in b2) for k in ("improved","worsened","tied")},
        "M4_vs_FullGreedy":{k:sum(x["m4_case"]==k for x in b2) for k in ("improved","worsened","tied")}}
    fg_cost=float(np.mean([x["full_cost"] for x in b2])); m4_cost=float(np.mean([x["m4_cost"] for x in b2]))
    cost_diffs=np.asarray([x["m4_cost"]-x["full_cost"] for x in b2],dtype=float)
    rng_cost=np.random.default_rng(fp.derive_final_seed("bootstrap|paired-cost"))
    cost_draws=np.asarray([rng_cost.choice(cost_diffs,size=len(cost_diffs),replace=True).mean() for _ in range(10000)])
    cost_ci=[float(x) for x in np.quantile(cost_draws,[.025,.975])]
    # Error counts by zone, policy and metric are reconstructed from locked initial/final metrics.
    error_changes=[]
    for policy in policies:
        initial=defaultdict(int); final=defaultdict(int)
        for sid in seeds:
            row=by_key[(sid,2,policy)]
            for metric, value in error_counts_from_report(row["initial_metrics"]).items(): initial[metric]+=value
            for metric, value in error_counts_from_report(row["final_metrics"]).items(): final[metric]+=value
        error_changes.append({"policy":policy,"initial_error_count_by_metric":dict(initial),
            "final_error_count_by_metric":dict(final),
            "net_count_reduction_by_metric":{m:initial[m]-final[m] for m in set(initial)|set(final)}})
    action_vectors_meta={r["index"]:{"sha256":r["response_sha256"],"rows":r["rows"]}
                         for r in eval_manifest["action_records"]}
    structure_action=[]
    for sid in seeds:
        row=by_key[(sid,2,full)]
        before=error_counts_from_report(row["initial_metrics"])
        after=error_counts_from_report(row["final_metrics"])
        structure_reduced=sum(before.values())>sum(after.values())
        delta=row["loss_bc"]-by_key[(sid,2,"S0")]["loss_bc"]
        structure_action.append({"seed_id":sid,"fullgreedy_structure_error_count_reduced":structure_reduced,
            "action_changed_vs_s0":row["recommended_action"]!=by_key[(sid,2,"S0")]["recommended_action"],
            "loss_case_vs_s0":"improved" if delta<0 else ("worsened" if delta>0 else "tied")})
    structure_action_counts={
        "structure_reduced_action_same":sum(x["fullgreedy_structure_error_count_reduced"] and not x["action_changed_vs_s0"] for x in structure_action),
        "structure_reduced_action_changed":sum(x["fullgreedy_structure_error_count_reduced"] and x["action_changed_vs_s0"] for x in structure_action),
        "structure_reduced_but_loss_worsened":sum(x["fullgreedy_structure_error_count_reduced"] and x["loss_case_vs_s0"]=="worsened" for x in structure_action),
        "structure_reduced_but_loss_tied":sum(x["fullgreedy_structure_error_count_reduced"] and x["loss_case_vs_s0"]=="tied" for x in structure_action)}
    result={"schema":"RESEARCH_D_FINAL_INDEPENDENT_ANALYSIS_V1","integrity_status":"PASS",
        "run_id":lock["run_id"],"run_lock_sha256":eval_manifest["run_lock_sha256"],
        "recommendation_row_count":len(recs),"g0_count":len(seeds),"g0_are_independent_external_scms":False,
        "action_order":actions,"action_summaries":action_summaries,"primary_B2_S0_minus_FullGreedy":{
            "mean_delta_loss_bc":primary,"n_paired_g0":len(seeds),"positive_favors":"FullGreedy",
            "estimand_scope":"conditional on one fitted DRF and fixed Development training frame"},
        "primary_intervals":bootstrap,"secondary_B2_M4_minus_FullGreedy":{
            "mean_delta_loss_bc":secondary,"paired_two_source_95":sec_ci,
            "n_paired_g0":len(seeds)},
        "m4_fullgreedy_cost_and_action":{
            "mean_fullgreedy_edit_count":fg_cost,"mean_m4_edit_count":m4_cost,
            "mean_paired_cost_difference_m4_minus_fullgreedy":float(cost_diffs.mean()),
            "paired_cost_difference_95":cost_ci,
            "m4_cost_reduction_fraction_vs_fullgreedy":float((fg_cost-m4_cost)/fg_cost) if fg_cost else None,
            "same_action_fraction":float(np.mean([x["same_action_m4_full"] for x in b2])),
            "same_repaired_graph_fraction":float(np.mean([x["same_repaired_graph_m4_full"] for x in b2])),
            "s0_fullgreedy_action_changed_n":int(sum(x["s0_full_action_changed"] for x in b2)),
            "paired_outcome_cases":improvement_counts},
        "graph_free_association_baseline":baseline,"policy_budget_curve":curve,
        "task_zone_off_task_error_counts_at_B2":error_changes,
        "structure_action_relationship":structure_action_counts,
        "prespecified_g0_strata":{"initial_no_error_n":len(no_error_ids),
            "task_zone_error_n":len(task_error_ids),
            "no_task_zone_error_n":len(no_task_error_ids),"task_zone_error_s0_loss":group_summary(task_error_ids,"S0"),
            "task_zone_error_fullgreedy_loss":group_summary(task_error_ids,"M1+M2+M3+M4"),
            "no_task_zone_error_s0_loss":group_summary(no_task_error_ids,"S0"),
            "no_task_zone_error_fullgreedy_loss":group_summary(no_task_error_ids,"M1+M2+M3+M4"),
            "initial_no_error_s0_loss":group_summary(no_error_ids,"S0"),
            "initial_no_error_fullgreedy_loss":group_summary(no_error_ids,"M1+M2+M3+M4")},
        "action_vectors":action_vectors_meta,"evaluation_rows":eval_manifest["total_rows"],
        "response_data_sha256_by_action":{str(k):v["sha256"] for k,v in action_vectors_meta.items()},
        "physical_manufacturing_claim":False,"absolute_regret_primary":False,
        "final_response_vectors_reused_or_regenerated":False,
        "precision_targets":{"action_mc_half_width_target":0.02,"combined_half_width_target":0.025,
            "action_mc_actual_half_width":bootstrap["action_mc_only_half_width"],
            "combined_actual_half_width":bootstrap["two_source_half_width"],
            "action_mc_target_met":bootstrap["action_mc_only_half_width"]<=0.02,
            "combined_target_met":bootstrap["two_source_half_width"]<=0.025,
            "missed_target_did_not_change_sample_size":True}}
    return result


def _peak_rss_sampler(stop_event, peak):
    class Counters(ctypes.Structure):
        _fields_=[("cb",ctypes.c_ulong), ("PageFaultCount",ctypes.c_ulong),
                  ("PeakWorkingSetSize",ctypes.c_size_t), ("WorkingSetSize",ctypes.c_size_t),
                  ("QuotaPeakPagedPoolUsage",ctypes.c_size_t), ("QuotaPagedPoolUsage",ctypes.c_size_t),
                  ("QuotaPeakNonPagedPoolUsage",ctypes.c_size_t), ("QuotaNonPagedPoolUsage",ctypes.c_size_t),
                  ("PagefileUsage",ctypes.c_size_t), ("PeakPagefileUsage",ctypes.c_size_t)]
    if os.name != "nt": return
    psapi=ctypes.WinDLL("Psapi.dll"); kernel=ctypes.WinDLL("Kernel32.dll")
    counters=Counters(); counters.cb=ctypes.sizeof(counters)
    handle=kernel.GetCurrentProcess()
    while not stop_event.wait(.02):
        if psapi.GetProcessMemoryInfo(handle,ctypes.byref(counters),counters.cb):
            peak[0]=max(peak[0],int(counters.WorkingSetSize))


def resource_benchmark(output: Path, seed: int) -> dict:
    if output.exists(): raise FileExistsError("resource benchmark output exists")
    stop=threading.Event(); peak=[0]
    monitor=threading.Thread(target=_peak_rss_sampler,args=(stop,peak),daemon=True); monitor.start()
    start=time.perf_counter(); rng=np.random.default_rng(seed)
    actions=[float(x) for x in fp.contract()["task"]["actions"]]
    ys=[rng.normal(loc=14+j*.1,scale=1.5,size=2500).astype(np.float64) for j in range(5)]
    fake_recs={"g0_seed_ids":list(range(200)),"recommendations":[]}
    actrng=np.random.default_rng(seed+1)
    for sid in fake_recs["g0_seed_ids"]:
        for budget in range(5):
            for policy in fp.contract()["learner_and_repair"]["policies"]:
                fake_recs["recommendations"].append({"g0_seed_id":sid,"budget":budget,"policy_id":policy,
                    "recommended_action":actions[int(actrng.integers(0,5))]})
    result=paired_bootstrap(ys,actions,fake_recs,15.46,1.56,reps=10000,seed=seed+2,chunk=128)
    del ys,fake_recs
    stop.set(); monitor.join(timeout=1)
    answer={"schema":"RESEARCH_D_FINAL_RESPONSE_BLIND_RESOURCE_BENCHMARK_V1","status":"PASS",
        "seed":seed,"synthetic_action_rows":12500,"synthetic_recommendation_rows":17000,
        "bootstrap_replicates":10000,"chunk_replicates":128,"peak_rss_bytes":peak[0],
        "elapsed_seconds":time.perf_counter()-start,"response_data_accessed":False,
        "final_action_or_task_used_for_selection":False,"bootstrap_execution":result}
    fp.atomic_json(output,answer)
    return answer


def main(argv=None):
    p=argparse.ArgumentParser()
    p.add_argument("--run-lock",type=Path)
    p.add_argument("--recommendations",type=Path)
    p.add_argument("--evaluation-manifest",type=Path)
    p.add_argument("--response-dir",type=Path)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--resource-benchmark",action="store_true")
    p.add_argument("--seed",type=int)
    a=p.parse_args(argv)
    if a.resource_benchmark:
        if a.seed is None: raise ValueError("synthetic resource benchmark seed is required")
        result=resource_benchmark(a.output,a.seed)
        print(json.dumps({"status":result["status"],"peak_rss_bytes":result["peak_rss_bytes"],
            "elapsed_seconds":result["elapsed_seconds"]},sort_keys=True)); return
    for path in (a.run_lock,a.recommendations,a.evaluation_manifest,a.response_dir):
        if path is None: raise ValueError("analysis requires all locked input paths")
    c=fp.contract()
    if a.output.exists(): raise FileExistsError("independent analysis output exists")
    lock=json.loads(a.run_lock.read_text(encoding="utf-8"))
    rec=json.loads(a.recommendations.read_text(encoding="utf-8"))
    ev=json.loads(a.evaluation_manifest.read_text(encoding="utf-8"))
    if ev.get("run_lock_sha256")!=fp.file_sha(a.run_lock):
        raise ValueError("response manifest refers to another run lock")
    if ev.get("recommendation_raw_sha256")!=fp.file_sha(a.recommendations):
        raise ValueError("response manifest refers to another recommendation file")
    vectors=[]
    for record in sorted(ev["action_records"],key=lambda x:x["index"]):
        path=a.response_dir/record["filename"]
        raw=path.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=record["response_sha256"]:
            raise ValueError(f"response vector hash mismatch: {path.name}")
        y=np.load(path,allow_pickle=False)
        if y.shape!=(2500,) or not np.isfinite(y).all() or len(y)!=record["rows"]:
            raise ValueError(f"response vector schema/finite check failed: {path.name}")
        vectors.append(y.astype(np.float64,copy=False))
    if len(vectors)!=5 or ev.get("total_rows")!=12500:
        raise ValueError("final evaluator vector count/row count incomplete")
    # All scientific lock and recommendation checks are independent of outcome values.
    body=dict(rec); content=body.pop("content_sha256",None)
    if hashlib.sha256(d.canonical_json(body)).hexdigest()!=content:
        raise ValueError("recommendation content digest mismatch")
    if len(rec.get("recommendations",[]))!=17000 or rec.get("g0_seed_ids")!=c["sample"]["g0_ids"]:
        raise ValueError("final recommendation manifest grid differs from final contract")
    result=summarize(lock,rec,vectors,ev)
    result["independent_analyzer_code_sha256"]=fp.file_sha(Path(__file__))
    fp.atomic_json(a.output,result)
    print(json.dumps({"status":"PASS_INDEPENDENT_ANALYSIS","recommendations":len(rec["recommendations"]),
        "intervention_rows":ev["total_rows"],"primary":result["primary_B2_S0_minus_FullGreedy"]["mean_delta_loss_bc"],
        "action_mc_half_width":result["primary_intervals"]["action_mc_only_half_width"],
        "two_source_half_width":result["primary_intervals"]["two_source_half_width"]},sort_keys=True))


if __name__=="__main__": main()

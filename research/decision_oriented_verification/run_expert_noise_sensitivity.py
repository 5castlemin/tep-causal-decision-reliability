"""Optional F-Lite hypothetical expert-noise sensitivity; never creates study inputs."""
from __future__ import annotations
import csv, hashlib, json, os, sys, time
from pathlib import Path
import numpy as np
import psutil

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/"src"))
from research.decision_oriented_verification.run_f_lite import SOURCES,restore_cohort,stable_seed,make_policy_view,_selection
from research.decision_oriented_verification.policy import (NO_EDGE,U_TO_V,V_TO_U,VerificationState,query_once)
from research.budget_aware_refinement.step3_adapter import evaluate
from research.budget_aware_refinement.step4c1_gt import analytic_response
from research.original_objective import policy_engine as pe
from integrated_pilot import fit_model
from decision_mvp import static_mean_response

OUT=ROOT/"research/decision_oriented_verification/outputs"
PRIVATE=Path(os.environ.get("DAT_RESEARCH_F_LITE_ROOT","C:/DAT_RESEARCH/research-f-lite/v1"))/"expert_noise"
ACCURACIES=(0.9,0.8);REPEATS=16;BUDGET=4
POLICIES=("RANDOM_VERIFICATION","SUSPICION_ONLY","DECISION_IMPACT_ONLY","DECISION_WEIGHTED_VERIFICATION")

def noisy_answer(truth,pair,accuracy,repeat,cohort,scm_id):
    rel=truth.get(pair)
    correct=NO_EDGE if rel is None else U_TO_V if rel==pair else V_TO_U
    rng=np.random.default_rng(stable_seed("hypothetical-expert-noise",cohort,scm_id,accuracy,repeat,pair))
    if rng.random()<accuracy:return correct
    return tuple(x for x in (NO_EDGE,U_TO_V,V_TO_U) if x!=correct)[int(rng.integers(0,2))]

def run_unit(record,accuracy,repeat,policy):
    view=make_policy_view(record);state=VerificationState(view["nodes"],dict(view["initial"]))
    rng=np.random.default_rng(stable_seed("hypothetical-expert-noise-random-policy",record["cohort"],record["scm_id"],accuracy,repeat)) if policy=="RANDOM_VERIFICATION" else None
    context={"data":view["data"],"nodes":view["nodes"],"action":view["action"],"target":view["target"],
             "action_values":view["actions"],"target_value":view["target_value"],"scale":view["scale"],
             "fit_model":fit_model,"response":static_mean_response,"model_cache":{}}
    transcript=[]
    for _ in range(BUDGET):
        trace=query_once(state,policy,state.query_count+1,
             lambda p:noisy_answer(record["truth"],p,accuracy,repeat,record["cohort"],record["scm_id"]),
             score_context=context,rng=rng)
        transcript.extend(trace)
    selection=_selection(view,state.relations)
    return {"cohort":record["cohort"],"scm_id":record["scm_id"],"accuracy":accuracy,"repeat":repeat,
            "policy":policy,"budget":BUDGET,"query_count":state.query_count,"edit_count":state.edits,
            "pending_count":len(state.pending),"relations":dict(state.relations),"history":list(state.history),
            "selection":selection}

def rec_content(rows):
    output=[]
    for r in rows:
        s=r["selection"];a=float(next(x["action"] for x in s["candidates"] if x["k"]==s["selected_k"]))
        output.append({k:r[k] for k in ("cohort","scm_id","accuracy","repeat","policy","budget","query_count","edit_count","pending_count")}|
                      {"action":a,"selected_k":float(s["selected_k"]),"predicted_losses":[float(x["predicted_loss"]) for x in s["candidates"]]})
    return output

def main():
    PRIVATE.mkdir(parents=True,exist_ok=True);OUT.mkdir(parents=True,exist_ok=True)
    started=time.perf_counter();process=psutil.Process();peak=process.memory_info().rss
    summary={"status":"RUNNING","accuracies":ACCURACIES,"repeats_per_scm":REPEATS,"budget":BUDGET,"policies":POLICIES,"cohorts":{}}
    for source in SOURCES:
        cohort=source[0];records,_=restore_cohort(source);rec_file=PRIVATE/f"{cohort.lower()}_recommendations.json";ev_file=PRIVATE/f"{cohort.lower()}_evaluator.jsonl"
        if rec_file.exists() or ev_file.exists():raise FileExistsError(f"Refusing to overwrite F3 artifact for {cohort}")
        all_rec=[]
        for i,record in enumerate(records,1):
            for accuracy in ACCURACIES:
                for repeat in range(REPEATS):
                    for policy in POLICIES:all_rec.append(run_unit(record,accuracy,repeat,policy))
            peak=max(peak,process.memory_info().rss)
            if i%8==0:print(f"F3 recommendations {cohort}: {i}/{len(records)}; {time.perf_counter()-started:.1f}s",flush=True)
            limit=7200
            if time.perf_counter()-started>limit:raise TimeoutError("F3 two-hour wall cap exceeded")
            if peak>4*1024**3:raise MemoryError("F3 4-GiB RSS cap exceeded")
        expected=len(records)*2*REPEATS*len(POLICIES)
        keys=[(r["scm_id"],r["accuracy"],r["repeat"],r["policy"],r["budget"]) for r in all_rec]
        if len(all_rec)!=expected or len(set(keys))!=expected:raise ValueError("F3 incomplete/duplicate recommendation keys")
        serial=rec_content(all_rec);content_hash=hashlib.sha256(json.dumps(serial,sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest()
        lock={"cohort":cohort,"rows":len(serial),"content_sha256":content_hash,"contract":"accuracy={0.9,0.8}; 16 repeats; B=4; four fixed policies","source_lock_sha256":"70aeb723faa5f87fc1023026894a099b144134f8a3fcb332651f530a0b598ece"}
        rec_file.write_text(json.dumps({"lock":lock,"records":serial},separators=(",",":")),encoding="utf-8")
        saved=json.loads(rec_file.read_text(encoding="utf-8"));actual=hashlib.sha256(json.dumps(saved["records"],sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest()
        if actual!=lock["content_sha256"]:raise ValueError("F3 recommendation lock mismatch")
        by_id={r["scm_id"]:r for r in records};evaluated=[]
        for r in all_rec:
            rec=by_id[r["scm_id"]];result=evaluate(r["selection"],rec["truth_spec"],analytic_response)
            evaluated.append({"cohort":cohort,"scm_id":r["scm_id"],"accuracy":r["accuracy"],"repeat":r["repeat"],"policy":r["policy"],
                              "budget":BUDGET,"query_count":r["query_count"],"edit_count":r["edit_count"],"pending_count":r["pending_count"],
                              "action":float(next(x["action"] for x in r["selection"]["candidates"] if x["k"]==r["selection"]["selected_k"])),
                              "regret":float(result["regret"]),"query_history":r["history"]})
        ev_file.write_text("\n".join(json.dumps(x,sort_keys=True) for x in evaluated),encoding="utf-8")
        grouped={}
        for accuracy in ACCURACIES:
            for policy in POLICIES:
                per_scm=[]
                for rec in records:
                    rs=[x for x in evaluated if x["scm_id"]==rec["scm_id"] and x["accuracy"]==accuracy and x["policy"]==policy]
                    per_scm.append({"regret":float(np.mean([x["regret"] for x in rs])),"edit_count":float(np.mean([x["edit_count"] for x in rs])),
                                    "query_count":float(np.mean([x["query_count"] for x in rs])),
                                    "wrong_responses":float(np.mean([sum(not q["correct"] for q in x["query_history"]) for x in rs]))})
                grouped[(accuracy,policy)]=per_scm
        aggregates=[]
        for (accuracy,policy),rs in grouped.items():
            aggregates.append({"cohort":cohort,"accuracy":accuracy,"policy":policy,"n_scm":len(rs),
                               "mean_regret":float(np.mean([x["regret"] for x in rs])),"sd_scm_mean_regret":float(np.std([x["regret"] for x in rs],ddof=1)),
                               "mean_edit_count":float(np.mean([x["edit_count"] for x in rs])),"mean_query_count":float(np.mean([x["query_count"] for x in rs])),
                               "mean_wrong_responses_per_trajectory":float(np.mean([x["wrong_responses"] for x in rs]))})
        summary["cohorts"][cohort]={"n_scm":len(records),"recommendation_rows":len(serial),"recommendation_sha256":content_hash,
                                     "recommendation_file_sha256":hashlib.sha256(rec_file.read_bytes()).hexdigest(),
                                     "evaluator_rows":len(evaluated),"evaluator_sha256":hashlib.sha256(ev_file.read_bytes()).hexdigest(),
                                     "elapsed_seconds":time.perf_counter()-started,"peak_process_rss_bytes_observed":peak,"aggregates":aggregates}
        with (OUT/f"{cohort.lower()}_noise_sensitivity.csv").open("w",newline="",encoding="utf-8") as f:
            w=csv.DictWriter(f,fieldnames=list(aggregates[0]));w.writeheader();w.writerows(aggregates)
    summary["status"]="COMPLETED";summary["total_elapsed_seconds"]=time.perf_counter()-started;summary["peak_process_rss_bytes_observed"]=peak
    (ROOT/"research/decision_oriented_verification/noise_sensitivity_summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    print(json.dumps(summary,indent=2))

if __name__=="__main__":main()

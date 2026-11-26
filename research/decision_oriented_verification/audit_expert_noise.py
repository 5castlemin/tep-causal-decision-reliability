"""Read-only audit and paired sensitivity analysis of locked F3 artifacts."""
from __future__ import annotations
import hashlib,json,os,sys,ast
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/"src"))
from research.decision_oriented_verification.run_f_lite import SOURCES,restore_cohort,stable_seed
from research.decision_oriented_verification.run_expert_noise_sensitivity import ACCURACIES,REPEATS,POLICIES,PRIVATE,NO_EDGE,U_TO_V,V_TO_U
from research.decision_oriented_verification.policy import VerificationState,graph_dag
OUT=ROOT/"research/decision_oriented_verification/outputs";BOOTSTRAPS=10000

def label(rel,pair):
    if rel is None or rel==NO_EDGE:return NO_EDGE
    return U_TO_V if tuple(rel)==tuple(pair) else V_TO_U

def bootstrap(mat,cohort,accuracy,comparator,proposed):
    # mat: SCM x shared repeat ID x policy; resample SCM and repeat IDs jointly.
    n,reps,_=mat.shape; ci=comparator;pi=proposed
    scm_mean=mat[:,:,ci].mean(axis=1)-mat[:,:,pi].mean(axis=1)
    rng=np.random.default_rng(stable_seed("f-lite-noise-nested-bootstrap-v1",cohort,accuracy,POLICIES[ci],POLICIES[pi]))
    draws=[];chunk=100
    for start in range(0,BOOTSTRAPS,chunk):
        k=min(chunk,BOOTSTRAPS-start);sidx=rng.integers(0,n,size=(k,n));ridx=rng.integers(0,reps,size=(k,n,reps))
        c=mat[:,:,ci][sidx];p=mat[:,:,pi][sidx]
        cv=np.take_along_axis(c,ridx,axis=2).mean(axis=(1,2));pv=np.take_along_axis(p,ridx,axis=2).mean(axis=(1,2))
        draws.extend((cv-pv).tolist())
    return {"comparator_minus_proposed":float(scm_mean.mean()),"ci95_low":float(np.quantile(draws,.025)),"ci95_high":float(np.quantile(draws,.975)),
            "scm_comparator_better":int(np.sum(scm_mean< -1e-12)),"scm_proposed_better":int(np.sum(scm_mean>1e-12)),"scm_tie":int(np.sum(np.abs(scm_mean)<=1e-12)),"bootstrap_replicates":BOOTSTRAPS,
            "bootstrap_seed":stable_seed("f-lite-noise-nested-bootstrap-v1",cohort,accuracy,POLICIES[ci],POLICIES[pi])}

def main():
    run=json.loads((ROOT/"research/decision_oriented_verification/noise_sensitivity_summary.json").read_text(encoding="utf-8"))
    if run.get("status")!="COMPLETED":raise ValueError("F3 run is not complete")
    out={"status":"AUDITED","expert_accuracies":list(ACCURACIES),"repeats_per_scm_accuracy":REPEATS,"budget":4,"policies":list(POLICIES),"bootstrap_replicates":BOOTSTRAPS,"cohorts":{}}
    for source in SOURCES:
        cohort=source[0];records,_=restore_cohort(source);byid={x["scm_id"]:x for x in records}
        recpath=PRIVATE/f"{cohort.lower()}_recommendations.json";evpath=PRIVATE/f"{cohort.lower()}_evaluator.jsonl"
        saved=json.loads(recpath.read_text(encoding="utf-8"));serial=saved["records"];lock=saved["lock"]
        rec_hash=hashlib.sha256(json.dumps(serial,sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest()
        if rec_hash!=lock["content_sha256"] or len(serial)!=len(records)*len(ACCURACIES)*REPEATS*len(POLICIES):raise ValueError("recommendation hash/count mismatch")
        rows=[json.loads(line) for line in evpath.read_text(encoding="utf-8").splitlines() if line]
        recorded=run["cohorts"][cohort]
        if rec_hash!=recorded["recommendation_sha256"]:raise ValueError("recommendation content hash differs from run summary")
        if hashlib.sha256(recpath.read_bytes()).hexdigest()!=recorded["recommendation_file_sha256"]:raise ValueError("recommendation raw-file hash differs from run summary")
        if hashlib.sha256(evpath.read_bytes()).hexdigest()!=recorded["evaluator_sha256"]:raise ValueError("evaluator raw-file hash differs from run summary")
        expected=len(records)*len(ACCURACIES)*REPEATS*len(POLICIES);keys=[(r["scm_id"],r["accuracy"],r["repeat"],r["policy"],r["budget"]) for r in rows]
        if len(rows)!=expected or len(set(keys))!=expected:raise ValueError("evaluator key completeness failure")
        keyset={(r["scm_id"],r["accuracy"],r["repeat"],r["policy"],r["budget"]) for r in rows}
        rec_keys={(r["scm_id"],r["accuracy"],r["repeat"],r["policy"],r["budget"]) for r in serial}
        if keyset!=rec_keys:raise ValueError("recommendation/evaluator key mismatch")
        # Replay only stored expert answers through the locked graph-update function.
        for row in rows:
            rec=byid[row["scm_id"]];truth=rec["truth"];nodes=rec["nodes"]
            state=VerificationState(nodes,dict(rec["initial"]));wrong=pending=wrong_pending=applied_wrong=wrong_not_applied=new_errors=0;queried=[]
            for q in row["query_history"]:
                pair=tuple(q["pair"]);correct=label(truth.get(pair),pair);answer=q["answer"]
                wrong += answer!=correct;pending += bool(q["pending"]);wrong_pending += bool(q["pending"]) and answer!=correct
                if answer not in (NO_EDGE,U_TO_V,V_TO_U):raise ValueError("invalid expert state")
                state.apply_answer(pair,answer)
                queried.append((pair,correct,answer))
            if state.query_count!=row["query_count"] or state.edits!=row["edit_count"] or len(state.pending)!=row["pending_count"]:
                raise ValueError("stored graph-update replay mismatch")
            if not graph_dag(nodes,state.relations):raise ValueError("non-DAG replay result")
            for pair,correct,answer in queried:
                final=label(state.relations.get(pair),pair)
                applied_wrong += (answer!=correct and final!=correct)
                wrong_not_applied += (answer!=correct and final==correct)
                initial=label(rec["initial"].get(pair),pair)
                new_errors += (initial==correct and final!=correct)
            row["audit_wrong_responses"]=int(wrong);row["audit_pending_query_responses"]=int(pending)
            row["audit_wrong_pending_responses"]=int(wrong_pending);row["audit_wrong_responses_finally_applied"]=int(applied_wrong)
            row["audit_wrong_responses_not_applied_finally"]=int(wrong_not_applied);row["audit_new_pair_errors"]=int(new_errors)
            row["audit_final_pending_count"]=len(state.pending)
        summaries=[];contrasts=[]
        idx={p:i for i,p in enumerate(POLICIES)}
        for acc in ACCURACIES:
            mat=np.full((len(records),REPEATS,len(POLICIES)),np.nan)
            extra={p:{k:[] for k in ("wrong","pending","wrong_pending","applied_wrong","wrong_not_applied","new_errors","pending_final","edits","queries")} for p in POLICIES}
            for row in rows:
                if row["accuracy"]!=acc:continue
                mat[list(byid).index(row["scm_id"]),row["repeat"],idx[row["policy"]]]=row["regret"]
                for name,col in (("wrong","audit_wrong_responses"),("pending","audit_pending_query_responses"),("wrong_pending","audit_wrong_pending_responses"),
                                 ("applied_wrong","audit_wrong_responses_finally_applied"),("wrong_not_applied","audit_wrong_responses_not_applied_finally"),("new_errors","audit_new_pair_errors")):
                    extra[row["policy"]][name].append(row[col])
                extra[row["policy"]]["pending_final"].append(row["audit_final_pending_count"])
                extra[row["policy"]]["edits"].append(row["edit_count"]);extra[row["policy"]]["queries"].append(row["query_count"])
            if not np.isfinite(mat).all():raise ValueError("incomplete F3 SCM/repeat/policy cube")
            for pi,p in enumerate(POLICIES):
                vals=mat[:,:,pi].mean(axis=1)
                summaries.append({"accuracy":acc,"policy":p,"n_scm":len(records),"repeats_per_scm":REPEATS,"mean_regret":float(vals.mean()),"sd_scm_mean_regret":float(vals.std(ddof=1)),
                                  "mean_wrong_answers_per_trajectory":float(np.mean(extra[p]["wrong"])),"mean_pending_queries_per_trajectory":float(np.mean(extra[p]["pending"])),
                                  "mean_wrong_answers_pending_at_query_per_trajectory":float(np.mean(extra[p]["wrong_pending"])),
                                  "mean_wrong_answers_finally_applied_per_trajectory":float(np.mean(extra[p]["applied_wrong"])),"mean_new_pair_errors_per_trajectory":float(np.mean(extra[p]["new_errors"])),
                                  "mean_wrong_answers_not_applied_finally_per_trajectory":float(np.mean(extra[p]["wrong_not_applied"])),
                                  "mean_final_pending_relations_per_trajectory":float(np.mean(extra[p]["pending_final"])),"mean_edit_count":float(np.mean(extra[p]["edits"])),
                                  "mean_query_count":float(np.mean(extra[p]["queries"]))})
            proposed=idx["DECISION_WEIGHTED_VERIFICATION"]
            for p in POLICIES:
                if p=="DECISION_WEIGHTED_VERIFICATION":continue
                contrasts.append({"accuracy":acc,"comparator":p,"proposed":"DECISION_WEIGHTED_VERIFICATION",**bootstrap(mat,cohort,acc,idx[p],proposed)})
        summary=run["cohorts"][cohort]
        out["cohorts"][cohort]={"n_scm":len(records),"recommendation_rows":len(serial),"evaluator_rows":len(rows),"recommendation_file_sha256":hashlib.sha256(recpath.read_bytes()).hexdigest(),
                                 "evaluator_file_sha256":hashlib.sha256(evpath.read_bytes()).hexdigest(),"row_replay_graph_state_valid":True,"aggregates":summaries,"paired_nested_bootstrap":contrasts}
    target=ROOT/"research/decision_oriented_verification/noise_sensitivity_audit.json";target.write_text(json.dumps(out,indent=2),encoding="utf-8")
    print(json.dumps({"status":out["status"],"cohorts":{k:{"n_scm":v["n_scm"],"recommendation_rows":v["recommendation_rows"],"evaluator_rows":v["evaluator_rows"]} for k,v in out["cohorts"].items()}},indent=2))
if __name__=="__main__":main()

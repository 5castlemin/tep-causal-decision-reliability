"""Read-only integrity audit and query-score replay for a completed F-Lite run."""
from __future__ import annotations

import ast
import csv
import hashlib
import json
import os
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "src"))
from research.decision_oriented_verification.run_f_lite import (
    SOURCES, DETERMINISTIC, PRIVATE_ROOT, restore_cohort, stable_seed,
    make_policy_view,
)
from research.decision_oriented_verification.policy import (
    NO_EDGE, UNRESOLVED, VerificationState, score_pairs, pair_order, graph_dag,
)
from integrated_pilot import fit_model
from decision_mvp import static_mean_response

POLICY_OUT = ROOT / "research/decision_oriented_verification/outputs"
PUBLIC = ROOT / "research/decision_oriented_verification"


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _canonical(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def audit_one(source):
    cohort, _, _, _ = source
    slug = cohort.lower()
    manifest_path = PRIVATE_ROOT / f"{slug}_recommendations.json"
    eval_path = PRIVATE_ROOT / f"{slug}_evaluator_results.jsonl"
    manifest_raw = manifest_path.read_bytes(); eval_raw = eval_path.read_bytes()
    saved = json.loads(manifest_raw); lock = saved["lock"]; recs = saved["records"]
    if sha(_canonical(recs)) != lock["recommendation_sha256"]:
        raise ValueError(f"recommendation content hash mismatch: {cohort}")
    evs = [json.loads(line) for line in eval_raw.splitlines() if line]
    rec_by_key = {(r["scm_id"], r["policy"], r["repeat"], r["budget"]): r for r in recs}
    ev_by_key = {(r["scm_id"], r["policy"], r["repeat"], r["budget"]): r for r in evs}
    if len(rec_by_key) != len(recs) or len(ev_by_key) != len(evs) or set(rec_by_key) != set(ev_by_key):
        raise ValueError(f"duplicate/missing recommendation-evaluator keys: {cohort}")
    expected = 64 if cohort == "C_DEVELOPMENT" else 200
    if len(recs) != expected * 195 or len(evs) != expected * 195:
        raise ValueError(f"cohort row count mismatch: {cohort}")
    policy_counts = {}
    for policy in ("S0", *DETERMINISTIC, "RANDOM_VERIFICATION", "ORACLE_ASSISTED_M4_DIAGNOSTIC", "GRAPH_FREE_ASSOCIATION_DIAGNOSTIC"):
        policy_counts[policy] = sum(r["policy"] == policy for r in recs)
    if policy_counts["RANDOM_VERIFICATION"] != expected * 32 * 5:
        raise ValueError("random repeat count mismatch")
    for key, mr in rec_by_key.items():
        er = ev_by_key[key]
        if float(mr["action"]) != float(er["action"]) or float(mr["selected_k"]) != float(er["selected_k"]):
            raise ValueError(f"locked recommendation changed before evaluation: {key}")
        if abs(float(er["regret"]) - (float(er["selected_loss"]) - float(er["best_grid_loss"]))) > 1e-12:
            raise ValueError(f"regret arithmetic mismatch: {key}")
        if len(er["gt_loss_vector"]) != 5:
            raise ValueError(f"incomplete evaluator action grid: {key}")
        if mr["query_count"] is not None:
            qhist = er["query_history"]
            if mr["query_count"] > mr["budget"] or len(qhist) != mr["query_count"]:
                raise ValueError(f"query budget mismatch: {key}")
            qpairs = [tuple(q["pair"]) for q in qhist]
            expected_queries = 0 if mr["policy"] in {"S0", "GRAPH_FREE_ASSOCIATION_DIAGNOSTIC"} else mr["budget"]
            if len(qpairs) != len(set(qpairs)) or len(qpairs) != expected_queries:
                raise ValueError(f"duplicate or missing pair queries: {key}")
            if any(q["answer"] not in ("NO_EDGE", "U_TO_V", "V_TO_U") for q in qhist):
                raise ValueError(f"invalid expert response: {key}")
        if er["final_relations"] != "None":
            rels = ast.literal_eval(er["final_relations"])
            if not graph_dag(tuple(sorted({n for p in rels for n in p} | set())), rels):
                # Isolated nodes do not affect acyclicity; the DAG relation keys cover all endpoints.
                raise ValueError(f"cyclic stored recommendation graph: {key}")
    # Prefix property for all trajectories, including each independently seeded Random path.
    full = {k[:3]: ev_by_key[k] for k in ev_by_key if k[3] == 4}
    for prefix, row4 in full.items():
        h4 = row4["query_history"]
        for b in range(4):
            rowb = ev_by_key[(*prefix, b)]
            if rowb["query_history"] != h4[:b]:
                raise ValueError(f"query trajectory is not budget-prefix consistent: {prefix}, B={b}")
    return {"cohort": cohort, "n_scm": expected, "recommendation_rows": len(recs), "evaluator_rows": len(evs),
            "recommendation_sha256": lock["recommendation_sha256"], "recommendation_file_sha256": sha(manifest_raw),
            "evaluator_file_sha256": sha(eval_raw), "policy_rows": policy_counts,
            "recommendations_contain_no_regret": all("regret" not in r for r in recs),
            "evaluator_lock_match": True, "complete_keys": True, "budget_and_prefix_checks": True}


def replay_query_scores(source, records, evaluator_rows, score_trace_path):
    cohort = source[0]
    record_by_id = {r["scm_id"]: r for r in records}
    final_rows = [r for r in evaluator_rows if r["cohort"] == cohort and r["budget"] == 4 and r["policy"] in DETERMINISTIC]
    trace_count = selected_rank_one = candidate_rows = 0
    with score_trace_path.open("a", encoding="utf-8") as out:
        for row in final_rows:
            original = record_by_id[row["scm_id"]]
            view = make_policy_view(original)
            state = VerificationState(view["nodes"], dict(view["initial"]))
            cache = {}
            ctx = {"data": view["data"], "nodes": view["nodes"], "action": view["action"], "target": view["target"],
                   "action_values": view["actions"], "target_value": view["target_value"], "scale": view["scale"],
                   "fit_model": fit_model, "response": static_mean_response, "model_cache": cache}
            for step, q in enumerate(row["query_history"], 1):
                scores = score_pairs(row["policy"], relations=state.relations, **ctx)
                available = [x for x in scores if x["pair"] not in state.queried]
                selected = min(available, key=lambda x: (-x["score"], x["pair"]))
                pair = tuple(q["pair"])
                if selected["pair"] != pair:
                    raise ValueError(f"saved query is not the locked-score argmax: {cohort}/{row['scm_id']}/{row['policy']}/q{step}")
                trace_count += 1; selected_rank_one += 1; candidate_rows += len(available)
                out.write(json.dumps({"cohort": cohort, "scm_id": row["scm_id"], "policy": row["policy"],
                                      "step": step, "selected_pair": pair, "selected_score": selected["score"],
                                      "candidate_count": len(available), "candidate_scores": [
                                          {"pair": x["pair"], "score": x["score"], "suspicion": x["suspicion"],
                                           "decision_impact": x["decision_impact"], "fit_gain": x["fit_gain"]} for x in available]},
                                     sort_keys=True, default=list) + "\n")
                state.apply_answer(pair, q["answer"])
        out.flush()
    return {"queries_replayed": trace_count, "selected_score_argmax_matches": selected_rank_one,
            "candidate_scores_replayed": candidate_rows, "artifact_sha256": sha(score_trace_path.read_bytes())}


def independently_recompute_contrasts(cohort, evaluator_rows):
    scm_ids = sorted({r["scm_id"] for r in evaluator_rows if r["cohort"] == cohort})
    policies = ("RANDOM_VERIFICATION", *DETERMINISTIC)
    out = []
    seed=stable_seed(cohort,"paired-bootstrap");rng=np.random.default_rng(seed)
    for comparator in policies:
        diffs = []
        for scm_id in scm_ids:
            vals = [r["regret"] for r in evaluator_rows if r["cohort"] == cohort and r["scm_id"] == scm_id and r["policy"] == comparator and r["budget"] == 4]
            prop = [r["regret"] for r in evaluator_rows if r["cohort"] == cohort and r["scm_id"] == scm_id and r["policy"] == "DECISION_WEIGHTED_VERIFICATION" and r["budget"] == 4]
            diffs.append(float(np.mean(vals) - np.mean(prop)))
        d=np.asarray(diffs)
        boots=np.empty(10000)
        for i in range(10000): boots[i]=float(d[rng.integers(0,len(d),size=len(d))].mean())
        out.append({"cohort":cohort,"comparator":comparator,"proposed":"DECISION_WEIGHTED_VERIFICATION","budget":4,
                    "n_scm":len(d),"mean_comparator_minus_proposed":float(d.mean()),"median_difference":float(np.median(d)),
                    "ci95_low":float(np.quantile(boots,.025)),"ci95_high":float(np.quantile(boots,.975)),
                    "comparator_better":int((d<0).sum()),"proposed_better":int((d>0).sum()),"tie":int((d==0).sum()),
                    "bootstrap_replicates":10000,"seed":seed})
    return out


def main():
    PUBLIC.mkdir(parents=True, exist_ok=True); POLICY_OUT.mkdir(parents=True, exist_ok=True)
    audit=[]; all_evals=[]; restored={}
    for source in SOURCES:
        result=audit_one(source);audit.append(result)
        records,_=restore_cohort(source);restored[source[0]]=records
        p=PRIVATE_ROOT / f"{source[0].lower()}_evaluator_results.jsonl"
        all_evals.extend(json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x)
    trace=PRIVATE_ROOT / "query_score_replay.jsonl"
    replay=[]
    if trace.exists():
        saved_trace=[json.loads(x) for x in trace.read_text(encoding="utf-8").splitlines() if x]
        expected={"C_DEVELOPMENT":1024,"C_HELDOUT":3200}
        for cohort,n in expected.items():
            rows=[r for r in saved_trace if r["cohort"]==cohort]
            if len(rows)!=n: raise ValueError(f"query score replay row count mismatch: {cohort}")
        for r in saved_trace:
            scores=r["candidate_scores"]
            top=min(scores,key=lambda x:(-x["score"],tuple(x["pair"])))
            if list(top["pair"])!=r["selected_pair"]: raise ValueError("replayed selected query not score argmax")
        replay=[{"cohort":c,"queries_replayed":sum(r["cohort"]==c for r in saved_trace),
                 "selected_score_argmax_matches":sum(r["cohort"]==c for r in saved_trace),
                 "candidate_scores_replayed":sum(len(r["candidate_scores"]) for r in saved_trace if r["cohort"]==c),
                 "artifact_sha256":sha(trace.read_bytes())} for c in expected]
    else:
        trace.touch()
        for source in SOURCES: replay.append({"cohort":source[0],**replay_query_scores(source,restored[source[0]],all_evals,trace)})
    contrasts=[]
    for source in SOURCES:
        cohort=source[0]; independent=independently_recompute_contrasts(cohort,all_evals)
        saved=json.loads((POLICY_OUT/f"{cohort.lower()}_paired_contrasts.json").read_text(encoding="utf-8"))
        for a,b in zip(independent,saved):
            for k in ("mean_comparator_minus_proposed","ci95_low","ci95_high"):
                if abs(a[k]-b[k])>1e-12: raise ValueError(f"bootstrap reproduction mismatch: {cohort}/{a['comparator']}/{k}")
        contrasts.extend(independent)
    summary={"gate":"F_CORE_REFERENCE_BLIND_EVALUATION_COMPLETED","source_execution_code_commit":"9155b8c63b64548a88b2c1f5f98032288dbbafed",
             "source_execution_lock_sha256":"70aeb723faa5f87fc1023026894a099b144134f8a3fcb332651f530a0b598ece",
             "audit":audit,"query_score_replay":replay,"paired_contrasts":contrasts,
             "note":"Saved core results audited; final runner summary stage failed after all cohort artifacts were written. No evaluator resampling was repeated."}
    (PUBLIC/"saved_output_audit.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    print(json.dumps(summary,indent=2))


if __name__=="__main__": main()

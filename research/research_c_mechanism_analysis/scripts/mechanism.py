"""Read-only M1-M4 mechanism extraction from a (regenerated) Research C cohort ledger."""
import sqlite3, json, sys, hashlib, statistics as st
from collections import Counter, defaultdict
db_path, out_path = sys.argv[1], sys.argv[2]
sha = hashlib.sha256(open(db_path,'rb').read()).hexdigest()
db = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
rows = db.execute("select scm_id, ordinal, result_json from scms where status='COMPLETED' order by ordinal").fetchall()
FG, M4 = "M1+M2+M3+M4", "M4"
recs = []   # flat policy x budget rows
scm_info = {}
for scm_id, ordn, rj in rows:
    p = json.loads(rj)["payload"]; e = p["e2e_result"]; md = p["fixture_metadata"]
    g0 = md["g0_generation"]
    init_counts = None
    for b in e["budgets"]:
        for pol in b["policies"]:
            ev = pol.get("evaluation") or {}
            edits = pol.get("edit_log") or []
            recs.append(dict(scm=scm_id, ord=ordn, B=b["budget"], pol=pol["policy_id"],
                regret=ev.get("regret"), k=ev.get("selected_k"), opt=ev.get("optimum_k"),
                margin=ev.get("decision_margin"), cost=pol.get("total_edit_cost"),
                graph=pol.get("final_graph_sha256"), learner=pol.get("learner_graph_sha256"),
                stop=pol.get("stop_reason"), P_all=pol.get("structural_P_all"),
                final=pol.get("final_error_counts"), init_err=pol.get("initial_error_count"),
                edits=[dict(o=x["order"], m=x["metric"], t=x["error_type"], pair=x["pair"], op=x["operation"],
                            score=x["score"], tz=x["task_zone"]) for x in edits],
                pred=ev.get("predicted_losses"), truth=[r["loss"] for r in ev.get("truth_rows") or []]))
    s0 = next(r for r in recs if r["scm"]==scm_id and r["pol"]=="S0" and r["B"]==0)
    scm_info[scm_id] = dict(ord=ordn, template=md["template"], n=md["node_count"], action=e["input"]["action"],
        target=e["input"]["target"], init_err=s0["init_err"], init_counts=s0["final"],
        g0_events=[(x["kind"], x["pair"], x["task_zone"]) for x in g0.get("attempted_events", []) if x.get("acceptance_status")=="accepted"])
json.dump(dict(db=db_path, db_sha256=sha, n_scm=len(rows), scm=scm_info, recs=recs), open(out_path,"w"))
print(len(rows), len(recs), sha)

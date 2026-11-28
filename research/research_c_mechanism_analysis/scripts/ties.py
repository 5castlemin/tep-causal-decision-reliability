"""Replay Full Greedy steps with the repo policy engine to classify off-task-over-task choices (tie vs strict)."""
import sys, json, sqlite3
from collections import Counter
from pathlib import Path; sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from research.original_objective import policy_engine as pe
run_dir, flat, out = sys.argv[1], sys.argv[2], sys.argv[3]
F = json.load(open(flat)); idx = {(r["scm"],r["pol"],r["B"]): r for r in F["recs"]}
pdb = sqlite3.connect(f"file:{run_dir}/research_c_proposal_stage.sqlite?mode=ro", uri=True)
props = {pid: json.loads(pj) for pid, pj in pdb.execute("select proposal_id, proposal_json from proposal_attempts where proposal_json is not null")}
cdb = sqlite3.connect(f"file:{run_dir}/research_c_cohort.sqlite?mode=ro", uri=True)
cfg = pe.Config(); FG = ("M1","M2","M3","M4")
stats = Counter(); detail = []; zone_sizes=[]
for scm_id, rj in cdb.execute("select scm_id, result_json from scms where status='COMPLETED' order by ordinal"):
    p = json.loads(rj)["payload"]; md = p["fixture_metadata"]; pr = props[md["proposal_id"]]
    truth = pe.state(pr["topology_edges"]); g = md["g0_generation"]["initial_graph"]
    g0 = pe.state(g["edges"], unresolved=g["unresolved"])
    a, t = p["e2e_result"]["input"]["action"], p["e2e_result"]["input"]["target"]
    m0 = pe.metrics(truth, g0, a, t, cfg)
    zone_sizes.append(dict(scm=scm_id, task_true=m0["support"]["M4"]["FN"], off_true=m0["support"]["M1"], off_pred=m0["support"]["M2"]))
    for B in (1, 2):
        res = pe.run(truth, g0, a, t, B, FG, cfg)
        logged = [(e["m"], tuple(e["pair"]), e["op"]) for e in idx[(scm_id, "M1+M2+M3+M4", B)]["edits"]]
        mine = [(e["metric"], tuple(e["pair"]), e["operation"]) for e in res["edits"]]
        stats[f"B{B}_replay_match"] += (logged == mine)
        # step-wise replay
        cur = dict(g0); applied=set()
        for step in res["edits"]:
            pool = pe.candidates(truth, g0, a, t, cfg)
            before = pe.metrics(truth, cur, a, t, cfg)
            sc = []
            for e in pool:
                if e.key in applied or cur.get(e.pair) == e.replacement: continue
                trial = pe.apply(cur, e)
                if not pe.dag(trial): continue
                after = pe.metrics(truth, trial, a, t, cfg)
                if not (before["events"].get(e.pair) == (e.metric, e.kind) and e.pair not in after["events"]): continue
                gain = pe.burden(before, m0, FG, cfg) - pe.burden(after, m0, FG, cfg)
                if gain > 1e-12: sc.append((e.metric, gain))
            best_task = max([g for m, g in sc if m == "M4"], default=None)
            chosen_off = step["metric"] != "M4"
            if chosen_off and best_task is not None:
                tie = abs(step["score"] - best_task) < 1e-12
                stats[f"B{B}_off_chosen_over_task_{'tie' if tie else 'strict'}"] += 1
                detail.append(dict(scm=scm_id, B=B, order=step["order"], chosen=step["metric"], score=step["score"], best_task=best_task, tie=tie))
            elif chosen_off: stats[f"B{B}_off_chosen_no_task_available"] += 1
            else: stats[f"B{B}_task_chosen"] += 1
            cur = pe.apply(cur, pe.Edit(step["metric"], step["error_type"], tuple(step["pair"]), step["operation"],
                           None if step["operation"]=="delete" else truth[tuple(step["pair"])]))
            applied.add((step["metric"], tuple(step["pair"]), step["operation"]))
json.dump(dict(stats=stats, detail=detail, zone_sizes=zone_sizes), open(out, "w"), indent=1)
print(dict(stats))
import statistics as st
print("task_true mean", st.mean(z["task_true"] for z in zone_sizes), "off_true mean", st.mean(z["off_true"] for z in zone_sizes), "off_pred mean", st.mean(z["off_pred"] for z in zone_sizes))
for x in detail: print(x)

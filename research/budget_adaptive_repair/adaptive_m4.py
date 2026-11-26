"""Exploratory blocker-aware M4 policy; never accepts evaluation outcomes."""
from __future__ import annotations

from research.original_objective import policy_engine as pe


def run(truth, initial, action, target, budget, config=pe.Config()):
    if type(budget) is not int or budget < 0:
        raise ValueError("budget must be a nonnegative integer")
    start = pe.metrics(truth, initial, action, target, config)
    pool = pe.candidates(truth, initial, action, target, config)
    current, log, spent, applied, rejects = dict(initial), [], 0, set(), 0
    cost_map = dict(config.costs)

    def scored_task(state):
        before = pe.metrics(truth, state, action, target, config)
        rows=[]
        for e in pool:
            if e.metric != "M4" or e.key in applied or state.get(e.pair) == e.replacement:
                continue
            trial=pe.apply(state,e)
            if not pe.dag(trial):
                continue
            after=pe.metrics(truth,trial,action,target,config)
            direct=before["events"].get(e.pair)==(e.metric,e.kind) and e.pair not in after["events"]
            gain=pe.burden(before,start,("M4",),config)-pe.burden(after,start,("M4",),config)
            if direct and gain>1e-12:
                rows.append((e,gain/cost_map[e.operation],trial))
        rows.sort(key=lambda r:(-r[1],pe.METRICS.index(r[0].metric),r[0].pair,r[0].operation))
        return rows

    while spent < budget:
        task_rows=scored_task(current)
        if task_rows:
            e,score,trial=task_rows[0]
            before=pe.graph_hash(current); current=trial; spent+=cost_map[e.operation]; applied.add(e.key)
            log.append({"metric":"M4","kind":e.kind,"pair":list(e.pair),"operation":e.operation,
                        "score":score,"before_hash":before,"after_hash":pe.graph_hash(current),"cost":cost_map[e.operation]})
            continue
        # Look ahead only when at least one positive-gain M4 repair is cycle-blocked.
        curr=pe.metrics(truth,current,action,target,config)
        blocked=[]
        for e in pool:
            if e.metric!="M4" or e.key in applied or current.get(e.pair)==e.replacement:
                continue
            trial=pe.apply(current,e)
            if pe.dag(trial): continue
            after=pe.metrics(truth,trial,action,target,config)
            direct=curr["events"].get(e.pair)==(e.metric,e.kind) and e.pair not in after["events"]
            gain=pe.burden(curr,start,("M4",),config)-pe.burden(after,start,("M4",),config)
            if direct and gain>1e-12: blocked.append((e,gain/cost_map[e.operation]))
        if not blocked:
            break
        if budget-spent<2:
            break
        blockers=[]
        for blocker in pool:
            if blocker.metric!="M2" or blocker.kind!="FP" or blocker.operation!="delete" or blocker.key in applied:
                continue
            after_block=pe.apply(current,blocker)
            if not pe.dag(after_block): continue
            unlocked=scored_task(after_block)
            if not unlocked: continue
            # Require that this repair actually removes a reference-relative off-task FP.
            if curr["events"].get(blocker.pair)!=("M2","FP"): continue
            best_gain=unlocked[0][1]
            blockers.append((blocker,best_gain,len(unlocked),unlocked[0]))
        if not blockers:
            break
        blockers.sort(key=lambda r:(-r[1],-r[2],r[0].pair,r[0].operation))
        blocker,_,_,task_row=blockers[0]
        before=pe.graph_hash(current); current=pe.apply(current,blocker); spent+=cost_map[blocker.operation]; applied.add(blocker.key)
        log.append({"metric":"M2_BLOCKER","kind":"FP","pair":list(blocker.pair),"operation":"delete",
                    "score":None,"before_hash":before,"after_hash":pe.graph_hash(current),"cost":cost_map[blocker.operation]})
        task,score,trial=task_row
        if not pe.dag(trial):
            rejects+=1; break
        before=pe.graph_hash(current); current=trial; spent+=cost_map[task.operation]; applied.add(task.key)
        log.append({"metric":"M4","kind":task.kind,"pair":list(task.pair),"operation":task.operation,
                    "score":score,"before_hash":before,"after_hash":pe.graph_hash(current),"cost":cost_map[task.operation]})
    return {"final_graph":current,"edits":log,"cost":spent,"unused_budget":budget-spent,
            "remaining_errors":sum(sum(x.values()) for x in pe.metrics(truth,current,action,target,config)["counts"].values()),
            "stop_reason":"budget_exhausted" if spent>=budget else "no_feasible_or_unblocked_task_edit",
            "dag_rejects":rejects}

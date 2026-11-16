"""Recompute Step 4B-1 design diagnostics from immutable matrix v2."""
from __future__ import annotations
from collections import Counter, defaultdict
import gzip, json
from pathlib import Path

from .policy_engine import _candidates, _distance, _acyclic
from .step4_topology_generator import generate_topology
from .step4b_task_budget import derive_stream_seeds, graph_hash, relabel_roles, select_task_pair
from .step4_error_injection import inject_condition

HERE = Path(__file__).parent
SOURCE = HERE / "step4b_task_budget_feasibility_v3.json.gz"
OUTPUT = HERE / "step4b1_critical_design_audit_v2.json"
KINDS = ("FN", "FP", "REV")
BUDGETS = (0, 1, 2, 4, 6)

def canonical(data):
    return json.dumps(data, sort_keys=True, separators=(",", ":"), default=list)

def reconstruct(row):
    streams = derive_stream_seeds(row["seed"])
    base = generate_topology(row["n"], row["template"], streams["topology"])
    nodes, truth, _, _ = relabel_roles(row["template"], base.nodes, base.edges, streams["relabel"])
    if row["task_kind"] == "indirect" and row["template"] == "observed_common_cause":
        preferred = (row["action"], row["target"])
        selected = select_task_pair(nodes, truth, streams["task"], preferred)
        assert dict(selected["selected"])["indirect"] == preferred
    requested = row.get("requested_error_type")
    injected = inject_condition(nodes, truth, row["action"], row["target"], row["condition"],
                                seed=streams["error_injection"], requested_b_type=requested)
    if injected.accepted:
        assert graph_hash(nodes, injected.initial_edges) == row["initial_hash"]
    return nodes, set(truth), set(injected.initial_edges)

def within_type_orders(nodes, truth, initial, action, target, kind):
    candidates = _candidates(nodes, truth, initial, (kind,))
    valid = []
    for op in candidates:
        _, a, b = op
        graph = set(initial)
        if kind == "FN": graph.add((a, b))
        elif kind == "FP": graph.remove((a, b))
        else: graph.remove((a, b)); graph.add((b, a))
        if _acyclic(nodes, graph): valid.append(op)
    global_order = sorted(valid)
    distance = _distance(nodes, initial, set(), action, target)
    def score(op):
        return sum(1/(1+distance[x]) if x in distance else 0 for x in op[1:])
    task_order = sorted(valid, key=lambda op:(-score(op),op[1],op[2]))
    return global_order, task_order

def pair_key(e):
    return (e["n"], e["template"], e["seed"], e["task_kind"], e["condition"],
            e["policy"][2:], e["budget"])

def analyze(data):
    rows, executions = data["rows"], data["executions"]
    initial_by_key = {(r["n"], r["template"], r["seed"], r["task_kind"], r["condition"]): r
                      for r in rows if r["accepted"]}
    reconstructed = {id(r):reconstruct(r) for r in rows if r["accepted"]}
    cond = {}
    for condition in ("A_path_disconnected", "B_path_survives", "C_mixed"):
        subset = [r for r in rows if r["condition"] == condition]
        hashes = [r["initial_hash"] for r in subset if r["accepted"]]
        cond[condition] = {
            "planned": len(subset), "accepted": sum(r["accepted"] for r in subset),
            "failed": sum(not r["accepted"] for r in subset),
            "unique_initial_graphs": len(set(hashes)),
            "duplicate_rate": (len(hashes)-len(set(hashes)))/len(hashes) if hashes else None,
            "task": {k: {"planned":sum(r["task_kind"]==k for r in subset),
                         "accepted":sum(r["task_kind"]==k and r["accepted"] for r in subset)}
                     for k in ("direct", "indirect")},
            "error_totals": {k:sum(r["errors"].get(k,0) for r in subset if r["accepted"]) for k in KINDS},
            "n_unique": {str(n):len({r["initial_hash"] for r in subset if r["accepted"] and r["n"]==n})
                         for n in range(6,11)},
            "template_unique": {t:len({r["initial_hash"] for r in subset if r["accepted"] and r["template"]==t})
                                for t in sorted({r["template"] for r in subset})}}
    b_rows = [r for r in rows if r["condition"] == "B_path_survives"]
    b = {kind:{"planned":sum(r["requested_error_type"]==kind for r in b_rows),
               "accepted":sum(r["requested_error_type"]==kind and r["accepted"] for r in b_rows),
               "failed":sum(r["requested_error_type"]==kind and not r["accepted"] for r in b_rows),
               "by_task":{t:sum(r["requested_error_type"]==kind and r["task_kind"]==t and r["accepted"] for r in b_rows)
                          for t in ("direct","indirect")},
               "by_template":{t:sum(r["requested_error_type"]==kind and r["template"]==t and r["accepted"] for r in b_rows)
                              for t in sorted({r["template"] for r in b_rows})},
               "dag_valid_fixes":sum(r["opportunities"].get(kind,{}).get("dag_valid_count",0)
                                      for r in b_rows if r["requested_error_type"]==kind and r["accepted"])}
         for kind in KINDS}
    budgets = {}
    for budget in BUDGETS:
        es=[e for e in executions if e["budget"]==budget]
        budgets[str(budget)]={"runs":len(es),"spent_total":sum(e["spent"] for e in es),
            "unused_total":sum(e["unused"] for e in es),"fully_used":sum(e["unused"]==0 for e in es),
            "edited":sum(e["edit_count"]>0 for e in es),"cycle_rejections":sum(e["cycle_rejections"] for e in es),
            "unique_final_graphs":len({e["final_hash"] for e in es}),
            "termination":dict(Counter(e["termination_reason"] for e in es))}
    # Matched Global/Task-Focused pairs and structural opportunity classes.
    paired=defaultdict(dict)
    for e in executions: paired[pair_key(e)][e["policy"][0]]=e
    pair_rows=[]
    h2_cross=defaultdict(Counter)
    for key, modes in paired.items():
        if set(modes)!={"G","T"}: continue
        g,t=modes["G"],modes["T"]
        n,template,seed,task,condition,allowed,budget=key
        row=initial_by_key[(n,template,seed,task,condition)]
        nodes, truth, initial = reconstructed[id(row)]
        orders={kind:within_type_orders(nodes,truth,initial,row["action"],row["target"],kind)
                for kind in allowed.split("-")}
        valid_counts={kind:len(orders[kind][0]) for kind in orders}
        competing=[kind for kind in allowed.split("-") if valid_counts[kind]>=2]
        rank_diff=[kind for kind in competing if orders[kind][0]!=orders[kind][1]]
        seq_diff=g["edits"]!=t["edits"]; graph_diff=g["final_hash"]!=t["final_hash"]
        sufficient_budget = budget >= sum(valid_counts[k] for k in allowed.split("-"))
        reason=("same_type_candidates_le_1" if not competing else
                "competition_rank_same" if not rank_diff else
                "rank_diff_final_graph_diff" if graph_diff else
                "rank_diff_sequence_only" if seq_diff else
                "rank_diff_budget_sufficient_same_final" if sufficient_budget else
                "rank_diff_budget_limited_same_final")
        record={"condition":condition,"task":task,"template":template,"budget":budget,
                "allowed_types":allowed,"competing_types":competing,"rank_differing_types":rank_diff,
                "candidate_counts":valid_counts,
                "sequence_diff":seq_diff,"final_graph_diff":graph_diff,
                "budget_spent_same":g["spent"]==t["spent"],
                "budget_sufficient_for_initial_valid_candidates":sufficient_budget,
                "cycle_rejections_differ":g["cycle_rejections"]!=t["cycle_rejections"],"class":reason}
        pair_rows.append(record)
        h2_cross[(condition,task,template,budget,allowed)][reason]+=1
    # Initial-graph diversity by seed and assignment axes.
    unique_by_seed={str(s):len({r["truth_hash"] for r in rows if r["seed"]==s}) for s in (11,12,13,14,15)}
    common=[r for r in rows if r["template"]=="observed_common_cause" and r["task_kind"]=="indirect" and r["accepted"]]
    common_summary={"indirect_rows":len(common),"scaffold_pair_selected":sum(r["action"]==r["role_map"]["action"] and r["target"]==r["role_map"]["target"] for r in common),
                    "direct_and_indirect_relation":sum(r["task_relation"]=="direct_and_indirect" for r in common),
                    "indirect_only_relation":sum(r["task_relation"]=="indirect_only" for r in common)}
    return {"source_file":SOURCE.name,"source_protocol":data["protocol"],"settings_sha256":data["settings_sha256"],
        "planned":data["planned_task_condition_attempts"],"accepted":data["accepted_task_conditions"],
        "failed":data["failed_task_conditions"],"unique_initial_graphs":data["unique_initial_graphs"],
        "policy_execution_count":data["policy_execution_count"],"condition":cond,"B_type_strata":b,
        "budgets":budgets,"paired_policy_count":len(pair_rows),
        "paired_policy_summary":dict(Counter(r["class"] for r in pair_rows)),
        "paired_policy_flags":{"same_type_candidate_count_le_1":sum(not r["competing_types"] for r in pair_rows),
            "rank_order_diff":sum(bool(r["rank_differing_types"]) for r in pair_rows),
            "sequence_diff":sum(r["sequence_diff"] for r in pair_rows),
            "final_graph_diff":sum(r["final_graph_diff"] for r in pair_rows),
            "cycle_rejection_difference":sum(r["cycle_rejections_differ"] for r in pair_rows),
            "rank_diff_budget_sufficient_same_final":sum(bool(r["rank_differing_types"]) and not r["final_graph_diff"] and r["budget_sufficient_for_initial_valid_candidates"] for r in pair_rows)},
        "paired_policy_cross_table":[{"condition":k[0],"task":k[1],"template":k[2],"budget":k[3],"allowed_types":k[4],"counts":dict(v)} for k,v in sorted(h2_cross.items())],
        "paired_policy_rows":pair_rows,"seed_truth_structure_diversity":unique_by_seed,
        "common_cause":common_summary}

def main():
    data=json.loads(gzip.decompress(SOURCE.read_bytes()))
    result=analyze(data)
    OUTPUT.write_text(json.dumps(result,indent=2)+chr(10),encoding="utf-8")
    print(json.dumps({k:result[k] for k in ("planned","accepted","failed","unique_initial_graphs","policy_execution_count","paired_policy_count","paired_policy_summary")},indent=2))
if __name__=="__main__": main()

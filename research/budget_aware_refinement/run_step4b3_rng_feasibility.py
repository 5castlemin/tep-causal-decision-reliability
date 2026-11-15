"""New-version topology-only feasibility run with context-keyed RNG streams."""
from __future__ import annotations

from collections import Counter, defaultdict
from hashlib import sha256
import gzip
import json
from pathlib import Path

from .policy_engine import refine
from .step4_error_injection import inject_condition
from .step4_topology_generator import TEMPLATES, generate_topology, is_dag, directed_paths
from .step4b_task_budget import (classify_task_pairs, graph_hash, relabel_roles,
                                 role_nodes, select_task_pair)
from .step4b2_population import classify_error_location, competition_recipes, select_q_recipe
from .step4_rng import RNGKey, RNG_PROTOCOL_VERSION, STREAMS, derive_seed, derive_streams

HERE = Path(__file__).parent
OUTPUT = HERE / "step4b3_rng_feasibility_v1.json.gz"
MASTER_SEEDS = (11, 12, 13, 14, 15)
NODE_COUNTS = tuple(range(6, 11))
TASKS = ("direct", "indirect")
ERROR_TYPES = ("FN", "FP", "REV")
BUDGETS = (0, 1, 2, 4, 6)
SETTINGS = {
    "protocol_version": RNG_PROTOCOL_VERSION,
    "cohort": "development",
    "master_seeds": MASTER_SEEDS,
    "node_counts": NODE_COUNTS,
    "templates": TEMPLATES,
    "topology_attempts": (0,),
    "task_slots": TASKS,
    "conditions": ("A_path_disconnected", "B_path_survives", "C_mixed"),
    "B_types_each_task": ERROR_TYPES,
    "Q_budget": 1,
    "Q_gamma": 1,
    "Q_recipe_selection": "separate q_recipe_selection stream; SHA256 deterministic selection; no outcome filtering",
    "retries": 0,
    "replacement": False,
    "outcomes_used": False,
    "coefficient_or_observation_sampling": False,
}
SETTINGS_SHA256 = sha256(json.dumps(SETTINGS, sort_keys=True, separators=(",", ":"),
                                   default=list).encode()).hexdigest()


def _key(cohort, seed, scm_id, template, n, attempt, stream, substream="", replicate=0):
    return RNGKey(RNG_PROTOCOL_VERSION, cohort, seed, scm_id, template, n,
                  attempt, stream, replicate, substream)


def _err_row(nodes, truth, task, condition, seed, requested=None):
    result = inject_condition(nodes, truth, *task, condition, seed=seed,
                              requested_b_type=requested)
    return {"condition": condition, "requested_type": requested,
            "accepted": result.accepted, "reason": result.reason,
            "truth_dag": is_dag(nodes, truth),
            "initial_dag": is_dag(nodes, result.initial_edges),
            "path_survives": bool(result.remaining_paths) if result.accepted else None,
            "errors": result.errors if result.accepted else (),
            "related_errors": result.relevant_errors if result.accepted else (),
            "peripheral_errors": result.peripheral_errors if result.accepted else (),
            "locations": classify_error_location(nodes, truth, *task, result.errors)
            if result.accepted else (),
            "truth_hash": graph_hash(nodes, truth),
            "initial_hash": graph_hash(nodes, result.initial_edges) if result.accepted else None,
            "initial_edges": sorted(result.initial_edges) if result.accepted else (),
            "error_seed": seed}


def _topology_records():
    records = []
    for template in TEMPLATES:
        for n in NODE_COUNTS:
            for seed in MASTER_SEEDS:
                attempt = 0
                scm_id = f"dev-{template}-n{n}-seed{seed}-attempt{attempt}"
                streams = derive_streams(cohort="development", master_seed=seed,
                                         scm_id=scm_id, topology_template=template,
                                         node_count=n, topology_attempt=attempt)
                base = generate_topology(n, template, streams["topology"])
                nodes, truth, roles, mapping = relabel_roles(template, base.nodes,
                                                             base.edges, streams["node_relabeling"])
                classes = classify_task_pairs(nodes, truth)
                preferred = (roles["action"], roles["target"]) if template == "observed_common_cause" else None
                selected = select_task_pair(nodes, truth, streams["task_selection"], preferred)
                task_map = dict(selected["selected"])
                topology = {"scm_id": scm_id, "cohort": "development", "master_seed": seed,
                            "template": template, "n": n, "attempt": attempt,
                            "accepted": is_dag(nodes, truth), "reason": "accepted" if is_dag(nodes, truth) else "generated_graph_not_dag",
                            "nodes": nodes, "truth_edges": sorted(truth),
                            "truth_hash": graph_hash(nodes, truth), "role_map": roles,
                            "id_mapping": mapping, "task_candidate_counts": {
                                "direct_only": len(classes.direct_only),
                                "indirect_only": len(classes.indirect_only),
                                "direct_and_indirect": len(classes.direct_and_indirect)},
                            "task_selection_failures": selected["failures"],
                            "stream_seeds": streams,
                            "unused_stream_seeds_are_not_draws": tuple(
                                name for name in STREAMS if name not in
                                ("topology", "node_relabeling", "task_selection"))}
                for task_kind in TASKS:
                    task = task_map.get(task_kind)
                    task_row = {"scm_id": scm_id, "template": template, "n": n,
                                "master_seed": seed, "attempt": attempt,
                                "task_kind": task_kind,
                                "task_accepted": task is not None,
                                "task_failure": selected["failures"].get(task_kind),
                                "action": task[0] if task else None,
                                "target": task[1] if task else None,
                                "task_relation": (
                                    "direct_only" if task_kind == "direct" else "indirect_only")}
                    if task is None:
                        for condition, requested in (("A_path_disconnected", None),
                                                     ("B_path_survives", "FN"),
                                                     ("B_path_survives", "FP"),
                                                     ("B_path_survives", "REV"),
                                                     ("C_mixed", None)):
                            records.append({**task_row, "condition": condition,
                                            "requested_type": requested, "accepted": False,
                                            "reason": f"task_selection_failed:{task_row['task_failure']}"})
                        continue
                    # Classify the actual structural relation, including overlap.
                    relation = ("direct_and_indirect" if task in classes.direct_and_indirect
                                else "direct_only" if task in classes.direct_only
                                else "indirect_only")
                    task_row["task_relation"] = relation
                    for condition, requested in (("A_path_disconnected", None),
                                                 ("B_path_survives", "FN"),
                                                 ("B_path_survives", "FP"),
                                                 ("B_path_survives", "REV"),
                                                 ("C_mixed", None)):
                        substream = f"{task_kind}:{condition}:{requested or 'all'}"
                        err_seed = derive_seed(_key("development", seed, scm_id, template,
                                                    n, attempt, "error_injection", substream))
                        err = _err_row(nodes, truth, task, condition, err_seed, requested)
                        records.append({**task_row, **err})
                records.append({"record_type": "topology", **topology})
    return records


def run():
    generated = _topology_records()
    topology_rows = [r for r in generated if r.get("record_type") == "topology"]
    p_rows = [r for r in generated if "condition" in r]
    summary = {"planned_topologies": len(topology_rows),
               "topology_failures": sum(not r["accepted"] for r in topology_rows),
               "planned_task_condition_rows": len(p_rows),
               "task_selection_failure_condition_rows": sum(not r.get("task_accepted", False) for r in p_rows),
               "task_selection_failure_slots": len({(r["scm_id"], r["task_kind"]) for r in p_rows
                                                     if not r.get("task_accepted", False)}),
               "accepted_by_condition_type": {},
               "failed_by_condition_type_reason": {},
               "unique_topologies": len({r["truth_hash"] for r in topology_rows}),
               "role_action_id_counts_by_template": {},
               "relabel_equal_pairs_same_seed_nodecount_across_templates": 0,
               "relabel_pair_count_same_seed_nodecount_across_templates": 0}
    accepted_counts = Counter()
    failure_counts = Counter()
    role_counts = defaultdict(Counter)
    tops = {(r["n"], r["master_seed"], r["template"]): r for r in topology_rows}
    for row in p_rows:
        key = (row["condition"], row.get("requested_type") or "ALL")
        if row.get("accepted"):
            accepted_counts[key] += 1
        else:
            failure_counts[(*key, row.get("reason", "task_selection_failed"))] += 1
    for r in topology_rows:
        role_counts[r["template"]][r["role_map"].get("action", "NA")] += 1
    for n in NODE_COUNTS:
        for seed in MASTER_SEEDS:
            group = [tops[(n, seed, t)] for t in TEMPLATES]
            for i, left in enumerate(group):
                for right in group[i + 1:]:
                    summary["relabel_pair_count_same_seed_nodecount_across_templates"] += 1
                    summary["relabel_equal_pairs_same_seed_nodecount_across_templates"] += (
                        left["id_mapping"] == right["id_mapping"])
    summary["accepted_by_condition_type"] = {f"{a}|{b}": n for (a, b), n in accepted_counts.items()}
    summary["failed_by_condition_type_reason"] = {"|".join(k): n for k, n in failure_counts.items()}
    summary["role_action_id_counts_by_template"] = {t: dict(sorted(c.items())) for t, c in role_counts.items()}

    q_rows, q_runs = [], []
    q_accept = Counter()
    q_fail = Counter()
    q_rank = Counter()
    q_final = Counter()
    q_budget = defaultdict(Counter)
    task_by_id = {(r["scm_id"], r["task_kind"]): r for r in p_rows}
    top_by_id = {r["scm_id"]: r for r in topology_rows}
    for (scm_id, task_kind), task_row in task_by_id.items():
        if not task_row.get("task_accepted"):
            for kind in ERROR_TYPES:
                q_fail[kind] += 1
                q_rows.append({"scm_id": scm_id, "task_kind": task_kind,
                               "error_type": kind, "accepted": False,
                               "reason": "task_selection_failed"})
            continue
        top = top_by_id[scm_id]
        nodes, truth = tuple(top["nodes"]), set(map(tuple, top["truth_edges"]))
        task = (task_row["action"], task_row["target"])
        base_seed = top["master_seed"]
        for kind in ERROR_TYPES:
            recipes = competition_recipes(nodes, truth, *task, kind)
            qseed = derive_seed(_key("development", base_seed, scm_id, top["template"],
                                     top["n"], top["attempt"], "q_recipe_selection",
                                     f"{task_kind}:{kind}"))
            selected = select_q_recipe(recipes, qseed)
            if selected is None:
                q_fail[kind] += 1
                q_rows.append({"scm_id": scm_id, "template": top["template"],
                               "n": top["n"], "master_seed": base_seed,
                               "task_kind": task_kind, "error_type": kind,
                               "accepted": False,
                               "feasible_recipe_count": len(recipes),
                               "reason": "no_two_same_type_related_peripheral_dag_valid_candidates"})
                continue
            q_accept[kind] += 1
            q_rank[kind] += selected["rank_diverges"]
            initial = set(selected["initial_edges"])
            qrow = {"scm_id": scm_id, "template": top["template"], "n": top["n"],
                    "master_seed": base_seed, "task_kind": task_kind,
                    "action": task[0], "target": task[1], "error_type": kind,
                    "accepted": True, "feasible_recipe_count": len(recipes),
                    "candidate_count": selected["candidate_count"],
                    "initial_hash": graph_hash(nodes, initial),
                    "truth_hash": graph_hash(nodes, truth),
                    "errors": selected["errors"], "locations": selected["locations"],
                    "path_survives": bool(directed_paths(nodes, initial, *task)),
                    "rank_diverges": selected["rank_diverges"],
                    "global_candidate_order": selected["candidate_orders"]["global"],
                    "task_focused_candidate_order": selected["candidate_orders"]["task_focused"],
                    "rng_seed": qseed}
            for budget in BUDGETS:
                logs = {}
                common_schedule = derive_seed(_key("development", base_seed, scm_id,
                                                   top["template"], top["n"], top["attempt"],
                                                   "policy_schedule", f"{task_kind}:{kind}:B{budget}"))
                for mode in ("G", "T"):
                    logs[mode] = refine(node_ids=nodes, initial_edges=initial,
                                        reference_edges=truth, allowed_types=(kind,),
                                        policy_id=f"{mode}-{kind}", budget=budget,
                                        gamma=1, action=task[0], target=task[1],
                                        seed=common_schedule, schedule_seed=common_schedule,
                                        graph_id=graph_hash(nodes, initial))
                diff = logs["G"]["final_hash"] != logs["T"]["final_hash"]
                q_final[(kind, budget)] += diff
                q_budget[(kind, budget)]["cells"] += 1
                q_budget[(kind, budget)]["sequence_diff"] += logs["G"]["edit_sequence"] != logs["T"]["edit_sequence"]
                q_budget[(kind, budget)]["final_graph_diff"] += diff
                q_budget[(kind, budget)]["global_spent"] += logs["G"]["spent_budget"]
                q_budget[(kind, budget)]["task_focused_spent"] += logs["T"]["spent_budget"]
                q_runs.append({"scm_id": scm_id, "template": top["template"], "n": top["n"],
                               "master_seed": base_seed, "task_kind": task_kind,
                               "error_type": kind, "budget": budget,
                               "global_seed": logs["G"]["seed"],
                               "task_focused_seed": logs["T"]["seed"],
                               "same_schedule": logs["G"]["type_schedule"] == logs["T"]["type_schedule"],
                               "global_edits": logs["G"]["edit_sequence"],
                               "task_focused_edits": logs["T"]["edit_sequence"],
                               "sequence_diff": logs["G"]["edit_sequence"] != logs["T"]["edit_sequence"],
                               "final_graph_diff": diff,
                               "global_hash": logs["G"]["final_hash"],
                               "task_focused_hash": logs["T"]["final_hash"],
                               "global_spent": logs["G"]["spent_budget"],
                               "task_focused_spent": logs["T"]["spent_budget"]})
            q_rows.append({**qrow, "budget_final_graph_diff": {
                str(b): sum(x["scm_id"] == scm_id and x["task_kind"] == task_kind and
                            x["error_type"] == kind and x["budget"] == b and x["final_graph_diff"]
                            for x in q_runs) for b in BUDGETS}})
    q_types_by_task = defaultdict(set)
    for row in q_rows:
        if row.get("accepted"):
            q_types_by_task[(row["scm_id"], row["task_kind"])].add(row["error_type"])
    q_common_tasks = {key for key, types in q_types_by_task.items()
                      if set(ERROR_TYPES).issubset(types)}
    q_common_scms = {scm_id for scm_id, _ in q_common_tasks}
    q_common_by_type = {}
    for kind in ERROR_TYPES:
        cells = [r for r in q_rows if r.get("accepted") and r["error_type"] == kind and
                 (r["scm_id"], r["task_kind"]) in q_common_tasks]
        q_common_by_type[kind] = {
            "cells": len(cells),
            "rank_divergent": sum(r["rank_diverges"] for r in cells),
            "by_template": {t: sum(r["template"] == t for r in cells) for t in TEMPLATES},
            "by_node_count": {str(n): sum(r["n"] == n for r in cells) for n in NODE_COUNTS}}
    q_common_strata = Counter(top_by_id[scm_id]["template"] for scm_id in q_common_scms)
    summary["Q"] = {"planned_cells_by_type": {k: len(task_by_id) for k in ERROR_TYPES},
                    "accepted_by_type": dict(q_accept), "failed_by_type": dict(q_fail),
                    "selected_rank_divergent_by_type": dict(q_rank),
                    "common_support_task_cells_all_types": len(q_common_tasks),
                    "common_support_scm_ids_all_types": len(q_common_scms),
                    "common_support_scm_by_template": dict(q_common_strata),
                    "common_support_by_type": q_common_by_type,
                    "budget_summary": {f"{k}|{b}": dict(v) for (k, b), v in sorted(q_budget.items())},
                    "final_graph_diffs_by_type_budget": {f"{k}|{b}": q_final[(k, b)]
                                                         for k in ERROR_TYPES for b in BUDGETS}}
    return {"protocol": "STEP4B3_CONTEXT_KEYED_RNG_STRUCTURE_FEASIBILITY_V1",
            "settings": SETTINGS, "settings_sha256": SETTINGS_SHA256,
            "stream_names": STREAMS, "planned_topology_grid": len(topology_rows),
            "planned_P_task_condition_rows": len(p_rows),
            "planned_Q_task_type_cells": len(task_by_id) * len(ERROR_TYPES),
            "summary": summary, "topologies": topology_rows,
            "P_rows": p_rows, "Q_rows": q_rows, "Q_policy_runs": q_runs}


def main():
    result = run()
    payload = json.dumps(result, sort_keys=True, separators=(",", ":"),
                         default=list).encode("utf-8")
    OUTPUT.write_bytes(gzip.compress(payload, compresslevel=9, mtime=0))
    print(json.dumps({"settings_sha256": result["settings_sha256"],
                      "topologies": result["planned_topology_grid"],
                      "P_task_condition_rows": result["planned_P_task_condition_rows"],
                      "Q_cells": result["planned_Q_task_type_cells"],
                      "summary": result["summary"], "output": OUTPUT.name},
                     sort_keys=True, indent=2, default=list))


if __name__ == "__main__":
    main()

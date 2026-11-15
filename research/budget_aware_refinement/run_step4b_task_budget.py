"""Run the bounded Step 4B-1 topology/task/budget diagnostic matrix only."""
from collections import Counter
from hashlib import sha256
import gzip
import itertools
import json
from pathlib import Path

from .policy_engine import refine
from .step4_error_injection import CONDITIONS, inject_condition
from .step4_topology_generator import TEMPLATES, generate_topology, is_dag
from .step4b_task_budget import (classify_task_pairs, graph_hash, operation_opportunities,
                                 derive_stream_seeds, relabel_roles, select_task_pair)

SEEDS = (11, 12, 13, 14, 15)
NODE_COUNTS = tuple(range(6, 11))
BUDGETS = (0, 1, 2, 4, 6)
GAMMA = 1
TYPES = ("FN", "FP", "REV")
B_TYPE_SCHEDULE = ("FN", "FP", "REV")
POLICIES = tuple((mode, subset) for mode in ("G", "T")
                 for size in range(1, 4) for subset in itertools.combinations(TYPES, size))
OUTPUT = Path(__file__).with_name("step4b_task_budget_feasibility_v3.json.gz")

SETTINGS = {"seeds": SEEDS, "node_counts": NODE_COUNTS, "templates": TEMPLATES,
            "conditions": CONDITIONS, "budgets": BUDGETS, "gamma": GAMMA,
            "task_selection": "independent task stream; distinct direct-only and indirect pair; common-cause scaffold X-to-Y selected whenever indirect",
            "role_relabel": "independent domain-separated stream; seeded bijection of immutable IDs",
            "rng_streams": ("topology=master seed", "relabel=SHA256 domain derived",
                            "task=SHA256 domain derived", "error_injection=SHA256 domain derived",
                            "policy_schedule=SHA256 domain derived"),
            "B_type_strata": "preassigned cyclic schedule (seed index + node-count index + template index + task-slot index) mod 3; no cross-type replacement",
            "C_recipe_search": "all disjoint one-each FN/FP/REV recipes; retain if any of six atomic orders keeps every intermediate graph a DAG; no path survival requirement",
            "retries": 0, "replacement": False, "policies": len(POLICIES)}
SETTINGS_SHA256 = sha256(json.dumps(SETTINGS, sort_keys=True, separators=(",", ":"),
                               default=list).encode()).hexdigest()


def run_matrix():
    rows, executions = [], []
    for n in NODE_COUNTS:
        for template in TEMPLATES:
            for seed in SEEDS:
                streams = derive_stream_seeds(seed)
                base = generate_topology(n, template, streams["topology"])
                nodes, truth, roles, mapping = relabel_roles(template, base.nodes, base.edges, streams["relabel"])
                preferred_indirect = ((roles["action"], roles["target"])
                                      if template == "observed_common_cause" else None)
                selected = select_task_pair(nodes, truth, streams["task"], preferred_indirect)
                tasks = dict(selected["selected"])
                task_classes = classify_task_pairs(nodes, truth)
                for kind in ("direct", "indirect"):
                    task = tasks.get(kind)
                    for condition in CONDITIONS:
                        if task is None:
                            rows.append({"n": n, "template": template, "seed": seed,
                                         "task_kind": kind, "condition": condition, "accepted": False,
                                         "reason": selected["failures"][kind], "role_map": roles,
                                         "task_counts": selected["candidate_counts"],
                                         "id_mapping": mapping, "rng_seeds": streams,
                                         "truth_dag": is_dag(nodes, truth), "initial_dag": None,
                                         "path_survives": None, "errors": {},
                                         "related_errors": 0, "peripheral_errors": 0,
                                         "truth_hash": graph_hash(nodes, truth), "initial_hash": None})
                            continue
                        action, target = task
                        b_type = None
                        if condition == "B_path_survives":
                            b_type = B_TYPE_SCHEDULE[(SEEDS.index(seed) + NODE_COUNTS.index(n) +
                                                     TEMPLATES.index(template) + (kind == "indirect")) % 3]
                        relation = ("direct_only" if task in task_classes.direct_only else
                                    "indirect_only" if task in task_classes.indirect_only else
                                    "direct_and_indirect")
                        result = inject_condition(nodes, truth, action, target, condition,
                                                  seed=streams["error_injection"],
                                                  requested_b_type=b_type)
                        errors = Counter(error[0] for error in result.errors)
                        row = {"n": n, "template": template, "seed": seed,
                               "task_kind": kind, "action": action, "target": target,
                               "task_relation": relation,
                               "same_pair": selected["same_pair"], "task_counts": selected["candidate_counts"],
                               "role_map": roles, "id_mapping": mapping, "condition": condition,
                               "requested_error_type": b_type,
                               "rng_seeds": streams,
                               "accepted": result.accepted, "reason": result.reason,
                               "truth_dag": is_dag(nodes, truth),
                               "initial_dag": is_dag(nodes, result.initial_edges),
                               "path_survives": bool(result.remaining_paths),
                               "errors": {k: errors[k] for k in TYPES},
                               "related_errors": len(result.relevant_errors),
                               "peripheral_errors": len(result.peripheral_errors),
                               "truth_hash": graph_hash(nodes, truth),
                               "initial_hash": graph_hash(nodes, result.initial_edges)}
                        rows.append(row)
                        if not result.accepted:
                            continue
                        opportunities = operation_opportunities(nodes, truth, result.initial_edges)
                        row["opportunities"] = {k: {"candidate_count": v["candidate_count"],
                                                   "dag_valid_count": v["dag_valid_count"]}
                                                 for k, v in opportunities.items()}
                        for mode, allowed in POLICIES:
                            policy_id = mode + "-" + "-".join(allowed)
                            for budget in BUDGETS:
                                log = refine(node_ids=nodes, initial_edges=result.initial_edges,
                                             reference_edges=truth, allowed_types=allowed,
                                             policy_id=policy_id, budget=budget, gamma=GAMMA,
                                             action=action, target=target, seed=streams["policy_schedule"],
                                             graph_id=row["initial_hash"])
                                original_ops = {tuple(item["operation"])
                                                for values in opportunities.values()
                                                for item in values["candidates"]}
                                seen_ops = set(original_ops)
                                newly_available = {kind: set() for kind in TYPES}
                                candidate_trace = []
                                for scan in log["candidate_operations"]:
                                    operations = [tuple(op) for op in scan.get("operations", [])]
                                    candidate_trace.append({"type": scan["type"], "count": len(operations)})
                                    for op in operations:
                                        if op not in seen_ops:
                                            newly_available[op[0]].add(op)
                                    seen_ops.update(operations)
                                executions.append({"n": n, "template": template, "seed": seed,
                                                   "task_kind": kind, "condition": condition,
                                                   "policy": policy_id, "budget": budget,
                                                   "rng_seeds": streams,
                                                   "initial_hash": row["initial_hash"],
                                                   "final_hash": log["final_hash"],
                                                   "candidate_counts": {k: v["candidate_count"] for k, v in opportunities.items()},
                                                   "dag_valid_counts": {k: v["dag_valid_count"] for k, v in opportunities.items()},
                                                   "edits": log["edit_sequence"],
                                                   "edit_count": len(log["edit_sequence"]),
                                                   "spent": log["spent_budget"],
                                                   "unused": log["unused_budget"],
                                                   "cycle_rejections": sum(x.get("reason") == "cycle" for x in log["rejected_operations"]),
                                                   "order": log["type_schedule"],
                                                   "candidate_trace": candidate_trace,
                                                   "newly_available_candidates": {k: sorted(newly_available[k]) for k in TYPES},
                                                   "termination_reason": log["termination_reason"]})
    hashes = [r["initial_hash"] for r in rows if r["accepted"]]
    execution_hashes = [r["final_hash"] for r in executions]
    return {"protocol": "STEP4B1_STRUCTURE_ONLY_TASK_BUDGET_V3_ANY_DAG_VALID_ORDER",
            "settings": SETTINGS, "settings_sha256": SETTINGS_SHA256,
            "planned_task_condition_attempts": len(rows),
            "accepted_task_conditions": sum(r["accepted"] for r in rows),
            "failed_task_conditions": sum(not r["accepted"] for r in rows),
            "condition_failures": dict(Counter(r["reason"] for r in rows if not r["accepted"])),
            "unique_initial_graphs": len(set(hashes)),
            "initial_duplicate_rate": ((len(hashes) - len(set(hashes))) / len(hashes) if hashes else None),
            "unique_final_graphs": len(set(execution_hashes)),
            "policy_execution_count": len(executions), "rows": rows, "executions": executions}


def main():
    result = run_matrix()
    raw = (json.dumps(result, indent=2) + "\n").encode("utf-8")
    OUTPUT.write_bytes(gzip.compress(raw, compresslevel=9, mtime=0))
    print(json.dumps({k: result[k] for k in ("planned_task_condition_attempts",
                                             "accepted_task_conditions", "failed_task_conditions",
                                             "condition_failures", "unique_initial_graphs",
                                             "policy_execution_count", "settings_sha256")}, indent=2))


if __name__ == "__main__":
    main()

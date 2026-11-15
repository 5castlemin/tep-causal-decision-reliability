"""Run a fixed, bounded topology/error matrix; no SCM or outcomes are made."""
from collections import Counter, defaultdict
from dataclasses import asdict
import hashlib
import json
from pathlib import Path

from .step4_error_injection import CONDITIONS, inject_condition
from .step4_topology_generator import TEMPLATES, generate_topology, is_dag

SEEDS = (11, 12, 13, 14, 15)  # covers each B error class via seed rotation
NODE_COUNTS = tuple(range(6, 11))
REPORT = Path(__file__).with_name("step4a_feasibility_matrix_v2.json")


def digest(nodes, edges):
    payload = json.dumps({"nodes": sorted(nodes), "edges": sorted(map(list, edges))},
                         separators=(",", ":"), ensure_ascii=True).encode()
    return hashlib.sha256(payload).hexdigest()


def run_matrix():
    rows = []
    for n in NODE_COUNTS:
        for template in TEMPLATES:
            for seed in SEEDS:
                try:
                    topology = generate_topology(n, template, seed)
                    topology_error = None
                except Exception as exc:
                    topology, topology_error = None, f"{type(exc).__name__}:{exc}"
                for condition in CONDITIONS:
                    if topology is None:
                        rows.append({"n": n, "template": template, "seed": seed,
                                     "condition": condition, "accepted": False,
                                     "reason": "topology_failure:" + topology_error,
                                     "retry_count": 0, "truth_dag": False,
                                     "initial_dag": False, "path_survives": False,
                                     "FN": 0, "FP": 0, "REV": 0,
                                     "related_errors": 0, "peripheral_errors": 0,
                                     "truth_hash": None, "initial_hash": None})
                        continue
                    task = next((t for t in topology.tasks if t.action == topology.nodes[0]
                                 and t.target == topology.nodes[-1] and t.kind == "indirect"), None)
                    if task is None:
                        # Retain this planned cell as a structural failure.
                        result = None; reason = "no_predeclared_indirect_endpoint_task"
                    else:
                        result = inject_condition(topology.nodes, topology.edges,
                                                  task.action, task.target, condition, seed=seed)
                        reason = result.reason
                    errors = result.errors if result else ()
                    counts = Counter(e[0] for e in errors)
                    rows.append({"n": n, "template": template, "seed": seed,
                                 "condition": condition, "accepted": bool(result and result.accepted),
                                 "reason": reason, "retry_count": 0,
                                 "truth_dag": is_dag(topology.nodes, topology.edges),
                                 "initial_dag": bool(result and is_dag(topology.nodes, result.initial_edges)),
                                 "path_survives": bool(result and result.remaining_paths),
                                 "FN": counts["FN"], "FP": counts["FP"], "REV": counts["REV"],
                                 "related_errors": len(result.relevant_errors) if result else 0,
                                 "peripheral_errors": len(result.peripheral_errors) if result else 0,
                                 "truth_hash": digest(topology.nodes, topology.edges),
                                 "initial_hash": digest(topology.nodes, result.initial_edges) if result else None,
                                 "cycle_rejections": len(result.cycle_rejections) if result else 0})
    grouped = defaultdict(list)
    for row in rows:
        grouped[(row["n"], row["template"], row["condition"])].append(row)
    summary = []
    for key, group in sorted(grouped.items()):
        accepted_hashes = [r["initial_hash"] for r in group if r["accepted"]]
        unique = len(set(accepted_hashes))
        summary.append({"n": key[0], "template": key[1], "condition": key[2],
                        "attempts": len(group), "accepted": sum(r["accepted"] for r in group),
                        "failures": dict(Counter(r["reason"] for r in group if not r["accepted"])),
                        "unique_initial_graphs": unique,
                        "duplicate_rate": (len(accepted_hashes) - unique) / len(accepted_hashes) if accepted_hashes else None})
    return {"protocol": "STEP4A_FIXED_TOPOLOGY_MATRIX_V2_NODE_AND_EDGE_HASH", "seeds": SEEDS,
            "node_counts": NODE_COUNTS, "templates": TEMPLATES, "conditions": CONDITIONS,
            "attempts": len(rows), "retry_policy": "zero replacement; every planned cell retained",
            "rows": rows, "summary": summary}


def main():
    result = run_matrix()
    REPORT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"report": str(REPORT), "attempts": result["attempts"],
                      "accepted": sum(r["accepted"] for r in result["rows"]),
                      "failed": sum(not r["accepted"] for r in result["rows"])}, indent=2))


if __name__ == "__main__":
    main()

"""P/B=4 graph-only distinguishability audit against preregistered Random."""
from __future__ import annotations

from collections import Counter, defaultdict
from hashlib import sha256
from itertools import combinations
import gzip
import json
from pathlib import Path

from .policy_engine import refine
from .run_step4b2_population import _reconstruct
from .step4_error_injection import inject_condition
from .step4b_task_budget import graph_hash, operation_opportunities

HERE = Path(__file__).parent
SOURCE = HERE / "step4b_task_budget_feasibility_v4.json.gz"
OUTPUT = HERE / "step4b3_p_b4_random_audit_v1.json.gz"
RANDOM_SEEDS = (0, 6, 12, 18, 24)
KINDS = ("FN", "FP", "REV")
BUDGET = 4
GAMMA = 1
POLICY_SETS = tuple(c for size in (1, 2, 3) for c in combinations(KINDS, size))
POLICIES = tuple((mode, allowed) for mode in ("G", "T") for allowed in POLICY_SETS)
SETTINGS = {
    "source": SOURCE.name,
    "budget": BUDGET,
    "gamma": GAMMA,
    "random_seeds": RANDOM_SEEDS,
    "random_type_schedule_seed": 0,
    "policy_type_schedule_seed": 0,
    "matched_fields": ("same_initial_graph", "same_allowed_types", "same_type_schedule",
                       "same_gamma", "same_budget", "same_dag_constraints"),
    "conditions": ("A_path_disconnected", "B_path_survives", "C_mixed"),
    "no_outcome_calculation": True,
}
SETTINGS_SHA256 = sha256(json.dumps(SETTINGS, sort_keys=True, separators=(",", ":"),
                                   default=list).encode()).hexdigest()


def _initial_for_row(row, nodes, truth, task, streams):
    result = inject_condition(nodes, truth, *task, row["condition"],
                              seed=streams["error_injection"],
                              requested_b_type=row["requested_error_type"])
    if not result.accepted:
        raise AssertionError("preserved v4 accepted row no longer regenerates")
    if graph_hash(nodes, result.initial_edges) != row["initial_hash"]:
        raise AssertionError("initial graph differs from preserved v4 matrix")
    return set(result.initial_edges)


def _run_one(nodes, truth, initial, action, target, allowed, policy_id, seed,
             schedule_seed):
    return refine(node_ids=nodes, initial_edges=initial, reference_edges=truth,
                  allowed_types=allowed, policy_id=policy_id, budget=BUDGET,
                  gamma=GAMMA, action=action, target=target, seed=seed,
                  schedule_seed=schedule_seed,
                  graph_id=graph_hash(nodes, initial))


def run():
    matrix = json.loads(gzip.decompress(SOURCE.read_bytes()))
    rows = [r for r in matrix["rows"] if r["accepted"]]
    pairs = []
    totals = defaultdict(Counter)
    group_totals = defaultdict(Counter)
    for row in rows:
        nodes, truth, _, _, streams = _reconstruct(row)
        task = (row["action"], row["target"])
        initial = _initial_for_row(row, nodes, truth, task, streams)
        for mode, allowed in POLICIES:
            policy_id = f"{mode}-" + "-".join(allowed)
            policy = _run_one(nodes, truth, initial, *task, allowed, policy_id,
                              seed=0, schedule_seed=0)
            for random_seed in RANDOM_SEEDS:
                random = _run_one(nodes, truth, initial, *task, allowed, "RANDOM",
                                  seed=random_seed, schedule_seed=0)
                if policy["type_schedule"] != random["type_schedule"]:
                    raise AssertionError("matched policy/random type schedule diverged")
                same_graph = policy["final_hash"] == random["final_hash"]
                sequence_diff = policy["edit_sequence"] != random["edit_sequence"]
                policy_opp = operation_opportunities(nodes, truth, policy["final_graph"])
                random_opp = operation_opportunities(nodes, truth, random["final_graph"])
                policy_remaining = sum(policy_opp[k]["candidate_count"] for k in allowed)
                policy_remaining_valid = sum(policy_opp[k]["dag_valid_count"] for k in allowed)
                random_remaining = sum(random_opp[k]["candidate_count"] for k in allowed)
                random_remaining_valid = sum(random_opp[k]["dag_valid_count"] for k in allowed)
                unit = {"same_final_graph": same_graph,
                        "sequence_diff": sequence_diff,
                        "policy_spent": policy["spent_budget"],
                        "random_spent": random["spent_budget"],
                        "policy_remaining_allowed_candidates": policy_remaining,
                        "policy_remaining_allowed_dag_valid": policy_remaining_valid,
                        "random_remaining_allowed_candidates": random_remaining,
                        "random_remaining_allowed_dag_valid": random_remaining_valid,
                        "policy_termination": policy["termination_reason"],
                        "random_termination": random["termination_reason"]}
                key = (policy_id, "ALL")
                group = (policy_id, row["condition"], row["task_kind"], "-".join(allowed))
                for target, target_key in ((totals, key), (group_totals, group)):
                    c = target[target_key]
                    c["pairs"] += 1
                    c["same_final_graph"] += same_graph
                    c["sequence_diff"] += sequence_diff
                    c["policy_spent_total"] += policy["spent_budget"]
                    c["random_spent_total"] += random["spent_budget"]
                    c[f"policy_spent:{policy['spent_budget']}"] += 1
                    c[f"random_spent:{random['spent_budget']}"] += 1
                    c["policy_budget_exhausted_with_dag_valid_candidate"] += (
                        policy["spent_budget"] == BUDGET and unit["policy_remaining_allowed_dag_valid"] > 0)
                    c["random_budget_exhausted_with_dag_valid_candidate"] += (
                        random["spent_budget"] == BUDGET and unit["random_remaining_allowed_dag_valid"] > 0)
                    c["policy_remaining_allowed_candidates_total"] += unit["policy_remaining_allowed_candidates"]
                    c["policy_remaining_allowed_dag_valid_total"] += unit["policy_remaining_allowed_dag_valid"]
                    c["random_remaining_allowed_candidates_total"] += unit["random_remaining_allowed_candidates"]
                    c["random_remaining_allowed_dag_valid_total"] += unit["random_remaining_allowed_dag_valid"]
                pairs.append({"n": row["n"], "template": row["template"], "seed": row["seed"],
                              "task_kind": row["task_kind"], "condition": row["condition"],
                              "requested_error_type": row["requested_error_type"],
                              "initial_hash": row["initial_hash"], "policy_id": policy_id,
                              "allowed_types": allowed, "random_seed": random_seed,
                              "type_schedule": policy["type_schedule"], **unit})
    return {"protocol": "STEP4B3_P_B4_MATCHED_RANDOM_STRUCTURE_AUDIT_V1",
            "settings": SETTINGS, "settings_sha256": SETTINGS_SHA256,
            "source_matrix_sha256": sha256(SOURCE.read_bytes()).hexdigest(),
            "accepted_initial_graph_rows": len(rows),
            "planned_pairs": len(rows) * len(POLICIES) * len(RANDOM_SEEDS),
            "actual_pairs": len(pairs),
            "summary_by_policy": {k[0]: dict(v) for k, v in sorted(totals.items())},
            "summary_by_condition_task_type": {"|".join(k): dict(v)
                                               for k, v in sorted(group_totals.items())},
            "pairs": pairs}


def main():
    result = run()
    payload = json.dumps(result, sort_keys=True, separators=(",", ":"),
                         default=list).encode("utf-8")
    OUTPUT.write_bytes(gzip.compress(payload, compresslevel=9, mtime=0))
    print(json.dumps({"settings_sha256": result["settings_sha256"],
                      "planned_pairs": result["planned_pairs"],
                      "actual_pairs": result["actual_pairs"],
                      "output": OUTPUT.name}, indent=2))


if __name__ == "__main__":
    main()

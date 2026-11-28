"""Outcome-neutral aggregation of already locked Development Pilot artifacts."""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

from research.external_validation.semisynthetic_evaluation.pipeline import (
    canonical_json, file_sha256, sha256_bytes,
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--recommendations", type=Path, required=True)
    parser.add_argument("--evaluation", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists(): raise FileExistsError("refusing to overwrite pilot diagnostics")
    rec = json.loads(args.recommendations.read_text(encoding="utf-8"))
    ev = json.loads(args.evaluation.read_text(encoding="utf-8"))
    if rec["content_sha256"] != ev["recommendation_lock_sha256"]:
        raise ValueError("evaluation is not bound to this recommendation manifest")
    rec_map = {(r["g0_seed_id"], r["budget"], r["policy_id"]): r for r in rec["recommendations"]}
    ev_map = {(r["g0_seed_id"], r["budget"], r["policy_id"]): r for r in ev["evaluation_rows"]}
    if set(rec_map) != set(ev_map): raise ValueError("recommendation/evaluation row keys differ")
    policies = sorted({key[2] for key in rec_map})
    budgets = sorted({key[1] for key in rec_map})
    seeds = sorted({key[0] for key in rec_map})
    rows, graph_duplicates = [], []
    for budget in budgets:
        s0_actions = {seed: rec_map[(seed, budget, "S0")]["recommended_action"] for seed in seeds}
        graphs = [rec_map[(seed, budget, policy)]["repaired_graph_sha256"] for seed in seeds for policy in policies]
        graph_duplicates.append({"budget": budget, "policy_rows": len(graphs),
            "unique_final_graphs": len(set(graphs)), "duplicate_excess": len(graphs)-len(set(graphs))})
        for policy in policies:
            items = [ev_map[(seed, budget, policy)] for seed in seeds]
            rec_items = [rec_map[(seed, budget, policy)] for seed in seeds]
            deltas = [ev_map[(seed, budget, policy)]["loss_bc"]-
                      ev_map[(seed, budget, "S0")]["loss_bc"] for seed in seeds]
            rows.append({"budget": budget, "policy_id": policy, "g0_n": len(seeds),
                "mean_loss_bc": sum(x["loss_bc"] for x in items)/len(items),
                "mean_loss_plugin": sum(x["loss_plugin"] for x in items)/len(items),
                "mean_repair_cost": sum(x["repair_cost"] for x in items)/len(items),
                "zero_cost_fraction": sum(x["repair_cost"] == 0 for x in items)/len(items),
                "mean_edit_count": sum(x["edit_count"] for x in rec_items)/len(rec_items),
                "same_action_fraction_vs_S0": sum(x["recommended_action"] == s0_actions[x["g0_seed_id"]]
                    for x in rec_items)/len(rec_items),
                "different_action_count_vs_S0": sum(x["recommended_action"] != s0_actions[x["g0_seed_id"]]
                    for x in rec_items),
                "positive_loss_delta_vs_S0_fraction": sum(x > 0 for x in deltas)/len(deltas),
                "negative_loss_delta_vs_S0_fraction": sum(x < 0 for x in deltas)/len(deltas),
                "tie_loss_delta_vs_S0_fraction": sum(x == 0 for x in deltas)/len(deltas)})
    body = {"schema": "RESEARCH_D_DEVELOPMENT_POLICY_DIAGNOSTICS_V1",
        "recommendation_lock_sha256": rec["content_sha256"],
        "evaluation_sha256_local_artifact": file_sha256(args.evaluation),
        "policy_budget_summary": rows, "unique_graph_summary_by_budget": graph_duplicates,
        "interpretation": "development-only; no policy selection or contract changes"}
    body["content_sha256"] = sha256_bytes(canonical_json(body))
    args.output.write_text(json.dumps(body, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "rows": len(rows), "content_sha256": body["content_sha256"]}))


if __name__ == "__main__":
    main()

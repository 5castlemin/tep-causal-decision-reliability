"""Finite outcome-blind proposal/Q rejection timing on deterministic fixtures."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import statistics
import time

from .step4c1_proposal import STRATA, _seed, build_structural_proposal, q_common_eligibility
from .step4_topology_generator import generate_topology

MASTER_SEED = 20261116
REPETITIONS = 3


def run() -> dict:
    rows = []
    for template, node_count in STRATA:
        proposal_id = f"resource-cost-{template}-n{node_count}"
        topology_seed = _seed("development", MASTER_SEED, proposal_id, template,
                              node_count, 0, "topology")
        topology_times, proposal_times, q_times = [], [], []
        proposal = None
        for _ in range(REPETITIONS):
            started = time.perf_counter()
            topology = generate_topology(node_count, template, topology_seed)
            topology_times.append(time.perf_counter() - started)
            started = time.perf_counter()
            proposal = build_structural_proposal(cohort="development", master_seed=MASTER_SEED,
                proposal_id=proposal_id, attempt=0, template=template, node_count=node_count)
            proposal_times.append(time.perf_counter() - started)
            if proposal.get("action") and proposal.get("target"):
                started = time.perf_counter()
                q = q_common_eligibility(proposal["nodes"], proposal["topology_edges"],
                                         proposal["action"], proposal["target"])
                q_times.append(time.perf_counter() - started)
                if q["eligible"] != proposal["accepted"]:
                    raise RuntimeError("proposal and independent Q-common recheck disagree")
        rows.append({"template": template, "node_count": node_count,
            "proposal_id": proposal_id, "proposal_repetitions_same_key": REPETITIONS,
            "topology_seed_sha256": hashlib.sha256(str(topology_seed).encode()).hexdigest(),
            "proposal_status": "accepted" if proposal["accepted"] else "rejected",
            "rejection_reason": proposal.get("reason"), "q_recipe_counts": proposal.get("q_recipe_counts", {}),
            "topology_only_median_seconds": statistics.median(topology_times),
            "full_proposal_median_seconds": statistics.median(proposal_times),
            "independent_q_check_median_seconds": statistics.median(q_times) if q_times else None,
            "coefficient_or_data_drawn": False, "study_scm": False})
    return {"schema_version": 1, "purpose": "fixed_outcome_blind_proposal_resource_microbenchmark",
        "master_seed": MASTER_SEED, "repetitions": REPETITIONS,
        "study_cohort_generated": False, "independent_scm_n": 0,
        "decision_regret_analysis": False, "rows": rows,
        "limitations": ["one fixed proposal key per stratum", "three timing repeats are not tail guarantees",
            "proposal keys are a separate resource fixture namespace", "no coefficient, noise, observation, effect, or regret was drawn"]}


def main() -> None:
    result = run()
    output = Path(__file__).with_name("step4c2_proposal_cost_benchmark_v1.json")
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"output": output.name, "proposals": len(result["rows"]),
        "accepted": sum(row["proposal_status"] == "accepted" for row in result["rows"]),
        "rejected": sum(row["proposal_status"] == "rejected" for row in result["rows"])}))


if __name__ == "__main__":
    main()

"""Fixed, topology-only Q-common yield audit across the 20 P strata.

It records every candidate attempt and does not generate SCM parameters,
observations, fitted models, effects, regret, or confirmation SCMs.
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
import gzip
import json
from pathlib import Path

from .step4_topology_generator import TEMPLATES, generate_topology
from .step4b_task_budget import graph_hash, relabel_roles, role_nodes, select_task_pair
from .step4b2_population import competition_recipes
from .step4_rng import RNGKey, RNG_PROTOCOL_VERSION, derive_seed, derive_streams
from .step4b4_design import clopper_pearson, minimum_attempt_cap

HERE = Path(__file__).parent
OUTPUT = HERE / "step4b4_q_yield_v1.json.gz"
MASTER_SEED = 20261115
NODE_COUNTS = tuple(range(6, 11))
ATTEMPTS_PER_STRATUM = 100
TARGETS = (64, 200)
KINDS = ("FN", "FP", "REV")
STRATA = tuple((template, n) for template in TEMPLATES for n in NODE_COUNTS)
SETTINGS = {
    "protocol": "STEP4B4_Q_COMMON_STRATIFIED_YIELD_AUDIT_V1",
    "rng_protocol_version": RNG_PROTOCOL_VERSION,
    "cohort": "development",
    "master_seed": MASTER_SEED,
    "templates": TEMPLATES,
    "node_counts": NODE_COUNTS,
    "p_stratum_probability": "1/20 for each template x node-count stratum",
    "attempts_per_stratum": ATTEMPTS_PER_STRATUM,
    "total_candidate_topology_attempts": len(STRATA) * ATTEMPTS_PER_STRATUM,
    "task": "one selected indirect-only task; common-cause scaffold X->Y preferred when eligible",
    "q_rule": "all FN/FP/REV each have at least one two-correction competition recipe under B=1; topology/task/error locations and DAG rules only",
    "retries": 0,
    "replacement": False,
    "outcomes_used": False,
    "coefficient_sampling": False,
    "observational_data": False,
}
SETTINGS_SHA256 = sha256(json.dumps(SETTINGS, sort_keys=True, separators=(",", ":"),
                                   default=list).encode()).hexdigest()


def _seed(cohort, master, scm_id, template, n, attempt, stream):
    return derive_seed(RNGKey(RNG_PROTOCOL_VERSION, cohort, master, scm_id,
                             template, n, attempt, stream))


def run():
    rows = []
    for template, n in STRATA:
        for attempt in range(ATTEMPTS_PER_STRATUM):
            scm_id = f"yield-v1-{template}-n{n}-candidate{attempt:04d}"
            streams = derive_streams(cohort="development", master_seed=MASTER_SEED,
                                     scm_id=scm_id, topology_template=template,
                                     node_count=n, topology_attempt=attempt)
            topology = generate_topology(n, template, streams["topology"])
            nodes, truth, roles, mapping = relabel_roles(
                template, topology.nodes, topology.edges, streams["node_relabeling"])
            scaffold_roles = role_nodes(template, topology.nodes)
            preferred = ((mapping[scaffold_roles["action"]], mapping[scaffold_roles["target"]])
                         if template == "observed_common_cause" else None)
            tasks = select_task_pair(nodes, truth, streams["task_selection"], preferred)
            indirect = next((pair for kind, pair in tasks["selected"] if kind == "indirect"), None)
            candidate_counts = {kind: 0 for kind in KINDS}
            if indirect is not None:
                action, target = indirect
                for kind in KINDS:
                    candidate_counts[kind] = len(competition_recipes(
                        nodes, truth, action, target, kind))
            else:
                action = target = None
            accepted = indirect is not None and all(candidate_counts[kind] > 0 for kind in KINDS)
            rows.append({
                "candidate_id": scm_id, "template": template, "node_count": n,
                "attempt": attempt, "accepted_q_common": accepted,
                "failure_reason": None if accepted else (
                    tasks["failures"].get("indirect", "missing_one_or_more_error_type_support")
                    if indirect is None or not all(candidate_counts[k] > 0 for k in KINDS)
                    else "unknown"),
                "topology_hash": graph_hash(nodes, truth),
                "role_map": roles, "id_mapping": mapping,
                "task_relation": "indirect_only" if indirect is not None else None,
                "action": action, "target": target,
                "candidate_recipe_counts": candidate_counts,
                "stream_seeds": streams,
                "coefficient_or_data_drawn": False,
            })

    strata_rows = []
    total_accepted = 0
    for template, n in STRATA:
        cell = [r for r in rows if r["template"] == template and r["node_count"] == n]
        accepted = sum(r["accepted_q_common"] for r in cell)
        total_accepted += accepted
        lo, hi = clopper_pearson(accepted, len(cell))
        strata_rows.append({"template": template, "node_count": n,
                            "candidate_attempts": len(cell), "q_common_accepted": accepted,
                            "acceptance_rate": accepted / len(cell),
                            "exact_95pct_interval": [lo, hi]})
    total_lo, total_hi = clopper_pearson(total_accepted, len(rows))
    attempt_plans = {}
    for target in TARGETS:
        for label, p in (("observed_rate", total_accepted / len(rows)),
                         ("exact_95pct_lower_bound", total_lo),
                         ("conservative_20pct_scenario", 0.20)):
            cap, yield_prob = minimum_attempt_cap(target, p, 0.95)
            attempt_plans[f"{target}|{label}"] = {
                "target_eligible": target, "acceptance_probability_assumption": p,
                "candidate_attempt_cap": cap,
                "conditional_probability_at_least_target": yield_prob,
            }
    q_type_accepts = {kind: sum(r["candidate_recipe_counts"][kind] > 0 for r in rows)
                      for kind in KINDS}
    return {
        "settings": SETTINGS, "settings_sha256": SETTINGS_SHA256,
        "planned_candidate_attempts": len(STRATA) * ATTEMPTS_PER_STRATUM,
        "actual_candidate_attempts": len(rows), "accepted_q_common": total_accepted,
        "acceptance_rate": total_accepted / len(rows),
        "exact_95pct_interval": [total_lo, total_hi],
        "q_support_by_type_candidate_attempts": q_type_accepts,
        "attempt_plan_conditional_binomial": attempt_plans,
        "strata": strata_rows, "rows": rows,
    }


def main():
    result = run()
    payload = json.dumps(result, sort_keys=True, separators=(",", ":"),
                         allow_nan=False).encode("utf-8")
    OUTPUT.write_bytes(gzip.compress(payload, compresslevel=9, mtime=0))
    print(json.dumps({"settings_sha256": result["settings_sha256"],
                      "planned": result["planned_candidate_attempts"],
                      "actual": result["actual_candidate_attempts"],
                      "accepted": result["accepted_q_common"],
                      "output": OUTPUT.name}, indent=2))


if __name__ == "__main__":
    main()

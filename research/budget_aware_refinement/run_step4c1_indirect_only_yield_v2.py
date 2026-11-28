"""Strict indirect-only rerun of the fixed Step 4B-4 2,000 topology audit.

Uses the original fixed strata, master seed, candidate IDs and RNG-key recipe;
only corrects task eligibility when a preferred scaffold pair has X->Y.
No SCM coefficients, observations, effects, or regret are generated.
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
import gzip
import json
from pathlib import Path

from .step4_topology_generator import TEMPLATES, generate_topology
from .step4b_task_budget import (classify_task_pairs, graph_hash, relabel_roles,
                                role_nodes, select_task_pair)
from .step4b2_population import competition_recipes
from .step4_rng import RNGKey, RNG_PROTOCOL_VERSION, derive_seed, derive_streams
from .step4b4_design import clopper_pearson, minimum_attempt_cap

HERE = Path(__file__).parent
OUTPUT = HERE / "step4c1_indirect_only_yield_v2.json.gz"
SUMMARY = HERE / "step4c1_indirect_only_yield_v2_summary.json"
MASTER_SEED = 20261115
ATTEMPTS_PER_STRATUM = 100
NODE_COUNTS = tuple(range(6, 11))
KINDS = ("FN", "FP", "REV")
STRATA = tuple((template, n) for template in TEMPLATES for n in NODE_COUNTS)
CAP_ALPHA = 0.025
TARGET_ATTAIN = 0.975
TARGETS = (64, 200)
SETTINGS = {
    "protocol": "STEP4C1_STRICT_INDIRECT_ONLY_YIELD_V2",
    "source_protocol": "STEP4B4_Q_COMMON_STRATIFIED_YIELD_AUDIT_V1",
    "master_seed": MASTER_SEED,
    "rng_protocol_version": RNG_PROTOCOL_VERSION,
    "stratum_design": "20 fixed template x node_count strata, 100 candidates each",
    "candidate_ids_and_topology_task_seed_derivation": "preserved from step4b4_q_yield_v1",
    "task_rule": "X->Y direct edge absent AND at least one directed path of length >=2; preferred common-cause scaffold only when it satisfies this rule",
    "q_rule": "all FN/FP/REV have same-type two-correction competition recipes under B=1; structural only",
    "outcomes_used": False,
    "coefficient_or_data_drawn": False,
    "caps": {"lower_interval_alpha": CAP_ALPHA, "conditional_attainment": TARGET_ATTAIN,
             "targets": TARGETS},
}
SETTINGS_SHA256 = sha256(json.dumps(SETTINGS, sort_keys=True, separators=(",", ":"),
                                  default=list).encode()).hexdigest()


def _seed(cohort, master, scm_id, template, n, attempt, stream):
    return derive_seed(RNGKey(RNG_PROTOCOL_VERSION, cohort, master, scm_id,
                             template, n, attempt, stream))


def run() -> dict:
    rows = []
    for template, n in STRATA:
        for attempt in range(ATTEMPTS_PER_STRATUM):
            candidate_id = f"yield-v1-{template}-n{n}-candidate{attempt:04d}"
            streams = derive_streams(cohort="development", master_seed=MASTER_SEED,
                                     scm_id=candidate_id, topology_template=template,
                                     node_count=n, topology_attempt=attempt)
            topology = generate_topology(n, template, streams["topology"])
            nodes, truth, roles, mapping = relabel_roles(
                template, topology.nodes, topology.edges, streams["node_relabeling"])
            scaffold = role_nodes(template, topology.nodes)
            preferred = ((mapping[scaffold["action"]], mapping[scaffold["target"]])
                         if template == "observed_common_cause" else None)
            classes = classify_task_pairs(nodes, truth)
            if preferred not in classes.indirect_only:
                preferred = None
            task_result = select_task_pair(nodes, truth, streams["task_selection"], preferred)
            task = next((pair for kind, pair in task_result["selected"] if kind == "indirect"), None)
            recipe_counts = {kind: 0 for kind in KINDS}
            accepted = False
            rejection = None
            if task is None:
                rejection = task_result["failures"].get("indirect", "no_indirect_only_task")
            else:
                action, target = task
                if (action, target) in truth or task not in classes.indirect_only:
                    rejection = "task_not_strictly_indirect_only"
                else:
                    recipe_counts = {kind: len(competition_recipes(nodes, truth, action, target, kind))
                                     for kind in KINDS}
                    accepted = all(recipe_counts[kind] > 0 for kind in KINDS)
                    if not accepted:
                        rejection = "missing_one_or_more_error_type_support"
            rows.append({
                "candidate_id": candidate_id, "template": template, "node_count": n,
                "attempt": attempt, "accepted_q_common_strict_indirect": accepted,
                "failure_reason": rejection, "topology_hash": graph_hash(nodes, truth),
                "truth_edges": [list(edge) for edge in sorted(truth)],
                "role_map": roles, "id_mapping": mapping,
                "task_class_counts": {"direct_only": len(classes.direct_only),
                                       "indirect_only": len(classes.indirect_only),
                                       "direct_and_indirect": len(classes.direct_and_indirect)},
                "action": task[0] if task else None, "target": task[1] if task else None,
                "selected_task_has_direct_edge": bool(task and task in truth),
                "candidate_recipe_counts": recipe_counts,
                "stream_seeds": streams, "coefficient_or_data_drawn": False,
            })
    strata = []
    for template, n in STRATA:
        cell = [row for row in rows if row["template"] == template and row["node_count"] == n]
        accepted = sum(row["accepted_q_common_strict_indirect"] for row in cell)
        lo, hi = clopper_pearson(accepted, len(cell))
        strata.append({"template": template, "node_count": n, "attempts": len(cell),
                       "accepted": accepted, "rate": accepted / len(cell),
                       "individual_cp95": [lo, hi]})
    accepted_total = sum(row["accepted_q_common_strict_indirect"] for row in rows)
    # Preserve the same stratified Bonferroni lower-bound and attainment rule as v2.
    per_stratum_alpha = CAP_ALPHA / len(STRATA)
    lower_bounds = [clopper_pearson(s["accepted"], s["attempts"], per_stratum_alpha)[0] for s in strata]
    cap_confidence = sum(lower_bounds) / len(lower_bounds)
    caps = {}
    for target in TARGETS:
        cap, probability = minimum_attempt_cap(target, cap_confidence, TARGET_ATTAIN)
        caps[str(target)] = {"candidate_cap": cap, "yield_lower_assumption": cap_confidence,
                             "conditional_probability_at_least_target": probability}
    old = json.loads(gzip.decompress((HERE / "step4b4_q_yield_v1.json.gz").read_bytes()))
    old_by_key = {(row["template"], row["node_count"], row["attempt"]): row for row in old["rows"]}
    def old_accepts(row):
        key = (row["template"], row["node_count"], row["attempt"])
        return bool(old_by_key[key]["accepted_q_common"])
    old_accepted = sum(old_accepts(row) for row in rows)
    changed = [row for row in rows if old_accepts(row) != row["accepted_q_common_strict_indirect"]]
    template_counts = {template: sum(row["accepted_q_common_strict_indirect"]
                                     and row["template"] == template for row in rows)
                       for template in TEMPLATES}
    return {
        "settings": SETTINGS, "settings_sha256": SETTINGS_SHA256,
        "source_v1_sha256": sha256((HERE / "step4b4_q_yield_v1.json.gz").read_bytes()).hexdigest(),
        "planned_attempts": len(rows), "actual_attempts": len(rows),
        "strict_indirect_accepted": accepted_total, "strict_indirect_yield": accepted_total / len(rows),
        "legacy_v1_accepted": old_accepted, "changed_acceptance_rows": len(changed),
        "legacy_v1_rejected_by_strict_rule": sum(not row["accepted_q_common_strict_indirect"] and old_accepts(row)
                                                  for row in rows),
        "accepted_with_direct_edge": sum(row["accepted_q_common_strict_indirect"] and row["selected_task_has_direct_edge"] for row in rows),
        "candidate_caps_same_rule": caps,
        "caps_362_1036_still_met": caps["64"]["candidate_cap"] <= 362 and caps["200"]["candidate_cap"] <= 1036,
        "strata": strata,
        "accepted_by_template": template_counts,
        "failures_by_reason": dict(Counter(row["failure_reason"] for row in rows if row["failure_reason"])),
        "rows": rows,
        "interpretation": "fixed topology-only yield diagnostic; no SCMs, coefficients, observations, effects or regret",
    }


def main():
    result = run()
    raw = json.dumps(result, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    compressed = gzip.compress(raw, compresslevel=9, mtime=0)
    OUTPUT.write_bytes(compressed)
    summary = {key: value for key, value in result.items() if key != "rows"}
    summary["raw_artifact_sha256"] = sha256(compressed).hexdigest()
    SUMMARY.write_text(json.dumps(summary, sort_keys=True, indent=2, allow_nan=False) + "\n",
                       encoding="utf-8")
    print(json.dumps({key: result[key] for key in (
        "settings_sha256", "actual_attempts", "strict_indirect_accepted", "strict_indirect_yield",
        "legacy_v1_accepted", "changed_acceptance_rows", "legacy_v1_rejected_by_strict_rule",
        "accepted_with_direct_edge", "candidate_caps_same_rule", "caps_362_1036_still_met")}, indent=2))


if __name__ == "__main__":
    main()

"""Run the finite, outcome-blind Step 4B-2 P/Q structural diagnostic."""
from __future__ import annotations

from collections import Counter, defaultdict
from hashlib import sha256
import gzip
import json
from pathlib import Path

from .policy_engine import refine
from .step4_error_injection import inject_condition
from .step4_topology_generator import TEMPLATES, generate_topology, is_dag
from .step4b_task_budget import (derive_stream_seeds, graph_hash, relabel_roles,
                                 select_task_pair, classify_task_pairs)
from .step4b2_population import (classify_error_location, competition_recipes,
                                 select_q_recipe, single_error_options)

HERE = Path(__file__).parent
SOURCE = HERE / "step4b_task_budget_feasibility_v4.json.gz"
OUTPUT = HERE / "step4b2_population_diagnostics_v1.json.gz"
SEEDS = (11, 12, 13, 14, 15)
NODE_COUNTS = tuple(range(6, 11))
BUDGETS = (0, 1, 2, 4, 6)
KINDS = ("FN", "FP", "REV")

SETTINGS = {
    "source_matrix": SOURCE.name,
    "seed_set": SEEDS,
    "node_counts": NODE_COUNTS,
    "templates": TEMPLATES,
    "population_P": "all fixed template x node-count x seed topologies; direct and indirect tasks separately; failures retained",
    "population_Q": "one outcome-blind recipe per topology-task-error-type cell; exactly two DAG-valid same-type corrections at distinct task/peripheral locations; path survives; budget 1; no replacements",
    "error_locations": ("gt_action_target_path", "upstream_of_action",
                        "target_adjacent_off_path", "action_adjacent_off_path",
                        "off_path_peripheral"),
    "q_budget_grid": BUDGETS,
    "q_gamma": 1,
    "q_recipe_seed": "SHA256 domain-separated from topology/relabel/task/error/policy streams",
    "legacy_topology_stream_scope": "B1 streams are keyed by seed only; cross-template/node-count mapping reuse is measured and documented, not silently corrected in this historical-source diagnostic",
    "outcomes_used_for_selection": False,
    "regret_or_effects_used": False,
}
SETTINGS_SHA256 = sha256(json.dumps(SETTINGS, sort_keys=True, separators=(",", ":"), default=list).encode()).hexdigest()


def _task_rows(matrix):
    result = {}
    for row in matrix["rows"]:
        if "action" not in row:
            continue
        key = (row["n"], row["template"], row["seed"], row["task_kind"])
        result.setdefault(key, row)
    return list(result.values())


def _reconstruct(row):
    streams = derive_stream_seeds(row["seed"])
    base = generate_topology(row["n"], row["template"], streams["topology"])
    nodes, truth, roles, mapping = relabel_roles(row["template"], base.nodes, base.edges,
                                                streams["relabel"])
    selected = select_task_pair(nodes, truth, streams["task"],
                                (roles["action"], roles["target"])
                                if row["template"] == "observed_common_cause" else None)
    task = dict(selected["selected"]).get(row["task_kind"])
    if task != (row["action"], row["target"]):
        raise AssertionError("task reconstruction differs from raw matrix")
    if graph_hash(nodes, truth) != row["truth_hash"]:
        raise AssertionError("truth graph reconstruction differs from raw matrix")
    return nodes, set(truth), roles, mapping, streams


def _b_eligibility(options, action, target):
    eligible = {kind: [] for kind in KINDS}
    for kind in KINDS:
        for option in options[kind]:
            if not option["path_survives"]:
                continue
            tags = option["locations"][0]["tags"]
            if kind in ("FN", "REV"):
                valid = "gt_action_target_path" in tags
            else:
                valid = action in option["operation"][1:] or target in option["operation"][1:]
            if valid:
                eligible[kind].append(option)
    return eligible


def _serialize_q(row, nodes, truth, task, kind, selected, streams):
    action, target = task
    initial = selected["initial_edges"]
    if not is_dag(nodes, initial):
        raise AssertionError("Q initial graph is not a DAG")
    candidate_counts = {"FN": 0, "FP": 0, "REV": 0}
    candidate_counts[kind] = selected["candidate_count"]
    if selected["candidate_count"] < 2 or selected["minimum_full_repair_cost"] <= 1:
        raise AssertionError("Q recipe does not enforce a one-unit budget limit")
    policy_runs = []
    for budget in BUDGETS:
        paired = {}
        for mode in ("G", "T"):
            policy_id = f"{mode}-{kind}"
            log = refine(node_ids=nodes, initial_edges=initial, reference_edges=truth,
                         allowed_types=(kind,), policy_id=policy_id, budget=budget,
                         gamma=1, action=action, target=target,
                         seed=streams["policy_schedule"], graph_id=graph_hash(nodes, initial))
            paired[mode] = log
        policy_runs.append({"budget": budget,
                            "initial_candidate_count": selected["candidate_count"],
                            "global_edits": paired["G"]["edit_sequence"],
                            "task_focused_edits": paired["T"]["edit_sequence"],
                            "global_spent": paired["G"]["spent_budget"],
                            "task_focused_spent": paired["T"]["spent_budget"],
                            "sequence_diff": paired["G"]["edit_sequence"] != paired["T"]["edit_sequence"],
                            "final_graph_diff": paired["G"]["final_hash"] != paired["T"]["final_hash"],
                            "global_final_hash": paired["G"]["final_hash"],
                            "task_focused_final_hash": paired["T"]["final_hash"],
                            "global_cycle_rejections": sum(r["reason"] == "cycle" for r in paired["G"]["rejected_operations"]),
                            "task_focused_cycle_rejections": sum(r["reason"] == "cycle" for r in paired["T"]["rejected_operations"])})
    return {"n": row["n"], "template": row["template"], "seed": row["seed"],
            "task_kind": row["task_kind"], "action": action, "target": target,
            "error_type": kind, "accepted": True, "reason": "eligible_two_candidate_competition",
            "initial_hash": graph_hash(nodes, initial), "truth_hash": graph_hash(nodes, truth),
            "errors": selected["errors"], "locations": selected["locations"],
            "path_survives": selected["path_survives"],
            "candidate_count": selected["candidate_count"],
            "global_order": selected["candidate_orders"]["global"],
            "task_focused_order": selected["candidate_orders"]["task_focused"],
            "rank_diverges": selected["rank_diverges"],
            "rng_seeds": streams, "budget_runs": policy_runs}


def run():
    matrix = json.loads(gzip.decompress(SOURCE.read_bytes()))
    task_rows = _task_rows(matrix)
    b_type_by_cell = {(r["n"], r["template"], r["seed"], r["task_kind"]): r["requested_error_type"]
                      for r in matrix["rows"]
                      if r["condition"] == "B_path_survives" and r["accepted"]}
    b_budget = defaultdict(Counter)
    b_execution_count = Counter()
    for execution in matrix["executions"]:
        if execution["condition"] != "B_path_survives":
            continue
        key = (execution["n"], execution["template"], execution["seed"], execution["task_kind"])
        kind = b_type_by_cell.get(key)
        if kind is None:
            continue
        cell = b_budget[(kind, execution["budget"])]
        cell["runs"] += 1
        cell["spent"] += execution["spent"]
        cell["fully_spent"] += execution["spent"] == execution["budget"]
        cell["edits"] += execution["edit_count"]
        cell["unused"] += execution["unused"]
        cell["cycle_rejections"] += execution["cycle_rejections"]
        cell[f"termination:{execution['termination_reason']}"] += 1
        b_execution_count[kind] += 1
    c_reference = {(r["n"], r["template"], r["seed"], r["task_kind"]): r
                   for r in matrix["rows"] if r["condition"] == "C_mixed"}
    p_rows, q_rows, q_runs = [], [], []
    b_counts = Counter()
    h1_common = Counter()
    location_counts = Counter()
    c_path = Counter()
    c_cross = Counter()
    c_error_locations = Counter()
    q_planned_by_kind = Counter()
    q_failure_by_kind = Counter()
    q_candidates_by_kind = Counter()
    q_accept_by_kind = Counter()
    q_selected_unique = defaultdict(set)
    p_topology_hashes = set()

    for row in task_rows:
        nodes, truth, roles, mapping, streams = _reconstruct(row)
        task = (row["action"], row["target"])
        p_topology_hashes.add(row["truth_hash"])
        task_relation = row["task_relation"]
        options = single_error_options(nodes, truth, *task)
        eligible = _b_eligibility(options, *task)
        common = all(eligible[kind] for kind in KINDS)
        h1_common[(row["task_kind"], task_relation, common)] += 1
        summary = {kind: {"candidate_count": len(options[kind]),
                          "path_surviving_task_site_count": len(eligible[kind]),
                          "path_surviving_unique_initials": len({graph_hash(nodes, x["initial_edges"]) for x in eligible[kind]})}
                   for kind in KINDS}
        for kind in KINDS:
            b_counts[(kind, row["task_kind"], bool(eligible[kind]))] += 1
            for option in options[kind]:
                for loc in option["locations"]:
                    for tag in loc["tags"]:
                        location_counts[(kind, tag)] += 1

        c_result = inject_condition(nodes, truth, *task, "C_mixed", seed=streams["error_injection"])
        ref_c = c_reference[(row["n"], row["template"], row["seed"], row["task_kind"])]
        if (c_result.accepted != ref_c["accepted"] or
                (c_result.accepted and bool(c_result.remaining_paths) != ref_c["path_survives"])):
            raise AssertionError("C reinjection differs from the preserved v4 matrix")
        if c_result.accepted:
            c_path[c_result.remaining_paths != ()] += 1
            c_cross[(row["n"], row["template"], row["task_kind"], bool(c_result.remaining_paths))] += 1
            for item in classify_error_location(nodes, truth, *task, c_result.errors):
                for tag in item["tags"]:
                    c_error_locations[(item["error"][0], tag)] += 1
        p_rows.append({"n": row["n"], "template": row["template"], "seed": row["seed"],
                       "task_kind": row["task_kind"], "task_relation": task_relation,
                       "action": task[0], "target": task[1], "role_map": roles,
                       "id_mapping": mapping, "truth_hash": row["truth_hash"],
                       "truth_dag": is_dag(nodes, truth), "b_style_single_error_options": summary,
                       "h1_common_path_survival_support": common,
                       "c_accepted": c_result.accepted,
                       "c_path_survives": bool(c_result.remaining_paths) if c_result.accepted else None,
                       "c_errors": c_result.errors if c_result.accepted else (),
                       "c_error_location_tags": classify_error_location(nodes, truth, *task, c_result.errors) if c_result.accepted else (),
                       "h1_common_support": common})

        for kind in KINDS:
            q_planned_by_kind[kind] += 1
            recipes = competition_recipes(nodes, truth, *task, kind)
            q_candidates_by_kind[kind] += len(recipes)
            selected = select_q_recipe(recipes, f"{row['n']}:{row['template']}:{row['seed']}:{row['task_kind']}:{kind}")
            if selected is None:
                q_failure_by_kind[kind] += 1
                q_rows.append({"n": row["n"], "template": row["template"], "seed": row["seed"],
                               "task_kind": row["task_kind"], "error_type": kind,
                               "accepted": False, "reason": "no_two_same_type_related_peripheral_dag_valid_candidates"})
                continue
            q_accept_by_kind[kind] += 1
            serialized = _serialize_q(row, nodes, truth, task, kind, selected, streams)
            q_selected_unique[kind].add(serialized["initial_hash"])
            q_runs.extend({"n": row["n"], "template": row["template"], "seed": row["seed"],
                           "task_kind": row["task_kind"], "error_type": kind, **run}
                          for run in serialized["budget_runs"])
            q_rows.append({**serialized, "feasible_recipe_count": len(recipes),
                           "eligible_recipe_count_is_not_population_n": True})

    q_by_stratum = defaultdict(Counter)
    for item in q_rows:
        q_by_stratum[(item["n"], item["template"], item["error_type"])]["planned"] += 1
        q_by_stratum[(item["n"], item["template"], item["error_type"])]["accepted"] += bool(item["accepted"])
    q_budget_summary = {}
    for budget in BUDGETS:
        items = [x for x in q_runs if x["budget"] == budget]
        q_budget_summary[str(budget)] = {
            "paired_policy_runs": len(items),
            "rank_divergent_cohort_cells": sum(bool(next(r for r in q_rows if r.get("accepted") and
                                                   (r["n"], r["template"], r["seed"], r["task_kind"], r["error_type"]) ==
                                                   (x["n"], x["template"], x["seed"], x["task_kind"], x["error_type"]))["rank_diverges"]) for x in items),
            "sequence_diff": sum(x["sequence_diff"] for x in items),
            "final_graph_diff": sum(x["final_graph_diff"] for x in items),
            "global_total_spent": sum(x["global_spent"] for x in items),
            "task_focused_total_spent": sum(x["task_focused_spent"] for x in items),
            "unique_initial_graphs": len({next(r["initial_hash"] for r in q_rows if r.get("accepted") and
                                         (r["n"], r["template"], r["seed"], r["task_kind"], r["error_type"]) ==
                                         (x["n"], x["template"], x["seed"], x["task_kind"], x["error_type"])) for x in items})}
    topology_rows = {(r["n"], r["template"], r["seed"]): r for r in p_rows}
    action_ids = {template: Counter(r["role_map"]["action"] for (n, t, seed), r in topology_rows.items()
                                   if t == template) for template in TEMPLATES}
    mapping_pairs = mapping_equal_pairs = 0
    for n in NODE_COUNTS:
        for seed in SEEDS:
            group = [topology_rows[(n, template, seed)] for template in TEMPLATES]
            for i, left in enumerate(group):
                for right in group[i + 1:]:
                    mapping_pairs += 1
                    mapping_equal_pairs += left["id_mapping"] == right["id_mapping"]
    summary = {
        "population_P": {"topologies": len(p_topology_hashes), "tasks": len(p_rows),
                         "task_counts": dict(Counter(r["task_kind"] for r in p_rows)),
                         "task_relation_counts": dict(Counter(r["task_relation"] for r in p_rows)),
                         "h1_common_support_tasks": sum(r["h1_common_path_survival_support"] for r in p_rows),
                         "h1_common_support_by_template": {t: sum(r["h1_common_path_survival_support"] for r in p_rows if r["template"] == t) for t in TEMPLATES},
                         "h1_b_type_cells": {kind: {"planned": sum(v for (k, task, ok), v in b_counts.items() if k == kind),
                                                    "eligible_tasks": sum(v for (k, task, ok), v in b_counts.items() if k == kind and ok),
                                                    "eligible_direct": sum(v for (k, task, ok), v in b_counts.items() if k == kind and task == "direct" and ok),
                                                    "eligible_indirect": sum(v for (k, task, ok), v in b_counts.items() if k == kind and task == "indirect" and ok)} for kind in KINDS},
                         "b_type_location_tag_counts": {f"{kind}:{tag}": n for (kind, tag), n in location_counts.items()},
                         "c_path_survival": {str(k):v for k,v in c_path.items()},
                         "c_by_n_template_task_path": [{"n":k[0],"template":k[1],"task":k[2],"path_survives":k[3],"count":v} for k,v in sorted(c_cross.items())],
                         "c_error_location_tag_counts": {f"{kind}:{tag}": n for (kind, tag), n in c_error_locations.items()},
                         "B_execution_by_type_budget": {f"{kind}:{budget}": dict(counts) for (kind, budget), counts in sorted(b_budget.items())},
                         "B_execution_count_by_type": dict(b_execution_count),
                         "role_action_id_counts_by_template": {t: dict(sorted(c.items())) for t, c in action_ids.items()},
                         "same_seed_same_nodecount_relabel_mapping_equal_pairs": mapping_equal_pairs,
                         "same_seed_same_nodecount_relabel_mapping_pair_count": mapping_pairs},
        "population_Q": {"planned_cells_by_type": dict(q_planned_by_kind),
                         "accepted_cells_by_type": dict(q_accept_by_kind),
                         "failed_cells_by_type": dict(q_failure_by_kind),
                         "eligible_recipe_count_by_type": dict(q_candidates_by_kind),
                         "selected_unique_initials_by_type": {k:len(v) for k,v in q_selected_unique.items()},
                         "rank_divergent_selected_cells_by_type": {k:sum(r.get("accepted",False) and r["rank_diverges"] for r in q_rows if r["error_type"]==k) for k in KINDS},
                         "final_graph_diff_by_type_budget": {f"{k}:{b}": sum(x["error_type"]==k and x["budget"]==b and x["final_graph_diff"] for x in q_runs) for k in KINDS for b in BUDGETS},
                         "by_n_template_type": [{"n":k[0],"template":k[1],"error_type":k[2],**dict(v)} for k,v in sorted(q_by_stratum.items())],
                         "budget_summary":q_budget_summary},
        "h1_h2_contract_recommendation": {
            "primary_policy_effectiveness": "P; selected development policy vs matched random, with Path-F1 as separate additional-information oracle comparison; SCM-level paired estimand",
            "H1": "conditional/type-location exploratory or stratified contrasts on prespecified common-support task/topology cells; do not infer pooled type superiority from selected successful B cells",
            "H2_P": "report the population-average same-allowed-type Global vs Task-Focused paired contrast in P; likely diluted when structural choices coincide",
            "H2_Q": "separate conditional estimand on outcome-blind two-candidate competition cohort; not mixed into P without prespecified target weights",
            "independence": "topology/SCM is the independent unit; tasks, conditions, error-type versions, Q recipes, and policy runs are repeated within topology",
            "weights": "candidate equal weights across 20 template x node-count strata, then equal topology seeds and the two declared task slots; Q conditional support rates must be reported and P/Q remain separate",
            "status": "recommendation only; sample size, inference, failure, and resource contracts are not frozen"},
        "rows":p_rows,"q_rows":q_rows,"q_policy_runs":q_runs}
    return {"protocol":"STEP4B2_STRUCTURE_ONLY_PQ_H1_H2_DIAGNOSTIC_V1",
            "settings":SETTINGS,"settings_sha256":SETTINGS_SHA256,
            "source_matrix_sha256":sha256(SOURCE.read_bytes()).hexdigest(),
            "planned_P_task_cells":len(p_rows),"planned_Q_cells":len(q_rows),
            "summary":summary}


def main():
    result = run()
    payload = json.dumps(result, separators=(",", ":"), sort_keys=True, default=list).encode("utf-8")
    OUTPUT.write_bytes(gzip.compress(payload, compresslevel=9, mtime=0))
    print(json.dumps({"settings_sha256":result["settings_sha256"],
                      "source_matrix_sha256":result["source_matrix_sha256"],
                      "planned_P_task_cells":result["planned_P_task_cells"],
                      "planned_Q_cells":result["planned_Q_cells"],
                      "P":result["summary"]["population_P"],
                      "Q":{k:v for k,v in result["summary"]["population_Q"].items() if k not in ("by_n_template_type",)},
                      "output":OUTPUT.name},indent=2,default=list))


if __name__ == "__main__":
    main()

"""Deterministic topology/G0 feasibility pilot; never creates SCM outcomes."""
from __future__ import annotations

from collections import Counter, defaultdict
from hashlib import sha256
from itertools import combinations
import json
import random

from research.budget_aware_refinement.step4_topology_generator import (
    TEMPLATES, generate_topology,
)
from . import policy_engine as pe
from .g0_candidate import corrupt_graph_candidate


def _seed(master: int, *parts) -> int:
    raw = json.dumps([master, *parts], ensure_ascii=True, separators=(",", ":")).encode()
    return int.from_bytes(sha256(raw).digest()[:4], "big")


def run_structural_pilot(*, replicates_per_stratum=25,
                         topology_master_seed=20261123,
                         task_master_seed=20261124,
                         g0_master_seed=81420623,
                         true_corruption_rate=0.15,
                         false_adjacency_rate=0.05) -> dict:
    """Run fixed design over 4 templates × 5 sizes × replicates.

    All outputs are graph-only diagnostics. No SCM coefficients, observations,
    fitted responses, intervention losses or regret are generated.
    """
    if type(replicates_per_stratum) is not int or replicates_per_stratum < 1:
        raise ValueError("replicates_per_stratum must be a positive integer")
    strata = [(template, n) for template in TEMPLATES for n in range(6, 11)]
    totals = Counter()
    template_totals = defaultdict(Counter)
    records = []
    cfg = pe.Config()
    for template, n_nodes in strata:
        for replicate in range(replicates_per_stratum):
            topology_seed = _seed(topology_master_seed, "topology", template, n_nodes, replicate)
            topology = generate_topology(n_nodes, template, topology_seed)
            key = f"{template}|n={n_nodes}|rep={replicate:03d}"
            edge_count = len(topology.edges)
            pair_count = n_nodes * (n_nodes - 1) // 2
            totals["topologies"] += 1
            totals["edges"] += edge_count
            totals["nonadjacent_pairs"] += pair_count - edge_count
            template_totals[template]["cases"] += 1
            template_totals[template]["true_edges"] += edge_count
            template_totals[template]["nonadjacent_pairs"] += pair_count - edge_count
            strict_tasks = [task for task in topology.tasks if task.kind == "indirect"
                            and (task.action, task.target) not in topology.edges]
            if not strict_tasks:
                totals["task_rejected_no_strict_indirect_pair"] += 1
                template_totals[template]["task_rejected_no_strict_indirect_pair"] += 1
                records.append({"case_id": key, "template": template, "node_count": n_nodes,
                                "replicate": replicate, "topology_seed": topology_seed,
                                "task_seed": None, "g0_master_seed": g0_master_seed,
                                "task_status": "REJECTED_NO_STRICT_INDIRECT_PAIR",
                                "true_edge_count": edge_count,
                                "nonadjacent_pair_count": pair_count-edge_count,
                                "g0_status": "NOT_GENERATED", "policy_runs": []})
                continue
            totals["task_eligible"] += 1
            template_totals[template]["task_eligible"] += 1
            task_seed = _seed(task_master_seed, "strict-indirect-task", topology_seed,
                              [(x.action, x.target) for x in sorted(strict_tasks,
                                                                   key=lambda x: (x.action, x.target))])
            task_rng = random.Random(task_seed)
            task = strict_tasks[task_rng.randrange(len(strict_tasks))]
            truth = pe.state(sorted(topology.edges))
            g0 = corrupt_graph_candidate(
                truth, nodes=topology.nodes, action=task.action, target=task.target,
                master_seed=g0_master_seed,
                task_id=f"{template}|n={n_nodes}|rep={replicate}|topology={topology_seed}",
                true_corruption_rate=true_corruption_rate,
                false_adjacency_rate=false_adjacency_rate)
            estimate = pe.state(g0["initial_graph"]["edges"],
                                unresolved=g0["initial_graph"]["unresolved"])
            totals["g0_eligible"] += 1
            template_totals[template]["g0_eligible"] += 1
            opportunities = g0["event_opportunities_by_metric_kind_and_zone"]
            realized = g0["realized_error_counts_by_metric"]
            proposed_by_type_zone = Counter()
            accepted_by_type_zone = Counter()
            rejected_by_type_zone = Counter()
            for event in g0["attempted_events"]:
                zone = "task_zone" if event["task_zone"] else "off_task"
                target_counter = (accepted_by_type_zone if event["acceptance_status"] == "accepted"
                                  else rejected_by_type_zone)
                target_counter[(event["kind"], zone)] += 1
                proposed_by_type_zone[(event["kind"], zone)] += 1

            all_candidates = pe.candidates(truth, estimate, task.action, task.target, cfg)
            initial_stats = pe.metrics(truth, estimate, task.action, task.target, cfg)
            policy_rows = []
            for budget in range(5):
                run_hashes = []
                for subset in pe.catalog():
                    result = pe.run(truth, estimate, task.action, task.target, budget, subset, cfg)
                    eligible = [e for e in all_candidates if e.metric in subset]
                    feasible_single = []
                    for edit in eligible:
                        cost = dict(cfg.costs)[edit.operation]
                        trial = pe.apply(estimate, edit)
                        if cost <= budget and pe.dag(trial):
                            before = pe.burden(initial_stats, initial_stats, subset, cfg)
                            after_stats = pe.metrics(truth, trial, task.action, task.target, cfg)
                            gain = before - pe.burden(after_stats, initial_stats, subset, cfg)
                            if gain > 1e-12:
                                feasible_single.append(edit)
                    applied_keys = {(log["metric"], tuple(log["pair"]), log["operation"])
                                    for log in result["edits"]}
                    final_state = pe.state(result["final_edges"], unresolved=result["final_unresolved"])
                    remaining_candidates = [e for e in eligible if e.key not in applied_keys
                                            and final_state.get(e.pair) != e.replacement]
                    dag_valid_remaining = [e for e in remaining_candidates
                                           if pe.dag(pe.apply(final_state, e))]
                    affordable_remaining = [e for e in dag_valid_remaining
                                            if dict(cfg.costs)[e.operation]
                                            <= budget - result["total_cost"] + 1e-12]
                    if result["total_cost"] >= budget - 1e-12:
                        stop_group = "budget_exhausted"
                    elif not remaining_candidates:
                        stop_group = "candidate_pool_exhausted"
                    elif not dag_valid_remaining:
                        stop_group = "all_remaining_candidates_dag_invalid"
                    elif not affordable_remaining:
                        stop_group = "remaining_candidates_unaffordable"
                    else:
                        stop_group = result["stop_reason"]
                    policy_rows.append({
                        "policy_id": result["policy_id"], "budget": budget,
                        "candidate_count_by_metric": {m: sum(e.metric == m for e in eligible)
                                                       for m in pe.METRICS},
                        "single_edit_feasible_count": len(feasible_single),
                        "competing_candidates_ge2": len(feasible_single) >= 2,
                        "selected_count_by_metric": {m: sum(e["metric"] == m for e in result["edits"])
                                                     for m in pe.METRICS},
                        "final_graph_sha256": result["final_hash"],
                        "unique_initial_to_final_graph": result["final_hash"] != result["initial_hash"],
                        "total_edit_cost": result["total_cost"],
                        "unused_budget": result["unused_budget"],
                        "stop_reason": result["stop_reason"], "stop_group": stop_group,
                        "dag_rejects": result["dag_rejects"]})
                    run_hashes.append(result["final_hash"])
                unique_count = len(set(run_hashes))
                totals["policy_budget_cells"] += len(policy_rows[-len(pe.catalog()):])
                totals["policy_graph_pair_count"] += len(list(combinations(run_hashes, 2)))
                totals["same_graph_policy_pairs"] += sum(a == b for a, b in combinations(run_hashes, 2))
                totals[f"budget_{budget}_unique_graph_sum"] += unique_count
                totals[f"budget_{budget}_cases"] += 1
                totals[f"budget_{budget}_budget_exhausted_cells"] += sum(
                    row["budget"] == budget and row["stop_group"] == "budget_exhausted"
                    for row in policy_rows[-len(pe.catalog()):])
                totals[f"budget_{budget}_candidate_stop_cells"] += sum(
                    row["budget"] == budget and row["stop_group"] == "candidate_pool_exhausted"
                    for row in policy_rows[-len(pe.catalog()):])
                totals[f"budget_{budget}_unaffordable_stop_cells"] += sum(
                    row["budget"] == budget and row["stop_group"] == "remaining_candidates_unaffordable"
                    for row in policy_rows[-len(pe.catalog()):])
                totals[f"budget_{budget}_competing_policy_cells"] += sum(
                    row["budget"] == budget and row["competing_candidates_ge2"]
                    for row in policy_rows[-len(pe.catalog()):])

            total_errors = sum(sum(counts.values()) for counts in realized.values())
            totals["zero_error_g0"] += total_errors == 0
            template_totals[template]["zero_error_g0_cases"] += total_errors == 0
            totals["dag_rejected_proposals"] += g0["summary"]["rejected_dag"]
            totals["proposed_events"] += g0["summary"]["proposed"]
            totals["accepted_events"] += g0["summary"]["accepted"]
            for metric in pe.METRICS:
                error_count = sum(realized[metric].values())
                totals[f"{metric}_active"] += error_count > 0
                totals[f"{metric}_events"] += error_count
                totals[f"{metric}_opportunities"] += sum(
                    sum(zones.values()) for zones in opportunities[metric].values())
                template_totals[template][f"{metric}_active_cases"] += error_count > 0
                template_totals[template][f"{metric}_events"] += error_count
            for kind, zone in proposed_by_type_zone:
                template_totals[template][f"proposed_{kind}_{zone}"] += proposed_by_type_zone[(kind, zone)]
            for kind, zone in accepted_by_type_zone:
                template_totals[template][f"accepted_{kind}_{zone}"] += accepted_by_type_zone[(kind, zone)]
            for kind, zone in rejected_by_type_zone:
                template_totals[template][f"rejected_{kind}_{zone}"] += rejected_by_type_zone[(kind, zone)]
            for kind in ("FN", "FP", "REV", "UNRES"):
                for zone in ("task_zone", "off_task"):
                    totals[f"proposed_{kind}_{zone}"] += proposed_by_type_zone[(kind, zone)]
                    totals[f"accepted_{kind}_{zone}"] += accepted_by_type_zone[(kind, zone)]
                    totals[f"rejected_{kind}_{zone}"] += rejected_by_type_zone[(kind, zone)]
                    totals[f"realized_{kind}_{zone}"] += g0["realized_error_counts_by_kind_and_zone"][kind][zone]
                    totals[f"opportunities_{kind}_{zone}"] += sum(
                        zones[zone] for metric_rows in opportunities.values()
                        for event_kind, zones in metric_rows.items() if event_kind == kind)
            record = {
                "case_id": key, "template": template, "node_count": n_nodes,
                "replicate": replicate, "topology_seed": topology_seed,
                "task_seed": task_seed, "g0_master_seed": g0_master_seed,
                "action": task.action, "target": task.target,
                "true_edge_count": edge_count, "nonadjacent_pair_count": pair_count-edge_count,
                "g0_status": g0["generation_status"], "error_event_count": total_errors,
                "opportunities": opportunities,
                "proposals": g0["summary"],
                "proposed_by_kind_zone": {f"{k}|{z}": v for (k, z), v in proposed_by_type_zone.items()},
                "accepted_by_kind_zone": {f"{k}|{z}": v for (k, z), v in accepted_by_type_zone.items()},
                "rejected_by_kind_zone": {f"{k}|{z}": v for (k, z), v in rejected_by_type_zone.items()},
                "realized_errors_by_metric": realized,
                "policy_runs": policy_rows,
                "unique_final_graphs_by_budget": {str(b): len({r["final_graph_sha256"] for r in policy_rows
                                                                  if r["budget"] == b}) for b in range(5)},
            }
            records.append(record)

    n_cases = totals["topologies"]
    eligible_cases = totals["g0_eligible"]
    summary = {"topology_proposals": n_cases, "task_eligible": totals["task_eligible"],
               "task_rejected_no_strict_indirect_pair": totals["task_rejected_no_strict_indirect_pair"],
               "g0_eligible_cases": eligible_cases,
               "template_case_counts": dict(Counter(r["template"] for r in records)),
               "mean_true_edges": totals["edges"] / n_cases,
               "mean_nonadjacent_pairs": totals["nonadjacent_pairs"] / n_cases,
               "zero_error_g0_count": totals["zero_error_g0"],
               "zero_error_g0_rate_among_task_eligible": (totals["zero_error_g0"] / eligible_cases
                                                            if eligible_cases else None),
               "proposal_count": totals["proposed_events"], "accepted_count": totals["accepted_events"],
               "dag_rejected_count": totals["dag_rejected_proposals"],
               "dag_rejection_rate_of_proposals": (totals["dag_rejected_proposals"] / totals["proposed_events"]
                                                    if totals["proposed_events"] else None),
               "metric_active_cases": {m: totals[f"{m}_active"] for m in pe.METRICS},
               "metric_event_counts": {m: totals[f"{m}_events"] for m in pe.METRICS},
               "metric_opportunity_counts": {m: totals[f"{m}_opportunities"] for m in pe.METRICS},
               "error_type_zone_counts": {kind: {zone: {
                   "opportunities": totals[f"opportunities_{kind}_{zone}"],
                   "proposed": totals[f"proposed_{kind}_{zone}"],
                   "accepted": totals[f"accepted_{kind}_{zone}"],
                   "dag_rejected": totals[f"rejected_{kind}_{zone}"],
                   "realized": totals[f"realized_{kind}_{zone}"],
               } for zone in ("task_zone", "off_task")} for kind in ("FN", "FP", "REV", "UNRES")},
               "policy_graph_pair_same_rate": totals["same_graph_policy_pairs"] / totals["policy_graph_pair_count"],
               "policy_graph_pair_same_count": totals["same_graph_policy_pairs"],
               "policy_graph_pair_count": totals["policy_graph_pair_count"],
               "budget_diagnostics": {str(b): {
                   "eligible_case_count": totals[f"budget_{b}_cases"],
                   "policy_budget_cells": totals[f"budget_{b}_cases"] * len(pe.catalog()),
                   "budget_exhausted_cells": totals[f"budget_{b}_budget_exhausted_cells"],
                   "candidate_stop_cells": totals[f"budget_{b}_candidate_stop_cells"],
                   "unaffordable_stop_cells": totals[f"budget_{b}_unaffordable_stop_cells"],
                   "competing_candidate_cells": totals[f"budget_{b}_competing_policy_cells"],
                   "mean_unique_final_graphs_per_eligible_case": (
                       totals[f"budget_{b}_unique_graph_sum"] / eligible_cases if eligible_cases else None),
               } for b in range(5)},
               "by_template": {k: {**dict(v),
                    "mean_true_edges": v["true_edges"] / v["cases"],
                    "mean_nonadjacent_pairs": v["nonadjacent_pairs"] / v["cases"],
                    "task_eligible": v["task_eligible"],
                    "task_rejected_no_strict_indirect_pair": v["task_rejected_no_strict_indirect_pair"],
                    "zero_error_g0_rate_among_task_eligible": (
                        v["zero_error_g0_cases"] / v["g0_eligible"] if v["g0_eligible"] else None),
                    "metric_active_rates_among_task_eligible": {
                        m: v[f"{m}_active_cases"] / v["g0_eligible"] if v["g0_eligible"] else None
                        for m in pe.METRICS}}
                    for k, v in template_totals.items()}}
    return {"status": "STRUCTURE_ONLY_FEASIBILITY_PILOT_NOT_REGRET_VALIDATION",
            "test_only": True, "research_cohort_generated": False,
            "study_regret_generated": False,
            "design": {"replicates_per_stratum": replicates_per_stratum,
                       "strata": [{"template": t, "node_count": n} for t, n in strata],
                       "topology_master_seed": topology_master_seed,
                       "task_master_seed": task_master_seed,
                       "g0_master_seed": g0_master_seed,
                       "true_corruption_rate": true_corruption_rate,
                       "false_adjacency_rate": false_adjacency_rate,
                       "true_error_mix": {"FN": 1/3, "REV": 1/3, "UNRES": 1/3},
                       "no_resampling_after_dag_rejection": True},
            "summary": summary, "cases": records}

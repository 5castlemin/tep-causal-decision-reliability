"""Outcome-blind structural checks for the Wind Tunnel design decision."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
from research.original_objective.policy_engine import state, task_zone, metrics, Config

INSPECTION = ROOT / "research" / "external_validation" / "inspection_results.json"


def qualify_graph(inspection: dict | None = None) -> dict:
    if inspection is None:
        inspection = json.loads(INSPECTION.read_text(encoding="utf-8"))
    source = inspection["mk1_graphs"]["wt_standard"]
    truth = state(source["edges"])
    nodes = set(source["nodes"])
    schema_experiment = "random_loads_intake"
    csv_variables = set(
        inspection["chamber"]["wt_bernoulli_v1"]["experiments"][schema_experiment]["dtypes"]
    )
    if len(nodes) != 32 or len(truth) != 42 or not source["dag"]:
        raise ValueError("Unexpected pinned Wind Tunnel standard graph")
    if {n for edge in truth.values() for n in edge} != nodes:
        raise ValueError("Graph node set does not match edge endpoints")
    pair_total = len(nodes) * (len(nodes) - 1) // 2
    absent = pair_total - len(truth)
    tasks = {}
    for target in ("rpm_in", "pressure_intake"):
        zone, zone_nodes = task_zone(truth, "load_in", target)
        tasks[target] = {
            "reference_direct_edge": truth.get(tuple(sorted(("load_in", target)))) == ("load_in", target),
            "zone_pairs": [list(p) for p in sorted(zone)],
            "zone_nodes": sorted(zone_nodes),
            "task_fp_opportunities_rule_a": sum(1 for a in zone_nodes for b in zone_nodes if a < b and tuple(sorted((a, b))) not in truth),
        }
    return {
        "nodes": len(nodes), "edges": len(truth), "unordered_pairs": pair_total,
        "reference_absent_pairs": absent, "oriented_absent_candidates": absent * 2,
        "dag": True, "tasks": tasks,
        "csv_schema_experiment": schema_experiment,
        "all_graph_nodes_in_csv_schema": nodes <= csv_variables,
        "csv_variables_outside_graph": sorted(csv_variables - nodes),
        "response_values_read": False,
    }


def fixture_checks() -> dict:
    """Test Research C M1-M4 coding on a tiny hand-built graph; no outcomes."""
    # This chain gives strict indirect task x -> z -> y for fixture-only engine checks.
    # Use a separate truth graph to expose all four metric families, including Rule A FP.
    truth = state([("x", "z"), ("z", "y"), ("x", "u"), ("u", "v")])
    task_zone_pairs, _ = task_zone(truth, "x", "y")
    base = dict(truth)
    # Hand edits: task FN, task REV, task UNRES, task FP within the task-node set;
    # off-task FN/REV/UNRES and Rule-A off-task FP.
    fn = dict(base); fn.pop(tuple(sorted(("x", "z"))))
    rev = dict(base); rev[tuple(sorted(("x", "z")))] = ("z", "x")
    unres = dict(base); unres[tuple(sorted(("x", "z")))] = "UNRES"
    off_fn = dict(base); off_fn.pop(tuple(sorted(("u", "v"))))
    off_rev = dict(base); off_rev[tuple(sorted(("u", "v")))] = ("v", "u")
    off_unres = dict(base); off_unres[tuple(sorted(("u", "v")))] = "UNRES"
    # x and y are task-zone nodes and have no reference edge in this fixture.
    task_fp = dict(base); task_fp[tuple(sorted(("x", "y")))] = ("x", "y")
    # u and y span zone/off-zone; Rule A deliberately assigns this to M2.
    off_fp = dict(base); off_fp[tuple(sorted(("u", "y")))] = ("u", "y")
    cases = {
        "task_fn": fn, "task_rev": rev, "task_unres": unres,
        "task_fp": task_fp, "off_fn": off_fn, "off_rev": off_rev,
        "off_unres": off_unres, "off_fp": off_fp,
    }
    out = {}
    for name, estimate in cases.items():
        result = metrics(truth, estimate, "x", "y", Config())
        out[name] = {m: dict(kinds) for m, kinds in result["counts"].items()}
    return {"task_zone_pairs": [list(p) for p in sorted(task_zone_pairs)], "cases": out}

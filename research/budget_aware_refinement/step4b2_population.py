"""Outcome-blind H1/H2 structure populations and error-location diagnostics."""
from __future__ import annotations

from collections import deque
from hashlib import sha256
from itertools import combinations
import random

from .step4_error_injection import classify_errors
from .step4_topology_generator import directed_paths, is_dag


def _route_dyads(nodes, truth, action, target):
    result = set()
    for path in directed_paths(nodes, truth, action, target):
        result.update(frozenset(edge) for edge in zip(path, path[1:]))
    return result


def _ancestor_path_dyads(nodes, edges, node):
    result = set()
    for source in nodes:
        if source == node:
            continue
        for path in directed_paths(nodes, edges, source, node):
            result.update(frozenset(edge) for edge in zip(path, path[1:]))
    return result


def classify_error_location(nodes, truth_edges, action, target, errors):
    """Return multi-tags; off-path is a broad tag, not a claim of harmlessness."""
    truth = set(truth_edges)
    route = _route_dyads(nodes, truth, action, target)
    upstream = _ancestor_path_dyads(nodes, truth, action)
    tags = []
    for kind, a, b in errors:
        dyad = frozenset((a, b))
        item = {"error": (kind, a, b), "tags": []}
        if dyad in route:
            item["tags"].append("gt_action_target_path")
        if dyad in upstream:
            item["tags"].append("upstream_of_action")
        if target in (a, b) and dyad not in route:
            item["tags"].append("target_adjacent_off_path")
        if action in (a, b) and dyad not in route and dyad not in upstream:
            item["tags"].append("action_adjacent_off_path")
        if dyad not in route:
            item["tags"].append("off_path_peripheral")
        tags.append(item)
    return tags


def single_error_options(nodes, truth_edges, action, target):
    """Enumerate one-error G0 options; retain DAG, route and location separately."""
    nodes = tuple(nodes)
    truth = set(truth_edges)
    output = {kind: [] for kind in ("FN", "FP", "REV")}
    for a, b in combinations(nodes, 2):
        true_edge = (a, b) if (a, b) in truth else (b, a) if (b, a) in truth else None
        if true_edge:
            candidates = (("FN", true_edge, truth - {true_edge}),
                          ("REV", (true_edge[1], true_edge[0]), truth - {true_edge} | {(true_edge[1], true_edge[0])}))
        else:
            candidates = (("FP", (a, b), truth | {(a, b)}),
                          ("FP", (b, a), truth | {(b, a)}))
        for kind, observed_error, initial in candidates:
            if not is_dag(nodes, initial):
                continue
            errors = classify_errors(nodes, truth, initial)
            path_survives = bool(directed_paths(nodes, initial, action, target))
            output[kind].append({"operation": (kind, *observed_error),
                                 "initial_edges": frozenset(initial),
                                 "path_survives": path_survives,
                                 "locations": classify_error_location(nodes, truth, action, target, errors)})
    return output


def _apply(nodes, graph, operation):
    kind, a, b = operation
    result = set(graph)
    if kind == "FN":
        result.add((a, b))
    elif kind == "FP":
        result.remove((a, b))
    else:
        result.remove((a, b))
        result.add((b, a))
    return result


def _distance(nodes, edges, action, target):
    adjacent = {n: set() for n in nodes}
    for a, b in edges:
        adjacent[a].add(b)
        adjacent[b].add(a)
    distance = {action: 0, target: 0}
    queue = deque(distance)
    while queue:
        node = queue.popleft()
        for other in adjacent[node]:
            if other not in distance:
                distance[other] = distance[node] + 1
                queue.append(other)
    return distance


def policy_candidate_orders(nodes, truth, initial, action, target, kind):
    """Return Graph-Global and Step-1 Task-Focused order for one allowed type."""
    ops = []
    for error in classify_errors(nodes, truth, initial):
        if error[0] != kind:
            continue
        correction = error
        fixed = _apply(nodes, initial, correction)
        if is_dag(nodes, fixed):
            ops.append(correction)
    global_order = sorted(ops, key=lambda op: (op[1], op[2]))
    distance = _distance(nodes, initial, action, target)
    def score(op):
        return sum(1 / (1 + distance[x]) if x in distance else 0 for x in op[1:])
    task_order = sorted(ops, key=lambda op: (-score(op), op[1], op[2]))
    return {"global": global_order, "task_focused": task_order,
            "task_scores": {"|".join(op): score(op) for op in task_order}}


def competition_recipes(nodes, truth_edges, action, target, kind):
    """Enumerate H2 challenge recipes with two same-type corrections.

    Every recipe contains one task-location error and one off-path peripheral
    error. Its initial graph and both individual corrections must be DAG-valid;
    the task path must survive; budget one cannot repair both unit-cost errors.
    Selection does not depend on policy execution or outcomes.
    """
    nodes = tuple(nodes)
    truth = set(truth_edges)
    route = _route_dyads(nodes, truth, action, target)
    candidates = []
    pairs = list(combinations(nodes, 2))
    truth_dyads = {frozenset(edge) for edge in truth}
    if kind == "FN":
        errors = [(edge, truth - {edge}, frozenset(edge) in route) for edge in sorted(truth)]
    elif kind == "REV":
        errors = [((edge[1], edge[0]), truth - {edge} | {(edge[1], edge[0])},
                   frozenset(edge) in route) for edge in sorted(truth)]
    elif kind == "FP":
        errors = []
        for a, b in pairs:
            if frozenset((a, b)) in truth_dyads:
                continue
            for edge in ((a, b), (b, a)):
                near_task = action in edge or target in edge
                errors.append((edge, truth | {edge}, near_task))
    else:
        raise ValueError(f"unknown error type: {kind}")

    for first, second in combinations(errors, 2):
        edge1, graph1, near1 = first
        edge2, graph2, near2 = second
        if frozenset(edge1) == frozenset(edge2) or near1 == near2:
            continue
        initial = set(graph1)
        if kind == "FN":
            initial = truth - {edge1, edge2}
        elif kind == "REV":
            original1 = (edge1[1], edge1[0])
            original2 = (edge2[1], edge2[0])
            initial = truth - {original1, original2} | {edge1, edge2}
        else:
            initial = truth | {edge1, edge2}
        if not is_dag(nodes, initial) or not directed_paths(nodes, initial, action, target):
            continue
        errors_found = classify_errors(nodes, truth, initial)
        if len(errors_found) != 2 or {e[0] for e in errors_found} != {kind}:
            continue
        corrections = policy_candidate_orders(nodes, truth, initial, action, target, kind)
        if len(corrections["global"]) < 2:
            continue
        locations = classify_error_location(nodes, truth, action, target, errors_found)
        # One error must occupy a task path (FN/REV) or task-adjacent position
        # (FP); the other must be outside the path and task endpoints.
        has_task_site = any(("gt_action_target_path" in loc["tags"] if kind != "FP"
                             else ("target_adjacent_off_path" in loc["tags"] or
                                   "action_adjacent_off_path" in loc["tags"])) for loc in locations)
        has_peripheral = any("off_path_peripheral" in loc["tags"] and
                             "target_adjacent_off_path" not in loc["tags"] and
                             "action_adjacent_off_path" not in loc["tags"]
                             for loc in locations)
        if not (has_task_site and has_peripheral):
            continue
        candidates.append({"kind": kind, "initial_edges": frozenset(initial),
                           "errors": errors_found, "locations": locations,
                           "path_survives": True, "candidate_orders": corrections,
                           "candidate_count": len(corrections["global"]),
                           "budget": 1, "minimum_full_repair_cost": 2,
                           "budget_limits_repairs": True,
                           "rank_diverges": corrections["global"] != corrections["task_focused"]})
    # Duplicate edge recipes are not multiple population units.
    unique = {frozenset(row["initial_edges"]): row for row in candidates}
    return [unique[key] for key in sorted(unique, key=lambda g: tuple(sorted(g)))]


def select_q_recipe(recipes, seed):
    """Select one eligible structure with a dedicated outcome-blind seed."""
    if not recipes:
        return None
    token = f"step4b2-q-recipe:{seed}".encode()
    derived = int.from_bytes(sha256(token).digest()[:8], "big")
    return recipes[random.Random(derived).randrange(len(recipes))]

"""Independent exhaustive structural audit of one-each FN/FP/REV recipes."""
from __future__ import annotations

from itertools import combinations, permutations

from .step4_error_injection import classify_errors
from .step4_topology_generator import directed_paths, is_dag


def _relevance(nodes, truth, action, target):
    path_edges = set()
    for path in directed_paths(nodes, truth, action, target):
        path_edges.update(zip(path, path[1:]))
    return path_edges


def _apply_one(graph, operation):
    kind, a, b = operation
    result = set(graph)
    if kind == "FN":
        result.remove((a, b))
    elif kind == "FP":
        result.add((a, b))
    else:
        result.remove((b, a))
        result.add((a, b))
    return result


def enumerate_mixed_recipes(nodes, truth_edges, action, target, *,
                            require_path_survival=False, require_fn_related=False,
                            require_fn_on_path=False):
    """Enumerate all disjoint one-FN/one-FP/one-REV recipes and valid orders.

    Relevance follows the Step 4A structural convention: an error is task-
    related if it lies on any GT action→target path or touches either endpoint.
    No coefficients, effects, policy scores, or regret are read.
    """
    nodes = tuple(nodes)
    truth = set(truth_edges)
    if not is_dag(nodes, truth) or not directed_paths(nodes, truth, action, target):
        raise ValueError("truth DAG and task path are required")
    route = _relevance(nodes, truth, action, target)
    route_edges = set()
    for path in directed_paths(nodes, truth, action, target):
        route_edges.update(zip(path, path[1:]))
    related_pairs = set(route)
    related_pairs.update(pair for pair in truth if action in pair or target in pair)
    dyads = [frozenset(pair) for pair in combinations(nodes, 2)]
    occupied = {frozenset(edge) for edge in truth}
    missing = [pair for pair in dyads if pair not in occupied]
    recipes = []
    counts = {"candidate_assignments": 0, "final_dag": 0,
              "relevance_ok": 0, "path_ok": 0, "order_ok": 0,
              "fixed_fn_fp_rev_order_ok": 0}
    for fn in sorted(truth):
        fn_dyad = frozenset(fn)
        fn_on_path = fn in route_edges
        if require_fn_on_path and not fn_on_path:
            continue
        fn_related = fn in related_pairs or (fn[1], fn[0]) in related_pairs
        if require_fn_related and not fn_related:
            continue
        for fp_dyad in missing:
            if fp_dyad == fn_dyad:
                continue
            a, b = sorted(fp_dyad)
            for fp in ((a, b), (b, a)):
                for rev in sorted(truth):
                    rev_dyad = frozenset(rev)
                    if rev_dyad in (fn_dyad, fp_dyad):
                        continue
                    counts["candidate_assignments"] += 1
                    operations = (("FN", *fn), ("FP", *fp), ("REV", rev[1], rev[0]))
                    initial = set(truth)
                    for operation in operations:
                        initial = _apply_one(initial, operation)
                    if not is_dag(nodes, initial):
                        continue
                    counts["final_dag"] += 1
                    errors = classify_errors(nodes, truth, initial)
                    if {item[0] for item in errors} != {"FN", "FP", "REV"}:
                        continue
                    related, peripheral = [], []
                    for error in errors:
                        _, x, y = error
                        is_related = ((x, y) in related_pairs or (y, x) in related_pairs
                                      or x in (action, target) or y in (action, target))
                        (related if is_related else peripheral).append(error)
                    if not related or not peripheral:
                        continue
                    counts["relevance_ok"] += 1
                    paths_survive = bool(directed_paths(nodes, initial, action, target))
                    if require_path_survival and not paths_survive:
                        continue
                    counts["path_ok"] += 1
                    valid_orders = []
                    for order in permutations(operations):
                        current = set(truth)
                        for operation in order:
                            current = _apply_one(current, operation)
                            if not is_dag(nodes, current):
                                break
                        else:
                            valid_orders.append(order)
                    if not valid_orders:
                        continue
                    counts["order_ok"] += 1
                    fixed_ok = operations in valid_orders
                    counts["fixed_fn_fp_rev_order_ok"] += fixed_ok
                    recipes.append({"fn": operations[0], "fp": operations[1],
                                    "rev": operations[2], "initial_edges": sorted(initial),
                                    "related_errors": related, "peripheral_errors": peripheral,
                                    "fn_on_path": fn_on_path,
                                    "paths_survive": paths_survive,
                                    "valid_orders": [[list(op) for op in order] for order in valid_orders],
                                    "fixed_order_valid": fixed_ok})
    return {"counts": counts, "recipes": recipes}

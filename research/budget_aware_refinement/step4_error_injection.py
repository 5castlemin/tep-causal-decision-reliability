"""Structure-only FN/FP/REV recipes and auditable condition outcomes."""
from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations

from .step4_topology_generator import directed_paths, is_dag

KINDS = ("FN", "FP", "REV")
CONDITIONS = ("A_path_disconnected", "B_path_survives", "C_mixed")


@dataclass(frozen=True)
class InjectionResult:
    condition: str
    accepted: bool
    reason: str
    truth_edges: frozenset[tuple[str, str]]
    initial_edges: frozenset[tuple[str, str]]
    errors: tuple[tuple[str, str, str], ...]
    remaining_paths: tuple[tuple[str, ...], ...]
    relevant_errors: tuple[tuple[str, str, str], ...]
    peripheral_errors: tuple[tuple[str, str, str], ...]
    cycle_rejections: tuple[tuple[str, str, str], ...]


def classify_errors(nodes, truth_edges, initial_edges):
    """Partition pairwise differences into atomic FN/FP/REV operations."""
    truth, initial = set(truth_edges), set(initial_edges)
    errors = []
    for a, b in combinations(nodes, 2):
        t = (a, b) if (a, b) in truth else (b, a) if (b, a) in truth else None
        g = (a, b) if (a, b) in initial else (b, a) if (b, a) in initial else None
        if t and not g:
            errors.append(("FN", *t))
        elif g and not t:
            errors.append(("FP", *g))
        elif t and g and t != g:
            errors.append(("REV", *g))
    return tuple(errors)


def _task_relevant(edges, nodes, action, target):
    """GT-based error-generation stratum, separate from G0/H policy scoring."""
    p = directed_paths(nodes, edges, action, target)
    relevant = set()
    for path in p:
        relevant.update(zip(path, path[1:]))
    return relevant


def _candidate_ops(nodes, truth, current, allowed):
    ops = []
    for a, b in combinations(nodes, 2):
        t = (a, b) if (a, b) in truth else (b, a) if (b, a) in truth else None
        g = (a, b) if (a, b) in current else (b, a) if (b, a) in current else None
        op = ("FN", *t) if t and not g else ("FP", *g) if g and not t else ("REV", *g) if t and g and t != g else None
        if op and op[0] in allowed:
            ops.append(op)
    return tuple(ops)


def _result(condition, reason, nodes, truth, initial, action, target, cycles=()):
    errors = classify_errors(nodes, truth, initial)
    routes = set()
    for p in directed_paths(nodes, truth, action, target):
        routes.update(zip(p, p[1:]))
    rel, per = [], []
    for op in errors:
        kind, a, b = op
        if (a, b) in routes or (b, a) in routes or a in (action, target) or b in (action, target):
            rel.append(op)
        else:
            per.append(op)
    initial_path = directed_paths(nodes, initial, action, target)
    valid = reason == "accepted" and is_dag(nodes, initial)
    return InjectionResult(condition, valid, reason, frozenset(truth), frozenset(initial),
                          errors, initial_path, tuple(rel), tuple(per), tuple(cycles))


def inject_condition(nodes, truth_edges, action, target, condition, seed=0):
    """Deterministic bounded recipe search; no outcome or policy result access.

    Search enumerates finite edge-operation combinations in immutable node-ID
    order. Every rejected cyclic intermediate recipe is retained in the result.
    No seed replacement or unbounded retry occurs.
    """
    nodes = tuple(nodes); truth = frozenset(map(tuple, truth_edges))
    if condition not in CONDITIONS:
        return _result(condition, "unknown_condition", nodes, truth, truth, action, target)
    if not is_dag(nodes, truth):
        return _result(condition, "truth_not_dag", nodes, truth, truth, action, target)
    paths = directed_paths(nodes, truth, action, target)
    if not paths:
        return _result(condition, "truth_has_no_task_path", nodes, truth, truth, action, target)

    cycles = []
    if condition == "A_path_disconnected":
        # Find a minimum-cardinality FN cut from the union of task-path edges.
        path_edges = sorted(set().union(*(set(zip(p, p[1:])) for p in paths)))
        for size in range(1, len(path_edges) + 1):
            for cut in combinations(path_edges, size):
                initial = truth - set(cut)
                if not directed_paths(nodes, initial, action, target):
                    return _result(condition, "accepted", nodes, truth, initial, action, target)
        return _result(condition, "no_fn_path_cut", nodes, truth, truth, action, target)

    if condition == "B_path_survives":
        relevant = _task_relevant(truth, nodes, action, target)
        ops = [("FN", *e) for e in sorted(relevant)]
        ops += [("REV", *e) for e in sorted(truth & relevant)]
        # A false edge is task-related when it touches an endpoint of an
        # existing truth route. This is a GT generation stratum only.
        for a, b in combinations(nodes, 2):
            if (a, b) in truth or (b, a) in truth: continue
            if action in (a, b) or target in (a, b):
                ops.extend([("FP", a, b), ("FP", b, a)])
        # Rotate the candidate class order with the declared seed so the B
        # feasibility audit does not silently test FN only.
        order = KINDS[seed % len(KINDS):] + KINDS[:seed % len(KINDS)]
        ops.sort(key=lambda op: (order.index(op[0]), op[1], op[2]))
        for kind, a, b in ops:
            if kind == "FN": candidate = truth - {(a, b)}
            elif kind == "FP": candidate = truth | {(a, b)}
            else: candidate = (truth - {(a, b)}) | {(b, a)}
            if not is_dag(nodes, candidate):
                if kind == "REV": cycles.append((kind, a, b))
                continue
            if directed_paths(nodes, candidate, action, target):
                return _result(condition, "accepted", nodes, truth, candidate, action, target, cycles)
        return _result(condition, "no_path_preserving_task_related_single_error", nodes, truth, truth, action, target, cycles)

    # C requires all three error types, at least one task-related error, and
    # at least one error on a structurally peripheral pair. Every intermediate
    # graph is checked; failed recipes remain bounded by the finite edge set.
    route = _task_relevant(truth, nodes, action, target)
    pairs = list(combinations(nodes, 2))
    for fn in sorted(route):
        g1 = truth - {fn}
        if not is_dag(nodes, g1): continue
        for a, b in pairs:
            if (a, b) in g1 or (b, a) in g1: continue
            for fp in ((a, b), (b, a)):
                g2 = g1 | {fp}
                if not is_dag(nodes, g2): continue
                for rev in sorted(truth - {fn}):
                    g3 = (g2 - {rev}) | {(rev[1], rev[0])}
                    if not is_dag(nodes, g3):
                        cycles.append(("REV", *rev)); continue
                    if not directed_paths(nodes, g3, action, target): continue
                    errors = classify_errors(nodes, truth, g3)
                    kinds = {e[0] for e in errors}
                    result = _result(condition, "accepted", nodes, truth, g3, action, target, cycles)
                    if set(KINDS) <= kinds and result.relevant_errors and result.peripheral_errors:
                        return result
    return _result(condition, "no_dag_mixed_related_and_peripheral_recipe", nodes, truth, truth, action, target, cycles)


def policy_opportunities(nodes, truth, initial):
    return {kind: len(_candidate_ops(nodes, set(truth), set(initial), {kind})) for kind in KINDS}

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
    """Structural relevance: edge touches the X-Y ancestral route skeleton."""
    p = directed_paths(nodes, edges, action, target)
    relevant = set()
    for path in p:
        relevant.update(zip(path, path[1:]))
    # Include one-hop task-adjacent candidate pairs for false additions.
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


def inject_condition(nodes, truth_edges, action, target, condition):
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
        # Enumerate one FN and one atomic REV, then a false edge. Keep only
        # acyclic graphs with a surviving path and all three relevant classes.
        for fn in sorted(set().union(*(set(zip(p, p[1:])) for p in paths))):
            after_fn = truth - {fn}
            for rev in sorted(after_fn):
                reversed_graph = (after_fn - {rev}) | {(rev[1], rev[0])}
                if not is_dag(nodes, reversed_graph):
                    cycles.append(("REV", *rev)); continue
                if not directed_paths(nodes, reversed_graph, action, target):
                    continue
                for a, b in combinations(nodes, 2):
                    if any(e in reversed_graph or e[::-1] in reversed_graph for e in ((a, b),)):
                        continue
                    for fp in ((a, b), (b, a)):
                        candidate = reversed_graph | {fp}
                        if not is_dag(nodes, candidate) or not directed_paths(nodes, candidate, action, target):
                            continue
                        errors = classify_errors(nodes, truth, candidate)
                        kinds = {e[0] for e in errors}
                        relevant = _task_relevant(truth, nodes, action, target)
                        relevant_errors = [e for e in errors if (e[1], e[2]) in relevant or
                                           (e[2], e[1]) in relevant or action in e[1:] or target in e[1:]]
                        if {"FN", "FP", "REV"} <= kinds and all(any(e[0] == k for e in relevant_errors) for k in KINDS):
                            return _result(condition, "accepted", nodes, truth, candidate, action, target, cycles)
        return _result(condition, "no_dag_path_preserving_fn_fp_rev_recipe", nodes, truth, truth, action, target, cycles)

    # Mixed: require at least one FN, FP, REV; add a peripheral error when the
    # topology admits one, otherwise preserve this exact infeasible outcome.
    base = inject_condition(nodes, truth, action, target, "B_path_survives")
    if not base.accepted:
        return _result(condition, "mixed_requires_path_surviving_fn_fp_rev:" + base.reason,
                       nodes, truth, truth, action, target, base.cycle_rejections)
    errors = base.errors
    task_edges = _task_relevant(truth, nodes, action, target)
    peripheral_truth = sorted(e for e in truth if e not in task_edges and e[::-1] not in task_edges)
    if not peripheral_truth:
        return _result(condition, "no_peripheral_truth_edge_for_control", nodes, truth,
                       base.initial_edges, action, target)
    # Label peripheral vs related; B recipe already preserves all three kinds.
    return _result(condition, "accepted", nodes, truth, base.initial_edges, action, target,
                   base.cycle_rejections)


def policy_opportunities(nodes, truth, initial):
    return {kind: len(_candidate_ops(nodes, set(truth), set(initial), {kind})) for kind in KINDS}

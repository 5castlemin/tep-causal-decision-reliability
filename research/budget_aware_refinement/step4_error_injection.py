"""Structure-only FN/FP/REV recipes and auditable condition outcomes."""
from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations, permutations
import random

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


def _has_dag_valid_order(nodes, truth, operations):
    """Whether any order of atomic corrections keeps every intermediate DAG valid."""
    for order in permutations(operations):
        current = set(truth)
        for kind, x, y in order:
            if kind == "FN": current.remove((x, y))
            elif kind == "FP": current.add((x, y))
            else: current.remove((y, x)); current.add((x, y))
            if not is_dag(nodes, current):
                break
        else:
            return True
    return False


def enumerate_c_recipes(nodes, truth_edges, action, target):
    """Return mixed C recipes that have at least one DAG-valid operation order."""
    nodes = tuple(nodes)
    truth = frozenset(map(tuple, truth_edges))
    pairs = list(combinations(nodes, 2))
    truth_dyads = {frozenset(edge) for edge in truth}
    route_dyads = set()
    for path in directed_paths(nodes, truth, action, target):
        route_dyads.update(frozenset(edge) for edge in zip(path, path[1:]))
    related_dyads = set(route_dyads)
    related_dyads.update(frozenset((a, b)) for a, b in pairs
                         if action in (a, b) or target in (a, b))
    recipes = []
    cycles = []
    for fn in sorted(truth):
        for a, b in pairs:
            fp_dyad = frozenset((a, b))
            if fp_dyad in truth_dyads or fp_dyad == frozenset(fn):
                continue
            for fp in ((a, b), (b, a)):
                for rev in sorted(truth - {fn}):
                    if frozenset(rev) in (frozenset(fn), fp_dyad):
                        continue
                    initial = (set(truth) - {fn, rev}) | {fp, (rev[1], rev[0])}
                    if not is_dag(nodes, initial):
                        cycles.append(("REV", *rev))
                        continue
                    operations = (("FN", *fn), ("FP", *fp), ("REV", rev[1], rev[0]))
                    if not _has_dag_valid_order(nodes, truth, operations):
                        continue
                    errors = classify_errors(nodes, truth, initial)
                    if {e[0] for e in errors} != set(KINDS):
                        continue
                    related = [e for e in errors if frozenset(e[1:]) in related_dyads]
                    peripheral = [e for e in errors if frozenset(e[1:]) not in related_dyads]
                    if related and peripheral:
                        recipes.append({"operations": operations,
                                        "initial_edges": frozenset(initial),
                                        "related_errors": tuple(related),
                                        "peripheral_errors": tuple(peripheral)})
    return recipes, tuple(sorted(set(cycles)))


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


def inject_condition(nodes, truth_edges, action, target, condition, seed=0, requested_b_type=None):
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
        if requested_b_type is not None and requested_b_type not in KINDS:
            return _result(condition, "unknown_requested_b_type", nodes, truth, truth, action, target)
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
        if requested_b_type is not None:
            ops = [op for op in ops if op[0] == requested_b_type]
            random.Random(seed).shuffle(ops)
        else:
            # Legacy v1 behavior retained for exact historical reconstruction.
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
        reason = (f"no_path_preserving_task_related_{requested_b_type}"
                  if requested_b_type is not None else "no_path_preserving_task_related_single_error")
        return _result(condition, reason, nodes, truth, truth, action, target, cycles)

    # C's written eligibility is mixed FN/FP/REV with both task-related and
    # peripheral errors. It does not require path survival or require the FN
    # itself to be on a task path. Enumerate all disjoint one-each recipes and
    # accept any recipe with at least one DAG-valid atomic operation order.
    # Select uniformly from structurally eligible recipes using the separate
    # error-injection stream; no effects, regret, or policy output is read.
    recipes, cycles = enumerate_c_recipes(nodes, truth, action, target)
    if recipes:
        rng = random.Random(seed)
        return _result(condition, "accepted", nodes, truth,
                       recipes[rng.randrange(len(recipes))]["initial_edges"], action, target,
                       cycles)
    return _result(condition, "no_dag_mixed_related_and_peripheral_recipe", nodes, truth, truth, action, target, cycles)


def policy_opportunities(nodes, truth, initial):
    return {kind: len(_candidate_ops(nodes, set(truth), set(initial), {kind})) for kind in KINDS}

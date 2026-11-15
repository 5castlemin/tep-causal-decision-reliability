"""Deterministic topology-only DAG generation for Step 4A feasibility work.

This module does not draw SCM coefficients, observations, fit learners, recommend
actions, or calculate regret. Template edges have priority over target density.
"""
from __future__ import annotations

from dataclasses import dataclass
import random

TEMPLATES = ("chain_mediation", "fork_branch", "observed_common_cause", "multiple_directed_paths")
MIN_NODES, MAX_NODES, MAX_PARENTS = 6, 10, 3


class TopologyError(ValueError):
    """A requested topology cannot be built under the declared constraints."""


@dataclass(frozen=True)
class Task:
    action: str
    target: str
    kind: str


@dataclass(frozen=True)
class Topology:
    nodes: tuple[str, ...]
    topological_order: tuple[str, ...]
    edges: frozenset[tuple[str, str]]
    template: str
    seed: int
    target_density: float
    target_edge_count: int
    tasks: tuple[Task, ...]


def is_dag(nodes, edges) -> bool:
    order = {node: i for i, node in enumerate(nodes)}
    return all(a in order and b in order and order[a] < order[b] and a != b for a, b in edges)


def _parents_ok(nodes, edges, maximum=MAX_PARENTS):
    return all(sum(v == node for _, v in edges) <= maximum for node in nodes)


def directed_paths(nodes, edges, source, target):
    children = {n: [] for n in nodes}
    for a, b in edges:
        children[a].append(b)
    found = []
    def walk(node, trail):
        if node == target:
            found.append(tuple(trail)); return
        for child in children[node]:
            if child not in trail:
                walk(child, trail + [child])
    walk(source, [source])
    return tuple(found)


def _scaffold(nodes, template):
    x, y = nodes[0], nodes[-1]
    m = len(nodes)
    if template == "chain_mediation":
        return {(nodes[i], nodes[i + 1]) for i in range(m - 1)}
    if template == "fork_branch":
        # X fans out; one branch reaches Y and the others are observed controls.
        return {(x, nodes[i]) for i in range(1, m - 1)} | {(nodes[-2], y)}
    if template == "observed_common_cause":
        # C is observed and causes both task variables; the second route gives
        # an explicit mediation motif. All arrows follow the fixed order.
        c, x, mid = nodes[:3]
        return {(c, x), (c, y), (x, mid), (mid, y)}
    if template == "multiple_directed_paths":
        a, b, c, d = nodes[1:5]
        # Two internally vertex-disjoint directed paths plus a peripheral edge.
        return {(x, a), (a, y), (x, b), (b, y), (c, d)}
    raise TopologyError(f"unknown template: {template}")


def classify_tasks(nodes, edges, allow_direct_plus_indirect=True):
    """Return deterministic direct and indirect X,Y task pairs.

    Direct means X->Y exists. Indirect means a length>=2 path exists. A pair
    with both is retained by default, so task classes can overlap by design.
    """
    edge_set = set(edges)
    direct, indirect = [], []
    for x in nodes:
        for y in nodes:
            if x == y:
                continue
            p = directed_paths(nodes, edge_set, x, y)
            has_direct = (x, y) in edge_set
            has_indirect = any(len(path) >= 3 for path in p)
            if has_direct and (has_indirect or allow_direct_plus_indirect):
                direct.append(Task(x, y, "direct"))
            if has_indirect:
                indirect.append(Task(x, y, "indirect"))
    return tuple(direct), tuple(indirect)


def generate_topology(n_nodes: int, template: str, seed: int, density=(0.2, 0.4)) -> Topology:
    if type(n_nodes) is not int or not MIN_NODES <= n_nodes <= MAX_NODES:
        raise TopologyError(f"n_nodes must be an integer in [{MIN_NODES},{MAX_NODES}]")
    if template not in TEMPLATES:
        raise TopologyError(f"unknown template: {template}")
    if type(seed) is not int:
        raise TopologyError("seed must be an integer")
    lo, hi = density
    if not (0 < lo <= hi < 1):
        raise TopologyError("density must satisfy 0 < low <= high < 1")
    rng = random.Random(seed)
    nodes = tuple(f"V{i:02d}" for i in range(n_nodes))
    # The canonical immutable ID order is the declared topological order.
    # Seed affects only eligible-edge augmentation, never node identity.
    topo = nodes
    edges = _scaffold(topo, template)
    max_edges = n_nodes * (n_nodes - 1) // 2
    requested = round((lo + hi) / 2 * max_edges)
    target = max(len(edges), requested)  # mandatory motif wins over density.
    target = min(target, max_edges)
    candidates = [(topo[i], topo[j]) for i in range(n_nodes) for j in range(i + 1, n_nodes)
                  if (topo[i], topo[j]) not in edges]
    rng.shuffle(candidates)
    for edge in candidates:
        if len(edges) >= target:
            break
        if sum(v == edge[1] for _, v in edges) >= MAX_PARENTS:
            continue
        edges.add(edge)
    if not is_dag(topo, edges) or not _parents_ok(topo, edges):
        raise TopologyError("internal scaffold/augmentation constraint failure")
    tasks = classify_tasks(topo, edges)
    direct, indirect = tasks
    if not direct or not indirect:
        raise TopologyError("template did not yield both direct and indirect task candidates")
    return Topology(nodes, topo, frozenset(edges), template, seed, (lo + hi) / 2,
                    target, tuple(direct + indirect))

"""GT-blind DAG completion option for software testing only.

The canonical node-ID topological order resolves undirected pairs without GT
input. It is intentionally not connected to the active policy/evaluation path:
orientation changes the learner input and the candidate does not charge that
transition to the repair budget.
"""
from __future__ import annotations

from heapq import heappop, heappush
from typing import Mapping

from .policy_engine import UNRES, dag, graph_hash


def complete_unresolved_for_test_only(
    graph: Mapping[tuple[str, str], tuple[str, str] | str],
    *, nodes: tuple[str, ...] | list[str], test_only: bool = False,
) -> dict:
    """Orient all UNRES pairs by lexical Kahn topological order, with no GT access.

    The result is a deterministic learner-input candidate. It is an
    unbudgeted representation transformation, not an approved repair rule.
    """
    if test_only is not True:
        raise PermissionError("DAG completion adapter is TEST_ONLY and not activated")
    nodes = tuple(nodes)
    if not nodes or len(set(nodes)) != len(nodes) or not dag(graph):
        raise ValueError("invalid nodes or directed graph state")
    if any(a not in nodes or b not in nodes for pair in graph for a, b in [pair]):
        raise ValueError("graph state contains a node outside the declared schema")

    children = {node: set() for node in nodes}
    indegree = dict.fromkeys(nodes, 0)
    for value in graph.values():
        if value == UNRES:
            continue
        parent, child = value
        if child not in children[parent]:
            children[parent].add(child)
            indegree[child] += 1
    ready = []
    for node, degree in indegree.items():
        if degree == 0:
            heappush(ready, node)
    order = []
    while ready:
        node = heappop(ready)
        order.append(node)
        for child in sorted(children[node]):
            indegree[child] -= 1
            if indegree[child] == 0:
                heappush(ready, child)
    if len(order) != len(nodes):
        raise ValueError("directed part is cyclic")
    rank = {node: index for index, node in enumerate(order)}
    completed = dict(graph)
    assignments = []
    for pair, value in sorted(graph.items()):
        if value != UNRES:
            continue
        u, v = pair
        edge = (u, v) if rank[u] < rank[v] else (v, u)
        completed[pair] = edge
        assignments.append({"pair": list(pair), "direction": list(edge)})
    if not dag(completed):
        raise AssertionError("topological completion failed DAG validation")
    edges = [list(value) for _, value in sorted(completed.items())]
    return {"status": "TEST_ONLY_UNAPPROVED_COMPLETION",
            "method": "lexicographic_kahn_order_orient_lower_rank_to_higher_rank",
            "gt_information_used": False,
            "outcome_information_used": False,
            "node_order": order,
            "assignments": assignments,
            "original_graph_sha256": graph_hash(graph),
            "completed_graph_sha256": graph_hash(completed),
            "completed_edges": edges,
            "residual_unresolved": [],
            "representation_transition_not_repair": True,
            "charged_to_repair_budget": False,
            "research_use_activated": False}

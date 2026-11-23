"""GT-blind learner encoding candidate for residual unresolved adjacencies.

This module separates the scored structural graph from the directed DAG given
to the current linear learner. Omitting an unresolved adjacency is an abstention
encoding, not an edge deletion, repair, or change to structural metrics. It is
implemented for TEST_ONLY E2E validation and is not an approved study contract.
"""
from __future__ import annotations

from typing import Mapping

from .policy_engine import UNRES, dag, graph_hash, pair


def encode_residual_unresolved_abstention(
    graph: Mapping[tuple[str, str], tuple[str, str] | str], *,
    nodes: tuple[str, ...] | list[str],
) -> dict:
    """Return separate structural and learner graph records without GT input."""
    nodes = tuple(nodes)
    if not nodes or len(nodes) != len(set(nodes)):
        raise ValueError("nodes must be nonempty and unique")
    allowed_pairs = {pair(a, b) for i, a in enumerate(nodes) for b in nodes[i + 1:]}
    if not set(graph) <= allowed_pairs:
        raise ValueError("structural graph contains an undeclared node pair")
    if not dag(graph):
        raise ValueError("directed component of structural graph must be acyclic")
    directed = {p: edge for p, edge in graph.items() if edge != UNRES}
    unresolved = sorted(p for p, edge in graph.items() if edge == UNRES)
    if not dag(directed):
        raise AssertionError("learner graph is not a DAG")
    return {
        "encoding_status": "TEST_ONLY_PROPOSED_ABSTENTION_NOT_APPROVED",
        "structural_graph_sha256": graph_hash(graph),
        "structural_unresolved_pairs": [list(p) for p in unresolved],
        "learner_dag_edges": [list(edge) for _, edge in sorted(directed.items())],
        "learner_dag_sha256": graph_hash(directed),
        "omitted_unresolved_count": len(unresolved),
        "uses_unresolved_as_directed_parent_child": False,
        "structural_unresolved_removed": False,
        "repair_or_resolution_performed": False,
        "additional_edit_cost": 0,
        "gt_information_used": False,
        "gt_outcome_information_used": False,
    }

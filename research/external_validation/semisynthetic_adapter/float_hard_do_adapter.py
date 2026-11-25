"""Stateless finite numeric hard-do sampling for causalAssembly fitted models.

The adapter follows the upstream pinned sampler's factorization and public
``DRF.produce_sample`` / SciPy KDE interfaces, without changing upstream state.
It is intentionally limited to a single constant intervention.
"""
from __future__ import annotations

import math
import numbers
from typing import Any

import networkx as nx
import numpy as np
import pandas as pd


def mutilated_graph_for_hard_do(graph: nx.DiGraph, node: str) -> nx.DiGraph:
    """Return a copy with only the intervention node's incoming edges cut."""
    if node not in graph:
        raise ValueError(f"intervention node {node!r} is not in the graph")
    mutilated = graph.copy()
    mutilated.remove_edges_from(list(graph.in_edges(node)))
    return mutilated


def sample_hard_do(
    fitted_model: Any,
    node: str,
    value: int | float | np.number,
    *,
    size: int,
    rng: np.random.Generator,
    smoothed: bool = True,
) -> pd.DataFrame:
    """Draw from the original DAG factorization under ``do(node=value)``.

    The model must expose causalAssembly's ``graph``, ``nodes``, ``drf`` and
    ``parents(of_node=...)`` attributes.  The function does not call
    ``intervene_on`` and does not mutate graph, fitted mechanisms, RNG fields,
    or intervention dictionaries on the supplied object.
    """
    if isinstance(size, (bool, np.bool_)) or not isinstance(size, numbers.Integral) or size <= 0:
        raise ValueError("size must be a positive integer")
    if not isinstance(rng, np.random.Generator):
        raise TypeError("rng must be an explicit numpy.random.Generator")
    real_numeric = isinstance(value, numbers.Real) or isinstance(value, (np.integer, np.floating))
    if isinstance(value, (bool, np.bool_)) or not real_numeric:
        raise TypeError("hard-do value must be a finite real numeric scalar, not bool")
    scalar = value.item() if isinstance(value, np.generic) else value
    try:
        finite_scalar = math.isfinite(float(scalar))
    except (OverflowError, TypeError, ValueError):
        finite_scalar = False
    if not finite_scalar:
        raise ValueError("hard-do value must be finite")
    if not isinstance(smoothed, (bool, np.bool_)):
        raise TypeError("smoothed must be bool")

    graph = fitted_model.graph
    nodes = list(fitted_model.nodes)
    if len(nodes) != len(set(nodes)) or set(nodes) != set(graph.nodes):
        raise ValueError("model node order must contain each graph node exactly once")
    if node not in graph:
        raise ValueError(f"intervention node {node!r} is not in the graph")
    mechanisms = fitted_model.drf
    if not isinstance(mechanisms, dict) or set(mechanisms) != set(nodes):
        raise ValueError("a fitted mechanism is required for every graph node")
    if not graph.is_directed() or not nx.is_directed_acyclic_graph(graph):
        raise ValueError("hard-do sampling requires a directed acyclic graph")
    do_graph = mutilated_graph_for_hard_do(graph, node)
    if set(do_graph.out_edges(node)) != set(graph.out_edges(node)):
        raise RuntimeError("hard-do mutilation changed outgoing edges")

    samples: dict[str, np.ndarray] = {}
    # The original DAG order remains a valid order after incoming edges are cut.
    for current in nx.topological_sort(graph):
        if current == node:
            samples[current] = np.full(int(size), scalar)
            continue
        mechanism = mechanisms[current]
        # causalAssembly uses scipy.stats.gaussian_kde for root mechanisms.
        # Duck typing keeps this adapter importable in the repository's CI
        # environment, where the optional external R/DRF stack is not installed.
        if hasattr(mechanism, "resample") and hasattr(mechanism, "dataset"):
            if smoothed:
                samples[current] = mechanism.resample(size=int(size), seed=rng)[0]
            else:
                dataset = np.asarray(mechanism.dataset[0])
                samples[current] = dataset[rng.choice(len(dataset), size=int(size), replace=True)]
            continue

        parents = list(fitted_model.parents(of_node=current))
        if any(parent not in samples for parent in parents):
            raise ValueError(f"parent ordering is inconsistent with DAG for {current!r}")
        parent_frame = pd.DataFrame({parent: samples[parent] for parent in parents}, columns=parents)
        produced = np.asarray(mechanism.produce_sample(newdata=parent_frame, random_state=rng))
        produced = np.squeeze(produced)
        if produced.ndim == 0 and size == 1:
            produced = produced.reshape(1)
        if produced.ndim != 1 or produced.shape[0] != size:
            raise ValueError(f"fitted mechanism for {current!r} returned an invalid sample shape")
        samples[current] = produced

    result = pd.DataFrame(samples).reindex(columns=nodes)
    if not np.all(result[node].to_numpy() == scalar):
        raise RuntimeError("hard-do value was not constant in every generated row")
    return result

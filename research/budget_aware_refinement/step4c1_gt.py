"""Analytic intervention evaluator for the active linear Gaussian SCM family."""
from __future__ import annotations

import math
from collections.abc import Mapping

from .step4_topology_generator import is_dag


def analytic_intervention_means(truth_spec: Mapping[str, object], action: str,
                                action_value: float) -> dict[str, float]:
    """Compute exact E[X | do(action=action_value)] by forward substitution.

    Exogenous means are supplied by the truth spec. The intervention replaces
    the action equation, thereby cutting all incoming edges to that node.
    No fitted learner or observational sample is accepted by this API.
    """
    nodes = tuple(truth_spec.get("nodes", ()))
    edges = tuple(tuple(edge) for edge in truth_spec.get("edges", ()))
    order = tuple(truth_spec.get("topological_order", ()))
    coefficients = truth_spec.get("coefficients")
    noise = truth_spec.get("noise")
    if (not nodes or len(set(nodes)) != len(nodes) or set(order) != set(nodes)
            or len(order) != len(nodes) or not is_dag(nodes, edges)):
        raise ValueError("invalid GT DAG or topological order")
    if action not in nodes or type(action_value) not in (int, float) or not math.isfinite(float(action_value)):
        raise ValueError("invalid intervention")
    if not isinstance(coefficients, Mapping) or not isinstance(noise, Mapping):
        raise ValueError("GT coefficients and exogenous means are required")
    means = noise.get("means")
    if not isinstance(means, Mapping) or set(means) != set(nodes):
        raise ValueError("exogenous means must be specified for every node")
    parents = {node: [] for node in nodes}
    for parent, child in edges:
        parents[child].append(parent)
    result: dict[str, float] = {}
    for node in order:
        if node == action:
            result[node] = float(action_value)
            continue
        terms = [float(means[node])]
        for parent in sorted(parents[node]):
            key = f"{parent}->{node}"
            coefficient = coefficients.get(key)
            if type(coefficient) not in (int, float) or not math.isfinite(float(coefficient)):
                raise ValueError(f"invalid GT coefficient for {key}")
            terms.append(float(coefficient) * result[parent])
        value = math.fsum(terms)
        if not math.isfinite(value):
            raise FloatingPointError(f"nonfinite analytic intervention mean at {node}")
        result[node] = value
    return result


def analytic_response(truth_spec: Mapping[str, object], action: str,
                      action_value: float) -> dict[str, float]:
    """Step 3 evaluator callback; returns exact intervention means by node."""
    return analytic_intervention_means(truth_spec, action, action_value)

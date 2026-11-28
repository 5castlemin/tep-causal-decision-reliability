"""Deterministic linear SCM and shared observation generation for Step 4C-1.

This module implements the existing proposed SCM family. It is exercised only
with fixed fixtures in Step 4C-1; it does not sample a study cohort.
"""
from __future__ import annotations

import hashlib
import heapq
import json
from typing import Mapping

import numpy as np

from .step4_rng import RNGKey, RNG_PROTOCOL_VERSION, numpy_seed_sequence

N_OBSERVATIONS = 512
COEFFICIENT_ABS_RANGE = (0.25, 0.8)
NOISE_SD_RANGE = (0.8, 1.2)
NOISE_FAMILY = "independent_gaussian_mean_zero"


def _canonical(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False).encode("ascii")


def _rng(*, cohort: str, master_seed: int, scm_id: str, template: str,
         node_count: int, attempt: int, stream: str, substream: str = ""):
    key = RNGKey(RNG_PROTOCOL_VERSION, cohort, master_seed, scm_id,
                 template, node_count, attempt, stream, substream=substream)
    return np.random.default_rng(numpy_seed_sequence(key))


def _topological_order(nodes, edges) -> tuple[str, ...]:
    indegree = {node: 0 for node in nodes}
    children = {node: [] for node in nodes}
    for parent, child in edges:
        if parent not in indegree or child not in indegree or parent == child:
            raise ValueError("invalid SCM edge")
        indegree[child] += 1
        children[parent].append(child)
    ready = [node for node, degree in indegree.items() if degree == 0]
    heapq.heapify(ready)
    result = []
    while ready:
        node = heapq.heappop(ready)
        result.append(node)
        for child in sorted(children[node]):
            indegree[child] -= 1
            if indegree[child] == 0:
                heapq.heappush(ready, child)
    if len(result) != len(nodes):
        raise ValueError("SCM graph contains a directed cycle")
    return tuple(result)


def _proposal_binding(proposal: Mapping[str, object]) -> tuple:
    if not proposal.get("accepted") or not proposal.get("scm_id"):
        raise ValueError("SCM parameters can be drawn only after structural eligibility")
    cohort = proposal.get("cohort")
    prefix = "dev-scm-" if cohort == "development" else "rep-scm-" if cohort == "confirmation" else None
    if prefix is None or not str(proposal["scm_id"]).startswith(prefix):
        raise ValueError("SCM ID is not namespaced to its cohort")
    master_seed = proposal.get("master_seed")
    if type(master_seed) is not int or master_seed < 0:
        raise ValueError("proposal must carry its nonnegative master seed")
    attempt = proposal.get("attempt")
    if type(attempt) is not int or attempt < 0:
        raise ValueError("proposal attempt must be nonnegative")
    nodes = tuple(proposal.get("nodes", ()))
    edges = tuple(sorted(tuple(edge) for edge in proposal.get("topology_edges", ())))
    if len(nodes) < 2 or len(set(nodes)) != len(nodes):
        raise ValueError("proposal node IDs must be unique")
    order = _topological_order(nodes, edges)
    return cohort, master_seed, str(proposal["scm_id"]), str(proposal["template"]), len(nodes), attempt, nodes, edges, order


def generate_scm_parameters(proposal: Mapping[str, object]) -> dict:
    """Draw fixed-range signed edge coefficients and node noise scales.

    Magnitudes are Uniform[.25,.8], signs are independent Bernoulli(1/2),
    assigned by sorted directed edge ID. Node noise SDs are Uniform[.8,1.2].
    No effect or loss is computed or used for rejection.
    """
    cohort, master, scm_id, template, n, attempt, nodes, edges, order = _proposal_binding(proposal)
    mag = _rng(cohort=cohort, master_seed=master, scm_id=scm_id, template=template,
               node_count=n, attempt=attempt, stream="coefficient", substream="magnitude")
    sign = _rng(cohort=cohort, master_seed=master, scm_id=scm_id, template=template,
                node_count=n, attempt=attempt, stream="coefficient", substream="sign")
    coefficients = {}
    for edge in edges:
        value = float(mag.uniform(*COEFFICIENT_ABS_RANGE))
        polarity = -1.0 if int(sign.integers(0, 2)) == 0 else 1.0
        coefficients["->".join(edge)] = polarity * value
    noise_rng = _rng(cohort=cohort, master_seed=master, scm_id=scm_id, template=template,
                     node_count=n, attempt=attempt, stream="exogenous_noise", substream="node_sd")
    noise_sd = {node: float(noise_rng.uniform(*NOISE_SD_RANGE)) for node in sorted(nodes)}
    truth = {"nodes": list(nodes), "topological_order": list(order),
             "edges": [list(edge) for edge in edges], "coefficients": coefficients,
             "noise": {"family": NOISE_FAMILY, "means": {node: 0.0 for node in sorted(nodes)},
                       "sd": noise_sd}}
    return {"truth_spec": truth, "equation_signature_sha256": hashlib.sha256(_canonical(truth)).hexdigest(),
            "coefficient_stream": "coefficient/magnitude + coefficient/sign",
            "noise_parameter_stream": "exogenous_noise/node_sd", "outcome_selection": False}


def generate_observations(proposal: Mapping[str, object], scm: Mapping[str, object],
                          n_rows: int = N_OBSERVATIONS) -> dict:
    """Generate one shared observational matrix from the acyclic linear SCM."""
    if type(n_rows) is not int or n_rows != N_OBSERVATIONS:
        raise ValueError(f"active contract requires exactly {N_OBSERVATIONS} rows")
    cohort, master, scm_id, template, n, attempt, nodes, edges, order = _proposal_binding(proposal)
    truth = scm.get("truth_spec")
    if not isinstance(truth, Mapping) or tuple(truth.get("nodes", ())) != nodes:
        raise ValueError("SCM specification does not match proposal node schema")
    if tuple(map(tuple, truth.get("edges", ()))) != edges:
        raise ValueError("SCM specification does not match proposal topology")
    if scm.get("equation_signature_sha256") != hashlib.sha256(_canonical(truth)).hexdigest():
        raise ValueError("equation signature mismatch")
    rng = _rng(cohort=cohort, master_seed=master, scm_id=scm_id, template=template,
               node_count=n, attempt=attempt, stream="observational_sample")
    noise = np.column_stack([rng.normal(0.0, float(truth["noise"]["sd"][node]), n_rows)
                             for node in nodes]).astype(np.float64, copy=False)
    return simulate_from_exogenous_noise(truth, noise, source="rng:observational_sample")


def simulate_from_exogenous_noise(truth: Mapping[str, object], noise: np.ndarray,
                                  *, source: str = "fixed_test_fixture") -> dict:
    """Evaluate a fixed exogenous-noise matrix through explicit SCM equations."""
    nodes = tuple(truth.get("nodes", ()))
    edges = tuple(tuple(edge) for edge in truth.get("edges", ()))
    order = tuple(truth.get("topological_order", ()))
    from .step4_topology_generator import is_dag
    if (not nodes or len(set(nodes)) != len(nodes) or set(order) != set(nodes)
            or len(order) != len(nodes) or not is_dag(nodes, edges)):
        raise ValueError("invalid SCM node/topological order")
    rank = {node: index for index, node in enumerate(order)}
    if any(rank[parent] >= rank[child] for parent, child in edges):
        raise ValueError("provided order is not a topological order")
    if not isinstance(noise, np.ndarray) or noise.ndim != 2 or noise.shape[1] != len(nodes):
        raise ValueError("exogenous noise must be rows x node_count")
    if noise.shape[0] != N_OBSERVATIONS or not np.isfinite(noise).all():
        raise ValueError("exogenous noise must be finite and contain exactly 512 rows")
    index = {node: i for i, node in enumerate(nodes)}
    coefficients = truth["coefficients"]
    values = np.zeros(noise.shape, dtype=np.float64)
    parents = {node: [] for node in nodes}
    for parent, child in edges:
        parents[child].append(parent)
    for node in order:
        col = index[node]
        values[:, col] = noise[:, col]
        for parent in sorted(parents[node]):
            coefficient = float(coefficients[f"{parent}->{node}"])
            values[:, col] += coefficient * values[:, index[parent]]
    if not np.isfinite(values).all():
        raise FloatingPointError("NONFINITE_OBSERVATIONS")
    sample_sd = values.std(axis=0, ddof=1)
    if not np.isfinite(sample_sd).all():
        raise FloatingPointError("NONFINITE_SAMPLE_SD")
    if np.any(sample_sd <= 0.0):
        raise ValueError("ZERO_SAMPLE_VARIANCE")
    return {"nodes": list(nodes), "rows": values.tolist(),
            "data_sha256": hashlib.sha256(values.tobytes(order="C")).hexdigest(),
            "n_rows": noise.shape[0], "sample_sd": sample_sd.tolist(),
            "observation_source": source,
            "numeric_status": "finite_positive_sample_variance", "same_data_for_all_types_policies": True}


def scm_signature(truth_spec: Mapping[str, object], scm_id: str | None = None) -> str:
    """Equation identity excludes observation noise draws and dataset bytes."""
    return hashlib.sha256(_canonical(dict(truth_spec))).hexdigest()


class EquationSignatureRegistry:
    """Prevent double-counting identical equations as independent SCMs."""
    def __init__(self):
        self._by_signature: dict[str, str] = {}

    def register(self, scm_id: str, signature: str) -> dict:
        if not scm_id or not signature:
            raise ValueError("SCM ID and equation signature are required")
        if signature in self._by_signature:
            return {"accepted": False, "reason": "duplicate_structural_equations",
                    "first_scm_id": self._by_signature[signature]}
        self._by_signature[signature] = scm_id
        return {"accepted": True, "reason": None, "scm_id": scm_id}

"""One explicit TEST_ONLY linear SCM and deterministic observational matrix."""
import numpy as np

from research.budget_aware_refinement.step4c1_scm import simulate_from_exogenous_noise
from .policy_engine import state
from .e2e_fixture import FixtureInput


def make_fixed_fixture() -> tuple[FixtureInput, dict]:
    """Return an explicit hand-specified fixture; this is not a cohort sampler."""
    nodes = ["A", "B", "C", "D", "Z", "X", "M", "Y"]
    edges = [["A", "B"], ["C", "D"], ["Z", "X"], ["Z", "Y"], ["X", "M"], ["M", "Y"]]
    truth_spec = {"nodes": nodes, "topological_order": nodes, "edges": edges,
                  "coefficients": {"A->B": 0.25, "C->D": -0.3, "Z->X": 0.4,
                                   "Z->Y": -0.2, "X->M": 0.7, "M->Y": 0.5},
                  "noise": {"family": "fixed_test_only", "means": dict.fromkeys(nodes, 0.0),
                            "sd": dict.fromkeys(nodes, 1.0)}}
    row = np.arange(512, dtype=np.float64)
    noise = np.column_stack([np.sin(row * (0.013 + j * .002)) +
                             np.cos(row * (0.007 + j * .001)) for j in range(len(nodes))])
    observations = np.asarray(simulate_from_exogenous_noise(truth_spec, noise)["rows"], dtype=np.float64)
    g0 = state([("D", "C"), ("X", "Z"), ("Z", "Y"), ("M", "Y"), ("A", "Y")])
    fixture = FixtureInput(truth_spec, g0, observations, "X", "Y", delta=1, test_only=True)
    return fixture, {"truth": state(edges), "nodes": nodes, "exogenous_noise_source": "fixed trigonometric sequence"}

"""Subprocess helper for actual process termination/restart tests."""
from __future__ import annotations

import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np

from research.budget_aware_refinement.step4c1_pipeline import run_eligible_proposal
from research.budget_aware_refinement.step4c1_proposal import build_structural_proposal
from research.budget_aware_refinement.step4c1_scm import _topological_order


def fixture():
    proposal = build_structural_proposal(cohort="development", master_seed=101,
        proposal_id="f5", attempt=0)
    nodes, edges = proposal["nodes"], proposal["topology_edges"]
    truth = {"nodes": nodes, "topological_order": list(_topological_order(nodes, edges)),
        "edges": edges, "coefficients": {f"{a}->{b}": .5 for a, b in edges},
        "noise": {"family": "fixed_fixture", "means": {node: 0.0 for node in nodes},
                  "sd": {node: 1.0 for node in nodes}}}
    return proposal, {"truth_spec": truth,
        "exogenous_noise": np.random.default_rng(723).normal(size=(512, len(nodes)))}


def main():
    ledger, stop_after = Path(sys.argv[1]), sys.argv[2]
    proposal, payload = fixture()
    hook = (lambda stage: os._exit(29) if stage == stop_after else None) if stop_after != "-" else None
    result = run_eligible_proposal(proposal, ledger, _fixture_payload=payload,
        delta=1, checkpoint_hook=hook, max_rss_bytes=None)
    print(result["status"])


if __name__ == "__main__":
    main()

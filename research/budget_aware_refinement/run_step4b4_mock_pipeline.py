"""Run one deterministic graph/Ridge/recommendation/truth-stub contract fixture."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
from research.budget_aware_refinement.policy_engine import refine
from research.budget_aware_refinement.step4b4_mock_runner import run_pipeline
from integrated_pilot import fit_model
from decision_mvp import static_mean_response


def build_mock_stages() -> dict:
    """Use a deterministic numeric fixture; no SCM-generated observations."""
    nodes = [f"V{i:02d}" for i in range(10)]
    truth_edges = [(nodes[i], nodes[i + 1]) for i in range(9)]
    initial_edges = truth_edges[1:]
    task = (nodes[0], nodes[-1])
    request = {
        "node_ids": nodes,
        "initial_edges": initial_edges,
        "reference_edges": truth_edges,
        "allowed_types": ["FN"],
        "policy_id": "G-FN",
        "budget": 1,
        "gamma": 1,
        "action": task[0],
        "target": task[1],
        "seed": 0,
    }
    r = np.arange(512, dtype=float)[:, None]
    c = np.arange(10, dtype=float)[None, :]
    matrix = np.sin(.013 * r * (c + 1)) + np.cos(.017 * r * (c + 2)) + .07 * c + .0003 * r
    state: dict[str, object] = {}

    def graph():
        result = refine(**request)
        state["final_edges"] = [tuple(edge) for edge in result["final_graph"]]
        return {"node_count": len(nodes), "edge_count": len(state["final_edges"]),
                "policy_status": result.get("status", "OK"), "fixture_only": True}

    def fit():
        model = fit_model(matrix, nodes, set(state["final_edges"]), 1.0)
        state["model"] = model
        return {"rows": int(matrix.shape[0]), "features": int(matrix.shape[1]),
                "model": "existing Ridge fit_model", "input_fixture": "deterministic dummy matrix"}

    def recommend():
        model = state["model"]
        mean = matrix.mean(axis=0)
        sd = matrix.std(axis=0, ddof=1)
        actions = [float(mean[0] + k * sd[0]) for k in (-1, -.5, 0, .5, 1)]
        predictions = [float(static_mean_response(model, task[0], action)[task[1]]) for action in actions]
        state["predictions"] = predictions
        return {"candidate_count": len(actions), "prediction_count": len(predictions),
                "values_are_mock_predictions": True}

    def truth_stub():
        # Explicit test double: it deliberately returns no causal effect/regret.
        return {"evaluator": "deterministic test double", "fixture_only": True,
                "evaluation_performed": False, "effect": None, "regret": None}

    return {"graph": graph, "fit": fit, "recommend": recommend, "truth": truth_stub}


def main() -> None:
    root = Path(__file__).resolve().parent
    ledger = root / "step4b4_mock_pipeline_run_v2.jsonl"
    result = run_pipeline("step4b4-fixed-mock-v2", ledger, build_mock_stages(), rng_key="step4b4-mock-stream-v2")
    print(json.dumps({"result": result, "ledger": ledger.name,
                      "interpretation": "software fixture only; no SCM, effect or regret"}, indent=2))


if __name__ == "__main__":
    main()

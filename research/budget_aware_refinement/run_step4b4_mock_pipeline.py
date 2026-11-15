"""Deterministic integration fixture for runner restart tests (not research data)."""
from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
from research.budget_aware_refinement.policy_engine import refine
from research.budget_aware_refinement.step4b4_mock_runner import recover_jsonl, run_pipeline
from integrated_pilot import fit_model
from decision_mvp import static_mean_response

MOCK_RNG_KEY = "step4c1-fixed-mock-stream-v1"
MOCK_CONFIG = {"fixture": "fixed-dummy-512x10", "ridge_alpha": 1.0,
               "candidate_count": 5, "status": "MOCK_ONLY"}
_NODES = tuple(f"V{i:02d}" for i in range(10))
_TRUTH = tuple((_NODES[i], _NODES[i + 1]) for i in range(9))
_INITIAL = _TRUTH[1:]
_R = np.arange(512, dtype=float)[:, None]
_C = np.arange(10, dtype=float)[None, :]
_MATRIX = np.sin(.013 * _R * (_C + 1)) + np.cos(.017 * _R * (_C + 2)) + .07 * _C + .0003 * _R
MOCK_INPUT_SHA256 = hashlib.sha256(_MATRIX.tobytes() + json.dumps([_NODES, _INITIAL]).encode()).hexdigest()


@dataclass(frozen=True)
class MockStage:
    name: str
    ledger: str
    stop_after: bool = False

    def _prior(self, stage: str) -> dict:
        for event in recover_jsonl(Path(self.ledger)):
            if event.get("event") == f"stage:{stage}" and event.get("status") == "OK":
                return event["output"]
        raise RuntimeError(f"missing verified prerequisite stage {stage}")

    def __call__(self):
        if self.name == "graph":
            result = refine(node_ids=_NODES, initial_edges=_INITIAL, reference_edges=_TRUTH,
                            allowed_types=["FN"], policy_id="G-FN", budget=1, gamma=1,
                            action=_NODES[0], target=_NODES[-1], seed=0)
            output = {"node_ids": list(_NODES), "final_edges": [list(e) for e in result["final_graph"]],
                      "policy_status": result.get("status", "OK"), "fixture_only": True}
        elif self.name == "fit":
            graph = self._prior("graph")
            model = fit_model(_MATRIX, list(_NODES), {tuple(e) for e in graph["final_edges"]}, 1.0)
            output = {"graph_sha256": hashlib.sha256(_canonical(graph["final_edges"])).hexdigest(),
                      "model": model,
                      "input_sha256": MOCK_INPUT_SHA256, "rows": 512, "features": 10}
        elif self.name == "recommend":
            graph = self._prior("graph")
            fit = self._prior("fit")
            if fit["input_sha256"] != MOCK_INPUT_SHA256:
                raise RuntimeError("fit input binding mismatch")
            model = fit["model"]
            mean, sd = _MATRIX.mean(axis=0), _MATRIX.std(axis=0, ddof=1)
            actions = [float(mean[0] + k * sd[0]) for k in (-1, -.5, 0, .5, 1)]
            predictions = [float(static_mean_response(model, _NODES[0], a)[_NODES[-1]]) for a in actions]
            output = {"actions": actions, "predictions": predictions,
                      "fixture_only": True, "deterministic_refit": True}
        else:
            recommendation = self._prior("recommend")
            output = {"evaluator": "test double", "fixture_only": True,
                      "evaluation_performed": False, "effect": None, "regret": None,
                      "recommendation_sha256": hashlib.sha256(_canonical(recommendation)).hexdigest()}
        if self.stop_after:
            import os
            os._exit(73)
        return output


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def build_mock_stages(ledger: Path | None = None, stop_after: str | None = None, *, stop_before: str | None = None) -> dict:
    """Top-level picklable stage callables; downstream steps restore from ledger."""
    names = ("graph", "fit", "recommend", "truth")
    if stop_before is not None:
        if stop_before not in names[1:]:
            raise ValueError("stop_before must name fit, recommend, or truth")
        stop_after = names[names.index(stop_before) - 1]
    if ledger is None:
        ledger = Path("step4c1_mock_fixture.jsonl")
    if stop_after not in (None, *names[:-1]):
        raise ValueError("stop_after must name graph, fit, recommend, or None")
    stages = {}
    for name in names:
        stages[name] = MockStage(name, str(ledger), name == stop_after)
    return stages


def main() -> None:
    root = Path(__file__).resolve().parent
    ledger = root / "step4c1_mock_pipeline_run_v1.jsonl"
    result = run_pipeline("step4c1-fixed-mock-v1", ledger, build_mock_stages(ledger),
                          rng_key=MOCK_RNG_KEY, config=MOCK_CONFIG,
                          input_sha256=MOCK_INPUT_SHA256, isolate_stages=True)
    print(json.dumps({"result": result, "ledger": ledger.name,
                      "interpretation": "mock contract only; not production research"}, indent=2))


if __name__ == "__main__":
    main()

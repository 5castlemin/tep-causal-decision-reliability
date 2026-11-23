"""Emit deterministic hand-graph policy results; never generates an SCM."""
from pathlib import Path

from research.original_objective.policy_engine import Config, run_catalog, save_json, state


def main():
    gt = state([("X", "A"), ("A", "Y"), ("X", "B"), ("B", "Y"), ("T", "U"), ("P", "Q")])
    g0 = state([("A", "Y"), ("X", "B"), ("B", "Y"), ("Q", "P"), ("R", "S")])
    config = Config()
    runs = {str(b): run_catalog(gt, g0, "X", "Y", b, config) for b in range(5)}
    path = Path("research/original_objective/fixture_run_v1.json")
    save_json(path, {"status": "FIXTURE_ONLY_NOT_RESEARCH_RESULT", "config": config.__dict__, "runs": runs})
    print(path)
    for b, result in runs.items():
        print(f"B={b} unique_graphs={len({r['final_hash'] for r in result['strategies']})}/16")


if __name__ == "__main__":
    main()

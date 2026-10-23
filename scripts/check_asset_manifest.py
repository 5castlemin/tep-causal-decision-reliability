"""Check recorded asset claims against frozen config and saved validation."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    audit = json.loads((ROOT / "docs/reproducibility/GRAPH_REPRODUCIBILITY.json").read_text(encoding="utf-8"))
    freeze = json.loads((ROOT / "graphs/final/FREEZE.json").read_text(encoding="utf-8"))
    graphs = audit["graphs"]
    if {g["graph_id"] for g in graphs} != set(freeze["frozen_algorithms"]) or len(graphs) != 7:
        raise ValueError("7개 graph ID 불일치")
    for g in graphs:
        config = ROOT / g["config_path"]
        if hashlib.sha256(config.read_bytes()).hexdigest() != g["config_sha256"]:
            raise ValueError("config hash 불일치")
        if freeze["code"][g["expected_generation_code"]] != g["expected_code_sha256"]:
            raise ValueError("원본 생성 코드 hash 기대값 불일치")
        if not g["generation_code_bytes_available"] and (g["rerun_executed"] or g["frozen_match"] is not None):
            raise ValueError("원본 코드 없이 생성 재현 주장")
    for name in ("original_evaluator.json", "clean_environment.json"):
        result = json.loads((ROOT / "docs/reproducibility/validation" / name).read_text(encoding="utf-8"))
        if set(result["results"]) != set(freeze["frozen_algorithms"]) or not all(x["matched"] for x in result["results"].values()):
            raise ValueError("평가 재현 근거 불일치")
    print("[PASS] Final config·미회수 생성 코드·평가 재현 범위의 기록 정합성")


if __name__ == "__main__":
    main()

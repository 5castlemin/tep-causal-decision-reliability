"""Validate recorded simulator evidence without requiring external simulator code."""
import csv
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent


def validate():
    run = ROOT / "run_20261023_v3"
    result = json.loads((run / "summary.json").read_text(encoding="utf-8"))
    for name, expected in result["csv_sha256"].items():
        assert hashlib.sha256((run / name).read_bytes()).hexdigest() == expected, name
        data = np.loadtxt(run / name, delimiter=",", skiprows=1)
        assert data.shape[1] == 54 and np.isfinite(data).all()
        assert np.all(np.diff(data[:, 0]) > 0)
    normal1 = np.loadtxt(run / "closed_normal_1.csv", delimiter=",", skiprows=1)
    normal2 = np.loadtxt(run / "closed_normal_2.csv", delimiter=",", skiprows=1)
    assert np.array_equal(normal1, normal2) and result["repeat_exact"]
    assert result["runs"]["manual_intervention"]["shutdown"]
    assert result["runs"]["closed_fault"]["disturbances_zero_after_reset"]
    assert not result["runs"]["closed_fault"]["initial_observation_restored"]
    with (ROOT / "benchmark_reference_mapping.csv").open(encoding="utf-8-sig") as f:
        mapping = {r["benchmark_variable_name"]: r["original_tep_variable"] for r in csv.DictReader(f)}
    assert mapping["X32"] == "XMV(10)" and mapping["X9"] == "XMEAS(9)"
    assert result["compatibility"] == "VARIABLE_MAPPING_ONLY_NOT_EFFECT_ORACLE"
    print("[PASS] 실행 CSV hash·반복·시계열·shutdown/reset 한계·mapping 검증")
    print("SIMULATOR FEASIBILITY: PARTIAL — 종료·reset·모델 호환성 관문 미해결")


if __name__ == "__main__":
    validate()

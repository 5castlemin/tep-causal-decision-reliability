"""New adapter for the recovered original Step 6 evaluator, not discovery code.

The original evaluator stays in a user-provided, checksum-pinned ZIP. A minimal
explicit config supplies variable names; U-rule scores are not reproduced here.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
import types
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
ZIP_SHA = "28824bc2a98acb77ce8fc5f56439ea4910f7dc9f22ed45b7d1391f7f703f6b22"
CODE_SHA = "5d120b8404b1a897e8fd69a022e749815f892c59751b6f05bbbd9fc0beba4ef2"
GT_SHA = "238542dbdde50887b5944fb3acc64a792b19a0c56bbfa06e3b267261f2fe6c43"
ALGOS = {"pc": "PC-stable", "boss": "BOSS", "directlingam": "DirectLiNGAM", "dagma": "DAGMA",
         "pcmciplus": "PCMCI+", "varlingam": "VarLiNGAM", "dynotears": "DYNOTEARS"}


def checked(data, expected):
    if hashlib.sha256(data).hexdigest() != expected:
        raise ValueError("입력 SHA-256 불일치")
    return data


def reproduce(archive: Path, gt_path: Path):
    checked(archive.read_bytes(), ZIP_SHA)
    checked(gt_path.read_bytes(), GT_SHA)
    with zipfile.ZipFile(archive) as z:
        code = checked(z.read("evaluation/evaluator.py"), CODE_SHA)
    variables = pd.read_csv(ROOT / "graphs/final/variables.csv").variable.tolist()
    common = types.ModuleType("common")
    common.config = types.SimpleNamespace(VARS=variables, CONTROL_LOOPS=())
    previous = sys.modules.get("common")
    sys.modules["common"] = common
    module = types.ModuleType("recovered_step6_evaluator")
    try:
        exec(compile(code, "recovered_step6/evaluation/evaluator.py", "exec"), module.__dict__)
    finally:
        if previous is None:
            del sys.modules["common"]
        else:
            sys.modules["common"] = previous
    gt = module.load_gt(str(gt_path))
    table = pd.read_csv(ROOT / "docs/audit/step6_main_table.csv")
    result = {}
    for algo, label in ALGOS.items():
        folder = ROOT / "graphs/final/graphs" / algo
        matrices = [pd.read_csv(folder / name, index_col=0) for name in ("A_dir.csv", "A_unres.csv")]
        for matrix in matrices:
            if matrix.index.tolist() != variables or matrix.columns.tolist() != variables:
                raise ValueError("그래프 변수 순서 불일치")
        scores = module.score_graph(*(m.values for m in matrices), gt, control_pairs=())
        row = table[(table.algo == label) & (table.stage == "final")].iloc[0]
        values = dict(sk_F1=scores["skeleton"]["F1"], dS_F1=scores["dir_strict"]["F1"], SHD_S=scores["shd_strict"]["SHD"])
        if not all(np.isclose(value, row[key], rtol=0, atol=1e-12) for key, value in values.items()):
            raise ValueError(f"Step 6 불일치: {algo}")
        result[algo] = dict(matched=True, **values)
    return dict(scope="ORIGINAL_EVALUATOR_STRICT_METRICS_ONLY_NOT_DISCOVERY_RERUN",
                archive_sha256=ZIP_SHA, evaluator_sha256=CODE_SHA, gt_sha256=GT_SHA,
                python=platform.python_version(), numpy=np.__version__, pandas=pd.__version__, results=result)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--step6-zip", type=Path, required=True)
    p.add_argument("--gt", type=Path, default=ROOT / "data/local/TEGroundTruth.txt")
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    if a.output.exists():
        raise FileExistsError("출력을 덮어쓰지 않습니다")
    result = reproduce(a.step6_zip, a.gt)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print("[PASS] 회수한 원본 평가기로 Final 7개 엄격 지표 일치 (인과발견 재실행 아님)")

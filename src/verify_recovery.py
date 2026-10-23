"""복사된 원본의 입력 정합성과 Step 6 최종 구조 점수를 독립 대조한다."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
ALGOS = {"pc": "PC-stable", "boss": "BOSS", "directlingam": "DirectLiNGAM",
         "dagma": "DAGMA", "pcmciplus": "PCMCI+", "varlingam": "VarLiNGAM",
         "dynotears": "DYNOTEARS"}
EXPECTED_HASHES = {
    "datasetTE.csv": "52ae445b4355201db9591822282381c8de861afe49bdbc9452db08b01e7d3711",
    "TEGroundTruth.txt": "238542dbdde50887b5944fb3acc64a792b19a0c56bbfa06e3b267261f2fe6c43",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def score(a: np.ndarray, u: np.ndarray, gt: np.ndarray) -> dict:
    n = len(a)
    iu = np.triu_indices(n, 1)
    sk = (a | a.T | u)[iu]
    truth = (gt | gt.T)[iu]
    tp_sk = int((sk & truth).sum())
    n_pred = int(sk.sum())
    n_gt = int(truth.sum())
    f_sk = 2 * tp_sk / (n_pred + n_gt) if n_pred + n_gt else 0.0
    correct = int((a & gt).sum())
    f_dir = 2 * correct / (n_pred + n_gt) if n_pred + n_gt else 0.0
    missing = int((truth & ~sk).sum())
    extra = int((sk & ~truth).sum())
    reversed_ = int((a.T & gt).sum())
    unresolved = int((u[iu] & truth).sum())
    return {"pairs": n_pred, "confirmed": int(a.sum()), "unresolved": int(u[iu].sum()),
            "skeleton_f1": f_sk, "strict_directed_f1": f_dir,
            "shd": missing + extra + reversed_ + unresolved}


def main() -> None:
    local = ROOT / "data" / "local"
    for name, expected in EXPECTED_HASHES.items():
        if sha(local / name) != expected:
            raise RuntimeError(f"입력 해시 불일치: {name}")
    data = pd.read_csv(local / "datasetTE.csv")
    variables = pd.read_csv(ROOT / "graphs" / "final" / "variables.csv").variable.tolist()
    if data.columns[0].startswith("Unnamed"):
        data = data.iloc[:, 1:]
    if data.shape != (1499, 31) or data.columns.tolist() != variables or data.isna().any().any():
        raise RuntimeError("데이터 크기·순서·결측 검증 실패")
    raw = np.loadtxt(local / "TEGroundTruth.txt", dtype=int)
    if raw.shape != (33, 33):
        raise RuntimeError("원본 GT 크기 불일치")
    keep = [int(v[1:]) - 1 for v in variables]
    gt = raw[np.ix_(keep, keep)].astype(bool)
    if int(gt.sum()) != 28 or np.any(np.diag(gt)):
        raise RuntimeError("평가 GT 간선 수·대각 불일치")

    table = pd.read_csv(ROOT / "docs" / "audit" / "step6_main_table.csv")
    results = {}
    for algo, label in ALGOS.items():
        graph_dir = ROOT / "graphs" / "final" / "graphs" / algo
        ad = pd.read_csv(graph_dir / "A_dir.csv", index_col=0)
        un = pd.read_csv(graph_dir / "A_unres.csv", index_col=0)
        if list(ad.index) != variables or list(ad.columns) != variables or list(un.index) != variables or list(un.columns) != variables:
            raise RuntimeError(f"변수 순서 불일치: {algo}")
        a, u = ad.to_numpy(), un.to_numpy()
        if not (np.isin(a, [0, 1]).all() and np.isin(u, [0, 1]).all() and np.array_equal(u, u.T)
                and not np.any(a & a.T) and not np.any((a | a.T) & u)):
            raise RuntimeError(f"행렬 규약 불일치: {algo}")
        actual = score(a.astype(bool), u.astype(bool), gt)
        row = table[(table.algo == label) & (table.stage == "final")]
        if len(row) != 1:
            raise RuntimeError(f"Step 6 최종 행 없음: {label}")
        row = row.iloc[0]
        expected = {"pairs": row.n_pairs, "confirmed": row.n_dir, "unresolved": row.n_unres,
                    "skeleton_f1": row.sk_F1, "strict_directed_f1": row.dS_F1, "shd": row.SHD_S}
        for key in actual:
            if not np.isclose(actual[key], expected[key], rtol=0, atol=1e-12):
                raise RuntimeError(f"Step 6 대조 실패: {algo}/{key}: {actual[key]} != {expected[key]}")
        results[algo] = actual

    out = {"status": "PASS", "dataset_shape": [1499, 31], "raw_gt_shape": [33, 33],
           "evaluation_gt_shape": [31, 31], "evaluation_gt_edges": 28,
           "gt_use": "구조 평가 대조만 사용; 모델 학습·방향 보정 금지",
           "step6_metric_definition": "skeleton=무방향 쌍 F1; strict direction=확정 정방향 TP/전체 예측 쌍; SHD=누락+추가+역방향+미확정",
           "results": results}
    path = ROOT / "experiments" / "pilot" / "logs" / "recovery_validation.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print("[PASS] 데이터·GT 및 7개 최종 그래프의 Step 6 점수 독립 대조")


if __name__ == "__main__":
    main()

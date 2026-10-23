"""정상 데이터의 공통 선형 Ridge 수치 적합 파일럿.

이 스크립트의 검증 MSE는 관측 부모를 사용한 one-step 예측 진단이다.
인과효과·개입·복구·안전 평가가 아니다.
"""

from __future__ import annotations

import hashlib
import json
import platform
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
ELIGIBLE = ["pc", "boss", "directlingam", "dagma", "varlingam", "dynotears"]
PILOT = ["pc", "directlingam", "boss"]


def filehash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_parents(algo: str, names: list[str]) -> dict[str, list[tuple[str, int]]]:
    d = ROOT / "graphs" / "final" / "graphs" / algo
    out = {name: [] for name in names}
    if algo in {"varlingam", "dynotears"}:
        edges = pd.read_csv(d / "lag_graph_edges.csv")
        if (edges.mark != "-->").any():
            raise ValueError(f"미확정 시차 mark를 자동 방향화할 수 없음: {algo}")
        for e in edges.itertuples():
            if e.source not in out or e.target not in out or not 0 <= int(e.lag) <= 5:
                raise ValueError(f"시차 간선 형식 오류: {algo}")
            out[e.target].append((e.source, int(e.lag)))
    else:
        a = pd.read_csv(d / "A_dir.csv", index_col=0)
        if list(a.index) != names or list(a.columns) != names:
            raise ValueError(f"변수 순서 오류: {algo}")
        for j, target in enumerate(names):
            out[target] = [(names[i], 0) for i in np.flatnonzero(a.iloc[:, j].to_numpy())]
    for target in out:
        if len(out[target]) != len(set(out[target])):
            raise ValueError(f"중복 parent-lag: {algo}/{target}")
    return out


def scaler(x: np.ndarray, train_targets: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    mean = x[train_targets].mean(axis=0)
    std = x[train_targets].std(axis=0, ddof=0)
    if not np.isfinite(mean).all() or not np.isfinite(std).all() or (std == 0).any():
        raise ValueError("비정상 값 또는 상수 열: 임의 보정 금지")
    return mean, std


def design(x: np.ndarray, target_rows: np.ndarray, parents: list[tuple[str, int]], index: dict[str, int]) -> np.ndarray:
    if not parents:
        return np.empty((len(target_rows), 0))
    return np.column_stack([x[target_rows - lag, index[source]] for source, lag in parents])


def fit_ridge(X: np.ndarray, y: np.ndarray, alpha: float) -> tuple[np.ndarray, float]:
    if len(X) != len(y) or len(y) == 0:
        raise ValueError("학습 행 불일치")
    if X.shape[1] == 0:
        return np.empty(0), float(y.mean())
    xm, ym = X.mean(axis=0), float(y.mean())
    xc, yc = X - xm, y - ym
    beta = np.linalg.solve(xc.T @ xc + len(X) * alpha * np.eye(X.shape[1]), xc.T @ yc)
    return beta, float(ym - xm @ beta)


def score_alpha(data: np.ndarray, names: list[str], parents_by_algo: dict, alpha: float, folds: list[dict]) -> tuple[float, int]:
    index = {v: i for i, v in enumerate(names)}
    target_rows = np.arange(5, 1200)
    losses = []
    for fold in folds:
        tr0, tr1 = fold["train_half_open"]
        va0, va1 = fold["validation_half_open"]
        tr, va = target_rows[tr0:tr1], target_rows[va0:va1]
        if not len(tr) or not len(va) or tr.max() >= va.min():
            raise ValueError("시간순 fold 오류")
        mean, std = scaler(data, tr)
        z = (data - mean) / std
        for algo in ELIGIBLE:
            for target, parents in parents_by_algo[algo].items():
                if not parents:
                    continue
                Xtr = design(z, tr, parents, index)
                Xva = design(z, va, parents, index)
                b, intercept = fit_ridge(Xtr, z[tr, index[target]], alpha)
                losses.append(float(np.mean((z[va, index[target]] - (Xva @ b + intercept)) ** 2)))
    return float(np.mean(losses)), len(losses)


def main() -> None:
    freeze = json.loads((ROOT / "docs" / "audit" / "pre_fitting_final_freeze.json").read_text(encoding="utf-8"))
    ridge = json.loads((ROOT / "docs" / "audit" / "ridge_policy_final.json").read_text(encoding="utf-8"))
    rows = json.loads((ROOT / "docs" / "audit" / "fitting_row_policy.json").read_text(encoding="utf-8"))
    if freeze["pcmciplus_status"] != "KEEP_BLOCKED_IDENTIFICATION" or rows["max_lag"] != 5:
        raise ValueError("동결된 그래프 예외 또는 시차 정책이 변경됨")
    if rows["common_target_rows"] != [5, 1498] or rows["train_rows"] != [5, 1199] or rows["validation_rows"] != [1200, 1498]:
        raise ValueError("동결된 학습·검증 구간과 불일치")
    if ridge["method"] != "RIDGE" or ridge["alpha_scope"] != "하나의 공통 alpha를 6개 eligible graph의 모든 비-root equation에서 선택; graph별 임의 변경 금지":
        raise ValueError("공통 alpha 정책과 불일치")
    data_path = ROOT / "data" / "local" / "datasetTE.csv"
    if filehash(data_path) != freeze["dataset_sha256"]:
        raise ValueError("학습 데이터 SHA-256 불일치")
    df = pd.read_csv(data_path)
    if not df.columns[0].startswith("Unnamed"):
        raise ValueError("예상한 무명 인덱스 열이 없음; 열을 임의 삭제하지 않음")
    df = df.iloc[:, 1:]
    names = pd.read_csv(ROOT / "graphs" / "final" / "variables.csv").variable.tolist()
    if df.shape != (1499, 31) or df.columns.tolist() != names or df.isna().any().any():
        raise ValueError("학습 데이터 크기·변수 순서·결측 오류")
    data = df.to_numpy(dtype=float)
    parents_by_algo = {a: load_parents(a, names) for a in ELIGIBLE}
    folds = ridge["inner_folds_relative_to_train"]
    alpha_losses = {}
    for alpha in ridge["alpha_grid"]:
        loss, count = score_alpha(data, names, parents_by_algo, float(alpha), folds)
        alpha_losses[str(alpha)] = {"mean_standardized_mse": loss, "equation_fold_count": count}
        print(f"alpha={alpha}: 평균 표준화 MSE={loss:.6f} ({count}식×fold)", flush=True)
    # 작은 차이는 같은 손실로 취급하지 않고, 정확히 같은 값이면 더 강한 규제를 선택한다.
    selected = min((float(v["mean_standardized_mse"]), -float(k), float(k)) for k, v in alpha_losses.items())[2]
    train = np.arange(5, 1200)
    valid = np.arange(1200, 1499)
    mean, std = scaler(data, train)
    z = (data - mean) / std
    index = {v: i for i, v in enumerate(names)}
    result_dir = ROOT / "experiments" / "pilot" / "results"
    result_dir.mkdir(parents=True, exist_ok=True)
    summaries = {}
    for algo in PILOT:
        parent_map = parents_by_algo[algo]
        coefficients = []
        train_resid = np.empty((len(train), len(names)))
        valid_resid = np.empty((len(valid), len(names)))
        for target in names:
            j = index[target]
            parents = parent_map[target]
            Xtr, Xva = design(z, train, parents, index), design(z, valid, parents, index)
            b, intercept = fit_ridge(Xtr, z[train, j], selected)
            train_resid[:, j] = z[train, j] - (Xtr @ b + intercept)
            valid_resid[:, j] = z[valid, j] - (Xva @ b + intercept)
            coefficients.append({"target": target, "intercept_standardized": intercept,
                                 "parents": [{"source": source, "lag": lag, "coefficient_standardized": float(value)}
                                             for (source, lag), value in zip(parents, b)]})
        artifact = {"algorithm": algo, "representation": "STATIC_CONFIRMED", "family": "LINEAR_ADDITIVE",
                    "fit": "RIDGE", "alpha": selected, "train_rows": [5, 1199], "validation_rows": [1200, 1498],
                    "scaler_mean": dict(zip(names, mean.tolist())), "scaler_std": dict(zip(names, std.tolist())),
                    "equations": coefficients, "status": "FIT_OK_NUMERICAL_NOT_CAUSAL_VALIDATION"}
        artifact_path = result_dir / f"{algo}__STATIC_CONFIRMED__LINEAR_RIDGE__COMMON_TARGET_ROWS_V1.json"
        artifact_path.write_text(json.dumps(artifact, ensure_ascii=False, indent=2), encoding="utf-8")
        pd.DataFrame(train_resid, columns=names).assign(target_row=train).to_csv(result_dir / f"{algo}_train_residuals.csv", index=False)
        pd.DataFrame(valid_resid, columns=names).assign(target_row=valid).to_csv(result_dir / f"{algo}_validation_one_step_residuals.csv", index=False)
        corr = np.corrcoef(train_resid, rowvar=False)
        off_diag = np.abs(corr[np.triu_indices(len(names), 1)])
        lag_corr = [float(np.corrcoef(train_resid[:-1, j], train_resid[1:, j])[0, 1])
                    for j in range(len(names))]
        diagnostics = {
            "train_residual_mean_by_variable": dict(zip(names, train_resid.mean(axis=0).tolist())),
            "train_residual_variance_by_variable": dict(zip(names, train_resid.var(axis=0).tolist())),
            "train_median_absolute_offdiagonal_residual_correlation": float(np.median(off_diag)),
            "train_median_absolute_lag1_residual_autocorrelation": float(np.median(np.abs(lag_corr))),
            "validation_one_step_mse_by_variable": dict(zip(names, np.mean(valid_resid ** 2, axis=0).tolist())),
        }
        (result_dir / f"{algo}_residual_diagnostics.json").write_text(
            json.dumps(diagnostics, ensure_ascii=False, indent=2), encoding="utf-8")
        summaries[algo] = {"non_root_equations": sum(bool(v) for v in parent_map.values()),
                           "confirmed_parent_links": sum(len(v) for v in parent_map.values()),
                           "train_standardized_mse_all_variables": float(np.mean(train_resid ** 2)),
                           "validation_standardized_mse_all_variables": float(np.mean(valid_resid ** 2)),
                           "validation_standardized_mse_nonroot": float(np.mean(valid_resid[:, [index[v] for v in names if parent_map[v]]] ** 2)),
                           "train_median_absolute_residual_correlation": diagnostics["train_median_absolute_offdiagonal_residual_correlation"],
                           "train_median_absolute_lag1_residual_autocorrelation": diagnostics["train_median_absolute_lag1_residual_autocorrelation"],
                           "artifact_sha256": filehash(artifact_path)}
    summary = {"status": "NORMAL_OBSERVATIONAL_FIT_ONLY", "pilot_graphs": PILOT,
               "common_alpha_selection_graphs": ELIGIBLE, "alpha_losses": alpha_losses,
               "selected_alpha": selected, "train_rows": [5, 1199], "train_count": len(train),
               "validation_rows": [1200, 1498], "validation_count": len(valid),
               "standardization": "각 fold 및 최종 train 구간에서만 평균·표준편차 추정; ddof=0",
               "prediction": "관측 부모를 사용한 one-step 검증; rollout/개입 결과 아님",
               "dataset_sha256": filehash(data_path), "numpy_version": np.__version__,
               "pandas_version": pd.__version__, "python_version": platform.python_version(),
               "random_seed": ridge["random_seed"], "results": summaries,
               "intervention_effect": None, "recovery": None, "safety": None}
    (ROOT / "experiments" / "pilot" / "logs" / "normal_fit_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[PASS] 공통 alpha={selected}; 정적 3개 정상상태 수치 적합만 완료", flush=True)


if __name__ == "__main__":
    main()

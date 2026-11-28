"""Final saved-output-only correction/reaggregation for Supplementary S1/S2.

This module intentionally reads the ignored, already-created unit result CSVs.
It never reconstructs SCMs or observations and never invokes a policy/evaluator.
"""
from __future__ import annotations

import csv
import hashlib
import inspect
import json
import os
import sys
import argparse
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / "outputs"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
REPS = 10_000
SEED = 2026112601
TOL = 1e-12
FULL = "M1+M2+M3+M4"


def read_csv(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows):
    rows = list(rows)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        if not rows:
            return
        w = csv.DictWriter(f, fieldnames=list(dict.fromkeys(k for r in rows for k in r)))
        w.writeheader()
        w.writerows(rows)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def common_bootstrap(rows, policy_pairs, value="regret", seed=SEED):
    out = []
    for cohort in ("C_DEVELOPMENT", "C_HELDOUT"):
        subset = [r for r in rows if r["cohort"] == cohort and r["target_delta"] == "original"
                  and float(r["gamma"]) == .2 and int(float(r["budget"])) == 2]
        by = {(r["scm_id"], r["policy"]): float(r[value]) for r in subset}
        ids = sorted({r["scm_id"] for r in subset})
        ix = np.random.default_rng(seed).integers(0, len(ids), size=(REPS, len(ids)))
        for a, b, label in policy_pairs:
            d = np.asarray([by[(sid, a)] - by[(sid, b)] for sid in ids], dtype=float)
            boot = d[ix].mean(axis=1)
            out.append({"cohort": cohort, "condition": "original_target_gamma_0.2_B2",
                        "contrast": label, "source_policy_a": a, "source_policy_b": b,
                        "mean_difference": float(d.mean()), "median_difference": float(np.median(d)),
                        "ci95_low": float(np.quantile(boot, .025)),
                        "ci95_high": float(np.quantile(boot, .975)),
                        "better": int((d < -TOL).sum()), "worse": int((d > TOL).sum()),
                        "tie": int((np.abs(d) <= TOL).sum()), "n": len(ids),
                        "bootstrap_seed": seed, "bootstrap_replicates": REPS,
                        "shared_index_set": "cohort-level; all contrasts",
                        "interval": "pointwise paired SCM percentile bootstrap"})
    return out


def objective_table(rows):
    chosen = ["S0", FULL, "M4", "M2+M4"]
    out = []
    for cohort in ("C_DEVELOPMENT", "C_HELDOUT"):
        for gamma in (0., .05, .2, .5, 1.):
            for policy in chosen:
                rr = [r for r in rows if r["cohort"] == cohort and r["policy"] == policy
                      and int(float(r["budget"])) == 2 and r["target_delta"] == "original"
                      and float(r["gamma"]) == gamma]
                reg = np.asarray([float(r["regret"]) for r in rr])
                actions = [float(r["predicted_k"]) for r in rr]
                out.append({"cohort": cohort, "gamma": gamma, "policy": policy, "n_scm": len(rr),
                            "mean_regret": float(reg.mean()), "median_regret": float(np.median(reg)),
                            "action_distribution": json.dumps({str(k): actions.count(k) for k in sorted(set(actions))}, sort_keys=True),
                            "mean_action_change_vs_s0": ""})
    # Direct unit-level action agreement for Full Greedy, M4 and other policies.
    for row in out:
        cohort, gamma, policy = row["cohort"], float(row["gamma"]), row["policy"]
        if policy == "S0":
            continue
        cur = {(r["scm_id"]): float(r["predicted_k"]) for r in rows if r["cohort"] == cohort
               and r["policy"] == policy and int(float(r["budget"])) == 2
               and r["target_delta"] == "original" and float(r["gamma"]) == gamma}
        base = {r["scm_id"]: float(r["predicted_k"]) for r in rows if r["cohort"] == cohort
                and r["policy"] == "S0" and int(float(r["budget"])) == 2
                and r["target_delta"] == "original" and float(r["gamma"]) == gamma}
        row["action_agreement_with_s0"] = sum(cur[k] == base[k] for k in cur)
        row["action_changed_vs_s0"] = len(cur) - row["action_agreement_with_s0"]
    return out


def effect_diagnostics(rows):
    out = []
    for cohort in ("C_DEVELOPMENT", "C_HELDOUT"):
        rr = [r for r in rows if r["cohort"] == cohort and r["target_delta"] == "original"
              and float(r["gamma"]) == .2 and int(float(r["budget"])) == 2]
        for policy in ("S0", FULL, "M4", "M2+M4", "ADAPTIVE_M4_BLOCKER_AWARE", "REFERENCE_GRAPH"):
            source = rows if policy == "REFERENCE_GRAPH" else rr
            xs = [r for r in source if r["cohort"] == cohort and r["policy"] == policy
                  and r["target_delta"] == "original" and float(r["gamma"]) == .2
                  and int(float(r["budget"])) == (0 if policy == "REFERENCE_GRAPH" else 2)]
            slope_err = [abs(float(r["estimated_slope"]) - float(r["true_slope"])) for r in xs]
            sign_ok = [np.sign(float(r["estimated_slope"])) == np.sign(float(r["true_slope"])) for r in xs]
            matched = [float(r["predicted_k"]) == float(r["true_optimal_k"]) for r in xs]
            out.append({"cohort": cohort, "policy": policy, "n_scm": len(xs),
                        "total_effect_sign_accuracy_zero_as_category": float(np.mean(sign_ok)),
                        "mean_abs_signed_slope_error": float(np.mean(slope_err)),
                        "mean_absolute_magnitude_error_not_available": "",
                        "predicted_action_matches_canonical_grid_optimum": float(np.mean(matched))})
    return out


def action_quality(rows, optimum_rows):
    opt = {(r["cohort"], r["scm_id"], r["target_delta"], float(r["gamma"])): float(r["optimal_k_set"])
           for r in optimum_rows}
    out = []
    for cohort in ("C_DEVELOPMENT", "C_HELDOUT"):
        for policy in ("S0", FULL, "M4", "M2+M4", "ADAPTIVE_M4_BLOCKER_AWARE"):
            rr = [r for r in rows if r["cohort"] == cohort and r["policy"] == policy
                  and int(float(r["budget"])) == 2 and r["target_delta"] == "original" and float(r["gamma"]) == .2]
            signed_ok = [np.sign(float(r["estimated_slope"])) == np.sign(float(r["true_slope"])) for r in rr]
            action_ok = [float(r["predicted_k"]) == opt[(cohort, r["scm_id"], "original", .2)] for r in rr]
            interior = [r for r in rr if 0 < abs(opt[(cohort, r["scm_id"], "original", .2)]) < 1]
            out.append({"cohort": cohort, "policy": policy, "n_scm": len(rr),
                        "sign_correct_action_incorrect_n": sum(a and not b for a, b in zip(signed_ok, action_ok)),
                        "sign_incorrect_action_correct_n": sum((not a) and b for a, b in zip(signed_ok, action_ok)),
                        "canonical_grid_action_agreement_n": sum(action_ok),
                        "canonical_grid_action_agreement": float(np.mean(action_ok)) if rr else None,
                        "nonzero_interior_optimum_n": len(interior),
                        "interior_optimum_mean_regret": float(np.mean([float(r["regret"]) for r in interior])) if interior else None,
                        "interior_optimum_action_agreement_n": sum(float(r["predicted_k"]) == float(r["true_optimal_k"]) for r in interior),
                        "interior_optimum_action_agreement": float(np.mean([float(r["predicted_k"]) == float(r["true_optimal_k"]) for r in interior])) if interior else None})
    # The reference-graph learner is a diagnostic at its saved B=0 row.
    for cohort in ("C_DEVELOPMENT", "C_HELDOUT"):
        for gamma in (0., .2):
            rr = [r for r in rows if r["cohort"] == cohort and r["policy"] == "REFERENCE_GRAPH"
                  and int(float(r["budget"])) == 0 and r["target_delta"] == "original" and float(r["gamma"]) == gamma]
            agreements = [float(r["predicted_k"]) == opt[(cohort, r["scm_id"], "original", gamma)] for r in rr]
            out.append({"cohort": cohort, "policy": "REFERENCE_GRAPH", "gamma": gamma, "n_scm": len(rr),
                        "canonical_grid_action_agreement_n": sum(agreements),
                        "canonical_grid_action_agreement": float(np.mean(agreements)) if rr else None,
                        "note": "reference-graph diagnostic; saved B=0 row"})
    return out


def parse_numeric(rows, keys):
    for r in rows:
        for k in keys:
            if k in r and r[k] not in ("", None):
                r[k] = float(r[k])
    return rows


def ranks(v):
    v = np.asarray(v, dtype=float)
    order = np.argsort(v, kind="mergesort")
    result = np.empty(len(v), dtype=float)
    i = 0
    while i < len(v):
        j = i + 1
        while j < len(v) and v[order[j]] == v[order[i]]:
            j += 1
        result[order[i:j]] = (i + j - 1) / 2 + 1
        i = j
    return result


def weighted_spearman(x, y, w):
    x, y, w = np.asarray(x, float), np.asarray(y, float), np.asarray(w, float)
    good = np.isfinite(x) & np.isfinite(y) & np.isfinite(w) & (w > 0)
    if good.sum() < 3:
        return None
    rx, ry, ww = ranks(x[good]), ranks(y[good]), w[good]
    dx, dy = rx - np.average(rx, weights=ww), ry - np.average(ry, weights=ww)
    den = float(np.sqrt(np.sum(ww * dx * dx) * np.sum(ww * dy * dy)))
    return float(np.sum(ww * dx * dy) / den) if den else None


def shared_metric_bootstrap(graphs, seed=2026112602):
    names = ("skeleton_f1", "directed_f1", "directed_shd", "atomic_error_count",
             "task_error_count", "task_error_rate", "xy_path", "abs_effect_magnitude_error")
    result = []
    rng = np.random.default_rng(seed)
    for cohort in ("C_DEVELOPMENT", "C_HELDOUT"):
        rr = [r for r in graphs if r["cohort"] == cohort]
        by = defaultdict(list)
        for r in rr:
            by[r["scm_id"]].append(r)
        ids = sorted(by)
        draws = rng.integers(0, len(ids), size=(REPS, len(ids)))
        for metric in names:
            x = [float(r[metric]) if r.get(metric) not in ("", None) else np.nan for r in rr]
            y = [float(r["regret"]) for r in rr]
            w = [1 / len(by[r["scm_id"]]) for r in rr]
            point = weighted_spearman(x, y, w)
            boot = []
            for draw in draws:
                bx, byy, bw = [], [], []
                for j in draw:
                    cluster = by[ids[j]]
                    wt = 1 / len(cluster)
                    for r in cluster:
                        value = r.get(metric)
                        bx.append(float(value) if value not in ("", None) else np.nan)
                        byy.append(float(r["regret"]))
                        bw.append(wt)
                v = weighted_spearman(bx, byy, bw)
                if v is not None:
                    boot.append(v)
            result.append({"cohort": cohort, "metric": metric, "n_scm": len(ids),
                           "spearman_scm_balanced": point,
                           "ci95_low": float(np.quantile(boot, .025)) if boot else None,
                           "ci95_high": float(np.quantile(boot, .975)) if boot else None,
                           "bootstrap_replicates_valid": len(boot), "bootstrap_seed": seed,
                           "shared_index_set": "cohort-level; all metrics",
                           "interval": "pointwise SCM bootstrap; weighted midrank Pearson"})
    return result


def nested_model_validation(graphs):
    # Reuse the already-saved structural features and the contract's frozen
    # grouped folds, SCM weights, ridge implementation and alpha candidates.
    from research.final_supplementary_validation.analyze_supplementary import (
        fit_ridge, grouped_folds, regression_metrics, weights_by_scm,
    )
    feat = {
        "B_original": ["n_nodes", "skeleton_precision", "skeleton_recall", "skeleton_f1",
                       "directed_precision", "directed_recall", "directed_f1", "directed_shd", "atomic_error_count"],
        "E_nested": ["n_nodes", "skeleton_precision", "skeleton_recall", "skeleton_f1",
                     "directed_precision", "directed_recall", "directed_f1", "directed_shd", "atomic_error_count",
                     "task_error_count", "task_fn", "task_fp", "task_rev", "task_unres", "task_support"],
        "F_nested": ["n_nodes", "skeleton_precision", "skeleton_recall", "skeleton_f1",
                     "directed_precision", "directed_recall", "directed_f1", "directed_shd", "atomic_error_count",
                     "task_error_count", "task_fn", "task_fp", "task_rev", "task_unres", "task_support", "xy_path"],
    }
    models = {}
    for cohort in ("C_DEVELOPMENT", "C_HELDOUT"):
        for r in graphs:
            if r["cohort"] == cohort:
                for c in set(k for cols in feat.values() for k in cols) | {"regret"}:
                    if r.get(c) not in ("", None):
                        r[c] = float(r[c])
    dev = [r for r in graphs if r["cohort"] == "C_DEVELOPMENT"]
    held = [r for r in graphs if r["cohort"] == "C_HELDOUT"]
    for name, cols in feat.items():
        scores = {a: [] for a in (.01, .1, 1., 10., 100.)}
        for tr, va in grouped_folds(dev):
            y = np.array([r["regret"] for r in tr]); wt = weights_by_scm(tr)
            yv = np.array([r["regret"] for r in va]); wv = weights_by_scm(va)
            x = np.array([[r[c] if r.get(c) is not None else np.nan for c in cols] for r in tr], float)
            xv = np.array([[r[c] if r.get(c) is not None else np.nan for c in cols] for r in va], float)
            med = np.nanmedian(x, axis=0); med = np.where(np.isfinite(med), med, 0)
            x = np.where(np.isfinite(x), x, med); xv = np.where(np.isfinite(xv), xv, med)
            for a in scores:
                pred = np.maximum(0, fit_ridge(x, y, wt, a)(xv))
                scores[a].append(float(np.average(np.abs(yv - pred), weights=wv)))
        alpha = min(scores, key=lambda a: np.mean(scores[a]))
        y = np.array([r["regret"] for r in dev]); w = weights_by_scm(dev)
        yh = np.array([r["regret"] for r in held]); wh = weights_by_scm(held)
        x = np.array([[r[c] if r.get(c) is not None else np.nan for c in cols] for r in dev], float)
        xh = np.array([[r[c] if r.get(c) is not None else np.nan for c in cols] for r in held], float)
        med = np.nanmedian(x, axis=0); med = np.where(np.isfinite(med), med, 0)
        x = np.where(np.isfinite(x), x, med); xh = np.where(np.isfinite(xh), xh, med)
        pred = np.maximum(0, fit_ridge(x, y, w, alpha)(xh))
        models[name] = {"alpha": alpha, "metrics": regression_metrics(yh, pred, wh),
                        "per_scm_abs_errors": {r["scm_id"]: [] for r in held}, "predictions": []}
        for r, p in zip(held, pred):
            models[name]["per_scm_abs_errors"][r["scm_id"]].append(abs(r["regret"] - float(p)))
            models[name]["predictions"].append({"scm_id": r["scm_id"], "graph_hash": r["structural_graph_hash"], "prediction": float(p)})
    ids = sorted({r["scm_id"] for r in held}); ix = np.random.default_rng(2026112602 + 100).integers(0, len(ids), size=(REPS, len(ids)))
    contrasts = []
    for a, b in (("B_original", "E_nested"), ("E_nested", "F_nested"), ("B_original", "F_nested")):
        d = np.asarray([np.mean(models[a]["per_scm_abs_errors"][sid]) - np.mean(models[b]["per_scm_abs_errors"][sid]) for sid in ids])
        boot = d[ix].mean(axis=1)
        contrasts.append({"contrast": f"MAE({a})-MAE({b})", "mean_scm_balanced_delta_mae": float(d.mean()),
                          "ci95_low": float(np.quantile(boot, .025)), "ci95_high": float(np.quantile(boot, .975)),
                          "better": int((d > TOL).sum()), "worse": int((d < -TOL).sum()),
                          "tie": int((np.abs(d) <= TOL).sum()), "n_heldout_scm": len(ids),
                          "bootstrap_seed": 2026112702, "shared_index_set": "all nested model contrasts",
                          "interval": "pointwise paired SCM bootstrap"})
    summary = [{"model": k, "selected_alpha": v["alpha"], **{f"heldout_{m}": x for m, x in v["metrics"].items()},
                "n_heldout_scm": len(ids), "feature_columns": json.dumps(feat[k]),
                "status": "post-hoc nested-feature re-fit on saved C graph features"} for k, v in models.items()]
    return summary, contrasts


def f_association_baseline():
    root = Path(os.environ.get("DAT_RESEARCH_ROOT", r"C:\DAT_RESEARCH"))
    base = root / "research-f-lite" / "v1"
    result = []
    for cohort, filename in (("C_DEVELOPMENT", "c_development_evaluator_results.jsonl"),
                             ("C_HELDOUT", "c_heldout_evaluator_results.jsonl")):
        path = base / filename
        if not path.is_file():
            return [{"status": "NOT_AVAILABLE", "reason": "saved F evaluator rows unavailable"}]
        records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        rs = [r for r in records if r["cohort"] == cohort and r["policy"] == "GRAPH_FREE_ASSOCIATION_DIAGNOSTIC" and int(r["budget"]) == 0 and int(r["repeat"]) == 0]
        by = defaultdict(list)
        for r in rs:
            by[r["scm_id"]].append(float(r["regret"]))
        h = hashlib.sha256(path.read_bytes()).hexdigest()
        result.append({"cohort": cohort, "baseline": "GRAPH_FREE_ASSOCIATION_DIAGNOSTIC",
                       "n_scm": len(by), "mean_gamma_zero_regret": float(np.mean([np.mean(v) for v in by.values()])),
                       "source_file_sha256": h,
                       "interpretation": "Existing F association learner, original gamma-zero objective; not evaluated for new S1 gamma conditions"})
    return result


def integrated_objective_associations(s1, graphs, replicates=2_000):
    """Compare objective-specific metric associations on a fixed common B=2 graph set."""
    metrics = ("directed_f1", "directed_shd", "task_error_rate", "xy_path", "abs_effect_magnitude_error")
    conditions = (("original", 0.), ("original", .2), ("original", .5), ("original", 1.),
                  ("-0.25", .2), ("0.25", .2))
    result = []
    rng = np.random.default_rng(2026112603)
    for cohort in ("C_DEVELOPMENT", "C_HELDOUT"):
        g = [r for r in graphs if r["cohort"] == cohort and int(float(r["budget"])) == 2]
        by_g = {(r["scm_id"], r["structural_graph_hash"]): r for r in g}
        maps = []
        for delta, gamma in conditions:
            vals = defaultdict(list)
            for r in s1:
                if r["cohort"] != cohort or int(float(r["budget"])) != 2 or r["target_delta"] != delta or float(r["gamma"]) != gamma:
                    continue
                vals[(r["scm_id"], r["graph_hash"])].append(float(r["regret"]))
            if not vals:
                raise ValueError(f"missing saved S1 rows for condition {cohort}/{delta}/{gamma}")
            reduced = {}
            for key, ys in vals.items():
                if max(ys) - min(ys) > 1e-10:
                    raise ValueError(f"same saved graph has inconsistent objective regret: {key}/{delta}/{gamma}")
                reduced[key] = float(np.mean(ys))
            maps.append(reduced)
        common = set(by_g)
        for m in maps:
            common &= set(m)
        keys = sorted(common)
        if not keys:
            raise ValueError(f"no common S1/S2 B=2 graph keys for {cohort}")
        ids = sorted({k[0] for k in keys})
        cluster = {sid: [k for k in keys if k[0] == sid] for sid in ids}
        x_by_metric = {metric: [float(by_g[k][metric]) if by_g[k].get(metric) not in ("", None) else np.nan for k in keys] for metric in metrics}
        cond_y = [[m[k] for k in keys] for m in maps]
        weights = [1 / len(cluster[k[0]]) for k in keys]
        point_corr = [[weighted_spearman(x_by_metric[metric], ys, weights) for metric in metrics] for ys in cond_y]
        draw_ix = rng.integers(0, len(ids), size=(replicates, len(ids)))
        boot_deltas = [[[] for _ in metrics] for _ in conditions]
        for draw in draw_ix:
            draw_keys = [k for j in draw for k in cluster[ids[j]]]
            bxw = [1 / len(cluster[k[0]]) for k in draw_keys]
            for mi, metric in enumerate(metrics):
                xx = [float(by_g[k][metric]) if by_g[k].get(metric) not in ("", None) else np.nan for k in draw_keys]
                base = weighted_spearman(xx, [maps[0][k] for k in draw_keys], bxw)
                for ci in range(1, len(conditions)):
                    cur = weighted_spearman(xx, [maps[ci][k] for k in draw_keys], bxw)
                    if base is not None and cur is not None:
                        boot_deltas[ci][mi].append(cur - base)
        for ci, (delta, gamma) in enumerate(conditions):
            for mi, metric in enumerate(metrics):
                boot = boot_deltas[ci][mi]
                base_point = point_corr[0][mi]
                current = point_corr[ci][mi]
                result.append({"cohort": cohort, "condition": f"delta={delta};gamma={gamma}",
                    "metric": metric, "n_scm": len(ids), "n_common_b2_graphs": len(keys),
                    "spearman_scm_balanced": current,
                    "difference_from_original_gamma0": None if ci == 0 else current - base_point,
                    "paired_delta_ci95_low": None if ci == 0 or not boot else float(np.quantile(boot, .025)),
                    "paired_delta_ci95_high": None if ci == 0 or not boot else float(np.quantile(boot, .975)),
                    "bootstrap_replicates": 0 if ci == 0 else len(boot),
                    "bootstrap_seed": 2026112603,
                    "interval": "paired SCM bootstrap of correlation change; descriptive, pointwise" if ci else "descriptive point estimate"})
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reuse-verified-metric-bootstrap", action="store_true")
    args = parser.parse_args()
    unit_path = OUT / "s1_unit_metrics.csv"
    graph_path = OUT / "s2_unique_graph_metrics.csv"
    pred_path = OUT / "s2_predictions_local.csv"
    for p in (unit_path, graph_path, pred_path):
        if not p.is_file():
            raise FileNotFoundError(f"required pre-existing ignored result missing: {p.name}")
    s1 = read_csv(unit_path)
    pairs = ((FULL, "S0", "FullGreedy-S0"), ("M4", FULL, "M4-FullGreedy"),
             ("M4", "S0", "M4-S0"), ("CANONICAL_ORACLE", "S0", "CanonicalOracle-S0"),
             ("M4", "CANONICAL_ORACLE", "M4-CanonicalOracle"))
    contrasts = common_bootstrap(s1, pairs)
    write_csv(OUT / "s1_corrected_primary_contrasts.csv", contrasts)
    write_csv(OUT / "s1_corrected_objective_policy_summary.csv", objective_table(s1))
    write_csv(OUT / "s1_corrected_effect_diagnostics.csv", effect_diagnostics(s1))
    optdiag = read_csv(OUT / "s1_optimum_diagnostics_local.csv")
    write_csv(OUT / "s1_action_quality_diagnostics.csv", action_quality(s1, optdiag))
    graphs = parse_numeric(read_csv(graph_path), ["regret", "selected_k", "estimated_effect_slope", "true_effect_slope",
        "abs_effect_magnitude_error", "effect_sign_error", "skeleton_f1", "directed_f1", "directed_shd",
        "atomic_error_count", "task_error_count", "task_error_rate", "xy_path", "n_nodes", "task_fn", "task_fp",
        "task_rev", "task_unres", "task_support"])
    metric_path = OUT / "s2_shared_index_metric_correlations.csv"
    metric_stamp = OUT / "s2_shared_index_metric_correlations.provenance.json"
    expected_sources = {p.name: sha(p) for p in (unit_path, graph_path, pred_path)}
    algorithm_sha = hashlib.sha256(inspect.getsource(shared_metric_bootstrap).encode()).hexdigest()
    if args.reuse_verified_metric_bootstrap:
        if not metric_path.is_file() or not metric_stamp.is_file():
            raise FileNotFoundError("verified metric-bootstrap checkpoint missing")
        stamp = json.loads(metric_stamp.read_text(encoding="utf-8"))
        if stamp.get("source_sha256") != expected_sources or stamp.get("algorithm_sha256") != algorithm_sha or stamp.get("output_sha256") != sha(metric_path):
            raise ValueError("metric-bootstrap checkpoint provenance mismatch")
        shared_corr = read_csv(metric_path)
    else:
        shared_corr = shared_metric_bootstrap(graphs)
        write_csv(metric_path, shared_corr)
        metric_stamp.write_text(json.dumps({"source_sha256": expected_sources, "algorithm_sha256": algorithm_sha,
            "output_sha256": sha(metric_path), "seed": 2026112602, "replicates": REPS,
            "completed_before_nested_audit": True}, indent=2) + "\n", encoding="utf-8")
    nested, nested_pairs = nested_model_validation(graphs)
    write_csv(OUT / "s2_nested_model_validation.csv", nested)
    write_csv(OUT / "s2_nested_prediction_bootstrap.csv", nested_pairs)
    integrated = integrated_objective_associations(s1, graphs)
    write_csv(OUT / "s1_s2_common_graph_objective_associations.csv", integrated)
    source_hashes = expected_sources
    summary = {"audit_status": "SAVED_OUTPUT_REAGGREGATION_COMPLETED_WITH_CORRECTIONS",
               "no_new_scm_g0_observation_response_or_expert_rows": True,
               "full_greedy_policy_id": FULL,
               "canonical_oracle_is_distinct": True,
               "s1_contrasts": contrasts, "s1_objective_policy_summary_rows": 40,
               "s1_effect_diagnostics": "absolute signed-slope error, not absolute-magnitude-only error",
               "s2_shared_index_correlations": "same cohort bootstrap SCM index matrix across all metrics",
               "s2_nested_model_rows": nested, "s2_nested_model_contrasts": nested_pairs,
               "s1_s2_integrated_objective_associations": {"rows": len(integrated), "common_graph_set": True,
                   "bootstrap_replicates": 2000, "same_scm_indices_across_conditions_and_metrics": True},
               "saved_f_association_baseline": f_association_baseline(),
               "source_sha256": source_hashes,
               "bootstrap_replicates": REPS}
    (OUT / "final_supplementary_audit_summary.json").write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()

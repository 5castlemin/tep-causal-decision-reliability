"""Independent comparison of saved Research D reproduction vectors and results."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from research.external_validation.semisynthetic_evaluation.pipeline import canonical_json, file_sha256


def _verified_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _manifest_rows(path: Path) -> dict:
    value = _verified_json(path)
    body = dict(value)
    recorded = body.pop("content_sha256", None)
    if hashlib.sha256(canonical_json(body)).hexdigest() != recorded:
        raise ValueError(f"recommendation canonical digest mismatch: {path.name}")
    rows = value["recommendations"]
    mapped = {(r["g0_seed_id"], r["budget"], r["policy_id"]): r for r in rows}
    if len(mapped) != len(rows):
        raise ValueError(f"duplicate recommendation key: {path.name}")
    return value


def _loss_and_bootstrap(action_order, vectors, rec, lock):
    target = float(lock["target_scale"]["target"])
    scale = float(lock["target_scale"]["scale"])
    n = int(lock["evaluation"]["rows_per_action"])
    losses, summaries = {}, {}
    for action, y in zip(action_order, vectors):
        mean = float(y.mean())
        var = float(y.var(ddof=1))
        bc = ((mean - target) ** 2 - var / n) / scale**2
        plugin = (mean - target) ** 2 / scale**2
        key = str(float(action))
        losses[key] = {"bias_corrected_loss": float(bc), "plug_in_loss": float(plugin)}
        summaries[key] = {"n": len(y), "mean": mean, "sample_variance": var,
            "response_sha256": hashlib.sha256(y.tobytes(order="C")).hexdigest()}

    by_key = {(r["g0_seed_id"], r["budget"], r["policy_id"]): r for r in rec["recommendations"]}
    seed_ids = list(lock["g0"]["seed_ids"])
    actions = [float(x) for x in action_order]
    lookup = {a: i for i, a in enumerate(actions)}
    deltas = []
    for seed in seed_ids:
        s0 = float(by_key[(seed, 2, "S0")]["recommended_action"])
        fg = float(by_key[(seed, 2, "M1+M2+M3+M4")]["recommended_action"])
        deltas.append(losses[str(s0)]["bias_corrected_loss"] -
                      losses[str(fg)]["bias_corrected_loss"])
    primary = float(np.mean(deltas))

    b_reps = int(lock["evaluation"]["bootstrap_replicates"])
    rng = np.random.default_rng(int(lock["evaluation"]["bootstrap_seed"]))
    action_matrix = np.empty((b_reps, len(actions)), dtype=float)
    for j, y in enumerate(vectors):
        draw_index = rng.integers(0, len(y), size=(b_reps, len(y)))
        boot = y[draw_index]
        boot_mean = boot.mean(axis=1)
        boot_var = boot.var(axis=1, ddof=1)
        action_matrix[:, j] = ((boot_mean - target) ** 2 - boot_var / len(y)) / scale**2
    paired_actions = {}
    for seed in seed_ids:
        paired_actions[seed] = {
            "S0": lookup[float(by_key[(seed, 2, "S0")]["recommended_action"])],
            "FullGreedy": lookup[float(by_key[(seed, 2, "M1+M2+M3+M4")]["recommended_action"])],
        }
    seed_deltas = np.stack([
        action_matrix[:, paired_actions[s]["S0"]] - action_matrix[:, paired_actions[s]["FullGreedy"]]
        for s in seed_ids], axis=1)
    g0_draws = rng.integers(0, len(seed_ids), size=(b_reps, len(seed_ids)))
    two_source = seed_deltas[g0_draws, np.arange(b_reps)[:, None]].mean(axis=1)
    mc_only = seed_deltas.mean(axis=1)
    fixed = np.asarray(deltas, dtype=float)
    g0_only = np.empty(b_reps, dtype=float)
    for j in range(b_reps):
        g0_only[j] = np.mean(rng.choice(fixed, size=len(fixed), replace=True))
    intervals = {
        "g0_only_percentile_95": np.quantile(g0_only, [0.025, 0.975]).tolist(),
        "action_mc_only_percentile_95": np.quantile(mc_only, [0.025, 0.975]).tolist(),
        "two_source_percentile_95": np.quantile(two_source, [0.025, 0.975]).tolist(),
    }
    return primary, summaries, losses, intervals


def compare(*, original_lock_path: Path, original_recommendations_path: Path,
            original_evaluation_path: Path, original_summary_path: Path,
            new_lock_path: Path, new_recommendations_path: Path,
            new_evaluation_path: Path, new_summary_path: Path,
            response_vectors_path: Path) -> dict:
    old_lock, new_lock = _verified_json(original_lock_path), _verified_json(new_lock_path)
    old_rec = _manifest_rows(original_recommendations_path)
    new_rec = _manifest_rows(new_recommendations_path)
    old_eval, new_eval = _verified_json(original_evaluation_path), _verified_json(new_evaluation_path)
    new_summary = _verified_json(new_summary_path)
    vector_record = new_eval.get("response_vectors_artifact")
    if not vector_record or file_sha256(response_vectors_path) != vector_record["sha256"]:
        raise ValueError("evaluator-only response-vector artifact digest mismatch")

    with np.load(response_vectors_path, allow_pickle=False) as stored:
        action_order = stored["action_order"].astype(np.float64).tolist()
        vectors = [stored[f"response_{i:02d}"].astype(np.float64)
                   for i in range(len(action_order))]
    if action_order != new_lock["action_grid"]["values"]:
        raise ValueError("response vectors use a different action order")
    if any(y.shape != (new_lock["evaluation"]["rows_per_action"],) or not np.isfinite(y).all()
           for y in vectors):
        raise ValueError("response vector shape or finite-value check failed")

    primary, action_summaries, losses, intervals = _loss_and_bootstrap(
        action_order, vectors, new_rec, new_lock)
    old_rows = {(r["g0_seed_id"], r["budget"], r["policy_id"]): r
                for r in old_rec["recommendations"]}
    new_rows = {(r["g0_seed_id"], r["budget"], r["policy_id"]): r
                for r in new_rec["recommendations"]}
    if set(old_rows) != set(new_rows):
        raise ValueError("historical and reproduction recommendation grids differ")
    recommendation_fields = ("recommended_action", "repair_cost", "initial_graph_sha256",
                             "repaired_graph_sha256")
    graph_hash_differences = sum(any(old_rows[k].get(field) != new_rows[k].get(field)
        for field in ("initial_graph_sha256", "repaired_graph_sha256")) for k in old_rows)
    differing_recommendations = sum(any(old_rows[k].get(field) != new_rows[k].get(field)
        for field in recommendation_fields) for k in old_rows)

    response_hash_matches = {}
    action_summary_matches = {}
    loss_matches = {}
    for action in action_order:
        key = str(float(action))
        digest = action_summaries[key]["response_sha256"]
        old_digest = old_eval["action_summary"][key]["response_sha256"]
        new_digest = new_eval["action_summary"][key]["response_sha256"]
        response_hash_matches[key] = digest == old_digest == new_digest
        old_summary = old_eval["action_summary"][key]
        new_stored = new_eval["action_summary"][key]
        action_summary_matches[key] = all(action_summaries[key].get(field) == old_summary.get(field)
            == new_stored.get(field) for field in ("n", "mean", "sample_variance", "response_sha256"))
        loss_matches[key] = (losses[key]["bias_corrected_loss"] ==
            old_eval["loss_table"][key]["bias_corrected_loss"] ==
            new_eval["loss_table"][key]["bias_corrected_loss"])

    old_fit = old_lock["fit_reproducibility"]["same_seed_refit_sample_sha256"]
    new_fit = new_lock["fit_reproducibility"]["same_seed_refit_sample_sha256"]
    old_train = old_lock["training"]["sha256"]
    new_train = new_lock["training"]["sha256"]
    old_delta = float(old_summary["primary_B2_S0_minus_FullGreedy"]["mean_delta_loss_bc"])
    new_delta = float(new_summary["primary_B2_S0_minus_FullGreedy"]["mean_delta_loss_bc"])
    interval_matches = all(np.array_equal(np.asarray(intervals[key]),
        np.asarray(new_eval["primary_two_source_uncertainty"][key])) for key in intervals)

    old_cost = {(r["g0_seed_id"], r["budget"], r["policy_id"]): r["repair_cost"]
                for r in old_rec["recommendations"]}
    new_cost = {(r["g0_seed_id"], r["budget"], r["policy_id"]): r["repair_cost"]
                for r in new_rec["recommendations"]}
    old_agreement = sum(old_rows[(s, 2, "M4")]["recommended_action"] ==
                        old_rows[(s, 2, "M1+M2+M3+M4")]["recommended_action"]
                        for s in old_lock["g0"]["seed_ids"])
    new_agreement = sum(new_rows[(s, 2, "M4")]["recommended_action"] ==
                        new_rows[(s, 2, "M1+M2+M3+M4")]["recommended_action"]
                        for s in new_lock["g0"]["seed_ids"])
    result = {"schema": "RESEARCH_D_ORIGINAL_VS_REPRODUCTION_COMPARISON_V1",
        "status": "COMPARED_FROM_SAVED_ARTIFACTS_AND_EVALUATOR_ONLY_RESPONSE_VECTORS",
        "response_vector_artifact": {"sha256": file_sha256(response_vectors_path),
            "bytes": response_vectors_path.stat().st_size, "rows": sum(len(y) for y in vectors)},
        "same_seed_drf_diagnostic_digest": old_fit == new_fit,
        "same_training_numeric_digest": old_train == new_train,
        "same_action_grid": old_lock["action_grid"]["values"] == new_lock["action_grid"]["values"],
        "same_target_scale": old_lock["target_scale"] == new_lock["target_scale"],
        "same_g0_ids_and_initial_graph_hashes": old_lock["g0"]["seed_ids"] == new_lock["g0"]["seed_ids"]
            and graph_hash_differences == 0,
        "graph_hash_rows_differing": graph_hash_differences,
        "recommendation_rows": len(new_rows),
        "recommendation_rows_differing_on_action_cost_or_graph_hash": differing_recommendations,
        "repair_costs_exact_match": old_cost == new_cost,
        "recommendation_row_count_matches_expected": len(new_rows) == 2720,
        "policy_budget_row_counts": {f"{budget}:{policy}": sum(
            row["budget"] == budget and row["policy_id"] == policy for row in new_rows.values())
            for budget in new_lock["g0"]["budgets"]
            for policy in sorted({row["policy_id"] for row in new_rows.values()})},
        "response_hash_matches_by_action": response_hash_matches,
        "action_summary_exact_matches_by_action": action_summary_matches,
        "loss_exact_matches_by_action": loss_matches,
        "primary": {"historical": old_delta, "reproduction": new_delta,
            "independently_recomputed_from_vectors": primary,
            "recomputed_matches_evaluator": primary == new_delta,
            "historical_difference": primary - old_delta},
        "bootstrap_intervals_recomputed_from_vectors": intervals,
        "bootstrap_intervals_match_evaluator": interval_matches,
        "M4_FullGreedy_action_agreement_B2": {"historical": old_agreement,
            "reproduction": new_agreement},
        "graph_free_baseline": {"historical": old_eval["graph_free_association_baseline"],
            "reproduction": new_eval["graph_free_association_baseline"]},
        "historical_raw_response_rows_available": False,
        "historical_bootstrap_independently_recomputed": False,
        "historical_primary_delta_comparison": {"old_saved": old_delta,
            "reproduction_from_new_response_vectors": primary},
        "g0_are_independent_external_scms": False,
        "final_evaluation": False}
    return result


def main(argv=None):
    parser = argparse.ArgumentParser()
    for name in ("original-lock", "original-recommendations", "original-evaluation", "original-summary",
                 "new-lock", "new-recommendations", "new-evaluation", "new-summary",
                 "response-vectors", "output"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    args = parser.parse_args(argv)
    result = compare(original_lock_path=args.original_lock,
        original_recommendations_path=args.original_recommendations,
        original_evaluation_path=args.original_evaluation, original_summary_path=args.original_summary,
        new_lock_path=args.new_lock, new_recommendations_path=args.new_recommendations,
        new_evaluation_path=args.new_evaluation, new_summary_path=args.new_summary,
        response_vectors_path=args.response_vectors)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.output.exists(): raise FileExistsError("refusing to overwrite comparison report")
    args.output.write_text(json.dumps(result, sort_keys=True, indent=2, allow_nan=False) + "\n",
                           encoding="utf-8")
    print(json.dumps({"status": result["status"], "rows": result["response_vector_artifact"]["rows"],
        "primary": result["primary"]}, sort_keys=True))


if __name__ == "__main__":
    main()

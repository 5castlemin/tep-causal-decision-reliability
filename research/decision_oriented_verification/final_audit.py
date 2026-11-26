"""Read-only closeout audit over saved F-Lite and Research C artifacts.

Does not restore/regenerate SCMs or observations and never calls policy/evaluator
recommendation paths. It reads C SQLite payloads and saved F-Lite rows only.
"""
from __future__ import annotations

import ast
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import sys
import subprocess

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from research.decision_oriented_verification.run_f_lite import DATA_ROOT, PRIVATE_ROOT, EXPECTED, SOURCES, stable_seed
from research.decision_oriented_verification.policy import VerificationState, graph_dag

OUT = ROOT / "research/decision_oriented_verification/outputs/final_audit_aggregate.json"
PUBLIC = ROOT / "research/decision_oriented_verification/outputs"
WEIGHTED = "DECISION_WEIGHTED_VERIFICATION"
POLICIES = ("RANDOM_VERIFICATION", "FIT_BASED_VERIFICATION", "SUSPICION_ONLY",
            "DECISION_IMPACT_ONLY", WEIGHTED)
EXPECTED_PRIVATE = {
    "C_DEVELOPMENT:recommendations": "e05855526d6f0ba57f775f1aef9eec2282ce0b4e690f33a72144ad2e7535a538",
    "C_DEVELOPMENT:evaluator": "c054e05de587592f2df51ef25717ab378d128c7df65dc88f8c71df6201374269",
    "C_HELDOUT:recommendations": "5b3f7fd54862f8657d8de08da68c7f48bb0ab1d13dcd172f7cb2d7e2cc0f3f83",
    "C_HELDOUT:evaluator": "16d05a2842b13fdde67cdae16ed1d5da3fa3843061090a044192c2c8ba5edaeb",
    "query_score_replay": "e624e3ca365e37155455062b7c323769fc939b3c875bddf09e3e6ff243e6bd92",
}


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def read_jsonl(path: Path):
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def read_source_graphs(cohort_path: Path, proposal_path: Path):
    """Read frozen G0/truth topology from stored payloads, never invoke generators."""
    con = sqlite3.connect(f"file:{cohort_path}?mode=ro", uri=True)
    pcon = sqlite3.connect(f"file:{proposal_path}?mode=ro", uri=True)
    try:
        proposals = {json.loads(raw)["scm_id"]: json.loads(raw)
                     for (raw,) in pcon.execute("SELECT proposal_json FROM proposal_attempts WHERE status='ELIGIBLE'")}
        out = {}
        for scm_id, status, raw in con.execute("SELECT scm_id,status,result_json FROM scms ORDER BY ordinal"):
            if status != "COMPLETED" or scm_id not in proposals:
                raise ValueError(f"incomplete or unmatched saved input: {scm_id}")
            payload = json.loads(raw)["payload"]
            g0 = payload["g0_generation"]["initial_graph"]
            nodes = tuple(proposals[scm_id]["nodes"])
            rels = {}
            for u, v in g0["edges"]:
                rels[tuple(sorted((u, v)))] = (u, v)
            for u, v in g0["unresolved"]:
                rels[tuple(sorted((u, v)))] = "UNRESOLVED"
            out[scm_id] = {"nodes": nodes, "g0": rels,
                           "truth_edges": {tuple(e) for e in proposals[scm_id]["topology_edges"]}}
        return out
    finally:
        con.close(); pcon.close()


def replay_pending(nodes, g0, history):
    """Replay stored answers only; return residual pending and final relations."""
    st = VerificationState(tuple(nodes), dict(g0))
    for q in history:
        st.apply_answer(tuple(q["pair"]), q["answer"])
    feasible = []
    for pair, desired in sorted(st.pending.items()):
        trial = dict(st.relations)
        if desired == "NO_EDGE":
            trial.pop(pair, None)
        else:
            trial[pair] = desired
        if graph_dag(nodes, trial):
            feasible.append(pair)
    return st, feasible


def common_bootstrap(rows, cohort):
    ids = sorted({r["scm_id"] for r in rows})
    by = {}
    for r in rows:
        if r["budget"] != 4 or r["policy"] not in POLICIES:
            continue
        by.setdefault((r["scm_id"], r["policy"]), []).append(float(r["regret"]))
    unit = {p: [] for p in POLICIES}
    for sid in ids:
        for p in POLICIES:
            vals = by.get((sid, p), [])
            if not vals:
                raise ValueError(f"missing bootstrap unit {cohort}/{sid}/{p}")
            unit[p].append(float(np.mean(vals)))
    arr = {p: np.asarray(v) for p, v in unit.items()}
    seed = stable_seed(cohort, "final-common-paired-bootstrap")
    rng = np.random.default_rng(seed)
    ix = rng.integers(0, len(ids), size=(10000, len(ids)))
    out = {}
    for comp in POLICIES:
        d = arr[comp] - arr[WEIGHTED]
        boots = d[ix].mean(axis=1)
        out[comp] = {"mean_comparator_minus_decision_weighted": float(d.mean()),
                     "ci95_pointwise_shared_indices": [float(np.quantile(boots, .025)), float(np.quantile(boots, .975))],
                     "better_worse_tie": [int((d < 0).sum()), int((d > 0).sum()), int((d == 0).sum())]}
    return {"seed": seed, "replicates": 10000, "comparisons": out}


def audit_cohort(name, source, private_root):
    cohort, _, cohort_path, proposal_path = source
    slug = cohort.lower()
    rec_path = private_root / f"{slug}_recommendations.json"
    ev_path = private_root / f"{slug}_evaluator_results.jsonl"
    rec_raw, ev_raw = rec_path.read_bytes(), ev_path.read_bytes()
    hashes = {"recommendations": hashlib.sha256(rec_raw).hexdigest(), "evaluator": hashlib.sha256(ev_raw).hexdigest()}
    for kind, path in (("recommendations", rec_path), ("evaluator", ev_path)):
        if hashes[kind] != EXPECTED_PRIVATE[f"{cohort}:{kind}"]:
            raise ValueError(f"F artifact hash mismatch {cohort}/{kind}")
    recommendations = json.loads(rec_raw)["records"]
    evaluations = [json.loads(x) for x in ev_raw.splitlines() if x]
    if len(recommendations) != len(evaluations):
        raise ValueError("recommendation/evaluator count mismatch")
    keys = [(r["scm_id"], r["policy"], r["repeat"], r["budget"]) for r in recommendations]
    ekeys = [(r["scm_id"], r["policy"], r["repeat"], r["budget"]) for r in evaluations]
    if len(set(keys)) != len(keys) or len(set(ekeys)) != len(ekeys) or set(keys) != set(ekeys):
        raise ValueError("duplicate/missing recommendation key")
    inputs = read_source_graphs(cohort_path, proposal_path)
    if len(inputs) != (64 if cohort == "C_DEVELOPMENT" else 200):
        raise ValueError("wrong original cohort count")
    s0 = {(r["scm_id"], r["budget"]): float(r["action"]) for r in evaluations if r["policy"] == "S0"}
    random_rates = {}
    for b in range(5):
        per_scm = {}
        for r in evaluations:
            if r["policy"] == "RANDOM_VERIFICATION" and r["budget"] == b:
                per_scm.setdefault(r["scm_id"], []).append(float(r["action"] != s0[(r["scm_id"], b)]))
        rates = [float(np.mean(v)) for v in per_scm.values()]
        random_rates[str(b)] = {"mean_scm_share_of_32_repeats_changed": float(np.mean(rates)),
                                "fraction_scm_ever_changed": float(np.mean([x > 0 for x in rates])),
                                "n_scm": len(rates), "repeats_per_scm": sorted({len(v) for v in per_scm.values()})}
    fit = {(r["scm_id"], r["budget"]): float(r["action"]) for r in evaluations if r["policy"] == "FIT_BASED_VERIFICATION"}
    fit_action_same_b3_b4 = sum(fit[(sid, 3)] == fit[(sid, 4)] for sid in inputs)
    deterministic = [r for r in evaluations if r["budget"] == 4 and r["policy"] in ("FIT_BASED_VERIFICATION", "SUSPICION_ONLY", "DECISION_IMPACT_ONLY", WEIGHTED)]
    pending_units = 0; pending_edges = 0; pending_feasible_edges = 0; pending_mismatch = 0
    pending_examples = []
    final_rows = [r for r in evaluations if r["budget"] == 4 and r["policy"] in ("FIT_BASED_VERIFICATION", "SUSPICION_ONLY", "DECISION_IMPACT_ONLY", WEIGHTED)]
    for r in final_rows:
        inp = inputs[r["scm_id"]]
        st, feasible = replay_pending(inp["nodes"], inp["g0"], r["query_history"])
        if len(st.pending) != int(r["pending_count"]):
            pending_mismatch += 1
        if st.pending:
            pending_units += 1; pending_edges += len(st.pending); pending_feasible_edges += len(feasible)
            if len(pending_examples) < 12:
                pending_examples.append({"scm_id": r["scm_id"], "policy": r["policy"],
                                         "pending_pairs": [list(p) for p in sorted(st.pending)],
                                         "final_individually_feasible": [list(p) for p in feasible]})
        stored = ast.literal_eval(r["final_relations"]) if isinstance(r["final_relations"], str) else r["final_relations"]
        if stored != st.relations:
            pending_mismatch += 1
    return {"cohort": cohort, "private_hashes": hashes, "n_scm": len(inputs),
            "recommendation_rows": len(recommendations), "evaluator_rows": len(evaluations),
            "random_action_change": random_rates,
            "fit_b3_b4_same_action": {"same": fit_action_same_b3_b4, "n": len(inputs)},
            "common_index_bootstrap_10k": common_bootstrap(evaluations, cohort),
            "pending_final_audit": {"deterministic_policy_scm_rows": len(final_rows), "rows_with_pending": pending_units,
                                    "pending_relations": pending_edges, "individually_dag_feasible_pending": pending_feasible_edges,
                                    "replay_vs_saved_mismatch_count": pending_mismatch,
                                    "example_keys": pending_examples}}


def query_mechanism_audit(source, private_root):
    cohort, _, cohort_path, proposal_path = source
    inputs = read_source_graphs(cohort_path, proposal_path)
    rows = read_jsonl(private_root / f"{cohort.lower()}_evaluator_results.jsonl")
    eval_by = {(r["scm_id"], r["policy"]): r for r in rows if r["budget"] == 4 and r["policy"] in POLICIES[1:]}
    traces = [r for r in read_jsonl(private_root / "query_score_replay.jsonl") if r["cohort"] == cohort]
    metrics = {p: {"queries": 0, "true_errors_queried": 0, "true_errors_with_zero_suspicion": 0,
                    "true_errors_with_zero_impact": 0, "true_errors_with_nonpositive_fit_gain": 0}
               for p in POLICIES[1:]}
    candidate_error_metrics = {p: {"candidate_snapshots": 0, "true_error_candidate_snapshots": 0,
                                   "error_candidates_zero_suspicion": 0, "error_candidates_zero_impact": 0,
                                   "error_candidates_nonpositive_fit_gain": 0} for p in POLICIES[1:]}
    zero_scores = {"all_candidates_zero": 0, "selected_score_zero": 0}
    for trace in traces:
        p = trace["policy"]; r = eval_by[(trace["scm_id"], p)]; inp = inputs[trace["scm_id"]]
        st = VerificationState(inp["nodes"], dict(inp["g0"]))
        hist = r["query_history"]
        step = int(trace["step"])
        for prev in hist[:step-1]:
            st.apply_answer(tuple(prev["pair"]), prev["answer"])
        q = hist[step-1]
        pair = tuple(q["pair"])
        desired = "NO_EDGE" if pair not in inp["truth_edges"] and (pair[1], pair[0]) not in inp["truth_edges"] else (
            "U_TO_V" if pair in inp["truth_edges"] else "V_TO_U")
        current = st.relations.get(pair, "NO_EDGE")
        current_state = ("UNRESOLVED" if current == "UNRESOLVED" else "NO_EDGE" if current == "NO_EDGE" else
                         "U_TO_V" if current == pair else "V_TO_U")
        error = current_state != desired
        candidates = trace["candidate_scores"]
        cm = candidate_error_metrics[p]
        for candidate in candidates:
            cp = tuple(candidate["pair"])
            c_current = st.relations.get(cp, "NO_EDGE")
            c_state = ("UNRESOLVED" if c_current == "UNRESOLVED" else "NO_EDGE" if c_current == "NO_EDGE" else
                       "U_TO_V" if c_current == cp else "V_TO_U")
            c_truth = "NO_EDGE" if cp not in inp["truth_edges"] and (cp[1], cp[0]) not in inp["truth_edges"] else (
                "U_TO_V" if cp in inp["truth_edges"] else "V_TO_U")
            is_error = c_state != c_truth
            cm["candidate_snapshots"] += 1
            if is_error:
                cm["true_error_candidate_snapshots"] += 1
                cm["error_candidates_zero_suspicion"] += int(float(candidate["suspicion"]) == 0.0)
                cm["error_candidates_zero_impact"] += int(float(candidate["decision_impact"]) == 0.0)
                cm["error_candidates_nonpositive_fit_gain"] += int(float(candidate["fit_gain"]) <= 0.0)
        row = metrics[p]; row["queries"] += 1
        if error:
            row["true_errors_queried"] += 1
            selected = next(x for x in candidates if tuple(x["pair"]) == pair)
            row["true_errors_with_zero_suspicion"] += int(float(selected["suspicion"]) == 0.0)
            row["true_errors_with_zero_impact"] += int(float(selected["decision_impact"]) == 0.0)
            row["true_errors_with_nonpositive_fit_gain"] += int(float(selected["fit_gain"]) <= 0.0)
        zero_scores["all_candidates_zero"] += int(all(float(x["score"]) == 0.0 for x in candidates))
        zero_scores["selected_score_zero"] += int(float(trace["selected_score"]) == 0.0)
    for v in metrics.values():
        v["error_discovery_yield"] = v["true_errors_queried"] / v["queries"] if v["queries"] else None
    for v in candidate_error_metrics.values():
        nerr = v["true_error_candidate_snapshots"]
        v["fraction_error_candidates_zero_suspicion"] = v["error_candidates_zero_suspicion"] / nerr if nerr else None
        v["fraction_error_candidates_zero_impact"] = v["error_candidates_zero_impact"] / nerr if nerr else None
    weighted = {(r["scm_id"], r["budget"]): r for r in rows if r["policy"] == WEIGHTED}
    impact = {(r["scm_id"], r["budget"]): r for r in rows if r["policy"] == "DECISION_IMPACT_ONLY"}
    n = len(inputs)
    same_query_sequence = 0
    for sid in inputs:
        wh = weighted[(sid, 4)]["query_history"]; ih = impact[(sid, 4)]["query_history"]
        same_query_sequence += int([q["pair"] for q in wh] == [q["pair"] for q in ih])
    return {"cohort": cohort, "query_metrics_by_policy": metrics,
            "error_candidate_score_diagnostics": candidate_error_metrics, "zero_score_ties": zero_scores,
            "decision_weighted_vs_impact_only": {"same_query_sequence_scm": same_query_sequence, "n_scm": n,
              "same_final_action_scm": sum(weighted[(sid,4)]["action"] == impact[(sid,4)]["action"] for sid in inputs)}}


def main():
    private_root = Path(os.environ.get("DAT_RESEARCH_F_LITE_ROOT", str(DATA_ROOT / "research-f-lite/v1")))
    before = {str(p): digest(p) for src in SOURCES for p in src[2:]}
    for src in SOURCES:
        for key, p in ((f"{src[0]}:cohort", src[2]), (f"{src[0]}:proposal", src[3])):
            if digest(p) != EXPECTED[key]:
                raise ValueError(f"original C source hash mismatch: {key}")
    query_path = private_root / "query_score_replay.jsonl"
    if digest(query_path) != EXPECTED_PRIVATE["query_score_replay"]:
        raise ValueError("query score replay hash mismatch")
    # Read-only audit of stored score decisions; no score/policy recomputation.
    qrows = read_jsonl(query_path)
    query_audit = {}
    for cohort in ("C_DEVELOPMENT", "C_HELDOUT"):
        q = [r for r in qrows if r["cohort"] == cohort]
        expected_n = 1024 if cohort == "C_DEVELOPMENT" else 3200
        if len(q) != expected_n:
            raise ValueError(f"query score replay row count mismatch for {cohort}: {len(q)}")
        for row in q:
            top = min(row["candidate_scores"], key=lambda x: (-float(x["score"]), tuple(x["pair"])))
            if list(top["pair"]) != row["selected_pair"]:
                raise ValueError(f"saved query does not match score argmax/tie-break: {cohort}/{row['scm_id']}/{row['policy']}")
        all_zero = [r for r in q if all(float(x["score"]) == 0 for x in r["candidate_scores"])]
        selected_zero = [r for r in q if float(r["selected_score"]) == 0]
        query_audit[cohort] = {"saved_selected_queries": len(q), "all_candidate_scores_zero": len(all_zero),
                               "selected_score_zero": len(selected_zero),
                               "candidate_score_rows": sum(len(r["candidate_scores"]) for r in q)}
    results = [audit_cohort(n, src, private_root) for n, src in enumerate(SOURCES)]
    query_mechanism = [query_mechanism_audit(src, private_root) for src in SOURCES]
    after = {str(p): digest(p) for src in SOURCES for p in src[2:]}
    if before != after:
        raise ValueError("C source changed during read-only audit")
    summary = {"audit_type": "saved-output-only; no SCM or observational regeneration",
               "source_hashes_unchanged": before == after, "cohorts": results,
               "query_score_replay_summary": query_audit, "query_mechanism_audit": query_mechanism}
    OUT.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with (PUBLIC / "random_action_change_audit.csv").open("w", encoding="utf-8", newline="") as f:
        import csv
        w = csv.writer(f); w.writerow(["cohort", "budget", "mean_scm_share_of_32_repeats_changed", "fraction_scm_ever_changed", "n_scm", "repeats_per_scm"])
        for c in results:
            for budget, v in c["random_action_change"].items():
                w.writerow([c["cohort"], budget, v["mean_scm_share_of_32_repeats_changed"], v["fraction_scm_ever_changed"], v["n_scm"], 32])
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    tree = subprocess.check_output(["git", "rev-parse", f"{commit}^{{tree}}"], cwd=ROOT, text=True).strip()
    db_hashes = {f"{src[0]}:{kind}": digest(path) for src in SOURCES
                 for kind, path in (("cohort_db", src[2]), ("proposal_db", src[3]))}
    private_hashes = {"query_score_replay": EXPECTED_PRIVATE["query_score_replay"]}
    for c in results:
        for kind, value in c["private_hashes"].items():
            private_hashes[f"{c['cohort']}:{kind}"] = value
    manifest = {"audit": "Research F-Lite final saved-output audit", "execution_commit": commit,
                "execution_tree": tree, "execution_script_sha256": digest(Path(__file__).resolve()),
                "source_databases_sha256": db_hashes, "private_artifacts_sha256": private_hashes,
                "public_aggregate_sha256": digest(OUT),
                "random_action_change_csv_sha256": digest(PUBLIC / "random_action_change_audit.csv"),
                "generated_new_scms_observations_or_interventions": 0}
    (PUBLIC / "final_audit_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

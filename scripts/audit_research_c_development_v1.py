"""Read-only audit and SCM-level summaries for the first Research C Development run.

The input SQLite databases are opened with SQLite ``mode=ro`` and are never
updated. The optional JSON output is created separately and must not be inside
the immutable raw-results directory.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path
import sqlite3
import statistics
import sys
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.original_objective import policy_engine as pe
from research.original_objective.runner import _digest

RUN_ID = "development-20261123-seed-2026112301-v1"
EXPECTED_COMMIT = "01473797e8edd9e01935a7bee57107b63a4d53ca"
EXPECTED_MANIFEST_DIGEST = "d992806153622173644edf470e3b79f41f29bc547fc588922f6e96bd9f3273ac"
POLICY_IDS = ["S0", *["+".join(s) for s in pe.catalog() if s], "CANONICAL_ORACLE"]
FULL = "M1+M2+M3+M4"


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _ro_sqlite(path: Path) -> sqlite3.Connection:
    uri = "file:" + quote(str(path.resolve()).replace("\\", "/"), safe=":/") + "?mode=ro"
    connection = sqlite3.connect(uri, uri=True)
    connection.execute("PRAGMA query_only=ON")
    return connection


def _t_cdf_positive(x: float, df: int) -> float:
    """Numerically integrate the Student-t density on [0,x] (Simpson rule)."""
    if x < 0 or df < 1:
        raise ValueError("x must be nonnegative and df positive")
    n = 2048
    h = x / n
    scale = math.gamma((df + 1) / 2) / (math.sqrt(df * math.pi) * math.gamma(df / 2))

    def density(t: float) -> float:
        return scale * (1.0 + t * t / df) ** (-(df + 1) / 2)

    total = density(0.0) + density(x)
    total += 4.0 * sum(density(i * h) for i in range(1, n, 2))
    total += 2.0 * sum(density(i * h) for i in range(2, n, 2))
    return 0.5 + total * h / 3.0


def _t_quantile(probability: float, df: int) -> float:
    if not 0.5 < probability < 1:
        raise ValueError("probability must be between 0.5 and 1")
    lo, hi = 0.0, 10.0
    for _ in range(60):
        mid = (lo + hi) / 2
        if _t_cdf_positive(mid, df) < probability:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def _mean_ci(values: list[float], confidence: float = 0.95) -> dict:
    if len(values) < 2:
        raise ValueError("paired t interval requires at least two SCM-level pairs")
    mean = statistics.mean(values)
    sd = statistics.stdev(values)
    df = len(values) - 1
    critical = _t_quantile((1 + confidence) / 2, df)
    half = critical * sd / math.sqrt(len(values))
    return {"method": "two-sided paired-t interval on SCM-level deltas",
            "confidence": confidence, "n_pairs": len(values), "df": df,
            "critical_t": critical, "mean": mean, "sample_sd": sd,
            "standard_error": sd / math.sqrt(len(values)),
            "lower": mean - half, "upper": mean + half}


def _counts(values: list[float]) -> dict:
    return {"improve": sum(v > 0 for v in values),
            "worsen": sum(v < 0 for v in values),
            "tie": sum(v == 0 for v in values)}


def _result_payload(row, errors: list[dict]) -> dict:
    scm_id, status, result_json, result_sha, failure_reason, failure_code = row
    if result_json is None:
        errors.append({"scm_id": scm_id, "error": "missing result payload"})
        return {}
    wrapper = json.loads(result_json)
    payload = wrapper.get("payload")
    if not isinstance(payload, dict):
        errors.append({"scm_id": scm_id, "error": "invalid wrapper payload"})
        return {}
    if _digest(payload) != result_sha or wrapper.get("payload_sha256") != result_sha:
        errors.append({"scm_id": scm_id, "error": "result checksum mismatch"})
    if status != "COMPLETED" or failure_reason or failure_code:
        errors.append({"scm_id": scm_id, "error": "SCM status/failure mismatch"})
    if (payload.get("classification") != "RESEARCH_COHORT_RESULT"
            or payload.get("test_only") is not False
            or payload.get("research_regret_result") is not True):
        errors.append({"scm_id": scm_id, "error": "research result classification mismatch"})
    return payload


def audit(run_dir: Path, config_path: Path, manifest_path: Path) -> dict:
    run_dir = run_dir.resolve()
    config_path, manifest_path = config_path.resolve(), manifest_path.resolve()
    cohort_db = run_dir / "research_c_cohort.sqlite"
    proposal_db = run_dir / "research_c_proposal_stage.sqlite"
    errors: list[dict] = []
    config = json.loads(config_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    config_digest, manifest_digest = _digest(config), _digest(manifest)
    if manifest_digest != EXPECTED_MANIFEST_DIGEST:
        errors.append({"error": "canonical manifest digest differs from approved value"})
    if config_digest != manifest.get("config_sha256"):
        errors.append({"error": "manifest/config digest mismatch"})
    if manifest.get("source_revision", {}).get("commit") != EXPECTED_COMMIT:
        errors.append({"error": "manifest source commit mismatch"})

    proposal_connection = _ro_sqlite(proposal_db)
    proposal_integrity = proposal_connection.execute("PRAGMA integrity_check").fetchone()[0]
    proposal_run = proposal_connection.execute(
        "SELECT status,active_seconds,failure_code,failure_reason,config_sha256 "
        "FROM proposal_stage_runs WHERE run_id=?", (RUN_ID,)).fetchone()
    attempt_rows = proposal_connection.execute(
        "SELECT attempt,proposal_id,status,proposal_json,proposal_sha256,active_seconds,"
        "sampled_rss_peak_bytes,failure_code,failure_reason FROM proposal_attempts "
        "WHERE run_id=? ORDER BY attempt", (RUN_ID,)).fetchall()
    attempts = []
    proposal_by_scm = {}
    for attempt, proposal_id, status, raw, sha, seconds, rss, failure_code, failure_reason in attempt_rows:
        proposal = json.loads(raw) if raw else {}
        valid = bool(proposal) and _digest(proposal) == sha
        if not valid:
            errors.append({"proposal_id": proposal_id, "error": "proposal checksum mismatch"})
        scm_id = proposal.get("scm_id")
        proposal_by_scm[scm_id] = proposal
        attempts.append({"attempt": attempt, "proposal_id": proposal_id,
                         "scm_id": scm_id, "status": status, "sha256": sha,
                         "checksum_valid": valid, "q_common_eligible": proposal.get("q_common_eligible"),
                         "template": proposal.get("template"), "node_count": proposal.get("node_count"),
                         "active_seconds": seconds, "sampled_rss_peak_bytes": rss,
                         "failure_code": failure_code, "failure_reason": failure_reason})
    proposal_connection.close()

    connection = _ro_sqlite(cohort_db)
    cohort_integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
    foreign_key_issues = connection.execute("PRAGMA foreign_key_check").fetchall()
    run = connection.execute(
        "SELECT cohort_type,master_seed,config_json,config_sha256,code_json,source_json,active_seconds "
        "FROM runs WHERE run_id=?", (RUN_ID,)).fetchone()
    scm_rows = connection.execute(
        "SELECT scm_id,status,result_json,result_sha256,failure_reason,failure_code,"
        "active_seconds,sampled_rss_peak_bytes FROM scms WHERE run_id=? ORDER BY ordinal", (RUN_ID,)).fetchall()
    proposal_rows = connection.execute(
        "SELECT scm_id,status,proposal_json,proposal_sha256 FROM proposals WHERE run_id=? ORDER BY rowid",
        (RUN_ID,)).fetchall()
    event_rows = connection.execute(
        "SELECT to_status,COUNT(*) FROM events WHERE run_id=? GROUP BY to_status", (RUN_ID,)).fetchall()
    connection.close()
    if cohort_integrity != "ok" or proposal_integrity != "ok" or foreign_key_issues:
        errors.append({"error": "SQLite integrity/foreign-key check failed"})
    if not run:
        raise ValueError(f"run {RUN_ID} missing from cohort ledger")
    cohort_type, master_seed, run_config_json, run_config_sha, code_json, source_json, cohort_active = run
    run_config, code_hashes, source = map(json.loads, (run_config_json, code_json, source_json))
    if (cohort_type != "RESEARCH_COHORT" or master_seed != config["rng_protocol"]["master_seed"]
            or source.get("commit") != EXPECTED_COMMIT
            or source != manifest.get("source_revision")):
        errors.append({"error": "cohort run/config/source binding mismatch"})
    # The cohort ledger binds the canonical config together with its code map.
    if run_config_sha != _digest({"config": run_config, "code_sha256": code_hashes}):
        errors.append({"error": "stored run configuration/code binding checksum mismatch"})
    if code_hashes != manifest.get("code_sha256"):
        errors.append({"error": "run code hashes differ from approved Manifest"})

    outcomes = []
    p1_deltas = []
    s0_regrets, full_regrets = [], []
    full_edits, full_costs = [], []
    tie_cross = Counter()
    tie_action_cross = Counter()
    noerror_noop = {"no_error_g0": 0, "full_greedy_noop": 0, "intersection": 0,
                    "no_error_but_greedy_edits": 0, "error_g0_but_greedy_noop": 0}
    g0_totals = Counter()
    g0_by_kind_zone = Counter()
    stale_metadata = []
    policy_means = defaultdict(list)
    pairwise = defaultdict(list)
    m4_action_groups = Counter()
    m4_regret_groups = Counter()
    m4_graph_groups = Counter()
    m4_edit_kinds = Counter()
    m4_edit_zones = Counter()
    m4_noop_count = 0
    m4_edit_counts = []
    m4_costs = []
    m4_pair_match = defaultdict(Counter)
    equal_penalty_different_regret = []
    different_penalty_same_regret = []
    graph_regret_cases = []
    per_scm = []
    total_policy_rows = 0
    qcommon_scm_ids = {r[0] for r in proposal_rows
                       if json.loads(r[2]).get("q_common_eligible") is True}
    proposal_state_counts = Counter(r[1] for r in proposal_rows)
    proposal_checksum_valid = 0
    for scm_id, status, raw_proposal, sha in proposal_rows:
        if _digest(json.loads(raw_proposal)) != sha:
            errors.append({"scm_id": scm_id, "error": "cohort proposal checksum mismatch"})
        else:
            proposal_checksum_valid += 1
    for row in scm_rows:
        scm_id, status, raw, row_sha, failure_reason, failure_code, active_seconds, rss = row
        payload = _result_payload(row[:6], errors)
        if not payload:
            continue
        meta = payload.get("fixture_metadata", {})
        g0 = meta.get("g0_generation", {})
        if meta.get("classification") != "RESEARCH_C_GENERATED_PROPOSAL":
            errors.append({"scm_id": scm_id, "error": "SCM factory classification mismatch"})
        if (g0.get("contract_status") != "PROPOSED_NOT_APPROVED"
                or g0.get("test_or_cohort_use") != "not_authorized"):
            errors.append({"scm_id": scm_id, "error": "expected legacy G0 tags were not found"})
        else:
            stale_metadata.append(scm_id)
        configured_rates = g0.get("rates", {}).get("configured", {})
        if (configured_rates.get("true_adjacency_corruption") != 0.15
                or configured_rates.get("false_adjacency") != 0.05
                or configured_rates.get("conditional_true_error_mix") !=
                   {"FN": 1 / 3, "REV": 1 / 3, "UNRES": 1 / 3}
                or g0.get("summary", {}).get("retries") != 0):
            errors.append({"scm_id": scm_id, "error": "G0 generated rates/retry contract mismatch"})
        gen_status = g0.get("generation_status")
        counts = g0.get("realized_error_counts_by_kind_and_zone", {})
        no_errors = sum(sum(zone.values()) for zone in counts.values()) == 0
        summary = g0.get("summary", {})
        for key in ("proposed", "accepted", "rejected_dag"):
            g0_totals[key] += summary.get(key, 0)
        for key, value in summary.get("proposed_by_kind", {}).items():
            g0_totals[f"proposed_{key}"] += value
        for key, value in summary.get("accepted_by_kind", {}).items():
            g0_totals[f"accepted_{key}"] += value
        for kind, zones in counts.items():
            for zone, value in zones.items():
                g0_by_kind_zone[f"{kind}_{zone}"] += value

        e2e = payload.get("e2e_result", {})
        budgets = {b.get("budget"): b for b in e2e.get("budgets", [])}
        if set(budgets) != {0, 1, 2, 3, 4}:
            errors.append({"scm_id": scm_id, "error": "budget grid mismatch"})
            continue
        policy_map = {}
        for budget, block in budgets.items():
            policies = {p.get("policy_id"): p for p in block.get("policies", [])}
            total_policy_rows += len(policies)
            if (set(policies) != set(POLICY_IDS) or block.get("policy_vector_status") != "COMPLETE"
                    or block.get("expected_policy_count") != 17
                    or block.get("evaluable_policy_count") != 17):
                errors.append({"scm_id": scm_id, "budget": budget, "error": "incomplete policy vector"})
            if any(p.get("status") != "OK" or p.get("evaluation_status") != "RESEARCH_OK"
                   for p in policies.values()):
                errors.append({"scm_id": scm_id, "budget": budget, "error": "policy evaluation failure"})
            policy_map[budget] = policies
            for pid, p in policies.items():
                policy_means[(budget, pid)].append(p["evaluation"]["regret"])

        b0, b2 = policy_map[0], policy_map[2]
        if (b0["S0"]["final_graph_sha256"], b0["S0"]["evaluation"]["selected_action"],
                b0["S0"]["evaluation"]["regret"]) != (
                b2["S0"]["final_graph_sha256"], b2["S0"]["evaluation"]["selected_action"],
                b2["S0"]["evaluation"]["regret"]):
            errors.append({"scm_id": scm_id, "error": "S0 B0/B2 mismatch"})
        if b2["S0"]["shared_input_sha256"] != b2[FULL]["shared_input_sha256"]:
            errors.append({"scm_id": scm_id, "error": "P1 shared input hash mismatch"})
        primary = budgets[2].get("primary_comparison", {})
        s0, full = b2["S0"], b2[FULL]
        delta = s0["evaluation"]["regret"] - full["evaluation"]["regret"]
        if (primary.get("status") != "COMPLETE" or primary.get("delta") != delta
                or primary.get("same_conditions_for_pair") is not True):
            errors.append({"scm_id": scm_id, "error": "stored P1 differs from independent recomputation"})
        p1_deltas.append(delta)
        s0_regrets.append(s0["evaluation"]["regret"])
        full_regrets.append(full["evaluation"]["regret"])
        full_edits.append(len(full["edit_log"]))
        full_costs.append(full["total_edit_cost"])
        qcommon = scm_id in qcommon_scm_ids
        m4 = b2["M4"]
        m4_action_groups[str(m4["evaluation"]["selected_action"])] += 1
        m4_regret_groups[str(m4["evaluation"]["regret"])] += 1
        m4_graph_groups[m4["final_graph_sha256"]] += 1
        m4_edit_counts.append(len(m4["edit_log"]))
        m4_costs.append(m4["total_edit_cost"])
        m4_noop_count += len(m4["edit_log"]) == 0
        for edit in m4["edit_log"]:
            m4_edit_kinds[edit.get("error_type", "UNKNOWN")] += 1
            m4_edit_zones["task_zone" if edit.get("task_zone") else "off_task"] += 1
        tie = delta == 0
        same_graph = s0["final_graph_sha256"] == full["final_graph_sha256"]
        same_action = ((s0["evaluation"]["selected_action"], s0["evaluation"]["selected_k"])
                       == (full["evaluation"]["selected_action"], full["evaluation"]["selected_k"]))
        same_loss = s0["evaluation"]["gt_selected_loss"] == full["evaluation"]["gt_selected_loss"]
        tie_action_cross["p1_ties_same_action"] += tie and same_action
        tie_action_cross["p1_ties_different_action"] += tie and not same_action
        tie_action_cross["same_action_all_pairs"] += same_action
        tie_action_cross["zero_error_g0_same_action"] += no_errors and same_action
        for other_id in ("S0", FULL, "CANONICAL_ORACLE", "M1+M4", "M2+M4", "M3+M4"):
            other = b2[other_id]
            m4_pair_match[other_id]["same_graph"] += other["final_graph_sha256"] == m4["final_graph_sha256"]
            m4_pair_match[other_id]["same_P_all"] += abs(
                other["structural_P_all"] - m4["structural_P_all"]) <= 1e-12
            m4_pair_match[other_id]["same_action"] += (
                (other["evaluation"]["selected_action"], other["evaluation"]["selected_k"])
                == (m4["evaluation"]["selected_action"], m4["evaluation"]["selected_k"]))
            action_equal = ((other["evaluation"]["selected_action"], other["evaluation"]["selected_k"])
                            == (m4["evaluation"]["selected_action"], m4["evaluation"]["selected_k"]))
            regret_equal = abs(other["evaluation"]["regret"] - m4["evaluation"]["regret"]) <= 1e-12
            m4_pair_match[other_id]["same_regret"] += regret_equal
            category = ("same_action_" if action_equal else "different_action_") + (
                "same_regret" if regret_equal else "different_regret")
            m4_pair_match[other_id][category] += 1
        policy_items = list(b2.items())
        for i, (left_id, left) in enumerate(policy_items):
            for right_id, right in policy_items[i + 1:]:
                same_penalty = abs(left["structural_P_all"] - right["structural_P_all"]) <= 1e-12
                same_regret = abs(left["evaluation"]["regret"] - right["evaluation"]["regret"]) <= 1e-12
                if same_penalty and not same_regret and len(equal_penalty_different_regret) < 12:
                    equal_penalty_different_regret.append({"scm_id": scm_id,
                        "left_policy": left_id, "right_policy": right_id,
                        "shared_P_all": left["structural_P_all"],
                        "left_regret": left["evaluation"]["regret"],
                        "right_regret": right["evaluation"]["regret"]})
                if not same_penalty and same_regret and len(different_penalty_same_regret) < 12:
                    different_penalty_same_regret.append({"scm_id": scm_id,
                        "left_policy": left_id, "right_policy": right_id,
                        "left_P_all": left["structural_P_all"],
                        "right_P_all": right["structural_P_all"],
                        "shared_regret": left["evaluation"]["regret"]})
        if tie:
            if no_errors:
                tie_cross["zero_error_G0"] += 1
            elif same_graph:
                tie_cross["same_final_graph_with_initial_errors"] += 1
            elif same_action:
                tie_cross["different_graph_same_action"] += 1
            elif same_loss:
                tie_cross["different_action_same_GT_loss"] += 1
            else:
                tie_cross["other_equal_regret"] += 1
        noerror_noop["no_error_g0"] += no_errors
        noerror_noop["full_greedy_noop"] += len(full["edit_log"]) == 0
        noerror_noop["intersection"] += no_errors and len(full["edit_log"]) == 0
        noerror_noop["no_error_but_greedy_edits"] += no_errors and len(full["edit_log"]) > 0
        noerror_noop["error_g0_but_greedy_noop"] += (not no_errors) and len(full["edit_log"]) == 0

        for pid in ("M4", FULL, "S0", "CANONICAL_ORACLE", "M1+M4", "M2+M4", "M3+M4"):
            if pid == "M4":
                continue
            pairwise[pid].append(policy_map[2][pid]["evaluation"]["regret"] -
                                 m4["evaluation"]["regret"])
        p_all_change = full["structural_P_all"] - s0["structural_P_all"]
        action_same = same_action
        best_gain = delta > 0
        candidate = {"scm_id": scm_id, "template": meta.get("template"),
                     "node_count": meta.get("node_count"), "q_common": qcommon,
                     "g0_zero_error": no_errors, "g0_status": gen_status,
                     "p1_delta": delta, "s0_regret": s0["evaluation"]["regret"],
                     "full_greedy_regret": full["evaluation"]["regret"],
                     "full_greedy_edit_count": len(full["edit_log"]),
                     "full_greedy_cost": full["total_edit_cost"],
                     "full_greedy_edits": full["edit_log"],
                     "full_greedy_structural_P_all": full["structural_P_all"],
                     "s0_structural_P_all": s0["structural_P_all"],
                     "P_all_change_full_minus_s0": p_all_change,
                     "s0_action": s0["evaluation"]["selected_action"],
                     "full_greedy_action": full["evaluation"]["selected_action"],
                     "actions_equal": action_same,
                     "s0_GT_selected_loss": s0["evaluation"]["gt_selected_loss"],
                     "full_greedy_GT_selected_loss": full["evaluation"]["gt_selected_loss"],
                     "m4_regret": m4["evaluation"]["regret"],
                     "m4_edits": m4["edit_log"],
                     "m4_action": m4["evaluation"]["selected_action"],
                     "m4_selected_GT_loss": m4["evaluation"]["gt_selected_loss"],
                     "m4_structural_P_all": m4["structural_P_all"],
                     "m4_cost": m4["total_edit_cost"],
                     "m4_graph_sha256": m4["final_graph_sha256"],
                     "full_graph_sha256": full["final_graph_sha256"],
                     "s0_graph_sha256": s0["final_graph_sha256"],
                     "e2e_input_sha256": payload.get("input_sha256"),
                     "result_sha256": row_sha,
                     "g0_sha256": _digest(g0)}
        per_scm.append(candidate)
    connection.close()

    if len(p1_deltas) != 64:
        errors.append({"error": f"expected 64 complete P1 pairs, found {len(p1_deltas)}"})
    primary_summary = {"n_complete_pairs": len(p1_deltas),
                       "mean_delta": statistics.mean(p1_deltas),
                       "median_delta": statistics.median(p1_deltas),
                       "sample_sd": statistics.stdev(p1_deltas),
                       "sign_counts": _counts(p1_deltas),
                       "mean_s0_regret": statistics.mean(s0_regrets),
                       "mean_full_greedy_regret": statistics.mean(full_regrets),
                       "mean_full_greedy_edit_count": statistics.mean(full_edits),
                       "mean_full_greedy_cost": statistics.mean(full_costs),
                       "full_greedy_noop_n": sum(n == 0 for n in full_edits),
                       "s0_full_greedy_action_same_n": sum(x["actions_equal"] for x in per_scm),
                       "paired_t_ci": _mean_ci(p1_deltas)}
    m4_comparisons = {}
    for pid in ("S0", FULL, "CANONICAL_ORACLE", "M1+M4", "M2+M4", "M3+M4"):
        deltas = pairwise[pid]
        m4_comparisons[pid] = {"n": len(deltas), "mean_other_minus_M4": statistics.mean(deltas),
                               "sign_counts_other_regret_minus_M4": _counts(deltas)}
    policy_b2_means = {pid: statistics.mean(policy_means[(2, pid)]) for pid in POLICY_IDS}
    regret_ties = [r for r in per_scm if r["p1_delta"] == 0]
    worse_full_than_m4 = [r for r in per_scm if r["full_greedy_regret"] > r["m4_regret"]]
    structure_cases = {
        "P_all_improved_but_regret_not_improved": [r for r in per_scm
            if r["P_all_change_full_minus_s0"] < 0 and r["p1_delta"] <= 0],
        "P_all_unchanged_but_regret_changed": [r for r in per_scm
            if r["P_all_change_full_minus_s0"] == 0 and r["p1_delta"] != 0],
        "P_all_improved_but_action_same": [r for r in per_scm
            if r["P_all_change_full_minus_s0"] < 0 and r["actions_equal"]],
        "regret_worsened": [r for r in per_scm if r["p1_delta"] < 0],
        "largest_positive_deltas": sorted(per_scm, key=lambda r: r["p1_delta"], reverse=True)[:5],
        "largest_negative_deltas": sorted(per_scm, key=lambda r: r["p1_delta"])[:5],
        "full_greedy_worse_than_M4": worse_full_than_m4,
    }
    qcommon_deltas = {label: [r["p1_delta"] for r in per_scm if r["q_common"] is value]
                      for label, value in (("q_common", True), ("not_q_common", False))}
    qcommon_summary = {label: {"n": len(v), "mean_delta": statistics.mean(v),
                               "sign_counts": _counts(v)}
                       for label, v in qcommon_deltas.items() if v}
    raw_records = []
    for r in per_scm:
        raw_records.append({"scm_id": r["scm_id"], "result_sha256": r["result_sha256"],
                            "g0_sha256": r["g0_sha256"], "e2e_input_sha256": r["e2e_input_sha256"],
                            "g0_zero_error": r["g0_zero_error"], "p1_delta": r["p1_delta"]})
    result = {
        "audit_schema": "research-c-development-v1-audit-v1",
        "audit_is_read_only": True,
        "run_id": RUN_ID,
        "approval": {"configuration_path": str(config_path), "configuration_canonical_sha256": config_digest,
                     "configuration_file_sha256": _sha256_file(config_path),
                     "manifest_path": str(manifest_path), "manifest_canonical_sha256": manifest_digest,
                     "manifest_file_sha256": _sha256_file(manifest_path),
                     "expected_manifest_canonical_sha256": EXPECTED_MANIFEST_DIGEST,
                     "approved_status": config.get("contract_status"),
                     "preregistration_status": config.get("preregistration_status"),
                     "cohort": config.get("cohort_type"), "master_seed": config.get("rng_protocol", {}).get("master_seed"),
                     "target_admissions": config.get("target_admissions"), "proposal_cap": config.get("proposal_cap"),
                     "runtime_fingerprint": config.get("runtime_fingerprint"),
                     "manifest_source_revision": manifest.get("source_revision")},
        "raw_sources": {"run_directory": str(run_dir),
                        "cohort_database": {"path": str(cohort_db), "bytes": cohort_db.stat().st_size,
                                            "sha256": _sha256_file(cohort_db), "integrity_check": cohort_integrity,
                                            "foreign_key_issues": foreign_key_issues},
                        "proposal_database": {"path": str(proposal_db), "bytes": proposal_db.stat().st_size,
                                              "sha256": _sha256_file(proposal_db), "integrity_check": proposal_integrity},
                        "proposal_stage": {"status": proposal_run[0], "active_seconds": proposal_run[1],
                                           "proposal_count": len(attempt_rows),
                                           "statuses": dict(Counter(a[2] for a in attempt_rows)),
                                           "q_common_admitted": len(qcommon_scm_ids),
                                           "checksums_valid": sum(a["checksum_valid"] for a in attempts),
                                           "attempts": attempts},
                        "cohort_run": {"type": cohort_type, "master_seed": master_seed,
                                       "active_seconds": cohort_active, "source_revision": source,
                                       "code_sha256_matches_manifest": code_hashes == manifest.get("code_sha256"),
                                       "admitted": len(proposal_rows),
                                       "proposal_statuses": dict(proposal_state_counts),
                                       "scm_statuses": dict(Counter(r[1] for r in scm_rows)),
                                       "events": dict(event_rows),
                                       "scm_result_checksums_valid": len(scm_rows) - sum(e.get("error") == "result checksum mismatch" for e in errors)}},
        "integrity": {"errors": errors, "status": "PASS" if not errors else "FAIL",
                      "stale_g0_metadata": {"count": len(stale_metadata), "scm_ids": stale_metadata,
                          "values": {"contract_status": "PROPOSED_NOT_APPROVED",
                                     "test_or_cohort_use": "not_authorized"}},
                      "p1_tie_cross_tab": dict(tie_cross),
                      "p1_tie_action_cross_tab": dict(tie_action_cross),
                      "zero_error_and_noop_cross_tab": noerror_noop},
        "g0_summary": {"generation_status": dict(Counter(
                            next((p.get("fixture_metadata", {}).get("g0_generation", {}).get("generation_status")
                                  for p in [_result_payload(r[:6], [])] if p), None)
                            for r in scm_rows)),
                        "accepted_and_proposed_counts": dict(g0_totals),
                        "accepted_error_counts_by_kind_zone": dict(g0_by_kind_zone)},
        "primary": primary_summary,
        "m4_development_comparisons": m4_comparisons,
        "b2_mean_regret_by_policy": policy_b2_means,
        "secondary": {"paired_s0_minus_full_greedy_mean_by_budget": {
                           str(b): statistics.mean([r["p1_delta"] if b == 2 else
                               policy_means[(b, "S0")][i] - policy_means[(b, FULL)][i]
                               for i, r in enumerate(per_scm)]) for b in (1, 2, 3, 4)},
                       "q_common_subsets": qcommon_summary,
                       "m4_graph_distinct_count": len(m4_graph_groups),
                       "m4_graph_hash_group_sizes": dict(Counter(m4_graph_groups.values())),
                       "m4_edit_summary": {"count": len([e for r in per_scm for e in r["m4_edits"]]),
                                           "mean_edits": statistics.mean(m4_edit_counts),
                                           "mean_cost": statistics.mean(m4_costs),
                                           "no_op_n": m4_noop_count,
                                           "error_kind_counts": dict(m4_edit_kinds),
                                           "task_zone_counts": dict(m4_edit_zones)},
                       "m4_vs_policy_match_counts": {k: dict(v) for k, v in m4_pair_match.items()},
                       "m4_action_counts": dict(m4_action_groups),
                       "m4_regret_value_counts": dict(m4_regret_groups)},
        "structure_vs_regret_cases": structure_cases,
        "cross_policy_structure_regret_examples": {
            "equal_P_all_different_regret_examples_capped_at_12": equal_penalty_different_regret,
            "different_P_all_same_regret_examples_capped_at_12": different_penalty_same_regret},
        "per_scm_p1_and_hashes": raw_records,
    }
    result["audit_payload_sha256"] = _digest(result)
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--approved-config", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    run_dir, output = args.run_dir.resolve(), args.output.resolve()
    if output == run_dir or run_dir in output.parents:
        parser.error("audit output must be outside the immutable raw-results directory")
    if output.exists():
        parser.error(f"refusing to overwrite existing audit output: {output}")
    result = audit(run_dir, args.approved_config, args.manifest)
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2,
                         allow_nan=False).encode("utf-8") + b"\n"
    temp = output.with_name(f".{output.name}.{__import__('os').getpid()}.tmp")
    try:
        with temp.open("xb") as stream:
            stream.write(payload)
            stream.flush()
            __import__('os').fsync(stream.fileno())
        __import__('os').link(temp, output)
    finally:
        if temp.exists():
            temp.unlink()
    print(json.dumps({"audit_output": str(output), "audit_status": result["integrity"]["status"],
                      "audit_payload_sha256": result["audit_payload_sha256"],
                      "p1": result["primary"], "g0_stale_metadata_count": result["integrity"]["stale_g0_metadata"]["count"],
                      "integrity_errors": result["integrity"]["errors"]}, ensure_ascii=False,
                     sort_keys=True))
    return 0 if result["integrity"]["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())

"""Read-only SCM-level analysis of a completed, approved Research C cohort."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.original_objective.analysis import (m4_secondary_delta, p1_delta,
    paired_bootstrap_mean, paired_t_summary, paired_summary)
from research.original_objective.runner import _digest

DEFAULT_BOOTSTRAP_SEED = 2026112302  # PROPOSED only; must be explicitly approved for held-out analysis.
FULL = "M1+M2+M3+M4"
POLICY_IDS = ["S0", *["+".join(s) for s in __import__(
    "research.original_objective.policy_engine", fromlist=["catalog"]).catalog() if s],
              "CANONICAL_ORACLE"]


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def open_ro(path: Path) -> sqlite3.Connection:
    uri = "file:" + quote(str(path.resolve()).replace("\\", "/"), safe=":/") + "?mode=ro"
    db = sqlite3.connect(uri, uri=True)
    db.execute("PRAGMA query_only=ON")
    return db


def _result_payload(raw: str, expected_sha: str) -> dict:
    envelope = json.loads(raw)
    payload = envelope.get("payload")
    if not isinstance(payload, dict):
        raise ValueError("missing result payload envelope")
    actual_sha = _digest(payload)
    if actual_sha != expected_sha or envelope.get("payload_sha256") != expected_sha:
        raise ValueError("result checksum mismatch")
    return payload


def _load_analysis_bundle(config_path: Path, manifest_path: Path) -> tuple[dict, dict]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if (config.get("contract_status") != "USER_APPROVED"
            or config.get("research_cohort_execution_enabled") is not True
            or config.get("preregistration_status") != "PREREGISTERED"):
        raise ValueError("analysis requires a user-approved, preregistered configuration")
    if manifest.get("approval_status") != "USER_APPROVED":
        raise ValueError("analysis manifest is not user-approved")
    if manifest.get("manifest_version") != "research-c-execution-manifest-v1":
        raise ValueError("unsupported manifest version")
    if manifest.get("config_sha256") != _digest(config):
        raise ValueError("approved configuration hash does not match manifest")
    cohort = config.get("cohort_type")
    if cohort not in {"development", "independent_evaluation"}:
        raise ValueError("unsupported cohort type")
    prefix = "development-" if cohort == "development" else "independent-evaluation-"
    if not str(config.get("run_id", "")).startswith(prefix):
        raise ValueError("run ID does not match cohort namespace")
    for key in ("run_id", "cohort_type", "configuration_version", "runtime_fingerprint", "output_root"):
        expected = cohort if key == "cohort_type" else config.get(key)
        if manifest.get(key) != expected:
            raise ValueError(f"manifest/config {key} mismatch")
    if manifest.get("excluded_untracked_paths") != [".build_reframed/"]:
        raise ValueError("manifest does not preserve the declared excluded build path")
    if manifest.get("contract_sha256") != _digest({
        key: config[key] for key in ("configuration_version", "contract_status",
            "preregistration_status", "population", "scm", "task", "g0", "repair", "evaluation")}):
        raise ValueError("scientific contract hash mismatch")
    if manifest.get("resource_limits_sha256") != _digest(config["resource_limits"]):
        raise ValueError("resource limit hash mismatch")
    return config, manifest


def analyze(cohort_db_path: Path, proposal_db_path: Path, *, config_path: Path,
            manifest_path: Path, run_id: str | None = None, bootstrap_seed: int,
            bootstrap_replicates: int = 10_000) -> dict:
    approved_config, manifest = _load_analysis_bundle(config_path, manifest_path)
    run_id = run_id or approved_config["run_id"]
    if run_id != approved_config["run_id"]:
        raise ValueError("requested run ID differs from approved configuration")

    db = open_ro(cohort_db_path)
    if db.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
        raise ValueError("cohort SQLite integrity check failed")
    if db.execute("PRAGMA foreign_key_check").fetchall():
        raise ValueError("cohort SQLite foreign key check failed")
    run = db.execute("SELECT cohort_type,master_seed,config_json,config_sha256,code_json,source_json,active_seconds "
                     "FROM runs WHERE run_id=?", (run_id,)).fetchone()
    if not run:
        raise ValueError(f"run not found: {run_id}")
    cohort_type, master_seed, config_raw, config_sha, code_raw, source_raw, active_seconds = run
    run_config, code_hashes, source = map(json.loads, (config_raw, code_raw, source_raw))
    if cohort_type != "RESEARCH_COHORT":
        raise ValueError("input is not a Research C cohort run")
    if run_config.get("cohort_type") != "RESEARCH_COHORT" or run_config.get("run_id") != run_id:
        raise ValueError("cohort run/config binding mismatch")
    if config_sha != _digest({"config": run_config, "code_sha256": code_hashes}):
        raise ValueError("run config/code binding checksum mismatch")
    if (master_seed != approved_config["rng_protocol"]["master_seed"]
            or source != manifest.get("source_revision")
            or code_hashes != manifest.get("code_sha256")
            or approved_config.get("runtime_fingerprint") != manifest.get("runtime_fingerprint")):
        raise ValueError("ledger source/runtime/seed does not match approved manifest")

    scm_rows = db.execute("SELECT scm_id,status,result_json,result_sha256,failure_code,failure_reason "
                          "FROM scms WHERE run_id=? ORDER BY ordinal", (run_id,)).fetchall()
    proposal_rows = db.execute("SELECT proposal_id,status,reason,topology_hash,scm_id,proposal_json,proposal_sha256 "
                               "FROM proposals WHERE run_id=? ORDER BY rowid", (run_id,)).fetchall()
    events = dict(db.execute("SELECT to_status,COUNT(*) FROM events WHERE run_id=? GROUP BY to_status",
                             (run_id,)).fetchall())
    db.close()

    stage = open_ro(proposal_db_path)
    if stage.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
        raise ValueError("proposal SQLite integrity check failed")
    stage_row = stage.execute("SELECT status,active_seconds,cohort_type,master_seed,target_admissions,proposal_cap,config_sha256,config_json "
                              "FROM proposal_stage_runs WHERE run_id=?",
                              (run_id,)).fetchone()
    attempts = stage.execute("SELECT attempt,proposal_id,status,proposal_json,proposal_sha256,failure_code,failure_reason "
                             "FROM proposal_attempts WHERE run_id=? ORDER BY attempt", (run_id,)).fetchall()
    stage.close()
    if not stage_row:
        raise ValueError("proposal-stage ledger entry missing")
    expected_stage_cohort = {"development": "development",
                             "independent_evaluation": "independent_evaluation"}[approved_config["cohort_type"]]
    if (stage_row[0] != "COMPLETED" or stage_row[2] != expected_stage_cohort
            or stage_row[3] != approved_config["rng_protocol"]["master_seed"]
            or stage_row[4] != approved_config["target_admissions"]
            or stage_row[5] != approved_config["proposal_cap"]):
        raise ValueError("proposal-stage ledger does not match approved cohort, RNG, target, or cap")
    stage_binding = json.loads(stage_row[7])
    if (stage_row[6] != _digest(stage_binding)
            or stage_binding.get("run_id") != run_id
            or stage_binding.get("code_sha256") != manifest.get("code_sha256")
            or stage_binding.get("source_revision") != manifest.get("source_revision")
            or stage_binding.get("runtime_fingerprint") != manifest.get("runtime_fingerprint")
            or stage_binding.get("target_admissions") != approved_config["target_admissions"]
            or stage_binding.get("proposal_cap") != approved_config["proposal_cap"]):
        raise ValueError("proposal-stage configuration/checksum does not match approved bundle")
    proposal_attempt_checksums_valid = 0
    for attempt, proposal_id, status, raw, sha, failure_code, failure_reason in attempts:
        if status in {"ELIGIBLE", "STRUCTURALLY_INELIGIBLE"}:
            if not raw or _digest(json.loads(raw)) != sha:
                raise ValueError(f"proposal attempt checksum mismatch: {proposal_id}")
            proposal_attempt_checksums_valid += 1

    admitted_proposals = {}
    q_common_n = 0
    for row in proposal_rows:
        item = json.loads(row[5])
        if _digest(item) != row[6]:
            raise ValueError(f"proposal checksum mismatch: {row[0]}")
        if row[1] == "ADMITTED":
            admitted_proposals[row[4]] = item
            q_common_n += item.get("q_common_eligible") is True

    completed, failures = [], []
    policy_failures = Counter()
    missing_policy_vectors = []
    official_provenance_rows = 0
    g0_contract_rows = 0
    stale_g0_metadata_rows = 0
    rows_by_scm = {}
    for scm_id, status, raw, sha, fail_code, fail_reason in scm_rows:
        if status != "COMPLETED" or not raw:
            failures.append({"scm_id": scm_id, "status": status,
                             "failure_code": fail_code, "failure_reason": fail_reason})
            continue
        try:
            payload = _result_payload(raw, sha)
        except (ValueError, json.JSONDecodeError) as exc:
            failures.append({"scm_id": scm_id, "status": "INVALID_RESULT",
                             "failure_reason": str(exc)})
            continue
        if payload.get("research_regret_result") is not True or payload.get("test_only") is not False:
            raise ValueError(f"cohort result classification mismatch: {scm_id}")
        binding = payload.get("cohort_binding", {})
        if (binding.get("run_id") != run_id or binding.get("scm_id") != scm_id
                or payload.get("source_revision") != source
                or payload.get("code_sha256") != code_hashes
                or payload.get("runtime_fingerprint") != approved_config.get("runtime_fingerprint")):
            raise ValueError(f"per-SCM run provenance binding mismatch: {scm_id}")
        official_provenance_rows += 1
        g0 = payload.get("fixture_metadata", {}).get("g0_generation", {})
        configured = g0.get("rates", {}).get("configured", {})
        if (configured.get("true_adjacency_corruption") != 0.15
                or configured.get("false_adjacency") != 0.05
                or configured.get("conditional_true_error_mix") !=
                   {"FN": 1 / 3, "REV": 1 / 3, "UNRES": 1 / 3}
                or g0.get("summary", {}).get("retries") != 0):
            raise ValueError(f"G0 generation contract metadata mismatch: {scm_id}")
        g0_contract_rows += 1
        stale_g0_metadata_rows += (g0.get("contract_status") == "PROPOSED_NOT_APPROVED"
                                   and g0.get("test_or_cohort_use") == "not_authorized")
        g0_summary = g0.get("summary", {})
        no_g0_errors = sum(g0_summary.get("accepted_by_kind", {}).values()) == 0
        budgets = {b.get("budget"): b for b in payload.get("e2e_result", {}).get("budgets", [])}
        if set(budgets) != {0, 1, 2, 3, 4}:
            failures.append({"scm_id": scm_id, "status": "INCOMPLETE_BUDGET_VECTOR"})
            continue
        policies_by_budget = {}
        for budget, block in budgets.items():
            policies = {p.get("policy_id"): p for p in block.get("policies", [])}
            policies_by_budget[budget] = policies
            s0_at_budget = policies.get("S0")
            for policy_id in POLICY_IDS:
                result = policies.get(policy_id)
                if (result is None or result.get("status") != "OK"
                        or result.get("evaluation_status") != "RESEARCH_OK"):
                    policy_failures[(policy_id, budget)] += 1
                elif s0_at_budget and s0_at_budget.get("status") == "OK" \
                        and result.get("shared_input_sha256") != s0_at_budget.get("shared_input_sha256"):
                    raise ValueError(f"policy shared-input mismatch: {scm_id} B{budget} {policy_id}")
        if any(set(policies_by_budget[b]) != set(POLICY_IDS) for b in policies_by_budget):
            missing_policy_vectors.append(scm_id)
        rows_by_scm[scm_id] = {"payload": payload, "budgets": policies_by_budget,
                               "g0_no_errors": no_g0_errors}
        completed.append(scm_id)

    complete_p1, incomplete_pairs = [], []
    complete_m4, incomplete_m4 = [], []
    m4_pairwise = defaultdict(list)
    policy_regrets = defaultdict(list)
    structural_categories = Counter()
    low_edit_positive = []
    noerror_noop = Counter()
    for scm_id in completed:
        policies_by_budget = rows_by_scm[scm_id]["budgets"]
        for budget, policies in policies_by_budget.items():
            for policy_id in POLICY_IDS:
                record = policies.get(policy_id)
                if record and record.get("status") == "OK" and record.get("evaluation_status") == "RESEARCH_OK":
                    policy_regrets[(budget, policy_id)].append(record["evaluation"]["regret"])
        s0_b0, s0_b2 = policies_by_budget[0].get("S0"), policies_by_budget[2].get("S0")
        if (s0_b0 and s0_b2 and s0_b0.get("status") == "OK" and s0_b2.get("status") == "OK"
                and (s0_b0["final_graph_sha256"], s0_b0["evaluation"]["selected_action"],
                     s0_b0["evaluation"]["regret"]) !=
                    (s0_b2["final_graph_sha256"], s0_b2["evaluation"]["selected_action"],
                     s0_b2["evaluation"]["regret"])):
            raise ValueError(f"S0 B0/B2 baseline mismatch: {scm_id}")
        b2 = policies_by_budget[2]
        s0, full, m4 = b2.get("S0"), b2.get(FULL), b2.get("M4")
        noerror_noop["no_error_g0"] += rows_by_scm[scm_id]["g0_no_errors"]
        if full and full.get("status") == "OK":
            full_noop = len(full.get("edit_log", [])) == 0
            noerror_noop["full_greedy_noop"] += full_noop
            noerror_noop["intersection"] += rows_by_scm[scm_id]["g0_no_errors"] and full_noop
            noerror_noop["no_error_but_greedy_edits"] += rows_by_scm[scm_id]["g0_no_errors"] and not full_noop
            noerror_noop["error_g0_but_greedy_noop"] += not rows_by_scm[scm_id]["g0_no_errors"] and full_noop
        comparison_targets = ["S0", FULL, "CANONICAL_ORACLE", "M1+M4", "M2+M4", "M3+M4"]
        if m4 and m4.get("status") == "OK" and m4.get("evaluation_status") == "RESEARCH_OK":
            for other_id in comparison_targets:
                other = b2.get(other_id)
                if other and other.get("status") == "OK" and other.get("evaluation_status") == "RESEARCH_OK":
                    if other.get("shared_input_sha256") != m4.get("shared_input_sha256"):
                        continue
                    m4_pairwise[other_id].append({
                        "delta_other_minus_m4": other["evaluation"]["regret"] - m4["evaluation"]["regret"],
                        "same_graph": other["final_graph_sha256"] == m4["final_graph_sha256"],
                        "same_action": (other["evaluation"]["selected_action"], other["evaluation"]["selected_k"])
                            == (m4["evaluation"]["selected_action"], m4["evaluation"]["selected_k"]),
                        "other_regret": other["evaluation"]["regret"], "m4_regret": m4["evaluation"]["regret"]})
        if all(p and p.get("status") == "OK" and p.get("evaluation_status") == "RESEARCH_OK"
               for p in (s0, full)):
            if (s0["shared_input_sha256"] != full["shared_input_sha256"]
                    or s0["initial_graph_sha256"] != full["initial_graph_sha256"]):
                incomplete_pairs.append({"scm_id": scm_id, "reason": "P1 shared input/initial graph mismatch"})
                continue
            delta = p1_delta(s0["evaluation"]["regret"], full["evaluation"]["regret"])
            complete_p1.append({"scm_id": scm_id, "delta": delta,
                "s0_regret": s0["evaluation"]["regret"], "full_regret": full["evaluation"]["regret"],
                "s0_action": [s0["evaluation"]["selected_action"], s0["evaluation"]["selected_k"]],
                "full_action": [full["evaluation"]["selected_action"], full["evaluation"]["selected_k"]],
                "same_graph": s0["final_graph_sha256"] == full["final_graph_sha256"],
                "s0_graph_sha256": s0["final_graph_sha256"], "full_graph_sha256": full["final_graph_sha256"],
                "s0_P_all": s0["structural_P_all"], "full_P_all": full["structural_P_all"],
                "candidate_count": full["repair_candidate_count"],
                "candidate_counts_by_metric": full["repair_candidate_counts_by_metric"],
                "edit_count": len(full["edit_log"]), "edit_cost": full["total_edit_cost"],
                "edits": full["edit_log"], "full_stop_reason": full["stop_reason"]})
            changed_action = complete_p1[-1]["s0_action"] != complete_p1[-1]["full_action"]
            changed_graph = not complete_p1[-1]["same_graph"]
            changed_regret = delta != 0
            structural_categories[("graph_changed" if changed_graph else "graph_same",
                                   "action_changed" if changed_action else "action_same",
                                   "regret_changed" if changed_regret else "regret_same")] += 1
            structural_improvement = s0["structural_P_all"] > full["structural_P_all"]
            structural_categories["P_all_improved"] += structural_improvement
            structural_categories["P_all_improved_regret_worsened"] += structural_improvement and delta < 0
            structural_categories["action_changed_regret_tied"] += changed_action and not changed_regret
            if len(full["edit_log"]) <= 1 and delta > 0:
                low_edit_positive.append({"scm_id": scm_id, "edit_count": len(full["edit_log"]),
                                          "cost": full["total_edit_cost"], "delta": delta})
        else:
            incomplete_pairs.append({"scm_id": scm_id,
                "S0_status": None if s0 is None else s0.get("status"),
                "FullGreedy_status": None if full is None else full.get("status")})
        if m4 and full and m4.get("status") == "OK" and full.get("status") == "OK" \
                and m4.get("evaluation_status") == "RESEARCH_OK" and full.get("evaluation_status") == "RESEARCH_OK":
            if m4["shared_input_sha256"] != full["shared_input_sha256"]:
                incomplete_m4.append(scm_id)
                continue
            complete_m4.append({"scm_id": scm_id,
                "delta_m4": m4_secondary_delta(full["evaluation"]["regret"], m4["evaluation"]["regret"]),
                "full_regret": full["evaluation"]["regret"], "m4_regret": m4["evaluation"]["regret"],
                "same_graph": full["final_graph_sha256"] == m4["final_graph_sha256"],
                "same_action": (full["evaluation"]["selected_action"], full["evaluation"]["selected_k"])
                    == (m4["evaluation"]["selected_action"], m4["evaluation"]["selected_k"]),
                "full_cost": full["total_edit_cost"], "m4_cost": m4["total_edit_cost"],
                "full_edit_count": len(full["edit_log"]), "m4_edit_count": len(m4["edit_log"]),
                "full_edits": full["edit_log"], "m4_edits": m4["edit_log"]})
        else:
            incomplete_m4.append(scm_id)

    p1_deltas = [row["delta"] for row in complete_p1]
    if not p1_deltas:
        raise ValueError("no complete P1 pairs available; no imputation is allowed")
    p1 = paired_summary(p1_deltas)
    p1["mean_s0_regret"] = sum(r["s0_regret"] for r in complete_p1) / len(complete_p1)
    p1["mean_full_greedy_regret"] = sum(r["full_regret"] for r in complete_p1) / len(complete_p1)
    p1["mean_edit_count"] = sum(r["edit_count"] for r in complete_p1) / len(complete_p1)
    p1["mean_edit_cost"] = sum(r["edit_cost"] for r in complete_p1) / len(complete_p1)
    p1["mean_modification_opportunities"] = sum(r["candidate_count"] for r in complete_p1) / len(complete_p1)
    p1["mean_candidate_count_by_metric"] = {
        metric: sum(r["candidate_counts_by_metric"].get(metric, 0) for r in complete_p1) / len(complete_p1)
        for metric in ("M1", "M2", "M3", "M4")}
    p1["no_op_n"] = sum(r["edit_count"] == 0 for r in complete_p1)
    p1["action_changed_n"] = sum(r["s0_action"] != r["full_action"] for r in complete_p1)
    p1["same_graph_n"] = sum(r["same_graph"] for r in complete_p1)
    p1["paired_t_ci"] = paired_t_summary(p1_deltas)

    m4_deltas = [r["delta_m4"] for r in complete_m4]
    m4_summary = paired_summary(m4_deltas)
    m4_summary.update({"mean_full_greedy_regret": sum(r["full_regret"] for r in complete_m4) / len(complete_m4),
        "mean_m4_regret": sum(r["m4_regret"] for r in complete_m4) / len(complete_m4),
        "same_graph_n": sum(r["same_graph"] for r in complete_m4),
        "same_action_n": sum(r["same_action"] for r in complete_m4),
        "mean_full_greedy_cost": sum(r["full_cost"] for r in complete_m4) / len(complete_m4),
        "mean_m4_cost": sum(r["m4_cost"] for r in complete_m4) / len(complete_m4),
        "mean_cost_delta_full_minus_m4": sum(r["full_cost"] - r["m4_cost"] for r in complete_m4) / len(complete_m4)})
    m4_edit_zone_counts = Counter()
    m4_edit_kind_counts = Counter()
    full_edit_zone_counts = Counter()
    full_edit_kind_counts = Counter()
    for row in complete_m4:
        for edit in row["m4_edits"]:
            m4_edit_zone_counts["task_zone" if edit.get("task_zone") else "off_task"] += 1
            m4_edit_kind_counts[edit.get("error_type", "UNKNOWN")] += 1
        for edit in row["full_edits"]:
            full_edit_zone_counts["task_zone" if edit.get("task_zone") else "off_task"] += 1
            full_edit_kind_counts[edit.get("error_type", "UNKNOWN")] += 1
    m4_summary["edit_error_kind_counts"] = {"M4": dict(m4_edit_kind_counts), "FullGreedy": dict(full_edit_kind_counts)}
    m4_summary["edit_zone_counts"] = {"M4": dict(m4_edit_zone_counts), "FullGreedy": dict(full_edit_zone_counts)}
    m4_pairwise_summary = {}
    for other_id, rows in m4_pairwise.items():
        deltas = [row["delta_other_minus_m4"] for row in rows]
        m4_pairwise_summary[other_id] = paired_summary(deltas)
        m4_pairwise_summary[other_id].update({
            "delta_definition": f"Regret({other_id}) - Regret(M4); positive favors M4",
            "same_graph_n": sum(row["same_graph"] for row in rows),
            "same_action_n": sum(row["same_action"] for row in rows),
            "mean_other_regret": sum(row["other_regret"] for row in rows) / len(rows),
            "mean_m4_regret": sum(row["m4_regret"] for row in rows) / len(rows)})

    policy_means = {str(budget): {policy: (sum(policy_regrets[(budget, policy)]) / len(policy_regrets[(budget, policy)])
                                      if policy_regrets[(budget, policy)] else None)
                                  for policy in POLICY_IDS}
                    for budget in (0, 1, 2, 3, 4)}
    all_proposals = len(attempts)
    admitted = len(admitted_proposals)
    result = {"analysis_schema": "research-c-cohort-analysis-v1",
        "classification": f"{approved_config['cohort_type'].upper()}_READ_ONLY_ANALYSIS",
        "run_id": run_id, "source_commit": source.get("commit"), "source_tree": source.get("tree"),
        "master_seed": master_seed, "cohort_type": approved_config["cohort_type"].upper(),
        "approval_bundle": {"config_file_sha256": file_sha256(config_path),
            "config_canonical_sha256": _digest(approved_config), "manifest_file_sha256": file_sha256(manifest_path),
            "manifest_canonical_sha256": _digest(manifest),
            "source_revision": source, "code_sha256": code_hashes,
            "runtime_fingerprint": approved_config["runtime_fingerprint"]},
        "source_hashes": {"cohort_database_sha256": file_sha256(cohort_db_path),
                          "proposal_database_sha256": file_sha256(proposal_db_path)},
        "ledger": {"proposal_attempts": all_proposals,
            "proposal_attempt_statuses": dict(Counter(x[2] for x in attempts)),
            "proposal_attempt_checksums_valid": proposal_attempt_checksums_valid,
            "admitted_scms": admitted, "q_common_admitted": q_common_n,
            "completed_scm_rows": sum(row[1] == "COMPLETED" for row in scm_rows),
            "complete_p1_pairs": len(complete_p1), "complete_m4_pairs": len(complete_m4),
            "incomplete_p1_pairs": incomplete_pairs, "incomplete_m4_pairs": incomplete_m4,
            "evaluation_failure_count": sum(policy_failures.values()),
            "policy_failures_by_policy_budget": {f"{k[0]}@B{k[1]}": v for k, v in policy_failures.items()},
            "missing_policy_vectors": missing_policy_vectors,
            "failure_rows": failures, "cohort_events": events,
            "official_provenance_bound_scm_rows": official_provenance_rows,
            "g0_configuration_bound_scm_rows": g0_contract_rows,
            "legacy_g0_metadata_label_rows": stale_g0_metadata_rows,
            "proposal_stage_status": stage_row[0],
            "proposal_active_seconds": stage_row[1], "cohort_active_seconds": active_seconds},
        "p1": p1,
        "bootstrap_sensitivity": {"status": "PROPOSED_SEED_REPRODUCIBILITY_CHECK_ONLY",
            "seed_status": "PROPOSED_NOT_APPROVED", "seed": bootstrap_seed,
            "result": paired_bootstrap_mean(p1_deltas, seed=bootstrap_seed,
                                             replicates=bootstrap_replicates)},
        "m4_development_selected_secondary": m4_summary,
        "m4_development_selected_pairwise_descriptives": m4_pairwise_summary,
        "mean_regret_by_policy_and_budget": policy_means,
        "structure_decision_diagnostics": {
            "full_greedy_vs_s0_b2_categories": {
                "/".join(k) if isinstance(k, tuple) else k: v for k, v in structural_categories.items()},
            "p1_tie_reasons": {"tied_regret_and_same_action": sum(
                row["delta"] == 0 and row["s0_action"] == row["full_action"] for row in complete_p1),
                "tied_regret_but_action_changed": sum(
                row["delta"] == 0 and row["s0_action"] != row["full_action"] for row in complete_p1),
                "no_error_g0": noerror_noop["no_error_g0"], "full_greedy_noop": noerror_noop["full_greedy_noop"],
                "no_error_and_full_greedy_noop": noerror_noop["intersection"],
                "no_error_but_greedy_edits": noerror_noop["no_error_but_greedy_edits"],
                "error_g0_but_greedy_noop": noerror_noop["error_g0_but_greedy_noop"]},
            "at_most_one_full_greedy_edit_and_positive_delta": low_edit_positive,
            "at_most_one_full_greedy_edit_and_positive_delta_n": len(low_edit_positive)},
        "admitted_without_completed_result_n": max(0, admitted - len(completed)),
        "pairing_note": "SCM is the independent unit; repeated policies and budgets are not counted as independent SCMs."}
    result["analysis_payload_sha256"] = _digest(result)
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cohort-db", type=Path, required=True)
    parser.add_argument("--proposal-db", type=Path, required=True)
    parser.add_argument("--run-id")
    parser.add_argument("--approved-config", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--bootstrap-seed", type=int, default=DEFAULT_BOOTSTRAP_SEED)
    parser.add_argument("--bootstrap-replicates", type=int, default=10_000)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    output = args.output.resolve()
    raw_paths = {args.cohort_db.resolve(), args.proposal_db.resolve()}
    if any(output == path or path in output.parents for path in raw_paths):
        parser.error("analysis output must be outside the immutable input database directories")
    if output.exists():
        parser.error(f"refusing to overwrite existing output: {output}")
    report = analyze(args.cohort_db, args.proposal_db, config_path=args.approved_config,
                     manifest_path=args.manifest, run_id=args.run_id,
                     bootstrap_seed=args.bootstrap_seed,
                     bootstrap_replicates=args.bootstrap_replicates)
    output.parent.mkdir(parents=True, exist_ok=True)
    temp = output.with_name(f".{output.name}.{__import__('os').getpid()}.tmp")
    data = json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2,
                      allow_nan=False).encode("utf-8") + b"\n"
    try:
        with temp.open("xb") as stream:
            stream.write(data)
            stream.flush()
            __import__("os").fsync(stream.fileno())
        __import__("os").link(temp, output)
    finally:
        if temp.exists():
            temp.unlink()
    print(json.dumps({"output": str(output), "analysis_payload_sha256": report["analysis_payload_sha256"],
        "p1": report["p1"], "bootstrap_sensitivity": report["bootstrap_sensitivity"],
        "m4": report["m4_development_selected_secondary"]}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Read-only validation and descriptive analysis of an authorized Step 5 run."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import sqlite3
import statistics
from collections import Counter, defaultdict

import numpy as np


EXPECTED_COMMIT = "06cbd7d4e1efbbff45559eef84b280acc9d081ce"
EXPECTED_TREE = "661f50e7cd859f5c32d909730f686cb93251cc59"
EXPECTED_SEED = 20261116
EXPECTED_CAP = 386
EXPECTED_ADMISSIONS = 64
EXPECTED_TYPES = ("FN", "FP", "REV")
EXPECTED_STAGES = ["proposal", "scm", "observations", "error_graphs",
                   "policy_graphs", "recommendations", "gt_evaluation", "composite"]


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      allow_nan=False).encode("utf-8")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_jsonl_readonly(path: Path) -> list[dict]:
    raw = path.read_bytes()
    if raw and not raw.endswith(b"\n"):
        raise ValueError(f"incomplete final record; raw file left untouched: {path.name}")
    events = []
    for line_number, line in enumerate(raw.splitlines(), 1):
        event = json.loads(line)
        event_hash = event.get("event_sha256")
        if not event_hash:
            raise ValueError(f"missing event hash in {path.name}:{line_number}")
        payload = dict(event)
        del payload["event_sha256"]
        if hashlib.sha256(canonical(payload)).hexdigest() != event_hash:
            raise ValueError(f"event hash mismatch in {path.name}:{line_number}")
        if "output_sha256" in event and hashlib.sha256(canonical(event.get("output"))).hexdigest() != event["output_sha256"]:
            raise ValueError(f"output hash mismatch in {path.name}:{line_number}")
        events.append(event)
    return events


def moment_summary(values: list[float]) -> dict:
    array = np.asarray(values, dtype=np.float64)
    if not len(array) or not np.isfinite(array).all():
        raise ValueError("summary requires a nonempty finite vector")
    zeros = int(np.count_nonzero(array == 0.0))
    return {
        "n": int(array.size),
        "mean": float(np.mean(array)),
        "median": float(np.median(array)),
        "sample_sd": float(statistics.stdev(array.tolist())) if array.size > 1 else None,
        "q1_linear": float(np.quantile(array, 0.25, method="linear")),
        "q3_linear": float(np.quantile(array, 0.75, method="linear")),
        "minimum": float(np.min(array)),
        "maximum": float(np.max(array)),
        "positive_n": int(np.count_nonzero(array > 0.0)),
        "negative_n": int(np.count_nonzero(array < 0.0)),
        "zero_n": zeros,
        "zero_fraction": float(zeros / array.size),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    root = args.run_root.expanduser().resolve()
    out = args.output_dir.expanduser().resolve()
    if not (root / "registry.sqlite").is_file() or not (root / "ledgers").is_dir():
        raise SystemExit("run root must contain registry.sqlite and ledgers/")
    if out == root or out.is_relative_to(root):
        raise SystemExit("analysis outputs must be outside the raw run root")

    raw_files = sorted(p for p in root.rglob("*") if p.is_file())
    before = {p: (p.stat().st_size, sha256(p)) for p in raw_files}
    db_uri = (root / "registry.sqlite").as_uri() + "?mode=ro"
    connection = sqlite3.connect(db_uri, uri=True)
    connection.row_factory = sqlite3.Row
    integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
    if integrity != "ok":
        raise ValueError(f"SQLite integrity_check failed: {integrity}")
    cohorts = [dict(row) for row in connection.execute("SELECT * FROM cohorts")]
    proposal_rows = [dict(row) for row in connection.execute(
        "SELECT * FROM proposals WHERE cohort='development' ORDER BY accepted_ordinal,proposal_id,attempt")]
    other_cohorts = connection.execute(
        "SELECT COUNT(*) FROM proposals WHERE cohort!='development'").fetchone()[0]
    connection.close()
    if len(cohorts) != 1 or cohorts[0]["cohort"] != "development":
        raise ValueError("registry must contain only the development cohort binding")
    binding = cohorts[0]
    if (binding["master_seed"] != EXPECTED_SEED or binding["target_eligible"] != EXPECTED_ADMISSIONS
            or binding["proposal_cap"] != EXPECTED_CAP or other_cohorts != 0):
        raise ValueError("registry cohort binding differs from the approved Step 5 contract")
    if len(proposal_rows) != 211:
        raise ValueError(f"unexpected proposal denominator: {len(proposal_rows)}")

    status_counts = Counter(row["status"] for row in proposal_rows)
    reason_counts = Counter((row["status"], row["reason"] or "") for row in proposal_rows)
    accepted = [row for row in proposal_rows if row["scm_id"] is not None]
    if len(accepted) != EXPECTED_ADMISSIONS or any(row["status"] != "completed" for row in accepted):
        raise ValueError("accepted/completed denominator mismatch")
    if len({row["scm_id"] for row in accepted}) != len(accepted):
        raise ValueError("duplicate SCM IDs in registry")
    if len({row["equation_signature_sha256"] for row in accepted}) != len(accepted):
        raise ValueError("duplicate equation signatures in registry")
    ordinals = sorted(row["accepted_ordinal"] for row in accepted)
    # The production registry stores zero-based admission ordinals; ordinal 0
    # is the first admission and receives the preregistered +1 direction.
    if ordinals != list(range(EXPECTED_ADMISSIONS)):
        raise ValueError("admission ordinals are missing or duplicated")
    if any(row["delta"] != (1 if row["accepted_ordinal"] % 2 == 0 else -1) for row in accepted):
        raise ValueError("delta does not alternate by admitted ordinal")

    per_scm = []
    policy_graph_same = Counter()
    policy_action_same = Counter()
    policy_k_same = Counter()
    fallback_counts = Counter()
    type_differences = defaultdict(list)
    type_global_regrets = defaultdict(list)
    type_task_regrets = defaultdict(list)
    subgroup_template = defaultdict(list)
    subgroup_delta = defaultdict(list)
    subgroup_node_count = defaultdict(list)
    ledgers_seen = set()

    for row in accepted:
        ledger_path = Path(row["ledger_path"]).resolve()
        if not ledger_path.is_relative_to(root) or not ledger_path.is_file():
            raise ValueError(f"missing/out-of-root ledger for {row['scm_id']}")
        if ledger_path in ledgers_seen:
            raise ValueError("two admissions point to the same ledger")
        ledgers_seen.add(ledger_path)
        events = load_jsonl_readonly(ledger_path)
        expected_names = [f"stage:{name}" for name in EXPECTED_STAGES] + ["terminal"]
        if [event["event"] for event in events] != expected_names:
            raise ValueError(f"incomplete or misordered ledger for {row['scm_id']}")
        for event in events:
            if (event.get("scm_id") != row["scm_id"] or event.get("cohort") != "development"
                    or event.get("rng_key") != row["rng_key"] or event.get("config_sha256") != row["config_sha256"]
                    or event.get("input_sha256") != row["input_sha256"]):
                raise ValueError(f"ledger/registry binding mismatch for {row['scm_id']}")
        terminal = events[-1]
        if terminal.get("status") != "OK" or terminal.get("result_sha256") is None:
            raise ValueError(f"non-success terminal for completed SCM {row['scm_id']}")
        outputs = {event["event"].split(":", 1)[1]: event["output"] for event in events[:-1]}
        proposal = outputs["proposal"]
        recommendations = outputs["recommendations"]
        gt = outputs["gt_evaluation"]
        composite = outputs["composite"]
        if proposal["master_seed"] != EXPECTED_SEED or proposal["accepted"] is not True:
            raise ValueError("proposal seed/eligibility mismatch")
        if composite["complete"] is not True or composite["types_complete"] is not True or composite["gt_evaluation_performed"] is not True:
            raise ValueError(f"incomplete SCM composite {row['scm_id']}")
        if not isinstance(composite["D_i"], (int, float)) or not math.isfinite(composite["D_i"]):
            raise ValueError(f"nonfinite SCM composite {row['scm_id']}")
        diffs = {}
        for kind in EXPECTED_TYPES:
            result = gt[kind]
            pair = recommendations[kind]
            if result["paired_status"] != "OK" or result["gt_evaluation_performed"] is not True:
                raise ValueError(f"incomplete GT type {kind} for {row['scm_id']}")
            g = float(result["global_regret"])
            t = float(result["task_focused_regret"])
            d = float(result["difference"])
            if not all(math.isfinite(value) for value in (g, t, d)) or g < 0 or t < 0:
                raise ValueError(f"invalid regret value for {row['scm_id']} {kind}")
            if not math.isclose(d, g - t, rel_tol=0.0, abs_tol=1e-12):
                raise ValueError(f"paired difference mismatch for {row['scm_id']} {kind}")
            diffs[kind] = d
            type_differences[kind].append(d)
            type_global_regrets[kind].append(g)
            type_task_regrets[kind].append(t)
            fallback_counts[f"{kind}:Global"] += int(bool(result["global_fallback_used"]))
            fallback_counts[f"{kind}:TaskFocused"] += int(bool(result["task_fallback_used"]))
            global_graph = pair["global_final_graph"]
            focused_graph = pair["task_focused_final_graph"]
            policy_graph_same[kind] += int(global_graph == focused_graph)
            global_selection = pair["global_selection"]
            focused_selection = pair["task_focused_selection"]
            policy_action_same[kind] += int(global_selection["action"] == focused_selection["action"])
            policy_k_same[kind] += int(global_selection["selected_k"] == focused_selection["selected_k"])
            if global_selection["target"] != focused_selection["target"] or global_selection["target_node"] != focused_selection["target_node"]:
                raise ValueError(f"paired methods do not share task target for {row['scm_id']} {kind}")
        expected_di = math.fsum(diffs[kind] for kind in EXPECTED_TYPES) / 3.0
        if not math.isclose(expected_di, float(composite["D_i"]), rel_tol=0.0, abs_tol=1e-12):
            raise ValueError(f"composite mean differs from FN/FP/REV vector for {row['scm_id']}")
        item = {
            "scm_id": row["scm_id"], "proposal_id": row["proposal_id"],
            "accepted_ordinal": row["accepted_ordinal"], "delta": row["delta"],
            "template": proposal["template"], "node_count": proposal["node_count"],
            "action": proposal["action"], "target": proposal["target"],
            "type_differences": diffs,
            "global_regret": {kind: float(gt[kind]["global_regret"]) for kind in EXPECTED_TYPES},
            "task_focused_regret": {kind: float(gt[kind]["task_focused_regret"]) for kind in EXPECTED_TYPES},
            "D_i": float(composite["D_i"]),
            "fallback_any": any(bool(gt[kind]["global_fallback_used"] or gt[kind]["task_fallback_used"])
                                 for kind in EXPECTED_TYPES),
        }
        per_scm.append(item)
        subgroup_template[item["template"]].append(item["D_i"])
        subgroup_delta[str(item["delta"])].append(item["D_i"])
        subgroup_node_count[str(item["node_count"])].append(item["D_i"])

    if len(ledgers_seen) != EXPECTED_ADMISSIONS:
        raise ValueError("registry accepted denominator differs from unique ledger denominator")
    if status_counts != Counter({"completed": 64, "structural_rejected": 145, "proposal_failed": 2}):
        raise ValueError(f"unexpected status denominator: {status_counts}")

    values = [item["D_i"] for item in per_scm]
    delta_counts = Counter(str(item["delta"]) for item in per_scm)
    templates = Counter(item["template"] for item in per_scm)
    node_counts = Counter(str(item["node_count"]) for item in per_scm)
    regret_summary = {
        "SCM_composite_D_i": moment_summary(values),
        "by_error_type_D_Global_minus_TaskFocused": {
            kind: moment_summary(type_differences[kind]) for kind in EXPECTED_TYPES},
        "Global_regret_by_error_type": {kind: moment_summary(type_global_regrets[kind]) for kind in EXPECTED_TYPES},
        "TaskFocused_regret_by_error_type": {kind: moment_summary(type_task_regrets[kind]) for kind in EXPECTED_TYPES},
        "by_delta": {key: moment_summary(rows) for key, rows in subgroup_delta.items()},
        "by_template": {key: moment_summary(rows) for key, rows in subgroup_template.items()},
        "by_node_count": {key: moment_summary(rows) for key, rows in subgroup_node_count.items()},
    }
    graph_comparisons = {
        kind: {"same_final_graph_n": policy_graph_same[kind], "n": EXPECTED_ADMISSIONS,
               "same_final_graph_rate": policy_graph_same[kind] / EXPECTED_ADMISSIONS,
               "same_action_n": policy_action_same[kind],
               "same_selected_k_n": policy_k_same[kind]}
        for kind in EXPECTED_TYPES
    }
    ordering = sorted(per_scm, key=lambda item: item["D_i"])
    summary = {
        "schema_version": 1,
        "cohort": "development",
        "master_seed": EXPECTED_SEED,
        "approved_commit": EXPECTED_COMMIT,
        "approved_tree": EXPECTED_TREE,
        "registry_integrity": integrity,
        "counts": {
            "topology_proposals": len(proposal_rows),
            "q_common_structural_rejections": status_counts["structural_rejected"],
            "q_common_structurally_eligible": len(accepted),
            "registry_accepted": len(accepted),
            "scm_generation_success": len(accepted),
            "three_type_evaluation_complete": len(accepted),
            "composite_available": len(accepted),
            "post_admission_failures": sum(row["status"] == "failed" for row in accepted),
            "pre_admission_topology_or_task_failures": status_counts["proposal_failed"],
            "unexpected_generator_errors": status_counts["generator_error"],
            "shortfall_eligible": EXPECTED_ADMISSIONS - len(accepted),
            "resource_cap_reached": False,
            "fallback_uses": sum(fallback_counts.values()),
            "delta_counts": dict(delta_counts),
            "template_counts": dict(templates),
            "node_count_counts": dict(node_counts),
            "status_reason_counts": {f"{status}|{reason or '(none)'}": count
                                      for (status, reason), count in reason_counts.items()},
        },
        "analysis": regret_summary,
        "paired_policy_comparisons": graph_comparisons,
        "extreme_D_i": {"lowest": ordering[:5], "highest": ordering[-5:]},
        "limitations": [
            "Option B descriptive analysis only; no confirmatory superiority/equivalence claim.",
            "Development cohort is not an independent replication or a population-level guarantee.",
            "All three error types are repeated measures within SCM; the independent unit is SCM.",
        ],
        "per_scm": per_scm,
    }

    out.mkdir(parents=True, exist_ok=True)
    csv_path = out / "STEP5_DEVELOPMENT_SCM_SUMMARY.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["scm_id", "proposal_id", "accepted_ordinal", "delta",
            "template", "node_count", "action", "target", "FN_D", "FP_D", "REV_D", "D_i",
            "FN_Global_Regret", "FN_TaskFocused_Regret", "FP_Global_Regret", "FP_TaskFocused_Regret",
            "REV_Global_Regret", "REV_TaskFocused_Regret", "fallback_any"])
        writer.writeheader()
        for item in per_scm:
            writer.writerow({"scm_id": item["scm_id"], "proposal_id": item["proposal_id"],
                "accepted_ordinal": item["accepted_ordinal"], "delta": item["delta"],
                "template": item["template"], "node_count": item["node_count"],
                "action": item["action"], "target": item["target"],
                "FN_D": item["type_differences"]["FN"], "FP_D": item["type_differences"]["FP"],
                "REV_D": item["type_differences"]["REV"], "D_i": item["D_i"],
                "FN_Global_Regret": item["global_regret"]["FN"],
                "FN_TaskFocused_Regret": item["task_focused_regret"]["FN"],
                "FP_Global_Regret": item["global_regret"]["FP"],
                "FP_TaskFocused_Regret": item["task_focused_regret"]["FP"],
                "REV_Global_Regret": item["global_regret"]["REV"],
                "REV_TaskFocused_Regret": item["task_focused_regret"]["REV"],
                "fallback_any": item["fallback_any"]})
    summary_path = out / "STEP5_DEVELOPMENT_ANALYSIS_SUMMARY.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    after_files = sorted(p for p in root.rglob("*") if p.is_file())
    after = {p: (p.stat().st_size, sha256(p)) for p in after_files}
    if before != after:
        raise ValueError("raw run root changed during read-only analysis")
    inventory = {
        "schema_version": 1,
        "raw_root": str(root),
        "cohort": "development",
        "master_seed": EXPECTED_SEED,
        "approved_commit": EXPECTED_COMMIT,
        "approved_tree": EXPECTED_TREE,
        "registry_integrity": integrity,
        "proposal_rows": len(proposal_rows),
        "accepted_scm_ledgers": len(ledgers_seen),
        "raw_root_file_count": len(raw_files),
        "raw_root_bytes": sum(size for size, _ in before.values()),
        "raw_files": [{"path": p.relative_to(root).as_posix(), "size_bytes": before[p][0],
                       "sha256": before[p][1]} for p in raw_files],
        "raw_unchanged_during_analysis": True,
    }
    inventory_path = out / "STEP5_DEVELOPMENT_RAW_INVENTORY.json"
    inventory_path.write_text(json.dumps(inventory, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"summary": summary_path.as_posix(), "csv": csv_path.as_posix(),
                      "inventory": inventory_path.as_posix(), "counts": summary["counts"],
                      "D_i": summary["analysis"]["SCM_composite_D_i"],
                      "type_differences": summary["analysis"]["by_error_type_D_Global_minus_TaskFocused"],
                      "paired_comparisons": graph_comparisons,
                      "raw_files": len(raw_files), "raw_root_bytes": inventory["raw_root_bytes"]},
                     sort_keys=True))


if __name__ == "__main__":
    main()

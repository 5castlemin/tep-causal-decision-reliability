"""Independent hash/schema/numeric audit of saved final artifacts.

This post-run verifier intentionally does not import the final runner or its
analysis module. It reads only saved manifests, recommendations and response
vectors and emits aggregate checks; response rows remain outside Git.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
from pathlib import Path

import numpy as np


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def close(a: float, b: float, *, tol: float = 2e-13) -> bool:
    return math.isclose(float(a), float(b), rel_tol=tol, abs_tol=tol)


def audit(root: Path, repo: Path) -> dict:
    root, repo = root.resolve(), repo.resolve()
    read = lambda name: json.loads((root / name).read_text(encoding="utf-8"))
    lock = read("final_run_lock.json")
    run = read("completion.json")
    execution = read("execution_manifest.json")
    response_manifest = read("evaluation_manifest.json")
    recommendation_path = root / "recommendations.json"
    recommendation = json.loads(recommendation_path.read_text(encoding="utf-8"))
    analysis = read("independent_analysis.json")
    contract_path = repo / "research/external_validation/semisynthetic_final/final_contract.json"
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    contract_sha = sha(contract_path)
    checks = {}
    checks["run_status"] = run.get("final_gate") == "EXTERNAL_FINAL_EVALUATION_VERIFIED"
    checks["run_lock_hash"] = sha(root / "final_run_lock.json") == run["run_lock_sha256"]
    checks["execution_manifest_hash"] = sha(root / "execution_manifest.json") == run["execution_manifest_sha256"]
    checks["response_manifest_hash"] = sha(root / "evaluation_manifest.json") == run["evaluation_manifest_sha256"]
    checks["analysis_hash"] = sha(root / "independent_analysis.json") == run["independent_analysis_sha256"]
    checks["contract_binding"] = contract_sha == lock["contract_sha256"] == execution["contract_sha256"]
    checks["recommendation_raw_hash"] = sha(recommendation_path) == run["recommendation_sha256"] == response_manifest["recommendation_raw_sha256"]
    body = dict(recommendation)
    content_sha = body.pop("content_sha256", None)
    checks["recommendation_content_hash"] = hashlib.sha256(canonical(body)).hexdigest() == content_sha
    locked_tree = subprocess.check_output(["git", "-C", str(repo), "rev-parse",
        f"{lock['repository']['commit']}^{{tree}}"], text=True).strip()
    ancestry = subprocess.run(["git", "-C", str(repo), "merge-base", "--is-ancestor",
        lock["repository"]["commit"], "HEAD"], check=False)
    checks["repository_locked_revision_in_history"] = locked_tree == lock["repository"]["tree"] and ancestry.returncode == 0
    code_checks = {}
    for name, expected in lock["code_sha256"].items():
        p = repo / name
        code_checks[name] = p.is_file() and sha(p) == expected
    checks["all_locked_code_bytes"] = all(code_checks.values())
    checks["execution_code_binding"] = execution["code_sha256"] == lock["code_sha256"]

    records = sorted(response_manifest["action_records"], key=lambda row: row["index"])
    vectors, action_stats, losses = [], [], []
    target, scale = float(lock["task"]["target"]), float(lock["task"]["scale"])
    actions = [float(x) for x in lock["task"]["actions"]]
    checks["five_action_records"] = len(records) == len(actions) == 5
    for idx, record in enumerate(records):
        path = root / "response_vectors" / record["filename"]
        raw_sha = sha(path)
        y = np.load(path, allow_pickle=False)
        valid = y.shape == (2500,) and y.dtype == np.float64 and bool(np.isfinite(y).all())
        checks[f"action_{idx}_vector"] = raw_sha == record["response_sha256"] and valid and record["rows"] == 2500 and record["action"] == actions[idx]
        n = len(y)
        mean, var = float(y.mean()), float(y.var(ddof=1))
        loss = ((mean - target) ** 2 - var / n) / scale**2
        vectors.append(y); losses.append(loss)
        action_stats.append({"action": actions[idx], "n": n, "mean": mean,
            "sample_variance_ddof1": var, "standard_error": math.sqrt(var/n),
            "mean_minus_target": mean-target, "bias_corrected_loss": loss,
            "response_file_sha256": raw_sha})
    checks["total_response_rows"] = sum(map(len, vectors)) == 12500 == response_manifest["total_rows"] == run["intervention_rows"]
    checks["recommendation_grid"] = len(recommendation["recommendations"]) == 17000 == run["recommendation_rows"]
    checks["all_final_G0_ids"] = recommendation["g0_seed_ids"] == list(range(703001, 703201))

    loss_by_action = dict(zip(actions, losses))
    recs = {(r["g0_seed_id"], r["budget"], r["policy_id"]): r for r in recommendation["recommendations"]}
    checks["unique_recommendation_keys"] = len(recs) == 17000
    full = "M1+M2+M3+M4"
    primary_values, secondary_values = [], []
    curves = []
    policies = lock["learner_and_repair"]["policies"]
    for budget in range(5):
        for policy in policies:
            rows = [recs[(sid, budget, policy)] for sid in recommendation["g0_seed_ids"]]
            curves.append({"budget": budget, "policy": policy, "g0_count": len(rows),
                "mean_bias_corrected_loss": sum(loss_by_action[float(r["recommended_action"])] for r in rows)/len(rows),
                "mean_edit_cost": sum(float(r["repair_cost"]) for r in rows)/len(rows),
                "mean_task_zone_edits": sum(int(r["task_zone_edit_count"]) for r in rows)/len(rows),
                "mean_off_task_edits": sum(int(r["off_task_edit_count"]) for r in rows)/len(rows),
                "no_op_rate": sum(float(r["repair_cost"]) == 0 for r in rows)/len(rows),
                "unused_budget_rate": sum(int(r["unused_budget"]) > 0 for r in rows)/len(rows)})
    for sid in recommendation["g0_seed_ids"]:
        s0 = recs[(sid, 2, "S0")]
        fg = recs[(sid, 2, full)]
        m4 = recs[(sid, 2, "M4")]
        primary_values.append(loss_by_action[float(s0["recommended_action"])] - loss_by_action[float(fg["recommended_action"])])
        secondary_values.append(loss_by_action[float(m4["recommended_action"])] - loss_by_action[float(fg["recommended_action"])])
    primary, secondary = sum(primary_values)/200, sum(secondary_values)/200
    checks["independent_primary_recalculation"] = close(primary, analysis["primary_B2_S0_minus_FullGreedy"]["mean_delta_loss_bc"])
    checks["independent_secondary_recalculation"] = close(secondary, analysis["secondary_B2_M4_minus_FullGreedy"]["mean_delta_loss_bc"])
    checks["independent_action_means_and_losses"] = all(
        close(stat["mean"], analysis["action_summaries"][str(stat["action"])]["mean"]) and
        close(stat["sample_variance_ddof1"], analysis["action_summaries"][str(stat["action"])]["sample_variance"]) and
        close(stat["bias_corrected_loss"], analysis["action_summaries"][str(stat["action"])]["bias_corrected_loss"])
        for stat in action_stats)
    checked_curves = analysis["policy_budget_curve"]
    curve_idx={(row["budget"],row["policy"]):row for row in checked_curves}
    checks["independent_85_policy_budget_recalculation"] = len(curves)==85 and all(
        close(row["mean_bias_corrected_loss"], curve_idx[(row["budget"],row["policy"])]["mean_bias_corrected_loss"]) and
        close(row["mean_edit_cost"], curve_idx[(row["budget"],row["policy"])]["mean_edit_cost"]) and
        close(row["mean_task_zone_edits"], curve_idx[(row["budget"],row["policy"])]["mean_task_zone_edit_count"]) and
        close(row["mean_off_task_edits"], curve_idx[(row["budget"],row["policy"])]["mean_off_task_edit_count"])
        for row in curves)
    checks["bootstrap_replications"] = analysis["primary_intervals"]["replicates"] == 10000 and all(
        len(analysis["primary_intervals"][key])==2 for key in ("g0_only_95","action_mc_only_95","two_source_95"))
    checks["final_samples_not_reused"] = response_manifest["rows_reused_from_prior_evaluation"] == 0
    result={"schema":"RESEARCH_D_FINAL_INDEPENDENT_ARTIFACT_AUDIT_V1",
        "status":"PASS" if all(checks.values()) else "FAIL", "checks":checks,
        "failed_checks":[key for key,value in checks.items() if not value],
        "run_id":run["run_id"], "source_commit":lock["repository"]["commit"],
        "source_tree":lock["repository"]["tree"], "contract_sha256":contract_sha,
        "run_lock_sha256":sha(root/"final_run_lock.json"),
        "execution_manifest_sha256":sha(root/"execution_manifest.json"),
        "recommendation_raw_sha256":sha(recommendation_path),
        "recommendation_content_sha256":content_sha,
        "response_manifest_sha256":sha(root/"evaluation_manifest.json"),
        "response_file_sha256_by_action":{str(x["action"]):x["response_file_sha256"] for x in action_stats},
        "independent_action_statistics":action_stats,
        "independent_primary_delta":primary,"analyzer_primary_delta":analysis["primary_B2_S0_minus_FullGreedy"]["mean_delta_loss_bc"],
        "independent_secondary_delta":secondary,"analyzer_secondary_delta":analysis["secondary_B2_M4_minus_FullGreedy"]["mean_delta_loss_bc"],
        "independent_policy_budget_curve":curves,
        "analyzer_primary_intervals":analysis["primary_intervals"],
        "resource_supervision_status":read("resource_supervision.json")["status"],
        "resource_peak_process_tree_rss_bytes":read("resource_supervision.json")["peak_process_tree_rss_bytes"],
        "resource_elapsed_seconds":read("resource_supervision.json")["elapsed_seconds"],
        "no_raw_response_values_in_audit":True}
    if not all(checks.values()):
        raise ValueError("one or more final artifact audit checks failed: "+", ".join(result["failed_checks"]))
    return result


def main(argv=None):
    p=argparse.ArgumentParser()
    p.add_argument("--external-root",type=Path,required=True)
    p.add_argument("--repo-root",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args(argv)
    result=audit(args.external_root,args.repo_root)
    out=args.output
    out.parent.mkdir(parents=True,exist_ok=True)
    if out.exists(): raise FileExistsError("audit output already exists")
    out.write_text(json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps({"status":result["status"],"checks":len(result["checks"]),
        "primary":result["independent_primary_delta"],"output_sha256":sha(out)},sort_keys=True))


if __name__=="__main__":
    main()

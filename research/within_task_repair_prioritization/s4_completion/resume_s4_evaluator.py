"""Continue only the locked S4 evaluator from preserved private pilot inputs.

This entry point never generates proposals, G0s, SCM parameters, observations,
recommendations, or sampled intervention responses. It verifies the persisted
checkpoint and evaluates the already locked recommendation graphs analytically.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "src")]
import run_s4_pilot as pilot
from research.original_objective import policy_engine as pe

OUT = Path(os.environ.get("S4_PILOT_OUTPUT", r"C:\DAT_RESEARCH\research-s4\pilot-20261127-v1"))
CHECKPOINT = OUT / "evaluator_resume_lock.json"
INPUTS = OUT / "pilot_inputs_private.json"
RECOMMENDATIONS = OUT / "recommendation_manifest_private.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(checkpoint: dict) -> dict:
    if checkpoint.get("status") != "LOCKED_CHECKPOINT_CONTINUATION":
        raise ValueError("missing explicit checkpoint continuation lock")
    if subprocess.check_output(["git", "-C", str(ROOT), "status", "--porcelain=v1"], text=True).strip():
        raise ValueError("continuation source checkout is not clean")
    commit = subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()
    tree = subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD^{tree}"], text=True).strip()
    if commit != checkpoint["continuation_commit"] or tree != checkpoint["continuation_tree"]:
        raise ValueError("continuation commit/tree does not match lock")
    for name, digest in checkpoint["checkpoint_files"].items():
        path = OUT / name
        if not path.is_file() or sha(path) != digest:
            raise ValueError(f"preserved checkpoint digest mismatch: {name}")
    expected_runner = checkpoint["runner_sha256"]
    if sha(HERE / "run_s4_pilot.py") != expected_runner:
        raise ValueError("corrected evaluator source digest mismatch")
    if sha(Path(__file__)) != checkpoint["resume_script_sha256"]:
        raise ValueError("continuation script digest mismatch")
    if checkpoint["recommendation_binding"]["recommendation_manifest_sha256"] != sha(RECOMMENDATIONS):
        raise ValueError("recommendation manifest is not the locked one")
    return {"commit": commit, "tree": tree, "runner_sha256": expected_runner,
            "resume_script_sha256": sha(Path(__file__)),
            "checkpoint_files": dict(checkpoint["checkpoint_files"])}


def main() -> None:
    if not CHECKPOINT.is_file():
        raise FileNotFoundError("checkpoint continuation lock was not provided")
    checkpoint = json.loads(CHECKPOINT.read_text(encoding="utf-8"))
    provenance = verify(checkpoint)
    outputs = ("unit_results_private.json", "candidate_values_private.json",
               "interaction_values_private.json", "policy_results_private.json",
               "public_policy_aggregates.csv", "pilot_summary_private.json",
               "attempts_summary.json", "pilot_artifact_manifest.json")
    if any((OUT / name).exists() for name in outputs):
        raise FileExistsError("refusing to overwrite any evaluator continuation output")
    manifest = json.loads(RECOMMENDATIONS.read_text(encoding="utf-8"))
    binding = checkpoint["recommendation_binding"]
    if len(manifest) != binding["rows"]:
        raise ValueError("recommendation row count mismatch")
    by_unit: dict[tuple[str, str], dict] = {}
    for row in manifest:
        by_unit.setdefault((row["cohort"], row["scm_id"]), {})[row["graph_hash"]] = {
            "selected_k": row["selected_k"], "selected_action": row["selected_action"],
            "target": row["target"], "scale": row["scale"]}
    raw_units = json.loads(INPUTS.read_text(encoding="utf-8"))
    if len(raw_units) != checkpoint["n_units"]:
        raise ValueError("private input unit count mismatch")
    unit_states = []
    for raw in raw_units:
        unit = dict(raw)
        unit["observations"] = np.asarray(raw["observations"], dtype=np.float64)
        unit["initial_graph"] = pe.state(
            [tuple(e) for e in raw["initial_graph"]["directed_edges"]],
            unresolved=[tuple(e) for e in raw["initial_graph"]["unresolved_pairs"]])
        unit["config"] = pilot.make_config()
        states, policies, diagnostics = pilot.build_states(unit, unit["cohort"])
        recs = by_unit.get((unit["cohort"], unit["scm_id"]), {})
        if set(states) != set(recs):
            raise ValueError(f"locked recommendation graph set mismatch for {unit['scm_id']}")
        unit_states.append({"unit": unit, "states": states, "policies": policies,
                            "diagnostics": diagnostics[0], "recommendations": recs})
    started = time.perf_counter()
    unit_rows, candidate_rows, interactions, policy_rows = pilot.evaluator_stage(
        unit_states, binding, OUT, started)
    for name, rows in (("unit_results_private.json", unit_rows),
                       ("candidate_values_private.json", candidate_rows),
                       ("interaction_values_private.json", interactions),
                       ("policy_results_private.json", policy_rows)):
        pilot.write_json(OUT / name, rows)
    cohort_meta = json.loads((OUT / "cohort_generation_summary.json").read_text(encoding="utf-8"))
    pilot.write_csv(OUT / "public_policy_aggregates.csv", pilot.summarize(
        unit_rows, candidate_rows, interactions, policy_rows, cohort_meta, binding,
        provenance, started)["policy_aggregates"])
    summary = pilot.summarize(unit_rows, candidate_rows, interactions, policy_rows,
                              cohort_meta, binding, provenance, started)
    summary["continuation"] = {"mode": "EVALUATOR_ONLY_FROM_PRESERVED_CHECKPOINT",
                               "new_scm": 0, "new_g0": 0, "new_observation_rows": 0,
                               "new_intervention_rows": 0}
    summary["private_artifact_sha256"] = {
        p.name: sha(p) for p in sorted(OUT.iterdir()) if p.is_file() and p.name != "pilot_summary_private.json"}
    pilot.write_json(OUT / "pilot_summary_private.json", summary)
    pilot.write_json(OUT / "attempts_summary.json", {"rows": checkpoint["attempt_rows"],
        "cohorts": cohort_meta, "proposal_attempts": sum(x["screening_attempts"] for x in cohort_meta.values())})
    pilot.write_json(OUT / "pilot_artifact_manifest.json", {
        "run_id": checkpoint["run_id"], "continuation_commit": provenance["commit"],
        "continuation_tree": provenance["tree"],
        "files_sha256": {p.name: sha(p) for p in sorted(OUT.iterdir()) if p.is_file()
                         and p.name not in ("pilot_artifact_manifest.json", "evaluator_resume_lock.json")},
        "recommendation_manifest_sha256": sha(RECOMMENDATIONS),
        "new_scm": checkpoint["n_units"], "new_g0": 0,
        "new_observation_rows": 0, "new_intervention_rows": 0,
        "continuation": "evaluator only; no generation or sampled response"})
    print(json.dumps({"status": "EVALUATOR_CONTINUATION_COMPLETE", "units": len(unit_rows),
                      "candidate_rows": len(candidate_rows), "policy_rows": len(policy_rows),
                      "interaction_rows": len(interactions), "summary": str(OUT / "pilot_summary_private.json")}, indent=2))


if __name__ == "__main__":
    main()

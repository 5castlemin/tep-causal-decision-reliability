"""Build a public manifest for aggregate-only supplementary artifacts."""
from __future__ import annotations
import hashlib, json, platform, subprocess, sys
import os
from pathlib import Path

ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[1]
OUT=ROOT/"outputs"

def digest(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""):h.update(block)
    return h.hexdigest()

def git(*args):
    return subprocess.check_output(["git",*args],cwd=REPO,text=True).strip()

def main():
    files=[p for p in ROOT.rglob("*") if p.is_file() and p.name!="supplementary_integrity_manifest.json" and not p.name.startswith(".") and "__pycache__" not in p.parts]
    files=[p for p in files if p.name not in {"s1_unit_metrics.csv","s2_unique_graph_metrics.csv","s2_predictions_local.csv","s1_optimum_diagnostics_local.csv","s2_predictions_local.csv"}]
    source_root=os.environ.get("DAT_RESEARCH_ROOT")
    if not source_root:raise SystemExit("DAT_RESEARCH_ROOT must point to the authorized local source-data directory")
    source_root=Path(source_root)
    input_paths={
        "C_DEVELOPMENT_COHORT":source_root/"research-c/development/development-20261123-seed-2026112301-v1/research_c_cohort.sqlite",
        "C_DEVELOPMENT_PROPOSAL":source_root/"research-c/development/development-20261123-seed-2026112301-v1/research_c_proposal_stage.sqlite",
        "C_HELDOUT_COHORT":source_root/"research-c/heldout/independent-evaluation-20261123-seed-2026112303-v1/research_c_cohort.sqlite",
        "C_HELDOUT_PROPOSAL":source_root/"research-c/heldout/independent-evaluation-20261123-seed-2026112303-v1/research_c_proposal_stage.sqlite",
    }
    observed={k:digest(v) for k,v in input_paths.items()}
    src=json.loads((OUT/"supplementary_summary.json").read_text(encoding="utf-8"))["source_sha256"]
    expected={"C_DEVELOPMENT_COHORT":src["C_DEVELOPMENT"]["cohort_db_sha256"],"C_DEVELOPMENT_PROPOSAL":src["C_DEVELOPMENT"]["proposal_db_sha256"],"C_HELDOUT_COHORT":src["C_HELDOUT"]["cohort_db_sha256"],"C_HELDOUT_PROPOSAL":src["C_HELDOUT"]["proposal_db_sha256"]}
    if observed!=expected:raise SystemExit(f"source hash mismatch: {observed}")
    protected=["research/original_objective/policy_engine.py","research/original_objective/runner.py","requirements.txt","RESEARCH_C_EXPERIMENT_CONTRACT_V1.md","RESEARCH_C_HELDOUT_ANALYSIS_LOCK.md"]
    manifest={
      "status":"SUPPLEMENTARY_ANALYSIS_COMPLETED_WITH_LIMITATIONS",
      "classification":"POST_HOC_SUPPLEMENTARY_DECISION_ROBUSTNESS_AND_METRIC_VALIDATION",
      "analysis_revision":"ed04f4d360591f11db25babfec62b8396e34f11b",
      "audit_revision":git("rev-parse","HEAD"),
      "report_generator_sha256":digest(ROOT/"write_supplementary_reports.py"),
      "audit_script_sha256":digest(ROOT/"audit_supplementary.py"),
      "core_analysis_script_sha256":digest(ROOT/"analyze_supplementary.py"),
      "core_analysis_script_sha256_at_execution_revision":hashlib.sha256(subprocess.check_output(["git","show","ed04f4d360591f11db25babfec62b8396e34f11b:research/final_supplementary_validation/analyze_supplementary.py"],cwd=REPO)).hexdigest(),
      "tests_sha256":digest(REPO/"tests/test_supplementary_validation.py"),
      "git_commit":git("rev-parse","HEAD"),
      "git_tree":git("rev-parse","HEAD^{tree}"),
      "runtime":{"python":sys.version,"platform":platform.platform()},
      "inputs_sha256":observed,
      "protected_file_git_blob_ids":{p:git("rev-parse",f"HEAD:{p}") for p in protected if (REPO/p).exists()},
      "public_artifacts_sha256":{p.relative_to(ROOT).as_posix():digest(p) for p in sorted(files) if p.name!="audit_final.log"},
      "private_local_artifacts_excluded":["outputs/s1_unit_metrics.csv","outputs/s2_unique_graph_metrics.csv","outputs/s2_predictions_local.csv","outputs/s1_optimum_diagnostics_local.csv"],
      "research_d_unit_level":"excluded: local/private artifacts unavailable",
      "sid_aid":"not run: no verified compatible implementation/fixture",
      "new_data_generated":False,
      "note":"Manifest records source and public aggregate artifacts; it does not claim full DGP identity or industrial generalization. Commit/tree values refer to the source revision immediately preceding this result-manifest commit."
    }
    (ROOT/"supplementary_integrity_manifest.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    print("Wrote supplementary_integrity_manifest.json")

if __name__=="__main__":main()

"""Generate locked final recommendations, qualify resources, then invoke evaluator once."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

from research.external_validation.semisynthetic_evaluation import pipeline as d
from research.external_validation.semisynthetic_evaluation import reproducibility as repro
from research.external_validation.semisynthetic_final import final_pipeline as fp


def require_outside(paths: list[Path]) -> None:
    repro.require_external_outputs(fp.ROOT, paths)


def run(cmd: list[str], *, cwd: Path | None = None) -> str:
    result = subprocess.run(cmd, cwd=cwd, check=True, text=True, capture_output=True)
    return result.stdout.strip()


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--source-root", type=Path, required=True)
    p.add_argument("--data-root", type=Path, required=True)
    p.add_argument("--training", type=Path, required=True)
    p.add_argument("--output-root", type=Path, required=True)
    p.add_argument("--reproduction-lock", type=Path, required=True)
    p.add_argument("--development-g0-manifest", type=Path, required=True)
    p.add_argument("--adapter-summary", type=Path, required=True)
    p.add_argument("--prior-records", type=Path, nargs="+", required=True)
    p.add_argument("--final", action="store_true")
    args = p.parse_args(argv)
    if not args.final:
        raise ValueError("only the explicitly approved final mode is supported")
    root = args.output_root.resolve()
    paths = {"root": root, "training": args.training.resolve(),
        "request": root / "recommendation_input.json", "run_lock": root / "final_run_lock.json",
        "recommendations": root / "recommendations.json",
        "execution_manifest": root / "execution_manifest.json",
        "evaluation_manifest": root / "evaluation_manifest.json",
        "response_dir": root / "response_vectors", "state": root / "evaluator_state.json",
        "comparison": root / "independent_analysis.json"}
    require_outside(list(paths.values()))
    if root.exists() and any(root.iterdir()):
        raise FileExistsError("final output location must be new and empty")
    fp.validate_paths(source_root=args.source_root, data_root=args.data_root,
                      training_csv=args.training, output_root=root)
    t0 = time.perf_counter()
    model, source, fit_info = fp.fit_diagnostic(args.source_root, args.data_root)
    preflight = fp.build_seed_collision_audit(source_root=args.source_root,
        data_root=args.data_root, prior_g0_manifest=args.development_g0_manifest,
        reproduction_lock=args.reproduction_lock, adapter_summary=args.adapter_summary,
        prior_records=args.prior_records)
    fp.atomic_json(root / "final_preflight.json", {"schema":"RESEARCH_D_FINAL_PREFLIGHT_V1",
        "status":"PASS_BEFORE_FINAL_RESPONSE_GENERATION", "fit_diagnostic":fit_info,
        "seed_collision_audit":preflight, "training_raw_sha256":fp.file_sha(args.training),
        "training_numeric_sha256":fp.EXPECTED_TRAIN_NUMERIC,
        "intervention_rows_generated":0, "final_evaluation_samples_generated":0})
    runlock = fp.create_request_and_runlock(model=model, source=source, train_path=args.training,
        source_root=args.source_root, data_root=args.data_root, paths=paths, fit_info=fit_info,
        seed_audit=preflight)
    lock_sha = fp.file_sha(paths["run_lock"])
    request_sha = fp.file_sha(paths["request"])
    env = dict(os.environ); env["PYTHONPATH"] = str(fp.ROOT)
    cmd = [sys.executable, "-m", "research.external_validation.semisynthetic_evaluation.recommendation_worker",
        "--input", str(paths["request"]), "--input-sha256", request_sha,
        "--training", str(args.training.resolve()), "--training-sha256", fp.EXPECTED_TRAIN_RAW,
        "--contract-sha256", fp.contract_hash(), "--output", str(paths["recommendations"])]
    rec_output = run(cmd, cwd=fp.ROOT)
    recommendation = json.loads(paths["recommendations"].read_text(encoding="utf-8"))
    if recommendation.get("row_count") != 17000:
        raise ValueError("recommendation worker did not generate exactly 17,000 locked rows")
    edit_audit = fp.enrich_recommendations_with_edit_zones(paths["request"], paths["recommendations"])
    recommendation = json.loads(paths["recommendations"].read_text(encoding="utf-8"))
    exec_manifest = fp.build_execution_manifest(lock_path=paths["run_lock"],
        recommendation_path=paths["recommendations"], paths={**paths,
            "source_root": args.source_root.resolve()})
    # Response-blind resource qualification exercises the exact chunked bootstrap at final dimensions.
    bench_cmd = [sys.executable, "-m", "research.external_validation.semisynthetic_final.final_analyze",
        "--resource-benchmark", "--output", str(root / "resource_benchmark.json"),
        "--seed", str(fp.derive_final_seed("resource-benchmark"))]
    bench_output = run(bench_cmd, cwd=fp.ROOT)
    bench = json.loads((root / "resource_benchmark.json").read_text(encoding="utf-8"))
    if bench.get("status") != "PASS" or bench.get("peak_rss_bytes", 0) >= 4294967296:
        raise RuntimeError("response-blind resource qualification did not pass")
    # Validate all bindings again immediately before the only evaluator invocation.
    lock = fp.verify_lock(lock_path=paths["run_lock"], expected_lock_sha256=lock_sha,
        source_root=args.source_root, data_root=args.data_root, training_path=args.training,
        recommendation_path=paths["recommendations"], execution_manifest_path=paths["execution_manifest"])
    fp.verify_final_artifacts(paths["run_lock"], paths["execution_manifest"], paths["recommendations"])
    evaluator_cmd = [sys.executable, "-m", "research.external_validation.semisynthetic_final.final_evaluate_worker",
        "--source-root", str(args.source_root.resolve()), "--data-root", str(args.data_root.resolve()),
        "--training", str(args.training.resolve()), "--run-lock", str(paths["run_lock"]),
        "--run-lock-sha256", lock_sha, "--recommendations", str(paths["recommendations"]),
        "--execution-manifest", str(paths["execution_manifest"]),
        "--evaluation-manifest", str(paths["evaluation_manifest"]),
        "--response-dir", str(paths["response_dir"]), "--state", str(paths["state"])]
    evaluator_output = run(evaluator_cmd, cwd=fp.ROOT)
    # Independent analysis is a separate process and never samples or refits.
    analysis_cmd = [sys.executable, "-m", "research.external_validation.semisynthetic_final.final_analyze",
        "--run-lock", str(paths["run_lock"]), "--recommendations", str(paths["recommendations"]),
        "--evaluation-manifest", str(paths["evaluation_manifest"]),
        "--response-dir", str(paths["response_dir"]), "--output", str(paths["comparison"])]
    analysis_output = run(analysis_cmd, cwd=fp.ROOT)
    comparison = json.loads(paths["comparison"].read_text(encoding="utf-8"))
    end_hashes = repro.research_code_hashes(fp.ROOT, fp.CODE_FILES)
    if end_hashes != runlock["code_sha256"]:
        raise ValueError("final code bytes changed during or after execution")
    completed = {"schema": "RESEARCH_D_FINAL_RUN_COMPLETION_V1", "run_id": runlock["run_id"],
        "status": "COMPLETED_ANALYZED", "run_lock_sha256": lock_sha,
        "recommendation_sha256": fp.file_sha(paths["recommendations"]),
        "execution_manifest_sha256": fp.file_sha(paths["execution_manifest"]),
        "evaluation_manifest_sha256": fp.file_sha(paths["evaluation_manifest"]),
        "independent_analysis_sha256": fp.file_sha(paths["comparison"]),
        "resource_benchmark_sha256": fp.file_sha(root / "resource_benchmark.json"),
        "recommendation_stdout": rec_output, "evaluator_stdout": evaluator_output,
        "analysis_stdout": analysis_output, "wall_seconds_before_supervisor": time.perf_counter()-t0,
        "edit_zone_policy_replay": edit_audit,
        "recommendation_rows": recommendation["row_count"],
        "intervention_rows": json.loads(paths["evaluation_manifest"].read_text())["total_rows"],
        "final_training_rows_generated": 0,
        "final_gate": "EXTERNAL_FINAL_EVALUATION_VERIFIED" if comparison.get("integrity_status")=="PASS" else "EXTERNAL_FINAL_EVALUATION_INCOMPLETE"}
    fp.atomic_json(root / "completion.json", completed)
    print(json.dumps({"status":completed["final_gate"], "recommendations":completed["recommendation_rows"],
        "intervention_rows":completed["intervention_rows"], "run_lock_sha256":lock_sha,
        "analysis_sha256":completed["independent_analysis_sha256"]}, sort_keys=True))


if __name__ == "__main__":
    main()

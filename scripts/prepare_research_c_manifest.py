"""Bind an already approved Research C config to the current source/runtime.

This tool does not approve a contract or preregister an experiment. It only
prepares the manifest after a separately user-approved configuration exists.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.original_objective import runner


def prepare_manifest(config_path: Path, output_path: Path) -> dict:
    config_path = Path(config_path).expanduser().resolve()
    output_path = Path(output_path).expanduser().resolve()
    if output_path == ROOT or ROOT in output_path.parents:
        raise ValueError("manifest output must be outside the source checkout")
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"approved configuration is unreadable: {exc}") from exc
    runner._validate_approved_config_schema(config)
    if (config.get("contract_status") != "USER_APPROVED"
            or config.get("research_cohort_execution_enabled") is not True
            or config.get("preregistration_status") != "PREREGISTERED"):
        raise ValueError("manifest preparation requires an already approved/preregistered config")
    runner._validate_supported_research_contract(config)
    if config.get("runtime_fingerprint") != runner._runtime_fingerprint():
        raise ValueError("configuration runtime fingerprint differs from this environment")
    if not runner._git_clean_except_build_artifacts(ROOT):
        raise ValueError("source tree must be committed and clean before manifest preparation")
    if output_path.exists():
        raise FileExistsError(f"refusing to overwrite manifest: {output_path}")

    contract_keys = ("configuration_version", "contract_status", "preregistration_status",
                     "population", "scm", "task", "g0", "repair", "evaluation")
    manifest = {
        # Copy only; this tool cannot grant or change contract approval.
        "approval_status": config["contract_status"],
        "manifest_version": "research-c-execution-manifest-v1",
        "config_sha256": runner._digest(config),
        "cohort_type": config["cohort_type"],
        "runtime_fingerprint": runner._runtime_fingerprint(),
        "excluded_untracked_paths": [".build_reframed/"],
        "source_revision": runner._git_revision(ROOT),
        "code_sha256": runner._code_hashes(ROOT),
        "configuration_version": config["configuration_version"],
        "contract_sha256": runner._digest({key: config[key] for key in contract_keys}),
        "resource_limits_sha256": runner._digest(config["resource_limits"]),
        "run_id": config["run_id"],
        "output_root": str(Path(config["output_root"]).expanduser().resolve()),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(manifest, ensure_ascii=False, sort_keys=True,
                         indent=2, allow_nan=False).encode("utf-8") + b"\n"
    temp_path = output_path.with_name(f".{output_path.name}.{os.getpid()}.tmp")
    try:
        with temp_path.open("xb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temp_path, output_path)
    finally:
        if temp_path.exists():
            temp_path.unlink()
    return {"manifest_path": str(output_path),
            "manifest_sha256": runner._digest(manifest),
            "approval_status_copied_from_config": config["contract_status"],
            "source_revision": manifest["source_revision"],
            "research_execution_started": False}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--approved-config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = prepare_manifest(args.approved_config, args.output)
    except (ValueError, FileExistsError, runner.ResearchModeBlocked) as exc:
        parser.exit(2, f"MANIFEST_PREPARATION_BLOCKED: {exc}\n")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Fail-closed entry point for a future frozen Step 5/6 cohort run.

This module is deliberately not invoked by Step 4C-2 validation. It refuses to
start proposal generation unless the runtime, content manifest and exact Git
commit supplied by the operator all match the frozen contract.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .step4c1_cohort import (COHORT_SETTINGS_SHA256, CohortRegistry, run_cohort,
                             sha256 as canonical_sha256)
from .step4c2_freeze import ROOT, assert_production_ready


def run_configured_cohort(*, cohort: str, master_seed: int, output_root: Path,
                          expected_commit: str, expected_tree: str) -> dict:
    settings, manifest, settings_sha, manifest_sha = assert_production_ready(
        expected_commit=expected_commit, expected_tree=expected_tree)
    if cohort not in settings["cohorts"]:
        raise ValueError("cohort must be development or confirmation")
    root = Path(output_root).expanduser().resolve()
    repo = ROOT.resolve()
    if root == repo or root.is_relative_to(repo) or repo.is_relative_to(root):
        raise ValueError("output_root must be a dedicated directory outside the repository")
    resource = settings["resources"]
    target = settings["cohorts"][cohort]
    registry = CohortRegistry(root / "registry.sqlite")
    bound_settings = canonical_sha256({"cohort_settings_sha256": COHORT_SETTINGS_SHA256,
        "operational_settings_sha256": settings_sha,
        "freeze_manifest_sha256": manifest_sha,
        "git_commit": expected_commit,
        "git_tree": expected_tree})
    return run_cohort(cohort=cohort, master_seed=master_seed, registry=registry,
        ledger_dir=root / "ledgers", config_sha256=bound_settings,
        target_eligible=target["eligible_admission_target"],
        proposal_cap=target["proposal_cap"],
        resource_cap_seconds=resource["cohort_active_stage_time_cap_seconds"],
        cohort_storage_root=root,
        max_cohort_storage_bytes=resource["cohort_total_storage_bytes_cap"],
        failure_reserve_bytes=resource["failure_record_reserve_bytes"],
        minimum_free_disk_bytes=resource["minimum_free_disk_bytes"],
        isolate_stages=resource["isolate_stages"],
        max_unit_seconds=resource["unit_timeout_seconds"],
        max_scm_active_seconds=resource["scm_active_stage_time_cap_seconds"],
        max_rss_bytes=resource["rss_sampled_kill_bytes"],
        max_ledger_bytes=resource["individual_ledger_bytes_cap"])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cohort", required=True, choices=("development", "confirmation"))
    parser.add_argument("--master-seed", required=True, type=int)
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--expected-commit", required=True)
    parser.add_argument("--expected-tree", required=True)
    args = parser.parse_args(argv)
    result = run_configured_cohort(cohort=args.cohort, master_seed=args.master_seed,
        output_root=args.output_root, expected_commit=args.expected_commit,
        expected_tree=args.expected_tree)
    # Do not print per-SCM policy outcomes; the run ledger is the controlled record.
    print(json.dumps({"cohort": result["cohort"], "counts": result["counts"],
        "shortfall_eligible": result["shortfall_eligible"],
        "cap_reached": result["cap_reached"],
        "resource_cap_reached": result["resource_cap_reached"],
        "storage_cap_reached": result["storage_cap_reached"],
        "cohort_storage_bytes": result["cohort_storage_bytes"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())

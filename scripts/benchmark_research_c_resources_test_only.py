"""Measure Research C resource use on a fixed, explicitly TEST_ONLY matrix.

This is an operations benchmark, not a study cohort. It never calls the
approved Research Mode entry point and marks every proposal/SCM study_sample
false. The topology/size matrix and repeat count are fixed before outcomes.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import os
from pathlib import Path
import shutil
import sqlite3
import sys
import time

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.budget_aware_refinement.step4_topology_generator import TEMPLATES
from research.budget_aware_refinement.step4c1_scm import (
    generate_observations, generate_scm_parameters,
)
from research.original_objective import policy_engine as pe
from research.original_objective.cohort_runner import (
    run_proposal_stage,
)
from research.original_objective.execution_limits import (
    ResourceLimits, directory_usage_bytes,
)
from research.original_objective.g0_candidate import corrupt_graph_candidate
from research.original_objective.proposal_pipeline import (
    build_research_c_proposal, run_cohort_orchestration,
)
from research.original_objective.runner import (
    _code_hashes, _digest, _git_revision, _runtime_fingerprint,
)
from research.original_objective.cohort_ledger_test_only import _subseed
from research.original_objective.e2e_fixture import FixtureInput


REPEATS = 3
BASE_SEED = 9_721_100
NODE_COUNTS = (6, 10)
CASES = tuple((template, n, repeat)
              for repeat in range(REPEATS)
              for template in TEMPLATES
              for n in NODE_COUNTS)

# Reuse the already-tested TEST_ONLY envelope. The output has a separate 1 GiB
# free-space floor for this run; these values are not Research resource limits.
TEST_LIMITS = ResourceLimits(
    unit_timeout_seconds=60,
    scm_active_seconds=120,
    cohort_active_seconds=2400,
    sampled_rss_bytes=512 * 1024 * 1024,
    max_result_bytes=10_000_000,
    max_ledger_bytes=20_000_000,
    max_cohort_storage_bytes=30_000_000,
    minimum_free_disk_bytes=1024 * 1024 * 1024,
    failure_reserve_bytes=4096,
    max_concurrent_scms=1,
    classification="TEST_ONLY_RESOURCE_ENVELOPE",
)


def _proposal_builder(*, cohort: str, master_seed: int,
                      proposal_id: str, attempt: int) -> dict:
    template, node_count, repeat = CASES[attempt]
    proposal = build_research_c_proposal(
        cohort=cohort, master_seed=master_seed, proposal_id=proposal_id,
        attempt=attempt, template=template, node_count=node_count)
    proposal["benchmark_assignment"] = {
        "classification": "TEST_ONLY_RESOURCE_BENCHMARK",
        "template": template, "node_count": node_count,
        "repeat": repeat, "study_sample": False,
    }
    return proposal


@dataclass(frozen=True)
class _TimedFixtureFactory:
    proposal: dict
    test_master_seed: int
    outer_scm_id: str
    generation_timing_path: Path

    def __call__(self):
        proposal = self.proposal
        started = time.perf_counter()
        scm_started = time.perf_counter()
        scm = generate_scm_parameters(proposal)
        scm_seconds = time.perf_counter() - scm_started
        obs_started = time.perf_counter()
        observations = generate_observations(proposal, scm)
        observations_seconds = time.perf_counter() - obs_started
        truth = pe.state(proposal["topology_edges"])
        g0_seed = _subseed(self.test_master_seed, "TEST_ONLY",
                           self.outer_scm_id, "g0")
        g0_started = time.perf_counter()
        corruption = corrupt_graph_candidate(
            truth, nodes=proposal["nodes"], action=proposal["action"],
            target=proposal["target"], master_seed=g0_seed,
            task_id=f"TEST_ONLY:{proposal['proposal_id']}")
        initial = pe.state(corruption["initial_graph"]["edges"],
                           unresolved=corruption["initial_graph"]["unresolved"])
        g0_seconds = time.perf_counter() - g0_started
        counts = pe.metrics(truth, initial, proposal["action"],
                            proposal["target"], pe.Config())["counts"]
        initial_error_count = sum(sum(row.values()) for row in counts.values())
        fixture = FixtureInput(
            truth_spec=scm["truth_spec"], initial_graph=initial,
            observations=np.asarray(observations["rows"], dtype=np.float64),
            action=proposal["action"],
            target=proposal["target"], delta=1, test_only=True)
        metadata = {
            "classification": "TEST_ONLY_RESOURCE_BENCHMARK",
            "study_sample": False,
            "proposal_id": proposal["proposal_id"],
            "scm_id": self.outer_scm_id,
            "template": proposal["template"],
            "node_count": proposal["node_count"],
            "action": proposal["action"], "target": proposal["target"],
            "g0_seed": g0_seed,
            "g0_error_counts": counts,
            "g0_initial_error_count": initial_error_count,
        }
        generation_timings = {
                "scm_parameters": scm_seconds,
                "observations": observations_seconds,
                "g0": g0_seconds,
                "total": time.perf_counter() - started,
        }
        self.generation_timing_path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = self.generation_timing_path.with_name(
            self.generation_timing_path.name + f".{os.getpid()}.tmp")
        temp_path.write_text(json.dumps(generation_timings, sort_keys=True), encoding="utf-8")
        os.replace(temp_path, self.generation_timing_path)
        return fixture, metadata


def _quantiles(values):
    values = sorted(float(x) for x in values if x is not None)
    if not values:
        return {"n": 0, "min": None, "median": None, "p95_nearest_rank": None, "max": None}
    rank = max(1, int((0.95 * len(values) + 0.999999999)))
    mid = len(values) // 2
    median = values[mid] if len(values) % 2 else (values[mid - 1] + values[mid]) / 2
    return {"n": len(values), "min": values[0], "median": median,
            "p95_nearest_rank": values[rank - 1], "max": values[-1]}


def _sqlite_result_sizes(path: Path):
    if not path.exists():
        return {}
    with sqlite3.connect(path) as db:
        return {str(scm_id): int(size) for scm_id, size in db.execute(
            "SELECT scm_id,length(result_json) FROM scms "
            "WHERE result_json IS NOT NULL ORDER BY ordinal")}


def run_benchmark(output_root: Path, raw_output: Path):
    output_root = output_root.resolve()
    raw_output = raw_output.resolve()
    if output_root.exists() and any(output_root.iterdir()):
        raise FileExistsError(f"refusing to reuse nonempty output root: {output_root}")
    output_root.mkdir(parents=True, exist_ok=True)
    free_before = shutil.disk_usage(output_root).free
    if free_before < TEST_LIMITS.minimum_free_disk_bytes:
        raise RuntimeError("TEST_ONLY benchmark requires at least 1 GiB free disk")

    runs = []
    for repeat in range(REPEATS):
        # Reuse precisely the same proposals, SCMs, observations and G0 on
        # every repetition; only execution timing/environment noise can vary.
        seed = BASE_SEED
        rep_root = output_root / f"repeat-{repeat + 1:02d}"
        rep_root.mkdir(parents=True, exist_ok=False)
        proposal_started = time.perf_counter()
        proposal_stage = run_proposal_stage(
            rep_root, run_id=f"test-only-resource-bench-r{repeat + 1:02d}",
            cohort_type="TEST_ONLY", master_seed=seed,
            target_admissions=len(CASES), proposal_cap=len(CASES),
            resource_limits=TEST_LIMITS, proposal_builder=_proposal_builder)
        proposal_wall = time.perf_counter() - proposal_started
        proposals = proposal_stage["proposals"]
        accepted = [p for p in proposals if p.get("accepted")]
        factories = {}
        for p in accepted:
            outer_id = f"test-only-scm-{p['proposal_id']}"
            factories[outer_id] = {
                "factory": _TimedFixtureFactory(
                    p, seed, outer_id,
                    rep_root / "generation-measurements" / f"{p['proposal_id']}.json"),
                "apply_g0_generator": False,
            }
        outcomes = []
        for p in proposals:
            outcomes.append({k: v for k, v in p.items() if k != "error_recipes"} | {
                "status": "ADMITTED" if p.get("accepted") else "STRUCTURALLY_INELIGIBLE",
                "study_sample": False,
            })
        cohort_started = time.perf_counter()
        cohort = run_cohort_orchestration(
            rep_root, mode="TEST_ONLY",
            run_id="test-only-resource-cohort-fixed-matrix",
            master_seed=seed, fixtures=factories, proposal_outcomes=outcomes,
            budgets=(0, 1, 2, 3, 4), resource_limits=TEST_LIMITS)
        cohort_wall = time.perf_counter() - cohort_started
        proposal_db = rep_root / "research_c_fixture_proposals.sqlite"
        cohort_db = rep_root / "research_c_fixture_cohort.sqlite"
        scm_records = []
        for row in cohort["scms"]:
            payload = row.get("result") or {}
            metadata = payload.get("fixture_metadata", {})
            budgets = payload.get("e2e_result", {}).get("budgets", [])
            candidate_counts = {}
            for b in budgets:
                full = next((p for p in b.get("policies", [])
                             if p.get("policy_id") == "M1+M2+M3+M4"), None)
                if full:
                    candidate_counts = full.get("repair_candidate_counts_by_metric", {})
                    break
            stage_timings = row.get("stage_timings") or {}
            budget_timings = stage_timings.get("budgets", [])
            for timing_key in ("structural_policy_execution_seconds",
                               "fit_recommendation_seconds", "gt_evaluation_seconds"):
                stage_timings[timing_key] = sum(
                    float(item.get(timing_key, 0.0)) for item in budget_timings)
            scm_records.append({
                "scm_id": row["scm_id"], "status": row["status"],
                "proposal_id": metadata.get("proposal_id"),
                "template": metadata.get("template"), "node_count": metadata.get("node_count"),
                "g0_initial_error_count": metadata.get("g0_initial_error_count"),
                "g0_error_counts": metadata.get("g0_error_counts"),
                "candidate_counts_by_metric": candidate_counts,
                "stage_generation_seconds": json.loads(
                    (rep_root / "generation-measurements" /
                     f"{metadata.get('proposal_id')}.json").read_text(encoding="utf-8")),
                "stage_timings": stage_timings,
                "scm_active_seconds": row.get("active_seconds"),
                "sampled_rss_peak_bytes": row.get("sampled_rss_peak_bytes"),
                "result_json_bytes": None,
                "complete_policy_evaluations": sum(len(b.get("policies", [])) for b in budgets),
                "result_sha256": row.get("result_sha256"),
            })
        result_sizes = _sqlite_result_sizes(cohort_db)
        for record in scm_records:
            record["result_json_bytes"] = result_sizes.get(record["scm_id"])
        runs.append({
            "repeat": repeat + 1, "test_only_master_seed": seed,
            "proposal_stage_status": proposal_stage["proposal_stage_status"],
            "proposal_count": proposal_stage["proposal_count"],
            "eligible_count": proposal_stage["eligible_count"],
            "proposal_shortfall": proposal_stage["shortfall"],
            "proposal_wall_seconds": proposal_wall,
            "proposal_worker_seconds": sum(x["active_seconds"] for x in proposal_stage["proposal_checkpoints"]),
            "proposal_samples": [{
                "proposal_id": x["proposal_id"], "status": x["status"],
                "template": (x.get("proposal") or {}).get("template"),
                "node_count": (x.get("proposal") or {}).get("node_count"),
                "worker_seconds": x["active_seconds"],
                "sampled_rss_peak_bytes": x["sampled_rss_peak_bytes"],
                "failure_code": x["failure_code"],
            } for x in proposal_stage["proposal_checkpoints"]],
            "cohort_wall_seconds": cohort_wall,
            "cohort_active_seconds": cohort["cumulative_active_seconds"],
            "cohort_stop_reason": cohort["cohort_stop_reason"],
            "completed_scm_count": cohort["completed_scm_count"],
            "complete_policy_evaluations": cohort["complete_policy_evaluations"],
            "cohort_storage_bytes": cohort["resource_metrics"]["cohort_storage_bytes"],
            "cohort_ledger_bytes": cohort["resource_metrics"]["ledger_bytes"],
            "proposal_ledger_bytes": proposal_db.stat().st_size if proposal_db.exists() else 0,
            "cohort_result_sizes_bytes": sorted(result_sizes.values()),
            "output_root_bytes": directory_usage_bytes(rep_root),
            "scms": scm_records,
            "run_ids": {"proposal": proposal_stage["run_id"], "cohort": cohort["run_id"]},
        })

    all_proposals = [p for r in runs for p in r["proposal_samples"]]
    all_scms = [s for r in runs for s in r["scms"]]
    completed = [s for s in all_scms if s["status"] == "COMPLETED"]
    all_evals = [s["complete_policy_evaluations"] for s in completed]
    zero_error = [s for s in completed if s["g0_initial_error_count"] == 0]
    unique_by_id = {s["scm_id"]: s for s in completed}
    unique_zero_error = [s for s in unique_by_id.values()
                         if s["g0_initial_error_count"] == 0]
    flat_stage = {}
    for key in ("scm_parameters", "observations", "g0", "total"):
        flat_stage[key] = _quantiles(
            s["stage_generation_seconds"][key] for s in completed
            if s.get("stage_generation_seconds"))
    policy_stage = {}
    for key in ("structural_policy_execution_seconds", "fit_recommendation_seconds",
                "gt_evaluation_seconds", "result_validation_and_serialization_seconds",
                "atomic_result_commit_seconds"):
        policy_stage[key] = _quantiles(
            (s.get("stage_timings") or {}).get(key) for s in completed)
    raw = {
        "classification": "TEST_ONLY_RESOURCE_BENCHMARK_NOT_RESEARCH_COHORT",
        "study_sample_count": 0, "research_cohort_generated": False,
        "research_regret_result": False,
        "source_revision": _git_revision(ROOT), "code_sha256": _code_hashes(ROOT),
        "runtime_fingerprint": _runtime_fingerprint(),
        "benchmark_design": {
            "repeats": REPEATS, "base_seed": BASE_SEED,
            "rng_use": "same dedicated TEST_ONLY seed and IDs on every repeat; ledgers/output roots are separate TEST_ONLY stores",
            "templates": list(TEMPLATES), "node_counts": list(NODE_COUNTS),
            "budgets": [0, 1, 2, 3, 4], "policy_evaluations_per_completed_scm": 85,
            "matrix": [
                {"template": t, "node_count": n, "repeats": REPEATS}
                for t in TEMPLATES for n in NODE_COUNTS],
            "seed_schedule": [BASE_SEED for _ in range(REPEATS)],
            "selection": "all fixed assigned proposals retained; no selection by G0 error or policy result",
            "repeat_purpose": "measure same-input timing variation and verify result checksum stability",
            "resource_limits": TEST_LIMITS.binding(),
        },
        "system_snapshot": {
            "disk_free_bytes_before": free_before,
            "disk_free_bytes_after": shutil.disk_usage(output_root).free,
            "output_root": str(output_root),
        },
        "summary": {
            "proposal_count": len(all_proposals),
            "proposal_eligible_count": sum(p["status"] == "ELIGIBLE" for p in all_proposals),
            "proposal_ineligible_count": sum(p["status"] == "STRUCTURALLY_INELIGIBLE" for p in all_proposals),
            "proposal_resource_failure_count": sum(p["status"] not in {"ELIGIBLE", "STRUCTURALLY_INELIGIBLE"} for p in all_proposals),
            "completed_scm_count": len(completed),
            "failed_or_missing_scm_count": len(all_scms) - len(completed),
            "complete_policy_evaluations": sum(all_evals),
            "expected_policy_evaluations_per_completed_scm": 85,
            "zero_error_g0_count": len(zero_error),
            "zero_error_g0_rate": len(zero_error) / len(completed) if completed else None,
            "unique_zero_error_g0_count": len(unique_zero_error),
            "unique_zero_error_g0_rate": (len(unique_zero_error) / len(unique_by_id)
                                           if unique_by_id else None),
            "g0_candidate_count_range_by_metric": {
                metric: {"min": min((s.get("candidate_counts_by_metric", {}).get(metric, 0) for s in completed), default=None),
                         "max": max((s.get("candidate_counts_by_metric", {}).get(metric, 0) for s in completed), default=None)}
                for metric in pe.METRICS},
            "proposal_worker_seconds": _quantiles(p["worker_seconds"] for p in all_proposals),
            "proposal_sampled_rss_peak_bytes": _quantiles(p["sampled_rss_peak_bytes"] for p in all_proposals),
            "stage_generation_seconds": flat_stage,
            "policy_and_persistence_stage_seconds": policy_stage,
            "scm_active_seconds": _quantiles(s["scm_active_seconds"] for s in completed),
            "scm_sampled_rss_peak_bytes": _quantiles(s["sampled_rss_peak_bytes"] for s in completed),
        "result_json_bytes": _quantiles(s["result_json_bytes"] for s in completed),
            "cohort_ledger_bytes": _quantiles(r["cohort_ledger_bytes"] for r in runs),
            "proposal_ledger_bytes": _quantiles(r["proposal_ledger_bytes"] for r in runs),
            "output_root_bytes_per_repeat": _quantiles(r["output_root_bytes"] for r in runs),
            "proposal_wall_seconds_per_repeat": _quantiles(r["proposal_wall_seconds"] for r in runs),
            "cohort_wall_seconds_per_repeat": _quantiles(r["cohort_wall_seconds"] for r in runs),
            "cohort_active_seconds_per_repeat": _quantiles(r["cohort_active_seconds"] for r in runs),
            "identical_input_result_hashes_across_repeats": (
                len({tuple((s["scm_id"], s["result_sha256"]) for s in r["scms"])
                     for r in runs}) == 1),
            "unique_completed_scm_inputs": len({s["scm_id"] for s in completed}),
        },
        "runs": runs,
    }
    raw_output.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(raw, ensure_ascii=False, sort_keys=True, indent=2,
                         allow_nan=False).encode("utf-8") + b"\n"
    temp = raw_output.with_name(raw_output.name + f".{os.getpid()}.tmp")
    temp.write_bytes(encoded)
    os.replace(temp, raw_output)
    return raw


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, required=True,
                        help="new TEST_ONLY directory outside the source checkout")
    parser.add_argument("--raw-output", type=Path, required=True,
                        help="new JSON record path; must not overwrite existing files")
    args = parser.parse_args(argv)
    if (args.output_root.resolve() == ROOT or ROOT in args.output_root.resolve().parents):
        parser.error("benchmark output must be outside the source checkout")
    if args.raw_output.exists():
        parser.error(f"refusing to overwrite raw benchmark record: {args.raw_output}")
    result = run_benchmark(args.output_root, args.raw_output)
    print(json.dumps({"classification": result["classification"],
                      "summary": result["summary"],
                      "raw_output": str(args.raw_output.resolve())},
                     sort_keys=True, allow_nan=False))
    return 0 if (result["summary"]["proposal_resource_failure_count"] == 0
                 and result["summary"]["failed_or_missing_scm_count"] == 0
                 and result["summary"]["identical_input_result_hashes_across_repeats"]) else 2


if __name__ == "__main__":
    raise SystemExit(main())

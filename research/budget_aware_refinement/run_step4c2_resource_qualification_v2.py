"""Production-isolated fixed-fixture resource qualification.

This runner uses strict-Q fixtures and the same process isolation, unit timeout,
RSS monitor, JSONL ledger and analytic evaluator configured for production. It
does not create a study SCM cohort or compute/store decision-regret outcomes.
"""
from __future__ import annotations

import hashlib
import gzip
import json
import os
from pathlib import Path
import statistics
import tempfile
import time

import numpy as np

from .step4c1_pipeline import execution_binding, run_eligible_proposal
from .step4c1_proposal import STRATA
from .step4c1_scm import _topological_order
from .step4b4_mock_runner import _run_isolated, recover_jsonl
from .step4b2_population import competition_recipes
from .step4c1_cohort import (CohortRegistry, CohortStorageMonitor,
    COHORT_SETTINGS_SHA256, sha256 as cohort_sha256)
from .step4c2_freeze import current_runtime

MASTER_SEED = 20261116
REPETITIONS = 1
UNIT_TIMEOUT_SECONDS = 2.0
RSS_MONITOR_BYTES = 512 * 1024 * 1024
WALL_CAP_SECONDS = 1800.0
LEDGER_CAP_BYTES = 100 * 1024 * 1024
COHORT_STORAGE_CAP_BYTES = 100 * 1024 * 1024
FAILURE_RESERVE_BYTES = 5 * 1024 * 1024
MINIMUM_FREE_DISK_BYTES = 1024 * 1024 * 1024


def _rss_bytes() -> int | None:
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes

        class Counters(ctypes.Structure):
            _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
                        ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                        ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t)]
        counters = Counters(); counters.cb = ctypes.sizeof(counters)
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        psapi = ctypes.WinDLL("psapi", use_last_error=True)
        kernel.GetCurrentProcess.restype = wintypes.HANDLE
        psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD]
        psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
        if psapi.GetProcessMemoryInfo(kernel.GetCurrentProcess(), ctypes.byref(counters), counters.cb):
            return int(counters.WorkingSetSize)
        return None
    try:
        import resource
        value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        return int(value if os.name == "darwin" else value * 1024)
    except (ImportError, AttributeError):
        return None


def _preserved_topologies() -> tuple[dict[tuple[str, int], dict], str]:
    """Reuse the preserved topology-only yield rows; do not draw new proposals."""
    source = Path(__file__).with_name("step4c1_indirect_only_yield_v2.json.gz")
    raw = source.read_bytes()
    artifact = json.loads(gzip.decompress(raw))
    selected = {}
    for row in artifact["rows"]:
        key = (row["template"], row["node_count"])
        if row["accepted_q_common_strict_indirect"] and key not in selected:
            selected[key] = row
    return selected, hashlib.sha256(raw).hexdigest()


def _proposal_from_preserved_row(row: dict) -> dict:
    nodes = [f"V{i:02d}" for i in range(row["node_count"])]
    edges = [tuple(edge) for edge in row["truth_edges"]]
    recipes, counts = {}, {}
    for kind in ("FN", "FP", "REV"):
        candidates = competition_recipes(nodes, edges, row["action"], row["target"], kind)
        if not candidates:
            raise RuntimeError("preserved Q-common row lost its structural recipe support")
        chosen = candidates[0]
        recipes[kind] = {"initial_edges": [list(e) for e in sorted(chosen["initial_edges"])],
                         "errors": [list(e) for e in chosen["errors"]],
                         "recipe_count": len(candidates)}
        counts[kind] = len(candidates)
    proposal_id = f"resource-v2-{row['template']}-n{row['node_count']}"
    return {"proposal_id": proposal_id, "cohort": "development", "master_seed": MASTER_SEED,
        "attempt": 0, "nodes": nodes, "template": row["template"],
        "node_count": row["node_count"], "topology_hash": row["topology_hash"],
        "topology_edges": [list(e) for e in sorted(edges)], "role_map": row["role_map"],
        "accepted": True, "reason": None, "scm_id": f"dev-scm-{proposal_id}-a0000",
        "action": row["action"], "target": row["target"], "q_recipe_counts": counts,
        "error_recipes": recipes, "outcomes_used": False,
        "coefficient_or_data_drawn": False,
        "fixture_source": "preserved step4c1_indirect_only_yield_v2 topology-only row"}


def _payload(proposal: dict) -> dict:
    nodes = proposal["nodes"]
    edges = proposal["topology_edges"]
    truth = {"nodes": nodes, "topological_order": list(_topological_order(nodes, edges)),
        "edges": edges, "coefficients": {f"{a}->{b}": .5 for a, b in edges},
        "noise": {"family": "explicit fixed resource fixture",
                  "means": {node: 0.0 for node in nodes}, "sd": {node: 1.0 for node in nodes}}}
    rng = np.random.default_rng(700000 + len(nodes) * 31 + sum(map(ord, proposal["template"])))
    noise = rng.normal(size=(512, len(nodes)))
    return {"truth_spec": truth, "exogenous_noise": noise}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _noop_stage() -> dict:
    return {"fixture": "spawn-startup-baseline"}


def qualify() -> dict:
    root_path = Path(__file__).resolve().parent
    rows = []
    fixed_rows, topology_source_sha256 = _preserved_topologies()
    process_rss_before = _rss_bytes()
    spawn_samples = []
    for _ in range(6):
        _, status, elapsed, _ = _run_isolated(_noop_stage, UNIT_TIMEOUT_SECONDS, RSS_MONITOR_BYTES)
        if status:
            raise RuntimeError(f"isolated no-op startup baseline failed: {status}")
        spawn_samples.append(elapsed)
    with tempfile.TemporaryDirectory(prefix="step4c2-isolated-v2-cohort-") as temp:
        cohort_root = Path(temp).resolve()
        monitor = CohortStorageMonitor(cohort_root, max_bytes=COHORT_STORAGE_CAP_BYTES,
            failure_reserve_bytes=FAILURE_RESERVE_BYTES,
            minimum_free_bytes=MINIMUM_FREE_DISK_BYTES)
        registry = CohortRegistry(cohort_root / "registry.sqlite")
        registry.set_storage_monitor(monitor)
        selected = [(key, row) for key, row in fixed_rows.items()]
        registry.bind_cohort("development", MASTER_SEED, len(selected), len(STRATA), COHORT_SETTINGS_SHA256)
        for template, node_count in STRATA:
            topology_row = fixed_rows.get((template, node_count))
            if topology_row is None:
                rows.append({"template": template, "node_count": node_count,
                    "strict_q_common_fixture_found": False, "runs": [],
                    "failure_reason": "no accepted row for this stratum in preserved fixed-yield diagnostic"})
                continue
            proposal = _proposal_from_preserved_row(topology_row)
            payload = _payload(proposal)
            ledger = cohort_root / "ledgers" / f"{proposal['scm_id']}.jsonl"
            ledger.parent.mkdir(parents=True, exist_ok=True)
            admitted = registry.admit(proposal, COHORT_SETTINGS_SHA256, ledger)
            delta = admitted["delta"]
            config, config_sha, input_sha = execution_binding(proposal, delta, payload)
            registry.bind_execution("development", proposal["proposal_id"], proposal["attempt"],
                config_sha, input_sha, initial_input_sha256=cohort_sha256({"proposal": proposal}))
            registry.transition("development", proposal["proposal_id"], proposal["attempt"], "running")
            started = time.perf_counter()
            result = run_eligible_proposal(proposal, ledger, delta=delta,
                isolate_stages=True, max_wall_seconds=WALL_CAP_SECONDS,
                max_unit_seconds=UNIT_TIMEOUT_SECONDS, max_rss_bytes=RSS_MONITOR_BYTES,
                max_ledger_bytes=LEDGER_CAP_BYTES, pre_write_guard=monitor.before_ledger_event,
                _fixture_payload=payload)
            elapsed = time.perf_counter() - started
            events = recover_jsonl(ledger)
            stage_events = [e for e in events if str(e.get("event", "")).startswith("stage:")]
            failed = [e for e in stage_events if e.get("status") != "OK"]
            terminal = [e for e in events if e.get("event") == "terminal"]
            if result.get("status") != "OK" or len(terminal) != 1 or terminal[0].get("status") != "OK":
                failure_reason = ({"stage": failed[-1].get("event"), "status": failed[-1].get("status"),
                    "reason": failed[-1].get("reason")} if failed else
                    {"status": terminal[-1].get("status")} if terminal else None)
                registry.transition("development", proposal["proposal_id"], proposal["attempt"],
                    "failed", str(failure_reason))
                raise RuntimeError(f"production-isolated fixture failed {template}/{node_count}: {failure_reason}; elapsed={elapsed:.3f}s")
            registry.reconcile("development")
            stage_seconds = {e["event"].split(":", 1)[1]: e.get("elapsed_seconds") for e in stage_events}
            stage_rss = {e["event"].split(":", 1)[1]: e.get("observed_rss_bytes") for e in stage_events}
            completed_ledger_hash = _sha(ledger)
            replay_started = time.perf_counter()
            replay = run_eligible_proposal(proposal, ledger, delta=delta,
                isolate_stages=True, max_wall_seconds=WALL_CAP_SECONDS,
                max_unit_seconds=UNIT_TIMEOUT_SECONDS, max_rss_bytes=RSS_MONITOR_BYTES,
                max_ledger_bytes=LEDGER_CAP_BYTES, pre_write_guard=monitor.before_ledger_event,
                _fixture_payload=payload)
            replay_seconds = time.perf_counter() - replay_started
            if replay.get("status") != "OK" or replay.get("resumed") is not True:
                raise RuntimeError("production-mode completed-ledger replay failed")
            if _sha(ledger) != completed_ledger_hash:
                raise RuntimeError("completed production-mode replay changed ledger bytes")
            rows.append({"template": template, "node_count": node_count,
                "proposal_id": proposal["proposal_id"], "scm_id": proposal["scm_id"],
                "topology_sha256": proposal["topology_hash"], "strict_q_common": True,
                "registry_delta": delta, "registry_status": next(x["status"] for x in registry.rows("development") if x["proposal_id"] == proposal["proposal_id"]),
                "equation_signature_bound": bool(next(x["equation_signature_sha256"] for x in registry.rows("development") if x["proposal_id"] == proposal["proposal_id"])),
                "runs": [{"repeat": 0, "delta": delta, "status": "OK",
                    "elapsed_seconds": elapsed, "stage_wall_seconds_including_spawn": stage_seconds,
                    "stage_sampled_child_rss_bytes": stage_rss,
                    "ledger_bytes": ledger.stat().st_size, "ledger_sha256": _sha(ledger),
                    "resume_seconds": replay_seconds, "resume_replayed": True,
                    "max_unit_seconds": UNIT_TIMEOUT_SECONDS, "isolate_stages": True}],
                "median_total_seconds": elapsed, "max_total_seconds": elapsed,
                "max_ledger_bytes": ledger.stat().st_size, "cohort_storage_bytes_after": monitor.usage_bytes()})
        counts = registry.counts("development")
        if counts["registry_accepted"] != len(selected) or counts["composite_available"] != len(selected):
            raise RuntimeError(f"registry/ledger completed denominator mismatch: {counts}")
        cohort_storage_bytes = monitor.usage_bytes()
        if cohort_storage_bytes > COHORT_STORAGE_CAP_BYTES - FAILURE_RESERVE_BYTES:
            raise RuntimeError("fixture cohort storage consumed protected failure reserve")
        registry_bytes = sum(p.stat().st_size for p in cohort_root.glob("registry.sqlite*"))
    data = {"schema_version": 2, "purpose": "production_isolated_fixed_fixture_resource_qualification",
        "platform": __import__("platform").platform(), "python": __import__("sys").version,
        "runtime_fingerprint": current_runtime(),
        "study_cohort_generated": False, "independent_scm_n": 0,
        "decision_regret_analysis": False, "template_node_strata": len(STRATA),
        "topology_source_sha256": topology_source_sha256,
        "registry_rows_are_fixed_fixture_test_doubles": True,
        "study_eligible_admissions": 0,
        "repetitions_per_stratum": REPETITIONS,
        "whole_cohort_storage_bytes": cohort_storage_bytes,
        "whole_cohort_storage_cap_bytes": COHORT_STORAGE_CAP_BYTES,
        "failure_reserve_bytes": FAILURE_RESERVE_BYTES,
        "minimum_free_disk_bytes": MINIMUM_FREE_DISK_BYTES,
        "registry_sqlite_and_wal_bytes": registry_bytes,
        "registry_counts": counts,
        "isolated_noop_spawn_and_initialization_samples_seconds": spawn_samples,
        "isolated_noop_spawn_and_initialization_median_seconds": statistics.median(spawn_samples),
        "settings": {"isolate_stages": True, "unit_timeout_seconds": UNIT_TIMEOUT_SECONDS,
            "rss_sampled_kill_bytes": RSS_MONITOR_BYTES, "scm_active_stage_cap_seconds": WALL_CAP_SECONDS,
            "individual_ledger_cap_bytes": LEDGER_CAP_BYTES,
            "cohort_storage_monitor_tested": "enabled for shared registry/WAL and all fixture ledgers; all appends guarded"},
        "process_rss_snapshot_before_bytes": process_rss_before,
        "process_rss_snapshot_after_bytes": _rss_bytes(),
        "rss_note": "parent process snapshots; child RSS is sampled by runner and may overshoot between checks; not peak RSS bound",
        "rows": rows,
        "limitations": ["fixture measurements are not SCM samples", "one run per accepted topology does not estimate p95 or tail risk",
            "proposal rejection stage costs are reported separately in step4c2_proposal_cost_benchmark_v1.json",
            "OS filesystem quota is not enforced",
            "RSS is sampled child working-set size and may overshoot between samples"]}
    out = root_path / "step4c2_resource_qualification_v2.json"
    out.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return data


if __name__ == "__main__":
    result = qualify()
    print(json.dumps({"output": "step4c2_resource_qualification_v2.json",
        "rows": len(result["rows"]), "fixture_runs": sum(len(r["runs"]) for r in result["rows"])}))

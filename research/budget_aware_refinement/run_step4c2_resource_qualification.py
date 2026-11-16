"""Fixed-fixture resource qualification; never emits a study cohort artifact.

Repeated runs reuse one deterministic mock fixture per node count. The JSON
contains timings, byte counts and hashes only, not model outcomes or regret.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import statistics
import tempfile
import time

import numpy as np

from .step4c1_pipeline import run_eligible_proposal
from .step4c1_proposal import build_structural_proposal
from .step4c1_scm import _topological_order
from .step4b4_mock_runner import recover_jsonl
from .step4c1_cohort import CohortRegistry


def _rss_bytes() -> int | None:
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes

        class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
            _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
                        ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                        ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t)]
        counters = PROCESS_MEMORY_COUNTERS()
        counters.cb = ctypes.sizeof(counters)
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        psapi = ctypes.WinDLL("psapi", use_last_error=True)
        kernel32.GetCurrentProcess.restype = wintypes.HANDLE
        psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE,
            ctypes.POINTER(PROCESS_MEMORY_COUNTERS), wintypes.DWORD]
        psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
        handle = kernel32.GetCurrentProcess()
        ok = psapi.GetProcessMemoryInfo(handle, ctypes.byref(counters), counters.cb)
        return int(counters.WorkingSetSize) if ok else None
    try:
        import resource
        peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        return int(peak if os.name == "darwin" else peak * 1024)
    except (ImportError, AttributeError):
        return None


def _fixture(node_count: int, repeat: int) -> tuple[dict, dict]:
    proposal = None
    for index in range(128):
        candidate = build_structural_proposal(cohort="development", master_seed=20261116,
            proposal_id=f"resource-n{node_count}-fixture-{index:03d}", attempt=0,
            template="multiple_directed_paths", node_count=node_count)
        if candidate["accepted"]:
            proposal = candidate
            break
    if proposal is None:
        raise RuntimeError(f"fixed resource fixture unavailable for n={node_count}")
    edges = proposal["topology_edges"]
    nodes = proposal["nodes"]
    truth = {"nodes": nodes, "topological_order": list(_topological_order(nodes, edges)),
        "edges": edges, "coefficients": {f"{a}->{b}": .5 for a, b in edges},
        "noise": {"family": "explicit resource test double",
                  "means": {node: 0.0 for node in nodes},
                  "sd": {node: 1.0 for node in nodes}}}
    noise = np.random.default_rng(8000 + node_count).normal(size=(512, node_count))
    return proposal, {"truth_spec": truth, "exogenous_noise": noise}


def qualify(*, repetitions: int = 3) -> dict:
    if repetitions < 2:
        raise ValueError("at least two repeats are required for a descriptive p95")
    rows = []
    rss_initial = _rss_bytes()
    for n in range(6, 11):
        proposal, fixture = _fixture(n, 0)
        times, ledger_sizes, resumes, registry_seconds = [], [], [], []
        for repeat in range(repetitions):
            with tempfile.TemporaryDirectory(prefix="step4c2-resource-") as td:
                ledger = Path(td) / "cohort" / f"fixture-{n}-{repeat}.jsonl"
                ledger.parent.mkdir(parents=True)
                started = time.perf_counter()
                result = run_eligible_proposal(proposal, ledger, delta=1,
                    isolate_stages=False, max_rss_bytes=None, _fixture_payload=fixture)
                times.append(time.perf_counter() - started)
                ledger_sizes.append(ledger.stat().st_size)
                events = recover_jsonl(ledger)
                if result.get("status") != "OK" or not events or events[-1].get("status") != "OK":
                    raise RuntimeError(f"fixed runner fixture did not complete for n={n}")
                terminal_digest = next(event["result_sha256"] for event in reversed(events)
                    if event.get("event") == "terminal" and event.get("status") == "OK")
                digest = hashlib.sha256(ledger.read_bytes()).hexdigest()
                # Replaying a completed ledger measures durable checkpoint validation,
                # not a second SCM or independent observation.
                started = time.perf_counter()
                resumed = run_eligible_proposal(proposal, ledger, delta=1,
                    isolate_stages=False, max_rss_bytes=None, _fixture_payload=fixture)
                resumes.append(time.perf_counter() - started)
                resumed_events = recover_jsonl(ledger)
                resumed_digest = next(event["result_sha256"] for event in reversed(resumed_events)
                    if event.get("event") == "terminal" and event.get("status") == "OK")
                if resumed_digest != terminal_digest:
                    raise RuntimeError("completed fixture replay changed final result hash")
                if hashlib.sha256(ledger.read_bytes()).hexdigest() != digest:
                    raise RuntimeError("completed fixture replay changed ledger bytes")
                registry = CohortRegistry(Path(td) / "registry.sqlite")
                reg_started = time.perf_counter()
                registry.admit(proposal, "fixture-config", ledger)
                registry.bind_equation_signature("development", proposal["proposal_id"],
                    proposal["attempt"], f"fixture-signature-{n}-{repeat}")
                registry_seconds.append(time.perf_counter() - reg_started)
        ordered = sorted(times)
        p95 = ordered[min(len(ordered)-1, int(np.ceil(.95*len(ordered)))-1)]
        rows.append({"node_count": n, "fixture_topology_sha256": proposal["topology_hash"],
            "repetitions_same_fixture": repetitions, "median_seconds": statistics.median(times),
            "p95_seconds_nearest_rank": p95, "max_seconds": max(times),
            "resume_median_seconds": statistics.median(resumes),
            "registry_admit_and_signature_seconds_median": statistics.median(registry_seconds),
            "ledger_bytes_median": int(statistics.median(ledger_sizes)),
            "ledger_bytes_max": max(ledger_sizes), "complete": True})
    return {"schema_version": 1, "purpose": "fixed_fixture_resource_qualification_only",
        "study_cohort_generated": False, "independent_scm_n": 0,
        "decision_regret_analysis": False, "repetitions_per_node_count": repetitions,
        "rss_initial_bytes": rss_initial, "rss_after_bytes": _rss_bytes(),
        "rss_before_and_after_are_process_snapshots_not_stage_peak": True,
        "results": rows,
        "extrapolation": {"development_64_seconds_at_measured_median":
            64 * statistics.median(row["median_seconds"] for row in rows),
            "replication_200_seconds_at_measured_median":
            200 * statistics.median(row["median_seconds"] for row in rows),
            "warning": "linear fixture extrapolation only; excludes generation, coordination overhead and tail risk"}}


def main() -> None:
    result = qualify()
    target = Path(__file__).with_name("step4c2_resource_qualification_v1.json")
    target.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(target)


if __name__ == "__main__":
    main()

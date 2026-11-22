"""Run one deterministic TEST_ONLY fixture and store a new result file once."""
import argparse
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.original_objective.e2e_fixture import run_fixed_fixture
from research.original_objective.fixed_fixture_data import make_fixed_fixture


def peak_rss_bytes():
    if sys.platform != "win32":
        return None
    import ctypes
    from ctypes import wintypes

    class Counters(ctypes.Structure):
        _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
                    ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                    ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                    ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t)]
    counters = Counters()
    counters.cb = ctypes.sizeof(counters)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    psapi = ctypes.WinDLL("psapi", use_last_error=True)
    kernel32.GetCurrentProcess.restype = wintypes.HANDLE
    psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD]
    psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
    process = kernel32.GetCurrentProcess()
    ok = psapi.GetProcessMemoryInfo(process, ctypes.byref(counters), counters.cb)
    return int(counters.PeakWorkingSetSize) if ok else None


def jsonable(value):
    if isinstance(value, dict):
        return {(json.dumps(list(key), ensure_ascii=False) if isinstance(key, tuple) else str(key)):
                jsonable(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [jsonable(item) for item in value]
    return value


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path,
                        default=ROOT / "research/original_objective/test_outputs/e2e_fixture_v1.json")
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit(f"refusing to overwrite existing fixture output: {args.output}")
    fixture, meta = make_fixed_fixture()
    started = time.perf_counter()
    result = run_fixed_fixture(fixture, budgets=(0, 1, 2, 3, 4))
    elapsed = time.perf_counter() - started
    result["qualification"] = {
        "classification": "TEST_ONLY_FIXED_FIXTURE_NOT_RESEARCH_RESULT",
        "wall_seconds_run_only": elapsed,
        "process_peak_working_set_bytes": peak_rss_bytes(),
        "output_storage_bytes": None,
        "registry_bytes": 0,
        "checkpoint_bytes": 0,
        "fixture_description": "explicit 8-node signed-linear DAG, explicit coefficients, deterministic 512-row exogenous sequence",
        "topology_metadata": meta,
        "cohort_resume_tested": False,
        "study_cohort_generated": False
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    serializable = jsonable(result)
    serializable["qualification"]["output_storage_bytes"] = 0
    while True:
        encoded = (json.dumps(serializable, ensure_ascii=False, sort_keys=True, indent=2,
                              allow_nan=False) + "\n").encode("utf-8")
        if serializable["qualification"]["output_storage_bytes"] == len(encoded):
            break
        serializable["qualification"]["output_storage_bytes"] = len(encoded)
    with args.output.open("xb") as f:
        f.write(encoded)
    print(json.dumps({"output": str(args.output), "wall_seconds_run_only": elapsed,
                      "process_peak_working_set_bytes": serializable["qualification"]["process_peak_working_set_bytes"],
                      "output_storage_bytes": len(encoded), "status": serializable["status"]}, indent=2))


if __name__ == "__main__":
    main()

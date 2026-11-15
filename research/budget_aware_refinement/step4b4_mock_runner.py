"""Outcome-free, resumable runner for Step 4B-4 execution-contract tests.

This runner accepts injected deterministic stage functions. It is a software
contract fixture, not the future study runner and not an SCM experiment.
"""
from __future__ import annotations

import hashlib
import json
import math
import multiprocessing
import numbers
import os
import sys
import time
from pathlib import Path
from typing import Callable, Mapping


class SimulatedProcessStop(BaseException):
    """Models abrupt process termination; deliberately bypasses normal catches."""


class LedgerConflict(ValueError):
    pass


def process_rss_bytes() -> int | None:
    """Best-effort process RSS including native allocations; monitoring only."""
    if sys.platform == "win32":
        import ctypes

        class Counters(ctypes.Structure):
            _fields_ = [("cb", ctypes.c_ulong), ("PageFaultCount", ctypes.c_ulong),
                        ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                        ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t),
                        ("PrivateUsage", ctypes.c_size_t)]
        counters = Counters()
        counters.cb = ctypes.sizeof(Counters)
        fn = ctypes.WinDLL("Psapi.dll").GetProcessMemoryInfo
        fn.argtypes = [ctypes.c_void_p, ctypes.POINTER(Counters), ctypes.c_ulong]
        fn.restype = ctypes.c_int
        if fn(ctypes.windll.kernel32.GetCurrentProcess(), ctypes.byref(counters), counters.cb):
            return int(counters.WorkingSetSize)
        return None
    try:
        import resource
        value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        return int(value if sys.platform == "darwin" else value * 1024)
    except (ImportError, AttributeError, OSError):
        return None


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def recover_jsonl(path: Path) -> list[dict]:
    """Read complete records and truncate only a non-newline-terminated tail."""
    if not path.exists():
        return []
    raw = path.read_bytes()
    if raw and not raw.endswith(b"\n"):
        boundary = raw.rfind(b"\n") + 1
        with path.open("r+b") as handle:
            handle.truncate(boundary)
            handle.flush()
            os.fsync(handle.fileno())
        raw = raw[:boundary]
    rows = []
    for line_no, line in enumerate(raw.splitlines(), 1):
        try:
            row = json.loads(line)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError(f"corrupt complete JSONL record at line {line_no}") from exc
        if not isinstance(row, dict):
            raise ValueError(f"JSONL record {line_no} is not an object")
        digest = row.get("event_sha256")
        if digest is not None:
            payload = dict(row)
            payload.pop("event_sha256", None)
            if hashlib.sha256(_canonical(payload)).hexdigest() != digest:
                raise ValueError(f"event digest mismatch at line {line_no}")
        if "output_sha256" in row:
            if hashlib.sha256(_canonical(row.get("output"))).hexdigest() != row["output_sha256"]:
                raise ValueError(f"output digest mismatch at line {line_no}")
        rows.append(row)
    return rows


def append_event(path: Path, event: dict, *, max_bytes: int) -> bool:
    """Append one fsynced event; duplicate identical keys are idempotent."""
    rows = recover_jsonl(path)
    key = (event["run_id"], event["event"])
    for prior in rows:
        if (prior.get("run_id"), prior.get("event")) == key:
            if _canonical(prior) != _canonical(event):
                raise LedgerConflict(f"conflicting replay for {key}")
            return False
    line = _canonical(event) + b"\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = path.stat().st_size if path.exists() else 0
    if existing + len(line) > max_bytes:
        raise OSError("ledger disk cap would be exceeded")
    with path.open("ab") as handle:
        handle.write(line)
        handle.flush()
        os.fsync(handle.fileno())
    return True


def _event(run_id: str, event: str, **fields: object) -> dict:
    if "output" in fields:
        fields["output_sha256"] = hashlib.sha256(_canonical(fields["output"])).hexdigest()
    payload = {"run_id": run_id, "event": event, **fields}
    payload["event_sha256"] = hashlib.sha256(_canonical(payload)).hexdigest()
    return payload


def run_pipeline(
    run_id: str,
    ledger: Path,
    stages: Mapping[str, Callable[[], object]],
    *,
    rng_key: str = "mock-fixture-v1",
    config: object = None,
    input_sha256: str = "unbound-mock-input",
    max_wall_seconds: float = 1800.0,
    max_unit_seconds: float = 2.0,
    max_ledger_bytes: int = 100 * 1024 * 1024,
    max_rss_bytes: int | None = 512 * 1024 * 1024,
    isolate_stages: bool = False,
    checkpoint_hook: Callable[[str], None] | None = None,
    clock: Callable[[], float] = time.monotonic,
) -> dict:
    """Run graph→fit→recommend→truth-stub and resume at completed stages.

    Wall/unit time and RSS are checked at stage boundaries, not preemptively.
    The ledger cap is enforced before writes. RSS is monitoring only in this
    in-process mock; it cannot prevent a transient peak inside a stage.
    """
    expected = ("graph", "fit", "recommend", "truth")
    if tuple(stages) != expected:
        raise ValueError(f"stages must be ordered exactly as {expected}")
    if not run_id or not rng_key:
        raise ValueError("run_id and rng_key must be non-empty")
    if max_wall_seconds <= 0 or max_unit_seconds <= 0 or max_ledger_bytes < 512:
        raise ValueError("time caps must be positive and ledger cap must reserve at least 512 bytes")
    prior = recover_jsonl(ledger)
    config_sha256 = hashlib.sha256(_canonical(config)).hexdigest()
    bindings = {"rng_key": rng_key, "config_sha256": config_sha256, "input_sha256": input_sha256}
    if any(row.get("run_id") == run_id and row.get("rng_key") != rng_key for row in prior):
        raise LedgerConflict(f"run_id {run_id!r} was already used with another RNG key")
    def event(name: str, **fields: object) -> dict:
        return _event(run_id, name, **bindings, **fields)
    run_rows = [row for row in prior if row.get("run_id") == run_id]
    for row in run_rows:
        if any(row.get(k) != v for k, v in bindings.items()):
            raise LedgerConflict(f"run_id {run_id!r} has a different or unbound execution contract")
    names = [row.get("event") for row in run_rows]
    stage_names = [name.split(":", 1)[1] for name in names if isinstance(name, str) and name.startswith("stage:")]
    if stage_names != list(dict.fromkeys(stage_names)) or stage_names != list(expected[:len(stage_names)]):
        raise LedgerConflict("checkpoint stages are duplicated or out of order")
    if names.count("terminal") > 1 or ("terminal" in names and names[-1] != "terminal"):
        raise LedgerConflict("invalid terminal event placement")
    done = {row["event"].split(":", 1)[1]: row for row in prior
            if row.get("run_id") == run_id and row.get("event", "").startswith("stage:")}
    terminal = next((r for r in prior if r.get("run_id") == run_id and r.get("event") == "terminal"), None)
    if terminal:
        if terminal.get("status") == "OK" and stage_names != list(expected):
            raise LedgerConflict("successful terminal exists without every ordered stage")
        if terminal.get("completed_stages") != stage_names:
            raise LedgerConflict("terminal completed-stage list does not match ledger")
        return {"status": terminal["status"], "resumed": True, "completed_stages": list(done)}
    start = clock()
    for stage in expected:
        if stage in done:
            continue
        current_bytes = ledger.stat().st_size if ledger.exists() else 0
        # Reserve enough room for a compact stop event before starting a unit.
        if current_bytes + 512 > max_ledger_bytes:
            status = "DISK_CAP"
            append_event(ledger, event("terminal", status=status,
                                        completed_stages=sorted(done)), max_bytes=max_ledger_bytes)
            return {"status": status, "resumed": bool(done), "completed_stages": sorted(done)}
        if clock() - start >= max_wall_seconds:
            status = "WALL_CAP"
            append_event(ledger, event("terminal", status=status,
                                        completed_stages=sorted(done)), max_bytes=max_ledger_bytes)
            return {"status": status, "resumed": bool(done), "completed_stages": sorted(done)}
        unit_start = clock()
        try:
            if isolate_stages:
                output, child_status = _run_isolated(stages[stage], max_unit_seconds, max_rss_bytes)
                if child_status == "STAGE_EXCEPTION":
                    raise RuntimeError("isolated stage raised an exception")
                if child_status:
                    append_event(ledger, event(f"stage:{stage}", status=child_status), max_bytes=max_ledger_bytes - 256)
                    append_event(ledger, event("terminal", status=child_status,
                                                completed_stages=list(done)), max_bytes=max_ledger_bytes)
                    return {"status": child_status, "resumed": bool(done), "completed_stages": list(done)}
            else:
                output = stages[stage]()
            unit_seconds = clock() - unit_start
            elapsed_total = clock() - start
            rss = process_rss_bytes()
            cap_status = None
            if not isolate_stages and unit_seconds > max_unit_seconds:
                cap_status = "TIMEOUT"
            elif elapsed_total >= max_wall_seconds:
                cap_status = "WALL_CAP"
            elif not isolate_stages and max_rss_bytes is not None and rss is not None and rss > max_rss_bytes:
                cap_status = "RSS_CAP_MONITOR"
            if cap_status:
                append_event(ledger, event(f"stage:{stage}", status=cap_status,
                                            elapsed_seconds=unit_seconds, elapsed_total_seconds=elapsed_total,
                                            observed_rss_bytes=rss, output=output),
                             max_bytes=max_ledger_bytes - 256)
                append_event(ledger, event("terminal", status=cap_status,
                                            completed_stages=sorted(done)), max_bytes=max_ledger_bytes)
                return {"status": cap_status, "resumed": bool(done), "completed_stages": sorted(done)}
            row = event(f"stage:{stage}", status="OK", output=output)
            try:
                append_event(ledger, row, max_bytes=max_ledger_bytes - 512)
            except OSError:
                status = "DISK_CAP"
                append_event(ledger, event("terminal", status=status,
                                            completed_stages=sorted(done)), max_bytes=max_ledger_bytes)
                return {"status": status, "resumed": bool(done), "completed_stages": sorted(done)}
            done[stage] = row
            if checkpoint_hook is not None:
                checkpoint_hook(stage)
        except SimulatedProcessStop:
            raise
        except Exception as exc:
            status = {"fit": "RIDGE_FAIL", "recommend": "RECOMMEND_FAIL", "truth": "GT_EVAL_FAIL"}.get(stage, "STAGE_FAIL")
            detail = {"status": status, "failure_type": type(exc).__name__, "reason": str(exc)[:300]}
            append_event(ledger, event(f"stage:{stage}", **detail), max_bytes=max_ledger_bytes)
            append_event(ledger, event("terminal", status=status,
                                        completed_stages=sorted(done)), max_bytes=max_ledger_bytes)
            return {"status": status, "resumed": bool(done), "completed_stages": sorted(done)}
    append_event(ledger, event("terminal", status="OK", completed_stages=list(expected)),
                 max_bytes=max_ledger_bytes)
    return {"status": "OK", "resumed": any(row.get("run_id") == run_id for row in prior),
            "completed_stages": list(expected)}


def composite_scm_result(type_rows: Mapping[str, Mapping[str, object]]) -> dict:
    """Keep a paired SCM vector incomplete if any type or policy value is absent."""
    required = ("FN", "FP", "REV")
    if set(type_rows) != set(required):
        return {"complete": False, "D_i": None, "reason": "missing_or_extra_type"}
    diffs = []
    for kind in required:
        row = type_rows[kind]
        if row.get("status") != "OK":
            return {"complete": False, "D_i": None, "status": "INCOMPLETE", "reason": f"incomplete_{kind}"}
        vals = (row.get("global_regret"), row.get("task_focused_regret"))
        if any(not isinstance(v, numbers.Real) or isinstance(v, bool) or not math.isfinite(float(v)) for v in vals):
            return {"complete": False, "D_i": None, "status": "NONFINITE", "reason": f"invalid_regret_{kind}"}
        diff = float(vals[0]) - float(vals[1])
        if not math.isfinite(diff):
            return {"complete": False, "D_i": None, "status": "NONFINITE", "reason": f"invalid_difference_{kind}"}
        diffs.append(diff)
    mean = math.fsum(diffs) / 3.0
    if not math.isfinite(mean):
        return {"complete": False, "D_i": None, "status": "NONFINITE", "reason": "invalid_composite"}
    return {"complete": True, "status": "OK", "D_i": mean, "type_differences": diffs}


def _worker(conn, stage):
    try:
        conn.send(("OK", stage()))
    except BaseException as exc:
        conn.send(("EXCEPTION", type(exc).__name__, str(exc)[:300]))
    finally:
        conn.close()


def _rss_for_pid(pid: int) -> int | None:
    if sys.platform.startswith("linux"):
        try:
            resident_pages = int(Path(f"/proc/{pid}/statm").read_text().split()[1])
            return resident_pages * os.sysconf("SC_PAGE_SIZE")
        except (OSError, ValueError, IndexError):
            return None
    if sys.platform == "win32":
        import ctypes
        from ctypes import wintypes
        class Counters(ctypes.Structure):
            _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
                        ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                        ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t),
                        ("PrivateUsage", ctypes.c_size_t)]
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        psapi = ctypes.WinDLL("Psapi.dll", use_last_error=True)
        handle = kernel.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
        if not handle:
            return None
        try:
            counters = Counters()
            counters.cb = ctypes.sizeof(Counters)
            if psapi.GetProcessMemoryInfo(handle, ctypes.byref(counters), counters.cb):
                return int(counters.WorkingSetSize)
        finally:
            kernel.CloseHandle(handle)
    return None


def _run_isolated(stage, timeout: float, rss_cap: int | None):
    ctx = multiprocessing.get_context("spawn")
    parent, child = ctx.Pipe(duplex=False)
    proc = ctx.Process(target=_worker, args=(child, stage))
    proc.start()
    child.close()
    started = time.monotonic()
    failure = None
    message = None
    while proc.is_alive():
        try:
            available = parent.poll()
        except OSError:
            available = False
        if available:
            try:
                message = parent.recv()
            except (EOFError, OSError):
                message = None
            break
        if time.monotonic() - started > timeout:
            failure = "TIMEOUT"
            break
        rss = _rss_for_pid(proc.pid)
        if rss_cap is not None and rss is not None and rss > rss_cap:
            failure = "RSS_LIMIT"
            break
        proc.join(0.01)
    if failure:
        proc.terminate()
        proc.join(0.5)
        if proc.is_alive() and hasattr(proc, "kill"):
            proc.kill()
            proc.join()
        return None, failure
    proc.join()
    if message is None:
        try:
            if parent.poll():
                message = parent.recv()
        except (EOFError, OSError):
            message = None
    parent.close()
    if message is None:
        return None, "CHILD_EXIT"
    if message[0] == "EXCEPTION":
        return None, "STAGE_EXCEPTION"
    return message[1], None

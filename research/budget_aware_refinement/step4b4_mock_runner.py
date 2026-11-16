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


class StageFailure(RuntimeError):
    """A stage failure with a research-contract status code."""
    def __init__(self, status: str, reason: str):
        super().__init__(reason)
        self.status = status


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


def append_event(path: Path, event: dict, *, max_bytes: int,
                 pre_write_guard: Callable[[Path, dict, int], None] | None = None) -> bool:
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
    if pre_write_guard is not None:
        pre_write_guard(path, event, len(line))
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
    scm_id: str = "dev-mock-scm",
    cohort: str = "development",
    max_wall_seconds: float = 1800.0,
    max_unit_seconds: float = 2.0,
    max_ledger_bytes: int = 100 * 1024 * 1024,
    max_rss_bytes: int | None = 512 * 1024 * 1024,
    isolate_stages: bool = False,
    checkpoint_hook: Callable[[str], None] | None = None,
    pre_write_guard: Callable[[Path, dict, int], None] | None = None,
    clock: Callable[[], float] = time.monotonic,
) -> dict:
    """Run an ordered durable stage pipeline and resume completed stages.

    Wall/unit time and RSS are checked at stage boundaries, not preemptively.
    The ledger cap is enforced before writes. RSS is monitoring only in this
    in-process mock; it cannot prevent a transient peak inside a stage.
    """
    expected = tuple(stages)
    if not expected or any(not isinstance(name, str) or not name for name in expected) or len(set(expected)) != len(expected):
        raise ValueError("stages must be a nonempty ordered mapping with unique names")
    if not run_id or not rng_key or not scm_id or cohort not in {"development", "confirmation"}:
        raise ValueError("run_id, RNG key, SCM ID and valid cohort are required")
    required_prefix = "dev-" if cohort == "development" else "rep-"
    if not scm_id.startswith(required_prefix):
        raise ValueError(f"SCM ID must use cohort namespace {required_prefix!r}")
    if max_wall_seconds <= 0 or max_unit_seconds <= 0 or max_ledger_bytes < 512:
        raise ValueError("time caps must be positive and ledger cap must reserve at least 512 bytes")
    prior = recover_jsonl(ledger)
    config_sha256 = hashlib.sha256(_canonical(config)).hexdigest()
    bindings = {"rng_key": rng_key, "config_sha256": config_sha256,
                "input_sha256": input_sha256, "scm_id": scm_id, "cohort": cohort}
    if any(row.get("run_id") == run_id and row.get("rng_key") != rng_key for row in prior):
        raise LedgerConflict(f"run_id {run_id!r} was already used with another RNG key")
    def event(name: str, **fields: object) -> dict:
        return _event(run_id, name, **bindings, **fields)
    def write_event(row: dict, *, max_bytes: int) -> bool:
        return append_event(ledger, row, max_bytes=max_bytes,
                           pre_write_guard=pre_write_guard)
    run_rows = [row for row in prior if row.get("run_id") == run_id]
    if any(row.get("scm_id") == scm_id and row.get("cohort") == cohort
           and row.get("run_id") != run_id for row in prior):
        raise LedgerConflict("an independent SCM ID is already bound to another run ID")
    for row in run_rows:
        if not row.get("event_sha256"):
            raise LedgerConflict("legacy unversioned events cannot resume under the production contract")
        if any(row.get(k) != v for k, v in bindings.items()):
            raise LedgerConflict(f"run_id {run_id!r} has a different or unbound execution contract")
    names = [row.get("event") for row in run_rows]
    stage_rows = [row for row in run_rows if isinstance(row.get("event"), str) and row["event"].startswith("stage:")]
    stage_names = [row["event"].split(":", 1)[1] for row in stage_rows]
    if stage_names != list(dict.fromkeys(stage_names)) or stage_names != list(expected[:len(stage_names)]):
        raise LedgerConflict("checkpoint stages are duplicated or out of order")
    if names.count("terminal") > 1 or ("terminal" in names and names[-1] != "terminal"):
        raise LedgerConflict("invalid terminal event placement")
    stage_events = {row["event"].split(":", 1)[1]: row for row in stage_rows}
    done = {stage: row for stage, row in stage_events.items() if row.get("status") == "OK"}
    elapsed_used = math.fsum(float(row.get("elapsed_seconds", 0.0)) for row in stage_rows)
    if not math.isfinite(elapsed_used) or elapsed_used < 0:
        raise LedgerConflict("invalid cumulative stage elapsed time")
    terminal = next((r for r in prior if r.get("run_id") == run_id and r.get("event") == "terminal"), None)
    if terminal:
        if terminal.get("status") == "OK" and list(done) != list(expected):
            raise LedgerConflict("successful terminal exists without every ordered stage")
        if terminal.get("completed_stages") != list(done):
            raise LedgerConflict("terminal completed stages do not match successful checkpoints")
        failed = next((row for row in reversed(stage_rows) if row.get("status") != "OK"), None)
        if failed and terminal.get("status") != failed.get("status"):
            raise LedgerConflict("terminal does not preserve the failed-stage status")
        if terminal.get("status") == "OK" and terminal.get("result_sha256") != _result_digest(done, expected):
            raise LedgerConflict("terminal result digest does not match successful stage outputs")
        return {"status": terminal["status"], "resumed": True, "completed_stages": list(done)}
    failed = next((row for row in reversed(stage_rows) if row.get("status") != "OK"), None)
    if failed:
        status = failed["status"]
        write_event(event("terminal", status=status, completed_stages=list(done),
                                    cumulative_elapsed_seconds=elapsed_used), max_bytes=max_ledger_bytes)
        return {"status": status, "resumed": True, "completed_stages": list(done)}
    for stage in expected:
        if stage in done:
            continue
        current_bytes = ledger.stat().st_size if ledger.exists() else 0
        # Reserve enough room for a compact stop event before starting a unit.
        if current_bytes + 512 > max_ledger_bytes:
            status = "DISK_CAP"
            write_event(event("terminal", status=status,
                                        completed_stages=sorted(done)), max_bytes=max_ledger_bytes)
            return {"status": status, "resumed": bool(done), "completed_stages": sorted(done)}
        remaining = max_wall_seconds - elapsed_used
        if remaining <= 0:
            status = "WALL_CAP"
            write_event(event("terminal", status=status,
                                        completed_stages=list(done), cumulative_elapsed_seconds=elapsed_used), max_bytes=max_ledger_bytes)
            return {"status": status, "resumed": bool(done), "completed_stages": sorted(done)}
        unit_start = clock()
        try:
            if isolate_stages:
                output, child_status, unit_seconds = _run_isolated(
                    stages[stage], min(max_unit_seconds, remaining), max_rss_bytes
                )
                if child_status == "STAGE_EXCEPTION":
                    raise RuntimeError("isolated stage raised an exception")
                if child_status:
                    status = child_status.split("|", 1)[0].removeprefix("STAGE_FAILURE:") if child_status.startswith("STAGE_FAILURE:") else child_status
                    elapsed_used += unit_seconds
                    write_event(event(f"stage:{stage}", status=status,
                                                elapsed_seconds=unit_seconds, elapsed_total_seconds=elapsed_used), max_bytes=max_ledger_bytes - 512)
                    write_event(event("terminal", status=status,
                                                completed_stages=list(done), cumulative_elapsed_seconds=elapsed_used), max_bytes=max_ledger_bytes)
                    return {"status": status, "resumed": bool(done), "completed_stages": list(done)}
            else:
                output = stages[stage]()
            unit_seconds = clock() - unit_start
            elapsed_used += max(0.0, unit_seconds)
            elapsed_total = elapsed_used
            rss = process_rss_bytes()
            cap_status = None
            if not isolate_stages and unit_seconds > max_unit_seconds:
                cap_status = "TIMEOUT"
            elif elapsed_total >= max_wall_seconds:
                cap_status = "WALL_CAP"
            elif not isolate_stages and max_rss_bytes is not None and rss is not None and rss > max_rss_bytes:
                cap_status = "RSS_CAP_MONITOR"
            if cap_status:
                write_event(event(f"stage:{stage}", status=cap_status,
                                            elapsed_seconds=unit_seconds, elapsed_total_seconds=elapsed_total,
                                            observed_rss_bytes=rss, output=output),
                             max_bytes=max_ledger_bytes - 512)
                write_event(event("terminal", status=cap_status,
                                            completed_stages=list(done), cumulative_elapsed_seconds=elapsed_used), max_bytes=max_ledger_bytes)
                return {"status": cap_status, "resumed": bool(done), "completed_stages": sorted(done)}
            row = event(f"stage:{stage}", status="OK", output=output,
                        elapsed_seconds=max(0.0, unit_seconds), elapsed_total_seconds=elapsed_total)
            try:
                write_event(row, max_bytes=max_ledger_bytes - 512)
            except OSError:
                status = "DISK_CAP"
                write_event(event("terminal", status=status,
                                            completed_stages=list(done), cumulative_elapsed_seconds=elapsed_used), max_bytes=max_ledger_bytes)
                return {"status": status, "resumed": bool(done), "completed_stages": sorted(done)}
            done[stage] = row
            if checkpoint_hook is not None:
                checkpoint_hook(stage)
        except SimulatedProcessStop:
            raise
        except Exception as exc:
            status = getattr(exc, "status", None) or {"fit": "RIDGE_FAIL", "recommend": "RECOMMEND_FAIL",
                      "recommendations": "RECOMMEND_FAIL", "truth": "GT_EVAL_FAIL",
                      "gt_evaluation": "GT_EVAL_FAIL", "scm": "SCM_GEN_FAIL",
                      "observations": "DATA_FAIL", "error_graphs": "ERROR_INJECTION_FAIL",
                      "policy_graphs": "POLICY_GRAPH_FAIL", "proposal": "TOPOLOGY_FAIL"}.get(stage, "STAGE_FAIL")
            unit_seconds = max(0.0, clock() - unit_start)
            elapsed_used += unit_seconds
            detail = {"status": status, "failure_type": type(exc).__name__, "reason": str(exc)[:300],
                      "elapsed_seconds": unit_seconds, "elapsed_total_seconds": elapsed_used}
            write_event(event(f"stage:{stage}", **detail), max_bytes=max_ledger_bytes)
            write_event(event("terminal", status=status,
                                        completed_stages=list(done), cumulative_elapsed_seconds=elapsed_used), max_bytes=max_ledger_bytes)
            return {"status": status, "resumed": bool(done), "completed_stages": sorted(done)}
    write_event(event("terminal", status="OK", completed_stages=list(expected),
                                cumulative_elapsed_seconds=elapsed_used,
                                result_sha256=_result_digest(done, expected)),
                 max_bytes=max_ledger_bytes)
    return {"status": "OK", "resumed": any(row.get("run_id") == run_id for row in prior),
            "completed_stages": list(expected)}


def composite_scm_result(type_rows: Mapping[str, Mapping[str, object]]) -> dict:
    """Keep a paired SCM vector incomplete if any type or policy value is absent."""
    from .step4b4_failure_rules import scm_composite
    required = ("FN", "FP", "REV")
    if set(type_rows) != set(required):
        return {"complete": False, "D_i": None, "reason": "missing_or_extra_type"}
    differences = {}
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
        differences[kind] = diff
    return scm_composite(differences)


def _result_digest(done: Mapping[str, Mapping[str, object]], expected) -> str:
    payload = [{"stage": name, "output_sha256": done[name].get("output_sha256")}
               for name in expected]
    return hashlib.sha256(_canonical(payload)).hexdigest()


def _worker(conn, stage):
    try:
        conn.send(("OK", stage()))
    except StageFailure as exc:
        conn.send(("STAGE_FAILURE", exc.status, str(exc)[:300]))
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
        return None, failure, max(0.0, time.monotonic() - started)
    proc.join()
    if message is None:
        try:
            if parent.poll():
                message = parent.recv()
        except (EOFError, OSError):
            message = None
    parent.close()
    if message is None:
        return None, "CHILD_EXIT", max(0.0, time.monotonic() - started)
    if message[0] == "EXCEPTION":
        return None, "STAGE_EXCEPTION", max(0.0, time.monotonic() - started)
    if message[0] == "STAGE_FAILURE":
        return None, f"STAGE_FAILURE:{message[1]}|{message[2]}", max(0.0, time.monotonic() - started)
    return message[1], None, max(0.0, time.monotonic() - started)

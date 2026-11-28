"""Crash-safe per-SCM ledger mechanics for deterministic fixtures only.

This is not the Research C production cohort entry point. The latter remains
blocked pending scientific approval. This module exercises immutable bindings,
atomic SCM checkpoints, checksums, resume, duplicate protection and boundary
resource stops without generating SCMs itself.
"""
from __future__ import annotations

from contextlib import contextmanager
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import shutil
import time
import uuid

from . import policy_engine as pe


class LedgerConflict(ValueError):
    pass


class ResourceStop(RuntimeError):
    pass


def _canonical(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False).encode("ascii")


def _sha(value) -> str:
    return sha256(value if isinstance(value, bytes) else _canonical(value)).hexdigest()


def _subseed(master_seed: int, cohort: str, scm_id: str, stream: str) -> int:
    return int.from_bytes(bytes.fromhex(_sha(["research-c-seed-v1", master_seed,
                                               cohort, scm_id, stream]))[:8], "big")


@contextmanager
def _run_lock(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = path.open("a+b")
    try:
        if os.name == "nt":
            import msvcrt
            # Avoid reading the lock file before acquiring the byte lock: on
            # Windows a competing process may deny that read even though it
            # correctly allows us to open the handle. Ensure byte 0 exists by
            # inspecting length only, then serialize writers with msvcrt.
            handle.seek(0, os.SEEK_END)
            if handle.tell() == 0:
                handle.seek(0); handle.write(b"0"); handle.flush()
            handle.seek(0)
            try:
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError as exc:
                raise LedgerConflict("run already has an active writer") from exc
        else:
            import fcntl
            try:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError as exc:
                raise LedgerConflict("run already has an active writer") from exc
        yield
    finally:
        try:
            handle.seek(0)
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        except OSError:
            pass
        handle.close()


def _current_rss_bytes() -> int | None:
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
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        psapi = ctypes.WinDLL("psapi", use_last_error=True)
        kernel32.GetCurrentProcess.restype = wintypes.HANDLE
        psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD]
        psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
        ok = psapi.GetProcessMemoryInfo(kernel32.GetCurrentProcess(), ctypes.byref(counters), counters.cb)
        return int(counters.WorkingSetSize) if ok else None
    try:
        import resource
        peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        return int(peak * (1024 if os.name != "darwin" else 1))
    except (ImportError, OSError, ValueError):
        return None


class FixtureCohortLedger:
    """Per-SCM atomic result ledger. It only accepts explicit TEST_ONLY workers."""

    def __init__(self, root: Path, *, run_id: str, cohort: str, master_seed: int,
                 config: dict, expected_policy_ids: list[str], max_active_seconds: float,
                 max_storage_bytes: int, max_rss_bytes: int | None = None,
                 failure_reserve_bytes: int = 65536):
        if not re.fullmatch(r"[A-Za-z0-9._-]{1,100}", run_id):
            raise ValueError("invalid run_id")
        if cohort not in {"development", "independent_evaluation"}:
            raise ValueError("cohort namespace must be development or independent_evaluation")
        if type(master_seed) is not int or master_seed < 0:
            raise ValueError("master_seed must be a nonnegative integer")
        if max_active_seconds <= 0 or max_storage_bytes <= failure_reserve_bytes or failure_reserve_bytes < 0:
            raise ValueError("invalid active-time or storage limits")
        if max_rss_bytes is not None and max_rss_bytes <= 0:
            raise ValueError("max_rss_bytes must be positive")
        if len(expected_policy_ids) != len(set(expected_policy_ids)) or not expected_policy_ids:
            raise ValueError("expected_policy_ids must be unique and nonempty")
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.run_id, self.cohort, self.master_seed = run_id, cohort, master_seed
        self.expected_policy_ids = tuple(expected_policy_ids)
        self.max_active_seconds, self.max_storage_bytes = float(max_active_seconds), int(max_storage_bytes)
        self.max_rss_bytes, self.failure_reserve_bytes = max_rss_bytes, failure_reserve_bytes
        self.binding = {"schema": "research-c-fixture-ledger-v1", "run_id": run_id,
                        "cohort": cohort, "master_seed": master_seed,
                        "config": config, "expected_policy_ids": list(self.expected_policy_ids),
                        "resource_caps": {"active_seconds": self.max_active_seconds,
                                          "storage_bytes": self.max_storage_bytes,
                                          "rss_sampled_bytes": max_rss_bytes}}
        self.config_sha256 = _sha(self.binding)
        self.meta_path = self.root / "run_binding.json"
        self.state_path = self.root / "run_state.json"
        self.lock_path = self.root / ".writer.lock"

    def usage_bytes(self):
        return sum(p.stat().st_size for p in self.root.rglob("*")
                   if p.is_file() and not p.is_symlink() and p != self.lock_path)

    def _atomic_json(self, path: Path, value: dict, *, emergency=False):
        payload = _canonical(value) + b"\n"
        used = self.usage_bytes() - (path.stat().st_size if path.exists() else 0)
        reserve = 0 if emergency else self.failure_reserve_bytes
        if used + len(payload) + reserve > self.max_storage_bytes:
            raise ResourceStop("COHORT_STORAGE_CAP")
        if shutil.disk_usage(self.root).free < len(payload) + (0 if emergency else self.failure_reserve_bytes):
            raise ResourceStop("FILESYSTEM_FREE_SPACE_CAP")
        temp = path.with_name(f".{path.name}.{os.getpid()}.{uuid.uuid4().hex}.tmp")
        try:
            with temp.open("xb") as stream:
                stream.write(payload); stream.flush(); os.fsync(stream.fileno())
            os.replace(temp, path)
            if os.name != "nt":
                fd = os.open(path.parent, os.O_RDONLY)
                try: os.fsync(fd)
                finally: os.close(fd)
        finally:
            if temp.exists():
                temp.unlink()

    def _read_verified(self, path: Path):
        try:
            wrapper = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise LedgerConflict(f"corrupt or unreadable ledger record: {path.name}") from exc
        payload = wrapper.get("payload")
        if not isinstance(payload, dict) or _sha(payload) != wrapper.get("payload_sha256"):
            raise LedgerConflict(f"ledger checksum mismatch: {path.name}")
        if payload.get("run_config_sha256") != self.config_sha256:
            raise LedgerConflict(f"ledger run/config binding mismatch: {path.name}")
        return payload

    def _initialize(self):
        if self.meta_path.exists():
            current = json.loads(self.meta_path.read_text(encoding="utf-8"))
            if current != self.binding:
                raise LedgerConflict("run_id reused with different cohort/config/seeds/resources")
        else:
            self._atomic_json(self.meta_path, self.binding)
        if not self.state_path.exists():
            self._write_record(self.state_path, {"run_config_sha256": self.config_sha256,
                                                 "cumulative_active_seconds": 0.0,
                                                 "status": "READY", "completed_scm_ids": []})
        state = self._read_verified(self.state_path)
        # The state payload is wrapped like all immutable-binding records.
        return state

    def run_fixture(self, scm_ids: list[str], worker, *, max_new_scms: int | None = None):
        if getattr(worker, "__test_only_fixture_worker__", False) is not True:
            raise PermissionError("Research C production execution is gated; fixture worker must be TEST_ONLY")
        if len(scm_ids) != len(set(scm_ids)) or any(not re.fullmatch(r"[A-Za-z0-9._-]{1,100}", s) for s in scm_ids):
            raise ValueError("SCM ids must be unique, safe, and deterministic")
        if max_new_scms is not None and max_new_scms < 0:
            raise ValueError("max_new_scms cannot be negative")
        with _run_lock(self.lock_path):
            state = self._initialize()
            if state["run_config_sha256"] != self.config_sha256:
                raise LedgerConflict("run state config binding mismatch")
            base_elapsed = float(state["cumulative_active_seconds"])
            started = time.monotonic()
            created = 0
            records = []
            for scm_id in scm_ids:
                path = self.root / f"scm-{scm_id}.json"
                if path.exists():
                    record = self._read_verified(path)
                    if record["scm_id"] != scm_id:
                        raise LedgerConflict("SCM result path/id conflict")
                    records.append(record)
                    continue
                elapsed_total = base_elapsed + (time.monotonic() - started)
                rss = _current_rss_bytes()
                stop_reason = ("COHORT_ACTIVE_TIME_CAP" if elapsed_total >= self.max_active_seconds else
                               "SAMPLED_RSS_CAP" if self.max_rss_bytes is not None and rss is not None and rss >= self.max_rss_bytes else None)
                if stop_reason:
                    state.update({"status": "RESOURCE_STOP", "stop_reason": stop_reason,
                                  "cumulative_active_seconds": elapsed_total,
                                  "last_sampled_rss_bytes": rss})
                    self._write_record(self.state_path, state, emergency=True)
                    break
                if max_new_scms is not None and created >= max_new_scms:
                    state.update({"status": "PAUSED_FIXTURE_TEST", "stop_reason": "TEST_PAUSE_AFTER_N_SCMS",
                                  "cumulative_active_seconds": elapsed_total,
                                  "last_sampled_rss_bytes": rss})
                    self._write_record(self.state_path, state)
                    break
                seeds = {stream: _subseed(self.master_seed, self.cohort, scm_id, stream)
                         for stream in ("scm", "g0", "evaluation")}
                if len(set(seeds.values())) != 3:
                    raise LedgerConflict("domain-separated seed collision")
                try:
                    result = worker({"run_id": self.run_id, "cohort": self.cohort,
                                     "scm_id": scm_id, "seeds": seeds,
                                     "config_sha256": self.config_sha256})
                    if not isinstance(result, dict) or result.get("test_only") is not True:
                        raise ValueError("fixture worker must return a TEST_ONLY dict")
                    policy_rows = result.get("policy_results", [])
                    ids = [row.get("policy_id") for row in policy_rows]
                    if len(ids) != len(set(ids)):
                        raise ValueError("duplicate policy result id")
                    exact_vector = set(ids) == set(self.expected_policy_ids)
                    all_success = exact_vector and all(row.get("status") == "OK" for row in policy_rows)
                    status = "COMPLETE_TEST_ONLY" if all_success else "INCOMPLETE_TEST_ONLY"
                    record = {"test_only": True, "run_id": self.run_id,
                              "run_config_sha256": self.config_sha256, "cohort": self.cohort,
                              "scm_id": scm_id, "seeds": seeds,
                              "input_sha256": result.get("input_sha256"),
                              "policy_results": policy_rows, "expected_policy_ids": list(self.expected_policy_ids),
                              "policy_vector_complete": exact_vector,
                              "all_policy_evaluations_successful": all_success,
                              "paired_comparison_allowed": all_success,
                              "status": status, "failure_reason": None if all_success else "INCOMPLETE_POLICY_VECTOR_OR_FAILURE",
                              "output_sha256": _sha(result)}
                except Exception as exc:
                    record = {"test_only": True, "run_id": self.run_id,
                              "run_config_sha256": self.config_sha256, "cohort": self.cohort,
                              "scm_id": scm_id, "seeds": seeds,
                              "input_sha256": None, "policy_results": [],
                              "expected_policy_ids": list(self.expected_policy_ids),
                              "policy_vector_complete": False,
                              "all_policy_evaluations_successful": False,
                              "paired_comparison_allowed": False,
                              "status": "FAILED_TEST_ONLY",
                              "failure_reason": f"{type(exc).__name__}:{str(exc)[:400]}",
                              "output_sha256": None}
                try:
                    self._write_record(path, record)
                except ResourceStop as exc:
                    elapsed_total = base_elapsed + (time.monotonic() - started)
                    state.update({"status": "RESOURCE_STOP", "stop_reason": str(exc),
                                  "cumulative_active_seconds": elapsed_total,
                                  "last_sampled_rss_bytes": _current_rss_bytes()})
                    self._write_record(self.state_path, state, emergency=True)
                    break
                records.append(record); created += 1
                elapsed_total = base_elapsed + (time.monotonic() - started)
                state.update({"status": "RUNNING", "cumulative_active_seconds": elapsed_total,
                              "completed_scm_ids": sorted(set(state.get("completed_scm_ids", [])) | {scm_id}),
                              "last_sampled_rss_bytes": _current_rss_bytes()})
                self._write_record(self.state_path, state)
                if elapsed_total >= self.max_active_seconds:
                    state.update({"status": "RESOURCE_STOP", "stop_reason": "COHORT_ACTIVE_TIME_CAP"})
                    self._write_record(self.state_path, state, emergency=True)
                    break
                if (self.max_rss_bytes is not None and state["last_sampled_rss_bytes"] is not None
                        and state["last_sampled_rss_bytes"] >= self.max_rss_bytes):
                    state.update({"status": "RESOURCE_STOP", "stop_reason": "SAMPLED_RSS_CAP"})
                    self._write_record(self.state_path, state, emergency=True)
                    break
            # Resolve all records, including previously checkpointed ones.
            all_records = [self._read_verified(self.root / f"scm-{scm_id}.json")
                           for scm_id in scm_ids if (self.root / f"scm-{scm_id}.json").exists()]
            complete = len(all_records) == len(scm_ids) and all(r["status"] == "COMPLETE_TEST_ONLY" for r in all_records)
            state = self._read_verified(self.state_path)
            if complete:
                state.update({"status": "COMPLETE_TEST_ONLY", "stop_reason": None})
                self._write_record(self.state_path, state)
            return {"status": state["status"], "run_id": self.run_id,
                    "run_config_sha256": self.config_sha256,
                    "scm_result_count": len(all_records),
                    "complete_test_only_scm_count": sum(r["status"] == "COMPLETE_TEST_ONLY" for r in all_records),
                    "failed_or_incomplete_scm_count": sum(r["status"] != "COMPLETE_TEST_ONLY" for r in all_records),
                    "cumulative_active_seconds": state["cumulative_active_seconds"],
                    "last_sampled_rss_bytes": state.get("last_sampled_rss_bytes"),
                    "storage_bytes": self.usage_bytes(), "records": all_records}

    def _write_record(self, path: Path, payload: dict, *, emergency=False):
        wrapper = {"payload": payload, "payload_sha256": _sha(payload)}
        self._atomic_json(path, wrapper, emergency=emergency)


def run_research_cohort(*_args, **_kwargs):
    raise PermissionError("RESEARCH_C_COHORT_BLOCKED: scientific approval and preregistration are absent")

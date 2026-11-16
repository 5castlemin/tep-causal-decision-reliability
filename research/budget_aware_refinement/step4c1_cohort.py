"""Durable proposal admission and deterministic cohort orchestration.

The coordinator is designed for fixed fixtures in Step 4C-1. Calling it with
the production proposal builder samples topology proposals only; the cohort
targets are not run as part of this module or its tests.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
import shutil
import sqlite3
import time
from contextlib import closing
from contextlib import contextmanager
from pathlib import Path
from typing import Callable, Mapping

from .step4c1_proposal import ATTEMPT_CAPS, ELIGIBLE_TARGETS, STRATA, build_structural_proposal
from .step4b4_mock_runner import recover_jsonl


def _canonical(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False).encode("ascii")


def sha256(value) -> str:
    return hashlib.sha256(value if isinstance(value, bytes) else _canonical(value)).hexdigest()


COHORT_SETTINGS = {"contract":"step4c1-cohort-v1","population":"P|strict-Q-common",
    "task":"indirect-only","budget":1,"gamma":1,"policies":["Task-Focused","ID-ordered Global"],
    "types":["FN","FP","REV"],"type_weight":"1/3 each","observations":512,
    "coefficient_abs":[0.25,0.8],"sign":"independent fair by sorted edge ID",
    "noise_sd":[0.8,1.2],"disturbance":"independent centered Gaussian",
    "delta":"alternating +/-1 after eligible admission, per cohort"}
COHORT_SETTINGS_SHA256 = sha256(COHORT_SETTINGS)
EXPECTED_TASK_GENERATION_REJECTIONS = frozenset({
    "no_indirect_only_task", "no_distinct_indirect_task",
})
EXPECTED_STRUCTURAL_REJECTIONS = frozenset({
    "task_not_indirect_only", "task_has_direct_edge",
    "missing_same_type_two_candidate_support",
})
EXPECTED_PROPOSAL_REJECTIONS = (EXPECTED_TASK_GENERATION_REJECTIONS
                                | EXPECTED_STRUCTURAL_REJECTIONS)


@contextmanager
def _cohort_process_lock(path: Path):
    """OS-released exclusive lock prevents two orchestrators running one cohort."""
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = path.open("a+b")
    try:
        handle.seek(0, 2)
        if handle.tell() == 0:
            handle.write(b"0")
            handle.flush()
        handle.seek(0)
        if __import__("os").name == "nt":
            import msvcrt
            try:
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError as exc:
                raise RegistryConflict("cohort already has an active orchestrator") from exc
        else:
            import fcntl
            try:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError as exc:
                raise RegistryConflict("cohort already has an active orchestrator") from exc
        yield
    finally:
        try:
            handle.seek(0)
            if __import__("os").name == "nt":
                import msvcrt
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        except OSError:
            pass
        handle.close()


class RegistryConflict(ValueError):
    """An immutable admission binding or registry transition conflicts."""


class ProposalGenerationError(RuntimeError):
    """Unexpected proposal software failure, durably recorded and fail-closed."""


class CohortStorageLimit(OSError):
    """Managed cohort output or available disk space reached its configured cap."""


class CohortStorageMonitor:
    """Measure all files under one dedicated run root before each write."""
    SQLITE_WRITE_RESERVE_BYTES = 16 * 1024

    def __init__(self, root: Path, *, max_bytes: int | None,
                 failure_reserve_bytes: int = 0, minimum_free_bytes: int = 0):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        if max_bytes is not None and max_bytes <= 0:
            raise ValueError("cohort storage cap must be positive")
        if failure_reserve_bytes < 0 or minimum_free_bytes < 0:
            raise ValueError("storage reserves cannot be negative")
        if max_bytes is not None and failure_reserve_bytes >= max_bytes:
            raise ValueError("failure reserve must be smaller than the cohort cap")
        self.max_bytes = max_bytes
        self.failure_reserve_bytes = failure_reserve_bytes
        self.minimum_free_bytes = minimum_free_bytes

    def usage_bytes(self) -> int:
        return sum(p.stat().st_size for p in self.root.rglob("*")
                   if p.is_file() and not p.is_symlink())

    def check_write(self, additional_bytes: int, *, emergency: bool = False) -> None:
        if additional_bytes < 0:
            raise ValueError("additional storage bytes cannot be negative")
        used = self.usage_bytes()
        reserve = 0 if emergency else self.failure_reserve_bytes
        if self.max_bytes is not None and used + additional_bytes + reserve > self.max_bytes:
            raise CohortStorageLimit(
                f"cohort storage cap: used={used}, next={additional_bytes}, "
                f"failure_reserve={reserve}, cap={self.max_bytes}"
            )
        free = shutil.disk_usage(self.root).free
        required = additional_bytes + (0 if emergency else self.minimum_free_bytes)
        if free < required:
            raise CohortStorageLimit(
                f"filesystem free space insufficient: free={free}, required={required}"
            )

    def before_ledger_event(self, _path: Path, event: dict, line_bytes: int) -> None:
        emergency = event.get("event") == "terminal" and event.get("status") != "OK"
        self.check_write(line_bytes, emergency=emergency)


class CohortRegistry:
    """SQLite-backed, transactionally serialized proposal/SCM registry."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self.storage_monitor: CohortStorageMonitor | None = None
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self._connect()) as db:
            # Serialize first-time schema creation with SQLite's writer lock.
            # executescript() implicitly commits and PRAGMA journal_mode can
            # raise SQLITE_BUSY when two fresh processes open an empty registry
            # together, despite busy_timeout. Keep DDL in one explicit txn.
            db.execute("BEGIN IMMEDIATE")
            try:
                db.execute("""CREATE TABLE IF NOT EXISTS proposals (
                    cohort TEXT NOT NULL, proposal_id TEXT NOT NULL, attempt INTEGER NOT NULL,
                    scm_id TEXT UNIQUE, topology_hash TEXT NOT NULL,
                    equation_signature_sha256 TEXT, rng_binding TEXT NOT NULL, rng_key TEXT NOT NULL,
                    config_sha256 TEXT NOT NULL, input_sha256 TEXT NOT NULL,
                    delta INTEGER, status TEXT NOT NULL, reason TEXT,
                    ledger_path TEXT, accepted_ordinal INTEGER,
                    created_at REAL NOT NULL, updated_at REAL NOT NULL,
                    PRIMARY KEY (cohort, proposal_id, attempt)
                )""")
                db.execute("""CREATE UNIQUE INDEX IF NOT EXISTS equation_signature_unique
                    ON proposals(equation_signature_sha256)
                    WHERE equation_signature_sha256 IS NOT NULL;
                """)
                db.execute("""CREATE TABLE IF NOT EXISTS cohorts (
                    cohort TEXT PRIMARY KEY, master_seed INTEGER NOT NULL,
                    target_eligible INTEGER NOT NULL, proposal_cap INTEGER NOT NULL,
                    settings_sha256 TEXT NOT NULL, created_at REAL NOT NULL
                )""")
                db.commit()
            except BaseException:
                db.rollback()
                raise

    def _connect(self):
        db = sqlite3.connect(self.path, timeout=30, isolation_level=None)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA busy_timeout=30000")
        return db

    def set_storage_monitor(self, monitor: CohortStorageMonitor | None) -> None:
        if monitor is not None:
            for path in (self.path.resolve(),):
                if not path.is_relative_to(monitor.root):
                    raise ValueError("registry path must be inside the managed cohort storage root")
        self.storage_monitor = monitor

    def _before_registry_write(self, *, emergency: bool = False) -> None:
        if self.storage_monitor is not None:
            self.storage_monitor.check_write(
                CohortStorageMonitor.SQLITE_WRITE_RESERVE_BYTES, emergency=emergency
            )

    def record_rejection(self, proposal: Mapping, config_sha256: str) -> dict:
        if proposal.get("accepted"):
            raise ValueError("accepted proposal cannot be recorded as rejected")
        return self._admit(proposal, config_sha256, None, None)

    def record_generator_error(self, *, cohort: str, master_seed: int,
                               proposal_id: str, attempt: int,
                               config_sha256: str, exception_type: str,
                               message: str) -> dict:
        """Persist a fatal proposal-builder error without calling it Q rejection."""
        proposal = {
            "cohort": cohort, "master_seed": master_seed,
            "proposal_id": proposal_id, "attempt": attempt,
            "accepted": False, "scm_id": None,
            "topology_hash": sha256({"proposal_id": proposal_id,
                                      "master_seed": master_seed,
                                      "attempt": attempt,
                                      "generator_error": exception_type}),
            "reason": f"GENERATOR_ERROR:{exception_type}:{message[:500]}",
        }
        return self._admit(proposal, config_sha256, None, None,
                           forced_status="generator_error")

    def admit(self, proposal: Mapping, config_sha256: str, ledger_path: Path) -> dict:
        if not proposal.get("accepted") or not proposal.get("scm_id"):
            raise ValueError("only structurally eligible proposals receive an SCM ID")
        return self._admit(proposal, config_sha256, str(Path(ledger_path).resolve()),
                           str(proposal["scm_id"]))

    def _admit(self, proposal, config_sha256, ledger_path, scm_id, forced_status=None):
        cohort, pid, attempt = proposal["cohort"], proposal["proposal_id"], proposal["attempt"]
        if cohort not in {"development", "confirmation"}:
            raise ValueError("invalid cohort")
        topology_hash = proposal["topology_hash"]
        rng_binding = sha256({"master_seed": proposal["master_seed"], "cohort": cohort,
                              "proposal_id": pid, "attempt": attempt,
                              "post_eligibility_rng_seeds": proposal.get("post_eligibility_rng_seeds")})
        rng_key = f"{cohort}:{proposal['master_seed']}:{pid}:{attempt}"
        # Matches run_eligible_proposal's immutable pipeline input binding.
        input_sha = sha256({"proposal": proposal})
        now = time.time()
        with closing(self._connect()) as db:
            self._before_registry_write(emergency=forced_status == "generator_error")
            db.execute("BEGIN IMMEDIATE")
            old = db.execute("SELECT * FROM proposals WHERE cohort=? AND proposal_id=? AND attempt=?",
                             (cohort, pid, attempt)).fetchone()
            if old:
                expected = (old["topology_hash"], old["rng_binding"], old["rng_key"],
                            old["input_sha256"], old["scm_id"])
                actual = (topology_hash, rng_binding, rng_key, input_sha, scm_id if scm_id is not None else None)
                # Replayed rejections remain null-ID; admitted rows must retain their ID.
                if expected != actual or (config_sha256 != "unbound" and old["config_sha256"] != config_sha256):
                    raise RegistryConflict("proposal replay has different topology/config/input/SCM binding")
                db.commit()
                return dict(old) | {"replayed": True}
            ordinal = None
            delta = None
            reason = str(proposal.get("reason", ""))
            if forced_status:
                status = forced_status
            elif reason.startswith(("TOPOLOGY_FAIL:", "TASK_FAIL:")) or reason in EXPECTED_TASK_GENERATION_REJECTIONS:
                status = "proposal_failed"
            else:
                status = "structural_rejected"
            if scm_id is not None:
                if db.execute("SELECT 1 FROM proposals WHERE scm_id=?", (scm_id,)).fetchone():
                    raise RegistryConflict("SCM ID already belongs to another proposal")
                ordinal = db.execute("SELECT COUNT(*) FROM proposals WHERE cohort=? AND scm_id IS NOT NULL",
                                     (cohort,)).fetchone()[0]
                # Alternate within each cohort; imbalance can never exceed one.
                delta = 1 if ordinal % 2 == 0 else -1
                status = "accepted"
            db.execute("""INSERT INTO proposals
                (cohort,proposal_id,attempt,scm_id,topology_hash,rng_binding,rng_key,config_sha256,input_sha256,
                 delta,status,reason,ledger_path,accepted_ordinal,created_at,updated_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (cohort,pid,attempt,scm_id,topology_hash,rng_binding,rng_key,config_sha256,input_sha,
                 delta,status,proposal.get("reason"),ledger_path,ordinal,now,now))
            row = db.execute("SELECT * FROM proposals WHERE cohort=? AND proposal_id=? AND attempt=?",
                             (cohort,pid,attempt)).fetchone()
            db.commit()
            return dict(row) | {"replayed": False}

    def bind_equation_signature(self, cohort: str, proposal_id: str, attempt: int,
                                 signature: str) -> None:
        with closing(self._connect()) as db:
            self._before_registry_write()
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT * FROM proposals WHERE cohort=? AND proposal_id=? AND attempt=?",
                             (cohort, proposal_id, attempt)).fetchone()
            if not row or row["scm_id"] is None:
                raise RegistryConflict("equation signature requires an admitted SCM")
            if row["equation_signature_sha256"]:
                if row["equation_signature_sha256"] != signature:
                    raise RegistryConflict("equation signature changed on replay")
            else:
                try:
                    db.execute("UPDATE proposals SET equation_signature_sha256=?,updated_at=? WHERE cohort=? AND proposal_id=? AND attempt=?",
                               (signature,time.time(),cohort,proposal_id,attempt))
                except sqlite3.IntegrityError as exc:
                    raise RegistryConflict("identical equation signature is already registered to another SCM") from exc
            db.commit()

    def bind_execution(self, cohort: str, proposal_id: str, attempt: int,
                       config_sha256: str, input_sha256: str,
                       initial_input_sha256: str | None = None) -> None:
        """Bind the final delta-specific runner config before any stage runs."""
        with closing(self._connect()) as db:
            self._before_registry_write()
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT config_sha256,input_sha256,status FROM proposals WHERE cohort=? AND proposal_id=? AND attempt=?",
                             (cohort,proposal_id,attempt)).fetchone()
            cohort_row=db.execute("SELECT settings_sha256 FROM cohorts WHERE cohort=?",(cohort,)).fetchone()
            if not row:
                raise RegistryConflict("execution binding has no admission")
            if row["status"] not in {"accepted","running"}:
                raise RegistryConflict("execution binding cannot change after terminal status")
            allowed_config={config_sha256}
            if cohort_row:
                allowed_config.add(cohort_row["settings_sha256"])
            allowed_config.add("unbound")
            if row["config_sha256"] not in allowed_config:
                raise RegistryConflict("execution config changed on replay")
            if row["input_sha256"] not in {input_sha256, initial_input_sha256}:
                raise RegistryConflict("execution input changed on replay")
            db.execute("UPDATE proposals SET config_sha256=?,input_sha256=?,updated_at=? WHERE cohort=? AND proposal_id=? AND attempt=?",
                       (config_sha256,input_sha256,time.time(),cohort,proposal_id,attempt))
            db.commit()

    def transition(self, cohort: str, proposal_id: str, attempt: int,
                   status: str, reason: str | None = None) -> None:
        allowed = {"accepted": {"running", "failed"}, "running": {"running", "completed", "failed"},
                   "failed": {"failed"}, "completed": {"completed"}}
        with closing(self._connect()) as db:
            self._before_registry_write(emergency=status == "failed")
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT status FROM proposals WHERE cohort=? AND proposal_id=? AND attempt=?",
                             (cohort,proposal_id,attempt)).fetchone()
            if not row or status not in allowed.get(row["status"], set()):
                raise RegistryConflict(f"invalid registry transition to {status}")
            db.execute("UPDATE proposals SET status=?,reason=?,updated_at=? WHERE cohort=? AND proposal_id=? AND attempt=?",
                       (status,reason,time.time(),cohort,proposal_id,attempt))
            db.commit()

    def rows(self, cohort: str | None = None) -> list[dict]:
        with closing(self._connect()) as db:
            query = "SELECT * FROM proposals" + (" WHERE cohort=?" if cohort else "") + " ORDER BY created_at,proposal_id"
            return [dict(row) for row in db.execute(query, (cohort,) if cohort else ())]

    def bind_cohort(self, cohort: str, master_seed: int, target: int,
                    proposal_cap: int, settings_sha256: str) -> None:
        if cohort not in {"development","confirmation"} or type(master_seed) is not int or master_seed < 0:
            raise ValueError("invalid cohort binding")
        with closing(self._connect()) as db:
            self._before_registry_write()
            db.execute("BEGIN IMMEDIATE")
            old=db.execute("SELECT * FROM cohorts WHERE cohort=?",(cohort,)).fetchone()
            binding=(master_seed,target,proposal_cap,settings_sha256)
            if old:
                actual=(old["master_seed"],old["target_eligible"],old["proposal_cap"],old["settings_sha256"])
                if actual != binding:
                    raise RegistryConflict("cohort restart changed master seed, target, cap, or settings hash")
            else:
                db.execute("INSERT INTO cohorts VALUES (?,?,?,?,?,?)",
                    (cohort,master_seed,target,proposal_cap,settings_sha256,time.time()))
            db.commit()

    def reconcile(self, cohort: str) -> dict:
        """Recover the SQLite/JSONL commit window without inventing completion."""
        repaired = []
        for row in self.rows(cohort):
            if row["scm_id"] is None:
                continue
            ledger = Path(row["ledger_path"])
            if not ledger.exists():
                if row["status"] == "completed":
                    raise RegistryConflict("registry says completed but bound ledger is missing")
                continue  # admitted but no ledger: deterministic same-key replay is safe
            events = recover_jsonl(ledger)
            bound = [event for event in events if event.get("scm_id") == row["scm_id"]
                     and event.get("cohort") == cohort]
            if any(event.get("config_sha256") != row["config_sha256"]
                   or event.get("input_sha256") != row["input_sha256"] for event in bound):
                raise RegistryConflict("ledger binding differs from registry")
            if any(event.get("rng_key") != row["rng_key"] for event in bound):
                raise RegistryConflict("ledger RNG key differs from registry")
            terminal = next((event for event in reversed(bound) if event.get("event") == "terminal"), None)
            if terminal and terminal.get("status") == "OK":
                if row["status"] == "failed" and row["reason"] == "DUPLICATE_SCM":
                    continue
                composite = next((event for event in bound if event.get("event") == "stage:composite"
                                  and event.get("status") == "OK"), None)
                output = composite.get("output", {}) if composite else {}
                if ("composite" not in terminal.get("completed_stages", [])
                        or output.get("complete") is not True
                        or output.get("gt_evaluation_performed") is not True):
                    raise RegistryConflict("successful terminal lacks a complete analytic-GT composite")
                if row["equation_signature_sha256"] is None:
                    signature = next((event.get("output", {}).get("equation_signature_sha256")
                                      for event in bound if event.get("event") == "stage:scm"
                                      and event.get("status") == "OK"), None)
                    if not signature:
                        raise RegistryConflict("successful ledger lacks equation signature")
                    try:
                        self.bind_equation_signature(cohort,row["proposal_id"],row["attempt"],signature)
                    except RegistryConflict:
                        self.transition(cohort,row["proposal_id"],row["attempt"],"failed","DUPLICATE_SCM")
                        repaired.append(row["scm_id"])
                        continue
                if row["status"] != "completed":
                    self.transition(cohort,row["proposal_id"],row["attempt"],"completed")
                    repaired.append(row["scm_id"])
            elif terminal and terminal.get("status") != "OK" and row["status"] not in {"failed","completed"}:
                self.transition(cohort,row["proposal_id"],row["attempt"],"failed",terminal["status"])
                repaired.append(row["scm_id"])
            elif row["status"] == "completed":
                raise RegistryConflict("registry completion has no successful terminal ledger event")
        return {"repaired": repaired}

    def counts(self, cohort: str) -> dict:
        rows = self.rows(cohort)
        stage_status = {row["scm_id"]: set() for row in rows if row["scm_id"]}
        for row in rows:
            if not row["scm_id"] or not row["ledger_path"] or not Path(row["ledger_path"]).exists():
                continue
            for event in recover_jsonl(Path(row["ledger_path"])):
                if event.get("scm_id") == row["scm_id"] and event.get("cohort") == cohort:
                    if event.get("status") == "OK":
                        stage_status[row["scm_id"]].add(event.get("event"))
        admitted = sum(row["scm_id"] is not None for row in rows)
        complete = sum(row["status"] == "completed" for row in rows)
        return {
            "topology_proposals": len(rows),
            "topology_or_task_generation_failures": sum(row["status"] == "proposal_failed" for row in rows),
            "unexpected_generator_errors": sum(
                row["status"] == "generator_error"
                or str(row.get("reason") or "").startswith("GENERATOR_ERROR:")
                for row in rows),
            "q_common_structural_rejections": sum(row["status"] == "structural_rejected" for row in rows),
            "q_common_structurally_eligible": sum(row["scm_id"] is not None for row in rows),
            "registry_accepted": admitted,
            "scm_parameter_generation_success": sum(bool(row["equation_signature_sha256"]) for row in rows),
            "shared_observation_generation_success": sum("stage:observations" in stage_status.get(row["scm_id"],set()) for row in rows if row["scm_id"]),
            "scm_generation_success": sum(bool(row["equation_signature_sha256"]) for row in rows),
            "three_type_evaluation_complete": complete,
            "missing_or_failed": sum(row["status"] == "failed" for row in rows),
            "incomplete_or_failed": admitted-complete,
            "composite_available": complete,
            "delta_counts": {str(delta): sum(row["delta"] == delta for row in rows if row["scm_id"])
                             for delta in (-1, 1)},
        }

    def active_stage_seconds(self, cohort: str) -> float:
        """Sum durable stage wall-time across all cohort ledgers."""
        total = 0.0
        for row in self.rows(cohort):
            if not row["ledger_path"] or not Path(row["ledger_path"]).exists():
                continue
            for event in recover_jsonl(Path(row["ledger_path"])):
                if event.get("cohort") == cohort and str(event.get("event", "")).startswith("stage:"):
                    value = event.get("elapsed_seconds", 0.0)
                    if not isinstance(value,(int,float)) or value < 0:
                        raise RegistryConflict("invalid stage timing in bound cohort ledger")
                    total += float(value)
        return total


@dataclass(frozen=True)
class CohortLimits:
    cohort: str
    target_eligible: int
    proposal_cap: int

    @classmethod
    def active(cls, cohort: str):
        return cls(cohort, ELIGIBLE_TARGETS[cohort], ATTEMPT_CAPS[cohort])


def _run_cohort_locked(*, cohort: str, master_seed: int, registry: CohortRegistry,
               ledger_dir: Path, config_sha256: str = COHORT_SETTINGS_SHA256,
               proposal_builder: Callable[..., Mapping] = build_structural_proposal,
               proposal_runner: Callable[[Mapping, Path, int], Mapping] | None = None,
               execution_binding_fn: Callable[[Mapping, int], tuple] | None = None,
               target_eligible: int | None = None, proposal_cap: int | None = None,
               resource_cap_seconds: float | None = None,
               storage_monitor: CohortStorageMonitor | None = None) -> dict:
    """Run a deterministic candidate sequence; fixture tests pass a small cap.

    Eligible SCMs are counted at atomic registry admission after strict
    structural eligibility. Later pipeline failures are retained and never
    silently replaced. Thus completed composite N can be below eligible N.
    """
    limits = CohortLimits.active(cohort)
    target = limits.target_eligible if target_eligible is None else target_eligible
    cap = limits.proposal_cap if proposal_cap is None else proposal_cap
    if not (0 < target <= limits.target_eligible and 0 < cap <= limits.proposal_cap):
        raise ValueError("fixture/production run cannot exceed active target or proposal cap")
    ledger_dir = Path(ledger_dir).resolve()
    if storage_monitor is not None:
        if not ledger_dir.is_relative_to(storage_monitor.root):
            raise ValueError("ledger directory must be inside the managed cohort storage root")
        registry.set_storage_monitor(storage_monitor)
        storage_monitor.check_write(CohortStorageMonitor.SQLITE_WRITE_RESERVE_BYTES)
        config_sha256 = sha256({"base_cohort_config_sha256": config_sha256,
            "cohort_storage_contract": {
                "max_cohort_storage_bytes": storage_monitor.max_bytes,
                "failure_reserve_bytes": storage_monitor.failure_reserve_bytes,
                "minimum_free_disk_bytes": storage_monitor.minimum_free_bytes,
                "per_ledger_default_bytes": 100 * 1024 * 1024,
            }})
    registry.bind_cohort(cohort,master_seed,target,cap,config_sha256)
    start = time.monotonic()
    ledger_dir = Path(ledger_dir)
    starting_stage_seconds = registry.active_stage_seconds(cohort)
    def cumulative_seconds():
        # Resource stop uses durable prior-stage wall time plus this invocation;
        # after restart, checkpointed stage durations become the new baseline.
        return starting_stage_seconds + (time.monotonic() - start)
    if proposal_runner is None:
        from .step4c1_pipeline import run_eligible_proposal
        proposal_runner = lambda proposal, ledger, delta: run_eligible_proposal(
            proposal, ledger, delta=delta,
            pre_write_guard=(storage_monitor.before_ledger_event if storage_monitor else None))
    if execution_binding_fn is None:
        from .step4c1_pipeline import execution_binding
        execution_binding_fn = execution_binding
    registry.reconcile(cohort)
    rows = registry.rows(cohort)
    fatal = next((row for row in rows
                  if row["status"] == "generator_error"
                  or str(row.get("reason") or "").startswith("GENERATOR_ERROR:")), None)
    if fatal:
        raise ProposalGenerationError(
            f"cohort stopped at persisted generator error {fatal['proposal_id']} "
            f"attempt={fatal['attempt']}: {fatal['reason']}"
        )
    seen = {row["proposal_id"] for row in rows}

    def valid_proposal_record(proposal, proposal_id):
        try:
            if not isinstance(proposal, Mapping):
                return False
            common = (proposal.get("cohort") == cohort
                      and proposal.get("master_seed") == master_seed
                      and proposal.get("proposal_id") == proposal_id
                      and type(proposal.get("attempt")) is int
                      and proposal.get("attempt") == 0
                      and type(proposal.get("accepted")) is bool
                      and isinstance(proposal.get("topology_hash"), str)
                      and bool(proposal.get("topology_hash")))
            if not common:
                return False
            if proposal["accepted"]:
                return isinstance(proposal.get("scm_id"), str) and bool(proposal.get("scm_id"))
            return (proposal.get("scm_id") is None
                    and proposal.get("reason") in EXPECTED_PROPOSAL_REJECTIONS)
        except Exception:
            return False

    def execute_admitted(row):
        try:
            proposal = proposal_builder(cohort=cohort, master_seed=master_seed,
                                        proposal_id=row["proposal_id"], attempt=row["attempt"])
        except Exception as exc:
            reason = f"GENERATOR_ERROR:{type(exc).__name__}:{str(exc)[:500]}"
            registry.transition(cohort,row["proposal_id"],row["attempt"],"failed",reason)
            raise ProposalGenerationError(
                f"admitted proposal regeneration failed at {row['proposal_id']}: {reason}"
            ) from exc
        if (not valid_proposal_record(proposal, row["proposal_id"])
                or not proposal.get("accepted") or proposal.get("scm_id") != row["scm_id"]):
            reason = "GENERATOR_ERROR:ProposalReplayMismatch:admitted proposal no longer reproduces its registered binding"
            registry.transition(cohort,row["proposal_id"],row["attempt"],"failed",reason)
            raise ProposalGenerationError(reason)
        config, cfg_sha, input_sha = execution_binding_fn(proposal, row["delta"])
        registry.bind_execution(cohort,row["proposal_id"],row["attempt"],cfg_sha,input_sha,
                                sha256({"proposal":proposal}))
        registry.transition(cohort,row["proposal_id"],row["attempt"],"running")
        outcome = proposal_runner(proposal, Path(row["ledger_path"]), row["delta"])
        signature = outcome.get("equation_signature_sha256") if isinstance(outcome, Mapping) else None
        target_ledger = Path(row["ledger_path"])
        if signature is None and target_ledger.exists():
            for event in recover_jsonl(target_ledger):
                if event.get("event") == "stage:scm" and event.get("status") == "OK":
                    signature = event.get("output", {}).get("equation_signature_sha256")
                    break
        if signature:
            try:
                registry.bind_equation_signature(cohort,row["proposal_id"],row["attempt"],signature)
            except RegistryConflict as exc:
                registry.transition(cohort,row["proposal_id"],row["attempt"],"failed","DUPLICATE_SCM")
                return {"status":"DUPLICATE_SCM","reason":str(exc)}
        status = outcome.get("status") if isinstance(outcome, Mapping) else None
        if status == "OK":
            registry.reconcile(cohort)
            final = next(item for item in registry.rows(cohort)
                         if item["proposal_id"] == row["proposal_id"] and item["attempt"] == row["attempt"])
            if final["status"] != "completed":
                raise RegistryConflict("runner returned OK without a complete bound composite ledger")
        elif status:
            registry.transition(cohort,row["proposal_id"],row["attempt"],"failed",str(status))
        return outcome

    # An admission without a terminal registry state is resumed before new proposals.
    for existing in rows:
        if existing["scm_id"] is not None and existing["status"] in {"accepted","running"}:
            if resource_cap_seconds is not None and cumulative_seconds() >= resource_cap_seconds:
                break
            execute_admitted(existing)
    next_index = 0
    storage_cap_reached = False
    while f"{cohort}-proposal-{next_index:06d}" in seen:
        next_index += 1
    while registry.counts(cohort)["registry_accepted"] < target and len(registry.rows(cohort)) < cap:
        if resource_cap_seconds is not None and cumulative_seconds() >= resource_cap_seconds:
            break
        if storage_monitor is not None:
            try:
                # Leave room for a registry transaction and emergency terminal record.
                storage_monitor.check_write(CohortStorageMonitor.SQLITE_WRITE_RESERVE_BYTES)
            except CohortStorageLimit:
                storage_cap_reached = True
                break
        proposal_id = f"{cohort}-proposal-{next_index:06d}"
        try:
            proposal = proposal_builder(cohort=cohort, master_seed=master_seed,
                                        proposal_id=proposal_id, attempt=0)
        except Exception as exc:
            registry.record_generator_error(cohort=cohort,master_seed=master_seed,
                proposal_id=proposal_id,attempt=0,config_sha256=config_sha256,
                exception_type=type(exc).__name__,message=str(exc))
            raise ProposalGenerationError(
                f"proposal builder failed at {proposal_id} attempt=0: "
                f"{type(exc).__name__}: {str(exc)[:500]}"
            ) from exc
        if not valid_proposal_record(proposal,proposal_id):
            detail = "builder returned malformed or misbound proposal record"
            registry.record_generator_error(cohort=cohort,master_seed=master_seed,
                proposal_id=proposal_id,attempt=0,config_sha256=config_sha256,
                exception_type="InvalidProposalRecord",message=detail)
            raise ProposalGenerationError(f"{proposal_id}: {detail}")
        if proposal.get("accepted"):
            scm_id = proposal.get("scm_id")
            ledger = ledger_dir / f"{scm_id}.jsonl"
            row = registry.admit(proposal, config_sha256, ledger)
            if row["status"] in {"accepted","running"}:
                execute_admitted(row)
        else:
            registry.record_rejection(proposal, config_sha256)
        next_index += 1
        seen.add(proposal_id)
    counts = registry.counts(cohort)
    rows = registry.rows(cohort)
    return {"cohort": cohort, "target_eligible": target, "proposal_cap": cap,
            "shortfall_eligible": max(0,target-counts["registry_accepted"]),
            "cap_reached": len(rows) >= cap,
            "resource_cap_reached": resource_cap_seconds is not None and cumulative_seconds() >= resource_cap_seconds,
            "storage_cap_reached": storage_cap_reached,
            "cumulative_active_stage_seconds": registry.active_stage_seconds(cohort),
            "current_invocation_elapsed_seconds": time.monotonic()-start,
            "cohort_storage_bytes": storage_monitor.usage_bytes() if storage_monitor else None,
            "counts": counts, "accepted_scm_ids": [row["scm_id"] for row in rows if row["scm_id"]],
            "proposal_ids": [row["proposal_id"] for row in rows]}


def run_cohort(*, cohort: str, master_seed: int, registry: CohortRegistry,
               ledger_dir: Path, config_sha256: str = COHORT_SETTINGS_SHA256,
               proposal_builder: Callable[..., Mapping] = build_structural_proposal,
               proposal_runner: Callable[[Mapping, Path, int], Mapping] | None = None,
               execution_binding_fn: Callable[[Mapping, int], tuple] | None = None,
               target_eligible: int | None = None, proposal_cap: int | None = None,
               resource_cap_seconds: float | None = None,
               cohort_storage_root: Path | None = None,
               max_cohort_storage_bytes: int | None = None,
               failure_reserve_bytes: int = 0,
               minimum_free_disk_bytes: int = 0) -> dict:
    """Serialize cohort scheduling while allowing crash-safe OS lock release."""
    storage_monitor = None
    if max_cohort_storage_bytes is not None:
        if cohort_storage_root is None:
            raise ValueError("a dedicated cohort_storage_root is required with a cohort-wide cap")
        storage_monitor = CohortStorageMonitor(cohort_storage_root,
            max_bytes=max_cohort_storage_bytes,
            failure_reserve_bytes=failure_reserve_bytes,
            minimum_free_bytes=minimum_free_disk_bytes)
    lock = registry.path.with_suffix(registry.path.suffix + f".{cohort}.lock")
    with _cohort_process_lock(lock):
        return _run_cohort_locked(cohort=cohort,master_seed=master_seed,registry=registry,
            ledger_dir=ledger_dir,config_sha256=config_sha256,proposal_builder=proposal_builder,
            proposal_runner=proposal_runner,execution_binding_fn=execution_binding_fn,
            target_eligible=target_eligible,proposal_cap=proposal_cap,
            resource_cap_seconds=resource_cap_seconds,storage_monitor=storage_monitor)

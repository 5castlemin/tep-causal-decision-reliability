"""Durable multi-SCM orchestration for TEST_ONLY and approved Research C runs.

It stores each SCM's full shared single-SCM Runner output in one SQLite
transaction and replays interrupted work under the same configuration binding.
"""
from __future__ import annotations

import json
from functools import partial
import os
from pathlib import Path
import shutil
import sqlite3
import time

from .cohort_ledger_test_only import LedgerConflict, _run_lock, _subseed
from .runner import (ROOT, _canonical, _code_hashes, _digest, _git_revision,
                     _jsonable, _runtime_fingerprint, execute_fixture_input)
from .e2e_fixture import _RESEARCH_EXECUTION_CAPABILITY
from .execution_limits import (ResourceLimitStop, ResourceLimits, check_storage,
                              directory_usage_bytes, run_isolated)


def _compute_fixture_payload(factory, g0_seed, task_id, budgets, apply_g0_generator,
                             research_authorized=False):
    generation_started = time.monotonic()
    fixture, metadata = factory()
    generation_seconds = time.monotonic() - generation_started
    timing = {}
    payload = execute_fixture_input(fixture, metadata=metadata, g0_seed=g0_seed,
                                    task_id=task_id, budgets=budgets,
                                    apply_g0_generator=apply_g0_generator,
                                    _research_authorized=research_authorized,
                                    _timing_sink=timing)
    return payload, {"scm_observation_g0_generation_seconds": generation_seconds,
                     **timing}


class CohortIntegrityError(RuntimeError):
    pass


def _connect(db_path: Path):
    connection = sqlite3.connect(db_path, timeout=30, isolation_level=None)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA journal_mode=DELETE")
    connection.execute("PRAGMA synchronous=FULL")
    connection.execute("PRAGMA foreign_keys=ON")
    connection.execute("PRAGMA busy_timeout=30000")
    return connection


def _schema(connection):
    connection.executescript("""
    CREATE TABLE IF NOT EXISTS runs (
      run_id TEXT PRIMARY KEY, cohort_type TEXT NOT NULL,
      master_seed INTEGER NOT NULL, config_json TEXT NOT NULL,
      config_sha256 TEXT NOT NULL, code_json TEXT NOT NULL,
      source_json TEXT NOT NULL, created_at REAL NOT NULL,
      active_seconds REAL NOT NULL DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS scms (
      run_id TEXT NOT NULL, scm_id TEXT NOT NULL, ordinal INTEGER NOT NULL,
      status TEXT NOT NULL, rng_json TEXT NOT NULL, attempt_count INTEGER NOT NULL DEFAULT 0,
      input_sha256 TEXT, result_json TEXT, result_sha256 TEXT,
      failure_reason TEXT, retryable INTEGER NOT NULL DEFAULT 0,
      started_at REAL, completed_at REAL,
      active_seconds REAL NOT NULL DEFAULT 0, sampled_rss_peak_bytes INTEGER,
      failure_code TEXT, stage_timing_json TEXT,
      PRIMARY KEY (run_id, scm_id), UNIQUE (run_id, ordinal),
      FOREIGN KEY (run_id) REFERENCES runs(run_id)
    );
    CREATE TABLE IF NOT EXISTS events (
      event_id INTEGER PRIMARY KEY AUTOINCREMENT, run_id TEXT NOT NULL,
      scm_id TEXT, from_status TEXT, to_status TEXT NOT NULL,
      reason TEXT, created_at REAL NOT NULL,
      FOREIGN KEY (run_id) REFERENCES runs(run_id)
    );
    CREATE TABLE IF NOT EXISTS proposals (
      run_id TEXT NOT NULL, proposal_id TEXT NOT NULL, status TEXT NOT NULL,
      reason TEXT, topology_hash TEXT, scm_id TEXT, proposal_json TEXT NOT NULL,
      proposal_sha256 TEXT NOT NULL,
      PRIMARY KEY (run_id, proposal_id),
      FOREIGN KEY (run_id) REFERENCES runs(run_id)
    );
    """)
    # Additive migration for TEST_ONLY SQLite files created by the prior runner.
    for table, column, declaration in (
        ("runs", "active_seconds", "REAL NOT NULL DEFAULT 0"),
        ("scms", "active_seconds", "REAL NOT NULL DEFAULT 0"),
        ("scms", "sampled_rss_peak_bytes", "INTEGER"),
        ("scms", "failure_code", "TEXT"),
        ("scms", "stage_timing_json", "TEXT"),
    ):
        columns = {row[1] for row in connection.execute(f"PRAGMA table_info({table})")}
        if column not in columns:
            connection.execute(f"ALTER TABLE {table} ADD COLUMN {column} {declaration}")


def _proposal_schema(connection):
    """Keep proposal checkpoints in a compact, mode-separated SQLite ledger."""
    connection.executescript("""
    CREATE TABLE IF NOT EXISTS proposal_stage_runs (
      run_id TEXT PRIMARY KEY, cohort_type TEXT NOT NULL, master_seed INTEGER NOT NULL,
      target_admissions INTEGER NOT NULL, proposal_cap INTEGER NOT NULL,
      config_json TEXT NOT NULL, config_sha256 TEXT NOT NULL,
      status TEXT NOT NULL, active_seconds REAL NOT NULL DEFAULT 0,
      failure_code TEXT, failure_reason TEXT, created_at REAL NOT NULL,
      completed_at REAL
    );
    CREATE TABLE IF NOT EXISTS proposal_attempts (
      run_id TEXT NOT NULL, attempt INTEGER NOT NULL, proposal_id TEXT NOT NULL,
      status TEXT NOT NULL, rng_binding_json TEXT NOT NULL,
      proposal_json TEXT, proposal_sha256 TEXT,
      active_seconds REAL NOT NULL DEFAULT 0, sampled_rss_peak_bytes INTEGER,
      failure_code TEXT, failure_reason TEXT,
      started_at REAL, completed_at REAL,
      PRIMARY KEY (run_id, attempt), UNIQUE (run_id, proposal_id),
      FOREIGN KEY (run_id) REFERENCES proposal_stage_runs(run_id)
    );
    """)


def _event(connection, run_id, scm_id, old, new, reason=None):
    connection.execute(
        "INSERT INTO events(run_id,scm_id,from_status,to_status,reason,created_at) VALUES(?,?,?,?,?,?)",
        (run_id, scm_id, old, new, reason, time.time()))


def _fixture_spec(value):
    if callable(value):
        return {"factory": value, "apply_g0_generator": True}
    if (isinstance(value, dict) and callable(value.get("factory"))
            and type(value.get("apply_g0_generator", True)) is bool):
        return {"factory": value["factory"],
                "apply_g0_generator": value.get("apply_g0_generator", True)}
    raise TypeError("TEST_ONLY fixture mapping values must be factories or fixture specs")


def _verify_result(result_json: str, expected_sha: str,
                   expected_classification="TEST_ONLY_NOT_RESEARCH_COHORT") -> dict:
    try:
        wrapper = json.loads(result_json)
    except json.JSONDecodeError as exc:
        raise CohortIntegrityError("stored SCM result is not valid JSON") from exc
    payload = wrapper.get("payload")
    if not isinstance(payload, dict) or _digest(payload) != expected_sha:
        raise CohortIntegrityError("SCM result checksum mismatch")
    if wrapper.get("payload_sha256") != expected_sha:
        raise CohortIntegrityError("SCM result wrapper checksum mismatch")
    if payload.get("classification") != expected_classification:
        raise CohortIntegrityError("result classification does not match cohort store")
    return payload


def _build_proposal_worker(cohort, master_seed, proposal_id, attempt, proposal_builder=None):
    if proposal_builder is None:
        from research.budget_aware_refinement.step4c1_proposal import build_structural_proposal
        proposal_builder = build_structural_proposal
    return proposal_builder(cohort=cohort, master_seed=master_seed,
                            proposal_id=proposal_id, attempt=attempt)


def run_proposal_stage(output_root: Path, *, run_id: str, cohort_type: str,
                       master_seed: int, target_admissions: int, proposal_cap: int,
                       resource_limits: ResourceLimits,
                       _authorization=None, proposal_builder=None,
                       after_proposal_checkpoint_hook=None,
                       before_proposal_commit_hook=None) -> dict:
    """Generate/checkpoint proposals one isolated unit at a time before admission.

    Research execution requires the runner capability. TEST_ONLY calls use a
    separate namespace and ledger file; hooks are accepted only for tests.
    """
    if cohort_type not in {"TEST_ONLY", "development", "independent_evaluation"}:
        raise ValueError("unsupported proposal cohort type")
    research_mode = cohort_type != "TEST_ONLY"
    if research_mode:
        if _authorization is not _RESEARCH_EXECUTION_CAPABILITY:
            raise PermissionError("research proposal stage requires validated runner capability")
        if resource_limits.classification != "USER_APPROVED_RESEARCH_RESOURCE_PROFILE":
            raise PermissionError("research proposal stage requires approved resource profile")
    elif resource_limits.classification != "TEST_ONLY_RESOURCE_ENVELOPE":
        raise PermissionError("TEST_ONLY proposal stage requires TEST_ONLY resource limits")
    for hook in (after_proposal_checkpoint_hook, before_proposal_commit_hook):
        if hook is not None and getattr(hook, "__test_only_fixture_hook__", False) is not True:
            raise PermissionError("proposal-stage interruption hooks are TEST_ONLY only")
    if type(master_seed) is not int or master_seed < 0:
        raise ValueError("master_seed must be a nonnegative integer")
    if type(target_admissions) is not int or target_admissions <= 0:
        raise ValueError("target_admissions must be positive")
    if type(proposal_cap) is not int or proposal_cap < target_admissions:
        raise ValueError("proposal_cap must cover target_admissions")
    if not isinstance(run_id, str) or not run_id:
        raise ValueError("run_id is required")
    if (research_mode and not run_id.startswith(
            "development-" if cohort_type == "development" else "independent-evaluation-")):
        raise ValueError("research proposal run_id must be cohort-namespaced")
    if not research_mode and not run_id.startswith("test-only-"):
        raise PermissionError("TEST_ONLY proposal run_id must use test-only namespace")

    from research.budget_aware_refinement.step4c1_proposal import ATTEMPT_CAPS
    generator_cohort = {"TEST_ONLY": "development", "development": "development",
                        "independent_evaluation": "confirmation"}[cohort_type]
    if proposal_cap > ATTEMPT_CAPS[generator_cohort]:
        raise ValueError("proposal_cap exceeds generator attempt cap")
    code_hashes = _code_hashes(ROOT)
    builder_name = ("default" if proposal_builder is None else
                    f"{proposal_builder.__module__}.{proposal_builder.__qualname__}")
    binding = {"schema": "research-c-proposal-stage-v1", "run_id": run_id,
               "cohort_type": cohort_type, "master_seed": master_seed,
               "target_admissions": target_admissions, "proposal_cap": proposal_cap,
               "resource_limits": resource_limits.binding(), "builder": builder_name,
               "code_sha256": code_hashes, "source_revision": _git_revision(ROOT),
               "runtime_fingerprint": _runtime_fingerprint()}
    config_sha = _digest(binding)
    root = Path(output_root).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    db_name = ("research_c_proposal_stage.sqlite" if research_mode
               else "research_c_fixture_proposals.sqlite")
    db_path = root / db_name
    lock_path = root / f".{db_name}.lock"

    with _run_lock(lock_path):
        connection = _connect(db_path)
        try:
            _proposal_schema(connection)
            connection.execute("BEGIN IMMEDIATE")
            run = connection.execute(
                "SELECT * FROM proposal_stage_runs WHERE run_id=?", (run_id,)).fetchone()
            if run is None:
                connection.execute("""INSERT INTO proposal_stage_runs
                    (run_id,cohort_type,master_seed,target_admissions,proposal_cap,
                     config_json,config_sha256,status,created_at)
                    VALUES(?,?,?,?,?,?,?,?,?)""",
                    (run_id, cohort_type, master_seed, target_admissions, proposal_cap,
                     _canonical(binding).decode("ascii"), config_sha, "RUNNING", time.time()))
                connection.commit()
                active_seconds = 0.0
            else:
                stored_binding = json.loads(run["config_json"])
                changed = sorted(key for key, value in binding.items()
                                 if stored_binding.get(key) != value)
                if (run["config_sha256"] != config_sha or run["cohort_type"] != cohort_type
                        or run["master_seed"] != master_seed or changed):
                    raise LedgerConflict(
                        "proposal run ID is bound to different config/code/RNG; "
                        f"changed_binding_fields={changed or ['run metadata']}")
                active_seconds = float(run["active_seconds"])
                connection.commit()

            proposals, admitted_count = [], 0
            stop_reason = None
            for attempt in range(proposal_cap):
                proposal_id = f"{generator_cohort}-proposal-{attempt + 1:06d}"
                row = connection.execute(
                    "SELECT * FROM proposal_attempts WHERE run_id=? AND attempt=?",
                    (run_id, attempt)).fetchone()
                if row is not None and row["status"] in {"ELIGIBLE", "STRUCTURALLY_INELIGIBLE"}:
                    parsed = json.loads(row["proposal_json"])
                    if _digest(parsed) != row["proposal_sha256"]:
                        raise CohortIntegrityError("proposal checkpoint checksum mismatch")
                    proposals.append(parsed)
                    admitted_count += int(bool(parsed.get("accepted")))
                    if admitted_count >= target_admissions:
                        break
                    continue

                if row is not None and row["status"] == "RUNNING" and row["started_at"] is not None:
                    # Reconcile a coordinator interruption conservatively. The
                    # same proposal ID/attempt is retried; no later ID is drawn.
                    interrupted = max(0.0, time.time() - float(row["started_at"]))
                    active_seconds += interrupted
                if active_seconds >= resource_limits.cohort_active_seconds:
                    stop_reason = "COHORT_ACTIVE_TIME_CAP"
                    break
                try:
                    check_storage(root, next_bytes=16 * 1024, limits=resource_limits)
                except ResourceLimitStop as exc:
                    stop_reason = exc.code
                    break

                rng_binding = {"cohort": generator_cohort, "master_seed": master_seed,
                               "proposal_id": proposal_id, "attempt": attempt,
                               "stream_protocol": "step4-rng-v1"}
                connection.execute("BEGIN IMMEDIATE")
                if row is None:
                    connection.execute("""INSERT INTO proposal_attempts
                        (run_id,attempt,proposal_id,status,rng_binding_json,started_at)
                        VALUES(?,?,?,?,?,?)""",
                        (run_id, attempt, proposal_id, "RUNNING",
                         _canonical(rng_binding).decode("ascii"), time.time()))
                else:
                    connection.execute("""UPDATE proposal_attempts SET status='RUNNING',
                        failure_code=NULL,failure_reason=NULL,started_at=?,completed_at=NULL
                        WHERE run_id=? AND attempt=?""",
                        (time.time(), run_id, attempt))
                connection.commit()
                remaining = resource_limits.cohort_active_seconds - active_seconds
                timeout = min(resource_limits.unit_timeout_seconds, remaining)
                started = time.monotonic()
                try:
                    proposal, stop_code, elapsed, sampled_peak = run_isolated(
                        partial(_build_proposal_worker, generator_cohort, master_seed,
                                proposal_id, attempt, proposal_builder),
                        timeout_seconds=timeout,
                        rss_cap_bytes=resource_limits.sampled_rss_bytes)
                    elapsed = max(elapsed, time.monotonic() - started)
                    active_seconds += elapsed
                    if stop_code:
                        code = ("COHORT_ACTIVE_TIME_CAP" if timeout < resource_limits.unit_timeout_seconds
                                and remaining <= resource_limits.unit_timeout_seconds else stop_code)
                        reason = f"{code}: isolated proposal worker did not complete"
                        connection.execute("BEGIN IMMEDIATE")
                        connection.execute("""UPDATE proposal_attempts SET status='RESOURCE_LIMIT',
                            active_seconds=active_seconds+?,sampled_rss_peak_bytes=?,failure_code=?,
                            failure_reason=?,started_at=NULL,completed_at=? WHERE run_id=? AND attempt=?""",
                            (elapsed, sampled_peak, code, reason, time.time(), run_id, attempt))
                        connection.execute("""UPDATE proposal_stage_runs SET status='RESOURCE_STOP',
                            active_seconds=?,failure_code=?,failure_reason=? WHERE run_id=?""",
                            (active_seconds, code, reason, run_id))
                        connection.commit()
                        stop_reason = code
                        break
                    if not isinstance(proposal, dict) or proposal.get("proposal_id") != proposal_id:
                        raise CohortIntegrityError("proposal worker returned mismatched proposal identity")
                    if proposal.get("cohort") != generator_cohort or proposal.get("attempt") != attempt:
                        raise CohortIntegrityError("proposal worker returned mismatched RNG binding")
                    status = "ELIGIBLE" if proposal.get("accepted") else "STRUCTURALLY_INELIGIBLE"
                    proposal_json = _canonical(_jsonable(proposal)).decode("ascii")
                    proposal_sha = _digest(_jsonable(proposal))
                    if before_proposal_commit_hook is not None:
                        before_proposal_commit_hook(proposal_id)
                    encoded_bytes = len(proposal_json.encode("utf-8"))
                    if encoded_bytes > resource_limits.max_result_bytes:
                        raise ResourceLimitStop("PROPOSAL_BYTE_CAP", "proposal record exceeds result cap")
                    ledger_bytes = db_path.stat().st_size if db_path.exists() else 0
                    if ledger_bytes + encoded_bytes + 16 * 1024 > resource_limits.max_ledger_bytes:
                        raise ResourceLimitStop("LEDGER_BYTE_CAP", "proposal checkpoint exceeds ledger cap")
                    check_storage(root, next_bytes=encoded_bytes + 16 * 1024, limits=resource_limits)
                    connection.execute("BEGIN IMMEDIATE")
                    connection.execute("""UPDATE proposal_attempts SET status=?,proposal_json=?,
                        proposal_sha256=?,active_seconds=active_seconds+?,sampled_rss_peak_bytes=?,
                        failure_code=NULL,failure_reason=NULL,started_at=NULL,completed_at=?
                        WHERE run_id=? AND attempt=?""",
                        (status, proposal_json, proposal_sha, elapsed, sampled_peak,
                         time.time(), run_id, attempt))
                    connection.execute("""UPDATE proposal_stage_runs SET status='RUNNING',
                        active_seconds=?,failure_code=NULL,failure_reason=NULL WHERE run_id=?""",
                        (active_seconds, run_id))
                    connection.commit()
                    proposals.append(_jsonable(proposal))
                    admitted_count += int(bool(proposal.get("accepted")))
                    if after_proposal_checkpoint_hook is not None:
                        after_proposal_checkpoint_hook(proposal_id)
                    if admitted_count >= target_admissions:
                        break
                except Exception as exc:
                    elapsed = max(0.0, time.monotonic() - started)
                    active_seconds += elapsed
                    code = getattr(exc, "code", None) or type(exc).__name__
                    reason = f"{type(exc).__name__}:{str(exc)[:500]}"
                    if connection.in_transaction:
                        connection.rollback()
                    connection.execute("BEGIN IMMEDIATE")
                    connection.execute("""UPDATE proposal_attempts SET status='FAILED',
                        active_seconds=active_seconds+?,failure_code=?,failure_reason=?,
                        sampled_rss_peak_bytes=COALESCE(sampled_rss_peak_bytes,0),
                        started_at=NULL,completed_at=? WHERE run_id=? AND attempt=?""",
                        (elapsed, code, reason, time.time(), run_id, attempt))
                    connection.execute("""UPDATE proposal_stage_runs SET status='FAILED',
                        active_seconds=?,failure_code=?,failure_reason=? WHERE run_id=?""",
                        (active_seconds, code, reason, run_id))
                    connection.commit()
                    stop_reason = code
                    break

            complete = stop_reason is None
            if complete:
                shortfall = max(0, target_admissions - admitted_count)
                stage_status = "COMPLETED" if shortfall == 0 else "SHORTFALL_PROPOSAL_CAP"
                connection.execute("BEGIN IMMEDIATE")
                connection.execute("""UPDATE proposal_stage_runs SET status=?,active_seconds=?,
                    failure_code=NULL,failure_reason=NULL,completed_at=? WHERE run_id=?""",
                    (stage_status, active_seconds, time.time(), run_id))
                connection.commit()
            else:
                shortfall = max(0, target_admissions - admitted_count)
            records = []
            for row in connection.execute(
                    "SELECT * FROM proposal_attempts WHERE run_id=? ORDER BY attempt", (run_id,)):
                item = {"attempt": row["attempt"], "proposal_id": row["proposal_id"],
                        "status": row["status"], "rng_binding": json.loads(row["rng_binding_json"]),
                        "active_seconds": row["active_seconds"],
                        "sampled_rss_peak_bytes": row["sampled_rss_peak_bytes"],
                        "failure_code": row["failure_code"],
                        "failure_reason": row["failure_reason"]}
                if row["proposal_json"]:
                    proposal = json.loads(row["proposal_json"])
                    if _digest(proposal) != row["proposal_sha256"]:
                        raise CohortIntegrityError("proposal checkpoint checksum mismatch")
                    item["proposal"] = proposal
                records.append(item)
            persisted_proposals = [item["proposal"] for item in records if "proposal" in item]
            final_status = (stage_status if complete else
                            ("RESOURCE_STOP" if stop_reason and
                             ("CAP" in stop_reason or "LIMIT" in stop_reason)
                             else "INCOMPLETE"))
            return {"run_id": run_id, "cohort_type": cohort_type,
                    "proposal_stage_status": final_status,
                    "proposal_stage_complete": complete,
                    "proposal_active_seconds": active_seconds,
                    "proposal_count": len(persisted_proposals),
                    "eligible_count": admitted_count, "shortfall": shortfall,
                    "stop_reason": stop_reason, "proposals": persisted_proposals,
                    "proposal_checkpoints": records, "config_sha256": config_sha,
                    "database_path": str(db_path)}
        finally:
            connection.close()


def run_test_only_cohort(output_root: Path, *, run_id: str, master_seed: int,
                         fixtures: dict, budgets=(0, 1, 2, 3, 4),
                         max_new_scms: int | None = None,
                         proposal_outcomes: list[dict] | None = None,
                         resource_limits: ResourceLimits | None = None,
                         after_claim_hook=None, before_commit_hook=None) -> dict:
    """Run/recover a fixed-fixture SCM sequence; never samples a study SCM.

    Optional hooks exist only for actual subprocess termination tests and must
    carry the explicit ``__test_only_fixture_hook__`` marker.
    """
    return _run_cohort(output_root, run_id=run_id, master_seed=master_seed,
                       fixtures=fixtures, budgets=budgets, max_new_scms=max_new_scms,
                       proposal_outcomes=proposal_outcomes, resource_limits=resource_limits,
                       after_claim_hook=after_claim_hook, before_commit_hook=before_commit_hook,
                       cohort_type="TEST_ONLY_FIXTURE", research_authorized=False)


def run_approved_research_cohort(output_root: Path, *, run_id: str, master_seed: int,
                                 fixtures: dict, budgets=(0, 1, 2, 3, 4),
                                 proposal_outcomes: list[dict] | None = None,
                                 resource_limits: ResourceLimits,
                                 proposal_active_seconds: float = 0.0,
                                 _authorization=None) -> dict:
    """Research ledger path; callable only with the runner's post-gate capability."""
    if _authorization is not _RESEARCH_EXECUTION_CAPABILITY:
        raise PermissionError("research cohort execution requires validated runner capability")
    if resource_limits.classification != "USER_APPROVED_RESEARCH_RESOURCE_PROFILE":
        raise PermissionError("research cohort requires a research-classified resource profile")
    return _run_cohort(output_root, run_id=run_id, master_seed=master_seed,
                       fixtures=fixtures, budgets=budgets, max_new_scms=None,
                       proposal_outcomes=proposal_outcomes, resource_limits=resource_limits,
                       after_claim_hook=None, before_commit_hook=None,
                       cohort_type="RESEARCH_COHORT", research_authorized=True,
                       initial_active_seconds=proposal_active_seconds)


def _run_cohort(output_root: Path, *, run_id: str, master_seed: int,
                fixtures: dict, budgets=(0, 1, 2, 3, 4),
                max_new_scms: int | None = None,
                proposal_outcomes: list[dict] | None = None,
                resource_limits: ResourceLimits | None = None,
                after_claim_hook=None, before_commit_hook=None,
                cohort_type="TEST_ONLY_FIXTURE", research_authorized=False,
                initial_active_seconds: float = 0.0) -> dict:
    if cohort_type not in {"TEST_ONLY_FIXTURE", "RESEARCH_COHORT"}:
        raise ValueError("invalid cohort type")
    if cohort_type == "RESEARCH_COHORT" and not research_authorized:
        raise PermissionError("research cohort requires validated runner capability")
    if cohort_type == "TEST_ONLY_FIXTURE" and resource_limits is not None and resource_limits.classification != "TEST_ONLY_RESOURCE_ENVELOPE":
        raise PermissionError("TEST_ONLY runner requires TEST_ONLY resource limits")
    if not isinstance(run_id, str) or not run_id or len(run_id) > 100:
        raise ValueError("run_id must be a nonempty string of at most 100 chars")
    if type(master_seed) is not int or master_seed < 0:
        raise ValueError("master_seed must be a nonnegative integer")
    if (type(initial_active_seconds) not in (int, float) or initial_active_seconds < 0):
        raise ValueError("initial_active_seconds must be nonnegative")
    if (not fixtures and not proposal_outcomes) or len(fixtures) != len(set(fixtures)):
        raise ValueError("fixtures or proposal outcomes are required; SCM IDs must be unique")
    if any(not callable(hook) or getattr(hook, "__test_only_fixture_hook__", False) is not True
           for hook in (after_claim_hook, before_commit_hook) if hook is not None):
        raise PermissionError("orchestration hooks are TEST_ONLY process-test hooks")
    if max_new_scms is not None and (type(max_new_scms) is not int or max_new_scms < 0):
        raise ValueError("max_new_scms must be a nonnegative integer")
    if resource_limits is not None and (after_claim_hook is not None or before_commit_hook is not None):
        raise ValueError("process interruption hooks cannot be combined with resource-limited workers")

    specs = {scm_id: _fixture_spec(value) for scm_id, value in fixtures.items()}
    if any(not isinstance(scm_id, str) or not scm_id or len(scm_id) > 100 for scm_id in specs):
        raise ValueError("SCM fixture IDs must be stable nonempty strings")
    root = Path(output_root).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    db_name = ("research_c_cohort.sqlite" if cohort_type == "RESEARCH_COHORT"
               else "research_c_fixture_cohort.sqlite")
    db_path = root / db_name
    lock_path = root / f".{db_name}.lock"
    code_hashes = _code_hashes(ROOT)
    factory_bindings = [{"scm_id": scm_id,
                         "factory": (f"{type(spec['factory']).__module__}.{type(spec['factory']).__qualname__}"
                                     if not hasattr(spec["factory"], "__qualname__") else
                                     f"{spec['factory'].__module__}.{spec['factory'].__qualname__}"),
                         "apply_g0_generator": spec["apply_g0_generator"]}
                        for scm_id, spec in specs.items()]
    config = {"schema": "research-c-multi-cohort-v1", "cohort_type": cohort_type,
              "run_id": run_id, "master_seed": master_seed, "budgets": list(budgets),
              "fixtures": factory_bindings, "execution_enabled_for_research": research_authorized,
              "proposal_active_seconds": float(initial_active_seconds),
              "resource_limits": resource_limits.binding() if resource_limits else None,
              "runtime_fingerprint": _runtime_fingerprint()}
    proposals = proposal_outcomes or []
    if any(not isinstance(item, dict) or item.get("proposal_id") is None for item in proposals):
        raise ValueError("proposal_outcomes require explicit proposal_id records")
    if len({item["proposal_id"] for item in proposals}) != len(proposals):
        raise ValueError("proposal IDs must be unique")
    proposal_bindings = [{k: item.get(k) for k in
                          ("proposal_id", "status", "reason", "topology_hash", "scm_id")}
                         for item in proposals]
    config["proposal_outcomes"] = proposal_bindings
    config_sha = _digest({"config": config, "code_sha256": code_hashes})
    source = _git_revision(ROOT)

    with _run_lock(lock_path):
        connection = _connect(db_path)
        try:
            _schema(connection)
            connection.execute("BEGIN IMMEDIATE")
            existing = connection.execute("SELECT * FROM runs WHERE run_id=?", (run_id,)).fetchone()
            if existing is None:
                connection.execute(
                    "INSERT INTO runs(run_id,cohort_type,master_seed,config_json,config_sha256,code_json,source_json,created_at,active_seconds) VALUES(?,?,?,?,?,?,?,?,?)",
                    (run_id, cohort_type, master_seed, _canonical(config).decode("ascii"),
                     config_sha, _canonical(code_hashes).decode("ascii"),
                     _canonical(source).decode("ascii"), time.time(),
                     float(initial_active_seconds)))
                for ordinal, (scm_id, spec) in enumerate(specs.items()):
                    namespace = cohort_type.lower()
                    streams = {name: _subseed(master_seed, namespace, scm_id, name)
                               for name in ("scm", "g0", "evaluation")}
                    connection.execute(
                        "INSERT INTO scms(run_id,scm_id,ordinal,status,rng_json) VALUES(?,?,?,?,?)",
                        (run_id, scm_id, ordinal, "PROPOSED", _canonical(streams).decode("ascii")))
                    _event(connection, run_id, scm_id, None, "PROPOSED", cohort_type)
                for item in proposals:
                    record = _jsonable(item)
                    record_json = _canonical(record).decode("ascii")
                    connection.execute("INSERT INTO proposals VALUES(?,?,?,?,?,?,?,?)",
                        (run_id, str(item["proposal_id"]), str(item.get("status", "PROPOSED")),
                         item.get("reason"), item.get("topology_hash"), item.get("scm_id"),
                         record_json, _digest(record)))
            else:
                if (existing["config_sha256"] != config_sha
                        or existing["cohort_type"] != cohort_type
                        or existing["master_seed"] != master_seed):
                    raise LedgerConflict("run_id reused with different fixture/config/code/seed binding")
                stored_proposals = connection.execute(
                    "SELECT proposal_id,proposal_sha256 FROM proposals WHERE run_id=? ORDER BY rowid",
                    (run_id,)).fetchall()
                expected_proposals = [(str(item["proposal_id"]), _digest(_jsonable(item)))
                                      for item in proposals]
                if [(row["proposal_id"], row["proposal_sha256"]) for row in stored_proposals] != expected_proposals:
                    raise LedgerConflict("proposal outcomes differ from persisted run")
                stored = connection.execute("SELECT scm_id,ordinal,rng_json FROM scms WHERE run_id=? ORDER BY ordinal",
                                            (run_id,)).fetchall()
                expected = [(scm_id, i) for i, scm_id in enumerate(specs)]
                if [(row["scm_id"], row["ordinal"]) for row in stored] != expected:
                    raise LedgerConflict("fixture IDs/order differ from persisted run")
            connection.commit()

            connection.execute("BEGIN IMMEDIATE")
            proposed = connection.execute("SELECT scm_id FROM scms WHERE run_id=? AND status='PROPOSED'",
                                          (run_id,)).fetchall()
            for row in proposed:
                connection.execute("UPDATE scms SET status='ADMITTED' WHERE run_id=? AND scm_id=?",
                                   (run_id, row["scm_id"]))
                _event(connection, run_id, row["scm_id"], "PROPOSED", "ADMITTED", "FIXTURE_ID_VALID")
            connection.commit()

            processed = 0
            cohort_stop_reason = None
            run_active = float(connection.execute(
                "SELECT active_seconds FROM runs WHERE run_id=?", (run_id,)).fetchone()[0])
            for scm_id, spec in specs.items():
                row = connection.execute("SELECT * FROM scms WHERE run_id=? AND scm_id=?",
                                         (run_id, scm_id)).fetchone()
                if row["status"] == "COMPLETED" or row["status"] == "FAILED":
                    if row["status"] == "COMPLETED":
                        _verify_result(row["result_json"], row["result_sha256"],
                                       "TEST_ONLY_NOT_RESEARCH_COHORT" if not research_authorized else "RESEARCH_COHORT_RESULT")
                    continue
                if max_new_scms is not None and processed >= max_new_scms:
                    break
                streams = json.loads(row["rng_json"])
                old = row["status"]
                scm_active = float(row["active_seconds"])
                if old == "RUNNING" and row["started_at"] is not None:
                    # A killed parent cannot checkpoint its final duration.
                    # Charge the entire wall gap conservatively on recovery.
                    interrupted = max(0.0, time.time() - float(row["started_at"]))
                    scm_active += interrupted
                    run_active += interrupted
                    connection.execute("BEGIN IMMEDIATE")
                    connection.execute("UPDATE scms SET active_seconds=?,started_at=NULL WHERE run_id=? AND scm_id=?",
                                       (scm_active, run_id, scm_id))
                    connection.execute("UPDATE runs SET active_seconds=? WHERE run_id=?",
                                       (run_active, run_id))
                    _event(connection, run_id, scm_id, "RUNNING", "RUNNING",
                           f"INTERRUPTED_ATTEMPT_RECONCILED:{interrupted:.6f}s")
                    connection.commit()
                if resource_limits is not None:
                    if run_active >= resource_limits.cohort_active_seconds:
                        cohort_stop_reason = "COHORT_ACTIVE_TIME_CAP"
                        connection.execute("BEGIN IMMEDIATE")
                        _event(connection, run_id, None, None, "RESOURCE_STOP", cohort_stop_reason)
                        connection.commit()
                        break
                    if scm_active >= resource_limits.scm_active_seconds:
                        connection.execute("BEGIN IMMEDIATE")
                        reason = "SCM_ACTIVE_TIME_CAP: persisted active time exhausted"
                        connection.execute("UPDATE scms SET status='FAILED',failure_code=?,failure_reason=?,retryable=0,completed_at=? WHERE run_id=? AND scm_id=?",
                                           ("SCM_ACTIVE_TIME_CAP", reason, time.time(), run_id, scm_id))
                        _event(connection, run_id, scm_id, old, "FAILED", reason)
                        connection.commit()
                        continue
                    try:
                        check_storage(root, next_bytes=16 * 1024, limits=resource_limits)
                    except ResourceLimitStop as exc:
                        cohort_stop_reason = exc.code
                        connection.execute("BEGIN IMMEDIATE")
                        _event(connection, run_id, None, None, "RESOURCE_STOP", f"{exc.code}:{exc}")
                        connection.commit()
                        break
                start_wall = time.time()
                connection.execute("BEGIN IMMEDIATE")
                connection.execute("""UPDATE scms SET status='RUNNING',attempt_count=attempt_count+1,
                                    failure_reason=NULL,failure_code=NULL,started_at=? WHERE run_id=? AND scm_id=?""",
                                   (start_wall, run_id, scm_id))
                _event(connection, run_id, scm_id, old, "RUNNING",
                       "RESUME_INTERRUPTED_SCM" if old == "RUNNING" else "EXECUTION_CLAIMED")
                connection.commit()
                unit_started = time.monotonic()
                sampled_peak = None
                try:
                    if after_claim_hook is not None:
                        after_claim_hook(scm_id)
                    if resource_limits is not None:
                        remaining_scm = resource_limits.scm_active_seconds - scm_active
                        remaining_cohort = resource_limits.cohort_active_seconds - run_active
                        timeout = min(resource_limits.unit_timeout_seconds,
                                      remaining_scm, remaining_cohort)
                        if timeout <= 0:
                            raise ResourceLimitStop("COHORT_ACTIVE_TIME_CAP" if remaining_cohort <= 0
                                                    else "SCM_ACTIVE_TIME_CAP", "active time exhausted")
                        payload, stop_code, worker_elapsed, sampled_peak = run_isolated(
                            partial(_compute_fixture_payload, spec["factory"], streams["g0"],
                                    f"{run_id}:{scm_id}", tuple(budgets),
                                    spec["apply_g0_generator"], research_authorized),
                            timeout_seconds=timeout,
                            rss_cap_bytes=resource_limits.sampled_rss_bytes)
                        if stop_code:
                            if stop_code == "UNIT_TIMEOUT" and timeout < resource_limits.unit_timeout_seconds:
                                stop_code = ("COHORT_ACTIVE_TIME_CAP" if remaining_cohort <= remaining_scm
                                             else "SCM_ACTIVE_TIME_CAP")
                            raise ResourceLimitStop(stop_code, "isolated SCM worker stopped")
                        payload, stage_timings = payload
                    else:
                        generation_started = time.monotonic()
                        fixture, metadata = spec["factory"]()
                        generation_seconds = time.monotonic() - generation_started
                        stage_timings = {}
                        payload = execute_fixture_input(
                            fixture, metadata=metadata, g0_seed=streams["g0"],
                            task_id=f"{run_id}:{scm_id}", budgets=budgets,
                            apply_g0_generator=spec["apply_g0_generator"],
                            _timing_sink=stage_timings)
                        stage_timings["scm_observation_g0_generation_seconds"] = generation_seconds
                        worker_elapsed = max(0.0, time.monotonic() - unit_started)
                    expected_classification = ("RESEARCH_COHORT_RESULT" if research_authorized
                                               else "TEST_ONLY_NOT_RESEARCH_COHORT")
                    if (payload["classification"] != expected_classification
                            or not all(b["policy_vector_status"] == "COMPLETE"
                                       for b in payload["e2e_result"]["budgets"])):
                        raise CohortIntegrityError("incomplete TEST_ONLY policy vector")
                    payload["cohort_binding"] = {"run_id": run_id, "cohort_type": cohort_type,
                                                  "scm_id": scm_id, "rng_streams": streams,
                                                  "scm_seed_used_for_sampling": False,
                                                  "evaluation_seed_used_for_sampling": False}
                    if before_commit_hook is not None:
                        before_commit_hook(scm_id)
                    persistence_started = time.perf_counter()
                    result_sha = _digest(payload)
                    result_json = json.dumps({"payload": _jsonable(payload),
                                              "payload_sha256": result_sha},
                                             ensure_ascii=False, sort_keys=True,
                                             separators=(",", ":"), allow_nan=False)
                    result_bytes = len(result_json.encode("utf-8"))
                    elapsed = max(0.0, time.monotonic() - unit_started)
                    new_scm_active = scm_active + elapsed
                    new_run_active = run_active + elapsed
                    if resource_limits is not None:
                        if result_bytes > resource_limits.max_result_bytes:
                            raise ResourceLimitStop("RESULT_BYTE_CAP",
                                                    f"result_bytes={result_bytes}, cap={resource_limits.max_result_bytes}")
                        ledger_size = db_path.stat().st_size if db_path.exists() else 0
                        if ledger_size + result_bytes + 16 * 1024 > resource_limits.max_ledger_bytes:
                            raise ResourceLimitStop("LEDGER_BYTE_CAP",
                                f"ledger={ledger_size}, result={result_bytes}, cap={resource_limits.max_ledger_bytes}")
                        check_storage(root, next_bytes=result_bytes + 16 * 1024,
                                      limits=resource_limits)
                    stage_timings["result_validation_and_serialization_seconds"] = (
                        time.perf_counter() - persistence_started)
                    stage_timing_json = _canonical(stage_timings).decode("ascii")
                    input_sha = payload["input_sha256"]
                    connection.execute("BEGIN IMMEDIATE")
                    latest = connection.execute("SELECT status FROM scms WHERE run_id=? AND scm_id=?",
                                                (run_id, scm_id)).fetchone()["status"]
                    if latest != "RUNNING":
                        raise LedgerConflict("SCM state changed before result commit")
                    connection.execute("""UPDATE scms SET status='COMPLETED',input_sha256=?,result_json=?,
                                        result_sha256=?,retryable=0,completed_at=?,started_at=NULL,
                                        active_seconds=?,sampled_rss_peak_bytes=?,stage_timing_json=?
                                        WHERE run_id=? AND scm_id=?""",
                                       (input_sha, result_json, result_sha, time.time(), new_scm_active,
                                        sampled_peak, stage_timing_json, run_id, scm_id))
                    connection.execute("UPDATE runs SET active_seconds=? WHERE run_id=?",
                                       (new_run_active, run_id))
                    _event(connection, run_id, scm_id, "RUNNING", "COMPLETED", "ATOMIC_RESULT_COMMIT")
                    commit_started = time.perf_counter()
                    connection.commit()
                    commit_seconds = time.perf_counter() - commit_started
                    # Resource timings live beside, not inside, the deterministic
                    # result payload. The primary result and its checksum remain
                    # atomically committed together; this sidecar records the
                    # measured first commit duration without changing that hash.
                    stage_timings["atomic_result_commit_seconds"] = commit_seconds
                    new_scm_active += commit_seconds
                    new_run_active += commit_seconds
                    run_active = new_run_active
                    connection.execute("BEGIN IMMEDIATE")
                    connection.execute("UPDATE scms SET active_seconds=?,stage_timing_json=? WHERE run_id=? AND scm_id=?",
                                       (new_scm_active, _canonical(stage_timings).decode("ascii"),
                                        run_id, scm_id))
                    connection.execute("UPDATE runs SET active_seconds=? WHERE run_id=?",
                                       (new_run_active, run_id))
                    connection.commit()
                except Exception as exc:
                    elapsed = max(0.0, time.monotonic() - unit_started)
                    new_scm_active = scm_active + elapsed
                    new_run_active = run_active + elapsed
                    if connection.in_transaction:
                        connection.rollback()
                    connection.execute("BEGIN IMMEDIATE")
                    latest = connection.execute("SELECT status FROM scms WHERE run_id=? AND scm_id=?",
                                                (run_id, scm_id)).fetchone()["status"]
                    if latest == "RUNNING":
                        reason = f"{type(exc).__name__}:{str(exc)[:500]}"
                        failure_code = getattr(exc, "code", None) or type(exc).__name__
                        connection.execute("""UPDATE scms SET status='FAILED',failure_code=?,failure_reason=?,retryable=0,
                                            completed_at=?,started_at=NULL,active_seconds=?,sampled_rss_peak_bytes=?
                                            WHERE run_id=? AND scm_id=?""",
                                           (failure_code, reason, time.time(), new_scm_active,
                                            sampled_peak, run_id, scm_id))
                        connection.execute("UPDATE runs SET active_seconds=? WHERE run_id=?",
                                           (new_run_active, run_id))
                        _event(connection, run_id, scm_id, "RUNNING", "FAILED", reason)
                        connection.commit()
                    else:
                        connection.rollback()
                    if isinstance(exc, ResourceLimitStop):
                        cohort_stop_reason = exc.code
                processed += 1
                run_active = new_run_active
                if cohort_stop_reason:
                    break

            rows = connection.execute("SELECT * FROM scms WHERE run_id=? ORDER BY ordinal", (run_id,)).fetchall()
            scm_results = []
            for row in rows:
                record = {"scm_id": row["scm_id"], "status": row["status"],
                          "attempt_count": row["attempt_count"], "rng_streams": json.loads(row["rng_json"]),
                          "input_sha256": row["input_sha256"], "result_sha256": row["result_sha256"],
                          "failure_reason": row["failure_reason"], "failure_code": row["failure_code"],
                          "active_seconds": row["active_seconds"],
                          "stage_timings": (json.loads(row["stage_timing_json"])
                                            if row["stage_timing_json"] else None),
                          "sampled_rss_peak_bytes": row["sampled_rss_peak_bytes"],
                          "retryable": bool(row["retryable"])}
                if row["status"] == "COMPLETED":
                    expected_class = ("RESEARCH_COHORT_RESULT" if research_authorized
                                      else "TEST_ONLY_NOT_RESEARCH_COHORT")
                    record["result"] = _verify_result(row["result_json"], row["result_sha256"], expected_class)
                scm_results.append(record)
            states = [row["status"] for row in rows]
            proposal_rows = connection.execute(
                "SELECT * FROM proposals WHERE run_id=? ORDER BY rowid", (run_id,)).fetchall()
            proposal_records = []
            for proposal_row in proposal_rows:
                parsed = json.loads(proposal_row["proposal_json"])
                if _digest(parsed) != proposal_row["proposal_sha256"]:
                    raise CohortIntegrityError("proposal record checksum mismatch")
                proposal_records.append(parsed)
            run_active_final = float(connection.execute(
                "SELECT active_seconds FROM runs WHERE run_id=?", (run_id,)).fetchone()[0])
            storage_metrics = None
            if resource_limits is not None:
                storage_metrics = {"cohort_storage_bytes": directory_usage_bytes(root),
                                   "free_disk_bytes": shutil.disk_usage(root).free,
                                   "ledger_bytes": db_path.stat().st_size if db_path.exists() else 0,
                                   "limit_binding": resource_limits.binding(),
                                   "rss_is_sampled": True,
                                   "filesystem_quota_enforced": False}
            return {"schema": "research-c-multi-cohort-v1",
                    "classification": ("RESEARCH_COHORT_RESULT" if research_authorized
                                       else "TEST_ONLY_NOT_RESEARCH_COHORT"),
                    "run_id": run_id, "cohort_type": cohort_type, "master_seed": master_seed,
                    "config_sha256": config_sha, "code_sha256": code_hashes, "source_revision": source,
                    "counts": {status.lower(): states.count(status)
                               for status in ("PROPOSED", "ADMITTED", "RUNNING", "COMPLETED", "FAILED")},
                    "completed_scm_count": states.count("COMPLETED"),
                    "complete_policy_evaluations": sum(
                        len(b["policies"]) for r in scm_results if r["status"] == "COMPLETED"
                        for b in r["result"]["e2e_result"]["budgets"]),
                    "proposal_counts": {
                        status.lower(): sum(item.get("status") == status for item in proposal_records)
                        for status in ("PROPOSED", "STRUCTURALLY_INELIGIBLE", "ADMITTED")},
                    "proposals": proposal_records,
                    "cohort_stop_reason": cohort_stop_reason,
                    "cumulative_active_seconds": run_active_final,
                    "resource_metrics": storage_metrics,
                    "all_scm_complete": bool(states) and all(s == "COMPLETED" for s in states),
                    "scms": scm_results}
        finally:
            connection.close()


def read_test_only_cohort(output_root: Path, *, run_id: str) -> dict:
    """Re-read a durable TEST_ONLY run, validating each stored result hash."""
    root = Path(output_root).expanduser().resolve()
    connection = _connect(root / "research_c_fixture_cohort.sqlite")
    try:
        _schema(connection)
        run = connection.execute("SELECT * FROM runs WHERE run_id=?", (run_id,)).fetchone()
        if run is None:
            raise KeyError(run_id)
        rows = connection.execute("SELECT * FROM scms WHERE run_id=? ORDER BY ordinal", (run_id,)).fetchall()
        payloads = []
        expected_type = run["cohort_type"]
        expected_class = ("RESEARCH_COHORT_RESULT" if expected_type == "RESEARCH_COHORT"
                          else "TEST_ONLY_NOT_RESEARCH_COHORT")
        for row in rows:
            result = _verify_result(row["result_json"], row["result_sha256"], expected_class) if row["result_json"] else None
            payloads.append({"scm_id": row["scm_id"], "status": row["status"],
                             "result": result, "failure_reason": row["failure_reason"]})
        return {"run_id": run_id, "config_sha256": run["config_sha256"], "scms": payloads}
    finally:
        connection.close()


def read_approved_research_cohort(output_root: Path, *, run_id: str,
                                  _authorization=None) -> dict:
    """Read and checksum a previously approved research run after gate validation."""
    if _authorization is not _RESEARCH_EXECUTION_CAPABILITY:
        raise PermissionError("research result access requires validated runner capability")
    root = Path(output_root).expanduser().resolve()
    connection = _connect(root / "research_c_cohort.sqlite")
    try:
        _schema(connection)
        run = connection.execute("SELECT * FROM runs WHERE run_id=?", (run_id,)).fetchone()
        if run is None or run["cohort_type"] != "RESEARCH_COHORT":
            raise KeyError(run_id)
        rows = connection.execute("SELECT * FROM scms WHERE run_id=? ORDER BY ordinal", (run_id,)).fetchall()
        expected = "RESEARCH_COHORT_RESULT"
        return {"run_id": run_id, "config_sha256": run["config_sha256"],
                "scms": [{"scm_id": row["scm_id"], "status": row["status"],
                          "result": (_verify_result(row["result_json"], row["result_sha256"], expected)
                                     if row["result_json"] else None),
                          "failure_reason": row["failure_reason"]} for row in rows]}
    finally:
        connection.close()

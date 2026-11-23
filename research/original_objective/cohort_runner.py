"""Durable multi-fixture orchestration for TEST_ONLY Research C inputs.

This is not a research-cohort executor. It stores each SCM's full existing
single-SCM Runner output in one SQLite transaction and can replay an
interrupted TEST_ONLY SCM deterministically.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import sqlite3
import time

from .cohort_ledger_test_only import LedgerConflict, _run_lock, _subseed
from .runner import (ROOT, _canonical, _code_hashes, _digest, _git_revision,
                     _jsonable, execute_fixture_input)


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
      source_json TEXT NOT NULL, created_at REAL NOT NULL
    );
    CREATE TABLE IF NOT EXISTS scms (
      run_id TEXT NOT NULL, scm_id TEXT NOT NULL, ordinal INTEGER NOT NULL,
      status TEXT NOT NULL, rng_json TEXT NOT NULL, attempt_count INTEGER NOT NULL DEFAULT 0,
      input_sha256 TEXT, result_json TEXT, result_sha256 TEXT,
      failure_reason TEXT, retryable INTEGER NOT NULL DEFAULT 0,
      started_at REAL, completed_at REAL,
      PRIMARY KEY (run_id, scm_id), UNIQUE (run_id, ordinal),
      FOREIGN KEY (run_id) REFERENCES runs(run_id)
    );
    CREATE TABLE IF NOT EXISTS events (
      event_id INTEGER PRIMARY KEY AUTOINCREMENT, run_id TEXT NOT NULL,
      scm_id TEXT, from_status TEXT, to_status TEXT NOT NULL,
      reason TEXT, created_at REAL NOT NULL,
      FOREIGN KEY (run_id) REFERENCES runs(run_id)
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


def _verify_result(result_json: str, expected_sha: str) -> dict:
    try:
        wrapper = json.loads(result_json)
    except json.JSONDecodeError as exc:
        raise CohortIntegrityError("stored SCM result is not valid JSON") from exc
    payload = wrapper.get("payload")
    if not isinstance(payload, dict) or _digest(payload) != expected_sha:
        raise CohortIntegrityError("SCM result checksum mismatch")
    if wrapper.get("payload_sha256") != expected_sha:
        raise CohortIntegrityError("SCM result wrapper checksum mismatch")
    if payload.get("classification") != "TEST_ONLY_NOT_RESEARCH_COHORT":
        raise CohortIntegrityError("non-fixture result found in TEST_ONLY cohort store")
    return payload


def run_test_only_cohort(output_root: Path, *, run_id: str, master_seed: int,
                         fixtures: dict, budgets=(0, 1, 2, 3, 4),
                         max_new_scms: int | None = None,
                         after_claim_hook=None, before_commit_hook=None) -> dict:
    """Run/recover a fixed-fixture SCM sequence; never samples a study SCM.

    Optional hooks exist only for actual subprocess termination tests and must
    carry the explicit ``__test_only_fixture_hook__`` marker.
    """
    if not isinstance(run_id, str) or not run_id or len(run_id) > 100:
        raise ValueError("run_id must be a nonempty string of at most 100 chars")
    if type(master_seed) is not int or master_seed < 0:
        raise ValueError("master_seed must be a nonnegative integer")
    if not fixtures or len(fixtures) != len(set(fixtures)):
        raise ValueError("fixtures must have unique deterministic SCM IDs")
    if any(not callable(hook) or getattr(hook, "__test_only_fixture_hook__", False) is not True
           for hook in (after_claim_hook, before_commit_hook) if hook is not None):
        raise PermissionError("orchestration hooks are TEST_ONLY process-test hooks")
    if max_new_scms is not None and (type(max_new_scms) is not int or max_new_scms < 0):
        raise ValueError("max_new_scms must be a nonnegative integer")

    specs = {scm_id: _fixture_spec(value) for scm_id, value in fixtures.items()}
    if any(not isinstance(scm_id, str) or not scm_id or len(scm_id) > 100 for scm_id in specs):
        raise ValueError("SCM fixture IDs must be stable nonempty strings")
    root = Path(output_root).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    db_path = root / "research_c_fixture_cohort.sqlite"
    lock_path = root / ".research_c_fixture_cohort.lock"
    code_hashes = _code_hashes(ROOT)
    factory_bindings = [{"scm_id": scm_id,
                         "factory": f"{getattr(spec['factory'], '__module__', '')}.{getattr(spec['factory'], '__qualname__', '')}",
                         "apply_g0_generator": spec["apply_g0_generator"]}
                        for scm_id, spec in specs.items()]
    config = {"schema": "research-c-multi-fixture-v1", "cohort_type": "TEST_ONLY_FIXTURE",
              "run_id": run_id, "master_seed": master_seed, "budgets": list(budgets),
              "fixtures": factory_bindings, "execution_enabled_for_research": False}
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
                    "INSERT INTO runs VALUES(?,?,?,?,?,?,?,?)",
                    (run_id, "TEST_ONLY_FIXTURE", master_seed, _canonical(config).decode("ascii"),
                     config_sha, _canonical(code_hashes).decode("ascii"),
                     _canonical(source).decode("ascii"), time.time()))
                for ordinal, (scm_id, spec) in enumerate(specs.items()):
                    streams = {name: _subseed(master_seed, "fixture", scm_id, name)
                               for name in ("scm", "g0", "evaluation")}
                    connection.execute(
                        "INSERT INTO scms(run_id,scm_id,ordinal,status,rng_json) VALUES(?,?,?,?,?)",
                        (run_id, scm_id, ordinal, "PROPOSED", _canonical(streams).decode("ascii")))
                    _event(connection, run_id, scm_id, None, "PROPOSED", "FIXED_TEST_ONLY_FIXTURE")
            else:
                if (existing["config_sha256"] != config_sha
                        or existing["cohort_type"] != "TEST_ONLY_FIXTURE"
                        or existing["master_seed"] != master_seed):
                    raise LedgerConflict("run_id reused with different fixture/config/code/seed binding")
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
            for scm_id, spec in specs.items():
                row = connection.execute("SELECT * FROM scms WHERE run_id=? AND scm_id=?",
                                         (run_id, scm_id)).fetchone()
                if row["status"] == "COMPLETED" or row["status"] == "FAILED":
                    if row["status"] == "COMPLETED":
                        _verify_result(row["result_json"], row["result_sha256"])
                    continue
                if max_new_scms is not None and processed >= max_new_scms:
                    break
                streams = json.loads(row["rng_json"])
                old = row["status"]
                connection.execute("BEGIN IMMEDIATE")
                connection.execute("""UPDATE scms SET status='RUNNING',attempt_count=attempt_count+1,
                                    failure_reason=NULL,started_at=? WHERE run_id=? AND scm_id=?""",
                                   (time.time(), run_id, scm_id))
                _event(connection, run_id, scm_id, old, "RUNNING",
                       "RESUME_INTERRUPTED_SCM" if old == "RUNNING" else "EXECUTION_CLAIMED")
                connection.commit()
                try:
                    if after_claim_hook is not None:
                        after_claim_hook(scm_id)
                    fixture, metadata = spec["factory"]()
                    payload = execute_fixture_input(
                        fixture, metadata=metadata, g0_seed=streams["g0"],
                        task_id=f"{run_id}:{scm_id}", budgets=budgets,
                        apply_g0_generator=spec["apply_g0_generator"])
                    if (payload["classification"] != "TEST_ONLY_NOT_RESEARCH_COHORT"
                            or not all(b["policy_vector_status"] == "COMPLETE"
                                       for b in payload["e2e_result"]["budgets"])):
                        raise CohortIntegrityError("incomplete TEST_ONLY policy vector")
                    payload["cohort_binding"] = {"run_id": run_id, "cohort_type": "TEST_ONLY_FIXTURE",
                                                  "scm_id": scm_id, "rng_streams": streams,
                                                  "scm_seed_used_for_sampling": False,
                                                  "evaluation_seed_used_for_sampling": False}
                    if before_commit_hook is not None:
                        before_commit_hook(scm_id)
                    result_sha = _digest(payload)
                    result_json = json.dumps({"payload": _jsonable(payload),
                                              "payload_sha256": result_sha},
                                             ensure_ascii=False, sort_keys=True,
                                             separators=(",", ":"), allow_nan=False)
                    input_sha = payload["input_sha256"]
                    connection.execute("BEGIN IMMEDIATE")
                    latest = connection.execute("SELECT status FROM scms WHERE run_id=? AND scm_id=?",
                                                (run_id, scm_id)).fetchone()["status"]
                    if latest != "RUNNING":
                        raise LedgerConflict("SCM state changed before result commit")
                    connection.execute("""UPDATE scms SET status='COMPLETED',input_sha256=?,result_json=?,
                                        result_sha256=?,retryable=0,completed_at=? WHERE run_id=? AND scm_id=?""",
                                       (input_sha, result_json, result_sha, time.time(), run_id, scm_id))
                    _event(connection, run_id, scm_id, "RUNNING", "COMPLETED", "ATOMIC_RESULT_COMMIT")
                    connection.commit()
                except Exception as exc:
                    if connection.in_transaction:
                        connection.rollback()
                    connection.execute("BEGIN IMMEDIATE")
                    latest = connection.execute("SELECT status FROM scms WHERE run_id=? AND scm_id=?",
                                                (run_id, scm_id)).fetchone()["status"]
                    if latest == "RUNNING":
                        reason = f"{type(exc).__name__}:{str(exc)[:500]}"
                        connection.execute("""UPDATE scms SET status='FAILED',failure_reason=?,retryable=0,
                                            completed_at=? WHERE run_id=? AND scm_id=?""",
                                           (reason, time.time(), run_id, scm_id))
                        _event(connection, run_id, scm_id, "RUNNING", "FAILED", reason)
                        connection.commit()
                    else:
                        connection.rollback()
                processed += 1

            rows = connection.execute("SELECT * FROM scms WHERE run_id=? ORDER BY ordinal", (run_id,)).fetchall()
            scm_results = []
            for row in rows:
                record = {"scm_id": row["scm_id"], "status": row["status"],
                          "attempt_count": row["attempt_count"], "rng_streams": json.loads(row["rng_json"]),
                          "input_sha256": row["input_sha256"], "result_sha256": row["result_sha256"],
                          "failure_reason": row["failure_reason"], "retryable": bool(row["retryable"])}
                if row["status"] == "COMPLETED":
                    record["result"] = _verify_result(row["result_json"], row["result_sha256"])
                scm_results.append(record)
            states = [row["status"] for row in rows]
            return {"schema": "research-c-multi-fixture-v1", "classification": "TEST_ONLY_NOT_RESEARCH_COHORT",
                    "run_id": run_id, "cohort_type": "TEST_ONLY_FIXTURE", "master_seed": master_seed,
                    "config_sha256": config_sha, "code_sha256": code_hashes, "source_revision": source,
                    "counts": {status.lower(): states.count(status)
                               for status in ("PROPOSED", "ADMITTED", "RUNNING", "COMPLETED", "FAILED")},
                    "completed_scm_count": states.count("COMPLETED"),
                    "complete_policy_evaluations": sum(
                        len(b["policies"]) for r in scm_results if r["status"] == "COMPLETED"
                        for b in r["result"]["e2e_result"]["budgets"]),
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
        for row in rows:
            result = _verify_result(row["result_json"], row["result_sha256"]) if row["result_json"] else None
            payloads.append({"scm_id": row["scm_id"], "status": row["status"],
                             "result": result, "failure_reason": row["failure_reason"]})
        return {"run_id": run_id, "config_sha256": run["config_sha256"], "scms": payloads}
    finally:
        connection.close()

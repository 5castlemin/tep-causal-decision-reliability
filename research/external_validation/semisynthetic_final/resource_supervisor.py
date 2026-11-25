"""Windows process-tree RSS and wall-time supervisor for the one final run."""
from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import psutil

from research.external_validation.semisynthetic_final.final_pipeline import atomic_json


def process_tree_rss(pid: int) -> tuple[int, list[int]]:
    try:
        root = psutil.Process(pid)
        rows = [root, *root.children(recursive=True)]
    except psutil.NoSuchProcess:
        return 0, []
    rss, ids = 0, []
    for proc in rows:
        try:
            rss += proc.memory_info().rss
            ids.append(proc.pid)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return rss, ids


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--report", type=Path, required=True)
    p.add_argument("--wall-seconds", type=int, default=7200)
    p.add_argument("--rss-bytes", type=int, default=4294967296)
    p.add_argument("command", nargs=argparse.REMAINDER)
    args = p.parse_args(argv)
    if args.report.exists():
        raise FileExistsError("resource report already exists")
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command:
        raise ValueError("supervised command is required")
    started = time.monotonic()
    proc = subprocess.Popen(command, creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0))
    peak, peak_ids, breach = 0, [], None
    while proc.poll() is None:
        rss, pids = process_tree_rss(proc.pid)
        if rss > peak:
            peak, peak_ids = rss, pids
        elapsed = time.monotonic() - started
        if rss > args.rss_bytes:
            breach = "process_tree_rss_limit"
        elif elapsed > args.wall_seconds:
            breach = "wall_time_limit"
        if breach:
            try:
                parent = psutil.Process(proc.pid)
                for child in parent.children(recursive=True):
                    try: child.kill()
                    except psutil.NoSuchProcess: pass
                parent.kill()
            except psutil.NoSuchProcess:
                pass
            break
        time.sleep(2.0)
    code = proc.wait()
    report = {"schema": "RESEARCH_D_FINAL_RESOURCE_SUPERVISION_V1",
        "status": "RESOURCE_LIMIT_BREACH" if breach else ("COMPLETED" if code == 0 else "CHILD_FAILED"),
        "child_exit_code": code, "breach": breach, "elapsed_seconds": time.monotonic()-started,
        "peak_process_tree_rss_bytes": peak, "peak_process_ids": peak_ids,
        "wall_limit_seconds": args.wall_seconds, "rss_limit_bytes": args.rss_bytes,
        "sampling_parallelism": 1, "monitor": "psutil process tree recursive RSS; Windows host",
        "psutil_version": psutil.__version__, "child_command": command,
        "resource_limit_enforced": True}
    atomic_json(args.report, report)
    print(json.dumps(report, sort_keys=True))
    return code if not breach else 124


if __name__ == "__main__":
    raise SystemExit(main())

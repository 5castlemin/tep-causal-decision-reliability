"""Fail a PR when substantive changes omit the three research status documents."""

from __future__ import annotations

import argparse
import subprocess

REQUIRED = {"PROJECT_STATUS.md", "PRIORITIES.md", "WORK_LOG.md"}
SUBSTANTIVE_PREFIXES = ("src/", "graphs/", "experiments/", "data/", "config/", "protocol/")
SUBSTANTIVE_FILES = {"RESEARCH_DESIGN.md", "PILOT_PLAN.md"}


def missing_documents(changed: set[str]) -> set[str]:
    substantive = any(p in SUBSTANTIVE_FILES or p.startswith(SUBSTANTIVE_PREFIXES) for p in changed)
    return REQUIRED - changed if substantive else set()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True, help="Comparison ref, e.g. origin/main")
    args = parser.parse_args()
    diff = subprocess.run(
        ["git", "diff", "--name-only", f"{args.base}...HEAD"],
        check=True, capture_output=True, text=True,
    )
    changed = set(diff.stdout.splitlines())
    missing = missing_documents(changed)
    if missing:
        print("[FAIL] 연구 코드/자료 변경에 동반되지 않은 문서:", ", ".join(sorted(missing)))
        return 1
    print("[PASS] 연구 문서 동기화 파일 변경 확인 (내용의 진실성은 별도 검토 필요)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

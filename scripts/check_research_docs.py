"""Ensure substantive PRs carry live status artifacts, not frozen Step 4 files."""

from __future__ import annotations

import argparse
import subprocess

REQUIRED = {"docs/research_state_current.json", "docs/current/PROJECT_STATUS_CURRENT.md",
            "docs/current/PRIORITIES_CURRENT.md", "docs/current/WORK_LOG_CURRENT.md"}
SUBSTANTIVE_PREFIXES = ("src/", "graphs/", "experiments/", "data/", "config/", "protocol/", "research/", "tests/")
SUBSTANTIVE_FILES = {"RESEARCH_DESIGN.md", "PILOT_PLAN.md"}
SUBSTANTIVE_SCRIPTS = ("scripts/run_", "scripts/analyze_", "scripts/audit_", "scripts/prepare_")


def missing_documents(changed: set[str]) -> set[str]:
    substantive = any(p in SUBSTANTIVE_FILES or p.startswith(SUBSTANTIVE_PREFIXES)
                      or p.startswith(SUBSTANTIVE_SCRIPTS) for p in changed)
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
    print("[PASS] 현행 연구 상태 문서 동기화 파일 변경 확인 (내용의 진실성은 별도 검토 필요)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

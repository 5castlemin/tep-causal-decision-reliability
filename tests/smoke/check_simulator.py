"""사용자가 제공한 실제 시뮬레이터 경로만 검사한다. 시뮬레이터를 설치·생성하지 않는다."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--sim-root", type=Path)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.sim_root is None or not args.sim_root.is_dir():
        result = {"status": "BLOCKED", "source_available": False,
                  "normal_run": "NOT_RUN", "fault_injection": "NOT_RUN",
                  "xmv_write": "NOT_RUN", "repeatability": "NOT_RUN",
                  "reason": "시뮬레이터 소스/API 경로를 확인하지 못함"}
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print("[BLOCKED] 시뮬레이터 소스/API가 없어 실제 가동·개입 smoke test를 실행하지 않음")
        return 2
    result = {"status": "PARTIAL", "source_available": True,
              "normal_run": "NOT_RUN", "fault_injection": "NOT_RUN",
              "xmv_write": "NOT_RUN", "repeatability": "NOT_RUN",
              "reason": "소스 경로만 확인됨. 실행 명령과 인터페이스 검증 필요"}
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print("[PARTIAL] 소스 경로 발견; 실제 실행은 별도 명령·환경 검토 후 수행")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

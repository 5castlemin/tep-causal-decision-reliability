"""Render/check current dashboards from one explicit state record.

Checks consistency only; cannot establish scientific truth from a status label.
"""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def render(state):
    items = state["workstreams"]
    ids = [x["id"] for x in items]
    if len(ids) != len(set(ids)):
        raise ValueError("중복 작업 ID")
    for x in items:
        if x["status"] not in {"VERIFIED", "PARTIAL", "BLOCKED", "NOT_RUN", "PROPOSED"}:
            raise ValueError("정의되지 않은 상태")
        if not x["evidence"] or any(dep not in ids for dep in x["depends_on"]):
            raise ValueError("근거 또는 의존성 오류")
    priorities = state["priority_order"]
    if len(priorities) != len(set(priorities)) or not set(priorities) <= set(ids):
        raise ValueError("중복/알 수 없는 우선순위")
    by_id = {x["id"]: x for x in items}
    status = ["# 프로젝트 현재 상태", "", f"기준일: {state['checked_at']}. 현재 상태는 이 표와 `docs/research_state.json`에만 정의한다.",
              "과거 문서는 `docs/history/`, 시간순 기록은 `WORK_LOG.md`에 보존한다. 외부 PR의 증거는 병합 여부를 명시한다.", "",
              "| ID | 연구 흐름 | 상태 | 근거 | 다음 행동 |", "|---|---|---|---|---|"]
    for x in items:
        status.append(f"| {x['id']} | {x['title']} | {x['status']} | {x['evidence']} | {x['next_action']} |")
    status += ["", "실행 코드 회수, frozen 산출물 검사, 인과발견 재실행, 관측 적합, 독립 개입 검증을 서로 다른 완료 단계로 취급한다.",
               "이 표의 일관성 검사가 연구 결과의 진실성을 보증하지는 않는다."]
    priority = ["# 연구 우선순위", "", f"기준일: {state['checked_at']}. 담당자·기한은 아직 배정하지 않았다.", "", "## 다음 가장 중요한 작업 3개", ""]
    for n, key in enumerate(priorities[:3], 1):
        x = by_id[key]
        priority.append(f"{n}. **{key} — {x['title']}**: {x['next_action']} ({x['status']})")
    priority += ["", "## 전체 실행 대기열", "", "| ID | 상태 | 선행 조건 | 다음 행동·완료 증거 |", "|---|---|---|---|"]
    for key in priorities:
        x = by_id[key]
        priority.append(f"| {key} | {x['status']} | {', '.join(x['depends_on']) or '없음'} | {x['next_action']} / {x['acceptance']} |")
    priority += ["", "## ID 이력", "", *[f"- {line}" for line in state["id_history"]], "", "새 알고리즘·비선형 탐색과 기존 과제 재선정은 현재 작업 범위에 포함하지 않는다."]
    return {"PROJECT_STATUS.md": "\n".join(status)+"\n", "PRIORITIES.md": "\n".join(priority)+"\n"}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--write", action="store_true")
    args = p.parse_args()
    state = json.loads((ROOT / "docs/research_state.json").read_text(encoding="utf-8-sig"))
    for name, content in render(state).items():
        path = ROOT / name
        if args.write:
            path.write_text(content, encoding="utf-8")
        elif path.read_text(encoding="utf-8-sig") != content:
            raise ValueError(f"구형/중복 상태 또는 수동 변경: {name}; state JSON 확인 후 --write")
    print("[PASS] 현재 상태·의존성·우선순위 ID 유일성·상단 문서 일치")


if __name__ == "__main__":
    main()

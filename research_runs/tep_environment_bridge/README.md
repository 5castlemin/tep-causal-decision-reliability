# TEP 환경 계약과 최소 기술 시험

2026-10-27. PR17 `a41683b` 기반 후속 작업. 기존 PR15~17 병합 없음.

- `PLAN_v1.json`/`.sha256`: 실행 전 로컬 고정. 8fresh runs×6steps, manual/closed 기준·+0.1pp 및 uninstrumented repeat.
- `technical_v1/`: 실제 원시 상태/센서/명령/제어기/RNG, 시계, source14파일hash, 환경·실패 상태. 학습자료/독립 평균효과 평가 아님.
- `CLOSURE_PLAN_v1.json`/`closure_v1/`: 기존 ±0.001pp valve-state만 바꾼3고정점. 현재 센서41/명령12 동일인데 W 변화율이 다른 국소 반례. rollout0, GT생성0.
- `contracts/`: software-only 합성 schema fixture와 실제 Python 부분/benchmark 미확정 metadata. 새 합성 데이터 아님.
- `CONTRACT_RESULTS.json`: 15개 명시 사례의 구조화된 거부/기술정합성 결과. 물리 승인 아님.
- `validation/`: 실제 실행 검사 로그. 외부 source 없는 CI 검산과 로컬 source 실행을 분리.

재현:
```text
python -X utf8 -m unittest tests.test_environment_contract -v
python -X utf8 scripts/validate_environment_contract.py
python -X utf8 scripts/run_tep_environment_bridge.py --source <pinned-checkout> --output <fresh-output>
python -X utf8 scripts/check_tep_observation_closure.py --source <pinned-checkout> --output <fresh-output>
```
외부 source는 `9a6c8e5fcef4a2850778704e7793c87b0a187005`와 기존4SHA 모두 일치해야 한다. source 변경/기존 output 덮어쓰기/가짜 source 대체는 금지. 기존 standalone Python3.11.15/NumPy1.26.4로 실제 실행했다. 외부라이브러리 재설치 없음.

보고서: `docs/research_design/TEP_ENVIRONMENT_BRIDGE_FEASIBILITY.md`.
결론: 원래 전체 구조–효과 연구는 NO-GO. metadata 검사 통과가 물리적 동일성 증명이 아니다. 다음 밸브 전이식 계약 검산은 제안이며 아직 실행하지 않았다.

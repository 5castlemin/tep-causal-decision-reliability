# 밸브 전이·동적 참조 범위 결정

기준 PR18 `2a03e1d`, 새 feature는 그 위의 후속 작업. 기존 PR15~18 병합 없음.

- `PLAN_v1.json`/SHA: source 실행 전 로컬 고정. 수동·무Fault 두 arm×두 step,양의시간 명령+.001pp.
- `run_v1/`: 실제 cache 전후·평가 명령·상태·미분·시간/단위·제어기·종료 상태 및 원source4SHA/환경. 최대4개새step만 실행.
- `RECHECKS.json`: 24개 기존 대수식 residual(적용cache 미기록으로 full contract BLOCKED),3기존고정점 차분,12모의입력 거부. 과거자료/기대값변경 없음.
- `SCOPE_PROPOSAL.json`: 사용자에게 제시할 B 제한 내부 동적 연구 설계안. 새GT/graph 파일/학습승인 아님.
- `validation/`: 실제 단위검사/기존검증/상태검사 로그. 새source 실행과 저장기록 검산을 구분.

명령:
```text
python -X utf8 scripts/validate_tep_valve_transition_contract.py
python -X utf8 -m unittest tests.test_tep_valve_transition -v
python -X utf8 scripts/validate_tep_valve_transition_contract.py --source <fixed-checkout> --output <fresh-output>
```
외부 source commit9a6c8e5fcef4a2850778704e7793c87b0a187005·기존4hash가 일치하고tracked clean이어야 한다. 실제Python3.11.15/NumPy1.26.4로 실행,재설치 없음. 새 output만 허용한다.

L1 VERIFIED는 정상밸브식 구현만. L2 PARTIAL,L3/L4 BLOCKED. 현재 연구의 다음 행동은 기술시험 추가가 아니라 내부상태·시간전개를 포함한 제한 설계안 검토 여부 결정이다. 공식GT/전체F1·제조복구·안전 결과를 만들지 않았다. 한국어판정: `docs/research_design/TEP_DYNAMIC_REFERENCE_DECISION.md`.

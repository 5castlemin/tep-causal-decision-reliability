# 연구 우선순위

기준일: 2026-10-23. 담당자·기한은 아직 배정하지 않았다.

## 다음 가장 중요한 작업 3개

1. **SRC-01 — Final 생성 코드 회수**: FREEZE.code의 algos/run_*.py 및 common/config.py·data_io.py 원본을 해시로 대조하여 회수 (BLOCKED)
2. **SIM-03 — 공개 후보 수치·shutdown 검증**: 1788초 종료 원인과 적분 step/Fortran 기준 동등성 조사 (PARTIAL)
3. **SIM-04 — 공개 후보 초기화 검증**: 동일 객체 reset 후 관측 불일치의 RNG/state/controller 원인 확인 (BLOCKED)

## 전체 실행 대기열

| ID | 상태 | 선행 조건 | 다음 행동·완료 증거 |
|---|---|---|---|
| SRC-01 | BLOCKED | 없음 | FREEZE.code의 algos/run_*.py 및 common/config.py·data_io.py 원본을 해시로 대조하여 회수 / 코드 원본 hash·의존성·실행 명령·frozen 재생성 일치 |
| SIM-03 | PARTIAL | 없음 | 1788초 종료 원인과 적분 step/Fortran 기준 동등성 조사 / 동일 조건 수치 수렴·종료 원인 원시 로그 |
| SIM-04 | BLOCKED | 없음 | 동일 객체 reset 후 관측 불일치의 RNG/state/controller 원인 확인 / reset 계약 및 재현 로그 |
| COMPAT-01 | PARTIAL | SIM-03, SIM-04 | 모델 revision·controller·운전모드·단위·전처리 계보 대조 / 변수 대응 이상의 모델 호환 근거 |
| SIM-01 | BLOCKED | 없음 | 당시 저장소 URL/ZIP·버전·실행 명령·로그의 구체 소재 확보 / 당시 구현 반복 정상 운전 로그 |
| SIM-02 | PARTIAL | SIM-03, SIM-04 | PR #2 검토 및 수치·reset 제한 해결 후 장기 운전 확인 / 30분 smoke 외 장기 운전·setpoint/override 검증 |
| DATA-01 | PARTIAL | 없음 | 고정 커밋 취득은 검증됨; 재배포 권리 추가 확인 / 권리 근거 확보 전 data/local 유지 |
| TASK-01 | BLOCKED | COMPAT-01, SIM-02 | 모델 호환 후 Fault/Action/Target·복구·안전 기준 사전 확정 / 결과 확인 전 버전된 과제 계약 |
| EFFECT-01 | NOT_RUN | TASK-01 | 확정 과제로 no-action 대비 동일 조건 실험 / 원시 trajectory·실패 포함 독립 평가 |
| PCMCI-ID | BLOCKED | 없음 | 동시점 순환의 인과계수 식별 근거 검토 / 별도 식별 방법 승인 전 primary fitting 보류 |

## ID 이력

- SIM-01은 기존 8월 구현 복구에만 사용한다.
- SIM-02는 PR #2 공개 후보의 인터페이스 smoke로 범위를 명확히 했다. 이전 단일 Gate와 구분한다.
- SIM-03·SIM-04·COMPAT-01은 PR #2 ID를 유지한다. SRC-01은 미회수 Final 코드에 한정한다.
- 중복된 하단 우선순위 추가 문단을 제거하고 과거 본문은 docs/history/에 보존했다.
- 임시 PR #2+#3 통합에서 GRAPH-GEN을 별도 표시하여 산출물 평가 VERIFIED와 생성 학습 BLOCKED를 명확히 구분했다.

새 알고리즘·비선형 탐색과 기존 과제 재선정은 현재 작업 범위에 포함하지 않는다.

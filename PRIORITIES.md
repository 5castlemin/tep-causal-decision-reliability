# 연구 우선순위

기준일: 2026-10-23. 담당자·기한은 아직 배정하지 않았다.

## 다음 가장 중요한 작업 3개

1. **COMPAT-01 — 공개 후보와 기존 데이터/GT 대응**: 고정 정상 원시 파일·timestamp/seed·median export 코드 및 model flag 회수; 공식 archive 운전점 근접은 정적 단서만 확인 (PARTIAL)
2. **BENCH-ENV — 공식 수정 TEP 복원 환경**: 회수 temexd_mod source에 맞는 MATLAB/Simulink 실행 위치·버전·권리 확인; 현재 PATH 명령 미확인, 실행 NOT_RUN (BLOCKED)
3. **SRC-01 — Final 생성 코드 회수**: FREEZE.code의 algos/run_*.py 및 common/config.py·data_io.py 원본을 해시로 대조하여 회수 (BLOCKED)

## 전체 실행 대기열

| ID | 상태 | 선행 조건 | 다음 행동·완료 증거 |
|---|---|---|---|
| COMPAT-01 | PARTIAL | SIM-03, SIM-04 | 고정 정상 원시 파일·timestamp/seed·median export 코드 및 model flag 회수; 공식 archive 운전점 근접은 정적 단서만 확인 / timestamp/구간·초깃값·제어기·sampling 연결과 실제 반복·개입 확인 전 직접 효과 정답 NO-GO |
| BENCH-ENV | BLOCKED | 없음 | 회수 temexd_mod source에 맞는 MATLAB/Simulink 실행 위치·버전·권리 확인; 현재 PATH 명령 미확인, 실행 NOT_RUN / 현재 archive와 실제 benchmark 사용 설정 대응 후 사전 계획된 짧은 정상 반복 및 시간·제어 검증 |
| SRC-01 | BLOCKED | 없음 | FREEZE.code의 algos/run_*.py 및 common/config.py·data_io.py 원본을 해시로 대조하여 회수 / 코드 원본 hash·의존성·실행 명령·frozen 재생성 일치 |
| SIM-03 | PARTIAL | 없음 | 압력 한계 종료와 제한적 dt 수렴 확인; 동일 모델·controller 독립 기준 대조 및 폐루프 시간 계약 검증 / 기준 구현 동일 조건·관측 시계 비교 및 수치 오차 범위; 현재 효과 정답 사용 보류 |
| SIM-01 | BLOCKED | 없음 | 당시 저장소 URL/ZIP·버전·실행 명령·로그의 구체 소재 확보 / 당시 구현 반복 정상 운전 로그 |
| SIM-02 | PARTIAL | SIM-03, SIM-04 | 2시간 정상 실행 추가 확인; 수치 기준·controller/override·호환성 제한 해결 뒤 Gate 재평가 / 30분 smoke 외 장기 운전·setpoint/override 검증 |
| DATA-01 | PARTIAL | 없음 | 고정 커밋 취득은 검증됨; 재배포 권리 추가 확인 / 권리 근거 확보 전 data/local 유지 |
| TASK-01 | BLOCKED | COMPAT-01, SIM-02 | 모델 호환 후 Fault/Action/Target·복구·안전 기준 사전 확정 / 결과 확인 전 버전된 과제 계약 |
| EFFECT-01 | NOT_RUN | TASK-01 | 확정 과제로 no-action 대비 동일 조건 실험 / 원시 trajectory·실패 포함 독립 평가 |
| PCMCI-ID | BLOCKED | 없음 | 동시점 순환의 인과계수 식별 근거 검토 / 별도 식별 방법 승인 전 primary fitting 보류 |

## ID 이력

- SIM-01은 기존 8월 구현 복구에만 사용한다.
- SIM-02는 PR #2 공개 후보의 인터페이스 smoke로 범위를 명확히 했다. 이전 단일 Gate와 구분한다.
- SIM-03·SIM-04·COMPAT-01은 PR #2 ID를 유지한다. SRC-01은 미회수 Final 코드에 한정한다.
- 중복된 하단 우선순위 추가 문단을 제거하고 과거 본문은 docs/history/에 보존했다.
- 승인된 PR #2+#3 통합 검증에서 GRAPH-GEN을 별도 표시하여 산출물 평가 VERIFIED와 생성 학습 BLOCKED를 명확히 구분했다.
- SIM-04는 2026-10-23 새 객체 초기화 재현 계약 VERIFIED로 범위를 명확히 했다. 같은 객체 reset 비트 일치는 보장하지 않는다. SIM-03/COMPAT-01은 PARTIAL 유지.
- Benchmark 결정 Gate에서 BENCH-ENV를 별도로 추가했다. 기존 SIM-03 수치 신뢰성과 공식 수정 모델 복원환경을 구분한다. A/B/C 연구 전환은 확정하지 않았다.

새 알고리즘·비선형 탐색과 기존 과제 재선정은 현재 작업 범위에 포함하지 않는다.

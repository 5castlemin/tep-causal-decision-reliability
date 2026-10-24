# 연구 우선순위

기준일: 2026-10-24. 담당자·기한은 아직 배정하지 않았다.

## 다음 가장 중요한 작업 3개

1. **ENV-MVP — 구조·추천 평가환경 대응**: 예제 IID FCM의 GT/관측/do acceptance 통과. 제조 generator/연구 환경 채택은 별도 승인; 시계·짝지은 잡음 한계 유지 (PARTIAL)
2. **POLICY-MVP — 실제 추천 정책 연결**: 예제 연결 파일럿의 범위·noise 가정·목표·비용·Action 경계·분포수준 기준정책을 사전 고정하고 실행 승인 (BLOCKED)
3. **EVAL-MVP — 구조 지표–추천 성능 비교**: 승인 후 동일 새 관측 데이터에서 PC/BOSS/Direct 학습과 공통 Ridge 연결. Gaussian fixture의 가정 차이 명시; 과거 F1 혼합 금지 (BLOCKED)

## 전체 실행 대기열

| ID | 상태 | 선행 조건 | 다음 행동·완료 증거 |
|---|---|---|---|
| ENV-MVP | PARTIAL | 없음 | 예제 IID FCM의 GT/관측/do acceptance 통과. 제조 generator/연구 환경 채택은 별도 승인; 시계·짝지은 잡음 한계 유지 / 예제 계약과 broader 연구 채택 구분; 제조/동적/TEP 동등성 자동 승격 금지 |
| POLICY-MVP | BLOCKED | ENV-MVP | 예제 연결 파일럿의 범위·noise 가정·목표·비용·Action 경계·분포수준 기준정책을 사전 고정하고 실행 승인 / 무차원 Action에 TEP 제약 이식 없이 공통 추천/독립 do 평가 contract |
| EVAL-MVP | BLOCKED | ENV-MVP, POLICY-MVP | 승인 후 동일 새 관측 데이터에서 PC/BOSS/Direct 학습과 공통 Ridge 연결. Gaussian fixture의 가정 차이 명시; 과거 F1 혼합 금지 / 별도 graph-fit/holdout batch의 실제 학습·정책·평가 로그; 지금은 미실행 |
| REF-B | PARTIAL | 없음 | 최소 내부 상태식 검산 완료; 관측 projection/비간선/알고리즘 의미의 외부 방법론 검토 전 추가 GT·실험 중단 / 기존 discovery와 동일한 참조 정의·불확실/음성 쌍·채점 계약 검토; 현재 전체 Q2 BLOCKED |
| SIM-B | PARTIAL | 없음 | 5초 밸브/3step cascade/관측 cache 순서 확인; 방법론 문제 해결 전 장기·Fault 실험 확장 보류 / 관측 정의 일치 후에만 정책·잡음·horizon의 별도 사전 계약 |
| DESIGN-B | BLOCKED | REF-B, SIM-B | 관측 수준 참조가 불가하면 원가설 보류/국소 도달성으로 범위 축소 대안을 검토; 전환은 사용자 승인 대상 / 독립 graph-fit·과제 family·평가 seed의 비교 계약과 유지/축소/보류 의사결정 |
| COMPAT-01 | PARTIAL | SIM-03, SIM-04 | 합법적 IEEE 계정으로 3_Normal Steady-State.zip 회수 후 목록·SHA·실제 시간축/seed 확인; 기술문서만 회수됨 / 정상 ZIP 원본·권리·선택 run 및 timestamp/seed 실재 확인; 직접 효과 정답 NO-GO 유지 |
| BENCH-ENV | BLOCKED | 없음 | 승인된 MATLAB/Simulink 위치·버전·라이선스 확보; PATH/registry/제품/일반 경로 탐색은 미발견, 라이선스 조회·로딩 NOT_RUN / 합법 환경에서 사본 .mdl/MAT 실제 로딩·MEX 검증 후 사전 계획된 정상 반복 |
| EXPORT-01 | BLOCKED | COMPAT-01 | 원시 run·median stride/경계·1499행 생성 코드를 회수; 불가 시 전환 대안의 승인 요청만 준비 / timestamp와 1499×31 값의 재현 연결 또는 복원 불가 근거 및 별도 연구 설계 승인 |
| SRC-01 | BLOCKED | 없음 | FREEZE.code의 algos/run_*.py 및 common/config.py·data_io.py 원본을 해시로 대조하여 회수 / 코드 원본 hash·의존성·실행 명령·frozen 재생성 일치 |
| SIM-03 | PARTIAL | 없음 | 압력 한계 종료와 제한적 dt 수렴 확인; 동일 모델·controller 독립 기준 대조 및 폐루프 시간 계약 검증 / 기준 구현 동일 조건·관측 시계 비교 및 수치 오차 범위; 현재 효과 정답 사용 보류 |
| SIM-01 | BLOCKED | 없음 | 당시 저장소 URL/ZIP·버전·실행 명령·로그의 구체 소재 확보 / 당시 구현 반복 정상 운전 로그 |
| SIM-02 | PARTIAL | SIM-03, SIM-04 | 기존 2시간 정상 기록 보존; controller/override·수치 기준·호환성 제한 해결 뒤 Gate 재평가 / 30분 smoke 외 장기 운전·setpoint/override 검증 |
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
- Track A Gate에서 EXPORT-01을 추가해 원시 ZIP 접근과 실제 CSV export 연결을 구분했다. 기존 ID/실험 상태는 유지한다.
- 2026-10-24 REF-B/SIM-B/DESIGN-B는 Track B 채택 전 타당성 조건이다. Track A 차단을 해제하거나 연구 전환을 뜻하지 않는다.
- 2026-10-24 REF-B PARTIAL은 내부 물리 블록의 한 점 구현 검산만 뜻한다. 전체 Q2 BLOCKED/Track B NO-GO 유지, 추가 GT 후보/실험은 중단한다.
- MVP-TECH는 실행 검증만 VERIFIED. ENV/POLICY/EVAL-MVP는 원래 지표–추천 성능 질문의 선결 단계다. REF-B 등 과거 ID와 차단 근거를 보존한다.
- ENV-EXAMPLE VERIFIED는 별도 승인된4노드IID fixture만 뜻한다. ENV-MVP는 broader 채택 미승인으로 PARTIAL; POLICY/EVAL 학습은 미실행이다.

새 알고리즘·비선형 탐색과 기존 과제 재선정은 현재 작업 범위에 포함하지 않는다.

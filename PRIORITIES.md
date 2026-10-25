# 연구 우선순위

기준일: 2026-10-25. 담당자·기한은 아직 배정하지 않았다.

## 다음 가장 중요한 작업 3개

1. **EVAL-MVP — 구조 지표–추천 성능 비교**: 주 비교 ΔMAE .014264 지지는 유지하되 M0 이후/연결F1 이후 추가 정보와 이론 평균·비용 .4에서의 불확실성을 새 사전 계약으로 분리 (PARTIAL)
2. **POLICY-MVP — 실제 추천 정책 연결**: 순환 PC출력2개·양립 DAG 없는3개에 대한 사전 실패/보류 정책과 선택 편향 대조를 정의. 현재 간선 수정·손실 임의 대입 금지 (PARTIAL)
3. **PILOT-CONFIRM — 12개 규칙 생성 구조의 독립 확인·방법론 대조**: 이론 평균 Δ .006317/고비용 Δ .004874의 불명확성과 유한 표본 최선후보15/96변경을 반영한 정밀도·교정 계약; 현재 결과 사후 변경 없음 (PARTIAL)

## 전체 실행 대기열

| ID | 상태 | 선행 조건 | 다음 행동·완료 증거 |
|---|---|---|---|
| EVAL-MVP | PARTIAL | ENV-MVP, POLICY-MVP | 주 비교 ΔMAE .014264 지지는 유지하되 M0 이후/연결F1 이후 추가 정보와 이론 평균·비용 .4에서의 불확실성을 새 사전 계약으로 분리 / 새 자료로 조정하지 않은 모형 비교·효과크기/과제·외삽 보정의 독립 검증; 현12구조 결과만으로 지표 우월성 주장 금지 |
| POLICY-MVP | PARTIAL | ENV-MVP | 순환 PC출력2개·양립 DAG 없는3개에 대한 사전 실패/보류 정책과 선택 편향 대조를 정의. 현재 간선 수정·손실 임의 대입 금지 / 적합 불가와 경로 부재 기준대체를 구분한 공통 운영계약 및 미확정 표현별 비교. 고정조작/경로보존 대조는 수행됐으나 인과적 분리 완료 아님 |
| PILOT-CONFIRM | PARTIAL | PILOT-DIVERSE, POLICY-MVP | 이론 평균 Δ .006317/고비용 Δ .004874의 불명확성과 유한 표본 최선후보15/96변경을 반영한 정밀도·교정 계약; 현재 결과 사후 변경 없음 / 144재현PASS/12 FCM검증/216그래프 중214SCM/5088평가/184320 do 수행. 일차 지지와 종합 추가정보 미확인·실패선택편향을 구분 |
| PILOT-REPEAT | VERIFIED | PILOT-IID | 기존12데이터/36학습 결과 보존. 새8구조 결과는 PILOT-DIVERSE로 분리하며 과거 수치와 혼합하지 않음 / 12데이터/36학습/432정책행/55296 do 원시 식·통계·고정추천·해시 검사. 제조 가설 입증 아님 |
| ENV-MVP | PARTIAL | 없음 | 검증된 합성 범위를 유지하고 제조 환경의 노드·직접 구조·do 의미가 같은지 입증할 채택 계약을 분리; 제조 채택 미승인 / 예제 계약과 broader 연구 채택 구분; 제조/동적/TEP 동등성 자동 승격 금지 |
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
- 2026-10-24 PILOT-IID 신규: 사용자 명시 실행 지시로 두 잡음군 합성 통합만 VERIFIED. POLICY/EVAL-MVP는 해당 진전 PARTIAL이며 제조 가설 입증·Track B 채택 아님. env_acceptance/decision_mvp는 과거 실행 불변 기록이다.
- 2026-10-24 사용자 승인으로 PR6~11 순차 일반 merge, main34b8dbe에서 PILOT-REPEAT 신규.12독립 데이터·36학습·4과제·3정책 실제 평가만 VERIFIED. 공식 지표 우월성/제조/Recovery/Safety는 미검증이며 POLICY/EVAL-MVP PARTIAL 유지.
- 2026-10-24 PILOT-DIVERSE 추가: 미병합 PR12 위에서 사용자 명시 승인된8개 합성 구조의144학습·918평가와8fold LOSO 실행만 VERIFIED. EVAL/POLICY는 지표 우월성/제조 검증 미완료로 PARTIAL, 기존 protocol 수치/상태기록 보존.
- 2026-10-25 PILOT-CONFIRM 추가: 기존8구조144재현과 새12구조216시도/214SCM를 구분. PILOT-DIVERSE 현재 replay만 실제 증거로 갱신하고 과거 보고서·원시는 보존.

새 알고리즘·비선형 탐색과 기존 과제 재선정은 현재 작업 범위에 포함하지 않는다.

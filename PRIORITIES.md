# 연구 우선순위

기준일: 2026-10-29. 담당자·기한은 아직 배정하지 않았다.

## 다음 가장 중요한 작업 3개

1. **MFG-MICRO — CausalMan micro 실제 수용 검사**: CONDITIONAL_NOT_ACCEPTED:관측-only 점효과 식별 조건 유지 여부를 결정.현재 고정 micro를 학습/추천에 연결하지 않으며 자동 패치·재실행 없음 (PARTIAL)
2. **ERROR-CONFIRM — 오류 위치 독립 계약: 정밀도·자원 결정 필요**: REDESIGN_REQUIRED:반폭0.1의독립SCM자원확대여부또는확인확대종료를결정. 신규실행/자동검사·문서루프없음 (PARTIAL)
3. **PATH-PRECISION — 추가 예측력 독립 확인 정밀도·예산**: 이번 저차원 모형 정밀도 거친 추정132구조/1188학습으로30/288 초과. 과거150추정 보존; 작은 정보와 실제 의사결정 이득을 분리한 후속 계약 (BLOCKED)

## 전체 실행 대기열

| ID | 상태 | 선행 조건 | 다음 행동·완료 증거 |
|---|---|---|---|
| MFG-MICRO | PARTIAL | MFG-INTEGRATED | CONDITIONAL_NOT_ACCEPTED:관측-only 점효과 식별 조건 유지 여부를 결정.현재 고정 micro를 학습/추천에 연결하지 않으며 자동 패치·재실행 없음 / hard-do 그래프 부모 삭제 결함과 참조/효과 식별 계약이 남음.외부 import·관측1/do16000 1완료,do30000중단·replay미실행;공식채택아님 |
| ERROR-CONFIRM | PARTIAL | ERROR-DIAG | REDESIGN_REQUIRED:반폭0.1의독립SCM자원확대여부또는확인확대종료를결정. 신규실행/자동검사·문서루프없음 / 대응손실계약고정;미해결2개는정밀도-구조예산및종단실행비용근거.30개반폭0.446/유지15개0.742;구조단위598/유지총1650근사. 신규SCM/적합/do0 |
| PATH-PRECISION | BLOCKED | PATH-MODEL | 이번 저차원 모형 정밀도 거친 추정132구조/1188학습으로30/288 초과. 과거150추정 보존; 작은 정보와 실제 의사결정 이득을 분리한 후속 계약 / 실행 가능한 사전 정밀도·구조 수·예산 계약; 유리한 결과를 위한 기준 완화 금지 |
| COMPAT-01 | PARTIAL | SIM-03, SIM-04 | 기존benchmark/Python직접결합NO-GO·계보미확보유지. 현TEP효과경로동결;새로운구체증거/지시없으면재검색하지않음 / 정상 ZIP 원본·권리·선택 run 및 timestamp/seed 실재 확인; 직접 효과 정답 NO-GO 유지 |
| PATH-MODEL | PARTIAL | EVAL-MVP | 고정9후보 중첩 검증은 기본19/경로1 선택. 품질 특징 추가가 이득 아님. 단순 기본모형을 개발 기준선으로 유지하고 MAE 탐색 확장 중단 / 구조 단위 검증·특징 선택 누출 검사·고정 모형 산출물 |
| PATH-CONFIRM | NOT_RUN | PATH-PRECISION, POLICY-MVP | 정밀도 통과 후에만 새 구조·계수·seed·M0~M6·실패 정책을 고정하고 실제 학습/do 실행 / 기존20구조 미사용의 확인 코호트, 추천 고정 후 이론/실제 do 평가, 구조 단위 구간 |
| EVAL-MVP | PARTIAL | ENV-MVP, POLICY-MVP | 낮은F1을 사후튜닝하지 않음. 7graph/84과제·198쌍 검산을 구조 진단으로 유지하고 제조 효과와 결합 금지; 참조·환경계약 선결 / 오류 위치·효과/선택 분리와 제조 동일환경의 참조·관측·do 계약; 합성 개발 결과로 제조 주장 금지 |
| POLICY-MVP | PARTIAL | ENV-MVP | 실패24행은 기준 조작0의 실제 이론 손실로 운영 평가; 가용2136/2160·조건부·계산추천1326 분리 유지 / 실패/경로부재/계산된 기준/방향보류 구분 및 새 확인 정책 사전 고정 |
| PILOT-CONFIRM | PARTIAL | PILOT-DIVERSE, POLICY-MVP | 과거12구조 독립 확인 기록 보존. C01~C12는 이후 모형 개발에 사용됐으므로 새 확인용으로 재사용하지 않음 / 144재현PASS/12 FCM검증/216그래프 중214SCM/5088평가/184320 do 수행. 일차 지지와 종합 추가정보 미확인·실패선택편향을 구분 |
| PILOT-REPEAT | VERIFIED | PILOT-IID | 기존12데이터/36학습 결과 보존. 새8구조 결과는 PILOT-DIVERSE로 분리하며 과거 수치와 혼합하지 않음 / 12데이터/36학습/432정책행/55296 do 원시 식·통계·고정추천·해시 검사. 제조 가설 입증 아님 |
| ENV-MVP | PARTIAL | 없음 | 검증된 합성 범위를 유지하고 제조 환경의 노드·직접 구조·do 의미가 같은지 입증할 채택 계약을 분리; 제조 채택 미승인 / 예제 계약과 broader 연구 채택 구분; 제조/동적/TEP 동등성 자동 승격 금지 |
| REF-B | PARTIAL | 없음 | 최소 내부 상태식 검산 완료; 관측 projection/비간선/알고리즘 의미의 외부 방법론 검토 전 추가 GT·실험 중단 / 기존 discovery와 동일한 참조 정의·불확실/음성 쌍·채점 계약 검토; 현재 전체 Q2 BLOCKED |
| SIM-B | PARTIAL | 없음 | 5초 밸브/3step cascade/관측 cache 순서 확인; 방법론 문제 해결 전 장기·Fault 실험 확장 보류 / 관측 정의 일치 후에만 정책·잡음·horizon의 별도 사전 계약 |
| DESIGN-B | BLOCKED | REF-B, SIM-B | 관측 수준 참조가 불가하면 원가설 보류/국소 도달성으로 범위 축소 대안을 검토; 전환은 사용자 승인 대상 / 독립 graph-fit·과제 family·평가 seed의 비교 계약과 유지/축소/보류 의사결정 |
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
| ENV-CONTRACT | VERIFIED | MFG-VALIDITY | 15개 계약 사례·실제 파일 해시 검사 완료. 새 join은 environment_contract.require_environment_contract 사용. 과학적 동등성 승인은 아님 / 같은 이름의 controller/시계/조작/노드/참조 불일치·미검증 근거 거부. CPCaD/Python 결합 계속 차단 |
| TEP-BRIDGE | PARTIAL | ENV-CONTRACT, REF-B | 실제cache4step 추가로 좁은전이식 확인. 센서 직접/음성참조 미확정으로 L3/L4 BLOCKED; 연구설계 선택을 우선 / 명령/밸브/센서 시계·잡음·초기화 분리. 연구join NO-GO 유지 |
| VALVE-TRANSITION | VERIFIED | TEP-BRIDGE | L1 정상 cache 전이만 검증 완료. 같은기술반복 종료; DYNAMIC-SCOPE에서 내부상태·시간전개 연구설계 검토 여부 결정 / 실제2arm/4step cache 전후·미분/Euler 시간단위 일치. 기존24step cache 미기록 차단,3고정점 재검산,12모의 거부. 전체GT/F1 아님 |
| MFG-EFFECT-SCOPE | BLOCKED | DYNAMIC-SCOPE | STOP-TEP-EFFECT-TRACK:현재경로동결. 추가TEP시험·패치·후속검토문서권고없음. SYNTH-FINAL로현재우선순위이동 / 최대2후보비교/1선택. 출처있는정책집합·비자명한목표/H·실패포함선택손실을정당화못함; API반응성/GT부재와구분 |
| DYNAMIC-SCOPE | BLOCKED | VALVE-TRANSITION, REF-B | B축약계약판정2·미채택초안보존. 이후효과중심검토도STOP이므로추가TEP설계확대중단 / 4node/12미채점후보·부모폐쇄/비간선/발견대상/비자명선택/독립평가의 미충족조건 명시. 공식연구설계변경 아님 |
| SYNTH-FINAL | VERIFIED | ERROR-DIAG, PILOT-CONFIRM | 분모/모형버전/확인당시와재사용개발을구분한최종Results·Discussion보존. 다음은ERROR-CONFIRM의독립오류대조계약/예산결정;실행승인아님 / A/D/E범위내지지,C/B1부분지지,B2추가정보미확립,F제조미검증.162쌍93/4/65·114경로유지48/3/63;새학습/do0 |

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
- 2026-10-25 PATH-MODEL/PATH-PRECISION/PATH-CONFIRM 추가: 기존 EVAL-MVP를 삭제하지 않고 개발 안정성·정밀도 차단·새 독립 확인 미실행을 분리. PR12~14 실제 병합 반영.
- 2026-10-25 ERROR-DIAG/ERROR-CONFIRM: 목적을 지표 우세/MAE 최적화와 분리. 오류–응답–선택 대조 완료와 새 독립 계약 미실행을 구분하며 제조 환경 정합성 검토를 우선.
- 2026-10-27 MFG-VALIDITY 감사완료와 ENV-CONTRACT 제안분리. 제조GO/학습재실행으로승격안함. 다음한작업은외부환경없이가능한 metadata fail-closed검사구현.
- 2026-10-27 ENV-CONTRACT 구현 VERIFIED는 metadata 소프트웨어만. TEP-BRIDGE PARTIAL: 실제8×6step·3고정점. VALVE-TRANSITION 제안은 별도 다음 작업. 전체 제조 구조–효과 NO-GO 유지.
- 2026-10-27 VALVE-TRANSITION VERIFIED는4실제cache-step의정상수치전이만. L2 PARTIAL/L3·L4 BLOCKED. 동일기술반복을종료하고DYNAMIC-SCOPE의사용자설계선택으로이동. 새GT/연구전환미승인.
- 2026-10-27 사용자승인은B설계검토만. DYNAMIC-SCOPE 초안은PROPOSED_FOR_REVIEW/판정2(미정당화),공식채택없음. MFG-EFFECT-SCOPE는별도효과중심설계검토결정으로분리;실행/GT승인아님.
- 2026-10-28 MFG-EFFECT-SCOPE 설계검토완료/STOP-TEP-EFFECT-TRACK(BLOCKED/FROZEN). B/C자동채택없음. DYNAMIC-SCOPE도실행차단지속,과거미채택초안불변. 다음은SYNTH-FINAL의기존합성결과최종주장정리;새실험승인아님.
- 2026-10-29 SYNTH-FINAL은기존결과통합분석완료VERIFIED이며원래가설확증완료아님. C01..C12는과거확인/현재개발구분. B1사전지지보존·B2안정추가정보미확립. TEP동결유지/새실험0.
- 2026-10-29 ERROR-CONFIRM 단일사전계약·예산검토완료/PARTIAL,REDESIGN_REQUIRED. PATH-PRECISION의MAE와별개Δ선택손실0.1폭계획. 신규실험없음;자원범위결정전실행안함.
- 2026-10-29 MFG-INTEGRATED는새대체후보의정적탐색/PARTIAL.CausalMan CONDITIONAL-CANDIDATE,실제GT/관측/do연결미검증.기존TEP STOP/ERROR-CONFIRM REDESIGN 및연구A원시·예산불변.공식채택/실행승인아님.

새 알고리즘·비선형 탐색과 기존 과제 재선정은 현재 작업 범위에 포함하지 않는다.

# 의사결정 이력

| 시점 | 결정 또는 제안 | 근거 | 채택하지 않은 대안·재검토 조건 |
|---|---|---|---|
| 2026-08-23 보고 | 시뮬레이터 연동과 반사실 추천을 지향 | 방학 스터디 보고서 | 현재 실행 자료가 없어 완료 상태로 승격하지 않음. 소스·로그 확보 시 재검토 |
| 2026-10-05~06 | 7개 최종 그래프와 Step 6 엄격 평가 보존 | Final ZIP, Step 6 CSV·FREEZE | GT 성능으로 그래프를 사후 수정하지 않음 |
| 2026-10-06 | 198→65→12 구조 평가 후보 기록 | GT·변수 대응·사람이 고른 대표 목록·자동 유효성 검사 | 12개를 실제 복구 과제로 간주하지 않음. 시뮬레이터 확인 시 별도 과제 확정 |
| 2026-10-06 | 정적 4개는 확정 방향만, VarLiNGAM·DYNOTEARS는 원래 시차 구조, PCMCI+는 보류 | 순환/시차 감사 | 미확정 간선 자동 방향화·순환 간선 임의 삭제를 기각. 인과적 식별 근거가 생기면 재검토 |
| 2026-10-06 | 선형 가산 SCM·공통 Ridge 격자·동일 목표 행·시간순 분할 설계 | 최종 학습 전 freeze | 비선형 모델은 파일럿 성공 뒤 민감도 분석. 실제 적합과 별개 |
| 2026-10월 중순 이후 | 전체 정확도 대 경로 정확도에서 여러 구조 지표의 유용성 비교로 **질문 확대 제안** | 구조 지표 순위 불일치와 팀 연구방향 문서 | 후속 성능 미측정이므로 설명력 결론 없음. 파일럿 실행 가능성에 따라 범위 축소 |
| 2026-10-23 | 실제 개입 전 1과제·정적 3그래프 파일럿 우선, 현 단계에서는 정상상태 수치 적합만 기록 | 시뮬레이터 소스/API 미확보, 기존 결과 감사 | 12과제 일괄 실험·알고리즘 확장을 보류. Gate A 재현 후 갱신 |
| 2026-10-23 | 공개 Python simulator 후보를 기존 8월 구현과 별도로 smoke 검증 | `docs/audit/SIMULATOR_FEASIBILITY_REPORT.md` | 30분 실행 성공을 장기 안정성·기존 GT 개입 정답으로 승격하지 않음. 수치·reset·controller 호환 관문 필요 |

| 2026-10-23 | 공개 후보의 반복 단위는 동일 source/backend/seed/mode의 새 객체 | `docs/audit/SIMULATOR_RELIABILITY_REPORT.md` 및 reset 10경우 | fresh twin 경로 exact, 같은 객체 운전 후 reset 관측 약 1e-12 차이. 관측값 강제 복원·원본 패치 기각 |
| 2026-10-23 | 관측 시계와 Euler 상태 시계를 별도 기록 | `experiments/simulator/diagnostics/run_20261023_aligned` | 추가 evaluate 호출 없이 공통 시각 비교. 기존 CSV에 누락된 상태를 소급 생성하지 않음 |
| 2026-10-23 | 후보 내부 탐색 CONDITIONAL / benchmark 개입 정답 직접 사용 NO-GO | 3 dt 수렴 경향, 압력 종료 및 2시간 정상 분포 차이 | 수치 수렴을 실제 모델/제어기 동등성으로 승격하지 않음. 독립 기준·생성 계보 확보 전 Recovery/Safety 주장 보류 |

| 2026-10-23 | Benchmark 호환성 Gate는 현재 증거 부족, 다음 최소 복원 경로는 A 권고 | `docs/research_design/BENCHMARK_COMPATIBILITY_DECISION.md` | 공식 수정 모델 source·setpoint 배선은 확보했으나 원시 timestamp/seed/export·실행 동등성 미확인. RESEARCH_DESIGN은 유지하며 B Primary 전환·C Secondary 도입은 승인 전 실행하지 않음 |
| 2026-10-23 | PR #4 raw·중간 결과의 중복은 보존 | `docs/research_design/evidence/local_20261023_v2/pr4_asset_review.json` | 동일 바이트 24그룹/88경로는 반복·빈 기록·파생 통계를 포함. 보존정책을 임의 변경하거나 원시 manifest를 깨는 삭제를 하지 않음 |

| 2026-10-23 | 사용자 승인으로 PR4→PR5 순서 통합 | PR4 merge 1e4fcc7, PR5 base main | 최초 decision의 dependency는 당시 기록으로 보존하고 현재 병합 상태를 github_current에 분리. 연구 질문·Track B/C 채택 변경 없음 |
# 2026-10-23 Track A 복원 접근·실행 Gate

정상 원시 ZIP의 공식 목록과 공개 기술보고서를 확보한 사실을 원시 바이트 회수와 구분한다. 문서상 Tests의 시간/seed 파일 구조를 정상 ZIP 또는 benchmark 선택 run에 전이하지 않는다. MATLAB 검색 범위 미발견을 전역 설치/라이선스 부재로 단정하지 않는다.
현재 A1/A2 BLOCKED이므로 A3는 NOT_RUN, 직접 효과 참조 NO-GO와 가설 INSUFFICIENT_EVIDENCE를 유지한다. 새로운 자료가 없는 반복 검색은 종료한다. 요청의 C(차단 명시 및 Track B 참조 구조 검증 설계 검토 제안)를 권고하되 연구 방향을 변경하거나 Track B/C를 채택하지 않는다. 새로운 실행환경/원본이 제공되면 Track A 재개 가능하다. 전환은 사용자 승인 대상이다.
근거: docs/research_design/TRACK_A_RECOVERY_GATE.md 및 track_a_evidence/gate_evidence.json.

## 2026-10-24 — Track B 채택 전 참조 타당성 감사

현재 채택은 NO-GO이다. Q2 관측 노드 수준 참조 구조가 확립되지 않았고 Q3/Q4 실험 단위·통계 조건도 미충족이다. 같은 simulator의 관측/개입 생성 능력은 독립 참조의 충분조건이 아니다. 코드 의존성·기존 28간선·자기 추정 그래프를 새 GT로 삼지 않는다. 국소 총반응과 직접 간선·매개경로를 구분한다.
기존 가설은 질문으로 유지하되 검증 가능성을 입증한 것으로 보고하지 않는다. 새 GT 생성·Track B/C 채택·연구 질문 변경은 하지 않았다. 먼저 REF-B/SIM-B/DESIGN-B의 참조/잡음/통계 계약을 검토하며, 참조가 해결되지 않으면 전환을 권고하지 않는다. 한 seed의 30초 RNG 일치를 다른 분기·horizon으로 일반화하지 않는다.
근거: docs/research_design/TRACK_B_REFERENCE_VALIDITY_AUDIT.md 및 track_b_evidence/. PR6 미병합 stacked dependency는 현재 상태에 명시한다.

## 2026-10-24 — REF-B 국소 진전과 조사 중단

원자로 냉각수 명령/밸브/냉각수 온도/에너지/센서·제어기 일부 식은 한 초기점에서 독립 수치 해법·해석 미분과 대조할 수 있었다. 이 범위만 REF-B PARTIAL로 기록한다. 같은 모델 상수를 쓴 구현 검산이며 실물/독립 기준 모델 또는 전체 관측 GT 증명이 아니다. 모든 구조는 CANDIDATE다.
내부 상태 전개와 기존 discovery의 관측 Xi 그래프가 의미상 다르고 관측 주변화·음성 쌍 채점 계약이 없어 이 블록에서 조사를 종료한다. 추가 GT 후보·실험을 확장하지 않는다. 전체 Q2 BLOCKED·Track B 채택 NO-GO·가설 검증 증거 부족을 유지한다. 외부 방법론 검토 후 유지/축소/보류를 판단해야 하며 연구 질문 변경은 승인하지 않았다.
근거: docs/research_design/REF_B_MINIMAL_SUBSYSTEM_VALIDATION.md 및 ref_b_minimal_evidence/.

## 2026-10-24 — 원래 질문 중심의 최소 실행 파이프라인

완벽한 TEP 복원 자체를 최종 목표로 삼지 않고 구조 참조/독립 추천 평가가 같은 환경에 대응하는 최소 계약을 우선한다. 기존 정적3개 계수로 추천 계산을 구현했지만 benchmark와 Python TEP의 환경 차이가 있어 그 값을 실제 적용·채점하지 않는다. 기술 API 확인에는 사전 지정 동일 정책만 실행한다. 연구 join은 Gate1에서 거부한다.
MVP-TECH VERIFIED는 dry 추천·로거·반복 실행만 뜻한다. 전체 가설 검증 NO-GO를 유지한다. 새 통제 후보 causalAssembly는 소스/API 검토만 했으며 채택·새 연구 데이터·학습은 별도 승인 대상이다. 그 후보의 adapter acceptance→공통 실제 정책→독립 평가 연결을 다음 실행 경로로 제안한다. RESEARCH_DESIGN·기존 frozen/Step6/적합/원시는 보존한다. 연관성 분석을 지표 개선의 인과효과로 해석하지 않는다.
근거: docs/research_design/CAUSAL_METRIC_TO_DECISION_MVP.md 및 research_runs/decision_mvp/.

## 2026-10-24 — 예제 GT–관측–do 계약 acceptance

사용자의 별도 실행 승인을 받아 고정 FCM 모듈을 격리 환경에서 검증했다. 직접 선언한4노드 IID 예제에서 reference·관측 생성·hard do 대체·seed분리·반복이 같은 계약으로 연결됨을 실행 확인했다. ENV-EXAMPLE만 VERIFIED이며 제조 generator나 Track B 채택으로 승격하지 않는다. 기존 TEP/CPCaD 결과와 혼합하지 않는다.
같은 seed여도 do의 RNG 소비/순서 변화로 관측과 행별 잡음이 다름을 확인했다. 현재 계약은 IID 분포수준 do 평가에만 유효하고 물리시계/strict counterfactual은 미검증이다. 다음3개 알고리즘 학습·목표/비용·추천 연결은 가정/범위 고정과 별도 승인 후 실행한다. Gaussian 예제의 DirectLiNGAM 가정 차이를 숨기지 않는다.
근거: docs/research_design/ENV_MVP_ACCEPTANCE.md 및 research_runs/env_acceptance/.

## 2026-10-24 — 합성 통합 실험 범위와 해석
- 사용자 명시 실행 요청에 따라 고정4변수의 Normal과 독립 Uniform 잡음 실험을 분리했다. Gaussian Direct는 가정불일치 진단, Uniform BOSS는 quasi-Gaussian 점수 한계로 표시한다. 제조 Track B 채택이나 연구 질문 변경은 승인/실행하지 않았다.
- GT 방향 보완 대신 confirmed-only 부모와 경로 없는 경우의 기준 조작0 대체를 사전 고정했다. 미확정 CPDAG와 DAG의 성능 차이에는 표현/정책/식별 가정이 혼재하므로 알고리즘 순위의 인과 주장을 금지한다.
- 예측을 먼저 동결하고 독립 do 평균/별도 기준 평균으로 효과를 평가한다. 같은 seed 행별 반사실 정렬을 가정하지 않는다. 같은 seed 전체 replay/공유 action holdout을 독립 graph-fit으로 세지 않는다.
- 다음은 graph-fit cluster·다중 과제·사전 정밀도 조건 설계다. 한 과제의 목표손실·효과오차와 F1 차이는 탐색 관찰일 뿐 원래 제조 가설의 검증 완료가 아니다.

## 2026-10-24 — 승인 순차 통합 및 합성 반복의 평가 계약
- PR6~11만 사용자 명시 승인으로 순차 일반 merge, 후속 연구 변경은 별도 feature PR. 과거 연구 질문/판정/원시 근거를 수정하지 않는다.
- 독립 graph-fit 단위는12데이터이며 36알고리즘 그래프·4과제·3정책·평가 표본을 독립N으로 세지 않는다. 새 seed·표본수·목표·미확정 처리·분석 조건을 생성 전에 고정했다.
- 미확정 방향의 기본 처리는 confirmed-only 유지. 추가 minimax/보류는 관측동치 제약의 일관된 DAG 확장들로만 실행하고, 구조 품질은 원래 그래프에만 계산한다. 같은 그래프의 정책 변화와 품질 변화의 영향을 분리한다.
- 실제 손실은 평균 목표 오차 제곱+비용, 개인 제곱오차 평균과 구분. 기준은do(X=0)이며 무개입 관측과 다르다. 이론 평균은 추천 동결 후 검산에만 쓴다.
- 사전 독립cluster/변동성 조건을 충족하는 층에서만 탐색 상관과 데이터단위 삭제민감도를 기록한다. 표본 수별3반복이므로 공식 추론/지표 우월성/인과효과는 주장하지 않는다. 계산상 확대 가능해도 이번36회 밖의 학습을 추가하지 않는다.

## 2026-10-24 — 다양한 합성 구조의 사전 비교 계약
- 사용자 명시 지시로8개 전관측 선형Uniform DAG와144회학습을 실제 실행. 제조도입/기존연구질문 변경/PR12 또는 후속PR 병합은 승인·실행하지 않음.
- 일차 비교는실제발견 graph·양성16과제·confirmed-only. 동일graph의 minimax/보류를보조비교하고, GT를써서방향완성하지 않음. 통제오류60모형/120행은인공적개입으로분리.
- 참조간선/식과source GT를first2→all8로검증후학습. worker에는GT/계수/과제가없고모든추천동결후do평가. 모든실제표본/정책공유로중복rollout·독립N부풀림방지.
- 구조간일차 손실은regret/사전scale². 기준분모·개선가능gap의 .01scale² 수치하한정책을사전고정, 결과를보고수정하지않음. 음성대조의분모가수치하한을넘더라도평균CI가목표를포함하므로안정성확증아님.
- 8개구조전체holdout/훈련7구조전용전처리/고정모형으로예측비교. 지표간중복·알고리즘차이·경로fallback의기계적연결을독립인과효과로보지않음. 경로단독평균이작아도조정후거의같고구조별순서가달라공식지표1위미확정.
- 다음확인은새구조/계수/seed와선택-확증분리의사전계획. 현재8fold를보고모형을선택한뒤같은8fold를새확증자료로재사용하지않음.

## 2026-10-25 — Independent confirmation contract and restricted interpretation
- Preserve the original research question and manufacturing NO-GO boundaries. Adopt only the user-authorized synthetic reproduction/confirmation contract; no Track B or manufacturing transition.
- Freeze random structural families/uniqueness rules, all seeds/tasks/settings/code and old-only fitted loss predictors before new sampling. Use macro MAE over whole reference structures; main delta threshold .01 plus structure bootstrap lower>0, without using confirmation outcomes to choose models.
- Retain cyclic PC outputs and incompatible PDAGs as failed/blocked cases. Do not orient to truth, delete edges, silently drop records, or retrospectively assign baseline losses. Current valid-loss analysis is conditional on usable graphs and remains selection-limited.
- Report narrow primary endpoint support separately from the unresolved incremental-information and robustness question. M0/M1 augmentation, analytic mean and high-cost results do not establish stable superiority. Correlations and artificial graph-error contrasts are not causal effects of raising a graph score.
- Exact replay evidence applies to the same host/installed environment; new216 second replay and manufacturing Recovery/Safety are NOT_RUN. Current full144 replay supersedes the old NOT_RUN state only in the live dashboard; historical artifacts stay unchanged.


## 2026-10-25 — 일회 검토 예외와 추가 예측력 평가 계약

사용자가 PR12~14에만 직접 승인 예외를 명시하여 검증 후 일반 병합. CONTRIBUTING 영구 검토 규칙 변경·가짜 팀원 승인·보호 우회 없음. 새 PR에는 자동 병합 권한 없음.

기존 S/C20구조는 모두 개발 전용. 이론 평균의 실제 운영 추가 손실을 평가하며 실패 시 사전 기준 조작0의 손실을 산출한다. 과제·graph 특징은 관측/적합 자료만 사용하고 정답 계수/최선 조작은 진단에 분리한다. 추가 정보 A(M1→M4) 다음 B(M5→M6)와 .01 개선·반폭.005를 계획 전에 기록. 새 독립 구조는 정밀도/예산150대30,1350대288 초과로 생성하지 않기로 Gate 규칙을 적용했다. 이 값은 검정력 보장이나 자원 자동 확대 승인이 아니다. 실제 do 검산만 기존3개 개발 구조에서 수행. RESEARCH_DESIGN 변경 및 제조 환경 채택 없음.


## 2026-10-25 — 오류의 의사결정 영향으로 목적 고정

RESEARCH_COMPASS는 실무 안내이며 RESEARCH_DESIGN을 대체/수정하지 않는다. 지표 순위를 유리하게 만드는 것이 아니라 오류→추정응답→조작선택→개선/악화의 조건을 검증한다. 기존20구조는 개발 전용. 원래 이름 대신 현재과제 경로로 핵심/주변을 재분류하고 실제동일오류 명칭108중복을 표시하되 원자료를 삭제하지 않았다. 같은F1의 반대사례/동률도 포함한다.

큰악화는 사전 loss-reference>loss_scale², 기준손실≈0 비율 미계산. oracle 구조/응답의 완벽정보 대조는 실제발견결과와 분리. 저차원9모형을 중첩 구조검증하고 기본모형 기준선 유지, 품질특징 추가의 일반적 우월성 미확인. 의미있는 추천개선과 작은 예측정보는 다르므로 범위초과132구조/1188학습을 억지 실행하지 않는다. 다음 우선은 제조 참조·관측·do 정합성 계약,독립 오류 대조 설계. PR15/새PR 자동병합 없음.


## 2026-10-27 — 제조 직접검증과 기술계약의 분리

기존환경복원/새Python후보는동일관측·참조·do환경이확인되지않아직접제조가설NO-GO. 기존smoke는기술증거만. 권고D추가확인;새환경채택/B전환/C공식범위축소를자동결정하지않음. 다음작업은id/Boolean이아닌model/controller/node/clock/reference/intervention/evidence metadata의fail-closed계약구현. 물리타당성은metadata일치만으로승인불가.

낮은F1은연구대상불완전성일수있지만참조의미가맞아야한다. 저장baselineCSV반올림으로동률비교가어긋나정수TP를유일복원하여동일수학적통계로검산. 이는원표p재정의/유리한튜닝이아니며실패기록보존. 기존측정·원설계·graph·과거결과변경없음. 선형/비선형4셀은조건부미실행설계로분리.

### 2026-10-27 — 환경 계약 통과와 제조 연구 승인 분리

새 metadata/evidence guard의 통과는 연구검토에 제출할 기술 정합성만 뜻한다. 과학적 동등성·실행권한·제조 채택을 자동 승인하지 않는다. legacy guard는 과거 재현용으로 남기고 새 join은 environment_contract.require_environment_contract를 사용한다. 현 CPCaD/Python join과 부분 양성참조의 전체F1 사용은 거부한다. 유한 lag universe 미지정 시 시차참조도 fail-closed로 거부한다.

8×6step 실제 실행과3고정점 반례는 Python의 실행 가능성과 현재 센서 상태충분성 한계를 함께 보인다. 이를 센서 전체GT·평균효과 정답·안전/복구·원가설 증명으로 승격하지 않는다. 원환경 복원/새Python전체연구 모두 핵심조건 미충족(권고D). 공식 범위 변경 없이 다음은 좁은 밸브 시간전이식과 적용조건 거부를 독립검산하는 한작업으로 제한한다. RESEARCH_DESIGN 불변. 근거: TEP_ENVIRONMENT_BRIDGE_FEASIBILITY.md, technical_v1/closure_v1/CONTRACT_RESULTS.json.

과거 실험이 decision_mvp 코드 bytes를 동결 입력으로 검증하므로 해당 파일에 신규 wrapper를 추가하지 않는다. 새 계약은 독립모듈만 사용하며 legacy의 약한 검사를 과학적 승인으로 사용하지 않는다. 실제 hash검사 실패3건이 이 결정을 뒷받침한다.

### 2026-10-27 — 정상 전이 검산 종료와 연구 범위 선택안

실제 u_req/u_eval/cache c와 v_t/v_next를4step에서분리했다. 과거cache미기록24step은 c를역산해보완하지않고BLOCKED를유지한다. stiction/clip/controller/shutdown은정상계약에서거부하며모의거부를실제Fault검증으로승격하지않는다. L1 VERIFIED는공식GT/관측구조/전체F1이아니며 L2 PARTIAL,L3/L4 BLOCKED다.

다음기술시험을관성적으로추가하지않는다. 우선권고B는기존정적센서/benchmark를보존한채별도내부상태·시간전개설계안을검토할지사용자가선택하는것이다. A원계보자료부족,C효과중심은전체구조가설의수정이필요하므로자동채택안함. SCOPE_PROPOSAL.json은제안일뿐,연구전환/GT/발견학습/본실험/기존PR병합은승인하지않음. RESEARCH_DESIGN 불변.

### 2026-10-27 — B 제한 동적 계약 검토 결과: 판정2

사용자가승인한B설계검토를수행한결과,4node/12후보쌍만으로는W/E/T_R의내생경계부모가닫히지않고발견추정대상/음성참조·관측변동·비자명한온도선택과제도미정이다. source의조건부함수부모를전체공정/관측GT로승격하지않고실행NO-GO로결론냈다. 초안은PROPOSED_FOR_REVIEW이며RESEARCH_DESIGN/기존benchmark/원시는불변.

이전B검토권고를유지하려고검사/가정을완화하지않는다. 추가smoke/대규모state확장/독립잡음삽입을자동수행하지않는다. 다음한결정은C별도효과·조작선택설계검토여부다. 전체직접GT부담은줄지만제조전체F1가설의직접검증은아니라는범위변경을사용자가검토해야한다. 공식전환/새실행/GT/기존PR병합승인은없다. 원benchmark와합성오류연구는독립결과로보존한다.

### 2026-10-28 — STOP-TEP-EFFECT-TRACK

효과중심설계검토에서manual XMV10→Y9를2후보중선택했지만출처있는허용정책집합·비자명한온도목표/H·실패포함손실/학습정책범위를정당화하지못했다. 대안setpoint17/ctrl18의정적연결문제도확인했으나새실행/패치를하지않는다. GT부재나비용부재만을중단원인으로삼지않으며숫자null을채워READY/CONDITIONAL로승격하지않는다.

현재TEP효과연구경로동결. 후속smoke/소스수정/운전범위찾기/새검토문서루프를권고하지않는다. 원래CPCaD구조평가와합성구조–효과–선택결과는독립보존하고다음작업은합성독립확인/강건성/오류대조의최종주장정리다. 이는공식가설변경/TEP폐기/새합성실행/기존PR병합승인이아니다. 근거:TEP_EFFECT_DECISION_FEASIBILITY와tep_effect_feasibility/PROTOCOL·DECISION.

### 2026-10-29 — 합성 Results·Discussion의 주장 범위 확정

- 최종주장표: 전체점수동점과동일선택은다름(A),구조/효과/선택순위는불일치(D),동일graph정책변경효과(E)는범위내지지. 오류위치/유형(C)및경로대체예측력(B1)은반례·강건성한계를포함한부분지지.
- B1당시사전지지를삭제하지않으며,추가정보(B2)는NOT_ESTABLISHED로별도판정. C12는당시확인이지만현재개발재사용이며새확인으로재분류금지. 제조(F)는NOT_TESTED,TEP STOP유지.
- 자원우선권고는새지표추가가아닌제한독립합성오류대조계약/예산결정. 작은MAE우세를얻기위한무한확대/기준완화/신규TEP재개없음. 이번신규실험승인없음.

### 2026-10-29 — 오류 위치 독립 확인 계약의 자원 Gate

- 일차는지표MAE순위가아닌,같은유형/개수/점수의핵심-주변오류graph를같은자료로재적합/추천한운영선택손실차이.반례·동률·실패기준정책을포함;일반순수위치인과효과아님.
- 새30개설계는고정하되실행준비로승격하지않음. 손실scale1의차이/반폭0.1은중간손실을보기위한설계제안이고,기존0.01MAE기준을소급수정하지않음.기존평균을유리한검정력근거로사용안함.
- REDESIGN_REQUIRED:정밀도-독립SCM자원과새경로종단시간/메모리근거2개만미해결. 신규실험/runner/후속검사·문서작업을자동생성하지않음. 자원확대여부또는확인확대종료결정전중단.원설계/TEP동결/과거판정보존.

### 2026-10-29 — 통합 제조 벤치마크 후보 판정

- 공식source기반5후보비교결과CausalMan을CONDITIONAL-CANDIDATE로선정.생산SCM과공통do코드·잠재투영을제공하지만source6반환/CLI4계약충돌,활성식/참조/mask정합성및식별가능한선택계약미검증으로READY아님.현재완전YES아님.
- Chambers실물/GT와부분기구simulator를같은생성모델로합치지않음.PenSimPy/IB의내부ODE/동역학으로센서GT를발명하지않음.causRCA의real/HIL·genericBNsimulator를같은실행플랜트로취급하지않음.
- 다음한검증은별도승인후고정micro의GT-관측-do acceptance.라이브러리/대형pickle획득·설치·실행은이번승인밖이며진행안함.기존TEP STOP/합성연구/PR23 REDESIGN·예산보존.공식채택/연구변경/병합없음.

### 2026-10-29 — CausalMan micro 미수용

- 실제import·관측·숫자do성공을연구수용과구분한다.원본mutilated graph의부모삭제결함과조건부참조/관측ADMG식별계약이남아CONDITIONAL_NOT_ACCEPTED.81간선계층차이만으로원시모델버그를선언하지않으며설치실패를과학적기각으로취급하지않음.
- 다음은관측-only점효과식별을필수로유지할지방법론결정하나.현재micro의학습/추천본연결은보류하며,privileged-state/알려진함수/부분식별대안은새승인계약이다.자동패치·smoke반복·공식채택·TEP재개·기존PR병합없음.

### 2026-10-29 — TEP 원본 복원 가능성

- 공식 C/헤더/초기상태와 Studio 파일3개 바이트일치는 유력 단서다. 제어기·잡음·clock·raw 계보와 구조 참조 타당성은 독립 문제여서 기존 STOP을 유지한다. setpoint 진단을 제조 효과·안전 검증으로 승격하지 않는다.

## 2026-10-29 — TEP Studio 기술 실행 후 판정
TEP_RECONSTRUCTION_PROMISING: 공식 3파일 일치 및 기술 실행은 확인, 원본 동일 생성환경과 전체 참조 구조는 미확립. 기존 7개 그래프와 신규 개입의 결합 및 연구환경 공식 채택은 보류.

## 2026-10-29 — TEP 운전 조건 중단
ORIGINAL_OPERATING_CONTRACT_NOT_ESTABLISHED. 제약 위반을 완화하지 않고 후속 장기 실행 중단. 문헌상의 고정 조작은 특정 현재 데이터 파일의 명령·전처리 계보가 확인되지 않아 별도 고정 실험을 실행하지 않음.

## 2026-10-29 — TEP 후보 잠정 판정
CLOSE_CANDIDATE_BUT_UNVERIFIED를 잠정 기록한다. 공식 2015 모델과 Studio 핵심 파일 계보는 유망하지만 원본 관측·제어·가공 및 전체 참조 정합성은 미검증. 일부 후보 미실행으로 탐색 완료나 일치 후보 발견을 선언하지 않는다.

## 2026-10-30 — 공식 MATLAB 실행 차단
BLOCKED_NO_MATLAB. 공식 계정·라이선스 및 컴파일러 확보 후 모델 사전 점검이 필요하다. 실시간 측정·상태·명령 제약 감시 검증 전 공식 시뮬레이션을 실행하지 않는다. 기존 시뮬레이터 비교와 연구 자산은 보존.

## 2026-10-30 — 공식 실행 검증과 연구 재개 보류
OFFICIAL_SIMULATOR_RUN_VERIFIED_ENVIRONMENT_UNVERIFIED. 평균·고정명령 근접과 공식 실행은 확인됐으나 동일환경 계약 전체 미확립으로 Phase B를 실행하지 않음.

## 2026-10-30 — 원본자료 접근 Gate
원본 ZIP 인증 전에는 동일환경·개입 연구를 진행하지 않음. 보존검사는 두 pilot 상태문서의 원문 prefix를 보존한 추가만 허용하고 다른 보호자산 변경은 계속 거부함.

원본ZIP 인증 문제 해소 후 원본 자료를 실제 분석함. 초기조건은 가깝지만 X20/X21 시간변화 차이와 가공 미복원으로 ENVIRONMENT_STILL_UNVERIFIED 유지,75h 및 개입 확대를 하지 않음.

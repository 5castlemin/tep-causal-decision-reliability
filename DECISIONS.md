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

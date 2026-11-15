# 결정 기록

- 2026-11-05 제안: 비용 제약의 구조 개선 정책과 후회 비교를 별도 연구 후보로 구축. 기존 RESEARCH_DESIGN.md와 완료 결과를 대체하지 않는다.
- 주 제안은 참조를 사용하는 oracle이며 비oracle 정책은 후속 별도 계약. 선택 지표 외 지표의 변화도 허용·기록.
- 균등 몫과 고정 순서를 예시로 사전 제안; 예산의 자유 배분 oracle과 구분. 겹치는 수정은 한 번만 과금. 통계적/계산 예산은 미승인.
- 선형 합성 우선, 비선형 별도 요인 실험; CausalMan과 TEP는 외부 Gate가 충족될 때만. 그 실패를 핵심 합성 연구의 자동 실패로 삼지 않는다.
- 이전 ERROR-CONFIRM의 REDESIGN_REQUIRED, CausalMan acceptance 실패 및 TEP 미검증은 취소되지 않았다. 특정 정책 우월성은 미결정이다.

## 2026-11-10 Step 0 공식 전환
15개 F1 지표 조합은 ARCHIVED_METRIC_COMBINATION_DESIGN.md에 보존하고 FN/FP/REV 7조합×Global/T 14개와 세 baseline으로 전환한다. 4개 기존 지표는 진단으로 유지한다. unit 비용과 표준화 평균반응 후회, 학습 SD ddof=1 및 후보 5수준은 채택; 예산 grid는 Step4에 동결. 실제 효과로 수정 순서 선택 금지. 신규 실험·GT 생성·시뮬레이터 실행 없음.

## 2026-11-10 Step1 유형 일정 교란 수정
Global 유형순 대 T 전체 위치순은 혼재이므로 공통 seed 회전 균형 유형 일정과 유형 내 위치 tie로 변경. 유형별 실현 수는 DAG·예산 때문에 다를 수 있어 별도 기록한다. 과거 Step0 규칙과 같은 estimand로 혼합하지 않는다. 소형17개 테스트 통과, 전체 엔진·기준선은 미구현.

## 2026-11-10 Step2 구현
Step1 계약을 policy_engine 및 graph_adapter로 구현. 명시적 스키마와 oracle graph-only 필드 경계를 채택하고 모델 및 평가기와 분리한다. 추가 참조 경로를 읽는 Path F1 기준선을 같은 정보량 정책으로 표시하지 않는다. 기존 계획·실험 결과 변경 없음; CI 확인 전 Step2 미완료.

2026-11-10: 엔진 커밋 f1494e7의 GitHub Actions 42777224302 및 관련36개 소형 검사를 확인해 Step2 DONE. mock 경계와 실제 Step3 SCM 연동의 검증은 분리한다. 연구 파일럿 미실행.

2026-11-10: 승인된 Step3 개발 파일럿은 S1/S7 첫 직접 과제와 기존 remove_key 조건을 결과 확인 전 고정했다. 전부 후회 0이며 단일 FN이어서 정책 우열을 주장하지 않는다. 실제 SCM 어댑터에서 추천 뒤 정답을 평가한다. Step3 IN_PROGRESS: 재현 및 CI 미완료.

2026-11-10: 기존 직접 과제의 삭제 간선은 조작 상류이며 예측 불변임을 재분석했다. 기존 경로 과제와 사전 명세된 복합 오류 보완 456회는 기존 자료 해시를 보존하는 탐색 진단이며 확인 실험이 아니다. CI 확인 전 Step3 IN_PROGRESS.

2026-11-10: Step3 완료 — 구현 531486a의 전체 149개 로컬 검사와 GitHub Actions 42780815082 성공, 사전계획된 보완 결과 보존. 두 개발 SCM 결과는 확인적 주장이 아니며 Step4 등록에서 표본·비용·실패·분석 규칙을 결정한다.

2026-11-10: Step4에서는 선택 정책과 동일한 오류 유형·일정의 matched Random 및 matched Path-F1 기준선을 제안한다. 기존 Step3 full-pool 결과는 유지한다. 64/200과 0.10은 후보이며 생성 적격성·자원·실패 규칙 미검증으로 동결하지 않는다. STEP4_READINESS_AUDIT.md.

2026-11-10: 사용자는 검증된 진행 중 개발물을 main의 공식 기준으로 통합하도록 지시했다. Development Integration은 Step4–9 완료나 연구 가설 검증이 아니다. 최소 1명 검토와 CI·동결 자산 확인을 유지한다. 기존 인과 결과와 미병합 연구는 보관한다.

## 2026-11-15 Step 4B-1 critical design audit (additional review, not frozen)

- Preserve historical v1/v2 outputs. Create a separate v3 feasibility matrix that checks all six atomic orders for disjoint one-each FN/FP/REV recipes. C requires mixed types and related plus peripheral errors, but does not require path survival or an on-route FN. Failed cells are never replaced with another error type.
- The outcome-blind B type schedule yielded FN 13/66, FP 67/67, REV 11/67. Under the current path-preserving recipe, direct-only FN/REV are infeasible. Do not interpret a pooled B mean as a fair type comparison.
- Across 17,185 graph-only matched Global/Task-Focused pairs, 97.2% lack two DAG-valid same-type candidates; final graphs differed in 12 (0.07%). The present topology matrix cannot identify H2 as a primary confirmatory effect. Any H2 challenge cohort must be preregistered with separate target-population weights.
- Fixed positive-control fixtures test policy distinguishability for all three error types; they are not policy performance evidence. Matched Random/Path-F1 comparisons do not substitute for an H2 Global-versus-Task-Focused contrast. Resolve H1/H2 status, estimands, and weights in Step 4B-2. Step 4B-1 and Step 4 remain IN_PROGRESS / NOT FROZEN.

## 2026-11-15 Step 4B-2 population and hypothesis design proposal (not frozen)

- Correct C recipe eligibility to enumerate all six atomic edit orders for each one-FN/one-FP/one-REV recipe. The fixed-order prefix could reject a recipe with a valid alternate intermediate-DAG order; preserve v3 and write the corrected result as v4.
- Keep the general topology population P and the structural two-candidate H2 cohort Q separate. Q eligibility uses only topology, fixed task roles, error locations, DAG-valid individual corrections, surviving path, and budget 1; no policy outcome, SCM effect, or regret enters selection.
- Define the primary selected-policy-vs-matched-Random estimand separately from H1 error type/location and H2 Global-vs-Task-Focused ordering. H1 has no current clean type-only support because direct FN/REV are absent and FP must occupy a non-truth dyad. H1 is proposed as conditional/type-location exploratory reporting. H2 in P is a population-average paired contrast; H2 in Q is a distinct conditional contrast, structurally exposed at budget 1 but not yet powered or confirmed.
- Retain C path-survival strata (v4 133/200 survive, 67/200 disconnect), and overlapping location tags. Upstream-of-Action labels do not imply harmlessness under hard-do(X).
- The 64/200 SCM sizes, inferential tests, missingness/failure rules, compute caps, and target weights remain candidates for later Step 4B work; no final sample or analysis contract is frozen.

## 2026-11-15 — Step 4B-3 주 추정량 및 RNG 설계안 (미동결)

- 보존된 v4 P 구조 행렬에서 P/B=4의 14개 정책 각각과 Matched Random 5개 seed를 대응 실행한 34,370쌍 모두 최종 그래프가 같았다. 이 결과는 regret 비교가 아니므로 P/B4를 보조·탐색적 벤치마크로 낮추고, Q-common/B=1의 Global 대 Task-Focused 대응 H2 질문을 계획상 주 확인 질문으로 제안한다.
- Q-common은 동일 SCM/task가 FN·FP·REV 세 구조 적격성을 모두 통과하는 outcome-blind subset이다. 유형별 1/3 동일 가중으로 SCM당 1개 대응값을 구성하며, 현재 진단에서는 34/100 topology ID만 공통 지지에 포함됐다. 64/200 eligible SCM은 현재 수율만으로 보장할 수 없고 목표 모집단 가중치·attempt cap·shortfall은 Step 4B-4에 남긴다.
- RNG는 protocol/cohort/master seed/SCM ID/template/node count/attempt/stream/replicate 키의 canonical JSON SHA-256 domain separation으로 파생한다. 이는 재현 가능한 명명 스트림 분리이지 수학적 독립성 증명은 아니다. Global/Task-Focused는 같은 type schedule seed를 공유하고 Random draw seed만 분리 가능하도록 Step 2 엔진에 선택적 인자를 추가했다.
- 새 context-keyed feasibility 결과는 v1 별도 파일로 보존한다. v1-v4 및 B2 원시는 변경하지 않았다. RNG 키 체계 변경과 B 행렬이 세 오류유형을 모두 시도하는 설계 변경이 함께 적용되어 과거 수치와 단순 RNG-only 비교는 하지 않는다.
- Step 4 전체는 IN_PROGRESS / NOT FROZEN. 표본·정밀도/검정력·추론/CI·실패·resource cap 동결은 수행하지 않았다.

- Step 4B-3 gate is DONE for the primary-estimand recommendation, P+B4 distinguishability audit, context-keyed structural feasibility, raw/report consistency, tests, frozen assets, exact-head CI, and Self-Review. This does not mark Step 4B-1/2 or Step 4 overall complete; Step 4B-4 inferential/sample/failure/resource contracts remain required.

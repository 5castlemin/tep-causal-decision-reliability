# Specification Gate V2 — 방법론 검토

**판정: V1의 핵심 specification gate는 부분 개선됐지만 아직 구현/사전등록 gate를 통과하지 않았다.** 검토는 원문 지표·비용 DOCX의 확인 가능한 동일 SHA 사본과 기존 v1 명세, 손계산 DAG fixture에 한정한다. SCM, 효과, regret, cost-weight 추정은 하지 않았다.

## 심각도별 문제

### P0 — 과제 구역 및 오류 분류가 결과를 바꿀 수 있음

V1 FP 예시 3은 `Z→X`를 한편으로 정답 간선, 한편으로 FP로 취급했고 해당 한 간선만으로 backdoor가 생긴다고 보았다. 이는 모순이다. 수정 fixture는 GT `{X→M,M→Y,Z→X,Z→Y,W→M}` 및 FP `W→X`로 명시한다. 여기서 `X←W→M→Y`는 collider 없는 open backdoor다. 참 간선 errors와 GT-absent FP assignment는 별도 단계로 처리한다.

또 “X에서 첫 edge가 X로 들어오는 path”와 “열린/active backdoor”는 동치가 아니다. collider가 있는 path는 conditioning 규칙에 따라 닫히거나 열릴 수 있다. conditioning set/descendant 조건을 고정하기 전 M4 zone의 경계는 실행계약이 아니다.

### P0 — M3 accuracy 단독 최적화는 unresolved로의 회피를 보상할 수 있음

Direction accuracy denominator에서 unresolved를 제외하면 wrong direction을 unresolved로 바꿀 때 accuracy가 상승할 수 있다. M3 accuracy와 unresolved rate/count를 항상 동시에 보고하고, unresolved를 잔존 벌점에서 빠뜨리지 않도록 별도 penalty disposition이 필요하다.

### P1 — M4 scalar와 오류 가중치 이중 적용

`α_FN,α_FP,α_REV`로 M4를 scalar화한 뒤 `w_FN,w_FP,w_REV,λ`가 같은 오류에 다시 곱해지면 task error가 중복 가중될 수 있다. M4 vector는 보존하고, penalty에서 event별 weighting을 한 번만 하거나 α를 통합계수로 대체해야 한다.

### P1 — quota의 unit, budget 및 효율 선택이 다름

V1 floor(B/k)는 B가 edit count인지 비용인지 불명확했고 서로 다른 `c_ori`에서 quota를 분할하는 방식도 없었다. V2는 A를 reference-unit edit-slot quota로 분리하고 actual cost cap을 따로 적용, B는 normalized gain/cost shared greedy 후보로 정의한다. B greedy는 M3+M4 scalar/normalization 승인 전에는 실행할 수 없다.

### P1 — 카탈로그 내 최선은 전역 최적해가 아님

15 metric-subset policies+no-edit 중 best는 해당 카탈로그에 대한 최선일 뿐 가능한 모든 edit trajectory의 global optimum이 아니다. 완전 탐색 optimizer를 추가한다면 별도 oracle upper-bound다.

## 수정 산출물

- `ORIGINAL_FOUR_METRIC_SPEC_V2.md`: pair-level event partition, M1–M4 formulas, unresolved/denominator caveats.
- `TASK_ZONE_FP_ASSIGNMENT_OPTIONS_V2.md`: FP가 GT edge 오류와 분리되는 A/B 규칙, collider/open path 구분, 6개 DAG fixture.
- `METRIC_TO_REPAIR_POLICY_SPEC_V2.md`: 16개 유지, quota A vs cost-efficient greedy B, B=1…4 example.
- `COST_AND_PENALTY_SPEC_V2.md`: C, P, R, ρ, unresolved cost/penalty 및 double-count separation.
- `SPEC_GATE_V2_FIXTURE_AUDIT.md`: hand calculations, DAG/edge event audit.
- `SPEC_GATE_V2_DECISION_OPTIONS.md`: 책임자가 승인할 선택지 목록.

## 남은 선결 조건

M4 active backdoor semantics, FP A/B 및 denominators, M3 unresolved rate, M4/penalty weighting, quota/greedy utility, unresolved edit/cost, B grid 및 sample/estimand contract는 아직 승인 대기다. 그 때문에 이 작업은 `SPECIFICATION REVIEW / NOT PREREGISTERED`이며 실험을 승인하지 않는다. 기존 Step4 frozen contract와 Step5/6 결과는 변경하지 않는다.

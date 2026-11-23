# 비용·벌점·Decision Regret 명세 V2 제안

**상태: 설계 후보. 원 비용 DOCX와 다르게 동결된 것은 없음.** 원래 제안의 세 계층을 구분한다.

## 1. 수정 비용

`C(π)=c_add·n_add+c_del·n_del+c_ori·n_ori`; unresolved 판정/확정/삭제 operation은 종류별 action 수와 비용을 별도 기록하고 mapping을 사전 승인한다. 원문 baseline은 `c_add=c_del=c_ori=1`. 보조 방향 비용은 `c_ori/c_add∈{1,2,3}`, `c_del=c_add`. B-2의 변수 비용 `w_i~Exponential(1)`로 방향 비용을 유도하는 제안은 derivation 미정으로 보존한다.

`B`는 resource-cost cap이며 `C(π)≤B`. A quota의 equal edit slots는 reference unit 비용 `c_ref=1`을 사용해 `N_ref=floor(B/c_ref)`로 별도 계산하고 실제 연산은 scenario 비용 및 global B를 모두 통과해야 한다. Quota는 edit-count budget이고 cost cap을 대신하지 않는다.

## 2. 잔존 오류 구조 벌점

Task/outside를 partition한 error-event counts/rates를 `E_{r,z}`, `r∈{FN,FP,REV,UNRES}`, `z∈{out,task}`라 한다. 후보:

`P(G)=Σ_{r∈{FN,FP,REV}} w_r[E_{r,out}(G)+λ E_{r,task}(G)] + P_UNRES(G)`.

`P_UNRES`는 unresolved가 0 벌점이 되지 않도록 하는 정책/계수다. 방법 후보는 (i) 오류 유형별 별도 `w_UNRES,out/task`, (ii) orientation error `w_REV`에 통합, (iii) count 및 unresolved rate를 별도 vector 결과로 두고 scalar 벌점에서 제외해 별도 민감도. 원 DOCX는 unresolved를 새 비용 모델에 정확히 어떻게 연결할지 확정하지 않았다. 이 선택 전에는 모든 잔존 오류를 벌점에 포함한다고 주장하지 않는다.

M4 aggregate weight `α`와 기존 `w_r,λ`를 함께 곱할 경우 같은 task error가 이중 가중될 수 있다. 우선 비교할 설계:

- **Option 1 (선호할 단순 후보):** M4는 reporting/policy objective의 vector; scalar structural penalty는 모든 zone별 error event에 `w_r`와 단일 `λ`를 한 번 적용한다. 추가 α 없음.
- **Option 2:** M4 scalar `Σ α_r E_{r,task}`를 별도 결과/정책 score로 두되, 이를 `P`에 더할 때 기존 `w_rλ` 적용을 제거하거나 통합계수를 한 번만 정의한다.
- **Option 3:** M4는 예측 feature로만 사용; 실제 선택 정책의 목적은 별도 utility. 이때 “네 지표 조합으로 비용을 최적화”하는 claim은 다른 해석이 된다.

계수는 정답 효과/Regret 평가 결과로 사후 고르지 않는다. DOCX는 `w_FN,w_FP,w_REV,λ`를 합성 데이터 회귀로 추정하는 안을 말하지만 추정/평가 자료 분리, model, uncertainty, causal interpretation은 미확정이다.

## 3. 별도 평가량: Decision Regret

고정 SCM과 action set `A`에서 `R(π)=L_GT(a_π)-min_{a∈A}L_GT(a)`. 이는 잔존 구조 penalty `P(G)`도 아니고 repair cost `C(π)`도 아니다. 주 최적화는 `min P(G_π)` s.t. `C(π)≤B`; regret은 별도 downstream outcome으로 정책별 평가한다. 구조 벌점이 감소해도 regret이 감소하지 않을 수 있으므로 관계는 새 독립 evaluation 데이터에서 확인한다.

보조 목적함수 `min[C(π)+ρP(G_π)]`는 DOCX가 제안한 cost–penalty tradeoff curve다. 고정한 하나의 `ρ`를 주 결과로 뽑지 않는다. `ρ` 의미는 C와 P scale, units 및 비용 해석에 의존한다.

## 4. 예산 feasibility

`c_ori=2/3`에서 B=1은 REV 수정 불가, `c_ori=3`에서 B=2도 불가. 이를 structural infeasibility, policy failure, zero regret로 다시 부르지 않는다. 정상적인 `UNAFFORDABLE_WITH_REMAINING_BUDGET` 상태로 기록하고 M3 opportunity, cost left, non-orientation candidates and actual edits를 함께 낸다. 비교는 동일 nominal B와 cost scenario 아래에서 하며, common action support의 별도 strata는 필요 시 별도 estimand로 사전 지정한다.

## 5. 민감도 보존

- FN/FP damage ratio `w_FN/w_FP∈{1/4,1/2,1,2,4}`.
- orientation cost ratios `{1,2,3}` vs add, deletion equal add.
- variable intervention derived orientation cost B-2 (derivation yet to specify).
- regression-based `w_FN,w_FP,w_REV,λ` B-4, only after training/evaluation split is fixed.
- ρ tradeoff curve and threshold cost ratios.
- budget–penalty curve, no post-result B or coefficient selection.

“16개 카탈로그 내 최저 벌점”은 catalog-relative winner다. 모든 가능한 edit sequence를 푸는 global optimum 아님. 완전 탐색 oracle을 더하면 별도 upper bound로 라벨링한다.

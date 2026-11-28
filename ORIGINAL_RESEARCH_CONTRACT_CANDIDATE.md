# 원 연구 통합 계약 후보

**상태: 실행 가능한 설계 후보 / 사용자 승인 전 / NOT FROZEN / NOT PREREGISTERED.** 이 문서는 계산 단계를 명시하지만 미결 선택을 승인된 계약으로 바꾸지 않는다. 새 SCM·효과·Regret 실험은 포함하지 않는다.

## 1. 연구 질문과 정보 조건

질문은 “불완전한 인과그래프에서 주어진 구조 수정 예산 안에 네 원 지표 중 무엇을 우선 개선할 때 다운스트림 Decision Regret이 줄어드는가?”이다. 분석 대상은 네 지표로 정의된 15개 nonempty metric subset 정책과 무수정 기준선 S0이다. 기존 Step 4의 FN/FP/REV 14개 ordering 정책과는 별도 연구다.

주 설계 후보는 **oracle-assisted 구조 진단**이다. 평가기 전용 정답 DAG는 오류 사건, 정답 수정 연산, task zone, 지표 변화량을 구성할 수 있다. 다만 정답 SCM 계수, 개입 평균, GT loss 또는 Decision Regret은 어떤 후보 필터·순위·tie-break에도 들어가지 않는다. 따라서 oracle 보정 정책은 실제 배포용 오류 발견기가 아니라 정답 정보가 주어진 진단이다. Non-oracle 오류 발견은 별도 연구다. Greedy 결과는 선택한 연산자·효용·예산 아래의 알고리즘 결과일 뿐, Regret의 upper bound라고 부르지 않는다.

## 2. 입력 및 사건 분할

각 고정 task `t=(X,Y)`에 대해 동일 node set `V`, reference DAG `G*`, initial estimate `G0`, 사전 지정된 allowed edits, task zone 후보, 수정 비용표 및 예산 `B`를 받는다. 각 비순서 pair는 estimate state `absent / unresolved / u→v / v→u` 중 하나다. GT adjacency 존재와 estimate state로 `correct, reversed, unresolved, missing, false-predicted`를 상호 배타적으로 분류한다. GT-absent FP의 task/non-task tag는 별도 규칙 A 또는 B로 평가자가 붙인다. 한 graph×task의 오류 사건은 M1, M2, M3 또는 M4의 단일 bucket에만 들어가며, 참 adjacency가 task zone에 있으면 M4의 FN/FP/REV/UNRES vector에 귀속한다. 맞은 edge는 오류 수가 아니지만 분모에는 반영될 수 있다.

## 3. 원 지표 산출

다음 식은 V2에서 제안된 계산 후보를 유지한다. 모든 rate와 그 분자·분모 count를 함께 저장하고, 0 분모는 NA 사유를 유지한다.

- `M1 = off-task missing true adjacencies / off-task true adjacencies` (낮을수록 좋음).
- `M2 = off-task FP / off-task predicted adjacencies` (낮을수록 좋음). FP task tag는 task denominator에서도 같은 규칙으로 제외한다.
- `M3_acc = correctly oriented off-task true adjacencies / (correct + reversed off-task true adjacencies)` (높을수록 좋음); `M3_unresolved = unresolved off-task true adjacencies / all estimated off-task true adjacencies` (낮을수록 좋음). 작은 분모는 비율 단독 순위화 대신 count를 병기한다.
- `M4 = (FN_task, FP_task, REV_task, UNRES_task)` event-count vector. 각 component rate는 그 component의 reference opportunity denominator와 함께 별도 보고하며, 단일 scalar로 축약하지 않는다.

정답 causal task zone 후보는 모든 정답 X→Y 방향 경로 edge의 합집합이다. Backdoor는 별개로 “X에서 화살표가 들어오는 모든 단순 X–Y path”와 “빈 conditioning set에서 open/active backdoor path” 중 하나를 정해야 한다. 주 분석 후보는 방향 경로 + 무조건화 open backdoor, FP rule A(양끝점이 task-zone node set 안)를 쓴다. Rule B(boundary FP가 정해진 causal/open route를 형성하면 task 귀속)와 별도 conditioning set은 보조 민감도 후보이며 선택은 미승인이다. 구조적 tag는 개입 손실 영향의 증명이 아니다.

## 4. 지표를 수정 연산으로 연결

지표 ratio만 낮아지는 것을 “오류 수정”으로 인정하지 않는다. Oracle candidate pool은 오직 분류된 사건에 대해 아래 원자 연산을 만든다.

| 목표 metric | 허용 후보 연산 | 직접 사건의 필요조건 |
|---|---|---|
| M1 | 정답 방향의 adjacency 추가 | off-task FN pair |
| M2 | 추정 adjacency 삭제 | non-task FP pair |
| M3 | 방향 반전 교정 또는 미확정 방향 resolve | off-task REV는 true 방향으로 orient; UNRES는 true direction으로 resolve. 방향을 지운 unresolved 생성은 M3 repair로 인정하지 않음 |
| M4 | task-zone FN/FP/REV/UNRES 교정 | task 오류 사건에 맞는 add/delete/orient/resolve; UNRES 삭제는 FN으로 상태 전이 |

방향 불확정 연산은 세 operation으로 분리한다: (i) `mark_unresolved`: directed adjacency를 unresolved 상태로 전환, (ii) `resolve`: unresolved adjacency에 방향을 지정, (iii) `delete_unresolved`: unresolved adjacency 제거. 이들은 서로 다른 op count와 비용 `c_mark_unresolved`, `c_resolve`, `c_delete_unresolved`를 가지며 모두 미승인이다. `mark_unresolved`는 M3 방향 정확도 분모를 줄여 보이는 점수를 높일 수 있으므로 metric report에서 M3 unresolved rate를 같이 산출하고, 오류부담 utility는 reversed+unresolved event count를 유지한다. 한 연산으로 여러 원 지표가 변할 수 있다. 따라서 전후 네 지표와 모든 count/denominator를 전부 재계산해 저장한다. 다만 특정 metric subset 정책은 그 subset의 오류 사건으로 직접 정당화된 후보만 선택하며, 분모만 변해 생긴 ratio 개선을 직접 repair gain으로 삼지 않는다. 같은 edit은 한 번만 실행·청구한다. DAG 위반 edit은 거부하고 후보 소진과 cycle rejection을 구분한다.

## 5. 정책 집합과 공유 비용 greedy 후보

`S0=∅`는 무수정. 나머지는 `{M1,M2,M3,M4}`의 모든 nonempty subset 15개다. 각 정책은 동일한 `G0, G*, task, candidate set, cost schedule, B, tie rule`에서 시작한다.

### Policy utility candidate (미승인 선택)

비율 분모 변화를 배제하는 실행 가능한 후보 효용을 둔다. 두 정규화는 구별한다. **초기 오류 개수 정규화**의 분모는 `G0`의 해당 잔존 오류 개수다. **고정 opportunity 정규화**의 분모는 `G0`에서 고정한 metric support다: M1 off-task true adjacency, M2 off-task predicted adjacency, M3 off-task true adjacency, M4 component별 support(FN=task true adjacency, FP=task predicted adjacency, REV=task oriented true adjacency, UNRES=task matched true adjacency). 0인 분모는 NA로 두고 그 component를 utility 계산에서 제외한다. M1/M2/M3 공식 rate 분모는 변경하지 않는다. 두 scheduler denominator는 원 지표의 보고 정의가 아니라 정책 보조효용 선택지다.

각 목표 metric `m`의 residual burden `e_m(G)`를 후보 정의한다. 초기 오류 정규화: M1 `FN_off(G)/FN_off(G0)`, M2 `FP_off(G)/FP_off(G0)`, M3 `(REV_off+UNRES_off)(G)/(REV_off+UNRES_off)(G0)`, M4는 component별 `E_{4,r}(G)/E_{4,r}(G0)`. 고정 opportunity 정규화는 같은 분자를 `G0`의 앞 문단 support denominator로 나눈다. 0 분모는 inactive/NA이며 가짜 gain을 만들지 않는다. M3 official `M3_acc`와 `M3_unresolved`는 계속 별도 보고하고, `REV+UNRES`는 reversal→unresolved를 repair로 보상하지 않는 scheduler proxy다. M4 scalar 후보는 active component 집합에서 renormalized nonnegative `β`를 적용한 `e_4=Σ_r β_r^active e_{4,r}`이며 β는 OPEN이다. 해당 정규화에서 각 repair의 gain은 실제 전후 error event count 변화로부터 계산한다. 코드에 수동 GAINS 상수를 넣지 않는다.

선택 subset `S`에서 `P_S(G)=|S|^{-1}Σ_{m∈S}e_m(G)`를 subset structural burden, `U_S(G)=1-P_S(G)`를 그 정책용 utility 후보로 정의한다(초기 오류 정규화는 baseline에서 `P_S(G0)=1`이 되며, fixed-opportunity 버전은 이 성질이 보장되지 않으므로 상수 이동은 ranking에 영향 없음). 비용 가능·DAG-valid 후보 edit `o` 중 `ΔU_S(o)/c(o)=[P_S(G)-P_S(G_o)]/c(o)`를 최대화한다. 각 edit은 direct event를 실제로 줄이는 경우에만 positive gain이며 같은 연산은 한 번만 후보에 넣는다. 이 평균은 metric equal weight, M4 component `β`, M3 proxy를 포함한 **명시적 설계 선택**이며, 결과 생성 전에 사용자 승인이 필요하다. 후보 효용이 0 이하이면 stop-positive-gain; 비용이 잔여 예산보다 큰 후보는 unaffordable; 모든 후보가 cycle이면 DAG-blocked; 후보가 없으면 exhausted; remaining cost가 0이면 budget-exhausted. 이 정지 사유는 별도 집계한다.

Tie는 (1) 더 큰 `ΔU/c`, (2) 사전 고정 metric order `M1<M2<M3<M4`, (3) canonical unordered pair ID, (4) operation order add/delete/orient/mark_unresolved/resolve/delete_unresolved 순으로 결정하는 후보를 제안한다. 허용 오차 및 canonical ID 규칙 역시 승인이 필요하다. 매 accept 후 모든 지표/분모/후보 feasibility를 재계산한다. 선택된 연산의 total cost는 `C(π)=c_add n_add+c_del n_del+c_ori n_ori+c_mark n_mark+c_resolve n_resolve+c_delete n_delete+…`; 비용 mapping은 미승인이고 모든 시점에서 `C(π)≤B`여야 한다.

### 균등 quota 비교 정책

Quota는 greedy와 다른 comparator다. 후보 V2 정의대로 reference cost `c_ref=1`에서 `N_ref=floor(B/c_ref)` edit-count slots를 subset의 metric들에 균등 분배하고 잔여 slot은 M1→M2→M3→M4 순으로 준다. Actual cost cap `C≤B`도 별도로 적용한다. `c_ori=2/3`이면 slot이 있어도 비용 불가로 남을 수 있다. Quota의 edit-count unit 및 unused-slot transfer 여부는 확정 전이다.

## 6. 비용, 구조 벌점, 결과변수

수정 resource cost `C(π)`, 잔존 오류 벌점 `P(Gπ)`, downstream `DecisionRegret(π)`는 다른 양이다.

`P(G)=Σ_{r∈{FN,FP,REV}} w_r [E_{r,out}(G)+λ E_{r,task}(G)] + P_UNRES(G)` 후보. 초기 시나리오는 `c_add=c_del=c_ori=1`, `w_FN=w_FP=w_REV=1`, `λ=1`로 **기준 scenario 후보**를 둘 수 있으나 사용자 승인 전 고정값으로 취급하지 않는다. `P_UNRES`의 포함 방식, λ가 task total multiplier인지 incremental `1+λ`인지, M4 추가 α 여부는 결정 대기다. event-level `w_r`와 λ를 한 번만 곱하고 M4 alpha를 중복 적용하지 않는 Option 1을 우선 후보로 둔다. unresolved를 무벌점으로 만들지 않는다.

원 비용 문서의 후보 민감도 `w_FN/w_FP∈{1/4,1/2,1,2,4}`, `c_ori/c_add∈{1,2,3}`, `c_del=c_add`, variable `w_i~Exp(1)`-derived orientation cost, ρ tradeoff curve, threshold ratios와 budget–penalty curve를 보존한다. ρ sweep domain과 threshold 식은 미지정이며 사용자 승인 전 실행하지 않는다.

subset `S`별 scheduler의 myopic 목표는 `min P_S(Gπ)` subject to `C(π)≤B`; greedy는 한 단계마다 `ΔU_S/cost`를 고르는 휴리스틱이지 `P_S`의 전역 최소값을 보장하지 않는다. `P_S`는 subset 내부의 정규화 error burden이고, `P_all(Gπ)`는 모든 정책을 동일하게 평가할 별도 공통 잔존 벌점(예: event-wise `w_r`와 zone multiplier 한 번 적용)이다. 둘은 동의어가 아니며 계수/정규화 승인이 필요하다. `ρ`가 포함된 `min[C(π)+ρP_all(Gπ)]`는 별도 tradeoff sensitivity다. Regret은 이후 별도 outcome 평가기에서 `L_GT(aπ)-min_{a∈A}L_GT(a)`로 계산한다. GT outcome 입력은 policy scheduler에 제공하지 않으며, `P_S` 또는 `P_all` 최소화가 regret 최소화와 같다고 전제하지 않는다. 비용 단가는 연구 내 structural resource 단위이지 실제 제조공정 경제비용이 아니다.

## 7. 예산, feasibility, 보고

`B∈{0,1,2,3,4}`는 fixture 검토 grid일 뿐 승인된 본 실험 grid가 아니다. 비용 시나리오 `c_ori/c_add∈{1,2,3}`, `c_del=c_add`에서 매 정책·subset별 affordable candidates, applied edits, `C(π)`, unused cost, cycle rejects, stop reason, 최종 graph hash, metric outcomes를 기록한다. B=1, c_ori=2/3에서 orientation candidate는 infeasible이고 이를 policy failure/zero regret으로 처리하지 않는다. 결과 reporting에서는 16 catalog 중 최소 벌점은 “catalog 내 최선”이며, 전역 edit sequence optimum이 아니다. Exhaustive optimizer는 추가한다면 별도 oracle로 정의해야 한다.

정책 구별 가능성은 subset × B × cost schedule × fixture별로 실제 final graph/trajectory를 비교한다. 명목 전략 수가 고유 graph 수와 같다고 간주하지 않는다. 소형 DAG 검증은 연구 SCM, intervention effect, Decision Regret 또는 정책 우월성의 증거가 아니다.

## 8. 분석 및 정보 경계

Stage 1 개발 자료에서 candidate utility·tie/normalization을 정하고, 별도 미열람 evaluation 자료에서 structural penalty–Decision Regret 관계를 평가하는 별도 설계가 필요하다. 가중치 학습 자료는 정책 설계와 최종 평가에 재사용하지 않는다. 기존 Step 5/6은 공개·분석 완료됐으므로 이 복원 연구의 untouched evaluation set이 아니다. Oracle selector와 non-oracle deployable algorithm 결과는 표와 해석 모두 분리한다. 이 후보 문서는 새 연구의 사전등록, 실험 승인, 확정 sample size 또는 선택된 가중치가 아니다.

## 9. 승인 전 결정 목록

1. M4 backdoor 정의와 conditioning set; task FP rule A 주 분석/B 보조 여부.
2. M2 denominator, M3 unresolved denominator 및 small/zero denominator disposition.
3. M3 policy proxy, M4 component normalization/`β`, metric equal weighting 승인 여부.
4. Candidate edit eligibility, unresolved resolve/delete 비용 및 operation tie order.
5. Greedy를 주 comparator로 할지; quota A slot/unused transfer/cost interaction.
6. `w_FN,w_FP,w_REV,λ,P_UNRES,ρ` 기준·민감도 범위와 추정자료 분할.
7. B grid, cost schedule, 16개 catalog vs separately labelled exhaustive oracle.
8. 개발·가중치 학습·독립 평가 모집단/표본/통계계약.

이 목록이 승인·기록되기 전에는 구현 또는 실험 실행 불가다.

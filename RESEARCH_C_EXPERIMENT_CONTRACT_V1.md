# 연구 C 주 실험 계약안 v1

**상태: USER_APPROVED / INTERNALLY_FROZEN / NO_EXTERNAL_PUBLIC_REGISTRATION**

**결정 반영 주석:** A2, P1, 계층 Task sampling은 이전 사용자 승인이다. 2026-11-23 사용자는 나머지 §10.1–10.4 A/B/C 과학적 계약과 Production 자원 상한, Development seed `2026112301`, N=64/cap=386, Held-out N=200/cap=1,104, paired-t CI와 SCM bootstrap 10,000회, 실패·shortfall 무대체를 승인했다. Rule B와 대체 정규화 민감도는 이번 주 실험 범위에서 제외한다. 이 문서는 내부 승인 계약이며 외부 공개 registry 등록을 의미하지 않는다. 실제 Development 실행은 config·manifest·비실행 Preflight 이후 별도 실행 승인 전까지 금지된다.

이 계약안은 기존 연구 A/B의 Step 4 동결 계약, 데이터, 원시 결과를 바꾸지 않는다. 승인 이후에도 새로운 SCM·관측자료·개입 효과·Decision Regret은 아직 생성하지 않았다. 연구 C 코호트와 결과는 아직 없다.

## 1. 연구 질문과 주장 범위

**주 질문:** 제한된 수정 예산에서 불완전한 인과그래프의 어떤 구조 오류를 우선 수정할 때, 정답 SCM에서 평가한 조작 Decision Regret이 줄어드는가?

이것은 오류를 정답 그래프와 비교해 찾는 **Oracle-assisted 구조 진단 실험**이다. 정답 DAG는 과제 구역, 오류 종류, 수정 후보를 정하는 데 쓴다. 정답 계수, 개입 반응, 행동별 GT loss, GT 최적 행동, Decision Regret은 수정 후보의 허용·순위·tie-break에 들어가지 않는다. 따라서 결과는 정답 구조를 이용한 진단의 결과이며, 오류를 실제로 발견할 수 있는 배포 시스템의 성능을 뜻하지 않는다.

구조 부담 감소와 Regret 감소는 서로 다른 결과다. Shared Greedy는 아래의 구조 대리효용을 줄이는 myopic 정책이며 전역 최소 구조오류나 최소 Regret을 보장하지 않는다.

## 2. 승인된 주 분석 계약

### 2.1 분석 단위 및 대응 구조

- 독립 단위: 새로 생성되는 SCM 하나.
- 각 SCM 안에서 사전 지정한 과제 `(X,Y)`, 초기 추정 그래프 `G0`, 행동 후보 집합, 관측자료를 공유한다.
- S0, 15개 subset 정책, Canonical Oracle Baseline을 동일 SCM과 같은 입력에서 실행한다.
- 각 정책·예산의 재학습과 결과는 SCM 안의 반복 측정이다. 노드·간선·오류유형·정책을 독립 표본으로 세지 않는다.
- 기존 Step 5/6 SCM은 새 연구의 개발·평가 표본에 포함하지 않는다.

### 2.1a 모집단 gate — A2 반영

strict indirect-only task 적격성은 유지한다. 다만 FN·FP·REV의 legacy Q-common recipe가 모두 존재해야 한다는 추가 admission gate는 사용하지 않는다. 특정 오류 수정 기회가 없는 경우 해당 지표 정책은 정상적인 no-op일 수 있으며, G0 오류 0건도 결과를 본 뒤 제외하지 않는다. Q-common 여부와 recipe support 수는 secondary subset 분석을 위해 별도 기록한다. A2는 승인되었다. 나머지 SCM/G0·정책·평가·표본·운영 계약은 2026-11-23 사용자 승인으로 확정되었으며, 실제 Development 실행은 별도 승인 전까지 차단한다.


### 2.1b Task 모집단 생성 — 계층 추출 선택 승인

Task sampler의 실제 동작을 유지하는 계층 방식은 이전에 승인되었다. 이후 2026-11-23 사용자 승인으로 나머지 과학적·운영 계약도 내부적으로 고정되었으며, 실제 Development 실행은 별도 승인 전까지 금지된다.

- 고정 strata 순서는 `TEMPLATES`의 기존 순서(chain_mediation, fork_branch, observed_common_cause, multiple_directed_paths) 각각에 노드 수 6, 7, 8, 9, 10을 결합한 20개 `(topology,node_count)` cell이다.
- 각 proposal은 `(cohort, master_seed, proposal_id)`와 counter를 포함한 `step4c1-stratum-v1|...` 문자열의 SHA-256 digest를 계산한다. `2^256 - (2^256 mod 20)`보다 작은 digest만 받고 나머지는 counter를 늘려 다시 hash한다. 수락된 정수를 20으로 나머지 계산해 stratum을 결정한다. 이는 modulo bias를 없앤 결정적 hash 기반 의사무작위 배정 규칙이며 순환 순서 배정은 아니다. 같은 식별자와 seed는 같은 stratum을 재현한다.
- Stratum에 맞춰 topology를 생성·relabel하고, topology 내 strict indirect-only ordered task pair를 기존 seeded uniform-index 규칙으로 선택한다. 직접 `X→Y`가 있는 pair는 strict indirect-only가 아니므로 제외한다. `observed_common_cause` template에서 scaffold action-target pair가 strict indirect-only 후보이면 그 pair를 우선 선택하고, 아니면 기존 후보 선택을 사용한다.
- A2 모집단에서는 strict indirect-only task가 없는 proposal은 구조 부적격이다. FN/FP/REV recipe support가 없다는 이유만으로는 추가 gate를 적용하지 않고 Q-common 상태는 보조 플래그로 둔다.

따라서 proposal 단계의 hash stratum assignment가 고정 seed 아래 20개 층의 실제 표본 수를 정확히 같게 보장하지 않으며, topology별 적격률과 admission conditioning 때문에 admitted SCM의 층 분포는 proposal strata 분포와 다를 수 있다. 층별 strict task pair의 개수 차이와 observed-common-cause scaffold 우선 규칙도 최종 task 분포에 영향을 준다. 이 설계는 전역 eligible `(X,Y)` pair-uniform 모집단이 아니다. 주 분석에서 사후 재가중은 하지 않는다. 층별 admitted 수는 기술통계로 기록할 수 있지만, 작은 층의 정책 성능 우월성을 단정하지 않는다. 추론 범위는 사전 지정된 합성 SCM 생성 규칙 및 strict-task 적격성 조건부 모집단이며 실제 제조공정 전체나 전역 pair-uniform 모집단으로 무조건 일반화하지 않는다.

### 2.2 승인된 Task zone

주 분석의 구조 task zone은 정답 DAG에서 다음 간선의 합집합으로 정의한다.

1. `X`에서 `Y`로 가는 모든 단순 유향 경로의 간선.
2. 빈 조건화 집합에서 열린 backdoor 경로의 간선. 경로는 `X`로 들어오는 화살표로 시작하고, 내부 노드는 collider가 없어야 한다.

Collider가 있는 경로는 무조건화 상태에서 차단된 것으로 분류한다. 특정 covariate 조건화는 주 분석에 포함하지 않는다. 이는 구조적 관련성 규칙이며 실제 개입 손실의 증명은 아니다.

### 2.3 오류 귀속 및 원 지표

모든 비순서 node pair는 하나의 추정 상태(absent, unresolved, 방향 있는 adjacency)만 갖는다. 오류 사건 하나는 아래 우선순위로 정확히 하나의 metric bucket에 배정한다: task zone이면 M4, 그 밖의 참 adjacency FN이면 M1, 참 adjacency REV/UNRES이면 M3, 참에 없는 비과제 adjacency FP이면 M2. 정답 방향과 같은 추정 adjacency는 오류 사건이 아니다.

- **M1:** 비과제 참 adjacency 중 추정에서 누락된 수 / 비과제 참 adjacency 수.
- **M2:** 비과제 FP 수 / 추정된 비과제 adjacency 수. 추정 adjacency 분모 증대로만 낮아진 비율을 repair gain으로 인정하지 않는다.
- **M3:** 정답 방향 adjacency / 방향이 정해진 추정 참 비과제 adjacency를 방향 정확도로 보고한다. UNRES 수와 추정된 참 비과제 adjacency 중 UNRES 비율도 별도로 보고한다. REV와 UNRES를 합친 잔존 오류 수는 policy proxy로만 사용한다.
- **M4:** 과제 구역의 `FN, FP, REV, UNRES` count vector를 유지한다. 각 count와 support를 함께 기록한다. 단일 공식 점수로 축약하지 않는다.

공식 rate의 분자·분모, count를 함께 저장한다. 0 denominator는 수치 0이 아니라 NA 및 이유로 기록한다. 작은 분모도 제외 사유가 되지 않으며 count와 함께 노출한다.

### 2.4 FP 귀속

**주 분석 Rule A:** GT-absent estimated adjacency의 두 endpoint가 task-zone node set 모두에 속할 때 task FP로 귀속한다. 다른 FP는 M2로 간다. 단순 endpoint 집합 규칙이므로 실제 causal harm을 보증하지 않으며, task-node 내부 chord FP까지 M4로 넓게 태그할 수 있다.

**승인 범위 제외 — Rule B (실행 금지):** A에 더해 정확히 한 endpoint가 task-zone node set에 있는 boundary FP를 평가한다. 실행 가능한 B의 제안 정의는 추정 방향의 FP 간선을 GT DAG에 단독 추가했을 때, 그 간선이 X→Y 유향 경로 또는 열린 무조건화 backdoor 경로에 포함되는 경우에만 task FP로 태그하는 것이다. UNRES FP는 가능한 두 방향 중 하나라도 해당 경로를 만들면 task로 태그하는 보수 규칙을 제안한다. 여러 FP의 상호작용으로만 생기는 경로는 이 단일-edge 민감도에 포함하지 않는다. 구현 전 이 규칙을 별도 손그래프로 검증한다.

위 Rule B 정의는 기존 검토 문서 보존용이며 이번 승인 실험에서는 실행하지 않는다. 주 분석은 Rule A만 사용한다.

### 2.5 승인된 정책 집합 및 원자 수정

`S0` 무수정 1개와 `{M1,M2,M3,M4}`의 모든 비공집합 부분집합 15개를 유지한다. Canonical Oracle Baseline은 이 16개와 별도 comparator다. 기존 연구 B의 ID-ordered Global과 같은 정책으로 취급하지 않는다.

승인된 repair 연산은 참 방향 adjacency add, FP adjacency delete, REV orient, UNRES를 참 방향으로 resolve다. UNRES adjacency 삭제는 UNRES를 FN으로 바꾸며 이득을 보장하지 않으므로 주 후보 집합에서 제외한다. 오류를 UNRES로 바꾸는 mark/abstain 연산도 repair 후보로 허용하지 않는다. 연산 단가는 실제 제조 원화가 아닌 연구 내 상대 자원 단위다.

정책은 선택 subset의 오류 사건으로 직접 정당화되는 후보만 고려한다. 각 적용 후 오류, DAG, 비용, 지원 분모와 나머지 후보를 다시 확인한다. 이벤트가 실제로 사라지지 않은 후보 gain은 0이다. 여러 지표의 공식 rate가 함께 변하더라도 원 지표 전체의 전후 값과 오류 count를 모두 보고한다.

### 2.6 Greedy 점수 — 승인된 주 분석

각 metric `m`의 고정 분모는 G0에서 한 번 정한다. G0에서 zero support인 metric은 그 SCM의 policy utility에서 비활성으로 두되, 사전 선택된 subset의 metric 수는 유지해 다른 metric의 가중치가 사후로 커지지 않게 한다. metric 공식 보고값의 분모는 이 policy denominator와 별개다.

- M1 residual: 비과제 FN 수 / G0 비과제 참 adjacency support.
- M2 residual: 비과제 FP 수 / G0 추정 비과제 adjacency support.
- M3 residual proxy: 비과제 `(REV+UNRES)` 수 / G0 비과제 참 adjacency support.
- M4 residual component: 각 task error count / 해당 M4 component의 G0 support. G0에서 오류가 존재하고 support가 양수인 성분만 active로 둔다. active FN/FP/REV/UNRES 성분의 β는 같은 값으로 정규화한다.

선택 subset `S`에 대해 `P_S(G)=Σ_{m∈S} e_m(G)/|S|`. 허용 후보 점수는 `(P_S(before)-P_S(after))/operation_cost`이다. 후보 선정에 GT effect/loss/Regret은 쓰지 않는다. 이 고정 opportunity 점수는 M4 성분이 작은 support를 가질 때 사건당 gain을 크게 만들 수 있다. 이는 주 분석의 해석 대상이며, ‘구조적으로 중립적인 점수’라고 주장하지 않는다.

결정적 tie order는 점수 내림차순, M1→M2→M3→M4, canonical unordered pair ID, add→delete→orient→resolve 순으로 제안한다. 허용 부동소수 비교오차와 canonical ID 규칙은 구현 전에 설정으로 명시해야 한다.

### 2.7 비용·구조 벌점·Regret 분리

승인된 주 비용표는 add/delete/orient/resolve 각각 1이다. 같은 수정을 중복 청구하지 않으며 총 비용 `C(π)≤B`를 강제한다. 비용은 통화나 실제 제조공정 비용 추정치가 아니다.

공통 구조 벌점 `P_all` 정의는 모든 오류 유형을 같은 기본 단위로 한 번씩 세고, UNRES도 명시적으로 포함한다:

`P_all(G)=Σ_r w_r [E_{r,off}(G)+λ E_{r,task}(G)]`, `r∈{FN,FP,REV,UNRES}`.

기준 제안은 모든 `w_r=1`, task multiplier `λ=1`이다. 여기서 λ는 task event 전체에 곱하는 **총 배수**이며 incremental `1+λ`가 아니다. M4 aggregate 추가 가중치를 곱하지 않는다. 주 분석 λ=1은 위치와 무관한 동일 사건 벌점이다. `P_all`은 정책 공통 기술 결과이지 Greedy 점수 또는 Decision Regret이 아니다.

각 수정 그래프를 동일 SCM 관측자료로 적합한다. 정책별 추천 action의 손실은 별도 GT evaluator가 계산한다:

`R(i,p,b)=L_GT(a(i,p,b))-min_{a∈A} L_GT(a)`.

**승인된 P1 primary**는 B=2에서 S0와 Full Greedy(`M1+M2+M3+M4`)를 같은 SCM별로 비교하며 `delta_i = R(i,S0,2)-R(i,FullGreedy,2)`로 정의한다. 양수는 Full Greedy의 regret이 더 낮음을 뜻한다. Primary 효과량은 독립 SCM들의 `delta_i` 평균이다. 단일 SCM Runner는 `delta_i`만 기록하고 cohort 평균이나 신뢰구간을 계산하지 않는다. 일반 정책 대비 진단에는 `R(i,p,b)-R(i,S0,b)`를 계속 보존할 수 있지만, 이는 P1의 부호 정의와 별도다. 모든 손실은 같은 SCM, action candidate set, 목표, 표준화와 GT evaluator에서 비교한다.

### 2.8 예산 및 정책 보고

전체 실행 grid는 B=0,1,2,3,4로 유지한다. 통계 분석 역할은 B=2 P1 primary, B=1 보조, B=3/4 포화 진단, B=0 무수정 기준이다. 모든 정책은 각 B에서 별도로 기록하며 예산 간 평균으로 합치지 않는다. Fixture는 이 grid에서 결과 중복이 가능함을 확인했지만, population에서의 중복률을 추정하지 않는다.

SCM마다 graph hash·수정 trajectory·error type과 task tag·후보 수·cost·unused budget·stop reason·중복 최종 graph·모델 예측·선택 action/k·GT chosen/best loss·Regret을 보존한다. Graph change, fitted prediction, action change, Regret change를 순서대로 분석한다. 같은 action/k가 선택되면 동일 GT loss와 regret이어야 한다. 같은 graph인데 model/recommendation이 다르면 구현 일관성 문제로 점검한다.

동률 정책 결과는 독립 표본/독립 정책 성능으로 세지 않는다. 그래프 hash와 선택된 action/k를 별도 비교한다. Canonical Oracle은 같은 G0, 후보, GT structural info, budget, cost와 DAG 제약을 받지만 canonical metric ordering으로 후보를 실행한다. 이는 비교 가능한 oracle diagnostic baseline이지 전역 최적해가 아니다.

## 3. 민감도 분석 — 제한된 one-factor-at-a-time

민감도는 주 분석을 대체하지 않으며 B=2에서 한 번에 한 축만 바꾼다. 상호작용을 해석하지 않는다.

1. **현재 승인 범위에서 제외:** G0 초기 오류 수 대체 정규화는 실행하지 않는다.
2. **현재 승인 범위에서 제외:** FP Rule B는 실행하지 않으며 Rule A만 주 분석에 적용한다.
3. `c_orient=c_resolve`의 상대 단가 1, 2, 3; 다른 단가는 1.
4. task multiplier λ의 0.5, 1, 2 (주 분석 1 포함).
5. M4 β의 동일 활성 성분 기준 대 FN 2배, UNRES 2배 stress vector. 두 stress vector는 중요도 추정치가 아니라 민감도용이다.

방향 수정 비용, λ 및 M4 β 민감도는 §10.3에 제안된 고정 후보만 허용한다. Rule B와 대체 정규화는 현 승인 실험에 포함하지 않는다. 세부 후보·시나리오를 outcome 열람 뒤 바꾸지 않는다. ρ tradeoff, 가중치 학습, 비용 최적화·exhaustive edit optimizer, equal quota, 추가 정책은 본 주 실험 밖으로 둔다.

## 4. 승인된 코호트·표본 수와 제한

- Development: admitted 독립 SCM 목표 64개, proposal cap 386회.
- Held-out: admitted 독립 SCM 목표 200개, proposal cap 1,104회.
- N은 admitted SCM 목표이지 complete-pair 또는 정책 평가 행 수가 아니다. 적격 후 평가 실패와 cap shortfall을 그대로 기록하며 성능에 따라 표본을 대체하지 않는다.
- P1 불확실성: 95% paired-t CI; 보조 SCM-level percentile bootstrap 10,000회. `s_max/h` 결과 기반 자동 증액은 사용하지 않는다.
- 64/200은 power 또는 효과 정밀도 보장이 아니다. 실패 후 complete-pair 표본이 줄면 해당 분모와 실패율을 함께 보고하고, complete-case 추정량을 무조건 전체 admitted 모집단 평균으로 일반화하지 않는다.

## 5. 현재 승인 범위 및 제외 항목

승인된 모집단은 4개 topology template, 노드 6–10개, signed linear acyclic SCM, G0 오류 제안 확률 `q=0.15`, `r=0.05`, true-edge 손상 시 FN/REV/UNRES 조건부 동일확률, no-redraw DAG 거절, 계층 Task sampler 및 A2 strict indirect-only admission이다. 승인 설정의 정확한 내용은 `RESEARCH_C_APPROVAL_DECISION_BRIEF.md` §10과 Development 승인 Configuration에 결합한다.

정책은 기존 M1–M4, S0·15개 비공집합 subset·Canonical Oracle, Rule A, G0-fixed opportunity only, 기존 비용·벌점·가중치, B=0–4 grid를 사용한다. Rule B와 대체 정규화 민감도는 이번 주 실험 범위에서 제외한다. 나머지 제한 민감도도 §10.3에 정해진 후보만 적용하며 결과 열람 후 변경하지 않는다.

## 6. 승인 지위와 실행 Gate

A/B/C 과학적 계약과 §10.4 Production 자원 상한은 2026-11-23 사용자 승인으로 내부 확정됐다. 이는 외부 공개 registry 등록을 의미하지 않는다. 승인 Config·Manifest와 비실행 Preflight를 준비하되, Development 코호트 시작은 별도 실행 승인 전까지 금지한다. Held-out 실행도 별도의 후속 승인이 필요하다. 이 문서와 준비 과정에서 연구 SCM, 관측자료, 실제 연구 Decision Regret을 생성하지 않았다.

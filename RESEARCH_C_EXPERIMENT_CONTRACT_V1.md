# 연구 C 주 실험 계약안 v1

**상태: 승인용 제안서 / NOT APPROVED / NOT FROZEN / NOT PREREGISTERED**

**결정 반영 주석:** 사용자는 A2(Strict indirect-only task 유지, Q-common recipe support gate 제거, 기회 부재·무오류 G0 포함)와 P1(B=2 Full Greedy 대 S0, SCM별 `R(S0)-R(Full Greedy)`)만 승인했다. 이 두 선택만 계약에 반영한다. 나머지 A/B/C 설정은 여전히 제안이며, 본 문서는 전체 승인·동결·사전등록 상태가 아니다.

이 계약안은 기존 연구 A/B의 Step 4 동결 계약, 데이터, 원시 결과를 바꾸지 않는다. 새로운 SCM·관측자료·개입 효과·Decision Regret은 이 문서를 준비하면서 생성하지 않았다. 연구 C 코호트와 결과는 아직 없다.

## 1. 연구 질문과 주장 범위

**주 질문:** 제한된 수정 예산에서 불완전한 인과그래프의 어떤 구조 오류를 우선 수정할 때, 정답 SCM에서 평가한 조작 Decision Regret이 줄어드는가?

이것은 오류를 정답 그래프와 비교해 찾는 **Oracle-assisted 구조 진단 실험**이다. 정답 DAG는 과제 구역, 오류 종류, 수정 후보를 정하는 데 쓴다. 정답 계수, 개입 반응, 행동별 GT loss, GT 최적 행동, Decision Regret은 수정 후보의 허용·순위·tie-break에 들어가지 않는다. 따라서 결과는 정답 구조를 이용한 진단의 결과이며, 오류를 실제로 발견할 수 있는 배포 시스템의 성능을 뜻하지 않는다.

구조 부담 감소와 Regret 감소는 서로 다른 결과다. Shared Greedy는 아래의 구조 대리효용을 줄이는 myopic 정책이며 전역 최소 구조오류나 최소 Regret을 보장하지 않는다.

## 2. 제안 주 분석 계약

### 2.1 분석 단위 및 대응 구조

- 독립 단위: 새로 생성되는 SCM 하나.
- 각 SCM 안에서 사전 지정한 과제 `(X,Y)`, 초기 추정 그래프 `G0`, 행동 후보 집합, 관측자료를 공유한다.
- S0, 15개 subset 정책, Canonical Oracle Baseline을 동일 SCM과 같은 입력에서 실행한다.
- 각 정책·예산의 재학습과 결과는 SCM 안의 반복 측정이다. 노드·간선·오류유형·정책을 독립 표본으로 세지 않는다.
- 기존 Step 5/6 SCM은 새 연구의 개발·평가 표본에 포함하지 않는다.

### 2.1a 모집단 gate — A2 반영

strict indirect-only task 적격성은 유지한다. 다만 FN·FP·REV의 legacy Q-common recipe가 모두 존재해야 한다는 추가 admission gate는 사용하지 않는다. 특정 오류 수정 기회가 없는 경우 해당 지표 정책은 정상적인 no-op일 수 있으며, G0 오류 0건도 결과를 본 뒤 제외하지 않는다. Q-common 여부와 recipe support 수는 secondary subset 분석을 위해 별도 기록한다. 이 A2 모집단 규칙은 승인되었지만, SCM/G0·비용·표본·운영의 나머지 계약은 미승인이다.

### 2.2 Task zone 후보

주 분석의 구조 task zone은 정답 DAG에서 다음 간선의 합집합으로 제안한다.

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

**사전 지정 민감도 Rule B:** A에 더해 정확히 한 endpoint가 task-zone node set에 있는 boundary FP를 평가한다. 실행 가능한 B의 제안 정의는 추정 방향의 FP 간선을 GT DAG에 단독 추가했을 때, 그 간선이 X→Y 유향 경로 또는 열린 무조건화 backdoor 경로에 포함되는 경우에만 task FP로 태그하는 것이다. UNRES FP는 가능한 두 방향 중 하나라도 해당 경로를 만들면 task로 태그하는 보수 규칙을 제안한다. 여러 FP의 상호작용으로만 생기는 경로는 이 단일-edge 민감도에 포함하지 않는다. 구현 전 이 규칙을 별도 손그래프로 검증한다.

Rule B는 같은 오류의 재분류 민감도이지 주 분석 정의를 바꾸는 선택이 아니다.

### 2.5 정책 집합 및 원자 수정

`S0` 무수정 1개와 `{M1,M2,M3,M4}`의 모든 비공집합 부분집합 15개를 유지한다. Canonical Oracle Baseline은 이 16개와 별도 comparator다. 기존 연구 B의 ID-ordered Global과 같은 정책으로 취급하지 않는다.

잠정 허용 repair 연산은 참 방향 adjacency add, FP adjacency delete, REV orient, UNRES를 참 방향으로 resolve다. UNRES adjacency 삭제는 UNRES를 FN으로 바꾸며 이득을 보장하지 않으므로 주 후보 집합에서 제외한다. 오류를 UNRES로 바꾸는 mark/abstain 연산도 repair 후보로 허용하지 않는다. 연산 단가는 실제 제조 원화가 아닌 연구 내 상대 자원 단위다.

정책은 선택 subset의 오류 사건으로 직접 정당화되는 후보만 고려한다. 각 적용 후 오류, DAG, 비용, 지원 분모와 나머지 후보를 다시 확인한다. 이벤트가 실제로 사라지지 않은 후보 gain은 0이다. 여러 지표의 공식 rate가 함께 변하더라도 원 지표 전체의 전후 값과 오류 count를 모두 보고한다.

### 2.6 Greedy 점수 — 주 분석 후보

각 metric `m`의 고정 분모는 G0에서 한 번 정한다. G0에서 zero support인 metric은 그 SCM의 policy utility에서 비활성으로 두되, 사전 선택된 subset의 metric 수는 유지해 다른 metric의 가중치가 사후로 커지지 않게 한다. metric 공식 보고값의 분모는 이 policy denominator와 별개다.

- M1 residual: 비과제 FN 수 / G0 비과제 참 adjacency support.
- M2 residual: 비과제 FP 수 / G0 추정 비과제 adjacency support.
- M3 residual proxy: 비과제 `(REV+UNRES)` 수 / G0 비과제 참 adjacency support.
- M4 residual component: 각 task error count / 해당 M4 component의 G0 support. G0에서 오류가 존재하고 support가 양수인 성분만 active로 둔다. active FN/FP/REV/UNRES 성분의 β는 같은 값으로 정규화한다.

선택 subset `S`에 대해 `P_S(G)=Σ_{m∈S} e_m(G)/|S|`. 허용 후보 점수는 `(P_S(before)-P_S(after))/operation_cost`이다. 후보 선정에 GT effect/loss/Regret은 쓰지 않는다. 이 고정 opportunity 점수는 M4 성분이 작은 support를 가질 때 사건당 gain을 크게 만들 수 있다. 이는 주 분석의 해석 대상이며, ‘구조적으로 중립적인 점수’라고 주장하지 않는다.

결정적 tie order는 점수 내림차순, M1→M2→M3→M4, canonical unordered pair ID, add→delete→orient→resolve 순으로 제안한다. 허용 부동소수 비교오차와 canonical ID 규칙은 구현 전에 설정으로 명시해야 한다.

### 2.7 비용·구조 벌점·Regret 분리

주 비용표 후보는 add/delete/orient/resolve 각각 1이다. 같은 수정을 중복 청구하지 않으며 총 비용 `C(π)≤B`를 강제한다. 비용은 통화나 실제 제조공정 비용 추정치가 아니다.

공통 구조 벌점 `P_all` 후보는 모든 오류 유형을 같은 기본 단위로 한 번씩 세고, UNRES도 명시적으로 포함한다:

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

1. G0-fixed opportunity 대 G0 초기 오류 수 정규화.
2. FP Rule A 대 위에 고정한 Rule B.
3. `c_orient=c_resolve`의 상대 단가 1, 2, 3; 다른 단가는 1.
4. task multiplier λ의 0.5, 1, 2 (주 분석 1 포함).
5. M4 β의 동일 활성 성분 기준 대 FN 2배, UNRES 2배 stress vector. 두 stress vector는 중요도 추정치가 아니라 민감도용이다.

세부 후보·시나리오를 outcome 열람 뒤 바꾸지 않는다. ρ tradeoff, 가중치 학습, 비용 최적화·exhaustive edit optimizer, equal quota, 추가 정책은 본 주 실험 밖으로 둔다.

## 4. 코호트·표본 수 제안 및 제한

### 제안할 개발/평가 분리

- 개발/engineering cohort: **64 SCM**을 제안한다. 목적은 pipeline debugging, G0/error coverage, 운영시간 측정과 SCM-level paired contrast의 개발 분산 산정이다. 개발 결과는 최종 정책 결론의 독립 재현으로 보고하지 않는다.
- 별도 evaluation cohort: **200 SCM을 planning candidate**로 제안한다. 이것은 기존 Step 6 자료를 재사용하거나 새 C 효과의 power를 증명하지 않는다. seed/ID namespace와 출력 디렉터리는 독립적으로 생성한다.
- 제안 N과 proposal cap은 연구 C의 SCM/task/G0 eligibility 및 자원 측정 전에 고정할 수 없다. 개발 결과로 evaluation N을 조정한다면 조정식과 목표 precision을 evaluation 열람 전에 고정하고, evaluation 결과를 본 뒤 N을 바꾸지 않는다.

기존 연구 B의 paired SCM SD 0.0824를 계획 참고 범위로만 대입하면, 정규근사 평균 SE의 1.96배는 N=64에서 약 0.0202, N=200에서 약 0.0114다. 연구 C는 정책·초기 graph·비교 수가 달라 실제 분산이 이와 같다는 근거가 없으므로 이 수치는 power 계산이나 보장된 CI 폭이 아니다. 사용 가능한 근거는 독립 단위가 SCM인 점, Step 5/6에서 64/200 코호트 운영이 가능했던 점, 그리고 C 기본 workload가 SCM당 B=1–4에서 약 65개 repair-model paths(16 repaired variants×4 budgets + S0 1개; graph hash가 같으면 실제 계산을 안전하게 공유 가능)라는 구조적 추산뿐이다. 민감도 workload는 여기에 중앙 B=2의 사전 고정 scenario 수만큼 추가된다.

따라서 64/200은 **주요 표본 목표 후보**이며 통계적 sufficiency가 아니다. 단일 최종 N은 별도 승인 묶음에서 개발 분산/운영 자원과 목표 기술적 정밀도를 함께 검토해 확정한다. 확인적 우월성 검정이나 Step 5/6의 결과 기반 재사용은 제안하지 않는다.

## 5. 아직 필요한 연구 범위 선택

실험에 들어가기 전에 가장 큰 대상 모집단 선택은 아래 중 하나로 고정해야 한다.

- **좁은 재사용 generator family:** 새 RNG namespace로 Step 4의 signed linear SCM family를 새로 표집하되, C 전용 task와 G0 계약을 사전 지정한다. 기존 SCM/원시자료는 재사용하지 않는다.
- **넓은 신규 corruption population:** C 전용 topology/task sampling과 G0 오류 생성 법칙을 새로 지정한다. 이 경우 지원 범위가 넓어질 수 있지만 생성 법칙과 오류율 자체가 새 연구 가정이 된다.

현재 문서만으로는 G0의 초기 오류 생성법(학습기 출력인지, 오류 주입인지), 과제쌍 추출 규칙, 구조 적격·attempt cap을 결정할 수 없다. 이것은 결과 분포를 직접 바꾸는 핵심 결손이므로, 아래 승인 없이 모집단 대표성이나 자연 발생 오류에 대한 주장을 하지 않는다.

## 6. 승인 지위

이 문서는 실행 가능한 단일 기준안과 제한 민감도 후보를 제안하지만 승인된 설계나 preregistration이 아니다. 사용자 승인을 기록하고, G0/task/population 생성계약·평가 pipeline·정확한 표본·resource/stop rules를 재현 가능한 설정으로 고정한 후에만 새 SCM 실행을 별도 승인받는다.

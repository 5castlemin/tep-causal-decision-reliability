# 비용·잔존 벌점·Decision Regret 명세

**상태: 계약 제안; 계수·가중치·예산은 동결되지 않음.** 비용 원문 사본 `비용을 어떻게 할까.docx` SHA-256 `a3d26fe83b736a6950c64ce54e2fca7b131582e6da19e3ea6e6aedbdef7c0818`. DOCX 원문은 표준 단가가 없다고 밝히고 시나리오 설계를 제안한다. 로컬 이름은 요청된 `(1)` 버전과 다르지만 byte hash가 기준값과 일치한다.

## 1. 세 가지 양을 분리

### 수정 자원 비용

수정 정책 `π`가 수행한 연산 수를 `n_add(π), n_del(π), n_ori(π)`라 하면

`C(π)=c_add·n_add(π)+c_del·n_del(π)+c_ori·n_ori(π)`.

unresolved를 resolve/delete하는 연산을 허용할 경우 어느 단가에 귀속할지 별도 결정한다. `c_*`는 **synthetic graph-edit resource units**다. 실제 공정의 인건비·다운타임·안전비용·수율비용이 아니다.

### 잔존 구조 오류 벌점

최종 그래프의 오류 개수/율을 task zone과 non-task zone으로 분리한 뒤 후보 목적함수:

`P(G)=Σ_{r∈{FN,FP,REV}} w_r·[E_r^out(G)+λ·E_r^task(G)]`.

여기서 `w_FN,w_FP,w_REV`는 오류 종류별 잔존 피해, `λ`는 task-zone 배수다. `E`의 단위(개수 또는 비율), 각 오류의 구역 할당, unresolved 방향을 먼저 확정해야 한다. DOCX의 “배수”가 task error 총배수 λ인지 기본 피해에 추가되는 증분(1+λ)인지는 모호하므로 이 식은 후보일 뿐 승인된 완성식이 아니다. 특히 ④ scalar화에 `α` 가중치가 필요하다면 별도 정의가 추가된다.

### Decision Regret — 별도 결과 평가량

동일 SCM과 사전 지정 행동 집합 `A`에서 정책이 선택한 조작 `a_π`의 GT loss를 `L_GT(a_π)`라 하면

`R(π)=L_GT(a_π)−min_{a∈A} L_GT(a)`.

regret은 정책이 구조 오류를 수정하는 목적함수와 다르다. 비용 최적화가 잔존 구조 벌점을 낮춘다고 Decision Regret도 자동 감소하지 않는다. 두 결과는 같은 evaluation SCM에서 대응해 **관계를 검증할 수 있지만**, 원래의 정책 최적화는 training/development에서 정하고 최종 regret 평가는 분리된 평가 SCM에서 하는 것이 안전하다. 개입 후보, target, loss scale 및 실행 실패 처리는 별도 동결해야 한다.

## 2. 목적함수 후보

### 주 분석 제안: 비용 제한 잔존 벌점 최소화

`min_{π∈Π} P(G_π)` subject to `C(π)≤B`.

이는 DOCX의 “정해진 비용 안에서 개선” 원칙에 맞고 `ρ`가 필요 없다. 비교 결과의 두 축은 실제 사용 수정 비용과 잔존 벌점이며, 정책별 불가능 후보와 unused budget도 기록한다.

### 보조 분석 제안: 비용과 벌점의 trade-off

`min_{π∈Π} [C(π)+ρ·P(G_π)]`에 대해 하나의 ρ를 선택하지 않고 ρ 범위별 비용–벌점 curve 및 임계 전환을 제시한다. 비용과 벌점의 스케일/단위가 정당화되지 않으면 ρ 수치의 실질 의미도 제한적이다. 임계 비용비는 특정 오차 수정을 선택하는 순위가 바뀌는 지점이지 보편적인 가격 기준이 아니다.

**Decision Regret을 P의 대체물로 사용하지 않는다.** 잔존 오류 벌점은 정책을 정하는 구조 대리 목적, regret은 다운스트림 결과 지표다. 둘이 일치하는지를 새 자료에서 평가한다.

## 3. 원 DOCX 시나리오 보존

| 시나리오 | DOCX 값/정의 | 처리 |
|---|---|---|
| A 기준 | `c_add=c_del=c_ori=1`; 15 지표 조합 + 무수정 | 주 비용 baseline 후보. 지표 조합은 원 네 지표의 subsets이며 A–D 기존 지표와 별개. |
| B-1 | `c_ori/c_add∈{1,2,3}`, `c_del=c_add` | 방향 교정 비용 강건성. 각 B별 후보 지원이 달라질 수 있으므로 불가능 수정 수 보고. |
| B-2 | 변수 intervention cost `w_i~Exp(1)`에서 orientation correction cost 도출 | 원문 제안 그대로 보존. 변수 비용 표본/간선 단가 도출 공식은 추가 명세 필요. `w_i`는 피해 가중치 `w_FN`과 다른 개념이다. |
| B-3 | `w_FN/w_FP∈{1/4,1/2,1,2,4}`를 한 번에 한 시나리오씩 변경 | FP/FN 상대 피해 중요도 민감도. 기준 분모·scale을 고정해야 함. |
| B-4 | 회귀 기반 `w_FN,w_FP,w_REV,λ` 추정 | 개발/계수 적합 및 최종 성능평가 분리. 회귀 사양·불확실성·중복 자료 누출은 미결. |
| ρ tradeoff | 고정 ρ 하나 대신 비용–벌점 곡선 | 예산 제한 주 분석과 별도 결과군. |
| 임계 비용비 | 오류 우선순위가 바뀌는 단가비 경계 | DOCX의 0.04 대 0.02, threshold=2는 설명용 가정 예이며 실측이 아님. |

## 4. Budget 및 방향 비용 문제

단위가 이산 resource unit이면 `B=1`, `c_ori=2/3`은 reversal 수정이 허용되지 않는다. 이것은 정상적으로 infeasible/unused-cost 상태며 임의로 비용을 1로 clip하거나 후보를 대체하지 않는다.

공정한 보고 후보:

1. 원 예산 grid를 유지하고 각 cell의 비용 가능한 연산·수정률·잔여 벌점을 그대로 비교한다. 이때 서로 다른 실제 action support라는 한계를 함께 표시한다.
2. 방향 수정까지 가능한 공통 budget 영역(`B≥max c`)을 별도 비용 민감도 stratum으로 보고한다. 이것은 기준 주 분석과 별도 estimand다.
3. 각 scenario에서 동일한 nominal B와 비용표를 모든 전략에 적용한다. 정책별로 다른 예산을 맞춰 주지 않는다.

원문은 완전한 B grid를 확정하지 않는다. `B={0,1,2,4}`는 archived A–D 문서의 과거 후보였을 뿐 이 gate의 자동 승인값이 아니다. 신규 grid, 실행 단위(연산 수 또는 비용 단위), `c_ori`와 γ의 관계는 사전 승인 전 미결이다.

## 5. 16개 정책과 최선값

16개는 원 지표 subset 기반으로 정한 정책 카탈로그다(`METRIC_TO_REPAIR_POLICY_SPEC.md`). 그 중 최소 평균 penalty인 행은 “16개 비교 전략 중 관측상 최선”이다. 후보 연산 sequence 전체를 탐색한 전역 optimizer와 같지 않다. 별도 exhaustive oracle을 포함하려면 정책 집합과 상계의 의미를 사전 선언하고 배포 가능 정책과 구분해야 한다.

## 6. 추정·개발·평가 분할과 정보 경계

- 기준 구조 채점은 assessor가 reference DAG를 이용하되 정책 실행기와 물리적으로 분리한다.
- 원 지표를 개선하는 정책이 `G*`, 참조 기반 FP/FN tag 또는 task-zone tag를 보고 후보를 정하면 그 정책은 oracle 진단이다.
- 비용계수·벌점 weight를 regret 또는 결과로 학습할 경우 해당 자료를 최종 평가용으로 재사용하지 않는다. 개발/가중치 적합/정책 선택과 신규 최종 evaluation cohort를 분리한다.
- 기존 Step 5/6은 H2용으로 이미 보고·열람했으므로 원 네 지표 새 분석의 untouched holdout이 아니다.
- 계수 추정 없이 DOCX 시나리오 범위만 제시하는 분석은 실질 비용 추정이라고 주장하지 않는다.

## Gate 전에 필요한 선택

1. 오류벌점 `E`의 count/rate 및 M4 component aggregation.
2. `w`와 λ의 추정자료/분리 및 uncertainty; λ가 총 배수인지 추가 배수인지.
3. unresolved orientation의 수정 단가와 허용 연산.
4. `B` grid, fractional/integers, `c_ori>B` cell 해석.
5. ρ sweep domain 및 비용·벌점 scale.
6. 구조 벌점과 regret의 별도 primary/secondary status.
7. 후보 오류가 이미 oracle label되어 있는 정책을 main estimand로 할지, non-oracle 실행 가능 정책을 별도로 포함할지.

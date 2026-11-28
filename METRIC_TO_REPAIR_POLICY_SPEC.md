# 네 지표에서 16개 수정 전략으로의 연결 명세

**상태: 정책 설계 후보. 실행·사용자 승인·사전등록 아님.** 기존 Step 4의 14개 FN/FP/REV 순서 정책은 여기에 재사용되지 않는다.

## 전략 집합

원 네 지표를 `M1`(비과제 누락률), `M2`(비과제 허위 연결률), `M3`(비과제 방향 정확도; 미확정률은 별도 부가값), `M4`(과제 구역 오류 구성요소)라 쓴다. 비공집합 `S⊆{M1,M2,M3,M4}` 15개와 수정하지 않는 `S=∅` 기준선 하나가 총 16개 전략이다. 이는 비용 DOCX의 16-way comparison을 형식화한 것이며 기존 A–D metric set이 아니다.

## 입력/정보 조건

각 paired 실행은 동일 reference DAG, initial incomplete graph, task, allowed atomic edit universe, budget, cost scenario, DAG constraint를 공유한다. 기준 정책은 참조를 이용해 어떤 수정이 정답으로 향하는지 알 수 있는 **oracle benchmark**다. 실제 알고리즘 비교가 필요하면 별도 non-oracle 후보 생성과 동일 정보 조건을 설계해야 한다. oracle의 결과를 배포 가능한 자동 오류 발견 성능이라고 부르지 않는다.

원자 연산 후보는 참조와 현재 그래프 상태의 차이에 대해 `ADD`(정답 간선을 추가), `DELETE`(거짓 간선 제거), `ORIENT/REVERSE`(잘못된 방향 교정), `RESOLVE`(unresolved를 방향 확정 또는 제거)로 제안한다. 실제로 허용할 unresolved 연산과 `c_ori` 적용 범위는 사용자 결정이 필요하다. 한 원자 연산이 여러 metric을 개선해도 비용은 한 번만 청구하고, 모든 지표를 매 단계 재계산한다.

## 후보 정책 알고리즘

정책 `S≠∅`는 `S` 내 지표의 순차 목표개선을 사용한다. 각 선택 시 유효 후보 `o`에 대해 `Δ_j(o)=score_j(after o)-score_j(before)`를 계산하고, 지표별 개선 방향을 사전에 정규화한다(낮은 오류율은 감소가 개선, 높은 방향 정확도는 증가가 개선). 같은 연산은 다수의 `Δ_j`를 바꿀 수 있다.

보관된 A–D 초안(`ARCHIVED_METRIC_COMBINATION_DESIGN.md`)의 후보 분배 방식을 **명시적 후보**로 둔다.

1. 선택 조합의 각 지표에 고정 quota `floor(B/k)`를 할당하고 나머지 `B mod k`를 사전 고정된 지표 ID 순서로 한 단위씩 배분한다.
2. 각 지표 차례에 해당 지표의 개선량이 가장 큰 DAG-valid, 아직 허용 가능한 수정 후보를 선택한다. `Δ≤0`이면 해당 할당을 소비하지 않는다.
3. 앞 수정이 다른 목표 지표를 개선해도 같은 연산에 재과금하지 않는다. quota는 다른 지표로 이월하지 않는 버전과, unused quota를 풀에 반환하는 버전을 구별해야 한다. archived A–D 제안은 이월하지 않는 쪽이다.
4. 미사용 예산, quota, 후보 소진 및 DAG cycle 거절을 별도 기록한다.

다만 이 알고리즘은 지표가 혼합 척도(분율/정확도/count)이고 M4가 아직 scalar가 아니어서 **현재 그대로 계산할 수 없다**. metric normalization, M4 scalar/구성요소 선택, quota 단위가 비용 단위인지 edit 단위인지 확정되기 전에는 전략을 실행 가능한 계약으로 간주하지 않는다.

### 우선순위·동률·DAG 규칙

- 지표 내 우선순위: `Δ` 최대. 필요 시 `Δ/c(o)`를 쓰는 비용효율 버전은 별도 정책 버전이며 baseline 정책으로 자동 섞지 않는다.
- 동률: 먼저 지표별 numeric tolerance, 그 다음 stable canonical `(operation, unordered pair, direction)` 정렬을 후보로 둔다. 허용오차 수치는 아직 미정.
- DAG: 각 원자 연산 적용 후 DAG 여부를 검사. 실패 수정은 비용 0으로 거부하고 다음 후보를 검사한다.
- 후보 재평가: accepted edit 뒤 네 지표와 모든 후보를 재계산한다.
- 종료: 선택된 조합에서 valid positive-gain action이 없거나 budget으로 남은 edit이 없을 때. no-edit는 언제나 변경 없는 명시 기준선.

## 16개 전략 카탈로그

각 행의 고정 quota 방식은 구현을 위해 제안하는 일관된 공통 스케줄이다. `M3` 방향 정확도만을 목표로 할 때 unresolved를 orient하는 것이 목표 점수에 도움 되는지, 제거가 합리적인지 별도 결정해야 한다.

| ID | 개선 목표 `S` | 정책상 후보 우선순위 |
|---|---|---|
| S0 | ∅: 없음 | 원 그래프 그대로; 비용 0; 후회는 별도 평가 |
| S1 | {M1} | 비과제 누락률을 가장 많이 낮추는 유효 add |
| S2 | {M2} | 비과제 허위률을 가장 많이 낮추는 유효 delete |
| S3 | {M3} | 비과제 orientation accuracy 개선이 큰 orient/resolve; 미확정 처리 결정 필요 |
| S4 | {M4} | task-zone 구성요소 개선이 큰 add/delete/orient; scalarization 결정 필요 |
| S5 | {M1,M2} | quota 1/1로 각 오류율의 개선량 기준 번갈아 선택 |
| S6 | {M1,M3} | quota 1/1, 누락 및 방향 목표 순차 선택 |
| S7 | {M1,M4} | quota 1/1, 비과제 누락 및 task 오류 |
| S8 | {M2,M3} | quota 1/1, 비과제 허위 및 방향 오류 |
| S9 | {M2,M4} | quota 1/1, 비과제 허위 및 task 오류 |
| S10 | {M3,M4} | quota 1/1, 비과제 방향 및 task 오류 |
| S11 | {M1,M2,M3} | quota 1/1/1; 잔여 unit은 fixed metric order |
| S12 | {M1,M2,M4} | quota 1/1/1; 잔여 unit은 fixed metric order |
| S13 | {M1,M3,M4} | quota 1/1/1; 잔여 unit은 fixed metric order |
| S14 | {M2,M3,M4} | quota 1/1/1; 잔여 unit은 fixed metric order |
| S15 | {M1,M2,M3,M4} | quota 1/1/1/1; 잔여 unit은 fixed metric order |

표의 모든 `M4` 행과 M3 unresolved 연산은 명세 미결점 때문에 아직 executable이 아니다. S15까지 모든 행이 총 16개다. 이름만 16개여도 실제 edit trajectory가 동일할 수 있으므로, 동일한 결과를 인위적으로 다르게 만들거나 합치지 않는다.

## 예산과 공정성

주 비용 제약은 `C(π)≤B`다. 각 정책은 같은 시작 그래프·수정 후보·동일 B·비용표에서 비교한다. DOCX는 주 분석 `c_add=c_del=c_ori=1`을 제안한다. 복수 지표 quota의 단위가 비용인지 edit 횟수인지는 아직 정해야 한다.

`c_ori/c_add=2` 또는 `3`일 때 `B=1`이면 방향 수정은 불가능하다. 이를 실패로 바꾸거나 더 작은 비용으로 자동 치환하지 않는다. 결과에는 실제 가능한 후보 수, 비용 미사용, 비용 때문에 비활성된 방향 후보를 보고한다. 공통 수정 지원에서 정책 비교가 필요한 경우 `B≥max(c_add,c_del,c_ori)`인 공통 예산 stratum을 별도로 두는 방안을 검토한다. 다만 이는 다른 예산 estimand이므로 자동으로 주 분석 B를 변경하지 않는다.

## 최선 정책과 전역 최적 구별

16개 사전 정의 전략 중 empirical 평균 벌점 또는 Decision Regret이 가장 낮은 것은 **비교된 16개 중 관측상 최선**이다. 가능한 모든 graph edit sequence를 푸는 전역 최적해는 아니다. 모든 가능한 시퀀스를 exhaustively 최적화한 bounded oracle는 별도 upper-bound 진단이며 지표 기반 실행 정책/배포 방법과 구분한다. 전략 선택·추정·확인은 개발/독립 평가 분리와 별도 사전등록을 요구한다.

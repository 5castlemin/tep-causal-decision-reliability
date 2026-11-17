# 원 연구 계약 후보 — fixture 검증 기록

**범위:** deterministic hand-built DAG와 event-count arithmetic만 검증. SCM 계수·관측자료·개입 효과·Regret·비용 가중치 추정 없음. 이 검증은 사용자 미승인 후보식의 일관성만 보여주며 연구 가설 검증이 아니다.

## 기준 fixture

GT DAG: `X→A, A→Y, X→B, B→Y, T→U, P→Q`.

초기 estimate: `A→Y, X→B, B→Y, Q→P, R→S`.

Task zone의 causal portion은 두 directed path의 네 간선이다. Off-task reference edges는 `T→U,P→Q`; off-task estimate adjacency는 `Q—P,R—S`다. Oracle 후보는 (1) `X→A` add M4-FN, (2) `T→U` add M1-FN, (3) `R—S` delete M2-FP, (4) `Q→P` orient to `P→Q` M3-REV다. 각 edit은 한번씩 단독 적용했을 때 DAG-valid이며 각 edit 후에도 전체 estimate DAG-valid다. 한 조작은 한 번만 적용·청구한다.

## 수작업 기준값 및 독립 산술 확인

초기 graph에서 M1=`1/2`; M2=`1/2` (FP R—S 1개 / off-task predicted adjacency 2개); M3 accuracy=`0/1=0`, unresolved=`0/1=0` (matched off-task true adjacency는 P—Q 하나); M4 vector=`(FN=1,FP=0,REV=0,UNRES=0)`이며 task true-edge denominator 4다. M3 정확도 분모 1은 작으므로 count를 같이 보여야 한다.

| 변화 | 원 지표 재계산 | 판정 |
|---|---|---|
| Add correct off-task `T→U` | M1 `1/2→0/2=0`; M2 `1/2→1/3`; FP numerator는 계속 1; M3 accuracy `0/1→1/2`, unresolved `0/1→0/2` | M2 허위율이 분모 증가만으로 .5에서 .333…으로 떨어진다. 이를 M2 FP-repair gain으로 인정하지 않는다. |
| Delete `R—S` FP | M2 `1/2→0/1=0`; FP numerator `1→0` | 실제 false adjacency 삭제 사건. |
| Orient `Q→P` to `P→Q` | M3 accuracy `0/1→1/1`; unresolved `0/2→0/2`; off-task reversed `1→0` | 실제 방향 교정. |
| Replace another reversed true edge with unresolved, fixture C | correct=1, reversed=1: acc `.5`, unresolved `0`; 이후 correct=1, reversed=0, unresolved=1: acc `1`, unresolved `1/2` | Accuracy만 보면 오답을 미확정으로 바꾸는 것만으로 apparent gain. 둘 다 보고, residual penalty에서 UNRES를 제거하지 않는다. |
| Add `X→A` | M4 FN `1→0`, M4 task denominator는 4 | Task event repair. 다른 M1/M2/M3가 바뀌지 않음. |

### M4 event penalty double-count 점검

Task-zone FP 1건, `w_FP=2`, `λ=1`이라면 event-wise penalty는 `2×1×1=2`다. 같은 사건을 M4 aggregate `α=3`으로 다시 곱하면 6으로 세 배가 되며 동일 task event를 중복 가중한다. Candidate는 event-wise `w_r×λ`를 한 번만 적용하고 M4 vector를 별도 보고한다. `UNRES` penalty는 별도 사전 지정 없이는 0으로 암묵 처리할 수 없다.

### FP option A/B

`X→M→Y`와 boundary node `W`를 둔 GT에서 `W→X`를 FP로 추가하면, A는 W가 zone node set 밖일 때 non-task, B는 실제로 열린 `X←W→M→Y` route를 만들면 task-tag 후보로 둔다. Fixture collider `X→C←Y`는 빈 conditioning set에서 blocked이므로, undirected 연결만으로 B task-tag가 되지 않는다. GT adjacency error(FN/REV/UNRES)와 GT-absent FP tag는 별개이며, 각 false pair는 A/B 중 정확히 하나의 tag를 얻는다. A/B에 따라 M2/M4와 denominator 모집단이 바뀐다.

## 16 subset × budget fixture 검토

15 subset과 S0의 후보 edit은 위 네 사건에 대응한다. Fixture에서 모든 네 후보는 DAG-valid지만 subset 밖 metric의 후보는 사용할 수 없다. S0는 모든 B에서 무수정이다. Quota-A(M1→M2→M3→M4, `c_ref=1`)의 S15 trajectory는 B=0: no edit; B=1: T→U; B=2: T→U, delete R—S; B=3: 이어 orient Q→P; B=4: 이어 add X→A다. 따라서 B=1 S15와 S1은 동일 최종 graph다. S1은 M1 후보 하나만 있어 B≥1에서 그 후보를 한 번 적용한 뒤 budget을 unused로 둔다.

Greedy-B candidate utility는 metric별 initial-G0 오류 count로 정규화한 residual event-burden 감소량을 subset에서 평균하는 검토 후보식이다. Fixture의 per-edit gains는 M1=.5, M2=.5, M3=1.0 (초기 reversed event 1개), M4=.25. 초기 오류 count가 0이면 그 component는 NA/비활성이다. 이 fixture utility와 metric-order tie에서는 subset마다 허용 후보가 다르고 일부 subset은 같은 trajectory를 만든다. 모든 후보는 한 번만 선택 가능하다. B=0은 모든 subset에서 무수정; B=1에서 M3를 포함한 subset은 greedy가 Q→P를 우선 orient할 수 있고, S15 quota-A는 M1 우선으로 T→U를 add하므로 두 scheduler 결과가 다를 수 있다. S1과 S15 quota-A는 여전히 B=1에서 같은 T→U graph다. B=2..4는 남은 event candidate를 공유 예산에서 이어 고르며 후보 소진 후 잔여 예산은 unused다. 이는 utility normalizer와 tie order에 의존하는 feasibility demonstration이지 권고 성능 결과가 아니다.

| Nominal B | c_ori=1 | c_ori=2 | c_ori=3 |
|---:|---|---|---|
| 0 | 모든 edit 불가 | 모두 불가 | 모두 불가 |
| 1 | 4개 단독 edit 가능 | orientation 불가, add/delete 가능 | orientation 불가, add/delete 가능 |
| 2 | 4개 가능 | orientation 가능(2 cost) | orientation 불가 |
| 3 | 4개 가능 | orientation 가능 | orientation 가능(3 cost) |
| 4 | 4개 가능 | orientation 가능 | orientation 가능 |

이는 다른 edits와 누적 비용을 반영하기 전 원자 후보 affordability다. 누적 trajectory에서는 잔여 budget으로 매번 재검사한다. 비용 불가, 후보 소진, DAG cycle, positive gain 부재, budget exhaustion, unused cost는 서로 다른 stop/status 값이어야 한다. Fixture edits를 포함한 모든 tested graphs는 DAG-valid이며, cycle-producing proposed edit을 넣은 경우는 cost 지출 전에 reject하는 별도 validator assertion으로 검증한다.

검증 스크립트의 고정 gains와 tie order에서 subset별 최종 graph 고유 개수는 아래와 같다. A/B 동일 subset graph 비율은 같은 subset index의 final edge set 비교다.

| B | Quota A 고유 graph | Greedy B 고유 graph | 동일 subset 결과 |
|---:|---:|---:|---:|
| 0 | 1/16 | 1/16 | 16/16 |
| 1 | 5/16 | 5/16 | 10/16 |
| 2 | 11/16 | 11/16 | 14/16 |
| 3 | 15/16 | 15/16 | 16/16 |
| 4 | 16/16 | 16/16 | 16/16 |

예를 들어 B=1, S15에서 A는 M1 add를, B는 M3 orient를 선택한다. 이 손작업 fixture에서 예산 3 이상이면 두 scheduler가 같은 subset별 최종 그래프를 만들지만, 수정 순서가 반드시 같다는 뜻은 아니다. 이 비율들은 선택한 utility 및 tie 후보에 조건부이며 다른 사용자 승인 선택에서 달라질 수 있다.

각 scheduler 내부에서 서로 다른 ordered trajectory 수도 각 B에서 각각 `1, 5, 11, 15, 16`이다. A/B가 같은 subset에서 동일한 ordered trajectory를 만든 수는 B=0..4에서 `16, 10, 10, 10, 10`이다. 즉 B=2..4에서는 여러 쌍의 최종 그래프가 같아도 수정 순서가 다른 사례가 있다. 최종 graph 중복률만으로 정책 순서가 같다고 결론 내릴 수 없다.

## 독립 재검산 범위 및 남은 확인

손계산 fractions, subset 집합, schedule trajectory 및 acyclicity를 `scripts/validate_original_research_fixture_contract.py`에서 결정론적으로 확인했다. 이는 연구 테스트 스위트나 실제 정책 구현 검증은 아니다. 모든 15 subset의 full sequence uniqueness는 제안된 M4 normalization/β와 fixed tie rule 승인 후에야 의미 있는 실행 계약이 된다. 현재 일부 trajectory는 candidate utility 선택에 의존하므로 본문에서 empirical finding처럼 인용하지 않는다.

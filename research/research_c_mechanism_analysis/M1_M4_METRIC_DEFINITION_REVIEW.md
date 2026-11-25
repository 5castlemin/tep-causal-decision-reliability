# M1–M4 지표 정의 검토 (Research C)

작성: 2026-11-25 · 대상 코드: `main` @ `7742180` (`research/original_objective/policy_engine.py`)
근거 문서: `RESEARCH_C_EXPERIMENT_CONTRACT_V1.md` §5–§6, `RESEARCH_C_APPROVAL_DECISION_BRIEF.md`, `RESEARCH_JOURNEY_AND_TEAM_HANDOFF.md` Part 3

이 문서는 인수인계 Part 6의 1단계 산출물이다. 결과를 해석하기 전에 "공식 보고 지표"와 "Greedy 정책용 점수 `P_S`"를 나누고, 계약 문서와 코드가 같은지 확인한다. 코드와 계약은 수정하지 않았다.

## 1. 결론 요약

- **계약과 코드는 일치한다.** 오류 귀속 우선순위, 각 지표의 분자·분모, G0 고정 분모 정규화, M4 활성 성분 동일 가중, 동점 처리 순서가 계약 §5–§6의 서술과 같다. 해석 전에 바로잡아야 할 정의 불일치는 찾지 못했다.
- 다만 해석에 영향을 주는 **설계상 특징 4가지**가 있다(§4). 특히 (a) Full Greedy에서 M4 한 건의 점수가 `1/|S|`와 M4 활성 성분 수로 두 번 나뉘어 off-task 수정과 같거나 낮은 점수를 받는 경우가 많고, (b) Rule A 때문에 X나 Y에 붙은 FP도 off-task(M2)로 분류될 수 있다.
- 공식 보고 지표(M3 정확도, M4 count vector 등)는 정책 점수에 직접 들어가지 않는다. 정책은 `P_S`만 본다.

## 2. 오류 사건의 귀속 (classify)

각 비순서 노드 쌍은 GT DAG와 추정 그래프 상태를 비교해 많아야 하나의 오류 사건이 된다.

| GT | 추정 | 종류 | task zone이면 | 아니면 |
|---|---|---|---|---|
| 없음 | 있음 | FP | M4 (Rule A: 두 끝점이 모두 task-zone **노드 집합**에 속할 때) | M2 |
| 있음 | 없음 | FN | M4 (쌍이 task-zone **간선 집합**에 속할 때) | M1 |
| 있음 | UNRES | UNRES | M4 | M3 |
| 있음 | 반대 방향 | REV | M4 | M3 |

- Task zone 간선 = GT DAG의 X→Y 모든 단순 유향 경로 간선 ∪ 무조건화 상태에서 열린 backdoor 경로 간선. task-zone 노드 집합 = 그 간선의 끝점 ∪ {X, Y}.
- **주의:** 참 간선의 task 여부는 "간선 집합" 기준이고 FP의 task 여부는 "노드 집합" 기준이다. 그래서 X 또는 Y와 zone 밖 노드를 잇는 FP는 M2(off-task)다. 실제로 Held-out 사례 `…000141`의 FP `V00–V06`(V06=Y)은 M2로 분류되었다.

## 3. 공식 지표와 정책 점수

### 3.1 공식 보고 지표 (`metrics()['report']`)

| 지표 | 분자 | 분모 | 계약 대조 |
|---|---|---|---|
| M1 | off-task FN 수 | off-task 참 adjacency 수 | 일치 |
| M2 | off-task FP 수 | 추정된 off-task adjacency 수(off-task 참 간선 중 추정에 있는 것 + M2 FP) | 일치 |
| M3 정확도 | 방향이 맞는 off-task 참 adjacency | 방향이 정해진 off-task 추정 참 adjacency(정답 + REV) | 일치 |
| M3 미해결률 | off-task UNRES 수 | 추정에 있는 off-task 참 adjacency | 일치 |
| M4 | FN/FP/REV/UNRES 성분별 count와 support를 따로 보고 | FN: task 참 간선 수 / FP: task 추정 adjacency 수 / REV: 추정에서 방향이 정해진 task 참 간선 수 / UNRES: 추정에 있는 task 참 간선 수 | 일치 (단일 점수로 축약하지 않음) |

### 3.2 Greedy 정책 점수 `P_S` (`burden()`)

- 잔여오류율 `e_m(G)`의 **분모는 G0 시점 support로 고정**한다(`fixed_opportunity`).
  - M1: off-task FN / G0 off-task 참 adjacency 수
  - M2: off-task FP / G0 추정 off-task adjacency 수
  - M3: off-task (REV+UNRES) / G0 off-task 참 adjacency 수
  - M4: G0에서 오류가 1개 이상이고 support>0인 성분만 활성. 활성 성분의 `count/support`를 β=1로 동일 평균.
- `P_S(G) = Σ_{m∈S} e_m(G) / |S|`. 후보 점수 = `(P_S(before) − P_S(after)) / 비용`, 비용은 모두 1.
- 매 단계 점수를 다시 계산하고, 양의 gain이 있고 DAG를 유지하는 후보 중 최고점을 고른다. 동점은 **M1→M2→M3→M4**, 그다음 쌍 ID, 연산 순서로 깬다(계약 §6 "결정적 tie order"와 일치).
- 정지 사유: 예산 소진, 후보 소진, 양의 gain 없음, DAG 위반 후보만 남음(`dag_invalid_candidate`).
- Canonical Oracle은 같은 후보 풀을 점수 없이 고정 순서(M1→M4, 쌍 ID)로 처리한다. GT 손실·Regret은 쓰지 않는다.

## 4. 해석에 영향을 주는 설계상 특징

1. **Full Greedy에서 M4 점수가 이중으로 희석된다.** M4 한 건의 gain은 `(1/|S|) × (1/활성 성분 수) × (1/해당 성분 support)`이고 M1·M2·M3 한 건은 `(1/|S|) × (1/support)`다. 따라서 M4에 성분이 여러 개 활성이면, support가 비슷한 off-task 오류보다 점수가 낮아진다. 재생성 자료에서 Full Greedy가 수정 가능한 task 오류를 두고 off-task를 먼저 고른 단계는 Held-out B=2에서 46번(점수가 실제로 높아서 43번, 동점 규칙으로 3번), Development에서 11번(9번, 2번)이었다. 계약 §6은 "작은 support의 M4 성분이 gain을 키울 수 있다"고 우려했는데, Full Greedy 안에서는 반대 방향의 희석이 더 자주 관찰되었다. M4 단독 정책에서는 `|S|=1`이라 이 희석이 없다.
2. **동점 순서가 M4를 마지막에 둔다.** 동점은 드물지만(위 3번, 2번), 생기면 항상 off-task 쪽이 이긴다. Development `…000014`가 그 예다(그림 없이 표에만 기록).
3. **Rule A의 노드 기준 FP 귀속.** X·Y에 붙은 FP도 zone 밖 노드와 이어지면 M2가 된다. 이런 FP는 X→Y 유향 경로를 만들어 추천 행동을 바꿀 수 있으므로 "off-task = 행동과 무관"이라고 가정하면 안 된다(분석 보고서 §5.3).
4. **정책 점수는 X→Y 경로를 보지 않는다.** 재생성 자료에서 추천 모형의 예측 효과가 0인 경우와 학습용 DAG에 X→Y 유향 경로가 없는 경우가 정확히 일치했다(Dev 5,440행, Held-out 17,000행 전부). Regret은 사실상 이 경로의 존재와 부호에 좌우되는데, `P_S`는 오류 개수 비율만 보고 어떤 수정이 경로를 복원하는지는 보지 않는다. 이는 계약이 의도한 "근시안적 구조 대리목적"이며 결함은 아니지만, 메커니즘 해석의 핵심 전제다.

## 5. 확인하지 못한 것

- 원본 Windows ledger를 직접 열지 못했다. 정의 대조는 코드와 문서로 했고, 수치 대조는 이 환경에서 재생성한 ledger로 했다(분석 보고서 §2).
- `M4` FP support는 "task 참 간선 중 추정에 있는 것 + M4 FP"로 계산된다. 계약은 이 분모를 "task 추정 adjacency"라고만 적어서 의미는 같지만 문장으로 명시돼 있지는 않다. 정의 변경은 필요 없다고 판단했다.

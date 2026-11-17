# 16개 지표 기반 수정 전략 V2 제안

**상태: 소형 fixture 설계 검토. 실행 가능한 실험 정책으로 승인되지 않음.** 15개 nonempty subsets of `{M1,M2,M3,M4}` + no-edit S0는 유지한다. FN/FP/REV 14개 수정순서 정책을 대체물로 쓰지 않는다.

## 공동 입력 및 편집

모든 strategy는 같은 reference graph, initial estimate, task, allowed edit set, DAG constraint, cost table 및 nominal budget을 공유한다. 원자 수정 후보는 true missing adjacency add, false adjacency delete, reversed direction orient, unresolved orientation resolve 또는 delete다. 미확정 추가/해소/삭제는 별도 operation type이며 단가 mapping을 확정하기 전 실행 금지다. 수정 후 graph가 DAG인지 확인하고, valid하지 않으면 비용을 지출하지 않고 기록한다.

정답 graph 기반 correction 후보를 쓰는 비교는 oracle upper-bound 진단이다. 모델/실행 정책에서 GT labels·task-zone assignment·GT effect·regret을 후보 생성·순위에 제공하지 않는다. Oracle과 non-oracle은 별도 정보 조건으로 보고한다.

## Strategy 집합

`S0=∅` 무수정; 그 외 15 subset은 다음과 같다.

| subset | 지표 목표 | 비공집합 수 |
|---|---|---:|
| singleton | M1, M2, M3, M4 | 4 |
| pair | M1M2, M1M3, M1M4, M2M3, M2M4, M3M4 | 6 |
| triple | M1M2M3, M1M2M4, M1M3M4, M2M3M4 | 4 |
| all | M1M2M3M4 | 1 |
| no-edit | S0 | 1 |

총 16. M3는 방향 정확도와 unresolved rate를 동시에 보존해야 한다. M4는 FN/FP/REV/UNRES vector 그대로를 보존한다.

## Allocation A — 균등 quota 후보

quota의 단위를 모호하게 두지 않는다.

- `B`는 총 edit resource cost 상한 `C(π)≤B`.
- 기본 비용 scenario `c_add=c_del=c_ori=1`에서 edit-slot 수 `N_ref=floor(B/c_ref)`, `c_ref=1`로 정의한다.
- subset 크기 `k=|S|`이면 `floor(N_ref/k)` action slots를 각 target metric에 주고, 나머지는 사전 고정 순서 M1→M2→M3→M4로 분배한다.
- 하나의 edit은 한 metric quota를 소비하지만, 바뀐 모든 metric을 재계산한다. 같은 edit을 다른 quota에서 중복 적용/청구하지 않는다.
- unequal edit costs에서는 quota가 **edit-count slot**이며 총비용 B가 별도 hard cap이다. 해당 metric 차례에 후보가 없거나 edit cost가 남은 global budget보다 크면 slot/비용은 unused; 다른 metric으로 자동 이월하지 않는 버전을 기본 후보로 둔다.
- 매 slot 후보 우선순위는 해당 목표 metric의 사전 지정 normalized gain 최대. tie는 고정 operation/pair ID로 푼다.

같은 action이 metric A/B를 동시에 향상해도 비용은 한 번이다. quota 목적을 분명히 하기 위해 그 action은 현재 순번 metric의 slot으로만 채택됐다고 기록하고, 다른 metric의 quota를 자동 채운 것으로 세지 않는다. 이 방식은 하나의 edit이 다수 목적에 주는 효과를 score에는 반영하지만, quota 분배가 유일한 정책은 아니라는 한계가 있다.

## Allocation B — 공유 비용 greedy 후보

매 단계 남은 예산에서 affordability 및 DAG-validity를 만족하는 edit 가운데 `ΔU_S(o)/cost(o)`가 최대인 것을 선택한다. `U_S`는 선택 subset에 대해 사전 고정한 normalized utility다. 예시는 각 metric의 [0,1] scale gain을 equal weight 평균하는 것이지만, M3의 accuracy+unresolved vector와 M4 vector를 scalar화하기 전에는 `U_S` 계산이 미정이다. Zero/negative gain, tie tolerance, 같은 edit이 여러 component를 개선할 때의 중복 처리도 정해야 한다.

B는 남은 비용을 subset 내 다른 metric 후보에 사용할 수 있어 A보다 자원 활용도가 높을 수 있다. 이 성질은 경험적 성능 우위가 아니다. 두 방식은 같은 정보량·비용·DAG 조건으로 결과를 따로 보고한다.

## 소형 DAG fixture: 기회와 S15/B=1 반례

이 fixture는 계산 연습이지 SCM/성능 데이터가 아니다.

- Nodes: `{X,A,B,Y,T,U,P,Q,R,S}`.
- GT: `X→A, A→Y, X→B, B→Y, T→U, P→Q`.
- Initial estimate: `A→Y, X→B, B→Y, Q→P, R→S`.
- Errors/corrections: task FN `X→A` (M4); off-task FN `T→U` (M1); off-task FP `R→S` delete (M2); off-task REV `Q→P` orient to `P→Q` (M3).
- All four corrections are DAG-valid independently. All base costs 1. Task zone in this miniature example is the two X→Y paths; `P,Q,T,U,R,S` are outside.
- Score gains for the greedy illustration are derived from event-count diagnostics: M1 reduces its one missing off-task edge; M2 removes the one false adjacency; M3 fixes the one reversed true edge; M4 fixes one of four task-zone true edges. To compare across metrics for B only, suppose a predeclared normalized utility gives gains `(M1=.5, M2=.5, M3=1.0, M4=.25)`. These numbers are a didactic score rule, not data.

### Equal-quota A, base unit costs

Use stable metric order M1→M2→M3→M4 and allocate all `N_ref` slots.

| B | S1={M1} edits | S15 slots/actions | Interpretation |
|---:|---|---|---|
| 1 | `T→U` | only first remainder slot is M1: `T→U` | S15 and S1 have same final graph at B=1. |
| 2 | `T→U`, then no more M1 candidate | M1 `T→U`; M2 delete `R→S` | S15 differs from S1; second slot has another objective. |
| 3 | still only M1 candidate | M1 add `T→U`; M2 delete `R→S`; M3 orient `Q→P` | S15 includes three error classes. |
| 4 | still only M1 candidate | one slot each: `T→U`, delete `R→S`, orient `Q→P`, add `X→A` | Four policy targets produce four valid edits. |

Thus S15 B=1 can collapse to S1 under quota ordering; distinct labels do not guarantee distinct trajectories.

### Shared greedy B, base unit costs

With the illustrative normalized gains above and tie order M1 then M2:

| B | selected edits | final graph distinguishability |
|---:|---|---|
| 1 | M3 orient `Q→P` (gain/cost 1) | differs from quota A and S1, but only because of the illustrative utility ranking. |
| 2 | M3, then M1 or M2 on the .5 tie | two distinct operation types; tie rule matters. |
| 3 | M3, M1, M2 | three distinct corrections. |
| 4 | all four | same corrected graph as quota A S15 in this fixture, though order can differ. |

No result here estimates Regret or shows B superior. It only proves schedules can induce identical/different edits depending on budget and utility/ties.

### Unequal orientation costs

For `c_ori=2` or `3`, orientation is unaffordable whenever remaining B is below that value. A keeps the slot count based on reference unit cost but enforces actual total C≤B; an M3 slot may therefore be stranded. B uses actual `gain/cost` and shared remaining budget. E.g. at B=1 the REV edit is infeasible in both; at B=2, c_ori=2 makes it feasible, while c_ori=3 does not. A/B may then yield different feasible support even on the same graph. Always record affordable candidates, attempted slots, unused cost and final graph. Do not change scenario-specific B or edit cost post-result to equalize policy performance.

## 결론과 사전결정

A is transparent but can strand quotas; B uses shared resources but requires cross-metric normalization and M4/M3 scalarization. Neither is selected by this review. Before implementation decide whether the 16 strategies are diagnostic policies or a winner-selection set, exact M4/M3 utility, quota slot conversion, cost/tie rules, and whether exhaustive global optimization is an additional separately labeled oracle. Minimum among 16 is “best among evaluated catalog,” never “global optimum.”

# 과제 구역 FP 귀속 V2 — 경로·collider 검토

**상태: 두 후보 규칙 비교. 승인된 task-zone 정의 아님.** V1 오류: 예시 3은 `Z→X`를 GT 간선과 FP 모두로 써 모순이 있었고, 이 edge만으로 open X–Y backdoor path가 성립하지 않았다.

## 오류 사건과 FP의 분리

먼저 정답 인접 pair의 오류를 분류한다. true edge가 absent면 FN, 반대 방향이면 REV, unresolved이면 UNRES. 이들은 정답 간선 자체의 오류다. 반면 FP는 G*에서 adjacency가 부재인데 추정 graph에서 새 adjacency가 나온 pair다. FP의 과제 관련 태그는 정답 edge membership으로 결정할 수 없으므로 candidate assignment rule로 따로 부여한다. 각 오류 사건은 최종적으로 M1, M2, M3(or unresolved), M4의 단일 bucket에만 간다.

## 비교 규칙

**A — zone-internal pair:** 정답 task zone node set `V_T`에 양 끝점이 모두 속하는 FP를 task FP로 지정한다. 나머지는 non-task FP. 단순하지만 비관련 내부 chord도 task로 넓게 잡을 수 있다.

**B — internal + route-relevant boundary:** A에 더해, 한 끝점만 `V_T`에 있는 경계 FP 중 삽입 시 사전 정의한 task 관련 route를 새로 형성하는 경우만 task FP로 지정한다. 후보 relevance test는 causal X→Y route 또는 conditioning 기준상 open backdoor route를 만든다는 것이다. 평가기만 GT topology를 참조할 수 있다. 정책 입력에는 이 tag, reference graph, effect/regret을 제공하지 않는다. test가 route topology를 본다는 것은 “FP가 실제 효과를 바꿈”을 증명하는 게 아니다.

## Collider 및 open backdoor의 조건

경로는 undirected simple path로 열거하되, **열거된 backdoor path**와 **open/active path**를 구분한다. Backdoor path는 X에서 첫 edge가 X로 들어오는 경로다. Collider에서 화살표가 양쪽 node로 들어오면, 별도 conditioning/descendant-on-collider 규칙이 없을 때 그 path는 닫힌다. B의 “새 route”가 단순 그래프 path인지, open causal bias path인지 결정해야 한다. 본 예시의 collider case는 conditioning set이 빈 집합이고 collider descendant도 condition하지 않는다고 가정한다.

## 최소 hand-check DAG 예시

`G*`는 정답이고 `+ FP`는 G*에 없는 edge를 추정 graph에 추가한 사건이다. 모든 경로 설명은 선택된 task `(X,Y)` 기준이다.

| # | 정답 DAG 및 zone | 추가 FP | A | B | 경로 판정 |
|---|---|---|---|---|---|
| 1 | `X→M→Y`, `V_T={X,M,Y}` | `X→Y` | task | task | 새 directed causal path shortcut. |
| 2 | `X→A→Y`, `X→B→Y`, `V_T={X,A,B,Y}` | `A→B` | task | task | DAG-valid 내부 edge가 새 causal path `X→A→B→Y`를 만듦. |
| 3 | `X→M→Y`, `Z→X`, `Z→Y`; `V_T`에는 backdoor의 `Z`도 포함. 외부 `W→M` | `W→X` | non-task (W 외부) | task 후보 | open backdoor `X←W→M→Y`; collider 없음. Z가 만든 기존 open backdoor는 참조 구성이고, W→X만 새 FP다. |
| 4 | `X→M→Y`, `W→C`, `C←Y`; `V_T={X,M,Y}` | `X→C` | non-task (C 외부) | non-task under empty conditioning | route `X→C←Y←…`의 C는 collider라 닫힘. 단순 연결만 보고 B task 처리하면 과포함. |
| 5 | `X→M→Y`, 외부 `Z→Y`; `V_T={X,M,Y}` | `M→Z` | non-task (Z 외부) | task | 새 causal route `X→M→Z→Y`. |
| 6 | `X→M→Y`, 외부 isolated `W→V`; `V_T={X,M,Y}` | `W→V` | non-task | non-task | task route/backdoor에 연결되지 않는 경계 밖 FP. |

예 3의 정확한 node/edge: `V={X,M,Y,Z,W}`, `G*={X→M,M→Y,Z→X,Z→Y,W→M}`. `W→X`는 G*에 없는 edge다. Task zone node set은 X–Y causal path와 기존 open backdoor `X←Z→Y`의 nodes. W는 zone 밖이다. FP를 넣은 뒤 열린 route `X←W→M→Y`가 생긴다. 따라서 단순 내부 pair A는 놓치고, B의 boundary route test는 잡을 수 있다.

예 4의 정확한 node/edge: `V={X,M,Y,C}`, `G*={X→M,M→Y,Y→C}`이고 FP는 `X→C`. 이때 path `X→C←Y←M←X`는? 이 표현은 기존 causal edges를 포함하면 cycle처럼 보이므로 사용하지 않는다. 정확한 collider 예시는 task X→M→Y와 disjoint `Y→C`, `W→C`를 동시에 둘 수 없으므로, 다음 graph로 한정한다: `V={X,M,Y,C,W}`, `G*={X→M,M→Y,Y→C,W→C}`. FP `X→C`를 넣으면 path `X→C←Y`는 C collider여서 unconditioned open backdoor가 되지 않는다. `X→C` 자체는 기존 X→M→Y path 외에 C를 통한 directed causal path도 아니다. B가 “simple undirected connection”만 사용하면 잘못 task로 tag할 수 있다.

> 예시 4의 정답 graph는 간선 `Y→C`와 `W→C`로 collider `Y→C←W`를 만든다. FP는 `X→C`다. collider를 통과하려면 C 또는 그 descendant를 condition해야 하지만, 예시에서는 conditioning하지 않는다. 따라서 신규 경로는 **존재하는 path**일 수 있으나 open path는 아니다.

### 예 4 주의

정확한 route `X→C←Y`에서 `Y→C`는 collider 방향이지만 기존 `Y`는 outcome이다. 간선 `X→C`를 추가해도 X와 Y 사이에는 undirected path `X→C←Y`가 생기며, C가 collider라 unconditioned path는 닫힌다. 여기에 task graph의 기존 `X→M→Y`는 유지되므로 cycle이 없다. 이 예시의 목적은 “존재하는 undirected path”와 “open backdoor path”가 다름을 보이는 것이다.

## 완전한 오류 분할 규칙

한 graph×task의 모든 **오류 사건**을 다음 순서로 딱 한 번 분류한다.

1. G*에 adjacency가 있음: 추정 absence→M1 또는 M4-FN; wrong orientation→M3-reversal 또는 M4-REV; unresolved→M3-unresolved 또는 M4-UNRES. 맞은 orientation은 오류 아님.
2. G* adjacency가 없음, estimate adjacency가 있음: FP assignment A/B가 task→M4-FP 또는 non-task→M2 중 하나를 지정.
3. 양쪽 모두 absent: 오류 사건 없음.

따라서 GT-absent FP를 FN/REV/UNRES와 혼합하지 않는다. 단일 task 안에서는 한 오류가 outside와 task에 동시에 들어가지 않는다. 여러 task를 평가할 때 동일 edge 오류가 여러 task-specific 결과에 반복될 수 있으나, 이는 task별 repeated outcome이며 독립 사례 수를 늘리지 않는다.

## 규칙 선택 영향 및 미결 사항

A는 단순·재현 가능하지만 zone 내부 chord 과포함 가능성이 있다. B는 zone 밖 boundary edge를 포함하되 경로/conditioning 정의에 민감하고 GT 기반 평가자 정보에 더 의존한다. 둘 다 structure-level proxy이며 실제 효과 relevance를 보장하지 않는다. 같은 입력을 A/B 양쪽에 적용한 구조 표본 집계는 민감도 비교가 될 수 있지만 결과에 맞춰 주 규칙을 고르지 않는다.

결정 필요: task zone이 all backdoor path인지 unconditioned-open path인지; conditioning set/descendant 규칙; B의 route test; A/B 중 주 규칙인지 sensitivity인지; task-FP M4 denominator. 신규 결과 열람 전 책임자가 정해야 한다.

# 과제 구역의 FP 귀속 대안

**상태: 설계 비교. 어느 규칙도 승인·실험 적용되지 않았다.** 목적은 정답 그래프에 없는 예측 간선의 구역 태그를 정의하는 것이다. 소형 DAG 예시는 모두 손으로 구성한 설명 fixture이며 연구 SCM이나 정책 성능 자료가 아니다.

## 공통 기반

과제 `(X,Y)`에 대해 task-zone node 집합 `V_T`는 정답 X→Y 단순 방향 경로와 사전 정의한 X–Y backdoor/confounder 구조의 노드 합집합으로 제안한다. `E_T`는 그 경로들의 정답 간선 합집합이다. 이 집합의 정확한 backdoor 규칙 자체도 `ORIGINAL_FOUR_METRIC_SPEC.md`의 승인 대기 항목이다.

규칙 A는 **내부 쌍 규칙**이다. 예측 FP `{u,v}`를 두 endpoint가 모두 `V_T`에 있을 때 task-zone FP로 분류한다. 이 정의는 실제 관련성이 불충분한 두 zone node 사이의 비관련 간선도 넓게 포함할 수 있다.

규칙 B는 A를 기반으로 **경계 연결 규칙**을 추가한다. endpoint 하나가 `V_T` 안, 하나가 밖인 간선은 자동 포함하지 않는다. 사전 고정된 structural relevance test를 통과할 때만 task-zone FP로 태그한다. 후보 test는 FP를 더한 그래프에서 X→Y 방향 경로 또는 X에서 시작하는 backdoor route를 새로 연결하는가이다. 해당 test에 정답 topology를 사용하는 것은 평가 태그 산출 용도로 격리하고 정책 입력으로 누출하지 않는다. 어떤 relevance test를 승인할지는 미결이다.

두 규칙 모두 FP를 “누락”하지 않으려면 모든 예측 FP를 task-zone 또는 non-task-zone에 정확히 하나로 배정해야 한다. ④에 들어간 오류는 ② 분자에서 제외하고, 나머지 FP는 ②에 포함하는 상호 배타적 회계가 후보 계약이다. ③은 참조상 인접한 pair에서만 orientation 평가하므로 FP에는 적용되지 않는다. 다만 ①–④의 pair membership을 확정하기 전에는 완전 분할이 보장되지 않는다.

## 비교

| 항목 | 규칙 A: `V_T` 내부 endpoint 쌍 | 규칙 B: 내부쌍 + 관련 경계 간선 |
|---|---|---|
| FP 귀속 | 두 끝점 모두 task zone node면 ④, 아니면 ② | 내부쌍은 A와 같고, 경계쌍은 사전 relevance test를 통과하면 ④, 아니면 ② |
| 오류 이중 집계 | ②에서 ④ FP를 빼면 방지 가능 | 같은 단일 tag 우선순위를 적용하면 방지 가능 |
| 누락 위험 | zone node 밖의 원인 노드가 X/Y에 허위 경로·공통 원인을 만들면 ④에서 빠질 수 있음 | 관련 경계 연결은 포착 가능. test 범위 밖의 간접 영향은 여전히 누락 가능 |
| 과포함 위험 | zone node 내부이지만 경로/교란과 무관한 chord FP까지 ④로 계산 | 관련성 검사 오류·경로 탐색 범위에 따라 과소/과포함 가능 |
| GT 정보 누출 | 구역 노드는 GT를 통해 정의되며 평가자만 접근해야 함 | 구조 relevance test가 GT를 참조할 가능성이 더 높음. 정책 입력으로 절대 전달 금지 |
| 구조 간 이식성 | 간단하고 graph/task별 자동 계산이 쉽지만 과제별 경계의 의미가 달라짐 | 더 기계적인 path criterion을 만들 수 있으나 relevance 규칙과 cycle/path semantics를 사전 고정해야 함 |

## 손계산 예시

기호 `X→M→Y`는 참조 graph의 task path다. `Z`는 예시에서 별도로 밝힌 zone node set이다. FP는 `G*`에는 없고 추정 graph에 추가된 방향 edge다.

| # | 참조 DAG 및 zone | 예측 FP | 규칙 A | 규칙 B | 설계상 포인트 |
|---|---|---|---|---|---|
| 1 | `X→M→Y`, `V_T={X,M,Y}` | `X→Y` | task FP (둘 다 zone) | task FP (새 X→Y causal route) | 직접 shortcut FP는 양쪽 모두 잡음. 과제 task 자체는 indirect-only일 필요가 없는 metric fixture. |
| 2 | `X→A→Y`, `X→B→Y`, `V_T={X,A,B,Y}` | `A→B` | task FP | task FP (새 directed route `X→A→B→Y` 형성) | 두 endpoint가 모두 zone이고 수정 뒤에도 DAG인 내부 chord. |
| 3 | `X→M→Y`, 외부 `Z→X`, `V_T={X,M,Y}` | `Z→X` | non-task FP | task FP (기존 X–Y route에 backdoor 연결) | 경계 FP의 핵심 예. ④가 교란변수 간선을 포함하려는 취지와 맞음. |
| 4 | `X→M→Y`, 외부 `Z→W`, `V_T={X,M,Y}` | `M→Z` | non-task FP | 보통 non-task; 다만 추가 edge가 관련 route를 만드는지는 승인 test로 판정 | zone 바깥 노드와 연결되었다는 이유만으로 모두 task-zone으로 분류하면 과포함. |
| 5 | `X→M→Y`와 외부 간선 `Z→Y`, `V_T={X,M,Y}` (`Z`는 GT에서 X와 연결되지 않아 common cause가 아님) | `M→Z` | non-task FP (Z가 zone 밖) | task FP (새 directed route `X→M→Z→Y` 형성) | 경계 연결이 가짜 Action→Target 경로를 만드는 예. |
| 6 | `X→M→Y`, 외부 `Z→W`, `V_T={X,M,Y}` | `Z→W` | non-task FP | non-task FP (관련 route를 만들지 않음) | 어느 규칙에서도 일반 주변 FP를 누락 없이 ②에 남겨야 함. |

예 3과 5의 “B task FP”는 예시에서 제시한 structural test의 결과를 보이기 위한 것으로, test 최종 승인 여부는 미정이다. 예시 4의 `M→Z` 같은 edge는 endpoint만으로는 효과 관련성을 단정할 수 없으므로 실제 fixture에서는 방향과 나머지 정답 경로까지 명시해 test에 넣어야 한다.

## 관련성·누출·평가 해석

- GT는 ④ 구역 태깅과 결과 채점에 쓸 수 있지만 graph-edit 정책에 task-zone membership이나 참조 간선을 전달하면 oracle 사용으로 분류한다.
- FP는 그 자체로 “효과 없음” 또는 “해로움”이 아니다. GT path 밖의 간선도 regression adjustment, collider conditioning, proxy 경로 등으로 downstream estimate에 영향을 줄 수 있다. B의 단순 경로 test도 실현된 효과를 대체하지 않는다.
- 구조 relevance와 실제 의사결정 relevance는 별개다. 이 설계 gate는 ①–④ 평가 분류만 제안하며 계수, 개입효과, regret을 이용해 FP 귀속을 정하지 않는다.
- A는 재현성·단순성 이점, B는 task-zone 밖 원인까지 포착할 수 있는 이점이 있다. 두 규칙은 ④ 점수와 ② 분모, 결과 해석 모집단을 바꾼다. 하나를 사후 결과에 맞춰 선택하지 말고 fixture 검증과 사전 승인이 필요하다.

## 미결 결정

1. `V_T` 또는 edge-tag 중 어느 membership을 ④에 사용할지.
2. B 경계 FP의 relevance test를 추가할지와 방향 조건.
3. ② 분모에서 task-zone FP를 제외할 때 `Â`의 denominator를 어떻게 다시 셀지.
4. 복수 task·복수 backdoor route의 중복 count/요약 단위.

다른 구조에도 일관 적용되려면 규칙은 오직 사전 고정된 graph/task topology에 의존하고, 문자열 ID·노드 입력 순서·효과나 정책 결과에 의존하지 않아야 한다.

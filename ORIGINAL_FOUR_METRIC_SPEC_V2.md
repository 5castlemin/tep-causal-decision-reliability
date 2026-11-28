# 원래 네 구조 지표 — 계산 명세 V2 제안

**상태: 설계 검토용. 사용자 승인·동결·사전등록이 아님.** V1 파일은 이력으로 보존한다. 원 지표는 기존 Skeleton F1, Directed F1, Path F1, Ancestor F1과 다른 개념이다.

## 입력·상태 표현

고정 노드 집합 `V`, 정답 DAG `G*=(V,E*)`, 추정 graph를 입력한다. 평가 universe `U`는 모든 비순서 노드쌍 `{u,v}`(u≠v)다. 한 pair의 추정 상태는 `ABSENT`, `UNRESOLVED`, `u→v`, `v→u` 중 하나다. 각 pair는 정답 기준으로 인접 또는 부재 하나다. 중복·자기간선·알 수 없는 노드·두 방향 동시 간선은 입력 오류다.

정답 인접 집합을 `A*⊂U`, 추정 인접 집합(방향 확정 또는 unresolved)을 `Â⊂U`라 한다. `C`는 참 인접성이 있고 방향이 맞음, `R`은 참 인접성이 있지만 방향이 반대, `Q`는 참 인접성이 있고 추정 인접은 있으나 방향 미정, `M=A*\Â`는 연결 누락, `F=Â\A*`는 GT에 없는 예측 연결이다. 이들은 pair별 사건 분류다.

## 과제 구역

과제 `t=(X,Y)`는 graph 결과를 열기 전에 고정한다. causal edge set `E_c(t)`는 G*의 모든 단순 X→Y 방향 경로에 있는 간선의 합집합이다.

confounder/backdoor 부분은 아직 원문만으로 유일하게 정해지지 않는다. 후보는 (i) X로 들어오는 방향으로 시작하는 모든 simple X–Y path edge, 또는 (ii) 사전 고정한 conditioning set 아래 열린(active) backdoor path edge다. (i)는 collider에 의해 차단된 path도 포함할 수 있고, (ii)는 conditioning choice에 의존한다. V2는 이 둘을 혼합하지 않으며, 어떤 estimand·conditioning rule을 쓰는지 승인 전까지 M4 계산을 미완료로 둔다.

평가자가 정답 기준으로 계산한 zone pair tag를 `Z_t⊂U`라 한다. 참 인접 pair의 M/R/Q는 edge class로 귀속한다. 참조 부재 pair에서 나온 FP는 이 정답 edge set에 속할 수 없으므로, 별도의 **FP assignment rule**로 `Z_t` 또는 `U\Z_t` 중 하나에 지정한다. 이 규칙은 `TASK_ZONE_FP_ASSIGNMENT_OPTIONS_V2.md`에 비교했다. 태그와 정답 간선은 평가 전용이며 정책에 전달하면 oracle 정책이다.

## 네 지표의 계산 후보

### M1 — 비과제 구역 누락률 (낮을수록 좋음)

`M1 = |M∩(U\Z_t)| / |A*∩(U\Z_t)|`.

분모 0은 `NA_NO_REFERENCE_EDGE`. 인접성을 찾은 reversed 또는 unresolved pair는 누락이 아니다. pair는 M3 또는 task M4의 방향/미확정 구성요소로 간다.

### M2 — 비과제 구역 허위 연결률 (낮을수록 좋음)

`M2 = |F_out| / |Â_out|`, 여기서 `F_out`은 FP assignment rule상 non-task로 태그된 false adjacency, `Â_out`은 동일한 평가 universe에서 non-task로 태그된 모든 predicted adjacency(방향 미정 포함)다. 분모 0은 `NA_NO_PREDICTED_EDGE`. FP task-tag는 분자 및 분모에서 제외되어 M4로 한 번만 간다.

### M3 — 비과제 조건부 방향 정확도 + unresolved rate

`M3_acc = |C_out|/(|C_out|+|R_out|)`. 분모 0이면 `NA_NO_ORIENTED_MATCH`이며, 작은 denominator에서는 rate만 순위화하지 않고 항상 `correct/reversed` 개수도 낸다. DOCX의 제안 기준은 denominator<5에서 개수 중심 보고다.

방향을 못 정한 true adjacency는 별도로 `M3_unresolved = |Q_out|/(|C_out|+|R_out|+|Q_out|)`로 제안한다. 이는 DOCX의 “unresolved / correctly found connections”를 실행 가능한 분모로 구체화한 후보이며 원문 확정식이 아니다. 분모 0은 `NA_NO_MATCHED_ADJACENCY`. 정확도만 단독 최적화하면 오답 방향을 unresolved로 바꾸어 apparent accuracy를 올릴 수 있으므로 두 값을 항상 함께 제시한다.

### M4 — 인과경로·교란 관련 task-zone error vector

`M4=(FN_t, FP_t, REV_t, UNRES_t)`를 주 출력으로 보존한다. 오류 사건 수와 support 분모를 함께 낸다.

- `FN_t=|M∩Z_t|`, rate 분모 후보 `|A*∩Z_t|`.
- `FP_t=|F_t|`; rate 분모는 assignment rule에 따른 task-tagged predicted adjacency count로 후보화하되, rule A/B별 pair universe와 denominator를 명시한다.
- `REV_t=|R∩Z_t|`; 방향 오류율 분모 후보 `|C∩Z_t|+|R∩Z_t|`.
- `UNRES_t=|Q∩Z_t|`; true matched adjacency 대비 rate를 별도 보고한다.

0 분모의 rate는 NA이며 사건 수를 임의로 0/1 점수로 치환하지 않는다. DOCX는 M4 단일 scalar의 component weight를 확정하지 않았다. 따라서 우선 vector를 보고하고, scalar가 꼭 필요하면 `α_FN, α_FP, α_REV, α_U`와 normalization을 별도 승인한다.

## 단일 귀속 검사

한 task의 모든 오류 pair는 다음 정확히 하나의 bucket에 속한다.

| 참조 pair 상태 | task tag | bucket |
|---|---|---|
| true adjacency absent from estimate | non-task | M1 |
| true adjacency absent from estimate | task | M4-FN |
| true adjacency predicted reversed | non-task | M3-reversed |
| true adjacency predicted reversed | task | M4-REV |
| true adjacency predicted unresolved | non-task | M3-unresolved |
| true adjacency predicted unresolved | task | M4-UNRES |
| GT absent, predicted adjacency | FP rule says non-task | M2 |
| GT absent, predicted adjacency | FP rule says task | M4-FP |

맞은 true adjacency는 오류 사건이 아니며 score denominator에만 반영될 수 있다. FP assignment는 정답 경로 FP와 주변 FP를 중복하거나 누락하지 않고 위 두 마지막 bucket 중 하나로 보낸다. 다중 task 결과는 task별 반복 평가이며 독립 graph/SCM 수가 늘지 않는다.

계산상 오류 사건의 배타성은 표본 독립성을 뜻하지 않는다. 네 metric은 동일 graph×task에서 산출되므로 상관·VIF는 관측 결과로 별도 진단한다.

## 미결 Gate

1. task zone의 backdoor path 기준과 conditioning/활성 여부.
2. FP option A/B와 분모 universe.
3. M3 unresolved rate 분모.
4. M4 scalarization 필요 여부, component normalization 및 `α` 승인.
5. 참조 graph 불완전성·분모 0·작은 분모 보고 규칙의 운영 승낙.

이 명세만으로 구현·사전등록을 시작하거나 원 연구가 승인됐다고 표시하지 않는다.

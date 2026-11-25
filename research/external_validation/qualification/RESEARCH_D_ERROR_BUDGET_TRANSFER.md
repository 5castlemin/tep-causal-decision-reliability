# Research C 오류 분포 및 예산 이전 검토

Mk2 reference DAG: V=90, E=142, unordered node pairs=4,005, unordered nonadjacent pairs=3,863. 각 비인접 pair에는 두 방향 FP 후보가 있어 방향 후보는 7,726개다. Research C 구현은 q=.15를 각 true adjacency에 독립 적용하고, r=.05를 각 unordered nonadjacent pair에 독립 적용한 뒤 FP 방향을 공평하게 선택한다. 따라서 DAG 검사 전 기대 proposal은 adjacency corruption 21.3개, FP 193.15개다. true-edge 오류는 FN/REV/UNRES에 기대 7.1개씩 나뉜다. DAG 위반 reverse/addition은 재추출 없이 거절 기록된다. 이 값은 오류 제안 기대치이지 전문가 수정 비용이나 최종 G0 부담이 아니다. 구조 후보의 원자 비용 1은 graph edit count이지 전문가 시간이나 물리 위험 비용이 아니다.

구조적으로 가능한 오류: FN/UNRES는 참 edge 제거로 생성 가능, REV는 역전 후 DAG인 경우 가능, FP는 참 비인접쌍에 추가할 때만 reference-relative로 가능. 전수 구조 검사를 하더라도 참 비간선의 과학적 진실을 보증하지 않는다. 기존 6–10 노드와 비교하면 90노드에서 기회 수와 위상 제약이 달라져 같은 q/r 및 절대 B=0–4는 오류 burden을 보존하지 않는다. Task-zone 비율, Rule A 인접 제한, off-task 기회도 외부 reference evidence 없이 설계자 임의로 맞출 수 없다.

| 안 | 기대/통제 부담 | 비용·DAG | 비교 가능성 |
|---|---|---|---|
| A 기존 q/r, B=0–4 | 노드 수 증가로 오류 제안 절대 수 증가 | 편집 1은 graph edit; DAG rejection 비율 달라짐 | 낮음; 이름은 같아도 난이도 불일치 |
| B 상대 부담 예산 | 사전 지정 오류율/정규화 예산으로 크기 보정 | 새로운 분모와 구조적 유효화 필요 | 새 외부 계약, C 수치와 직접 비교 제한 |
| C 사전 지정 오류 개수/부담 | 고정 개수 또는 burden strata 사전 선언 | DAG 조건부 수용, seed 실패 보존 필요 | C와 가장 가깝지만 graph-size topology는 여전히 다름 |

후속 승인 전에 exact pair denominator, 오류 제안→DAG conditioning 규칙, task-zone 사전 근거, B 의미, 실패 seed 처리, 공통 오류 표본 설계를 결정해야 한다. M4 유리성을 위해 task-zone 오류 비율을 올리지 않는다. 이번에는 G0 seed cohort, 추천, 정책 또는 regret을 만들지 않았다.

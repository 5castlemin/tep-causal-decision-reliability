# Step 1 정책 및 수학적 검증 계약

2026-11-10. 최소 소형 fixture `step1_fixture.py`와 `tests/test_budget_refinement_step1.py`, 실행 로그 `STEP1_FIXTURE_LOG.json`이 근거다. 정책 엔진이나 SCM 실험이 아니다.

## 기존 코드와 변경 근거

`src/diverse_structure_pilot.py::all_paths/score_graph`, `src/integrated_pilot.py::recommend/structure_metrics`, `src/decision_reliability_next.py::choose_response`, `src/independent_confirmation.py`의 구조 단위 평가를 후속 단계에서 활용한다. 기존 정적 그래프의 unresolved는 별도 집합이고 strict F1은 반전이 FP와 FN으로 분모에 반영될 수 있다. 수정 분류는 반전 한 작업·한 비용이며 점수 계산을 바꾸지 않는다. 기존 key_path_edge_recall은 FP 경로를 벌점하지 않으므로 Path F1과 다르다.

Step0의 Global 유형 우선 대 T 전체 후보 위치 정렬은 유형 효과를 교란한다. 수정: 같은 허용 유형의 사전 고정 순환 일정을 적용하고, 각 유형 내에서만 위치 점수를 차별한다. FN→FP→REV 고정 시작은 작은 예산에서 FN에 유리하다. 유형 목록을 사전 고정 stable 순서로 두고 공통 seed mod 유형 수만큼 시작을 회전한 뒤 균형 순환한다. seed별 시작 균형을 계획하고 결과 후 변경하지 않는다. 독립 seed는 정책의 무작위성이지 독립 SCM이 아니다. 정책 효과를 과거 Step0의 교차 유형 점수 정렬 결과와 동일한 추정량으로 연결하지 않는다.

두 정책은 동일 초기 DAG·참조 후보 접근·유형 순환·예산·DAG·동률 ID를 공유하며 차이는 동일 유형 내 위치 우선뿐이다. **실제 유형별 실행 건수의 동일성은 보장되지 않는다.** 서로 다른 위치를 고르면 다음 후보의 cycle 유효성과 예산 소진이 달라질 수 있다. 요청 기회·후보 수·거부·실제 유형 수를 짝별 기록하며, 주 의도된 비교는 전체 무조건 대조, 유형별 실현 구성과 미사용 예산은 교란/매개 진단으로 보고한다. 같은 실현 건수만 사후 선택하면 선택 편향이 생기므로 제한된 층 비교는 탐색적이다. 정확한 유형별 수가 반드시 필요한 확인 실험은 별도의 선행 등록된 paired 제약 및 불가능 쌍 처리 계약이 필요하다.

## 14개 명목 정책

| 허용 유형 | Global | Task-Focused |
|---|---|---|
| FN | G-FN | T-FN |
| FP | G-FP | T-FP |
| REV | G-REV | T-REV |
| FN,FP | G-FN-FP | T-FN-FP |
| FN,REV | G-FN-REV | T-FN-REV |
| FP,REV | G-FP-REV | T-FP-REV |
| FN,FP,REV | G-FN-FP-REV | T-FN-FP-REV |

모든 행은 동일 규칙이다. 각 차례의 후보는 oracle이 현재 그래프의 해당 유형에서 찾은 실제 정답 수정. Global은 사전 등록한 순서상 불변 정수 노드 ID의 (source,target) 순으로 선택한다. T는 G0+사전 H 기반 위치점수 내림차순 후 동일 ID 순이다. 후보가 현재 DAG에 순환을 만들거나 잔여 예산에 비싸면 거절·사유 기록하고 다음 후보를 본다. 유형별 한 번 수정 후 다음 유형으로 이동, 전체 순환에서 수정이 없으면 종료한다. 예산0 또는 소진도 동일하게 종료한다. FN/FP/REV 비용은 gamma=1에서1, REV는 gamma=2/3일 때 해당 가중치다. 기각은 무비용; 최종 잔여 예산·후보 소진과 거절을 구분해 기록한다. 실제 그래프에서 오류 유형 목록·후보가 소진되면 조합끼리 수정 집합/순서가 같을 수 있다. 단일 FN 예제에서 G-FN과 T-FN-FP가 동일함을 확인했다. 인위적인 구별이나 사후 병합은 금지한다.

불변 ID는 이름 문자열 순서가 아니라 데이터 스키마에 사전 고정된 노드 식별자다. 이름만 바꾼 fixture에서 선택이 보존됐다. 그러나 입력 순서마저 바뀌면 tie가 바뀔 수 있으므로 Step2는 명시적인 불변 ID를 요구한다. T 점수는 초기 G0와 H에서 action 또는 target까지의 최소 무방향 거리 d에 대해 s(u,v)=1/(1+d(u))+1/(1+d(v)), 무한 거리는0이다. FN처럼 간선이 없어도 양 끝으로 평가하고 H가 없으면 빈 집합을 사용한다. G0에 진짜 경로가 빠지면 구역이 틀릴 수 있다. 이 점수는 숨은 GT 경로나 실제 효과를 나타내지 않는다.

## 순서·기준선·누출

oracle 후보 중 cycle인 수정은 무비용 거부한다. 예를 들어 현재 b→c→a이면 참조 a→b 추가는 거부되고 잘못된 c→a를 제거한 후 유효해진다. FP가 허용되지 않거나 예산1이면 해당 수정이 불가능하다는 것을 소형 DAG의 모든 오류정정 유효 순서 열거로 대조했다. 구현 오류는 독립 closure 기반 DAG 검사 및 brute-force 순서 열거와 불일치할 때만 선언한다. 불가능과 구현 오류를 합치지 않는다.

No-edit는 B=0/무변경이다. Random valid oracle은 비교 대상과 동일 유형·동일 순환 기회·예산·유효 후보에서 해당 유형의 후보를 균등 무작위로 골라 후보가 바뀔 때 재계산한다. 독립 난수 seed 0~19를 예비 계약으로 제안하며 최종 반복 수/seed는 Step4 전 동결하고 평균은 SCM 내부에 묶는다. Path F1 oracle은 같은 후보·비용·DAG·유형 일정을 사용하되 해당 유형의 유효 후보 중 참조/예측 Action→Target 경로 간선 합집합의 F1을 가장 크게 개선하는 것을 선택한다. 0분모는 NA, 개선 가능한 후보가 없으면 해당 기회를 넘긴다; 동률은 불변 노드 ID. 거짓 경로 간선은 FP다. 이는 GT 숨은 경로를 읽는 별도 oracle 기준이며 주 T보다 더 많은 정보를 사용한다. 기존 path recall을 그대로 F1이라 부르지 않는다. 랜덤과 Path 기준선은 명세만 있으며 구현 완료가 아니다.

수정 선택 함수는 참조 DAG/현재 DAG/유형/예산/G0·H/action/target/seed만 받으며 SCM 계수·정답 개입 평균·손실·regret 인자를 받지 않는다. 효과 계수만 교체하는 모의 호출이 같은 결과를 내고 금지 인자는 TypeError임을 검사했다. 이는 인터페이스 수준 시험이지 장래 전체 파이프라인 누출 검증이 아니다. H 출처·시점의 외부 검토와 Step2 end-to-end 차단 테스트가 필요하다.

각 실행 기록: initial_graph, allowed_types, candidate_operations, rejected_operations, edit_sequence, final_graph, spent_budget, unused_budget, failure_reason, policy_id, seed와 type_opportunities. Step1은 fixture만 기록한다. 수정 집합 중복은 Jaccard |A∩B|/|A∪B| (둘 다 공집합이면1), 순서 중복은 전체 시퀀스 완전 일치율과 예산별 공통 접두 길이로 보고한다. 예산마다 정책·SCM별 중복을 기록하고 독립 SCM 단위로 집계한다.

검증 2026-11-10: `python -X utf8 -m unittest discover -s tests -p test_budget_refinement_step1.py -v` 17개 통과. 완전 열거 비교는 소형 fixture 범위이며 대규모 그래프의 완전성·실험 성능을 보장하지 않는다.

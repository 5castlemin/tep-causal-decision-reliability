# Step2 엔진 및 테스트 계약

`policy_engine.refine`은 키워드 전용 입력 node_ids, initial_edges, reference_edges, allowed_types, policy_id, budget, gamma, action, target, prior_edges, seed, display_names, graph_id를 받는다. 정답 그래프를 이용하는 oracle 실험 전용이다. node_ids는 원래 스키마의 불변 문자열이며 표시 이름은 별도 매핑이다. 저장 순서는 정렬된 ID이고 원래 SCM의 열은 `schema_mapping(ids,expected_ids,values)`가 정확한 순서와 길이를 확인한다. 자동 재배열하지 않는다. 초기 그래프 ID가 없으면 동일 그래프의 SHA-256을 ID로 쓴다. G-/T-와 허용 유형의 조합 14개 및 NO-EDIT, RANDOM, PATH-F1을 지원한다.

출력은 JSON 직렬화 가능한 초기/최종 DAG 및 해시, 후보와 위치점수·선택순서, 유형 기회, 무비용 cycle/예산/Path F1 거부, 원자 수정·비용 장부, 횟수·사용/잔여·종료·실패 이유 및 seed·스키마를 포함한다. Path F1의 양쪽 무경로(정의 불가)와 정의되지만 양의 개선이 없는 경우를 분리한다. 개선이 없으면 기회를 넘긴다. 추정 경로의 거짓 간선은 벌점하며 reference path 정보가 추가로 필요한 더 강한 oracle이다. 경로 나열은 조합 폭발할 수 있어 대규모 실행 전 제한·성능 검토가 필요하다. Random은 독립 `random.Random(seed)`으로 유형 내 유효 후보를 균등 선택한다. `compare_edits`는 수정 Jaccard(둘 다 비면1), 시퀀스 완전 일치 및 공통 접두 길이다.

`graph_adapter.run_graph_stage`는 graph-only 필드가 정확한 일반 dict만 허용하고 평가 객체·학습/평가 데이터 등 추가 필드를 거부한다. 테스트용 외부 evaluator를 주입하려는 시도는 실패하며 같은 DAG에서 효과 계수를 바꾼 모의 evaluator를 선택 단계 밖에 두면 선택이 같다. 이는 mock 경계와 현재 의존성 검사이며 임의 Python 코드에 대한 보안 샌드박스나 실제 Step3 전체 SCM 학습/평가 흐름의 누출 검증이 아니다. 사전 정보 H의 출처와 숨은 정답 유출 여부도 호출자가 감사해야 한다. 모델 학습·조작 추천·정답 평가 모듈은 구현/호출하지 않는다.

기존 연동 후보: `src/integrated_pilot.py::fit_model/recommend/structure_metrics`, `src/diverse_structure_pilot.py::score_graph/analytic_response`, `src/decision_reliability_next.py::evaluate`의 입력 의미와 스케일을 Step3 연결 전에 대조한다. 기존 F1의 REV·unresolved 규칙과 편집 원자비용은 다르다. 최종 평가 정보가 정책 구성으로 역류하지 않도록 향후 실제 어댑터 통합 테스트를 선행한다. 데이터 생성이나 후회 평가는 이번에 수행하지 않았다.

추가 검사: 모의 그래프→학습→추천→평가 흐름에서 평가 계수만 바꿔도 수정 선택이 같고 평가 결과는 달라진다. evaluator·학습/평가 데이터를 graph-only 요청에 주입하면 거부한다. 120개 임의 소형 DAG에서 Step1 참조 구현과 순서/비용을 비교했다. 양쪽 무경로와 Path F1 개선량 0, 동률을 별도 검사했다. 이들은 모의·fixture이며 신규 SCM 실험이 아니다.

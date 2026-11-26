# Research F-Lite fixture 및 저장 결과 검증

## 결정론적 단위 테스트

`tests/test_research_f_lite_policy.py`는 현재 14개, noise/bootstrap 검증을 포함한 F-Lite 전용 테스트는 총 17개다. 최초 11개 정책 fixture는 core 평가 전에 통과했다. Core 산출물 감사 후에는 같은 정책 계약을 바꾸지 않은 상태에서 숨은 참조 불변성, 두 간선 path-synergy 반례, zero-impact tie 동작, noise 정답 재구성 및 nested bootstrap 방향을 보강해 다시 통과했다. 따라서 보강 fixture들의 시간 순서는 실제 core 평가 전이 아니며, 이를 사전 검증이었다고 소급 표현하지 않는다.

두 간선 synergy fixture에서 빈 그래프 및 각 단일-edge 대안은 action X에서 target Y로 평탄한 예측 손실을 냈지만, `X→M→Y`를 함께 둔 graph는 비평탄한 예측을 냈다. 이는 단일 관계 impact 점수가 경로 상호작용을 놓칠 수 있는 결정론적 한계 사례다. 별도 fixture에서 모든 impact가 0이어도 결정론적 canonical pair를 질문한다.

## 전체 cohort 저장 산출물 감사

`audit_saved_outputs.py`는 결과 재실행 없이 사적 저장물을 읽어 Development 64 × 195 policy/budget keys 및 Held-out 200 × 195 keys를 확인했다. cohort당 12,480 및 39,000행 recommendation과 같은 수의 evaluator rows가 있으며, 총 2,720 deterministic recommendations가 포함된다(나머지는 32-repeat Random trajectories). 고유 key, 0–4 prefix, 행동, edit count, DAG, evaluator arithmetic, perfect expert relation, key/action/loss 연결을 검사했다.

점수 replay는 매 질의 시점 정책을 다시 호출해 선택된 pair가 점수 최댓값/결정론적 tie-break와 일치하는지 4,224회 확인했다(Development 1,024; Held-out 3,200). 재생된 candidate score 113,984개는 evaluator 결과가 아닌 정책 진단이다.

## 한계

17개 fixture/test가 prompt의 모든 가능한 combinatorial interaction이나 실제 인간 전문가 오류를 exhaustively 검증하지 않는다. BIC는 근사 heuristic이며 Gaussian/local score 가정이 어긋날 수 있다. Query replay는 저장된 결과와 정책 소스의 정합성 검사이지 독립적인 전문가 검증은 아니다. 전 과정의 OS sandbox는 없다.

# Research F-Lite 정책 정의

모든 정책은 B=0–4 질의 단계와 기존 C learner/action/loss 계약을 사용한다. F 정책의 오류 의심도는 확률로 보정되거나 검증된 posterior가 아니며, 단순 구조 점수다.

| 정책 | 질의 선택 기준 | 해석 |
|---|---|---|
| S0 | 질의 없음 | 초기 그래프 기준 |
| RANDOM_VERIFICATION | 균일 무복원 pair 선택, 32 반복 | 질의 수 고정 무작위 기준선 |
| FIT_BASED_VERIFICATION | Gaussian local BIC 차이 기반 | 관측 분포에 대한 구조 적합 heuristic |
| SUSPICION_ONLY | 현재 relation과 대안별 local-BIC weight의 불일치 점수 | 오류 의심도 중심 |
| DECISION_IMPACT_ONLY | 후보 relation 변경이 Ridge 기반 선택 행동/예측 손실에 미치는 변화 | 행동 중요도 중심 |
| DECISION_WEIGHTED_VERIFICATION | suspicion × decision impact | 제안된 결합 점수 |
| ORACLE_ASSISTED_M4_DIAGNOSTIC | 기존 C reference-aware M4 | 비동등 Oracle-assisted 상한 진단 |
| GRAPH_FREE_ASSOCIATION_DIAGNOSTIC | 관측 X–Y 연관성 회귀 추천 | 그래프 미사용 기준선 |

후보 쌍은 reference-blind하게 모든 unordered variable pair다. Local BIC는 인과 방향의 참 확률이 아니다. Impact 점수도 counterfactual GT value of information이 아니라 잘못 지정한 후보 graph 아래의 learner 예측 변화다. 최종 정책은 기존 Learner를 재사용하며 질의 응답에 따라 graph 관계를 수정하고, cycle이 생기는 변경은 pending 상태로 두고 다시 검사한다. unresolved 관계는 기존 C learner bridge의 계약대로 학습에서 생략된다.

완벽한 전문가는 실제 실험에서 가질 수 없는 이상화다. Noise sensitivity에서는 고정 pair별 seed로 정확도 0.9/0.8의 오답을 모의하고, 정답 이외 두 관계 중 하나를 균등 선택하도록 잠갔다. 이 민감도는 전문가 실측 자료가 아니다.

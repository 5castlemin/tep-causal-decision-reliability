# 최종 주장–근거 매트릭스

| 주장 | 등급 | 근거와 단위 | 반례·제한 | 허용 문장 |
|---|---|---|---|---|
| 제한 예산 구조 수정은 무수정 대비 의사결정 손실을 낮출 수 있다 | `CONFIRMATORY_WITHIN_FROZEN_SYNTHETIC_CONTRACT` + `CONDITIONAL_EXTERNAL_ROBUSTNESS` | C Held-out 독립 합성 SCM 200개, B=2 paired regret delta +0.07483636, 95% CI [0.05089822, 0.09877450]. D 고정 DRF DGP·학습 프레임의 G0 200개, tracking-loss 대비 +0.03422490, two-source CI [0.00617347, 0.06535080]. | D는 실제 제조 개입도 독립 SCM 표본도 아니다. 두 효과 척도는 직접 비교 불가. | “동결된 합성 계약에서 효과가 확인됐고, 단일 외부 반합성 생성환경에서도 조건부로 양의 대비가 관찰됐다.” |
| 과제 중심 수정은 edit 횟수를 줄일 수 있다 | `DEVELOPMENT_SELECTED_SECONDARY` | C M4 평균 비용 .695 vs Full Greedy 1.435; D .335 vs 1.160, action 일치 198/200. | 비용은 원자 edit 수이며 시간·금전·전문가 비용이 아니다. M4 손실은 D에서 Full Greedy보다 +.00122956 높음. | “두 연구에서 M4는 평균 수정 횟수가 적었지만, D에서는 손실이 약간 높았다.” |
| 경로·효과 부호 복원이 성능 차이를 설명한다 | `POST_HOC_MECHANISM_EVIDENCE` | 원본 Ledger의 C held-out 사례 재계산. S0 regret 양수 55건 중 49건은 경로 부재/flat 예측. M4 우세 action-disagreement 6개 중 5개 경로 복원, 1개 기존 경로에서 행동 부호 차이. | 사후 분석이며 매개효과를 확증하지 않는다. …000146 구조 수정 후 악화 사례가 있고 …000076 DAG 제약 반례도 있다. | “사후 사례 분석은 경로 부재와 방향 추정이 주요 설명 후보임을 보인다.” |
| 구조 정확도와 의사결정 성능은 항상 일치한다 | `UNSUPPORTED` | …000146에서 수정 후 행동/손실 악화; 구조가 달라져도 행동 동일 사례 다수. | 구조 지표는 downstream 목적을 직접 최적화하지 않는다. | “구조 개선만으로 의사결정 개선이 보장되지는 않는다.” |
| 자체 signed-linear SCM 밖에서도 긍정 효과가 관찰될 수 있다 | `CONDITIONAL_EXTERNAL_ROBUSTNESS` | Station1 6노드 reference, 재적합 DRF 기반 단일 DGP; 200 corruption draw. | 외부 DGP 하나, MC 및 combined 정밀도 목표 미달, 학습 프레임 고정. | “한 외부 반합성 생성환경에서 조건부 양의 효과가 관찰됐다.” |
| M4는 항상 Full Greedy보다 우수하다 | `UNSUPPORTED` | C에는 FG 우세 사례; D M4 손실이 FG보다 .00122956 큼. | 방향 일관성 없음. | 사용 금지. |
| 그래프 정책은 graph-free 회귀보다 우수하다 | `UNSUPPORTED` | D graph-free baseline loss .789362로 Full Greedy와 동일. | 단일 DGP·고정 학습표본. | “이번 외부 조건에서는 graph-free 기준선이 Full Greedy와 같은 손실을 보였다.” |
| 현장 제조 효과 또는 배포 안전성이 입증됐다 | `UNSUPPORTED` | 실측 개입이 아닌 반합성 DGP. | 장치·공정·운영비·안전성 미평가. | 사용 금지. |

세부 출처, 재계산 상태와 통계 단위는 `ORIGINAL_LEDGER_MECHANISM_AUDIT.md`, `RESEARCH_D_FINAL_REAUDIT.md`, `FINAL_RESULTS_TABLES.md`를 참조한다.

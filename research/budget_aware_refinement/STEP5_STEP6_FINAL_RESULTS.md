# Step 5–6 최종 결과 교차 검증

이 문서는 별도 개발·재현 코호트의 저장 요약과 원시 분석 기록을 대조한 결과다. SCM을 새로 생성하지 않았고, 코호트들을 합쳐 추론하지 않았다.

## 분모와 완전성

| 코호트 | Proposal 분해 | Admission | 세 유형/Composite | 후속 실패·결측 | delta |
|---|---|---:|---:|---:|---:|
| Step 5 개발 | 211 = 145 Q 거절 + 2 task/topology 실패 + 64 admission | 64 | 64/64 | 0 | +1 32, −1 32 |
| Step 6 독립 재현 | 675 = 466 Q 거절 + 9 task/topology 실패 + 200 admission | 200 | 200/200 | 0 | +1 100, −1 100 |

두 코호트 모두 registry 및 원장 바인딩, 고유 ID, 완료 단계, finite regret 및 composite를 독립 분석기가 확인했다. 독립 analytic evaluator는 개발 384개와 재현 1,200개 정책·유형 실행을 재계산했고 평균·손실·regret 최대 절대 오차는 각각 0이었다. raw inventory의 경로·크기·SHA-256은 분석 전후 일치했다.

## SCM 수준 결과

`D_i,type = Regret_Global,type − Regret_TaskFocused,type`; `D_i`는 FN/FP/REV 산술평균이다. 양수는 Task-Focused regret이 더 작음을 뜻한다.

| 통계량 | Step 5 개발 | Step 6 재현 |
|---|---:|---:|
| n SCM | 64 | 200 |
| 평균 | 0.0146604849 | 0.0200725113 |
| 중앙값 | 0 | 0 |
| 표본 SD | 0.0621579483 | 0.0824273027 |
| Q1 / Q3 | 0 / 0 | 0 / 0 |
| 최소 / 최대 | −0.0006981415 / 0.4195602264 | −0.1447868859 / 0.6097471190 |
| 양수 / 음수 / 0 | 6 / 1 / 57 | 25 / 8 / 167 |
| 최댓값 1개 제외 평균 | 0.0082335 | 0.0171093 |
| 최댓값 2개 제외 평균 | 0.0046345 | 0.0143115 |
| 상위 1개 / 2개 합 기여율 | 44.7% / 69.4% | 15.2% / 29.4% |

극단값 제외 평균은 지정 민감도 진단이며 전체 평균을 대체하지 않는다. 양수 평균은 다수의 양수 사례를 뜻하지 않는다. 재현 코호트의 83.5%가 동률이고 4%가 음수였다.

## 유형별 차이

| 유형 | Step 5 평균 D | Step 6 평균 D | Step 5 양/음/0 | Step 6 양/음/0 |
|---|---:|---:|---:|---:|
| FN | 0.0058258 | 0.0307732 | 2/1/61 | 12/2/186 |
| FP | 0 | 0.0021787 | 0/0/64 | 3/0/197 |
| REV | 0.0381557 | 0.0272656 | 5/0/59 | 17/8/175 |

유형별 관측 평균의 순위는 코호트에서 달랐다(개발 REV가 가장 큼, 재현 FN이 가장 큼). 세 유형은 동일 SCM 내 반복 측정이므로 유형별 n을 독립 SCM n으로 해석하지 않는다.

## 그래프, Action, k, regret

| 코호트/유형 | 최종 그래프 다름 | Action 같음 | 선택 k 다름 |
|---|---:|---:|---:|
| 개발 FN | 18/64 | 64/64 | 3/64 |
| 개발 FP | 31/64 | 64/64 | 0/64 |
| 개발 REV | 26/64 | 64/64 | 5/64 |
| 재현 FN | 76/200 | 200/200 | 14/200 |
| 재현 FP | 109/200 | 200/200 | 3/200 |
| 재현 REV | 93/200 | 200/200 | 25/200 |

동일 Action은 paired design에서 과제가 동일했기 때문이며 정책 독립 성과가 아니다. 동일한 `k`는 같은 개입값이므로 공통 GT 손실도 동일하다. 그래프 차이만으로 결정/손실 차이를 주장하지 않는다.

## 집단 기술통계

Step 5 template counts: chain 17, fork 5, multiple paths 32, common cause 10. Step 6: 49, 28, 88, 35. Step 6 평균 D는 delta +1에서 0.0210997, −1에서 0.0190453이었다. template별 Step 6 평균은 chain 0.0067301, fork 0.0018254, multiple paths 0.0338076, common cause 0.0188156. 작거나 불균형한 하위집단의 수치는 탐색적 기술값이다.

## 독립 감사 원시 출처

- Step 5 보고서/요약/SCM CSV: `step5_development_v1/STEP5_DEVELOPMENT_EXECUTION_REPORT.md`, `STEP5_DEVELOPMENT_REGRET_ANALYSIS.md`, `STEP5_DEVELOPMENT_ANALYSIS_SUMMARY.json`, `STEP5_DEVELOPMENT_SCM_SUMMARY.csv`, `STEP5_DEVELOPMENT_RAW_INVENTORY.json`.
- Step 6 보고서/요약/SCM CSV: `step6_confirmation_v1/STEP6_CONFIRMATION_EXECUTION_REPORT.md`, `STEP6_CONFIRMATION_REGRET_ANALYSIS.md`, `STEP6_CONFIRMATION_ANALYSIS_SUMMARY.json`, `STEP6_CONFIRMATION_SCM_SUMMARY.csv`, `STEP6_CONFIRMATION_RAW_INVENTORY.json`.
- Cross-cohort comparison: `step6_confirmation_v1/STEP5_VS_STEP6_REPLICATION_COMPARISON.md`.
- Raw outputs are outside the repository at their dedicated Windows run roots and are read-only. This repository contains inventories/summaries, not copies of SCM raw ledgers.

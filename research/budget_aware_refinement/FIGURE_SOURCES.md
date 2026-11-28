# Step 8 그림 출처와 재생성

모든 그림은 벡터 SVG다. Step5/6 raw registries와 ledgers는 읽기 전용이며, 시각화를 위해 새 SCM이나 결과를 만들지 않았다.

| 파일 | 표시 내용 | 입력 출처 | 단위·주의 |
|---|---|---|---|
| `figures/step8_scm_difference_distribution.svg` | SCM별 D 점 분포, 평균 마름모, 부호/동률 | `step5_development_v1/STEP5_DEVELOPMENT_SCM_SUMMARY.csv`; `step6_confirmation_v1/STEP6_CONFIRMATION_SCM_SUMMARY.csv` | 점 하나는 SCM 1개. x-jitter는 시각 전용. 0점 유지. |
| `figures/step8_error_type_means.svg` | FN/FP/REV별 평균 대응 차이 | 같은 두 SCM summary CSV | 오류 유형은 SCM 내 반복 측정; 막대는 추론 비교가 아니다. |
| `figures/step8_graph_k_regret_transition.svg` | 그래프·selected k·regret이 다른 SCM 수 | Step6 summary report의 집계와 200개 ledger 이벤트 교차 집계 | 분모 200/type. 같은 Action은 고정 과제 때문. 관측 빈도를 일반법칙처럼 해석 금지. |
| `figures/step8_extreme_sensitivity.svg` | full mean, top 1/2 D 제외 mean | `STEP5_STEP6_REPLICATION_COMPARISON.md`; Step5/6 analysis summaries | 0에서 시작하는 축. 제외 요약은 감도진단이며 primary mean을 바꾸지 않는다. |
| `figures/step8_case_mechanism.svg` | proposal 238/606의 task-path schematic 및 정책별 편집/k/regret | 각 proposal의 Step6 JSONL ledger events; `CASE_STUDY_POSITIVE_NEGATIVE.md` | 두 사례만 표시. 전체 DAG가 아니며 대표성 표본이 아니다. |

재생성 명령(저장된 추적 CSV에 대해서만):

```powershell
python scripts/render_step8_figures.py
```

SVG의 `viewBox`와 XML well-formedness를 확인했다. 글꼴은 로컬 시스템의 Segoe UI/Arial 대체 글꼴에 따라 달라질 수 있다.

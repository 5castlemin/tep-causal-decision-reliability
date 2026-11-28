# 연구 발표 구성안 (14장)

| # | 슬라이드 제목 | 핵심 메시지 | 근거 수치 | 그림/도표 제안 | 발표자 설명 |
|---:|---|---|---|---|---|
| 1 | 불완전 인과그래프와 제조 의사결정 | 구조 점수만으로 결정 품질을 대변할 수 있는가가 출발점 | 연구 범위: TEP 구조 자산 + 합성 정책 실험 | 연구 계보 타임라인 | 실제 공정 검증까지 끝난 연구가 아님을 첫 장에서 분명히 한다. |
| 2 | 인과그래프에서 의사결정까지 | 구조→학습→추천→정답 손실은 다른 단계 | 6단계 개념 흐름 | 화살표 파이프라인 | 한 단계의 성공이 다음 단계의 성공을 보장하지 않는다. |
| 3 | 원래 질문과 현재 질문 | Step 4–6은 초기 지표 우열 질문을 직접 검증하지 않는다 | 원 질문 vs B=1 ordering 질문 | 두 질문 나란히 | 서로 연결되지만 추정 대상이 다른 연구다. |
| 4 | 왜 구조 점수만으로 부족할 수 있나 | 같은 점수에서 오류 위치가 다르면 손실도 다를 수 있다 | 162 쌍: 손실 악화 93, 개선 4, 동률 65 | matched-pair 분포/사례 도식 | 존재 증거이며 독립 공정 수나 보편 법칙은 아니다. |
| 5 | Step 3 파일럿이 알려준 것 | 단순 파일럿은 정책을 구분할 조건이 부족했다 | 114/114 regret 0; supplement 456회 | 예산·후보 소진 그림 | 소규모 구조 진단으로 Step 4 설계를 개선했으며 성능 증명은 아니다. |
| 6 | 동결된 Step 4 계약 | 하나의 제한된 질문·모집단·정책 비교를 고정했다 | Q-common, indirect-only, B=1, 3 error types, 1/3 | 계약 카드 | 전체 Step 상태와 Option B를 안내한다. |
| 7 | 두 코호트와 재현성 | 개발과 confirmation namespace를 분리해 같은 계약을 적용 | Step5 n64/211 proposals; Step6 n200/675 | 분모 흐름도 | admission·완전 평가·독립 SCM 단위를 분리한다. |
| 8 | 평균만 보면 놓치는 분포 | 평균은 양수지만 대다수 SCM은 동률 | Step5 57/64 zero; Step6 167/200 zero | `figures/step8_scm_difference_distribution.svg` | 0점도 전부 표시한다. Step6 음수 8건이 있고, 점은 독립 SCM 단위다. 기술적 결과이지 확인적 우월성 검정이 아니다. |
| 9 | 그래프가 달라도 결정은 같을 수 있다 | graph edits ≠ action choice | Step6 graph diff 76/109/93, k/regret diff 14/3/25 (FN/FP/REV) | `figures/step8_graph_k_regret_transition.svg` | 같은 Action은 task를 고정했기 때문이다. 실제 k 차이가 난 예외와 regret의 관계를 보여준다. |
| 10 | 오류 유형 패턴은 고정되지 않았다 | 유형별 평균 순위가 코호트 간 달랐다 | Step5 REV .0382; Step6 FN .0308 | `figures/step8_error_type_means.svg` | 같은 SCM 안의 반복 오류유형이며 유형 순위를 확인적 결론으로 올리지 않는다. |
| 11 | 극단값과 민감도 | 전체 평균은 소수 사례 크기에 영향받는다 | Step6 상위 2건 29.4%, 제외 평균 .0143; Step5 69.4% | `figures/step8_extreme_sensitivity.svg` | y축은 0에서 시작한다. 민감도는 전체 평균을 대체하지 않는다. |
| 12 | 실제 사례: Task-Focused가 유리 | 이 사례에서 경로 오류 수정과 `k` 선택이 연결됐다 | proposal 238: FN/REV 각각 Dtype +0.914621, FP 0; Di +0.609747 | `figures/step8_case_mechanism.svg` 상단, 세부 [case study](CASE_STUDY_POSITIVE_NEGATIVE.md) | 설명용 선택 사례임을 말하고, 첫 단계의 Task-Focused 이점이 항상 재현되는 법칙이 아님을 설명한다. |
| 13 | 실제 반례: Global이 유리 | 경로 간선을 복구해도 개입 손실이 나빠질 수 있다 | proposal 606 REV D=−0.434361; SCM Di=−0.144787 | `figures/step8_case_mechanism.svg` 하단 | 경로 우선수정만으로 계수·Ridge 추천·GT 손실을 보장하지 않는다. |
| 14 | 결론과 실제 공정의 거리 | 결과는 synthetic Q-common/B=1에 조건부다 | Step4 FROZEN; Step5/6 완료; 산업효과 미검증 | 한계 경계 그림/다음 단계 | Task-Focused 우월성, 구조 지표 우열, 제조 recovery/safety는 검증되지 않았다. |

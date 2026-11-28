# 관련 연구와 기여 범위

## 관련 흐름

### 인과 구조 학습의 평가

Eigenmann, Mukherjee, Maathuis (2020)는 causal structure learning 알고리즘을 그래프 일치도만이 아니라 causal risk와 decision-theoretic loss 관점에서 평가하고, 관측·개입 자료를 활용하는 risk 추정 절차를 논의했다. 이는 graph score와 실제 사용 성능을 구분해야 한다는 본 연구의 큰 동기와 가깝다. 본 연구의 Step 5/6은 해당 평가 문제 전반을 해결하거나 그 방법과 경쟁하는 것이 아니다. 정답 DAG가 주어진 합성 환경의 수정 후보 순서를 비교한다.

Emezue et al.의 Bayesian causal discovery benchmark는 causal discovery 결과를 downstream treatment-effect estimation에서 평가한다. 구조 학습 결과의 품질을 downstream task로 연결하는 점에서 원래 질문과 인접하다. 본 연구의 차이는 Bayesian graph discovery 또는 효과추정 정확도 비교가 아니라, oracle 기반 FN/FP/REV 후보의 편집 순서와 공통 action grid의 regret에 초점을 둔 실험이다.

### 결정 목적의 예측/최적화

Elmachtoub & Grigas의 Smart Predict, then Optimize (SPO)는 예측 오차와 downstream optimization decision loss가 다를 수 있음을 형식화하고 decision-aware loss를 제안했다. 이는 예측·결정 평가를 분리하는 개념적 배경이다. 본 연구는 SPO 학습법을 구현하지 않았고, 같은 개념을 새롭게 발명했다고 주장하지 않는다.

### 구조 학습과 그래프 공간

Squires & Uhler의 causal structure learning review는 DAG 탐색 공간과 동치류의 조합론적 구조를 정리한다. 본 연구는 새 causal discovery 알고리즘이나 식별 이론을 제시하지 않는다. 오히려 완전 관측과 알려진 GT를 사용한 작은 synthetic testbed로 범위를 제한한다.

## 이 연구가 실제로 추가한 것

현재 결과의 기여 후보는 다음처럼 제한적으로 표현할 수 있다.

1. 제한된 B=1에서 유형별 오류 수정 후보와 과제 관련성 순서를 명시적으로 대응시켰다.
2. Global을 ID-ordered ordering으로 정확히 특정하고, Task-Focused와 같은 SCM·관측자료·오류·action 평가를 공유했다.
3. SCM 내부 FN/FP/REV 반복 측정을 동일 가중으로 하나의 SCM 차이로 요약하고, 개발 코호트와 domain-separated held-out 코호트 결과를 별도로 공개했다.
4. 최종 그래프 차이, selected k 차이 및 analytic GT regret 차이가 다른 사건임을 실제 로그와 함께 보여줬다.

## 독창성에 대한 판단

이 검토는 repository의 기존 비교문헌과 확인 가능한 주요 원문을 중심으로 한 서술적 검토이지 systematic review가 아니다. 인접 연구가 이미 downstream causal loss나 decision-focused evaluation을 다루므로 “그래프 오류가 결정에 영향을 줄 수 있다”는 일반적 문장만으로 독창성을 주장할 수 없다. 본 연구의 좁은 차별점 후보는 오류 유형/위치, 편집 예산, Task-Focused 대 ID-ordered ordering, SCM별 analytic regret을 함께 둔 실험 설계다. 이 후보도 기존 연구 전체를 체계적으로 검색·비교한 뒤 확정된 novelty claim이 아니다.

## 참고문헌

1. Eigenmann, M. F., Mukherjee, S., & Maathuis, M. H. (2020). Evaluation of Causal Structure Learning Algorithms via Risk Estimation. *Proceedings of UAI 2020*, PMLR 124, 151–160. [원문 및 서지](https://proceedings.mlr.press/v124/eigenmann20a.html).
2. Emezue, C. C., Drouin, A., Deleu, T., Bauer, S., & Bengio, Y. (2023). Benchmarking Bayesian Causal Discovery Methods for Downstream Treatment Effect Estimation. arXiv:2307.04988. [원문](https://arxiv.org/abs/2307.04988).
3. Elmachtoub, A. N., & Grigas, P. (2022 issue; first published online 2021). Smart “Predict, then Optimize”. *Management Science, 68*(1), 9–26. DOI: [10.1287/mnsc.2020.3922](https://doi.org/10.1287/mnsc.2020.3922).
4. Squires, C., & Uhler, C. (2023). Causal Structure Learning: A Combinatorial Perspective. *Foundations of Computational Mathematics, 23*, 1781–1815. DOI: [10.1007/s10208-022-09581-9](https://doi.org/10.1007/s10208-022-09581-9).

Repository context: `research/budget_aware_refinement/LITERATURE_NOVELTY_MATRIX.md`.

# 선행연구 비교 — 2026-11-10

확인 범위는 아래 출판사·저자 원문 및 초록 중심이다. **GT 열의 미상은 정답 미사용의 증거가 아니다.** 비용·평가에 관한 차이와 마지막 열은 우리 연구의 해석이며 저자가 직접 입증한 결론이 아니다. 최초성이나 선행연구 부재를 주장하지 않는다.

| 문헌 | 문제 / 구조 수정 | 비용 정의 | 성능 | GT 사용·환경 | 중복 및 남는 차별성 후보 |
|---|---|---|---|---|---|
| [Causal Structure Learning: A Combinatorial Perspective](https://pmc.ncbi.nlm.nih.gov/articles/PMC9342837/) | 구조 학습의 조합론 관점; 우리 방식의 오류 repair가 주제가 아님 | 구조학습의 계산·실험 관련, 단일 수정비용과 동일하지 않음 | 구조 식별/복잡도 | 이론·예시, 정답 사용 범위 개별 결과별 확인 필요 | 구조 탐색과 겹침; 고정 수정 예산에서 downstream regret 비교는 별도 질문 |
| [ABCD-Strategy](https://proceedings.mlr.press/v89/agrawal19b.html) | 대상 구조 발견을 위한 Bayesian 실험 선택; oracle 오류 repair 아님 | 개입 실험 예산 | 대상 구조 식별 | 가정된 모델·합성 실험, 정답 접근은 세부 실험별 확인 | 과제 관련 구조에 예산 집중은 중복; 우리는 정답 오류 후보 수정 이후 결정 후회 평가 |
| [Smart Predict, then Optimize](https://doi.org/10.1287/mnsc.2020.3922) | 예측을 결정 손실에 맞춰 학습; 그래프 repair 아님 | 의사결정 목적 손실 | downstream 최적화 손실 | 최적화·데이터 사례; causal DAG GT 주제 아님 | 예측오차와 결정손실 차이는 중복; 인과 오류 유형별 수정 예산은 별도 |
| [Active learning for optimal intervention design](https://dspace.mit.edu/entities/publication/bcca862a-7b77-44cf-a56d-4f8e1f05d410) | 목표 평균에 도달할 개입을 Bayesian 순차 선택; 구조 repair 아님 | 실험/표본의 순차 횟수 | 개입 최적성·목표 평균 차이 | 이론은 알려진 선형 그래프, 합성 및 단일세포 실험 | 목표 평균 기반 결정은 직접 중복; 그래프 오류 유형과 수정비는 별도. DOI 원문 접근 제한으로 MIT의 저자 공개 출판본/초록 확인 |
| [Partial Structure Discovery and Causal Bandits](https://papers.nips.cc/paper_files/paper/2024/hash/c50e3c72bf45a361afc7c16d26c21a1a-Abstract-Conference.html) | 결정에 필요한 부분 구조 발견과 causal bandit; 오류 repair 아님 | 순차 학습/개입, 명시적 우리 수정비와 다름 | no-regret 이론 | 인과 bandit 가정; 정답 접근과 실험 세부는 논문별 조건 확인 | 부분 구조와 후회의 결합이 직접 겹침; 유한 예산 오류 수정 비교는 별도 후보 |
| [Bayesian Discovery and Treatment Effect Benchmark](https://www.servicenow.com/research/publication/chris-chinenye-emezue-benc-spigm2023.html) | 발견 결과의 downstream 처치효과 평가; 오류 repair 아님 | 수정비 없음/미상 | 처치효과 추정 | benchmark; 참조·데이터별 GT 사용 세부는 본문 확인 필요 | 구조품질과 효과의 연결이 겹침; 수정 예산과 정책별 선택 손실 추가 |
| [Cost-Aware Learning of Causal Graphs](https://papers.nips.cc/paper_files/paper/2018/hash/ba3e9b6a519cfddc560b5d53210df1bd-Abstract.html) | essential graph에서 최소비용 개입 구조학습; repair 아님 | 변수별 개입 비용 | 식별 비용 및 근사 보장 | 주로 이론적 그래프; 정답은 분석 기준 | 비용 제약은 중복; 간선 편집 자원과 결정 후회는 다른 대상 |
| [Weighted Causal DAG Search](https://proceedings.mlr.press/v202/choo23b.html) | 적응형 개입을 통한 DAG 탐색; repair 아님 | 노드별 개입비용 | 그래프 확인 비용·근사 | 이론적 가정; GT는 검증 기준 | 비용 인지 구조 학습과 겹침; 편집 유형·위치의 결정 효율은 별도 질문 |
| [Budgeted Causal Bandits](https://proceedings.mlr.press/v130/nair21a.html) | 비용 제약에서 행동 탐색; graph repair 아님 | 관측 및 개입 비용 | simple/cumulative regret | 가정된 causal graph의 bandit; 논문별 구조 정보 조건 확인 | 예산과 regret은 직접 겹침; 간선 수정비와 GT oracle repair 분리 필요 |

합리적인 기여 후보는 (1) FN/FP/REV 수정 유형, (2) 관측 가능한 초기 그래프 기반 과제 위치, (3) 동일 편집 예산의 결정 후회, (4) 독립 SCM 재현성을 하나의 통제 평가에서 연결하는 것이다. 이 조합의 독창성은 추가 전문 검색·전체 본문 확인 전 잠정적이다. 논문들이 우리 주장을 입증한다고 해석하지 않는다.

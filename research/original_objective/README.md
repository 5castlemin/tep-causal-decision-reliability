# 연구 C 구조 수정 엔진 (잠정 구현)

`policy_engine.py`는 정답 DAG를 이용해 **구조 오류만** 분류·수정하는 Oracle-assisted 진단기다. SCM 계수, 개입효과, GT 손실 및 Decision Regret은 입력받지 않는다. 기존 연구 B 생산 코드를 수정하지 않는다.

```powershell
python -m unittest discover -s tests -p test_original_objective_policy_engine.py -v
python scripts/validate_original_research_fixture_contract.py
python -m scripts.run_original_objective_policy_fixture
```

호출 예:

```python
from research.original_objective.policy_engine import Config, state, run_catalog, save_json
gt = state([("X", "M"), ("M", "Y"), ("A", "B")])
g0 = state([("X", "M"), ("M", "Y")])
result = run_catalog(gt, g0, "X", "Y", budget=1, config=Config())
save_json("fixture_only.json", result)
```

`state`는 각 비순서 노드쌍에 directed/UNRES/absent 중 하나만 허용한다. DAG 판정은 directed 부분에 적용한다. `task_zone`은 정답 X→Y 방향경로와 빈 conditioning에서 열린 backdoor 경로의 간선 합집합을 반환한다. FP Rule B의 추가 boundary pair는 `route_relevant_fp`로 명시해야 한다. 이 집합을 결과를 보고 생성해서는 안 된다.

기본 Config는 **미승인 Fixture 후보**다: Rule A, G0 고정 기회 수 정규화, 동일 지표·M4 활성 성분 가중, add/delete/orient/resolve 각 비용 1, 동일 구조 벌점 가중과 task 배수 1. `initial_error_count`와 Rule B는 설정으로 비교할 수 있다. 비용과 가중치를 바꾸면 정책 자체가 달라질 수 있다.

`run_catalog`는 15개 nonempty subset 및 S0, 별도 `CANONICAL_ORACLE`을 동일 G0·GT·예산·비용·DAG 조건에서 실행한다. 기록에는 사건 유형·위치, 수정 비용, 점수, 그래프 해시, 전후 공식 지표, 정책용 `P_S`, 공통 구조 벌점 `P_all`이 포함된다. `evaluation`의 GT 관련 값은 `null`로 남는다. `evaluation_record`의 Decision Margin은 예측 손실 최선과 차선의 차이만 계산하며 동률이면 0이다. GT 평가기는 향후 별도 모듈에서 연결해야 한다.

이 엔진의 실행 결과는 Fixture 산술 검증이며 연구 C의 SCM 또는 Regret 성능 결과가 아니다. D1–D19의 과학적 선택은 여전히 OPEN이다.

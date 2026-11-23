# 연구 C 정책 엔진 검증 보고

**상태:** 구현·수작업 Fixture 검증. 연구 계약 승인/사전등록 아님. 새 SCM·관측자료·개입효과·Regret 결과 없음.

## 구현

`research/original_objective/policy_engine.py`에서 graph state와 directed DAG, GT 경로·무조건화 open backdoor task zone, 단일 오류 사건 귀속, M1/M2/M3/M4 공식 지표, Oracle 수정 후보, 실제 사건 감소량/비용 Greedy, 16 subset catalog, canonical Oracle 기준선, JSON 직렬화 및 향후 평가 레코드 형식을 구현했다. GT 효과·손실·Regret은 엔진 함수 인자에 없다. 기존 연구 B의 SCM 생성·Ridge/추천·analytic GT 코드는 재사용 후보이지만 이번 엔진에는 연결하지 않았다.

## 실행 검증

- Python 3.11.15: `python -m unittest discover -s tests -p test_original_objective_policy_engine.py -v` → 8개 통과.
- `python scripts/validate_original_research_fixture_contract.py` → 기존 수작업 지표·A/B 귀속·분모 착시·cycle·비용·정규화 검증 통과.
- `python -m compileall -q research/original_objective tests/test_original_objective_policy_engine.py` → 통과.
- 기존 기준 Fixture의 M1=`1/2`, M2=`1/2`, M3 accuracy=`0/1`, unresolved=`0/1`, M4 FN=`1` 재현. M2는 M1 복구 후 FP 1개를 유지하면서 `1/2→1/3`이 됨을 확인했다. 이를 M2 repair gain으로 보상하지 않는다.
- 16 subset, B=0..4의 고유 최종 그래프 수는 `1,5,11,15,16`으로 기존 Fixture 보고와 일치했다. M4 복합 사건 `FN=FP=REV=UNRES=1`, Rule B에서 boundary FP가 task 쪽으로 한 번 이동하는 것도 확인했다.
- `python -m scripts.run_original_objective_policy_fixture`로 85개 정책×예산 실행의 전후 지표·비용·해시·수정 로그를 `research/original_objective/fixture_run_v1.json`에 저장했다(고정 손그래프만 사용).
- 전체 `unittest discover -s tests -q`: 199개 중 22개 import 오류(이 Python 3.11 실행 환경에 NumPy 없음), 기존 Step4B4 원시 ledger 해시 관련 실패 1개. 전체 스위트 통과로 보고하지 않는다. 보호 파일은 수정하지 않았다.
- GT에 없는 효율/Regret 수치는 생성하지 않았다.

## 잠정 설정과 미승인 결정

`Config`의 Rule A, open backdoor, 고정 기회 수 정규화, 동일 지표·M4 활성 성분 가중, 단위 수정비용, P_all 동일 오류 가중은 모두 구현 기본값일 뿐이다. Rule B는 사전 입력된 boundary route pair가 필요하다. D1–D6의 task zone/FP 귀속·공식 분모·M4 support, D7/D17/D18의 scheduler 정규화·β, D9–D12의 비용·잔존 벌점·λ/ρ, D13–D16의 연구 모집단·자료 분리·평가 계약은 과학적 선택으로 OPEN이다. D19의 복수 후보 재계산과 DAG 거절은 기술적으로 구현했으나 본 실험 운영 계약은 OPEN이다.

## 한계 및 다음 Gate

고정 소형 DAG에서 코드 일관성을 확인한 것이며 정책 우월성, M1–M4의 상대적 중요성 또는 의사결정 결과를 확인한 것이 아니다. 새 SCM 실험 전에는 과제 구역·boundary FP 규칙, 공식 분모와 M4 scalarization, 정규화·동률, 수정 비용·벌점과 예산, 개발/가중치 추정/독립 평가 분할 및 표본·통계 계약을 승인하고 동결해야 한다. 이후 새 개발 SCM 코호트 → 16 정책/기준선 비교 → 조작·Regret 분석 → 별도 독립 평가 순서로 진행한다. 기존 Step 5/6은 새 연구의 미열람 확인 표본이 아니다.

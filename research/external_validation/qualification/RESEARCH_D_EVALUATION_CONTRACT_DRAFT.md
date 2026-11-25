# Research D 평가 계약 초안 — 미승인

이 초안은 Step 1 제안일 뿐이다. 외부 결과를 이용해 action, 목표, lag, window, task 또는 정책을 선택하지 않았다.

## 후보 estimand와 과제

- 제안 조작: 배정된 `green` 밝기 명령 (settable integer 0–255). 실제 광출력 actuation telemetry가 확인되지 않으면 명령 ITT로 한정한다.
- 제안 목표: `current_led_2_uv` (UV LED 전류, A 단위 calibrated measurement; 광출력/품질이 아님). 전류가 decision target으로 의미가 있는지는 별도 정당화가 필요하다.
- 경로: 설정 도식상 `green→ir_1→led_2_uv→current_led_2_uv`; strict indirect-only 조건은 direct nonedge 증거가 없어 보류.
- primary 형태 제안: 동일 과제·공통 행동 집합 A에서 정책 추천의 검증 손실 차이 `Δ_D = L_exp(a_S0)-L_exp(a_FullGreedy)`. 낮은 쪽이 유리한 방향으로 부호를 고정할 필요.
- 실측 평균 목표 추종 손실: `L_c(a)=(μ_c(a)-y*_c)^2/s_train,c^2`. 이는 관측 개별값 MSE가 아니다. 학습만으로 `μ`를 추정하고 독립 평가자료에서 행동 추천 금지. 평가 시 행동별 실측 평균으로 손실을 산출하면 선택 편향/공분산을 반영한다.

같은 공통 A에서 두 정책의 손실 차이는 absolute regret의 공통 oracle 최소항 상쇄와 연결되지만, 최소 평균/최소 손실의 추정 불확실성은 남는다. Primary 정책 간 대비를 absolute empirical regret과 혼동하지 않는다. 행동별 평균 제곱의 비선형 편향, shared evaluation data의 공분산, 선택된 최솟값의 낙관 편향을 추론에 반영한다.

## 설계 요소 제안 (확정 전)

| 요소 | 초안 | 사전 확정에 필요한 증거 |
|---|---|---|
| 참조 | partial/reference-relative pair scope; strict C DAG 반복 아님 | pair-level evidence 및 전문가 확인 |
| 행동 A | 공개 generator의 실제 배정 수준만 지원 후보; `{30,45,60,75,90}`은 Step0 예시일 뿐 채택 아님 | 명령 구현, 공통 support, 평가 독립성 |
| 분할 | 기존 20×5500 경계는 논문 설명과 부합하지만 rowwise SET experiment이며 CSV에 train/test label 없음. 원 논문에서 이 benchmark를 이미 사용했으므로 blind external evaluation이 아님 | 새 command schedule과 독립 세션/수집 자료 또는 공개 benchmark 재분석으로 주장범위 재설정 |
| 목표 y* 및 scale | train-only, 단위/운영 의미와 목표 선택 근거 선등록 | 센서 단위, 스케일 규칙, 사용자 결정 |
| 최소 지원 | 행동별 독립 run/session support를 사용; 임의 행 수 threshold 미지정 | 원하는 정밀도와 분산/ICC 정보 확보 절차 |
| 손실/불확실성 | paired 정책 대비, run 단위 또는 정당화한 randomization/serial model | 독립단위 확인; cluster 숫자만으로 독립 가정 금지 |
| G0/예산 | 별도 사전등록; observational discovery/fit을 당연시하지 않고 개입자료에서 graph estimate를 만드는 방식 정의. 현재 90-node에 B=0..4 그대로 복사 금지 | 개입식 learner compatibility, 오류 분모, reference contract, cost semantics |
| 실패/제외 | 행/세션 제외 기준 선등록, 부정결과와 실패 seed 보존 | 장치 로그/quality flags |
| 누출 방화벽 | 추천 모델은 train 자료만; action choice, 평가 응답은 evaluator에 격리 | split manifest와 코드 검토 |

## Graph-free baseline

`GRAPH_FREE_ACTION_BASELINE`은 동일 train split, 동일 관측변수/가능하면 동일 learner class, 동일 공통 A와 동일 목표/손실로 각 행동의 평균 반응을 직접 예측하고 최소 예측 손실 행동을 추천한다. 완전 무작위 green 배정은 arm mean 학습에 자연스러운 comparator이나 S0/Full Greedy보다 더 많은 action-outcome supervision을 제공할 수 있어 비교 질문은 “graph-repair pipeline vs direct randomized action learner”다. 정보 차이를 보고하고 그래프 기반 정책과 동등 정보라고 주장하지 않는다. train/evaluation은 session/시간에 따라 분리, support 밖 행동 금지, 평가 반응으로 행동 재선택 금지. 이 기준선은 현재 Primary S0 vs Full Greedy를 대체하지 않으며 구현/성능계산은 하지 않았다.

## 정밀도 계획

표본 수를 지금 임의로 고정하지 않는다. 필요한 최소 과학적 대비/허용 CI 폭을 연구 계약에서 먼저 정하고, 독립 단위 내 처리 배정과 반복 반응의 분산, serial dependence/ICC, paired 손실 공분산을 개발 자료 또는 별도 노출 진단에서 추정한다. 독립 session/device가 없으면 확증 목표의 정밀도 계산이 성립하지 않는다. 필요한 표본이 현재 archive 지원보다 크면 신규 독립 물리 수집 또는 조건부 기술 사례로 축소 중 결정한다.

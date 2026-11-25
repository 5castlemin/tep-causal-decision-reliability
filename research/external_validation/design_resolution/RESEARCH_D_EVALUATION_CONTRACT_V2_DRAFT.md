# Research D 평가 계약 v2 — 미승인 설계 초안

OPTION C에 따라 Wind Tunnel archive에 대한 정책 성능 평가는 시작하지 않았다. 아래는 후속 재설계 결정을 돕는 초안이며 Research C 계약을 수정하지 않는다.

## 후속 설계가 연구질문을 유지하려면

연구질문은 제한 예산하 구조 불일치 repair와 실측 decision loss의 관계로 유지할 수 있다. 다만 참조는 완전 물리 GT가 아니라 핀된 `wt_standard` 도식에 대한 **reference-relative** benchmark여야 한다. Direct task는 strict indirect-only 반복이 아니며 Task zone/Rule A/오류 분모가 Research C와 다르다. 32 nodes/42 edges의 오류 pair universe 및 비용/예산을 새로 사전 지정해야 한다.

## 후보 추정대상

확정 전 후보: assignment block에 배정된 `load_in` 명령 수준과 `rpm_in` 또는 `pressure_intake`의 측정 반응. 목표는 운영 문서에서 정한 값을 우선하고, 그런 값이 없으면 평가 응답을 보지 않은 개발 기준으로만 정해야 한다. scale은 train-only로 산정한다. 단위·손실의 운영 의미가 확보되지 않으면 목표추종 점수를 목적 효용으로 부르지 않는다.

가능한 loss는 `L(a) = (E[Y | assigned load_in=a, declared window] - target)^2 / scale_train^2`. 이것은 block 평균반응의 목표추종 손실이며 개별 행 MSE나 에너지/안전 효용이 아니다. 후보 primary contrast `Δ = L(a_S0)-L(a_FullGreedy)`는 동일 task, train, reference, G0, budget, action set 및 평가자료에서의 paired contrast다. 양수는 Full Greedy가 낮은 손실이다. M4는 secondary 후속 비교. 절대 empirical regret은 최적 arm 선정의 낙관편향과 추정 불확실성까지 정당화될 때만 고려한다.

## 미확정 설계 항목

| 요소 | 초안 | 선행 증거/승인 |
|---|---|---|
| reference | 핀된 standard reference, reference-relative discrepancy | graph provenance와 pair semantics; complete physical GT 금지 |
| action/target | `load_in`, Y는 공식 변수 의미/운영 목표로 사전 선택 | 운영상 target/단위 근거. 결과 패턴으로 선택 금지 |
| learner | 기존 observational SCM 적합을 자동 재사용하지 않음. randomized block 학습 절차 신설 여부 결정 | static SCM vs sequential/dynamic response 모델을 별도 비교·승인 |
| action set | 데이터 지원 grid 교집합 | split 이후 block-level support와 허용 precision 기준 사전 고정 |
| train/eval | 시간순 또는 block-aware split, 동일 block 혼합 금지, 필요 시 temporal gap buffer | 공개 benchmark reuse임을 선언; 세션 independent holdout으로 부르지 않음 |
| estimand | 명령배정 ITT / 시간창 평균 response. 실 physical actuation 또는 steady-state 효과와 구분 | 명령과 측정 시간의 추가 로그, carryover 가정 |
| G0/error burden | 여러 오류 부담을 쓰려면 reference-relative pair universe에 대해 사전 고정 | q/r, 오류 수, DAG 거절 및 seed 실패 처리, 예산 의미 |
| 비교기 | S0 vs Full Greedy 후보; M4 secondary; graph-free arm mean 필수 검토 | 같은 split/action/target/eval, information set 명시 |
| 분석단위 | assignment blocks within one archived experiment, temporal dependence explicit | independent device/session 미확인; population inference 불가 |
| 불확실성 | paired policy loss contrast, serial-dependence/randomization-valid inference 가능성 | 분산/효과크기 정보와 허용 CI 폭 사전 선언 후 표본정밀도 계획 |
| leakage | action recommendation은 train only; 평가 response는 봉인 | 접근 제어, split manifest, evaluator test |

자료가 주는 arm당 12–24 full-archive blocks인 예시 grid는 split 뒤 표본을 보장하지 않는다. 최소 표본을 임의로 정하지 않는다. 과학적으로 허용할 효과크기/정밀도와 block 간 의존성 정보를 먼저 요구하고, 현재 archive가 충족하지 못하면 새 독립 수집 또는 기술 사례로 중단한다.

가능한 성과 수준은 단일 archive의 조건부 재분석/기술사례다. graph seed와 정책 수를 독립 물리 반복으로 집계하지 않는다. 결과가 반대이거나 graph-free baseline이 우수한 경우 그대로 보고한다.

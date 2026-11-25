# Research D 후속 설계 옵션

## 1. Mk2 조건부 실측 비교

장치·설정·정해진 시간창에서 이해되는 단일 실측 비교가 최우선 제안이다. `green` 명령에서 `current_led_2_uv` [A]까지의 매개경로, 고정 수준 공통 A, 학습 전용 목표/scale을 사전 지정한다. 정책 입력은 승인된 참조의 구조정보와 공통 train rows이며, 평가 응답은 추천 목록·그래프·코드 해시가 고정된 후에만 접근한다. 행동 지원 통계와 시간/결측 metadata는 평가 관리자가 결과값과 분리해 제공한다. 가능하면 동일 설정의 별도 세션을 평가에 확보한다. 같은 파일을 분할하는 경우 5,500행 배치를 통째로 분리하고 경계 인접성·carryover를 평가한다. 공개 자료의 outcome provenance와 기존 발표 노출은 별도로 확인한다.

### 평가 대상

조건 (c)와 사전 지정한 평가 시점에서 (mu_c(a)=E[Y\mid do(\text{command}=a),c]). Research C와 같은 형식은 (L_c(a)=(mu_c(a)-y_c^*)^2/s_{c,train}^2)다. 분모 없이 보고하면 단위는 A²이며 표준화 손실은 무차원이다. 이 손실은 평균 추종 오차를 평가한다. (E[(Y-y_c^*)^2]/s^2)는 분산 페널티가 포함된 별도 설계다. 조건·과제별 평균을 합치려면 동일 단위의 물리 목표와 사전 지정 가중치 또는 training-only scale이 필요하다.

선택 행동은 고정하고, 각 수준을 지원하는 실제 배정에서 시간창의 응답을 집계한다. 같은 명령을 한 번 설정한 100 readings라면 블록 평균 한 개를 쓴다. Mk2에서는 각 배치 안의 무작위 명령 기록을 사용하되 시간·이전 명령에 따른 전달효과와 측정 상관을 다룬다. 명령–상태 불일치가 남으면 명령 배정의 intention-to-treat estimand와 실제 actuation 효과를 구분한다. 미지원 수준은 외삽하지 않는다. 연속 반응 모델을 사용하면 함수 형태·smoothness·overlap·검증 오차와 uncertainty를 별도 명시하고 유형 3으로 기록한다.

`R_exp(a)=L_exp(a)−min_A L_exp`. 동일 과제·A에서 `R_exp(a_S0)−R_exp(a_Full)=L_exp(a_S0)−L_exp(a_Full)`이므로 공통 최소항이 정확히 상쇄된다. B=2 대비를 참조 사례의 1차 후보로 제안한다. 두 정책이 같은 행동을 고른다면 차이는 정확히 0이다. M4는 비교표에 둘 수 있는 secondary이며, Full Greedy와 M4가 악화하거나 정체해도 유효한 관찰이다.

두 정책 차이에서도 제곱 평균의 plug-in 편향은 남는다. 독립 또는 설계상 대조 가능한 split 평균으로 `(mean1−target)(mean2−target)/s²`를 계산하거나, 검증된 분산 추정으로 `[(mean−target)²−VarHat(mean)]/s²`를 쓸 수 있다. 배치 상관 또는 비정상성에서 split 독립 가정을 검토하고 적격하지 않으면 그 가정을 사용하지 않는다. 정책 비교는 같은 블록/arm 자료를 공유하고 공동으로 분산을 계산한다.

절대 Regret의 plug-in minimum은 최솟값 선택 편향과 near-tie 불안정성을 포함한다. 모든 (L_c(a))에 대한 사전 지정 동시 구간을 통해 regret 범위를 보고하거나, 분리 표본의 최적 후보 선택과 또 다른 평가를 통해 선택된 comparator와의 차이를 추정한다. 선택된 comparator는 표본오차가 있는 추정 최적 행동이다. A가 커질수록 안정적 arm 비교에 더 많은 배치가 필요하다. 절대 Regret 자료가 부족해도 유형 2의 해석은 가능할 수 있다.

### 불확실성과 분석 단위

물리 시스템 → 장치/구성 → 독립 session/run → 무작위 배정 및 그 안의 반복 측정 순으로 계층을 기록한다. 과제, G0 seed, 정책과 예산은 층 내 반복이다. 같은 개입 결과표를 재사용한 seed 차이는 서로 종속한다. 독립 평가 세션이 충분하면 세션 cluster를 함께 재표집하고, 각 세션의 응답표를 모든 정책·seed에 공유한다. 한 장치의 연속 기록만 허용되면 설계 기반 무작위화 또는 time-block uncertainty를 명시한 조건부 기술 사례로 보고한다. 단일 장치에서 얻은 B=2 차이로 장치 모집단이나 제조라인 모집단의 paired-t CI를 제공할 수 없다. 사전에 의미 있는 손실 차이·정밀도와 최소 arm별 독립 블록 수를 정하고 증빙이 부족하면 확증을 중단한다.

## 2. 비교 설계와 변경 범위

| 옵션 | 보존·변경 | 해석과 진입 조건 |
|---|---|---|
| Mk2 controlled error injection + linear Ridge | 정책/지표/Rule A/UNRES를 보존하고 데이터·행동·평가를 바꾼다. 상수 컨텍스트, 측정 alias, 시간 adapter를 별도 승인한다. | 구조 가설과 선형 추천 규칙의 외부 스트레스 테스트. 90노드에서 고정 q/r·B의 수리 기회를 구조에서 먼저 확인한다. |
| Mk2 nonlinear 또는 동적 learner | saturation, clamped LED, 양자화와 시차에 맞는 모델을 사전 지정한다. outcome-blind 구조 정책과 동일 A는 유지 가능. | learner까지 바뀐 확장. 동일 실측 평가에서 양 모델을 사전 지정 쌍으로만 비교한다. |
| Mk2 discovered G0 | 관측 training에서 PC-stable(CPDAG/UNRES), BOSS(DAG), DirectLiNGAM(선형·비가우시안 가정)을 검토한다. 조건화된 상수·결정론적 alias와 autocorrelation 가정을 선검토한다. GT 방향으로 임의 보완하지 않는다. DAG 부분과 UNRES를 명시하고, latent ADMG/PAG는 현재 엔진과 별도 계약으로 보낸다. | 실제 discovery 오류 분포. 수리에는 여전히 reference를 이용하므로 배포 자동 수리의 검증 범위 밖이다. 이번에는 알고리즘을 실행하지 않았다. |
| Mk1 direct-task 변경 | WT intake fixed grid 또는 LT binary arms. strict eligibility를 새로 정의한다. | 직접 효과의 별도 실측 사례. Research C strict 질문의 반복으로 취급할 수 없다. |
| 반합성/구조 대안 | causalAssembly 예제의 정책 변환 또는 ESS subsystem 구조 진단. | 제한된 유형 3–4. CausalMan/TEP는 기존 차단 근거가 해소되기 전 보류한다. |

상수 노드는 scale 계산을 깨뜨린다. 맥락 상수로 고정한 구조방정식, 동일 변수집합의 학습 가능성 또는 정당한 projection 중 하나를 별도 승인한다. raw/보정 채널이 같은 물리량을 중복 표현할 때 한쪽을 제외할 수 있는 기준은 측정 모델에 근거해야 한다. 후보 선택 뒤에 경로와 특성을 바꾸면 estimand가 달라진다. 그래프 복잡도와 운영 정책의 성공층을 공개하고 실패를 0 regret으로 대체하지 않는다.

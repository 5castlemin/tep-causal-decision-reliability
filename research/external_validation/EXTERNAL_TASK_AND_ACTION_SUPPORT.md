# 외부 과제와 실측 행동 지원

## Light Tunnel Mk2 linked_leds

공식 Figure 1의 묶음 노드를 펼치고 식 (1)·(2)의 slope/intercept 입력을 연결한 감사용 전사본은 90노드·142간선 DAG이며 최대 유향 경로 길이는 5다. 104열 모두를 그래프 변수로 삼으면 안 된다. 전사 90노드는 네 CSV에 모두 있고, 나머지는 4개 기록 필드와 10개 진단·고정 제어 컬럼이다. 제조사 그림은 알려진 효과를 문서화하고 비간선과 숨은 공통원인의 한계를 명시한다. 이 전사는 두 번째 검토자가 재현하고 비간선 범위를 심사할 대상이다. [공식 설정 PDF, 9쪽](https://cchamber-box.s3.eu-central-2.amazonaws.com/config_doc_lt_mk2_linked_leds.pdf) · [전사와 매핑](inspection_results.json)

| 조작 후보 X | 목표 Y와 경로 | 평가 지원 |
|---|---|---|
| `green`, LED 명령 정수 | `current_led_2_uv` [A], `green → ir_1 → led_2_uv → current_led_2_uv`. Figure 1에서 직접 edge 없음 | 제1 과제 제안. 명령값은 광출력의 실측값과 구별. `ir_1`은 측정 매개변수, `led_2_uv`는 clamped controller 입력, Y는 보정 전류 계측. |
| `green` | `current_led_3_uv` [A], `green → ir_2 → led_3_uv → current_led_3_uv`과 `ir_1 → led_2_uv → ir_2` 경유 경로 | 감사를 통해 확인한 대안. 같은 물리 장치·입력·배치의 결과이며 독립 과제가 아님. |
| `green` | `ir_2` 또는 `ir_3` | 그림에 직접 edge가 있어 strict 제외. 같은 raw/calibrated 전류 컬럼도 독립 endpoint로 세지 않는다. |
| `slope_f2` | `slope_f2 → led_2_uv → current_led_2_uv` | 조작 가능하나 제공 파일에서는 약 0.0624 고정. 동일 환경 다중 arm 없음. |

`exp_1_low_noise`와 `exp_2_noisy`마다 110,000행, green 지원 118수준(2–126)이다. 생성기는 동일 seed의 반올림·절단 정규분포 배정, 5,500행 × 20번과 배치 사이 1초 대기를 정의한다. CSV의 19개 경계 간격은 약 1.19–1.24초다. 두 실험에서 각 수준의 행 수가 일치한다. `sps_current_ls`가 4와 7인 별도 계측 조건이고 두 실험의 독립성 및 장치 식별자는 미확인이다. 배치가 동일 장치에서 연속 채집됐을 수 있다. Noise 파일 2개는 각각 5,000행, `green=0`만 지원한다. 네 파일 모두 `flag` 한 그룹과 `intervention=0`이다. 배정 및 관측 기준분포는 공식 생성기로 해석한다. 내부 파일에는 별도 학습/평가 플래그가 없다. [공식 데이터·생성기](https://github.com/juangamella/causal-chamber/tree/c2b307036446b8d3ca173e9f41ff465b7111819a/datasets/lt_spice_v1) · [논문](https://arxiv.org/abs/2604.09135) · [직접 검사](inspection_results.json)

| `green` 명령 예시 | low-noise 행 | noisy 행 | 나타난 배치 수(파일별) |
|---:|---:|---:|---:|
| 30 | 410 | 410 | 20/20 |
| 45 | 1,656 | 1,656 | 20/20 |
| 60 | 3,035 | 3,035 | 20/20 |
| 75 | 1,802 | 1,802 | 20/20 |
| 90 | 418 | 418 | 20/20 |

이 집합은 반응값을 보지 않고 support로 확인한 예시다. 각 110,000행 파일에서 timestamp는 단조 증가하며 고유하지만 counter는 100,001개만 고유하므로 counter 단독으로 행이나 run을 Join할 수 없다. 정책 공통 A로 잠그기 전에 배치 분할 뒤 지원, 실제 배정 파일 및 명령 열 대조, 기록 지연, 하드웨어 포화와 carryover를 확인한다. `led_2_uv`와 `led_3_uv`의 시간 정렬을 공식 프로토콜/펌웨어로 확인한다. 배정 이전에 고정된 센서·보정 조건과 초기 상태는 통제하고, 매개변수에 조건화하여 green의 총 효과를 지우지 않는다. 랜덤 green이 잠재 주변광과 독립이라는 주장과 Ridge DAG의 causal sufficiency는 별개다. [설정 PDF, 식 (1)·(2)와 Figure 1](https://cchamber-box.s3.eu-central-2.amazonaws.com/config_doc_lt_mk2_linked_leds.pdf)

## Mk1의 직접 경로와 행동 지원

| 설정 / CSV | 가능한 직접 검증 | 확인한 배정과 시간 | C 이전 |
|---|---|---|---|
| LT standard / `uniform_reference`, `uniform_red_mid`, `uniform_red_strong` | `red → current` 또는 `red → vis_1` | reference 10,000행, mid/strong 각각 1,000행. 공식 red 균등 정수 범위 0–85, 86–170, 171–255. 다른 조작은 동일 분포에서 새로 추출. 연속 세션 효과와 범위 이동을 분리해야 함. | reference는 논문의 observational 기준분포. 실험 간 fixed arm처럼 합치지 않는다. |
| LT standard / `validate_pol_1` | `pol_1 → vis_3` 또는 `pol_1 → angle_1` | 명령 0° 21행, 90° 29행, T=0 ms. 무작위 대기 후 배정. 각도 센서와 명령을 분리. | K=2와 direct task 변경 필요. `angle_1`을 넣어 공식 `pol_1→vis_3`를 삭제할 근거 없음. |
| LT standard / `lt_malus_v1` | `pol_1, pol_2 → vis_3` | 12×1,000행. 광원 조건별 파일에서 두 편광기를 랜덤 회전. 각도 명령 기록 양자화, 다른 편광기 및 광원 조건 보존. | 2개 입력·직접 경로, Malus 비선형·상호작용. 단일 입력 평균 효과는 context 고정·표준화가 필요. |
| WT standard / `validate_load_in` | `load_in → rpm_in` | 0.01과 1.00 각 25행, T=10초. 기록 float32 표현은 0.009999999776…처럼 다름. `validate_load_out`은 계획 50행 중 49행(23/26). | `rpm_in`은 실측 반응, fan load는 명령. direct, T·배경 load가 다른 파일 결합 금지. |
| WT standard / `random_loads_intake` | `load_in → pressure_intake` 또는 `rpm_in` | 0.01 격자 101수준, 2,000 random blocks, `load_out≈0.1`, hatch 0, 명령 후 8초, block당 100 readings. 예시 0.10/0.30/0.50/0.70/0.90의 블록 수 24/23/20/12/18. | 풍압 단위 Pa 또는 rpm으로 손실 제안 가능. `random_loads_both`는 두 부하 공동 조작이며 같은 다섯 수준 배정 수를 별도 독립 반복으로 합산할 수 없음. |
| WT pressure-control / `hatch_0`, `validate_pressure_downwind_loads` | PID 하의 단일 검증으로 활용 가능 | hatch 0 고정 10,000행. 검증은 센서값 override 명령 93,000/95,000 Pa 22/28행, T=0. PID 내부 기록 8열 추가. | 센서 override를 물리 압력 actuator로 바꾸지 않는다. 두 feedback cycle, C DAG 불가. |

Mk1 WT standard의 random walks는 시간 의존적이며 baseline seed 같은 이름이 session ID를 확증하지 않는다. 예를 들어 `actuators_random_walk_1`은 1,016행인 별도 이름이며 문서에서 설명하는 `actuators_random_walk_seed_*` 10회와 구분한다. 표준 WT의 물리적 rpm·기류 매개 과정은 실재할 수 있으나 공식 DAG의 graph path는 길이 1이다. 새 rpm→pressure 참조를 도입하기 전 독립 근거와 같은 시간·변수 정의가 필요하다. LT의 회전 명령과 별도 측정 각도도 같은 노드가 아니다. [Chamber 카탈로그](https://github.com/juangamella/causal-chamber/tree/c2b307036446b8d3ca173e9f41ff465b7111819a) · [부록 V](https://arxiv.org/html/2404.11341v2#A5) · [명령·시간·배정 수 전체](inspection_results.json)

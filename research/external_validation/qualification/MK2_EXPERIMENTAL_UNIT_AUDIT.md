# Mk2 실험 단위 및 독립성 감사

## 관찰된 계층

| 계층 | 이번 자료에서 확인 가능한 수/상태 | 해석 |
|---|---|---|
| 물리 시스템 | Mk2 Light Tunnel 한 configuration family; 고유 장치 serial/개수 미공개 | 독립 시스템 모집단 단위로 셀 수 없음 |
| 장치 | 장치 식별자 미확인 | 여러 장치 여부 미확인 |
| configuration | `lt_mk2_linked_leds` v1.0 하나 | 고정된 설정 조건 사례 |
| experiment submission | noisy와 low-noise 각각 generator상 한 번 submit | 제출 id가 공개 CSV와 연결되지 않음; 장치 세션 독립성 미확인 |
| 배치 | 각 제출 내 5,500행 × 20 연속 추가; 블록 사이 1초 wait | 원 논문의 5,000 training+500 test × 20회와 길이가 맞으나 CSV에 split label 없음; 독립 세션이나 reset 아님 |
| 명령 배정 | 각 제출 110,000행, green 순서 동일 | 행별 순차 무작위 명령. 명령 assignment unit과 결과 독립 단위는 다름 |
| 센서 기록 | timestamp 증가, counter 중복값 포함 | time series 행을 독립 표본으로 처리 불가 |
| 과제 | 사후 선택 금지; 제안 green→current_led_2_uv는 미확정 | 하나의 과제도 모집단 반복 수를 늘리지 않음 |
| G0 seed | Step 1에서 생성하지 않음 | 이후 graph seed도 독립 물리 반복이 아님 |
| 정책/예산 | Step 1에서 실행하지 않음 | 정책×예산 셀은 동일 응답자료 재사용 시 독립 단위 아님 |

## 공통 순서 및 환경

저장소 Step 0 검사에서 noisy/low-noise green 배정 순서는 완전히 같다. CSV metadata에서 `sps_current_ls`는 low-noise 4, noisy 7로 일정하며, 원 논문은 이를 light-source raw-current ADC data rate 차이로 설명한다. 원 논문은 낮은 값에서 더 많은 reading을 결합해 proxy noise를 낮춘다고 한다. 이 이름은 전체 광센서 시스템의 모든 noise를 무작위화했다는 뜻이 아니다. 설정간 차이가 ADC 조건 외에 장치·날짜·재보정·초기 상태까지 통제됐는지 공개 CSV만으로 확인할 수 없다. batch 사이 reset이 generator에 명시되어 있지 않으며 1초 protocol wait만 있다. 중단·재개 이력, calibration drift, ambient light/temperature와 장치 상태 provenance도 미제공이다. 그러므로 두 파일을 독립 세션 또는 독립 장치 복제로 부르지 않는다.

원 논문은 20회 반복마다 5,000 training + 500 test sample로 causal-function estimator를 평가했다고 설명한다. generator의 20 × 5,500 데이터 생성은 그 설계와 맞지만 archive CSV에는 반복별 split label이나 세션 ID가 없고, 동일 command schedule이 두 ADC 조건에서 재사용된다. published estimator benchmark로부터 결과 문헌 노출이 있으므로 이 데이터를 새 평가자료로 쓰면 미열람 holdout이 아니라 공개 benchmark 재사용/재분석이다.

## 추론 가능 범위

- **A 확증 평가:** 불가. 독립 장치/세션 ID와 충분한 독립 복제 자료가 확인되지 않았다.
- **B 무작위화 기반 장치 내 조건부 평가:** 배정 순서 복원 가능성은 있지만 serial dependence, carryover, 반복 schedule 공유와 session provenance 미확인 때문에 현재 정당화되지 않는다. 추가 로그/설계 근거가 있으면 조건부 재검토 가능.
- **C 기술적 사례:** 가능. 원본 기록에서 명령 범위·프로토콜·데이터품질을 설명하는 단일 장치/설정 사례. 이를 정책 효과 확증으로 부르지 않는다.
- **D 유효한 개입효과 평가 불가:** 물리 actuation과 행별 결과 정렬까지 확인되지 않으면 정책 성능 추론은 이 결론으로 내려간다.

무작위화 기반 추론은 실제 배정 메커니즘, 분석 단위, 잠재 결과가 배정에 의해 교환 가능하다는 조건, carryover를 포함하는 treatment regime 정의를 요구한다. Serial-dependence robust 추론은 사전 지정된 시간 의존 구조/의존 범위와 충분한 시간 구간을 요구하며, 20개 배치를 독립 cluster로 선언하는 것만으로는 충족되지 않는다. 고정 장치 기술 분석은 유한 관측 구간 내 배정-응답 연관을 설명할 수 있지만 다른 run/device/configuration으로 일반화하지 못한다.

다른 200개 G0 변형에 같은 반응표를 재사용한다면 구조 알고리즘의 조건부 민감도 실험이지 200개 물리 실험이 아니다. 이 audit은 정책별 결과를 계산하지 않았다.

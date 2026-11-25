# Mk2 참조 그래프 적격성 검토

상태: Step 1 구조 감사. 외부 평가, 과제 채택, 본실험 승인 아님.

## 근거와 재전사 범위

기준 문서는 [Mk2 linked_leds 설정 v1.0](https://cchamber-box.s3.eu-central-2.amazonaws.com/config_doc_lt_mk2_linked_leds.pdf), 특히 변수표, 식 (1)–(2), Figure 1이다. 원본 PDF를 별도 페이지로 렌더링해 Figure 1, 약어 표기와 controller 수식을 읽었다. 그러나 Step 0 전사본을 이미 알고 있으므로 blind transcription이 아니며, 90개 노드와 142개 모든 방향 간선을 별도 파일로 처음부터 독립 전사해 diff한 검증은 수행하지 못했다. 아래 aggregate counts와 candidate path는 기존 machine-readable transcription을 기준으로 보고하고, PDF 두 번째 육안 검토는 이 과제/식 및 전반적 도식 일관성 수준으로 제한한다. 이를 독립 전문가 검증 또는 전체 edge-set 검증으로 부르지 않는다. 설정 문서는 제어 메커니즘과 알려진 효과를 기술하지만 완전성이나 모든 비간선의 부재를 보증하지 않는다.

## 비교 결과

| 항목 | Step 0 전사 | 재전사/판정 |
|---|---:|---|
| 변수 노드 | 90 | 90; 이름 집합 일치 |
| 방향 간선 | 142 | 142; 식에서 유도한 `ir_1→led_2_uv`, `ir_2→led_3_uv` 포함 |
| DAG | 예 | 예; 순환 없음 |
| 노드/간선 불일치 | — | 전체 set diff 미수행. candidate path/controller 방향과 표기상 모순은 두 번째 육안 검토에서 발견 못했으나 전체 일치 판정은 미확인 |

도식 묶음은 광원별 센서 영향과 채널별 raw/calibrated 측정, 설정/진단 변수로 풀었다. 제안 후보의 `green`은 settable 밝기 명령 `{0,…,255}`이며 실제 광출력량을 측정한 값은 아니다. `ir_1`은 첫 IR 센서의 uncalibrated intensity measurement `{0,…,65535}`이고 settable action이 아니다. `led_2_uv`는 독립 명령처럼 보일 수 있지만 식 (1)의 `clamp(0.0624×ir_1+intercept_f2)` linked controller 출력이다. `current_led_2_uv`는 UV LED 전류를 A 단위로 읽는 calibrated sensor measurement이며 `_raw`는 raw ADC output이다. 따라서 Y는 광량/품질 자체가 아니고, 전류가 의사결정 손실에서 의미 있는 목표인지는 별도 근거가 필요하다. 문서는 LED가 센서 측정 중에만 켜져 다른 광센서 측정에 미치는 효과를 제거한다고 서술한다. 이는 설정된 configuration의 물리 주장이지 모든 조건에서 비간선이 없다는 증명은 아니다. 모터 enable/steps/max는 정확한 위치를 위해 고정된다.

후보 경로는 `green → ir_1 → led_2_uv → current_led_2_uv`이다. 참조 도식에는 이 경로의 세 방향 간선이 있다. 문서상 누락된 `green→current_led_2_uv` 직접 간선은 **REFERENCE_ABSENT_BUT_UNVERIFIED**로 분류한다. 직접효과 부재도 총효과 부재도 입증되지 않았다. 따라서 현재 strict indirect-only task에서 요구하는 직접 간선 부재 조건은 과학적으로 보증되지 않는다.

## 비간선 분류 및 오류 호환성

간선은 `SUPPORTED_DIRECT_EDGE`로 다룰 수 있는 설정 수준의 positive evidence다. 음성쌍은 문서의 명시적 부재 근거가 개별 pair에 연결될 때만 `SUPPORTED_NO_DIRECT_EDGE`가 될 수 있다. 나머지는 `REFERENCE_ABSENT_BUT_UNVERIFIED`; 문서의 표현이 복수 해석을 허용하면 `AMBIGUOUS_OR_UNRESOLVED`; 고정 메타데이터/진단 변수처럼 의사결정 구조에서 제외되는 쌍은 `OUT_OF_SCOPE`다. 이 audit은 4,005개 비인접 쌍을 일괄 true negative로 만들지 않는다. 세 Rule A chord도 명시적 부재의 과학적 근거가 없어 미확인이다.

| 오류 | 완전 DAG 계약 A | 제한 부분 참조 계약 B | reference-relative 계약 C |
|---|---|---|---|
| FN | 전체 간선에서 계산 | 확인된 positive pair에 한함 | 도식 누락은 참조 기준 누락으로만 표시 |
| FP | 확인된 모든 비간선 필요 | 확인된 negative pair에서만 계산 | 도식에 없는 추가 간선; 실제 FP라 단정 불가 |
| REV | 반대 방향과 참 방향 모두 알려져야 함 | 방향이 확인된 positive pair에서만 | 도식 대비 역방향 불일치 |
| UNRES | Research C 정의 그대로 가능 | 미확인 pair 분모와 abstain 규칙 재설계 | 도식상 미상인 방향/간선으로 새 해석 필요 |

Research C M1–M4를 같은 이름으로 구현할 수는 있어도 B 또는 C에서는 분모, 후보쌍, 오류 라벨과 점수 의미가 달라진다. 실제 적용 가능성만으로 C를 GT DAG라고 간주해서는 안 된다. A는 현 증거로 부적격, B는 pair별 과학적 증빙과 새 계약 필요, C는 reference-relative 재현이지만 완전 GT 외부 검증이 아니다. 어느 안도 이번 감사에서 채택하지 않는다.

## 출처

- [설정 PDF](https://cchamber-box.s3.eu-central-2.amazonaws.com/config_doc_lt_mk2_linked_leds.pdf), v1.0, Figure 1, 변수표, 식 (1)–(2), causal ground truth 절.
- [Causal Chamber 논문](https://www.nature.com/articles/s42256-024-00964-x).
- 기계 판독 Step 0 그래프/검사: `../inspection_results.json`, 그래프 이름 `mk2_figure_transcription`; 원본 데이터 SHA 및 catalog revision: `../dataset_manifest.json`.

**판정:** Step 0 그래프는 configuration의 효과 도식에 대한 기존 전사다. Step 1의 독립 전체 재전사는 미완료이며, 따라서 완전한 인과 GT와 strict indirect-only negative-pair oracle로 검증되지 않았다. 독립 전사 또는 저자/장치 전문가 확인은 후속 진입 조건이다.

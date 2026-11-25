# Mk2 상수 노드 및 projection 대안

## 실제 파일 상수 검사 재사용

Step 0 검사 파일은 주요 파일별 104개 CSV 컬럼 중 상수 컬럼 67개를 보고한다. 상수 컬럼과 90개 참조 노드를 교차한 결과 상수 reference node는 **59/90**, 가변 reference node는 **31/90**이다. 상수 CSV 컬럼 중 8개는 graph node가 아니다. 이는 원자료의 값 손실이나 그래프 불필요성을 뜻하지 않는다. `inspection_results.json`은 파일별 상세 상수명과 dtype/열 통계를 담는다. 이번에는 반응값으로 노드를 추려내지 않았다.

| 분류 | 근거/예 | 처리 시 주의 |
|---|---|---|
| 기록 metadata | `timestamp`, `counter`, `flag`, `intervention` | graph 노드와 분석 공변량을 구분; 기록 의미를 graph causal variable로 오인 금지 |
| 설정/제어 입력 | `slope_f2`, `intercept_f2`, 모터 enable/steps/max 등 파일에서 고정된 설정 | 현재 configuration context; 상수여도 관계식의 의미와 참조 DAG에서 삭제 불가 |
| 센서 설정 | offsets, samples-per-second, resolution 관련 변수 | calibration/measurement mechanism일 수 있어 단순 상수 삭제 금지 |
| 고정 물리 상태 | 현재 configuration에서 변화가 없는 polarizer/controller 상태 후보 | 실제 고정 장치 상태인지 공개 자료만으로 판정 불가 |
| raw/calibrated 쌍 | `*_raw`와 calibrated measurement, digital/raw angle 등 | 수치가 같거나 다른지만으로 중복채널 판정 불가. calibration 관계가 측정모형 의미를 바꿈 |
| 잠재 매개/교란 | 도식의 광원, 센서, controller 및 고정 설정 | 관측 상수라도 제한된 환경에서만 불변일 수 있고 다른 설정에선 변함 |

상수인 전체 CSV 열 67개, 그중 graph node인 59개, 상수 비노드 열 8개는 서로 다른 수다. 구체 이름 목록과 재현 가능한 정량 통계는 `../inspection_results.json`의 `chamber.lt_spice_v1.experiments.exp_1_low_noise.constant_columns`와 `mk2_figure_transcription.nodes`를 교차해 확인한다. 두 주요 110,000행 파일에서 교집합 수는 동일하다.

## 처리 대안

**A. Context로 고정 설정 보존.** 모든 정책에 같은 90-node reference와 같은 104-column input schema를 유지한다. 상수 변수는 learner에서 계수 적합이 안 될 수 있음을 기록하고, 고정 context/known mechanism으로 명시한다. 외부 설정으로 일반화하지 않는다. 정책별 노드별 결측/제외는 허용하지 않는다.

**B. 명확한 중복/불필요 채널 제외.** 물리 정의·장치 처리 순서·중복 측정 증거가 확인된 경우에만 일괄 제거한다. `raw`/calibrated는 단순 이름 유사성만으로 중복 처리하지 않는다. 동일 분석 집합을 모든 정책에 적용한다.

**C. 정당화된 제한 구조.** 제거 집합이 매개나 공통원인을 포함하면 단순 induced subgraph는 잘못된 causal graph일 수 있다. latent projection으로 숨긴 경로의 새 directed edge 또는 공통원인의 bidirected 관계(ADMG)를 반영해야 한다. 문서에서 음성쌍을 입증할 수 없으면 strict indirect-only 과제를 유지하지 않는다. projection의 그래프 클래스가 DAG에서 ADMG로 바뀌면 Research C DAG 전용 오류 정의/정책 호환성을 새 계약으로 검토한다.

경로 `green→ir_1→led_2_uv→current_led_2_uv`에서 `ir_1` 또는 `led_2_uv` 제거 시 매개경로가 축약되어 direct edge/latent relation 해석이 달라진다. 제외 변수가 공통원인인 경우 conditioning과 marginalization은 서로 대체할 수 없다. 실제 SCM 적합 및 변수 집합 선택은 수행하지 않았고, 결과값으로 변수를 삭제하지 않았다.

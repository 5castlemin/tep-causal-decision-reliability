# Mk2 명령–계측 시간 정렬 감사

상태: 메타데이터/프로토콜 구조 검사만 수행. Y 또는 매개변수 반응값, 평균, 효과, 손실 및 정책 추천은 읽거나 계산하지 않았다.

## 명령 생성과 파일 정렬

공식 generator [spice.py at pinned catalog commit](https://github.com/juangamella/causal-chamber/blob/c2b307036446b8d3ca173e9f41ff465b7111819a/datasets/lt_spice_v1/generators/spice.py)는 numpy RNG seed `23432`로 green 명령을 생성하고, noisy/low-noise experiment를 각각 구성한다. 각 행에서 green과 `sps_current_ls`, `offset_current_ls`, `slope_f2`를 입력으로 지정한다. 각 experiment에는 5,500행 입력 dataframe을 20회 `from_df`로 추가하고 각 블록 후 1초 대기한 다음 **experiment를 한 번 제출**한다. 생성기는 noisy와 low-noise에 동일한 green 명령열을 재사용한다. Step 0에서 기록한 CSV와 생성 규칙 간 대조 결과는 각 파일에서 110,000/110,000 green 명령 순서 일치, 두 조건의 전체 순서 일치였다. 이는 CSV의 기록 컬럼이 배정 의도와 행 단위로 일치함을 보이지만 실제 물리 광출력/성공 actuation을 입증하지 않는다.

SDK 소스 `causalchamber/lab/chamber.py`의 `Batch.from_df`는 각 dataframe row마다 각 입력 열에 SET 명령을 만들고 이어 MSR을 발행한다. 공식 변수표의 `intervention`은 SET 지시 뒤 첫 측정에 1이라고 정의되지만 이 archive의 110,000행 모두 0이다. 따라서 해당 열은 CSV에서 SET 이벤트의 행별 표식으로 사용할 수 없으며 기록 의미와 generator schedule 사이에 미해결 차이가 있다. `Protocol.submit`은 하나의 experiment id를 반환한다. 공개 CSV에는 그 id 및 20개 클라이언트 배치 경계를 식별할 provenance가 없다. timestamp는 파일 내 유일·증가, counter는 100,001개의 유일값이며 9,999행에서 중복 counter 값이 있다. `flag=0`이다. median timestamp 간격은 약 0.18–0.19초이고 블록 경계에서 약 1.2초 간격이 나타난다.

원 논문 Appendix J에서 정의한 역할은 **green=confounder/광원 밝기 설정, ir_1=treatment(첫 센서 IR 계측), ir_2=outcome(둘째 센서 IR 계측), current_ls_raw=proxy**다. 논문의 `green` 조작은 confounder를 움직이는 입력이지 그 논문의 `ir_1→ir_2` treatment-effect estimand와 동일하지 않다. 현재 Audit에서 제안한 `green→current_led_2_uv`는 Research D를 위한 새 action/target task이고 SPICE paper 재현으로 부르면 안 된다. `ir_1`은 센서 계측변수라 장치 설정에서 직접 SET 가능한 action이라는 근거가 없다.

원 논문은 Experiment I/II에서 각각 5,000 training + 500 test × 20회를 보고하고, Appendix J에서 low-noise/noisy 조건의 `sps_current_ls`를 각각 4와 7로 지정한다. 이는 current-light-source raw proxy를 측정하는 ADC data rate 설정이며, 낮은 값에서 더 많은 reading을 결합해 noise를 줄인다고 설명한다. `offset_current_ls=2950`, `slope_f2=0.064`는 논문 표의 설정이다. 공개 generator/CSV는 `slope_f2≈0.0624`를 기록하므로 논문 텍스트 수치와 아카이브 구현 사이에 작은 설정 불일치가 있다. 이는 데이터 버전/실험 reproducibility를 구분할 사안이며 임의로 맞추지 않았다. generator의 각 5,500행 배치는 논문의 5,000+500 길이와 맞지만 CSV에 train/test 표식은 없다. 20개 배치 경계를 분할에 활용하는 것은 후속 사전 지정이 필요하며, 그것만으로 session reset이나 독립 반복을 입증하지 않는다.

## 실행 순서의 증거 한계

| 단계 | 확인 수준 |
|---|---|
| 명령 배정 | generator 및 seed에서 직접 확인 |
| protocol 내 각 행 SET 후 MSR 발행 | 공개 SDK 코드에서 직접 확인 |
| dataframe 입력 명령이 CSV `green`에 같은 순서로 기록 | 기존 검사에서 전체 순서 대조 확인 |
| 명령이 각 장치 채널에 물리적으로 적용된 시점/정확도 | 로그에 실 actuation telemetry가 없어 확인 불가 |
| IR 센서 측정과 controller 계산/LED 갱신의 내부 순서 | PDF에서 관계식은 확인되나 펌웨어의 한 행 내 원자적 순서는 미확인 |
| current 센서 취득 시점이 해당 행 직전 SET 뒤인지, 직전 명령 영향인지 | 확인 불가; CSV row 동시성 가정 금지 |
| 배치 사이 1초 wait | generator code에서 프로토콜 요청 확인; 장치 reset/settle 증거 아님 |

Green은 생성기 입력이며 light source의 물리 출력은 직접 기록된 처리변수가 아니다. `ir_1`은 센서 측정, `led_2_uv`는 PDF상 `clamp(0.0624 × ir_1 + intercept_f2)` controller 출력이다. `current_led_2_uv`는 광량 자체가 아닌 별도의 전류 계측 변수다. 명령 green이 실 actuation과 동일하다거나 같은 CSV 행의 모든 센서가 동시 측정됐다고 말할 수 없다.

원 논문 Appendix J에서 정의한 역할은 **green=confounder/광원 밝기 설정, ir_1=treatment(첫 센서 IR 계측), ir_2=outcome(둘째 센서 IR 계측), current_ls_raw=proxy**다. 논문의 `green` 조작은 confounder를 움직이는 입력이지 `ir_1→ir_2` treatment-effect estimand와 동일하지 않다. 현재 Step 0에서 제안된 `green→current_led_2_uv`는 Research D의 새 action/target task이고 SPICE paper 재현으로 부르면 안 된다. `ir_1`은 센서 계측변수라 직접 SET 가능한 action이라는 근거가 없다.

원 논문은 Experiment I/II에서 각각 5,000 training + 500 test × 20회를 보고하고, Appendix J에서 low-noise/noisy 조건의 `sps_current_ls`를 각각 4와 7로 지정한다. 이는 `current_ls_raw` proxy를 측정하는 ADC data rate 설정이며, 낮은 값에서 더 많은 reading을 결합해 noise를 줄인다고 설명한다. `offset_current_ls=2950`, `slope_f2=0.064`는 논문 표의 설정이다. 공개 generator/CSV는 `slope_f2≈0.0624`를 기록하므로 논문 텍스트 설정과 archive 구현 사이에 작은 차이가 있다. 이는 version/reproduction discrepancy로 남긴다. Generator의 각 5,500행 배치는 논문의 5,000+500 길이와 맞지만 CSV에는 split 표식이 없다. 20개 배치 경계를 분할에 활용하는 것은 후속 사전 지정이 필요하며, 그것만으로 session reset이나 독립 반복을 입증하지 않는다.

## 가능한 estimand

1. **배정 명령 ITT:** 무작위로 배정한 green setpoint 수준에 대한 결과. 실제 row alignment와 무작위화 구현이 확인되면 배정된 순차 명령 regime의 결과로 정의 가능. 그러나 serial/carryover를 반영한 regime 효과이며 독립행 평균이 아니다.
2. **물리 actuation 효과:** 실제 광출력/적용 green 값이 없으므로 현 CSV 단독으로는 식별 불가.
3. **현재 명령의 과거 상태 평균 효과:** lagged 상태/히스토리와 행 정렬이 불확실하여 이번 단계 근거로 식별 주장 불가.
4. **고정 green의 정상상태 제어 효과:** 무작위 매 행 변경 설계와 1초 블록 간격은 고정값 유지/settling을 보장하지 않는다. 식별 불가.

따라서 현 단계에서 지지되는 것은 명령열 audit 뿐이다. 행 수준 response 효과는 결과값을 본 진단, 확정된 시간창, carryover 처리, 독립 평가 계획이 선행되어야 한다. 공식 논문과 공개 benchmark의 outcome 관련 내용은 문헌 노출로 기록한다. 논문 Appendix J의 공개 결과표 일부가 검색 추출 출력에 함께 노출되었으며 과제/action 선택에 사용하지 않았다. 실제 원자료 outcome response를 이 Step에서 열어 요약하거나 정책별 성능을 계산하지 않았다. 그러므로 본 자료를 완전히 미열람된 external holdout이라 주장할 수 없다.

## 다음 진단 제안 (미승인)

추가 분류: archive는 무개입 관측자료가 아니라 행마다 입력을 SET한 sequential randomized-command experiment다. 이를 표준 관측 Causal Discovery와 같은 자료로 취급해 G0를 추정할 수 있다고 가정할 수 없다. 원자료의 `intervention` 열은 모두 0이라 관측과 개입을 구분하는 유효 표식도 제공하지 않는다.

원 저자/관리자의 장치 로그·펌웨어/응답 지연 설명을 먼저 확보한다. 그래도 lag/carryover 판단에 반응값이 필요하면, 별도 승인된 개발 진단 구간과 사전 지정 분석 코드/시간창을 사용하고 해당 파일은 이후 독립 평가에서 제외한다. 이 감사는 어떤 lag, window 또는 action을 결과에 맞춰 고르지 않았다.

출처: [SPICE 논문 PDF](https://arxiv.org/pdf/2604.09135), pinned generator 위 링크, 공개 package source `causalchamber/lab/chamber.py` (Step 0 package artifact), Mk2 설정 PDF, `../dataset_manifest.json`, `../inspection_results.json`.

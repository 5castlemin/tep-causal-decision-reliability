# Wind Tunnel Direct-task Feasibility

## 판정

`wt_bernoulli_v1 / random_loads_intake`는 물리 장치에서 무작위로 배정된 `load_in` 설정과 반복 계측을 제공한다. 다만 제안한 두 과제는 모두 공식 `wt_standard` 도식의 **직접 간선**이다. 따라서 strict indirect-only 과제가 아니며, 이 기록으로 평가할 수 있는 것은 문서화된 명령 배정에 대한 조건부 응답 관계다. 실제 actuation, 정상상태 또는 독립 장치 모집단의 효과는 확인되지 않았다.

## 변수와 운영 해석

공식 [variables.csv](https://github.com/juangamella/causal-chamber/blob/c2b307036446b8d3ca173e9f41ff465b7111819a/datasets/wt_bernoulli_v1/variables.csv)는 `load_in`, `rpm_in`, `pressure_intake`를 측정 변수 목록에 두고 각 설명을 원 논문 Appendix II로 연결한다. 공식 [generator](https://github.com/juangamella/causal-chamber/blob/c2b307036446b8d3ca173e9f41ff465b7111819a/datasets/wt_bernoulli_v1/generators/random_loads_intake.py)는 `load_in`을 0–1에서 draw해 0.01 단위로 기록하고 그 외 주요 외생 설정을 고정한다. 코드는 조작 명령을 직접 뒷받침하지만 variables.csv만으로 센서의 물리 단위와 제어 목적의 적절성을 확정하지 못한다. Dataset README는 이를 Bernoulli 원리 설명 및 symbolic regression(Fig. 6e) 자료로 소개하며 RPM/압력 setpoint 결정 과제로 제시하지 않는다.

| 후보 | 참조 관계 | 과제 의미 | 한계 |
|---|---|---|---|
| `load_in → rpm_in` | 직접 간선 | 팬/흡입 측 부하 설정에 따른 흡입측 회전수 계측. 회전수 setpoint 추종이라는 제어 손실 후보 | 문서에 운영상 목표 회전수, 허용편차 또는 안전/효율 기준이 없음. `rpm_in`의 값 단위를 변수 CSV 자체가 제공하지 않음 |
| `load_in → pressure_intake` | 직접 간선 | 부하 설정에 따른 흡입측 압력 계측. 압력 setpoint 추종 후보 | 목표 압력의 운영 의미, 변수 단위 및 직접-edge 외 경로의 완전성이 이 task 선정 근거로 확보되지 않음 |

두 Y 모두 측정 결과이지 조작 변수가 아니다. 손실이 작아진다 해도 실제 에너지 소비, 환기 품질, 안전 또는 산업 공정 개선으로 해석할 수 없다. 명령 설정 `load_in`과 실제 팬 부하가 같다는 telemetry도 없다.

## outcome-blind 구조 결과

핀된 standard graph는 32 node / 42 directed edge의 DAG다. 두 과제 모두 `load_in`에서 Y로 가는 유일한 reference 경로가 하나의 직접 간선이며, Research C `task_zone()`이 돌려주는 zone은 그 unordered pair 한 개뿐이다. Rule A task-zone FP opportunity는 0이다. 각 task에서 M4가 지원할 수 있는 task 오류는 사실상 해당 edge의 FN/REV/UNRES 한 건이고, FP component는 정의상 분모 0이다. `M1`–`M3`은 나머지 41개 reference edge 또는 주입 FP를 다루지만, 이들이 해당 direct outcome task의 수리 가치라는 해석은 별도 근거가 없다.

이는 측정 결과를 보지 않고 그래프와 원 정책 코드만으로 계산했다. 두 후보 중 유리한 결과를 골라 선택하지 않는다.

## 권고

이 direct task만으로 기존 M1–M4 수정 우선순위 연구를 외부 검증한다고 부르지 않는다. 기술적 물리 사례로서는 매력적이나, 기존 점수 간 비교가 task zone 하나와 task FP 0으로 지나치게 축소된다. 추가적으로 기존 observational SCM learner와 순차 무작위 SET 데이터의 역할도 다르다. 그러므로 이 과제는 Step 2에서 채택하지 않고, 새 task-zone 정의, 동적/배정 기반 learner 및 목표값 근거를 포함한 별도 계약 재설계가 있어야 재검토한다.

실제 결과값, action별 반응 평균, 방향 또는 손실은 이 검토에서 읽거나 계산하지 않았다.

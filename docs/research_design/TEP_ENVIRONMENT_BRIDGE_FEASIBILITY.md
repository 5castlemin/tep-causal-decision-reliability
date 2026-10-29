# TEP 환경 연결: 계약 구현과 실제 실행 가능성

기준일 2026-10-27. **권고 D — 원래 전체 구조 품질–의사결정 연구의 핵심 조건은 두 경로 모두 미충족.** Python 후보의 국소 기술 검산은 실행 가능하지만, 새 공식 연구환경이나 국소 연구로 전환하지 않았다. 기존 연구 질문·데이터·28간선·7개 graph·Step6·과거 실험은 보존했다.

## 1. 해결할 문제와 Git 기준

기존 CPCaD-Bench의 1499×31 정상 관측 자료에는 구조 채점용 참조가 있지만 같은 생성환경에서 실행한 개입 결과가 없다. 공개 Python TEP에서는 조작할 수 있지만 benchmark와 모델·제어기·관측 시계·집계·초기화가 같다는 증거가 없다. 한쪽의 frozen F1과 다른 쪽의 반응을 결합하면 환경 차이와 구조 오류를 분리할 수 없다.

시작 시 `git fetch origin`, GitHub의 PR 정보를 확인했다. main=`e960fa81cf8ef1ce097516c84f5fd724e592ac2e`, PR15=`e769ef5`, PR16=`d12c6be`, PR17=`a41683bd9a0a0bd568b5e40c4d6374b033eb424e` 모두 OPEN. 의존성 main→15→16→17 유지. 시작 작업 트리는 깨끗했고 새 `feature/tep-environment-bridge-feasibility`는 PR17 위에서 분기했다. 기존 PR을 병합하지 않았다.

## 2. 새로 구현한 계약과 그 한계

`src/environment_contract.py`는 모델 source/commit/hash, 제어기 설정·mode, 노드 순서·단위·종류, 상태/센서 시계, 적분/샘플링/집계, 참조 노드/직접·시차 의미/양성·음성·미확정 쌍, 명령/밸브/setpoint 조작, 초기화·잡음·학습/평가 구분·horizon을 비교한다. 각 section은 실제 근거 파일의 상대 경로·SHA256·VERIFIED 등급을 요구한다. 경로 탈출, 파일 부재, 해시 불일치, REPORTED/UNKNOWN은 거부한다.

새 진입점은 `environment_contract.require_environment_contract`다. 기존 ID/Boolean 함수는 고정 코드 hash를 사용하는 과거 실행의 재현을 위해 바이트 그대로 유지했다. 이 보고서에서 legacy 검사로 구분한다. 과거 실행기를 새로 실행하지 않았으며 기존 synthetic acceptance 결과의 의미도 소급 변경하지 않았다. 새 연구 join은 새 진입점을 사용해야 한다.

전체 직접 F1용 참조는 현재 구현에서 유한한 **동시점 방향쌍 전체**의 양성/음성 분할만 지원한다. 미확정·빠진 쌍·중복·노드 불일치·내부상태 참조와 센서 노드 불일치를 거부한다. 시차 참조는 유한 lag universe와 별도 평가 규약이 없으므로 명시적으로 미지원/거부한다. 이것이 시차 인과구조의 과학적 부정을 뜻하지 않는다.

15개 저장 계약 사례와 13개 단위 검사로 같은 이름의 controller·sampling·aggregation·조작·노드 순서 불일치, 부족한 음성쌍·내부상태 참조 오용·미검증 근거를 거부했다. 현재 CPCaD/Python join은 이름을 억지로 같게 해도 거부하며, Python 부분 참조를 자기 자신과 결합해도 전체 F1 연구 join은 거부한다. 실제 계약 원본/구조화 거부 사유는 `research_runs/tep_environment_bridge/contracts/`와 `CONTRACT_RESULTS.json`에 있다.

동일 합성 **schema 시험 fixture**는 메타데이터 검사만 통과한다. 새 합성 관측 데이터를 생성한 것이 아니다. `research_join_eligible_for_review`는 과학 검토에 제출할 기술적 자격이며 최종 승인 값이 아니다. 모든 결과의 `scientific_equivalence_proven`, `manufacturing_adopted`, `execution_authorized`는 false다. VERIFIED 파일이 존재한다는 사실은 그 파일의 과학적 주장까지 증명하지 않는다. 계약은 허위로 작성된 동일 metadata의 진실성을 판별할 수 없으며 외부 근거 검토를 대체하지 않는다. Boolean만으로 연구가 승인되는 경로를 새로 만들지 않았다.

## 3. 실제 실행: 작은 명령–밸브–센서 adapter

외부 checkout은 고정 commit `9a6c8e5fcef4a2850778704e7793c87b0a187005`, tracked 변경 없음, 기존 네 source hash 일치였다. source `.py` 14개 전체 hash도 `technical_v1/EXECUTION_IDENTITY.json`에 기록했다. 원 source를 수정·복사·재설치하지 않았다. 기존 실행 가능한 Python3.11.15/NumPy1.26.4를 사용했다. 이전 REF-B 기록의 NumPy2.4.6와 다른 환경이므로 과거 결과의 byte 재현이라고 부르지 않는다.

`src/tep_technical_adapter.py`와 `scripts/run_tep_environment_bridge.py`는 **같은 schema**에 초기 상태·센서41·명령12·제어기 기억·IDV·RNG, 명령/실제밸브/냉각수/에너지, 센서 평가 시각/적분 후 시각, 종료·유한값을 분리해 남긴다. 초기 fingerprint는 열거한 필드의 fingerprint이며 모든 backend cache 전체 동일성의 증명은 아니다.

결과를 보기 전에 `PLAN_v1.json`과 SHA를 저장했다. 이는 로컬 사전 고정이며 외부 사전등록은 아니다. seed465120799, Euler1초, IDV0, 기존 초기점, XMV10 +0.1pp, 6step을 유지했다. 수동/폐루프 각각 기준·조작·새 객체 반복을 실행해 **8실행×6step=48회 적분, 56개 시점 기록**을 얻었다. 큰 데이터 생성·Fault·graph 학습·SCM 적합은 하지 않았다.

| 실제 확인 | 결과와 해석 |
|---|---|
| 초기 반복 | mode 내 fresh baseline/action 초기 fingerprint 일치. 네 조건의 새 객체 반복 core가 정확히 일치 |
| 명령≠밸브 | t0 명령41.20581288%, 밸브41.10581288%. 수동 첫 적분 후 밸브41.12581288%. `v_next=v+(u−v)/5` 독립 검산 |
| 자동 제어 | 외부 명령41.20581288%가 첫 controller call 후41.20609998156198%로 갱신. **조작 효과가 완전히 취소됐다는 뜻이 아니다**. 직접 command와 setpoint 변경·지속 override는 다른 정책 |
| 관측 시계 | 첫 반환 상태는1초, cached 센서는0초 평가값. 매 step 차이1초. 물리적 전달 지연과 수치/기록 순서를 혼동하지 않음 |
| 잡음 | 두 mode의 baseline/action에서 RNG 호출 누적수·실제 draw sequence hash 일치. observer를 제거한 반복과 core exact 일치. 이6초/IDV0 조건에만 해당하며 다른 horizon/Fault/적응형 solver의 정렬 보장 아님 |
| 공정 반응 | 수동 마지막 Y9 차이 −0.000018438156772049297°C. 단일 짧은 경로의 구현 진단이며 평균 효과·유의성·정답 효과로 승격하지 않음 |
| 정상 관측 변동 | 수동 기준 XMV10 range=0. 조작 변수의 자연 변동/충분한 자극이 없으므로 이6초 기록을 인과발견용 학습 자료로 쓰지 않음 |
| 실패·범위 | 8실행 유한값 유지, shutdown/step 실패0. 물리 안전 범위 검증·장기 안정성·독립 효과 정밀도·Recovery/Safety는 NOT_RUN |

고정 원시 JSON, 변수/단위 schema, source/환경/계획 hash를 저장했다. 관측/학습/선택/미사용 평가 namespace를 실제로 생성한 것은 아니다. 이 이미 본 진단 기록은 향후 untouched holdout이 될 수 없다. 별도 effect 자료를 만들 경우 fresh 객체·분리 seed namespace·고정 정책·관측 시계·독립 반복 평균 또는 검증된 잡음 정렬을 먼저 정해야 한다.

## 4. 실제 검산: 왜 센서만으로 직접 구조를 만들 수 없는가

추가 `CLOSURE_PLAN_v1.json`을 먼저 저장/해시한 뒤 기존 REF-B와 같은 v10 ±0.001pp를 사용해 세 번 고정점 평가했다. rollout0, 명령 변경0, source 수정0이다. 새 전체 GT가 아니라 **관측 표현의 상태 충분성 반례**다.

초기 backend를 복제하여 명령12개와 외생/RNG 상태를 같게 두고 실제밸브 `yy47`만 바꿨다. `evaluate(t=0)`의 센서41개는 세 경우에 정확히 같았지만 다음 변화율은 달랐다.

| 밸브 상태 차이(pp) | 실제 냉각수 유량 model값 | 냉각수온도 `yy36` 변화율(모델시간 h 기준) |
|---:|---:|---:|
| −0.001 | 411.04812880000003 | 0.042253422209196236 |
| 0 | 411.0581288000001 | −0.00000043807567094608337 |
| +0.001 | 411.06812879999995 | −0.04225429836001047 |

변화율 차이는 기존 식 `10*500.53*(T_in−W)/7060 * Δv`와 독립 검산했다. 같은 센서/명령값이라도 숨은 밸브 상태에 따라 상태 변화가 달라진다. 따라서 **현재값 센서+명령을 완전한 결정론적 1차 상태로 보는 가정은 이 점에서 성립하지 않는다.** 이것이 충분한 과거 관측·잠재변수 모형의 불가능성, 전역 비간선 부재, 일반적 비식별 정리를 증명하는 것은 아니다. 가용 상태를 추가하거나 시간·제어 기억을 명시하는 정의가 필요하다.

### Q1–Q3와 참조의 세 수준

| 질문/수준 | 판정 | 남은 조건 |
|---|---|---|
| Q1 같은 simulator 관측·조작 실행 | PARTIAL | 고정 source/짧은 fresh pair/명령·시계 검증. 실제 학습용 excitation·정상 운전 범위·미사용 평가 분리·평균효과 정밀도는 미검증 |
| 내부 상태 업데이트 참조 | PARTIAL/CANDIDATE | u10→v10 변화율, v10→유량→W 변화율, E/조성→온도 등 기존 국소 검산. 정상조건 외 stiction/IDV·controller·상태 보존·경계 부모를 제거할 수 없음 |
| 센서 관측 직접 참조 | BLOCKED | 숨은밸브/에너지/조성/제어기 기억·시간 주변화. 비교 가능한 노드·시차·직접성·음성쌍 universe 미확립 |
| 조작 총반응/도달 | PARTIAL | 짧은 u10→Y9 반응과 구현 경로. 직접 센서 간선이나 평균 효과의 정밀 검증과 다름 |
| 비교 가능한 부분 구조 품질 | BLOCKED | 양성 일부만 검증. 음성관계와 발견 출력의 동일 노드/시간/간선 의미가 없음. precision/F1 미계산 |
| Q2/Q3 원래 전체 구조 품질–추천 가설 | NO-GO | 관측–참조–개입이 같은 정의라는 조건 미충족. 기존28간선 자동 승계 금지 |

## 5. 세 경로와 재사용 범위

| 경로 | 기존 결과/재학습 | 참조 신뢰성·독립 개입 | 현재 장애·판정 |
|---|---|---|---|
| A 원환경 복원 | 기존 데이터/7graph/F1을 원래 benchmark 기록으로 유지. 원 생성 코드 재학습은 여전히 별개 차단 | 28간선은 benchmark 구조참조. raw run·controller·MATLAB·sampling/export가 맞아야 같은 환경 개입 가능 | 새 단서 없음. 원자료/정식 실행환경/1499행 계보 미확보. 직접연결 NO-GO. 반복 다운로드/환경 검색 안 함 |
| B Python 신규 관측–발견–참조–do | 기존 알고리즘 구현·채점 정의·추천 인터페이스는 조건부 재사용. 새 학습·새 참조·새 효과는 전부 별도 결과 | 같은 simulator 실행은 가능. 센서 직접/시차 참조 및 음성쌍 미검증; 현재값 상태 충분성 반례 | 기존 질문을 새 환경에서 검증할 가능성은 열려 있으나 지금 채택 근거 부족. 전체 구조 연구 NO-GO |
| C 외부 전이 | 기존7graph를 원환경 산출물로만 사용. F1은 원benchmark 점수로 유지; 재학습은 전이 자체에 필수 아님 | 새 Python 측 반응 측정은 조건부 가능하지만 환경·graph·계수 오류를 분리 못함 | 원래 가설 직접 검증 아님. 별도 탐색/범위 변경 승인이 필요. 자동 실행 안 함 |

기존 TEP CSV는 새 source의 관측 데이터가 아니다. 7 frozen graph/Step6는 원래 구조 평가 기록으로 계속 유효하다. 기존 Ridge 적합은 원환경 관측 예측 진단이며 새 simulator 인과효과 계수가 아니다. metric 코드와 추천 정책은 **같은 노드/시간/식별 가정일 때만** 구현 자산으로 재사용한다. cycle/시차/미확정 방향 제약도 그대로 남는다. 새로운 연구에서는 참조가 타당해진 뒤 새 데이터를 실제 학습해야 하며 과거 Final 생성 코드를 전부 회수했다는 주장은 하지 않는다.

**D를 권고하는 이유:** A는 계보·실행환경, B는 관측 참조와 충분한 학습 변동이 미충족이다. 새 software guard와 실행 adapter는 이 장애를 숨기지 않고 드러낸다. 현재 Python에서 가능한 것은 C형 **국소 기술 반응** 수준이나, 이를 공식 축소 연구로 채택하지 않는다. 원래 연구 질문은 유지한다.

## 6. 바로 다음 한 작업과 완료 조건

**다음 한 작업: 수동·무Fault 조건의 밸브 한 단계 전이 계약을 독립 검산한다.** 전체 센서 GT를 재구성하는 것이 아니다. `scripts/validate_tep_valve_transition_contract.py`(아직 없음)를 만들고, 고정 source의 `python_backend.py:1241–1254`, `simulator.py:308–334`, 현재 `PLAN_v1.json`/`closure_v1/RESULT.json`과 기존 REF-B 국소 결과를 입력으로 사용한다.

`명령 u_t`, `실제밸브 v_t`, `다음밸브 v_t+1`을 서로 다른 시간/종류의 노드로 명시한다. 기존 ±0.001pp 고정점 범위 내에서 식 `v_t+1=v_t+(u_t−v_t)/5`를 독립 계산하고 actual evaluate/Euler와 대조한다. stiction/클리핑/IDV/제어기 개입 시 단순식 적용을 거부하는 경계 검사를 포함한다. 과거 명령 cache·초기상태·난수/시계와 어떤 조건에서 다른 부모를 고정했는지 기록한다. 이때 입력 의미가 기존 PC/BOSS 정적 센서 graph와 다름을 자동 검사한다.

완료 조건: 좁은 정상 영역에서 명시한 전이식/부모의 실제 검산과 **미지원 조건 거부**가 모두 통과하고, 원 센서 구조평가로 연결하면 환경 계약이 거부되는 것. 유한점에서 반응이 없었다는 사실만으로 전역 음성 간선을 확정하지 않는다. 산출물은 작은 `VALVE_TRANSITION_RESULT.json`과 재현 코드이며 공식 GT/발견학습 데이터/전체 F1은 아니다. 기존 source와 실행환경이 이미 있어 원자료/MATLAB 확보를 기다릴 필요는 없다.

이 단계는 관측가능한 상태를 늘린 좁은 동적 연구가 수학적으로 정의될지 확인하는 기술 선결조건이다. 이것만으로 B 채택이나 원래 가설 입증을 선언하지 않는다. 후속 실제 연구는 발견 알고리즘의 노드·시차 estimand, 충분한 자극과 독립 반복, 타당한 양성/음성 참조 범위를 별도로 확정하고 사용자에게 설계 변경 여부를 제시해야 한다.

## 7. 재현·실행 기록

명령(기존 별도 환경의 Python3.11 사용):

```text
python -X utf8 -m unittest tests.test_environment_contract -v
python -X utf8 scripts/run_tep_environment_bridge.py --source <pinned-checkout> --output <fresh-output>
python -X utf8 scripts/check_tep_observation_closure.py --source <pinned-checkout> --output <fresh-output>
python -X utf8 scripts/validate_environment_contract.py
python -X utf8 scripts/check_research_state.py
git diff --check
```

각 runner는 기존 출력 덮어쓰기를 거부한다. 기술 원시 `technical_v1/`와 고정점 `closure_v1/`에 별도 SHA256 manifest가 있다. CI validator는 외부 source를 실행하지 않고 저장 원시의 시간/반복/밸브 차분/국소식/거부사유/hash를 다시 계산한다. 로컬 실제 실행과 CI 저장검산은 다른 증거다. 전체 테스트·기존 동결/상태 검사의 실제 결과는 `research_runs/tep_environment_bridge/validation/`에 기록한다. 누락 원자료·MATLAB·장기 연구환경 검증을 새로 수행한 것으로 표시하지 않는다.

실제 전체 단위검사 첫 실행은81개 중 과거 hash 고정검사3건 실패했다. 원인은 legacy decision_mvp에 wrapper를 추가한 것이었다. 과거 기대 hash/산출물을 수정하지 않고 해당 파일을 원래 bytes로 복원하고 독립모듈 진입점만 유지했다. 실패로그와 해결은 validation/00_unittest.txt·FAILURE_EXPLANATION.json에 보존했다. 최종 재검사 결과는 FINAL_CHECKS.json을 기준으로 확인한다.

최종 로컬 전체81단위검사와10개 새/기존 검증script는 통과했다. 실행코드는 `256b65635d2b7fc2287323e3e1975914694e6c9a`, 새 PR은 #18(base PR17)이며 미병합이다. 초기 실패3건은 삭제하지 않았다. GitHub Actions는 별도 최신 head 결과를 확인한다.

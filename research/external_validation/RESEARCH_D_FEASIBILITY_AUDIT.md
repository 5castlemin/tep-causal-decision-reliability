# Research D 외부 검증 타당성 감사

2026-11-25 · Research C main `7742180cef09b506e3d26e56d58a03b3d6a4e37d` · **CONDITIONAL_GO**

## A. Executive Summary

최우선 후보는 **Causal Chamber Light Tunnel Mk2, linked_leds v1.0의 `lt_spice_v1`**이다. 실제 챔버 측정에서 LED 명령 `green`과 `ir_1 → led_2_uv → current_led_2_uv`의 매개경로가 기록된다. 제조사의 알려진 효과 그래프에는 `green→current_led_2_uv` 직접 간선이 없다. 서로 구별되는 정수 명령 5개가 각 noise 구성의 20개 순차 배치 모두에 나타난다. 이는 지원된 행동의 실측 정책 손실 차이를 검토할 근거다. 전쌍 참조, 실제 배정–응답 시간 정렬, 학습·평가 독립성, 분석 단위 및 상수 노드가 남은 조건이다. 다음 단계는 감사 결과와 후보의 기술 증빙을 검토하는 일이다. [후보와 과제](EXTERNAL_TASK_AND_ACTION_SUPPORT.md)

## B. 공식 근거와 실제 검사

| 질문 | 확인 결과 |
|---|---|
| 1. 오류 수정 정책을 적용할 물리 환경 | Mk2 참조 구조가 기술적으로 DAG로 표현된다. 독립 재전사와 음성쌍 검증이 구조 채점 전 필요하다. Mk1 두 표준 DAG에는 strict 과제가 0개다. WT pressure-control은 순환이다. |
| 2. 관측과 구조를 함께 확보하는가 | LT Mk1의 저자 지정 reference와 Mk2의 무작위 범위 명령 기록을 확보했다. 두 reference 모두 설정을 구분했다. Mk2 기록의 동일 파일 내부 배치는 장치 외부 provenance와 별도 검토가 필요하다. |
| 3. 실측 개입으로 손실을 평가할 수 있는가 | 지정된 물리 명령 수준에 반복 지원이 있다. Mk2 고정 조건의 독립 평가 분할과 시간·carryover 증빙을 충족하면 정책 손실 차이를 추정할 수 있다. 절대 regret은 모든 행동의 평균 및 최적 행동 불확실성을 추가로 다룬다. |
| 4. 유지할 수 있는 범위 | 참조의 정의가 승인되는 경우 M1–M4, Rule A, UNRES abstention, 구조적 후보/정책/편집비용 유지. 평가 자료는 추천 단계에서 차단. |
| 5. 변경할 범위 | 외부 데이터 및 action/evaluation adapter, 상수/시차·referent 기준, 독립성 설계가 필요하다. nonlinear/dynamic learner나 direct 과제는 별도 연구로 보고한다. |
| 6. 독립 반복이 충분한가 | 공개 CSV에서 장치 또는 평가 독립 세션 수를 확정할 수 없다. WT Bernoulli의 2,000 배정 블록과 Mk2 20개 연속 배치는 서로 다른 실험 단위다. 장치 조건부 사례가 현실적이며 C 수준의 독립 SCM 확증은 근거가 부족하다. |

**공식 문서.** Causal Chamber 논문과 부록 V는 물리 근거와 특정 개입·지연에서의 방향 검증을 제공한다. 비교 조건, carryover 없음 및 정상성 가정이 명시된다. 장시간 풍압은 대기압 drift 영향을 받는다. 노출 CSV의 `intervention`은 기록 관례상 SET 이후 첫 측정을 표시하며 `flag`의 의미는 프로토콜별로 다르다. `uniform_reference` 전 행은 기록상 1이고 Mk2 SPICE 파일 전 행은 0이다. 관측/개입 연구 역할은 배정 프로토콜과 실험 파일 이름으로 정의한다. [논문](https://doi.org/10.1038/s42256-024-00964-x) · [부록 V](https://arxiv.org/html/2404.11341v2#A5) · [문서](https://docs.causalchamber.ai/)

**직접 확인.** LT/WT의 9개 공식 v1 ZIP에서 165개 실험 CSV, 총 1,643,815행을 검사했다. 파일별 타입, 열, 결측, counter·timestamp, 그래프 누락과 추가 컬럼, flag 및 기록 명령 빈도를 JSON으로 보존했다. 이 합계는 독립 표본 수를 표현하지 않는다.

| 공식 ZIP | CSV 수 | 합계 행 × 파일당 열 | 참조 및 설정 |
|---|---:|---:|---|
| `lt_spice_v1` | 4 | 230,000 × 104 | Mk2 linked_leds, 독립 검토 전 전사 90/142 DAG |
| `lt_interventions_standard_v1` | 59 | 68,000 × 46 | LT standard 38/57 DAG |
| `lt_validate_v1` | 29 | 4,300 × 46 | LT standard 38/57 DAG |
| `lt_malus_v1` | 12 | 12,000 × 46 | LT standard 38/57 DAG |
| `wt_validate_v1` | 28 | 23,449 × 37 | WT standard 32/42 DAG |
| `wt_walks_v1` | 28 | 891,016 × 37 | WT standard 32/42 DAG |
| `wt_bernoulli_v1` | 3 | 405,000 × 37 | WT standard 32/42 DAG |
| `wt_pressure_control_v1` | 1 | 10,000 × 45 | WT pressure-control 32/44 순환 |
| `wt_pc_validate_v1` | 1 | 50 × 45 | WT pressure-control 32/44 순환 |

9개 ZIP에서 pandas 기준 결측은 0건이었다. LT Mk1에는 reference 밖 `camera,v_board,v_reg`가 있고 WT pressure-control에는 PID 진단 8열이 있다. 하나의 명령 설정 CSV만으로 독립 세션 식별자의 존재를 입증할 수 없다. 비교 자료는 ESS reduced archive와 공식 전처리/참조, causalAssembly 반합성 예제와 참조, CausalMan micro 공개 simulation CSV 및 mixed graph를 확보했다. [다운로드·해시](dataset_manifest.json) · [전체 검사](inspection_results.json) · [비교 자료 직접 확인](DATASET_CANDIDATE_MATRIX.md)

## C. Gate A–E 및 최종 판정

후보별 표와 판단 연결은 [Gate 매트릭스](DATASET_CANDIDATE_MATRIX.md)에 있다. Mk2 A는 PASS이고 B/C/D/E는 CONDITIONAL이다. 관측–배정–그래프의 시간·변수 조건이 맞아야 하며 비간선 및 숨은 공통원인이 오분류를 만들 수 있다. 67개 상수 열 때문에 C의 전 노드 learner는 그대로 적합이 불가능하다. WT standard는 exact finite actions의 물리 평가 후보지만 C의 strict Gate에서 실패한다. ESS의 전문가 그래프와 TEP의 기존 구조 참조만으로 개입 손실을 식별할 수 없다.

## D. 추천 설계

Mk2 `green` → `current_led_2_uv` 단일 과제에서 동일 조건의 정확한 공통 행동과 장치·세션 또는 적격 배치 단위를 동결하는 방안을 제안한다. 학습 표본으로 목표와 scale을 고정하고, 평가자가 가린 응답은 추천 확정 뒤에만 공개한다. B=2 S0−Full Greedy는 공통 최소 손실이 상쇄되어 독립 개입자료의 행동별 평균으로 대비할 수 있다. 절대 regret, 제곱 평균의 추정 편향, 세션 변동 및 최적-arm uncertainty는 별도 절차로 다룬다. [평가 설계](RESEARCH_D_DESIGN_OPTIONS.md)

## E. 비판적 평가와 노출 기록

| 검토 | 확인한 점 | 부족하거나 근거가 없는 주장 |
|---|---|---|
| 연구 적합성 | Mk1 그래프의 구조적 차단과 Mk2 매개경로를 실제 graph/CSV에 확인 | 물리 장치 내 가변 조건이 제조라인의 구조 또는 오류 모집단을 대표한다는 근거 없음 |
| 평가 타당성 | 원본 명령 수준 수와 후보별 반복을 집계 | 빈도는 명령 fidelity, 정착 시간, 독립 평가 가능성 및 실제 손실 정밀도의 증명이 아님 |
| 통계 | WT 블록과 센서 행, Mk2 배치와 장치, G0 seed와 정책을 구분 | 장치 독립성이 증명되지 않았다. 같은 평가 파일을 여러 seed에 쓰는 경우 불확실성 공유 |
| 정보 누출 | 응답 통계는 결측과 상수 여부의 품질 진단에 한정했다. Y 원시 값·평균·효과·손실·정책 성능의 표시/집계를 하지 않았다. 논문의 공개 근거와 프로토콜은 열람했다. | 공개 benchmark는 이전 사용이나 외부 분석자의 outcome 노출을 배제할 수 없다. 과제·action 범위는 그래프와 설정값으로 제안했고 승인 때 해당 데이터의 출판·사용 이력을 확인한다. |
| 계약 일관성 | 구조 정책과 손실 형태 재사용을 우선 검토. C 코드에서 GT 정보 경계를 점검 | 단일 장치의 empirical action-loss 대비로 C의 synthetic paired-t 결과를 재확증할 수 없다. 이번 읽기에서 C 정의나 결과 수정이 필요한 새 결함을 확인하지 않았다. |
| 실패 가능성 | 영효과, Full Greedy 또는 M4 악화도 기록 가능한 설계 제안 | 활성 매개경로와 연구에 의미 있는 손실 대비는 다르다. 포화, 비선형, 고정 설정으로 학습 불가, 정책 action 동률, 참조 누락과 작은 유효 표본이 해석을 제한할 수 있다. |

파일을 파싱할 때 응답 열을 메모리에 읽어 스키마와 결측을 검사했다. 센서별 값, 목표 손실 및 정책 결과를 감사 산출물에 저장한 사례는 0건이다. 기계 기록의 `constant_columns`는 적합 불가능한 컬럼의 이름만 보존한다. 외부 장치 조작, SCM 적합·실험 추천, 정책별 regret, C 코호트 실행, discovery 실행은 하지 않았다.

## F. 다음 단계

Mk2 참조·배정·세션 증빙을 우선 검토하고, 결과를 가린 상태에서 적격성이 확인되는 경우에만 새 외부 분석 계약으로 진행한다. 필수 기준 실패 시 조건부 사례, direct 또는 반합성 경로의 연구 질문 변경을 별도 검토한다. [진입·완료·중단 기준](RESEARCH_D_ROADMAP.md)

## G. 재현 및 작업 기록

`research/research-d-external-validation-feasibility`는 PR #39의 main 기준이다. 원자료 및 외부 참조 원본은 저장소 밖의 작업 폴더에 둔다. Checksum과 집계 결과만 version control에 넣는다. 공식 PyPI wheel은 정적 AST로 읽고 장치 API를 호출하지 않는다. Python 3.11.15 격리 환경, pandas 3.0.1, NetworkX 3.6.1. PDF 9쪽의 도식 육안 확인에는 별도 설치한 pypdfium2 5.15.2와 Pillow 13.0.0을 사용했다.

```text
git clone https://github.com/juangamella/causal-chamber.git <catalog-outside-repo>
git -C <catalog-outside-repo> checkout c2b307036446b8d3ca173e9f41ff465b7111819a
python -m venv <audit-venv>
python -m pip install -r requirements.txt -r requirements-research-c-ci.txt
python -X utf8 research/external_validation/inspect_support.py --download --data <data-outside-repo> --catalog <catalog-outside-repo> --output <inspection-json>
python -X utf8 -m unittest discover -s tests -p test_external_validation_support.py -v
git diff --check
```

감사에서는 manifest URL의 최초 파일 확보에 `curl.exe -fLsS`와 Python `urllib.request.urlretrieve`를 사용하고 검사기를 `--download` 없이 실행했다. ESS 첫 전송은 부분 파일로 종료됐으며 재전송본이 게시 크기·MD5·ZIP CRC를 통과했다. 해당 partial 파일의 해시는 정상 데이터의 manifest에 포함하지 않았다. 환경 정책상 원자료 폴더를 checkout 바깥으로 지정한다. [기계 요약](feasibility_audit_summary.json) · [검증 명령과 기록](VALIDATION.md)

# Research C — 최종 Feasibility 및 실험 실행 Gate

상태: **구조 파일럿 완료 / 연구 계약 후보 미승인 / 연구용 SCM 실행 차단 유지**
기준 커밋: `26f5b2fe0ceb5cae5c7cdd14b5aff66bbbb5476b`
범위: 결정론적 구조 fixture 및 TEST_ONLY 실행 원장만 사용. 연구 SCM 계수, 관측자료, 개입 손실, 정책 성능 Regret은 생성하지 않았다.

## 1. 구현 감사 요약

기존 제안 구현은 true adjacency마다 확률 `q=0.15`로 손상을 제안하고, 손상 시 FN/REV/UNRES를 각각 1/3 확률로 고른다. GT에 없는 unordered pair마다 `r=0.05`로 FP를 제안하며 방향은 공정하게 선택한다. pair별 난수 stream은 결정적으로 분리되어 있고, 오류 제안은 DAG 조건을 통과할 때만 수락된다. DAG-invalid proposal은 기록 후 거절하며 재추출하지 않는다. 따라서 q/r은 오류 실현 비율이 아니며, 특히 FP·REV는 DAG 제약으로 실현률이 낮아질 수 있다.

정책 진단은 현재 후보 계약 그대로 Rule A, G0-fixed opportunity, M4 활성 성분 동등 가중, 단위 비용, B=0..4를 사용했다. 이는 이 파일럿의 설정이지 승인된 연구 계약이 아니다. 지표 활성은 실현 구조 사건에 의존하고, M4의 기회 수·후보 수와 선택된 오류 구성은 M1–M3와 다를 수 있다. 따라서 동일 가중치·fixed-opportunity가 공정성을 자동 보장한다고 볼 수 없다.

## 2. 사전 고정 구조 파일럿

설정은 [structural_pilot_design_v1.json](research/original_objective/structural_pilot_design_v1.json), 실행기는 [structural_pilot.py](research/original_objective/structural_pilot.py), 진입 스크립트는 [run_research_c_structural_pilot.py](scripts/run_research_c_structural_pilot.py)다. 설계는 네 topology × 노드 수 6–10의 20개 층마다 25회, 총 500 topology proposal이다. master seed는 topology 20261123, task 20261124, G0 81420623이며, task와 G0 난수 stream은 분리했다. task는 strict indirect-only ordered pair에서 균등 선택한다. eligible pair가 없는 topology는 분모에 보존하고 대체하지 않는다.

실행 결과는 [structural_feasibility_pilot_v1.json](research/original_objective/test_outputs/structural_feasibility_pilot_v1.json)이다. 설계 SHA-256은 `80abd18f44fb006339ba7907bbeb5462248f71d657bd33653b80640e6b9e9415`, compact 결과 파일 SHA-256은 `8e1f8353f71d102dc75afea047a569418b1ea5c1b6d4b7e680fec1164378fc65`이며 wrapper 내부 payload checksum도 재검증했다. 파일에는 모든 topology/G0 case 기록과 집계 정책 진단을 보존하고, 상세 per-policy trajectory 행은 동일 설계 seed로 재현할 수 있어 생략했다.

### 관측된 구조 가능성

| 측정 | 결과 |
|---|---:|
| topology proposal | 500 |
| strict indirect task eligible / rejected | 494 / 6 |
| 참 간선 / 비인접 쌍 평균 | 8.8 / 20.2 |
| eligible G0 중 오류 0개 | 55/494 (11.1%) |
| 오류 제안 / DAG 수락 / DAG 거절 | 1,190 / 1,044 / 146 (거절률 12.3%) |
| 실현 오류 M1 / M2 / M3 / M4 성분 합 | 121 / 363 / 213 / 347 |

각 지표가 한 번 이상 활성화된 G0 비율은 M1 108/494 (21.9%), M2 245/494 (49.6%), M3 163/494 (33.0%), M4 235/494 (47.6%)였다. M1과 M3는 절대 오류 수가 상대적으로 적고 활성화 비율이 낮다. 이는 해당 정책을 비교할 기회가 드문 표본이 상당함을 뜻하며 성능을 뜻하지 않는다.

토폴로지별 strict task 거절은 fork_branch 5/125, observed_common_cause 1/125였다. 이는 제안된 topology/task 생성 계약에서 생기는 정상적인 proposal 거절이며, 새 seed나 새 proposal로 보충하지 않았다.

오류 제안/수락/거절은 유형과 구역에 따라 달랐다. FN off-task 121/121 수락, task 89/89; FP off-task 417 제안 중 363 수락·54 거절, task 106 중 63 수락·43 거절; REV off-task 139 중 104 수락·35 거절, task 109 중 95 수락·14 거절; UNRES off-task 109/109, task 100/100 수락이었다. FP task-zone 제안 거절률은 40.6%, FP off-task는 12.9%였다. 오류 위치에 따른 DAG 가능성 차이가 정책 기회 수에 반영되므로, proposal·accepted·rejected 분모 모두 보존해야 한다.

### 예산 포화와 정책 구별

각 예산에서 16개 명목 전략 × 494개 eligible G0, 총 7,904 policy-case를 보았다.

| 예산 | 예산 소진 | 후보 소진 | 경쟁 후보 2개 이상인 case | case당 평균 고유 최종 그래프 |
|---:|---:|---:|---:|---:|
| B=0 | 100.0% | 0.0% | 해당 없음 | 1.00 |
| B=1 | 57.9% | 42.0% | 26.9% | 2.51 |
| B=2 | 27.1% | 72.7% | 26.9% | 3.18 |
| B=3 | 12.2% | 87.6% | 26.9% | 3.43 |
| B=4 | 5.0% | 94.7% | 26.9% | 3.51 |

단위 비용에서 B=3·4는 대부분 후보가 먼저 소진됐다. 따라서 예산 3·4는 실현 오류가 적은 case에서 추가 구별을 거의 제공하지 않는 포화 진단으로 보는 것이 타당하다. pairwise policy graph 동일률은 B=1 45.95%, B=2 39.95%, B=3 38.49%, B=4 38.25%였다 (B=0은 정의상 모두 동일). 전체 case-budget 조합에서 비교 pair의 52.53%가 동일 그래프였다. 명목 전략 수는 서로 다른 수정 결과 수가 아니다. 이 파일럿의 정책 진단 수치는 검토 중인 G0/정책 후보에 대한 구조 결과일 뿐 Regret 성능 결과가 아니다.

고정 opportunity는 각 지표의 G0 기회를 고정하므로 작은 task support만으로 수정 후 분모가 줄어 점수가 부풀어나는 현상은 막는다. 그러나 M4의 활성 성분 수와 오류 사건 정의, 기회 크기의 차이는 남는다. M4가 불리하거나 유리하다고 단정할 수 없고, 결과에서 기회 수 및 활성 성분을 함께 층별 보고해야 한다.

## 3. Residual UNRES 처리

[unresolved_abstention.py](research/original_objective/unresolved_abstention.py)는 구조 수정 뒤 남은 UNRES를 구조 그래프 및 M1–M4 기록에 그대로 남기고, 학습 입력 DAG에는 방향 간선을 넣지 않는 TEST_ONLY adapter를 구현한다. 이는 예산을 쓰는 resolve/delete 연산도, 정답 간선 복구도 아니다. 기존 test-only topological completion adapter는 보존했으며 기본 연구 경로에 연결하지 않았다.

고정 E2E fixture에서 새 인코딩으로 17개 정책 × 5개 예산 경로(85/85)가 적합 및 평가까지 완료됐고, 구조상의 unresolved 수는 유지됐다. 이는 학습 경로가 실행 가능함을 보여줄 뿐, 다양한 SCM에서의 안정성·동등한 적합 성공률을 증명하지 않는다. 방향을 버리는 표현은 UNRES 정보를 학습에서 잃으므로 특정 오류를 가진 그래프의 적합 결과와 정책 비교 가능성에 영향을 줄 수 있다. GT 정보를 사용하지는 않지만, 반대로 무료로 방향을 제거해 학습 문제를 바꾸므로 구조 수정과 명확히 분리해 기록해야 한다.

권고는 이 인코딩을 주 분석 후보로 승인 검토하되, 수정된 구조 graph hash와 learner DAG hash를 별도 보존하고, 평가 완료 집합은 모든 정책에서 공통인 SCM에 한정하는 것이다. 일부 정책만 실패하면 paired 결과에서 제외하고 실패 사유를 분모에 남긴다. 실패 Regret=0 대체는 금지한다. 이 선택은 아직 미승인이다.

## 4. Fixture 전용 cohort ledger

[cohort_ledger_test_only.py](research/original_objective/cohort_ledger_test_only.py)는 연구 생성기가 아닌 TEST_ONLY 저장·재개 기구다. 실행/config binding과 SCM/G0/evaluation seed stream 분리, 단일 writer lock, checksum이 붙은 원자적 per-SCM checkpoint, 같은 입력 replay, 중복/설정 충돌 및 손상 감지, 누적 시간·저장량·RSS 표본 기록, 실패 또는 불완전 정책 vector 격리를 구현했다. 실제 프로세스 종료 후 SCM checkpoint 재개, 동시 writer 차단, resource stop, checksum 불일치를 테스트했다.

현재 제한은 명확하다. worker는 SCM 경계 사이에서만 자원 cap을 확인하고, 진행 중인 SCM 안에서 강제 종료되지 않는다. RSS는 sampled 관측이라 순간 overshoot 가능성이 있으며 OS hard quota가 아니다. 연구 cohort CLI, stage-isolated worker, 연구 pipeline과의 binding은 아직 없다. 그래서 production readiness는 완료되지 않았다. 이 TEST_ONLY ledger를 실제 64/200 실행에 사용하면 안 된다.

Windows에서 동시 writer 검사 시 기존 lock 코드가 byte-lock 전에 파일을 읽다가 `PermissionError`를 낸 것이 확인됐다. lock byte를 읽지 않고 파일 길이 확인 후 byte-lock을 시도하도록 수정했고, 프로세스 종료·resume/동시 충돌 테스트가 통과했다.

## 5. 사용자 승인용 결정표

아래는 승인 요청을 한 번에 압축한 권고다. 어느 행도 승인된 계약 또는 사전등록으로 간주하지 않는다.

| 묶음 | 권고 선택 | 사용자 응답 | 근거 및 영향 |
|---|---|---|---|
| A. SCM/task/G0 | **MODIFY 권고**: 네 topology와 6–10 노드, q=.15/r=.05 및 conditional true error 1/3 mix는 후보로 유지. strict indirect task 거절 6/500은 denominator에 보존. 단위 비용 아래 B=1·2를 주 비교 예산 후보로 두고 B=3·4는 사전 포화 진단으로 보고. | APPROVE / MODIFY / DEFER | M1/M3 활성률이 낮고 오류 없는 G0가 11.1%; B3·4 후보 소진이 각각 87.6%·94.7%. 오류율을 사후 조정하지 않음. 이 pilot은 대표성이나 효과를 보증하지 않음. |
| B. 정책/비용 | **DEFER 권고**: Rule A, G0-fixed opportunity, 동일 활성 M4 성분 β, 기준 비용 1 및 task multiplier λ=1 후보를 계약에서 명시하되, Rule B·초기 오류 수 정규화·방향 상대비용 2/3·사전 지정 λ/β 대안은 제한 민감도 규칙으로 승인받기 전 실행하지 않음. | APPROVE / MODIFY / DEFER | M4 opportunity와 active component 구성은 다른 지표와 다르며 구조적 공정성을 보장하지 않음. 공식 지표 분모, 정책용 utility, 공통 잔존 구조 벌점은 서로 분리해야 함. |
| C. 평가/운영 | **MODIFY 권고**: residual UNRES abstention을 학습 adapter 후보로 채택, 구조 graph와 learner DAG 분리. B0는 no-edit 기준선, 모든 정책 성공한 공통 SCM만 paired 평가. N=64 개발/N=200 독립 평가는 후보로만 남기며, fixture ledger를 production runner로 간주하지 않음. | APPROVE / MODIFY / DEFER | 85/85 TEST_ONLY 경로 성공은 확인됐으나 cohort 수준 격리·자원·resume runner가 미완료. 기존 A/B 자료는 재사용하지 않음. |

결정 후에도 별도 실행 승인이 필요하다. 우선순위는 residual UNRES 정책 의미, A/B/C의 응답, 주 예산·주 추정량·민감도 및 표본분할을 한 승인 기록에 확정하는 것이다.

## 6. 검증 결과

사용 환경: Windows, CPython 3.11.15, 저장소 requirements 기반 `uv run`.

| 명령 | 결과 |
|---|---|
| `uv run --python <CPython-3.11.15> --with-requirements requirements.txt python -m unittest tests.test_original_objective_structural_pilot_and_ledger tests.test_original_objective_e2e_fixture tests.test_original_objective_policy_engine -v` | 30 tests PASS |
| `uv run --python <CPython-3.11.15> --with-requirements requirements.txt python scripts/validate_original_research_fixture_contract.py` | 기존 fixture validation PASS; A/B trajectory 기대값 유지, 정규화별 진단 출력 |
| `uv run --python <CPython-3.11.15> python -m compileall -q research/original_objective scripts/run_research_c_structural_pilot.py` | PASS |
| `git diff --check` | PASS (CRLF 변환 경고만 출력) |

일반 `python.exe`는 이 환경의 애플리케이션 제어 정책에 의해 차단되어 사용하지 못했으며, 저장소 환경인 `uv run` 경로로 검증을 마쳤다. 기존 Step 4 동결 파일, Step 5/6 원시 결과, 발표 자료는 이번 변경 파일 목록에 없고 수정하지 않았다. 작업 시작 전부터 있던 미추적 `.build_reframed/`는 보존했다.

## 7. Gate 판정 및 다음 단계

**구조 feasibility: 완료.** 현 설정에서 여러 오류 유형과 정책 간 그래프 차이가 관측되지만, M1/M3 활성 기회는 상대적으로 적고 B3–4는 주로 후보 포화 상태다. 이 자료는 설계 비교 가능성만 평가한다.

**연구 C 생산 준비: 미완료.** 과학적 선택은 승인 전이며, production-grade 연구 cohort runner, SCM 단위 격리·복구 및 안전 cap도 아직 없다. 새 개발/독립 SCM과 실제 Regret은 생성하지 않았다. 다음 단계는 사용자 A/B/C 결정표 응답 후 해당 계약을 확정하고, fixture-only ledger와 분리된 production runner gate를 구현·검증하는 것이다. 그 이후에도 개발 코호트 실행은 별도 명시 승인이 필요하다.

연구 C의 SCM 실험은 현재 진입 가능하지 않다. 이 보고서는 권고를 제시하지만 연구 계약을 승인, 동결 또는 사전등록하지 않는다.

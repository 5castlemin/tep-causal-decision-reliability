# 연구 C G0·UNRES·생산 준비 독립 점검

**상태: Fixture 검증 보강 완료 / 연구 계약 미승인 / 신규 연구 SCM·Regret 미생성**

## 범위와 실행 환경

기준 커밋 `49bbbfd7fda7d62b4c07df26f7893eeb365aaebd`의 연구 C 후보 코드를 CPython 3.11.15 및 저장소 `requirements.txt` 환경에서 점검했다. 사용한 자료는 명시 계수의 기존 8-node TEST_ONLY fixture와 결정론적 관측행렬뿐이다. 새 proposal 코호트 또는 연구 표본을 생성하지 않았다.

## 1. G0 오류 생성 계약 후보와 구현

`research/original_objective/g0_candidate.py::corrupt_graph_candidate`의 기존 제안은 각 GT 인접쌍을 독립적으로 확률 `q=0.15`로 손상 시도하고, 조건부 FN/REV/UNRES를 각각 1/3로 뽑는다. 각 비인접 무순서 쌍은 독립적으로 `r=0.05` 확률로 FP를 제안하며 방향은 1/2씩 선택한다. 이 값은 관측 자료에서 추정된 오류율이 아니라 승인 대기 중인 생성 시나리오다.

이번 보강은 pair별 제안과 DAG 적합 순서를 분리했다. 제안은 각 true/false pair별 domain-separated RNG로 결정하고, DAG 수락 검토 순서는 별도 결정론적 stream으로 섞는다. 따라서 정렬된 노드 ID가 항상 먼저 cycle-compatible edge를 차지하지 않는다. cycle을 만드는 제안은 `rejected_dag`로 보존하며 재추출하지 않는다. 각 무순서 pair에는 최대 한 제안만 생긴다. 기록에는 `proposal_status`, `acceptance_status`, acceptance order, 제안 kind/state, DAG rejection 및 retry 0이 포함된다.

`configured`, `proposed`, `accepted` 단계의 비율을 분리하고, `metric × kind × task/off-task` 기회 수 및 최종 실현 오류 수를 직렬화 가능한 결과로 기록한다. 오류가 0개면 `NO_INITIAL_ERRORS`이며 재추출하지 않는다. 제안 설정 q/r와 실제 실현 오류율은 같다고 가정하지 않는다. DAG rejection 및 작은 지원집합 때문에 실현 종류별 비율은 달라질 수 있다.

고정 fixture에는 6개 true adjacency와 22개 비인접 쌍이 있다. seed 44 fixture 실행에서 2개 제안(UNRES 1, FP 1)이 모두 수락되어 실제 오류도 2개였다. 이는 검산 사례 한 개일 뿐 수율 추정이 아니다. 이 fixture의 task zone에는 true edge 기회 4개, off-task true edge 기회 2개가 있으며 Rule A의 FP 기회는 task node pair 2개, off-task pair 20개다. M4가 강제 활성화되지는 않지만 후보 지원 수가 지표별로 다를 수 있음을 보인다. 이 차이는 결과 보고에서 반드시 함께 제시해야 한다.

**권고 후보(승인 대기):** q/r 및 균등 조건부 true-error mix를 그대로 사전 지정하고, 모든 기회·제안·수락·cycle 거절 분모를 보존한다. 주 분석에서 M1–M4가 모두 활성화되도록 강제하거나, 결과를 보고 오류율을 재조정하지 않는다. 오류 기회 수를 맞춘 보조 분석은 별도 사전 정의가 필요하며 주 자연분포 분석과 합치지 않는다.

## 2. UNRES 정책 대안 및 권고

### A. GT 비사용 DAG completion

`unresolved_completion_test_only.py::complete_unresolved_for_test_only`를 만들었다. GT, SCM 계수, 효과 또는 손실 입력 없이 확정 방향 부분그래프의 lexicographic Kahn 순서를 구하고, UNRES 쌍을 그 순서에 맞춰 방향화한다. 동일 입력에서 재현되고, 완료 그래프는 DAG이며 고정 Step 3 Ridge learner에 들어갈 수 있음을 시험했다. 호출에는 명시적인 `test_only=True`가 필요하고 active E2E 경로에서는 호출하지 않는다.

이 방법은 GT 누출은 피하지만, 방향화를 예산 밖 무료로 적용한다. 또한 변수명 순서가 completion 방향에 영향을 준다. 즉 구조·행동 추정치가 달라질 수 있는 비중립적 표현 규칙이며 승인된 수리 연산으로 볼 수 없다. completion 완료율이 정책에 따라 다르면 서로 다른 SCM 집합에서 Regret을 비교하게 되므로 금지해야 한다.

### B. 주 분석에서 UNRES 제외

이 방법은 learner 입력을 단순화할 수 있지만 원래 M3의 unresolved rate와 M4의 UNRES 성분을 주 분석 대상에서 제거하거나 별도 모집단으로 옮긴다. 따라서 질문과 목표 모집단이 변경된다.

### 권고

현재 production/E2E 경로는 잔여 UNRES에서 기존처럼 `GRAPH_INPUT_UNSUPPORTED`로 fail closed 해야 한다. A를 시험 어댑터로만 두고, 과학적 승인 전에는 활성화하지 않는다. B 역시 범위 변경이므로 자동 채택하지 않는다. 주 실험 진입 전에 UNRES가 예산 내 resolve되어야 하는지, 별도 GT-blind completion을 허용한다면 비용·동률·노드 재명명 규칙을 어떻게 다룰지 사용자가 승인해야 한다. 평가 불능 policy는 실패로 보존하며 Regret=0으로 대체하지 않는다. 전체 정책 벡터가 완전하지 않으면 그 SCM에서 공통 정책 비교를 허용하지 않는다.

## 3. 정책 비교 가능성 기록

`e2e_fixture.py::run_fixed_fixture`는 각 budget/policy에서 M1–M4별 repair-candidate 수와 실제 선택 수를 기록한다. 각 17-policy 벡터에서 예상 정책 수, 평가 가능한 수, complete/incomplete 상태 및 공통 비교 허용 여부를 별도로 저장한다. 정책 쌍 진단은 동일 최종 graph, 동일 action, Regret 동률 비율을 서로 다른 분모로 기록하고 다음 원인 범주를 둔다: 수리 후보 없음, 동일 그래프, 다른 그래프·같은 행동, 다른 행동·같은 GT loss, 다른 행동·다른 GT loss, 실패로 비교 불가. 이는 구조·행동·손실 단계가 어디서 합쳐지는지 향후 확인하기 위한 진단 스키마다.

고정 fixture B=1에서는 모든 17개 레코드가 평가 가능하며 pair 분류는 136쌍이다. 이 값은 검증된 소프트웨어 fixture 한 건의 출력이지 정책 성능·확률 추정치가 아니다. 후보 수가 작은 policy는 생성 오류 기회가 없었는지, 후보는 있었으나 예산/지표 subset상 선택할 수 없었는지를 분리해 해석해야 한다. 16개 명목 전략이 16개 고유 그래프를 만든다고 가정하지 않는다.

## 4. GT 정보 경계와 계산 경로

정책 엔진은 GT DAG 구조로 사건·수정 후보를 확인하는 Oracle-assisted 단계다. 정책 API에 GT 계수, 개입 효과, action loss 또는 Regret 인수가 없다. completion 시험기도 GT/outcome 입력을 받지 않는다. E2E 학습·추천은 수정 방향 그래프와 공통 관측자료만 받고, recommendation을 고정한 후에 별도 analytic evaluator가 GT를 읽는다. 이 경계는 코드 수준 TEST_ONLY 테스트를 통과했다. Oracle-assisted 결과는 오류를 알고 고칠 수 있는 진단이며 배포 가능한 자동 오류 탐지기로 해석할 수 없다.

## 5. 생산 실행 준비 상태

현재 `run_research_cohort()`는 명시적으로 `RESEARCH_C_COHORT_BLOCKED`를 반환한다. 이번 변경은 정책별 실패와 비교 불가 상태를 보존하지만 durable cohort runner를 구현하지 않았다. Research C 전용 SQLite admission registry, 원자적 per-policy ledger/checksum, checkpoint/crash resume, 중복 실행 차단, 개발/독립 평가 코호트 격리, time/storage cap과 복구 검증이 없다. G0 seed와 SCM seed의 운영 바인딩도 cohort manifest 수준으로 확정·저장되지 않는다.

기존 Step 4의 runner는 별도 구현이며 Research C 통합 경로의 복구를 증명하지 않는다. 따라서 생산 SCM 실행 준비 완료라고 판정할 수 없다. 다만 고정 입력 E2E 결과 저장 스크립트는 새 파일만 exclusive-create하며 결과 직렬화 크기를 계산한다. 현재 스크립트에는 결과 checksum과 restart registry가 없어 production 보장으로 확장할 수 없다.

## 6. 검증 결과

실행 명령:

```powershell
uv run --python <CPython-3.11.15> --with-requirements requirements.txt python -m unittest tests.test_original_objective_e2e_fixture -v
uv run --python <CPython-3.11.15> --with-requirements requirements.txt python -m unittest tests.test_original_objective_policy_engine -v
uv run --python <CPython-3.11.15> --with-requirements requirements.txt python scripts/validate_original_research_fixture_contract.py
uv run --python <CPython-3.11.15> --with-requirements requirements.txt python scripts/run_original_objective_e2e_fixture.py --output <temporary-file>
uv run --python <CPython-3.11.15> --with-requirements requirements.txt python -m unittest discover -s tests -v
```

- E2E/G0/UNRES suite: 14/14 pass.
- 정책 엔진 suite: 8/8 pass.
- 원래 Fixture 계약 검증 스크립트: PASS. M1–M4 graph event 분자·분모, M3 reverse→UNRES, M4 vector/Rule A-B 귀속, 비용/DAG rejection, normalization counterexample를 재검산했다.
- 새 고정 E2E resource sample: 0.0495초 run-only, Windows peak working set 67,629,056 bytes, JSON output 398,649 bytes. 단일 fixture·모듈 import 제외의 측정이며 cohort 예상치나 상한으로 외삽하지 않는다. registry/checkpoint 자원은 미측정이다.
- 전체 suite: 297개 실행, 294 pass, 2 fail, 1 error. 세 실패는 기존 Step 4 보존/준비 검사다. (1) `test_final_gate_manifest_matches_mock_sources_and_raw_ledger`: Windows CRLF 작업파일 SHA `e8a1c6…` 대 frozen expected/Git blob `9c12a2…`; (2) `test_production_manifest_hashes_match_artifacts`: `WORK_LOG.md` 정규화 SHA `351869…` 대 stale expected `608efe…`; (3) `test_exact_clean_revision_passes_production_readiness_without_generating_data`: 수정 중인 worktree 및 보존된 미추적 `.build_reframed/` 때문에 dirty-tree gate가 거부. 앞 두 검사는 기존 Step 4 자산/manifest 원인으로 앞선 독립 감사에서도 확인되었고 이번에 변경하지 않았다. 세 번째는 테스트가 clean checkout을 요구하므로 현재 작업 트리 상태에 따른 오류다. Step 4 원시파일·manifest는 손대지 않았다.
- 전체 테스트의 실패 3건은 Research C 코드 실패가 아니다. 신규 연구 cohort 실행은 하지 않았다.

## 7. 승인 묶음 및 다음 Gate

| 묶음 | 구체적인 권고 후보 | 미승인인 과학적 선택 |
|---|---|---|
| A. 모집단/G0 | 기존 제안 q=.15, r=.05, 조건부 FN/REV/UNRES 각 1/3, FP 방향 공정 추출, cycle 제안 기록 후 무재추출; 지원·실현 분모 모두 기록 | SCM/topology/task 모집단, 오류율 및 혼합비, zero-error 포함, task별 기회 보고와 보조 matched-opportunity 정의 |
| B. 정책/비용 | 기존 후보 Task Zone 및 Rule A 주 후보/Rule B 보조, G0-fixed normalization, β equal-active, edit unit cost 1, B=0–4를 Fixture 출발값으로 사용 | zone/backdoor 및 FP 귀속, 정규화/가중치/β, 비용과 λ/P_all, 본 실험 예산·canonical 비교 해석 |
| C. 평가/운영 | 동일 SCM 내 모든 정책 paired; incomplete vector는 공통 비교 금지; 실패 대체 및 Regret 0 금지; UNRES fail closed 유지 | UNRES의 연구 처리, primary contrast/통계·N, 개발/평가 분리와 자원 상한, registry/checkpoint/output protocol |

이 값들은 승인/사전등록이 아니다. 승인 후 첫 기술 단계는 구조 전용 population/G0 feasibility와 자원 dry-run이다. 그 검토 뒤 연구용 SCM 실행에 대한 별도 명시 승인이 있어야 한다. 이번 커밋은 그 gate를 열지 않는다.

## 결론

G0의 proposal/acceptance 및 기회 분모, 정책 비교 단계별 diagnostics, 그리고 UNRES completion의 테스트 전용 후보가 고정 fixture에서 검증됐다. 그러나 UNRES 의미, 과학적 생성·정책 계약, 그리고 durable cohort 운영기는 아직 미해결이다. **신규 개발 SCM 실험 진입은 현재 불가**하며, 이번 연구 후보는 FROZEN/PREREGISTERED로 표시되지 않는다.

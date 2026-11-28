# Research C 최종 기술 Gate 보고서

## 판정

**TECHNICALLY_READY_FOR_APPROVAL** — proposal 자원 격리·체크포인트와 approval gate 통합의 기술 검증을 완료했다. 이 판정은 실제 사용자 승인, 사전등록, 연구 코호트 실행 또는 연구 결과 검증을 뜻하지 않는다. 현재 Development/Held-out 실행은 계속 차단된다.

## 변경 내용

- `research/original_objective/cohort_runner.py`
  - proposal을 별도 TEST_ONLY/Research SQLite ledger에 분리하고, proposal 단위 ID·RNG binding·상태·SHA-256·경과시간·RSS 측정치를 기록한다.
  - 기존 `run_isolated` 감시 경로를 재사용해 proposal worker에 개별 시간·샘플 RSS 제한을 적용한다. 중단된 proposal은 같은 ID와 attempt로 재시도한다.
  - 모든 목표 admission 또는 proposal cap 판정이 끝나기 전에는 다음 SCM cohort ledger로 전달할 수 없도록 했다. 체크포인트가 불완전하면 `run_approved_research_proposal_cohort`가 SCM orchestration을 호출하지 않는다.
  - 저장된 proposal을 재생성하지 않고 입력 assembly에 사용한다. resume 시 config/code/runtime/RNG binding이 달라지면 충돌을 거부하고, 불일치한 binding 항목을 기록한다.
  - proposal active time을 새 cohort ledger의 최초 누적 active time으로 이어 준다. SCM/G0 생성, 구조 정책 실행, 적합·추천, GT 평가, 결과 직렬화 및 원자 커밋의 시간을 별도 sidecar 진단값으로 남긴다. 이 시간은 결정론적 연구 payload와 checksum 안에 넣지 않는다.
  - 기존 cohort ledger 스키마를 건드리지 않도록 proposal ledger 스키마를 별도 DB에 두었다.
- `research/original_objective/proposal_pipeline.py`
  - 승인된 실행은 격리·체크포인트된 proposal 단계부터 시작하며, 저장 proposal로 기존 factory를 조립하고 동일 연구 실행 코어에 전달한다.
- `research/original_objective/runner.py`
  - Research output 경로에서 TEST_ONLY proposal ledger를 거부하고, 동일 경로의 기존 연구 proposal ledger가 다른 run/cohort에 묶여 있으면 실행을 중단한다.
  - private TEST_ONLY gate injection 경로를 추가했다. 실제 CLI는 이를 노출하지 않으며, config/manifest/code/runtime 검증이 통과한 테스트만 격리된 TEST_ONLY 실행으로 연결한다.
- `research/original_objective/e2e_fixture.py`
  - 기존 결과의 해시와 값을 바꾸지 않고, budget별 구조 수정·적합/추천·GT 평가 시간을 선택적 측정 sink에 기록한다.
- `tests/test_original_objective_runner.py`, `tests/test_original_objective_proposal_stage_gate.py`
  - proposal 정상 생성, 부적격 기록, timeout, 샘플 RSS cap, 실제 coordinator 프로세스 종료 후 재개, 체크포인트 직전/직후 중단, positive/negative approval gate, 시간 누계 전달, 불완전 proposal에서 admission 금지를 검증한다.

## 검증

- Python compile: 변경·추가한 Python 파일 6개 통과.
- Research C 회귀 명령:
  `python -m unittest tests.test_original_objective_proposal_stage_gate tests.test_original_objective_runner tests.test_original_objective_cohort_runner tests.test_original_objective_e2e_fixture tests.test_original_objective_policy_engine tests.test_original_objective_policy_engine_independent tests.test_original_objective_structural_pilot_and_ledger -q`
  **65 tests, 모두 통과.**
- proposal gate의 unittest discovery 실행: **9 tests, 모두 통과.**
- `python scripts/validate_original_research_fixture_contract.py`: 통과. 새 SCM, 관측자료, 개입효과 또는 연구 Regret은 생성하지 않았음.
- `git diff --check`: 통과.
- `python scripts/run_research_c_runner.py --mode research`: config/manifest가 없는 상태에서 `RESEARCH_MODE_BLOCKED`로 종료(프로세스 exit 1). proposal ledger 또는 연구 코호트는 생성되지 않음.
- 전체 저장소 `python -m unittest discover -s tests -q`: **331 tests 중 328 통과, 2 failures와 1 error.** 실패는 이 변경 외 Step 4 계열이다.
  - Step 4 post-freeze readiness: 현재 의존성 `numpy 2.4.6`, `pandas 3.0.3`, `networkx 3.6.1`이 동결 fingerprint와 불일치.
  - Step 4B4 mock raw-ledger hash 및 Step 4C1 production manifest hash: 저장 manifest의 기대 SHA와 현재 파일 SHA 불일치.
  - 위 frozen 자료와 manifest는 수정하지 않았다.

## Proposal 자원·재개 확인 범위

- 기본 구조 proposal generator를 TEST_ONLY 격리 worker에서 1건 실행했고, 제안 결과와 구조 적격성 상태를 체크포인트로 확인했다. 이 결과는 SCM 표본이 아니다.
- worker timeout 및 1-byte sampled RSS 상한 테스트에서 proposal 단계가 `RESOURCE_STOP`으로 기록되고 eligible admission 수가 0으로 남았다.
- 별도 OS 프로세스에서 proposal checkpoint 직후와 checkpoint 직전 저장 경계에서 coordinator를 종료한 뒤, 같은 run/config로 재개했다. Proposal ID·proposal payload·config hash가 uninterrupted 실행과 일치했고, 중복 checkpoint가 생기지 않았다.
- 중단 전 이미 완료된 proposal은 checksum 검증 후 재사용하며, 뒤 attempt 번호를 먼저 소비하지 않는다. SCM admission 단계는 proposal stage 완료 이후에만 호출한다.
- 자원 계측은 기존 Step 4 격리기의 **주기적 RSS 표본 측정**이다. OS 메모리 quota가 아니며, 디스크 여유/저장량은 쓰기 전 검사이지 파일시스템 quota가 아니다.
- active time은 proposal/SCM worker 실행 및 첫 결과 원자 커밋을 포함한다. coordinator 프로세스가 중단된 proposal attempt의 경과 구간은 보수적으로 active time에 합산한다. 시스템 외부 대기 시간 전체를 일관되게 잰 wall time과는 구분한다.

## 승인 Gate의 범위

positive 경로는 임시 디렉터리의 테스트용 config/manifest로 전체 schema·hash·runtime·cohort·RNG·resource 검증을 거친 후, 테스트 전용 dependency injection으로 고정 TEST_ONLY SCM 1개와 B=0의 17개 평가를 실행했다. 실제 USER_APPROVED bundle은 만들지 않았고, 실제 proposal/SCM 연구 코호트 실행 경로를 호출하지 않았다. 승인 상태가 없는 Production CLI와 manifest/config 충돌은 proposal 생성 전에 거부된다.

따라서 **실제 사용자 승인 bundle의 운영 검증은 승인 이후 남아 있는 절차**다. TEST_ONLY hook은 CLI 인자나 우회 플래그로 제공되지 않는다.

## 남은 승인·운영 사항

- A/B/C 과학적 계약 및 사전등록은 미승인이다. 제안된 topology/G0 분포, 지표·정규화·비용, 예산, UNRES 처리, N, resource limits를 사용자 승인 없이 실행 설정으로 확정하지 않았다.
- Production resource profile 수치는 TEST_ONLY 검증값이 아니다. 실제 연구 실행 전 승인된 config/manifest, 정확한 commit/tree와 환경 fingerprint가 필요하다.
- 전체 저장소 테스트의 Step 4 무결성/환경 실패는 별도 조사 대상이며, 동결 자료를 고쳐 해소하지 않았다. Research C 핵심 회귀군에서는 재현되지 않았다.

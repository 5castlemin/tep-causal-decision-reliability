# Research C Runner 3C — 구현 및 검증 기록

상태: **IN_PROGRESS**. 실제 Development/Held-out 코호트는 승인 설정이 없어 실행하지 않았다.

## 구현 경로

`run_research_mode()`의 승인 검증 뒤 다중 SCM orchestration을 연결했다. `build_approved_research_inputs()`는 고정 proposal cap까지 outcome-blind topology/task proposal을 만들고 구조 적격 SCM을 admission ordinal로 고정한다. 적격 SCM별 factory는 기존 SCM 계수·관측자료 생성기와 G0 generator를 사용한다. 이후 `run_cohort_orchestration()`은 TEST_ONLY와 승인 Research 실행을 별도 cohort type/SQLite ledger로 분리하고 동일한 `execute_fixture_input()` 및 policy/fit/recommend/analytic GT 평가 core를 호출한다.

연구 실행은 17개 정책과 B=0–4의 다섯 예산을 모두 기록한다. 같은 SCM 내 정책은 factory에서 생성된 하나의 G0와 관측자료를 공유한다. Proposal/admission 상태, 적격성 이유, SCM 체크섬, 결과 체크섬, 실패 상태와 자원 측정은 기존 SQLite ledger에 저장한다. Admission 뒤 실패는 대체하지 않는다. 개발과 독립 평가에는 기존 generator의 서로 다른 RNG namespace를 사용하며, admission ordinal로 delta를 교대한다.

승인 Gate는 config/manifest 승인 및 사전등록 상태, 실행 schema/manifest version, 모집단/SCM/task/G0/repair/evaluation 계약, target/proposal cap, 예산, RNG protocol, runtime fingerprint, resource profile, output root/run ID, config/contract/resource hashes, Git commit/tree와 runner code hashes를 확인한다. 연구 결과 출력 경로는 checkout 밖이어야 하며 TEST_ONLY ledger와 공유할 수 없다. 승인 config schema 후보는 `research_c_approved_execution.schema.json`이다. 승인 인스턴스는 생성하지 않았다.

## TEST_ONLY 검증

- 관련 단위·회귀 suite: 56개 통과.
- 공유 orchestration core의 고정 TEST_ONLY SCM 경로: 1 SCM, B=0에서 17개 평가 완료.
- 생성형 TEST_ONLY proposal 실행: 2 proposal (적격 1, 구조적 부적격 1), SCM 1개, 예산 0–4에 85개 평가 완료.
- 생성형 실행의 누적 worker 시간 0.672초, sampled RSS 69,992,448 bytes, ledger 356,352 bytes, 전체 출력 디렉터리 356,353 bytes. 설정은 TEST_ONLY 프로파일이며 생산 자원 상한 추정치가 아니다.
- Research CLI는 config/manifest 미제공 시 proposal 생성 전 `RESEARCH_MODE_BLOCKED`로 종료했다.
- 연구 proposal 입력 빌더는 주입된 고정 topology proposal로 admission/delta만 검증했으며 계수·관측자료·G0·SCM 적합·개입·Regret을 생성하지 않았다.
- 기존 fixture-contract validator, compileall, JSON syntax 및 `git diff --check` 통과.

## 아직 검증하지 않은 사항과 실행 차단

현재 작업에는 실제 사용자 승인 bundle이 없다. 따라서 승인 Gate의 양성 경로, 실제 연구형 proposal-to-ledger 실행, 64/200 목표 달성, 연구 결과 저장 및 재개는 실행하지 않았고 검증 완료로 표현하지 않는다. 계약의 과학적 선택도 승인 또는 사전등록되지 않았다.

Topology proposal 생성 루프는 고정된 proposal cap으로 유한하지만 SCM worker 시간 예산 밖에서 동기적으로 계산된다. Proposal별 별도 process timeout/checkpoint 및 proposal 단계 누적 시간 청구는 아직 없다. Runner 3B처럼 RSS는 sampled monitoring이며 filesystem 검사도 사전 검사이지 OS quota가 아니다. 이 차이를 해결하거나 운영 한계로 승인받기 전에는 기술적으로 안전한 실험 실행 준비가 완료됐다고 판정할 수 없다.

따라서 실제 cohort 진입은 계속 차단되어야 한다. 다음 단계는 승인된 A/B/C 계약 및 실행 설정/manifest 작성, proposal 단계 자원 처리의 보완 또는 명시적 한계 승인, 이후 실제 승인 bundle의 양성 Gate 검증이다. 새 연구 cohort는 이 작업에서 생성하지 않았다.

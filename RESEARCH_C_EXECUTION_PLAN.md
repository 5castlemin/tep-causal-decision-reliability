# 연구 C 실행 계획 및 Gate

**현재 상태: 계약 후보 작성 완료 / 실행 미승인.** 이 계획 작성은 SCM 생성, 계수·자료 추출, 정책별 SCM 실행, 개입 평가, Regret 계산이 아니다.

## 1. 현재 준비 상태

현재 `research/original_objective/policy_engine.py`는 명시 DAG에서 오류 사건·M1–M4·수정 후보·비용/예산 Greedy·DAG 제한·trajectory 기록을 계산한다. 독립 감사에서는 정책 엔진 테스트 17/17 및 기존 hand-fixture validator가 통과했다. 하지만 엔진은 SCM sampling, 공유 관측자료, fitted model, action recommendation, analytic GT outcome을 연결한 연구 C production runner가 아니다. `evaluation_record`는 GT outcome을 null로 남기는 인터페이스에 그친다.

따라서 현재 상태는 **정책 엔진 검토에 충분, 실험 실행에는 불충분**이다. 별도 생산 통합 및 계약 승인 Gate를 통과하기 전에는 후보·적격성 검사도 연구 SCM 생성으로 취급해 실행하지 않는다.

## 2. 권장 순서

### Gate 0 — 계약 승인 기록

사용자가 [사전등록 체크리스트](RESEARCH_C_PREREGISTRATION_CHECKLIST.md)의 결정 묶음 A–E를 승인/수정/거부한다. 특히 아래 세 항목은 다른 조건보다 먼저 필요하다.

1. **대상 SCM/task 모집단 및 G0 생성법:** 기존 frozen generator family를 새 RNG namespace로 재표집할지, 별도 corruption population을 만들지; task pair; G0 error-generation/learner와 오류 기회 법칙.
2. **정책·오류·비용 계약:** task zone 및 Rule A/B, official denominators, Greedy normalization/M3 proxy/M4 β, 허용 연산, 비용, λ, budgets.
3. **Outcome와 cohort 계약:** SCM-level estimands, GT evaluator/정보 firewall, 개발·독립 평가 split, 목표 N/precision, eligibility, caps/failures/shortfall.

승인된 정의를 결정 등록부와 버전 설정에 반영한다. 승인 전 상태표시는 `PROPOSED`/`OPEN`이다.

### Gate 1 — production integration (fixture-only)

새 SCM 없이 기존 고정 fixture 및 합성값 없는 deterministic test double로 다음을 구현·검증한다.

1. **Proposal/task/G0 contract:** 모집단·task·초기 graph 생성이 승인 설정과 RNG namespace를 바인딩한다. G0는 policy마다 공유되고 결과 기반 rejection/reseed가 없다.
2. **Shared SCM artifact interface:** 동일 SCM의 계수·잡음·관측자료를 한 번 생성/고정하고 모든 policies·budgets에 immutable input으로 전달한다. 같은 SCM의 결과는 SCM ID 아래 묶인다.
3. **Policy path:** 각 approved metric subset, S0, Canonical baseline을 같은 G0/task/cost/B에서 수행한다. 모든 stage는 input/config/code hash와 RNG binding을 기록한다.
4. **Learner/action path:** 학습기에는 graph와 공통 관측자료만 전달한다. 각 final graph의 fitted model, 예측 action loss, action candidate grid, selected action/k와 tie를 저장한다.
5. **Truth evaluator:** 별도 모듈이 GT SCM에서 동일 candidate action의 analytic loss, best loss, regret을 계산한다. Policy scheduler는 이 값에 접근하지 못한다.
6. **Decomposition:** `G0 → repaired graph → fitted prediction → selected action/k → GT loss → regret` link ID를 보존해 어느 연결에서 차이가 유지/소실됐는지 찾는다.
7. **Failures/denominators:** structural rejection, admitted SCM, generation failure, model failure, policy failure, incomplete policy vector, GT failure, complete regret vector, S0 pairing을 별도 분모로 남긴다. 실패는 0 대체·신규 SCM으로 대체 금지.
8. **Restart/resource integrity:** deterministic fixture에서 강제 종료·resume, same graph hash dedup, ledger/registry consistency, timeout/RSS/disk stop, 원시 파일 hash를 검증한다.

필수 테스트에는 same graph → same recommendation/loss, same action → same GT loss/regret, same shared observations, outcome firewall, one policy missing → no fabricated contrast, candidate tie/NaN/zero support, cost cap/DAG rejection, `P_S` vs `P_all`, policy-result hash binding이 포함된다.

### Gate 2 — 개발 cohort 64 (별도 실행 승인 필요)

Gate 0·1 및 clean runtime·manifest 검증이 통과되고 사용자가 SCM 실행을 별도 승인한 후에만 새 개발 표본을 생성한다. `development` 전용 cohort/RNG/ID/output root를 사용한다. 제안은 64 admissions이며 실제 proposal cap은 모집단·수율 진단에서 실행 전에 고정한다. 이 64는 자동으로 독립 평가에 합치지 않는다.

개발 cohort는 end-to-end failure·candidate support·유형/위치 커버리지·운영시간·SCM-level paired contrast의 분산을 평가한다. 정책이나 가중치 선택에 개발 Regret을 사용한다면 이후 평가 자료는 미열람 독립 표본으로 유지하고, 선택 절차를 기록한다. 개발 자료로 성능이 좋은 policy에 맞게 G0, weights, denominator, outcome을 바꾸지 않는다.

### Gate 3 — evaluation N 및 실행 설정을 사전 고정

평가 cohort seed/ID/RNG key 및 출력은 개발과 별도 namespace에 둔다. 평가 데이터를 만들거나 열기 전에 다음을 동결한다.

- 최종 설정 및 코드 hash / runtime fingerprint
- 목표 admissions N, proposal cap, 구조 적격성 및 post-admission 실패 분모
- 모든 주·민감도 시나리오와 budget grid
- analysis script와 estimand/sign convention
- 자원·중단·resume·shortfall rules
- 결과 열람 권한과 raw immutability

제안 evaluation `N=200`은 시작점이다. 개발 cohort에서 pre-specified primary contrasts의 SCM-level `s_max`와 사용자가 승인한 기술적 half-width `h`로 `N=ceil((1.96*s_max/h)^2)`를 계획 후보로 계산할 수 있다. 최종 N은 이 후보와 처리량·자원 비용 중 사전에 고른 규칙으로 확정하고, evaluation 열람 후 N 변경을 금지한다. `h` 승인 전에는 N=200을 최종 표본 계약으로 표시하지 않는다. 유의성 검정이나 우월성 주장의 power를 보장하는 식으로 해석하지 않는다.

### Gate 4 — 독립 evaluation cohort (별도 실행 승인 필요)

승인된 exact commit/tree, clean checkout, pinned runtime과 frozen config만 사용한다. `confirmation` 전용 namespace, seed, SCM ID와 출력 디렉터리를 사용한다. 개발 자료나 Step 5/6 표본과 ID/RNG/data overlap이 없어야 한다. 실행은 승인된 N, proposal cap 또는 안전 자원 상한 중 먼저 충족할 때 멈춘다. Shortfall은 보고하고 재-seed/추가 proposal로 조용히 대체하지 않는다.

## 3. 정책 run count와 처리량 추정

주 budget grid B=1,2,3,4에서 각 SCM당 16개 repair policies(15 subsets + Canonical Oracle)를 실행한다. S0를 같은 graph/data에서 1회 계산해 예산별 기준으로 연결하면 주 분석은 SCM당 최대 64 repaired policy-budget ledger cells 및 최대 65 unique final graph/model paths (16×4 + S0)이다. Graph hash 중복 시 재계산을 안전하게 줄일 수 있으나, 모든 policy-budget row는 독립 분석 단위가 아니라 SCM 안의 행으로 유지한다.

B=2 민감도 8개(one-at-a-time: normalization 1, FP rule 1, orientation cost 2, λ 2, β 2)를 모두 수행하면 SCM당 최대 128 추가 repaired graph/model paths와 136 ledger cells가 생긴다. 최대량은 개발 64에서 약 12,352 model paths, evaluation 200에서 약 38,600 model paths다(중복 graph dedup 이전). 이는 실행량 산술이지 실제 wall time 측정이 아니다.

따라서 Gate 1에서 기존 fixed fixture를 이용해 topology/task enumeration, SCM/data fixture handoff, Ridge fit, recommendation, analytic GT, JSONL/registry, resume를 각 단계별로 측정해야 한다. 64/200 대상에 대한 wall-time/disk extrapolation은 실제 측정된 단계 비용과 동일 처리량 가정으로만 작성하고, Step 4 runner timing을 C 전체 pipeline 측정치로 잘못 전용하지 않는다. Resource cap은 측정 후 승인하며 실행 실패는 보존한다.

## 4. 저장·보고 계획

연구용 실행이 별도 승인된 뒤에만 다음과 같은 별도 결과 위치를 만든다.

```text
research_runs/original_objective/development_v1/
research_runs/original_objective/evaluation_v1/
```

각 cohort에는 immutable raw ledger, SQLite admission registry, manifest, per-SCM/policy/budget result, failure inventory, hash inventory를 둔다. Evaluation raw data는 개발 브랜치로 가져오거나 개발 중 미리 열람하지 않는다.

예정 보고물은 execution report, SCM-level descriptive results, failure/denominator report, sensitivity report, reproducibility manifest다. 평균·중앙값·분포·SD·분위수·양/음/동률과 action/graph/Regret change decomposition을 기술적으로 제시한다. 높은 정책의 점수만 선별하거나 정책×SCM cell을 독립 N으로 취급하지 않는다.

## 5. 허용되지 않는 자동 확장

- old Step 5/6 데이터를 Research C evaluation으로 재사용하지 않는다.
- 결과를 본 뒤 seed, G0 corruption, task sampling, error rates, weights, β, λ, normalization, subset definitions, budget, sample N을 바꾸지 않는다.
- 모든 16개 명목 전략이 고유 graph를 만들었다고 가정하지 않는다.
- Canonical Oracle 또는 catalog 내 최선을 전역 최적/배포 정책으로 부르지 않는다.
- Oracle-assisted 결과를 현실적 error discovery 성능이나 실제 제조공정 효율·수율·안전 개선으로 해석하지 않는다.
- 본 계약안 작성으로 PREREGISTERED/FROZEN/실험 완료 표시를 하지 않는다.

## 6. 지금의 다음 한 단계

실제 SCM 생성 전에 필요한 다음 단계는 **묶음 A–E의 승인 회의/결정 기록**이다. 우선 모집단·task·G0 생성법(D 묶음)을 승인해야 하며, 여기서 정한 오류 기회 분포가 Greedy와 M4 비교의 의미를 결정한다. 승인 후에도 production integration과 고정 fixture 검증(Gate 1)을 먼저 완료하고, 개발 cohort는 별도의 명시적 실행 승인 뒤에만 시작한다.

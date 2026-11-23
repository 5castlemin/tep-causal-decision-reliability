# 연구 C 사전등록 전 체크리스트

**현재 지위: 계약안 검토 중 / NOT APPROVED / NOT FROZEN / NOT PREREGISTERED.**

이 체크리스트는 실제 실험 승인이 아니다. 승인 묶음의 모든 필수 항목을 기록하고, 코드·환경·분모·실패 규칙을 검증한 뒤 별도의 실행 승인으로 넘어간다.

## A. 사용자가 승인해야 하는 최소 결정 묶음

| 묶음 | 승인할 결정 | 현재 제안 | 승인 전 영향 |
|---|---|---|---|
| **A. task와 오류 모집단** | task-zone causal/backdoor 정의, conditioning, FP Rule A/B, official denominator | causal X→Y path + unconditional open backdoor; Rule A 주 분석, 사전 규칙 B 민감도; M1/M2/M3 분모와 M4 component supports 문서 정의 | task 오류 귀속과 분모, 평가 모집단이 바뀜 |
| **B. 수정 효용과 원자 연산** | 15 subset + S0, Greedy, fixed-opportunity, 동일 metric weights, active M4 β, UNRES 연산·tie | 현재 contract의 식; add/delete/orient/resolve만 허용, delete-UNRES/mark-UNRES 제외; M3 proxy REV+UNRES | 실제 수정 순위와 결과 graph가 바뀜 |
| **C. budget/penalty/outcome** | B grid, operation costs, λ 의미, UNRES 벌점, 주요 estimands | B=1,2,3,4; 기준 각 허용 수정 cost=1; orient/resolve 상대비용 2/3 민감도; λ는 task total multiplier; `P_all` event-level equal weights; paired SCM-level regret을 별도 평가 | feasibility, 정책 비교량, 목표 해석이 바뀜 |
| **D. target population과 표본** | SCM family, task pair sampling, G0 생성법/오류율, eligibility, proposal caps, cohort N 및 RNG | 개발 64, 독립 평가 200은 planning 후보일 뿐; 새 namespaces; old A/B data 미사용 | 대상 모집단 및 정책 기회 분포를 결정함. 현 문서에서 가장 큰 과학적 미결점 |
| **E. 실행·평가·분석 경계** | Ridge/recommendation/GT evaluator binding, failure denominator, analysis summary and stopping rules | common observation/action grid; GT outcomes selector 밖; incomplete policy result is missing/failure, never zero; descriptive SCM-level summaries, no superiority claim | production readiness와 재현성·주장 범위를 결정함 |

승인 기록은 각 묶음별로 `approve / revise / reject`와 버전 및 날짜를 남긴다. 문서 존재 자체를 승인으로 간주하지 않는다.

## B. D1–D19 상태 요약

`proposed default`는 검토용 주 분석 제안, `sensitivity`는 사전 지정 보조 축, `deferred`는 이번 연구 범위 밖, `unresolved`는 주 실험 전 결정을 더 해야 한다는 뜻이다. 어느 상태도 사용자 승인이나 동결을 의미하지 않는다.

| ID | 주제 | 현재 제안 상태 | 요약 |
|---|---|---|---|
| D1 | Causal task zone | proposed default | GT의 모든 X→Y 유향 경로 간선 합집합 |
| D2 | Backdoor 정의 | proposed default | 빈 조건화에서 X로 들어오는 열린 단순 경로; 대안 conditioning set은 deferred |
| D3 | FP task 귀속 | proposed default | Rule A 주 분석; Rule B 사전 route test는 sensitivity |
| D4 | M1/M2 denominator | proposed default | M1 GT 비과제 adjacency support; M2 G0 추정 비과제 adjacency support; M2 비율 변화만으로 gain 금지 |
| D5 | M3 보고 | proposed default | 조건부 방향 정확도와 unresolved 수/rate 동시 보고; count/support 병기 |
| D6 | M4 | proposed default | FN/FP/REV/UNRES vector 및 component support 유지 |
| D7 | Shared Greedy utility | proposed default | 실제 사건 감소/비용, selected metric 동일 가중, M3 residual REV+UNRES |
| D8 | Scheduler 비교 | proposed default | Shared Greedy와 Canonical Oracle; equal quota는 deferred |
| D9 | Cost schedule | proposed default | 허용 edit 단가 1; orient/resolve 2/3는 sensitivity; delete-UNRES는 deferred/excluded |
| D10 | `P_all` | proposed default | 유형별 사건 벌점 1회, UNRES 명시, task total multiplier λ |
| D11 | event weights | proposed default | FN/FP/REV/UNRES 각각 1의 기준 시나리오; 실증 산업 비용 아님 |
| D12 | ρ cost–penalty tradeoff | deferred | 주 실험에서 사용하지 않음 |
| D13 | Policy catalog comparison | proposed default | 15 subset + S0 + 별도 Canonical Oracle; catalog 최선만 보고, global optimum claim 금지 |
| D14 | Information access | proposed default | Oracle-assisted structural diagnostic; deployable non-oracle 방법은 deferred |
| D15 | Cohort separation / sample | unresolved | 개발/평가 namespace 분리는 제안; G0/population law, exact N/cap은 승인 필요 |
| D16 | Outcome link | proposed default | 별도 GT evaluator의 Decision Regret, 구조 벌점과 동치 가정 없음 |
| D17 | Normalization | proposed default + sensitivity | G0-fixed opportunity 주 분석; initial-error-count at B=2 sensitivity |
| D18 | M4 β | proposed default + sensitivity | active components equal; FN×2 및 UNRES×2 stress sensitivity |
| D19 | Candidate scheduling | proposed default; production gate open | 매 적용 뒤 실제 event/gain/cost/DAG 재계산; end-to-end SCM→Regret adapter 검증은 미완료 |

## C. 사전등록 전에 기술적으로 완료할 항목

### 정책 계산 재현성

- [x] 엔진 단위 및 결정적 손그래프 테스트를 작성·실행했다 (audit report 참조).
- [ ] 주 설정값을 버전된 JSON/YAML 설정 파일로 기록하고 파일 hash를 저장한다.
- [ ] Rule B의 GT+단일 FP path 판정 및 UNRES-FP 양방향 규칙을 구현·손계산 테스트한다.
- [ ] `delete_unresolved` 제외와 M4→FN 등 상태전이를 production policy contract에 반영한다.
- [ ] Greedy 결과와 수정 후 지표·candidate count·cost·unused budget·stop reason이 일관된 versioned ledger에 남는지 검사한다.
- [ ] 각 policy×budget에서 graph hash deduplication을 결과 링크로 하며, 공유한 모델/예측을 독립 계산처럼 세지 않는지 확인한다.

### End-to-end evaluator 연결

- [ ] GT DAG 구조가 policy 후보 생성에 필요한 최소 정보로만 전달된다.
- [ ] GT 계수, 개입 평균, 후보 행동별 truth loss, regret은 추천/selection/scheduler API에서 접근할 수 없음을 부정 테스트로 확인한다.
- [ ] 같은 SCM의 관측자료 1세트를 모든 policy·budget에 공유한다.
- [ ] 동일 최종 graph와 동일 입력은 Ridge/recommendation 결과가 동일해야 한다.
- [ ] GT evaluator는 예측 모델과 독립적으로 같은 action candidate grid의 analytic loss를 계산한다.
- [ ] 추천 action, predicted action loss, GT chosen loss, GT best loss, regret, S0 대비 paired change가 단계별로 기록된다.
- [ ] 하나라도 필수 policy result가 실패/비유한/누락이면 0 대체 없이 missing/failure로 보존한다. SCM-level composite denominator를 사전 고정한다.

### 모집단, 표본, 운영

- [ ] G0를 얻는 방법 및 오류 주입/학습기, 오류율, 후보 수 생성 법칙을 고정한다.
- [ ] action–target pair sampling 및 direct/indirect/backdoor 구조의 포함 범위를 고정한다.
- [ ] 개발 64/평가 200 candidate와 추가 N 결정식 또는 정밀도 목표를 승인받는다.
- [ ] eligibility, structural rejection, post-admission failure, proposal cap, shortfall, 시간·메모리·디스크 중단 규칙을 고정한다.
- [ ] 개발·평가 RNG namespace, seed custody, output roots, ledger backup 및 raw immutability 절차를 문서화한다.
- [ ] evaluation 열람 전 exact analysis script, tables, failure denominators 및 sensitivity set을 해시·동결한다.

## D. 표본 및 분석 규칙 후보

독립 SCM 단위는 유지한다. 각 SCM에 대해 모든 정책·예산 간 paired regret을 산출한다. 주 표에는 각 정책×budget의 mean, median, SD, IQR, min/max, sign counts, completeness/failure denominator, unique final graph count, action/k change rate, total cost 및 unused budget을 포함한다.

계약안의 N candidate `64 development / 200 evaluation`은 운영 규모 비교를 위한 시작점이다. 기존 Step 5/6은 모집단·정책·estimand가 달라 새로운 연구의 independent results로 병합하거나 holdout으로 재사용하지 않는다. Step 6의 SD 0.0824에서 계산한 근사 폭은 오직 산술 시나리오이며 새 연구의 분산 추정치가 아니다.

확인적 superiority/equivalence claim은 이번 후보 계약에서 제안하지 않는다. 15개 subset×4 budgets와 sensitivity는 많은 대조를 만든다. “가장 낮은 관측 mean”은 사전 지정한 catalog 내 기술적 최선이라고만 말하고, 이후 confirmatory study가 필요하다면 개발 결과를 본 뒤 새로 사전등록한다. Multiple comparison p-value로 후보를 골라 주 연구 결론으로 승격하는 것은 금지한다.

## E. 별도 유산 테스트 이슈 및 본 실험 차단 요인

### 연구 C 결함이 아닌 기존 이슈

1. **Step 4B4 원장 SHA 검사:** `research/budget_aware_refinement/step4b4_mock_pipeline_run_v2.jsonl`의 Git blob bytes(1,408 bytes) SHA `9c12a2…`는 `step4b4_final_gate_manifest.json`과 일치한다. Windows checkout은 LF 5개를 CRLF로 변환해 raw `read_bytes()` hash가 `e8a1c6…`가 되지만 LF 정규화하면 Git blob과 동일하다. 동결 원시자료 변경은 확인되지 않았고, `tests/test_step4b4_mock_runner.py::test_final_gate_manifest_matches_mock_sources_and_raw_ledger`의 줄바꿈 처리 문제다.
2. **Step 4C1 manifest 검사:** `tests/test_step4c1_production.py::test_production_manifest_hashes_match_artifacts`에서 CRLF 정규화 후 `WORK_LOG.md`의 실제 hash `351869…`가 `research/budget_aware_refinement/step4c1_production_manifest.json`의 `NOT_FROZEN` 후보 기대 `608efe…`와 다르다. 이는 줄바꿈 문제가 아닌 stale manifest 내용이며 연구 C 코드의 실패가 아니다.
3. **Production readiness clean tree:** `tests/test_step4_post_freeze_readiness.py::test_exact_clean_revision_passes_production_readiness_without_generating_data`는 `research/budget_aware_refinement/step4c2_freeze.py::assert_production_ready`의 clean-tree 조건 때문에 dirty main checkout에서 오류가 났다. 사용자가 보존하도록 한 `.build_reframed/`와 audit edits가 원인이었다. 정확한 기준 커밋의 detached clean worktree에서 같은 readiness positive test 1/1 통과했다. 임시 worktree는 제거했다. 실제 실행 때도 clean isolated checkout을 사용해야 한다.

### 새로운 SCM 실험의 실제 차단 요인

현재의 주 차단은 이 세 유산 테스트 문제가 아니라 **연구 C target population와 G0/error-generation law 미승인**, **policy engine과 SCM fit/recommendation/analytic GT evaluator 간 미검증 production integration**, **표본 N/eligibility/cap/failure denominator 미고정**이다. 이 조건이 충족되기 전에는 연구용 SCM을 생성하지 않는다.

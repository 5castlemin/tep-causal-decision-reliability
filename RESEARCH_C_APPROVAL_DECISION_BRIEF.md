# Research C — A/B/C 최종 과학적 계약 검토 및 승인 브리프

**정합화 기준:** 이번 변경을 담는 로컬 커밋으로 갱신 예정.
**상태:** A2, P1, 계층 Task 추출 및 잔여 A/B/C 계약·§10.4 Production 자원 상한 권고값은 사용자가 승인했다. 내부 계약 설정은 반영·고정했으며, 실제 Development 실행은 별도 승인 전까지 금지된다.
**범위:** 계층 Task 계약에 맞춰 Schema·Validator와 승인 문서를 정합화하고 TEST_ONLY 회귀를 검증했다. 새 SCM, 관측자료, 개입 결과 또는 연구 Regret은 만들지 않았다.

이번 정합화는 앞선 A2 모집단·P1 primary·계층 Task 승인과 2026-11-23 사용자의 잔여 A/B/C 계약 및 Production 자원 상한 승인을 반영한다. 과학적 계약은 승인됐고, 실제 Development 실행은 별도 승인 전이다. 연구 코호트나 Regret은 생성하지 않았다. 상태는 **CONTRACT_APPROVED / CONFIGURATION_AND_PREFLIGHT_PENDING / EXECUTION_NOT_AUTHORIZED**다.

## 1. 연구 질문과 현재 증거

**연구 C 질문:** 제한된 수정 비용 안에서 불완전한 인과그래프의 어떤 오류 유형과 위치를 먼저 고치면, 수정 그래프로 선택한 조작의 정답 환경 Decision Regret이 낮아지는가?

SCM은 변수 사이의 구조적 인과관계를 나타내는 모형이다. 연구 C의 WHAT은 정답 DAG를 참조해 M1–M4 오류를 분류하고 수정 후보를 만드는 일, HOW는 선택된 지표 조합의 구조 부담 감소량/수정 비용을 탐욕적으로 적용하는 일, EVALUATION은 수정 그래프에서 공통 관측자료로 SCM을 적합하고 추천을 확정한 뒤 별도 GT 평가기에서 Regret을 계산하는 일이다.

검증된 것은 정책 엔진, 생성·평가 경로, ledger/재개와 자원 감시의 결정적 TEST_ONLY 검증이다. 실제 새 Research C 개발 또는 독립 평가 SCM 코호트, 정책별 연구 Regret 결과, 정책 우월성은 아직 없다. `TECHNICALLY_READY_FOR_APPROVAL`은 운영 코드 검토 판정일 뿐 과학적 계약 승인이나 연구 실행 승인이 아니다.

## 2. 기존 세 실패의 재현 및 영향

아래 세 테스트만 재실행했다. **모두 동일하게 실패했다.** 어떤 동결 데이터·manifest·기대 SHA도 수정하지 않았다.

| 실패 테스트 | 기대와 실제 | 원인 판정 | Research C 영향 |
|---|---|---|---|
| `tests.test_step4_post_freeze_readiness.PostFreezeReadinessTests.test_exact_clean_revision_passes_production_readiness_without_generating_data` (ERROR) | 고정 fingerprint와 달리 실제 NumPy `2.4.6` (기대 `2.4.3`), pandas `3.0.3` (기대 `3.0.1`), NetworkX `3.6.1` (일치) | **환경·의존성 차이.** Step 4 고정 readiness 검사가 현재 Python 환경을 거부함. 저장소 파일 변경 징후는 없음. | 연구 C 계산 자체의 실패 증거는 아니다. 다만 Research C 승인 bundle은 실행환경 fingerprint를 묶으므로, 승인할 환경과 실제 runtime을 일치시키기 전 실제 코호트를 실행할 수 없다. 지정된 의존성 환경에서 재검증해야 한다. |
| `tests.test_step4b4_mock_runner.Step4B4MockRunnerTests.test_final_gate_manifest_matches_mock_sources_and_raw_ledger` (FAIL) | raw ledger manifest 기대 `9c12a2b9d7d8fe15b886783be9f53b0486d137a742c467d0f00b653b62905c21`; 현재 Windows 파일 바이트 `e8a1c6144d1c40351469754d16b956647ce9e812dea64ebca84f8dd5f18c783a` | **환경/개행 재현성 경고.** 검사는 raw bytes를 해시한다. Git에 저장된 객체는 expected SHA와 일치하고 worktree는 clean이며, checkout CRLF가 물리 바이트 SHA를 바꾼다. | Step 4B4 mock raw ledger에 한정된 검증 불일치. Research C 입력 또는 결과를 검증하는 테스트가 아니며, manifest나 원시 파일은 손대지 않는다. |
| `tests.test_step4c1_production.Step4C1ProductionIntegrationTests.test_production_manifest_hashes_match_artifacts` (FAIL) | `WORK_LOG.md`의 Step4C1 manifest 기대 정규화 SHA `608efe6ad1619267aae66e0d90dcdef39dc5ff057880bad288bfe534740ad6f1`; 현재 정규화 SHA `351869ebe1af9893cc6b149ded13cc0e972a18659eb9510dec1553e317ea7d7d` | **기존 비동결 개발 manifest의 stale binding.** 해당 기대값은 Step4C1 시점 WORK_LOG와 맞았고, 이후 작업 기록이 추가됐다. 해당 manifest는 `NOT_FROZEN`; Step4C2 최종 동결 manifest가 아니다. | Research C 파이프라인과 격리되어 있다. Step4C1 개발 manifest를 현재 최종 frozen 계약으로 오인하지 않는다. |

테스트 명령:

```powershell
python -m unittest tests.test_step4_post_freeze_readiness.PostFreezeReadinessTests.test_exact_clean_revision_passes_production_readiness_without_generating_data tests.test_step4b4_mock_runner.Step4B4MockRunnerTests.test_final_gate_manifest_matches_mock_sources_and_raw_ledger tests.test_step4c1_production.Step4C1ProductionIntegrationTests.test_production_manifest_hashes_match_artifacts -v
```

이전 전체 실행은 331개 중 328개 통과, 이 3개 실패/오류였다. 이번 작업에서 전체 331개를 다시 돌린 것은 아니다. 동결 무결성에 영향을 주는 미해결 오류는 현재 조사 증거상 확인되지 않았으나, 실행환경 fingerprint 차이는 Research C 실행환경이 정해지기 전까지 실질적인 사전 실행 조건이다.

## 3. A — 모집단 및 G0 계약

| 결정 항목 | 제안/코드에서 확인한 값 | 근거 및 한계 | 권고 |
|---|---|---|---|
| Topology·크기 | 4종: chain mediation, fork branch, observed common cause, multiple directed paths; 노드 6–10; density `[0.2, 0.4]` | 승인 schema가 상수로 제한. 기존 Step4 topology generator 재사용은 새 SCM 데이터가 아니라 생성 규칙 재사용임. 네 template의 의미와 구현을 사전등록 부록에 고정할 것. | 승인됨 |
| Task 추출 분포 | 각 proposal의 `(cohort, master_seed, proposal_id, counter)` 기반 SHA-256 digest를 rejection 방식으로 고정된 20개 topology×node-count strata에 결정적으로 매핑한다. 같은 입력은 같은 층을 재현하며, 해시 출력의 modulo bias를 피한다. 순환 배정은 아니다. 그 stratum에서 topology·relabel 후 strict indirect-only ordered pair를 선택하고 direct `X→Y`는 제외한다. | 이는 계층 추출이지 전역 eligible `(X,Y)` pair-uniform이 아니다. 일반 topology는 topology 내부 후보를 seeded uniform index로 고르고, `observed_common_cause`의 scaffold action-target pair가 strict indirect-only이면 우선한다. Stratum별 적격률·후보 수와 preferred 예외, admission conditioning 때문에 admitted task/stratum 분포는 달라질 수 있다. | **계층 Task 분포 승인됨.** 기타 A/G0 계약은 2026-11-23 승인 기록 참조. |
| **추가 Q-common support gate — A2 반영** | Research C proposal wrapper가 기존 frozen proposal generator의 `missing_same_type_two_candidate_support`만 C 전용으로 승격하고 `q_common_eligible=false`, recipe counts를 보존한다. 구조적으로 strict indirect-only task가 없는 proposal은 계속 거절한다. | 모집단은 오류별 recipe availability가 모두 있는 구조에 조건화되지 않는다. 500→494 파일럿은 다른 기존 builder 조건을 사용한 구조 진단이며 A2 production admission 비율 추정치가 아니다. Q-common 결과는 secondary subset 분석 플래그다. | **A2 및 잔여 모집단 규칙은 2026-11-23 승인됨.** |
| SCM 구조·계수 | signed linear acyclic; 계수 절댓값 `[0.25,0.8]`, 독립 fair sign | 설정은 제안 상수. 이 합성 family 밖 제조 공정으로 일반화 불가. | 승인됨 |
| 관측자료·잡음 | SCM당 공통 관측자료 `n=512`; 독립 centered Gaussian noise, SD `[0.8,1.2]`; 정책별 동일 관측자료 | 계수/잡음/표본 생성용 RNG를 분리하고 seed namespace 기록. `n=512`는 효과 추정 정밀도를 보장한 근거가 아님. | 승인됨 |
| 행동·목표·손실 | 사전 선택 task, action grid `[-1,-.5,0,.5,1]`; standardized target mean squared error; GT 평가는 analytic hard-do | 동일 action grid와 손실을 전 정책에 적용. 실제 수율·안전·비용 함수가 아님. | 승인됨 |
| G0 오류 주입 | 참 adjacency 손상 `q=.15`, 손상 시 FN/REV/UNRES 각 1/3; GT nonadjacent pair FP 제안 `r=.05`, 방향 무작위 | q/r은 제안 확률이지 실현 오류율이 아님. 구조 전용 파일럿의 494 strict-task eligible 중 오류 없는 G0 55 (11.1%); 이는 Q-common 추가 적격성을 통과한 생산 모집단의 비율이 아님. 오류 제안 1,190 중 DAG 수락 1,044·거절 146. | 오류 생성 규칙 승인됨 |
| DAG 거절·재추출 | DAG-invalid 오류 제안은 기록 후 거절, 재추출 없음 | 파일럿과 schema 제안이 일치. proposal 수와 accepted/rejected를 모두 분모와 함께 보존. | 승인됨 |
| Task zone·backdoor | 모든 X→Y 단순 유향 경로와 무조건화 상태의 open backdoor 경로; collider 내부 노드가 없는 backdoor만 open. Rule A FP 귀속 | 경로 기반 구조 표식은 실제 개입 손실 자체가 아님. 무조건화 backdoor 한정이며 특정 조건화 집합은 다루지 않음. Rule A는 양 끝점 모두 task-zone node set 내 FP를 task로 태깅하여 내부 chord를 넓게 포함할 수 있음. | Rule A 승인; Rule B는 이번 범위에서 제외 |
| 오류 없는 G0·표본 흐름 | A2에 따라 G0 오류 0건도 admitted 모집단에서 제외하지 않음. Proposal, strict-task, Q-common 플래그, admitted, full-policy-complete SCM을 구분 | zero-error G0는 TEST_ONLY 전체 17개 정책이 비용 0으로 적합·추천·GT 평가까지 완료했다. 무오류 여부나 결과로 사후 제외하지 않음. | **승인됨** |
| Cohort | Development / `independent_evaluation`(표시상 held-out); 별도 seed namespace·ledger·output; 권고 N=64/200 admitted SCM, cap 386/1,104 | Schema에는 `independent_evaluation`, generator는 proposal namespace로 `confirmation` 사용. 외부 이름과 내부 RNG binding의 매핑을 Manifest에서 고정해야 함. N은 power 보장이 아님. | 분리·N/cap 승인됨 |
| 모집단 분모 | `target_admissions`는 구조 적격 proposal 목표. 완료 SCM/완전 paired SCM 수를 뜻하지 않는다. `proposal_cap`까지 outcome-blind proposal을 진행하고 미달 shortfall은 보존. | Admission 후 정책 평가 실패는 다른 SCM으로 교체하지 않음. 실패율과 완전 평가 분모를 분리한다. generator 상한은 development 386, confirmation 1,104 proposal attempts. | 분모·cap 규칙 승인됨 |

파일럿의 포화 진단에서 B=3/4 후보 선소진은 각각 87.6%/94.7%였으므로 이를 주 성능 예산으로 두기보다 포화 기술 결과로 보는 것이 타당하다. 권고는 B=2 주 비교, B=1 저예산 보조, B=3/4 후보 포화 기술 진단, B=0 S0 기준선이다.

## 4. B — 오류 수정 정책 및 비용

| 항목 | 구현·제안 계약 | 권고 및 해석 제한 |
|---|---|---|
| 원 지표 | M1 비과제 FN / 비과제 참 adjacency support. M2 비과제 FP / 추정 비과제 adjacency. M3 비과제 참 adjacency의 방향 정확도와 unresolved rate를 각각 보고. M4 task-zone FN/FP/REV/UNRES 벡터와 component support를 보존. | 공식 분자·분모/count는 policy utility와 별도로 기록. 분모 0은 NA. M2 분모만 늘어난 비율 하락과 REV→UNRES만으로 M3 정확도 수치가 오르는 현상은 repair gain으로 인정하지 않음. |
| 16개 조합 | S0 무수정 + M1–M4 비공집합 부분집합 15개 | 이 전략군은 어떤 지표 subset에 repair 후보를 제한하는지 나타냄. 명목 16개가 서로 다른 그래프를 보장하지 않음. |
| Canonical Oracle | 지표 gain 순위가 아닌 고정 canonical 순서로 같은 structural candidate pool을 수정; 같은 GT 구조정보·G0·비용·예산·DAG 제약 | 구조 라벨을 이용하는 oracle 진단 기준선. GT 계수·행동별 손실·최선 GT action·Regret은 쓰지 않음. 전역 최적해, regret upper bound, 배포 정책이 아님. |
| Greedy | 매 단계 `(P_S(before)-P_S(after))/edit_cost`; 실제 오류 사건이 사라지는 gain만 인정; 매 수정 뒤 후보·DAG·비용 재계산; deterministic tie order | Myopic 구조 대리목적의 탐욕 정책이며 `P_S` 전역 최소화나 최소 Regret을 보장하지 않음. 정답 DAG로 후보를 찾는 Oracle-assisted 진단임. |
| 정규화·가중치 | G0-fixed opportunity 분모, subset 내 지표 동일 가중, M4의 G0 active FN/FP/REV/UNRES components 동일 β | 작은 support는 사건당 상대 gain을 키울 수 있다. 파일럿과 별도 민감도 없이는 공정성/중립성 보장으로 표현 금지. 초기-error-count 대체 정규화는 이번 승인 범위에서 제외되어 실행하지 않는다. |
| 비용·벌점 | `C≤B`; add/delete/orient/resolve 각각 1 상대 비용. `P_all=Σ_r w_r(E_off,r+λE_task,r)`, 모든 `w=1`, `λ=1`은 task 사건에 주는 총 배수(누적 `1+λ` 아님). `P_S`와 `P_all`, Decision Regret 별개. | 단위는 연구상 상대 자원이며 원화/제조 비용 추정이 아니다. `λ=1`은 task/off-task 동일 벌점. 비용과 벌점 같은 수정에 중복 부과 금지. |
| 미확정 간선 수정 | 제안 허용은 true-edge add, FP delete, REV orient, UNRES resolve. `delete_unresolved` 키는 `Config`의 호환성 검증값으로만 요구됨. | 후보 생성 함수는 FN→add, FP→delete, REV→orient, UNRES→resolve만 만든다. `delete_unresolved`는 candidate pool에 나오지 않고, 우선순위·실제 지출 비용·정책 결과에 사용되지 않는다. 두 Schema에 이를 **비활성 예약 키**로 명시했다. 주 계약의 수정 연산은 바꾸지 않았다. |
| 예산 | 현재 runner/schema는 `[0,1,2,3,4]` 전체를 실행한다. 분석 역할은 B=0 S0/reference, B=1 보조, B=2 주 후보, B=3/4 포화 진단이다. | 이는 모순이 아니다. Schema 설명을 보완했다. Runner는 예산별 결과를 실행·저장하고 통계 contrast를 계산하지 않는다. 그러므로 분석 역할은 승인된 분석 계약/사전등록에 고정해야 한다. |

정답 그래프 접근은 Oracle-assisted 구조 후보 식별에 한정한다. 학습·추천에 허용된 입력은 공통 관측자료와 정책별 repaired graph다. 추천 행동을 고정한 다음에만 GT analytic evaluator가 실제 손실과 최선 action을 계산한다. 이 firewall이 실제 구현된다고 현재 기술 Gate 보고서와 runner 경로가 주장하지만, 실제 코호트에서의 무누출은 아직 실행 검증 전이다.

## 5. C — 평가·UNRES·통계·실패

**P1 승인 반영:** SCM별 B=2에서 S0와 Full Greedy(`M1+M2+M3+M4`)의 paired Regret 차이를 둔다. `delta_i = R_i(S0, B=2) − R_i(Full Greedy, B=2)`로 정의해, **양수일수록 Full Greedy의 Regret이 낮다.** 목표 모집단은 모든 A2-admitted SCM이고, 계산 가능한 Primary 표본은 두 정책이 모두 성공한 complete-pair SCM이다. Primary 효과량은 그 complete pairs의 평균이다. Runner는 SCM별 차이만 기록하고 cohort 평균을 계산하지 않는다. S0는 수정하지 않으므로 같은 SCM에서 B=0과 B=2의 최종 그래프·Regret이 같아야 한다. 고정 TEST_ONLY 입력에서 이 불변 조건을 확인했다. 실패·결측 때문에 complete-pair 평균이 admitted 모집단 평균과 다를 수 있으므로 무조건 일반화하지 않는다.

**Canonical Oracle 비교는 secondary**로 둔다: `D_i = R_i(Full Greedy,B=2) − R_i(Canonical,B=2)`이며 음수는 Full Greedy에 낮은 Regret이다. 이 기준선은 고정 canonical 순서의 구조 수정이지 GT 손실을 보는 전역 최적/Regret 상한선이 아니다. 계약 V1의 기존 일반 정책 대 S0 비교를 바꾸지 않고, 승인된 P1은 해당 대비의 primary 정책·예산·부호를 지정한다. P1은 수정 없음 대비 전체 지표 Greedy 구조 수정의 효과를 묻고, Full Greedy–Canonical은 oracle-assisted 구조 순서 기준선과 비교하는 secondary 질문이다. 15 subset의 결과를 보고 primary를 바꾸지 않는다.

Primary 추정 표본은 S0/B2와 Full Greedy/B2가 모두 정상 평가된 complete-pair SCM이다. 목표 모집단은 모든 A2-admitted SCM이지만, complete-case 평균은 실패가 없거나 적절한 결측 가정이 성립한다는 근거 없이 그 전체 모집단 평균으로 일반화하지 않는다. 정책별·실패 원인별 평가율을 admitted 분모와 함께 보고한다. Incomplete pair는 0으로 대체하지 않고, 성능을 본 뒤 재추출하지 않는다.

N은 Development admitted 목표 64, Held-out admitted 목표 200으로 고정하는 안을 권고하며 proposal cap 386/1,104를 사용한다. 이는 표본 목표이지 power·정밀도 보장이 아니다. 기존 계획의 development `s_max/h` 기반 자동 증액 아이디어는 역사적 계획으로 남기되 이번 권고에서는 **사용하지 않는다**. Step5/6 SD를 C의 분산 추정에 전용하지 않는다.

최종 권고는 95% SCM-paired t 신뢰구간과 보조 SCM-level paired percentile bootstrap 10,000회(2.5/97.5 percentile CI)다. Bootstrap seed와 분석 코드 버전은 Held-out 결과 열람 전에 고정한다. 정책·예산 행을 따로 재표집하지 않는다. 통계 계약은 승인됐다. 실제 cohort 통계량은 아직 계산하지 않았다.

| C 결정 | 제안/코드 상태 | 승인 권고 |
|---|---|---|
| 잔여 UNRES | 구조 그래프에는 UNRES 유지; 학습 DAG에서는 방향 부모/자식으로 쓰지 않는 abstention encoding. GT 방향으로 채우지 않고 무료 구조 복구로 세지 않음. | 승인된 주 처리. 정보 손실로 인해 UNRES 보유 정책에 학습 불이익 가능성을 한계로 기록; 대체 encoding은 별도 승인 전 수행하지 않음. |
| 결과·표본 단위 | 독립 SCM; 같은 SCM 내 정책/예산은 반복 측정. P1은 B2 `S0−Full Greedy` SCM paired difference의 평균. Full Greedy vs Canonical은 secondary. B1 보조, B3/B4 포화, B0 기준. | **P1 승인됨.** Primary 대상은 A2 admitted SCM이고 추정 표본은 두 정책이 모두 성공한 complete pair다. Complete-case mean을 실패 가정 없이 전체 admitted 모집단 평균으로 해석하지 않는다. |
| 개발/평가 N | Development 64, Held-out 200 admitted 목표; proposal cap 386/1,104. 과거 `s_max/h` precision 기반 자동 증액은 이번 권고에서 쓰지 않음. | N은 고정 목표이지 power/precision 보장이 아니다. Complete pairs, 실패율과 사유를 따로 보고하고 cap shortfall은 유지한다. Held-out 열람 뒤 N·정책·Primary 변경 금지. |
| 실패·complete-case | Proposal/admission/전 정책 완료/paired 벡터 수 각각 보존. 정책 일부 실패 SCM은 paired 주 비교에서 제외하되 전체 제안 분모와 원인별 실패율 보고. 실패 Regret=0 대체 금지, admitted SCM 사후 대체 금지. | 승인됨. 실패가 정책 의존적이면 complete-case 선택편향 위험을 결과 한계로 평가; 평가 실패율 차이가 심각하면 효과 결론을 보류. |
| 추정·불확실성 | Runner는 row 기록만 한다. 권고 N=64/200 admitted 목표와 cap 386/1,104를 사전 고정하고 `s_max/h` 자동 증액은 사용하지 않는다. Primary 95% paired-t CI; 보조 SCM-level paired percentile bootstrap 10,000회. | Complete-pair mean은 두 정책 모두 성공한 SCM에 한정하며 admitted 모집단 평균으로 자동 일반화하지 않는다. 실패율은 정책/원인별 보고. Bootstrap seed와 분석 코드 버전은 Held-out 결과 열람 전 고정. N은 power 보장이 아니다. |
| 환경·실행 승인 | 격리 Windows CPython 3.11.15, NumPy 2.4.3, pandas 3.0.1, NetworkX 3.6.1, jsonschema 4.26.0. `research_c_runtime_lock.txt`에 pip 포함 전체 설치 패키지 버전을 고정. | 이 환경에서 Research C 테스트/fixture가 통과했다. 승인 설정은 실제 실행할 동일 runtime fingerprint와 전체 package inventory에 묶어야 한다. |
| Gate·운영 | Runner가 JSON Schema, 승인 상태, 지원된 과학 설정, proposal/admission 수, budgets, runtime, hashes, output·resource limits를 검사한다. RSS는 sampled monitor, 저장량은 파일시스템 quota가 아닌 사전 검사. | `--mode preflight`는 같은 승인/Manifest Gate를 검증하고 proposal/SCM 없이 종료한다. `scripts/prepare_research_c_manifest.py`는 **이미 사용자 승인 및 사전등록된 config**의 해시 manifest만 바인딩한다. 도구 실행은 승인을 생성하지 않으며 이번 승인으로 Configuration·Manifest를 생성하고 비실행 Preflight까지 수행한다. 도구는 승인을 발급하지 않는다. `PREREGISTERED`는 저장소 내부 사전 고정 상태이며 외부 공개 registry 등록을 뜻하지 않는다. |

### 표본 크기와 자원

64/200은 승인된 admitted 실행 목표이지 최소 검정력이나 정밀도 보증이 아니다. 기존 계약은 Step5/6 paired SD 0.0824를 단순 대입한 숫자를 참고로만 제시하며, C의 분산에 적용된다고 주장하지 않는다. runner의 계획 workload는 예산 전체에서 SCM당 최대 65개 고유 graph/model 경로 전후(중복 그래프는 캐시·공유 가능)이고, 실제 시간은 topology 적격률, 오류 후보, 적합 실패와 민감도 수에 따라 달라진다. 생산 상한은 사용자 승인 runtime에서 먼저 작은 승인된 개발 실행의 계측을 본 후 고정해야 한다; 이 기술 검토만으로 N=200의 완료 가능성/통계력은 확정 못 한다.

## 6. 승인 반영 및 별도 실행 Gate

사용자는 2026-11-23에 A2, P1, 계층 Task 추출 및 아래 표의 잔여 과학적·운영 설정을 승인했다. Rule B 및 대체 정규화 민감도는 승인 범위에서 제외했다. 이 승인은 계약 확정만 뜻하며 실제 Development 실행은 승인하지 않는다.

| 묶음 | 권고 선택 | 사용자 응답 |
|---|---|---|
| **A — 모집단/G0** | strict indirect-only, A2; topology 4종·노드 6–10; signed linear SCM; G0 q=.15/r=.05, FN/REV/UNRES conditional 1/3; Development 64/cap386, Held-out 200/cap1104 | **APPROVED — 2026-11-23 사용자 승인.** |
| **B — 정책/비용** | Rule A + 열린 무조건화 backdoor task zone, S0+15 subsets+Canonical, G0-fixed opportunity only; Rule B·대체 정규화 제외, 동일 subset metric weights 및 M4 active-component β, 단위 비용/λ=1, B2 primary·B1 보조·B3/4 saturation·B0 reference | **APPROVED — 2026-11-23 사용자 승인** |
| **C — 평가/운영** | P1 B2 `S0 − Full Greedy`; 95% paired-t CI + paired bootstrap 10,000; no `s_max/h` increase; admitted goals and caps as specified; failures/shortfalls retained without replacement | **APPROVED — 2026-11-23 사용자 승인.** |
| **실행환경** | CPython 3.11.15 + 고정 `research_c_runtime_lock.txt` 전체 package inventory. 주요 직접 패키지 NumPy 2.4.3 / pandas 3.0.1 / NetworkX 3.6.1 / jsonschema 4.26.0 | **APPROVED — CPython 3.11.15 + lock** |
| **운영** | Development admissions 목표 64, Held-out 200은 후보. Generator attempt 상한 386/1,104; 실행별 실제 proposal cap·resource cap은 config에서 사전 고정. Proposal shortfall 및 admitted 후 실패는 보존·대체 금지. | **APPROVED — 목표·cap 및 무대체 규칙** |
| **상태** | A2/P1/Task, 잔여 A/B/C와 Production resource profile 승인. Configuration·Manifest·비실행 Preflight를 준비하고 코호트 실행은 별도 승인 전까지 차단. | **CONTRACT_APPROVED / EXECUTION_APPROVAL_PENDING** |

사용자는 §10.1–10.4의 나머지 설정을 승인했고 Rule B·대체 정규화만 제외했다. Config·Manifest와 비실행 Preflight를 마친 뒤 Development 실행은 별도 승인을 받는다.

A에 대한 권고는 **A2**다. 원 연구 질문은 strict indirect-only task 모집단에서 오류 위치의 우선순위를 비교하는 것이므로, 각 오류 유형의 topology-level recipe가 반드시 존재해야 한다는 조건으로 모집단을 선별하지 않고 지표별 수정 기회 0건도 결과로 포함하는 편이 목표에 더 잘 맞는다. A1을 선택하면 논문 모집단을 “FN/FP/REV recipe support가 모두 있는 Q-common subset”으로 제한해 명시해야 하며, 구조 파일럿 494/500을 그 수율 추정치로 사용하지 않는다.

## 7. 테스트 실패 및 보고 정정

1. **의존성 fingerprint 불일치:** 기존 전역 환경에서 Step4 readiness가 실패했으나, Research C 격리 환경을 Python 3.11.15와 pinned requirements로 구성해 C 전용 73개 회귀 테스트를 통과했다. 기존 Step4 readiness 실패 자체는 이번에 재실행하지 않았고, 해당 Step4 전역 검증은 별도로 남는다. C runtime lock은 승인 실행과 같은 환경을 고정하기 위한 근거다.
2. **Step4B4 raw-ledger SHA 불일치:** Git blob 예상 SHA는 보존, raw-byte 테스트와 Windows CRLF checkout 간 차이. frozen 원본 수정 없이 재현환경/개행 핸들링을 별도 정비할 수 있음. 현재 판단상 Research C 계산 격리.
3. **Step4C1 WORK_LOG SHA stale:** 개발용 `NOT_FROZEN` manifest의 기록 파일 해시가 이후 WORK_LOG 추가로 낡음. Step4C2 frozen manifest 및 Research C 데이터/코드는 영향 근거 없음. manifest를 고쳐 통과시키지 않음.

이번에 Step4의 세 실패를 재조사하거나 재실행하지 않았다. 기존 분류는 위와 같이 유지한다. Research C 전용 격리 runtime은 requirements와 full lock을 설치해 검증했고, Step4 frozen fingerprint/manifest/원시 파일은 변경하지 않았다.

이번 변경에서 `jsonschema==4.26.0`을 requirements에 추가하고, Runner는 approved config와 참조 candidate schema를 Draft 2020-12로 검증한 뒤 기존 custom contract, hash, runtime, cohort, resource gate를 적용한다. Standalone manifest JSON Schema는 여전히 없으며 필수 manifest field/hash는 existing custom validation에서 검사한다. `--mode preflight`는 이 Gate를 모두 검증하되 dispatch 전에 요약을 반환한다. positive preflight는 임시 TEST_ONLY 합성 bundle로만 검증했고, 실제 사용자 승인이나 실제 bundle을 만들지 않았다.

## 8. 승인 Bundle 준비 및 승인 후 순서

승인 bundle은 만들지 않았다. 현재 승인 schema는 config에 `USER_APPROVED`, `PREREGISTERED`, cohort, run ID/output, target admissions/proposal cap, 전체 `[0,1,2,3,4]` budgets, population/SCM/task/G0/repair/evaluation, RNG, resource limits, runtime fingerprint를 요구한다. manifest는 승인 상태와 config/manifest/code/commit/tree/runtime/cohort/RNG/resource hash를 묶는다. `PREREGISTERED`는 설정의 상태 문자열이고, public registry URL/ID를 검사하지 않는다. 사용자 제공 승인 bundle 외에 테스트 hook/임시 테스트 승인 객체를 production에서 사용할 수 없다.

계약 v1 및 실행 Gate의 차이를 먼저 승인 기록에 반영하고, 다음 순서로 진행한다.

1. 이 문서의 A/B/C와 실행환경·운영 항목에 사용자가 APPROVE/MODIFY/DEFER로 응답한다.
2. 응답에 맞춰 계약, 분석 계획, 실패/precision/resource 규칙을 업데이트하고 사용자가 검토 가능한 승인본을 만든다. 로컬 연구계약 동결과 외부 preregistration은 구분한다.
3. 승인된 운영 runtime을 `research_c_runtime_lock.txt`로 설치하고 기록한다. 실행 전에 clean commit/tree와 runtime fingerprint 전체를 고정한다. frozen Step4 readiness/manifest는 별도 원상태로 둔다.
4. 나머지 A/B/C 선택에 대한 별도 사용자 승인, 로컬 계약 동결 및 필요한 외부 사전등록을 구분해 완료한 뒤 실제 승인 Configuration을 작성한다. 현재 실제 승인 config/manifest는 없다. 승인된 config 작성 후, clean commit 및 격리 runtime에서 아래 Manifest prep 명령을 실행한다. 이 스크립트는 config 내용을 승인하지 않으며 config의 승인 상태를 manifest에 복사·바인딩만 한다. Manifest에는 `approval_status`, config/contract/resource hashes, cohort/run/output, runtime inventory, `excluded_untracked_paths=[".build_reframed/"]`, source commit/tree 및 code hashes가 포함된다.
5. `python scripts/prepare_research_c_manifest.py --approved-config <approved-config.json> --output <execution-manifest.json>`으로 기존 승인 config를 바인딩한 뒤 `python scripts/run_research_c_runner.py --mode preflight --approved-config <approved-config.json> --execution-manifest <execution-manifest.json>`로 JSON Schema·custom contract·manifest·runtime·output 검증을 하고 proposal 0건/SCM 0건으로 종료했음을 확인한다. Manifest 작성은 사용자 승인 행위가 아니다. Preflight도 실행을 시작하지 않는다. 실제 실행 명령은 `--mode research`이며 이후 별도 실행 승인이 있어야 사용한다. `target_admissions`는 eligible SCM 수 목표, `proposal_cap`은 최대 proposal 시도 수(상한 development 386)다. cap 후 shortfall은 기록하며 평가 실패 SCM을 대체하지 않는다.
6. Development cohort 실행 후 proposal/admission/failure/complete/paired 수와 resource 측정을 확인한다.
7. 개발 자료에서 사전 허용된 정밀도/실행성 요약과 정책 선택만 수행한다. 선택 규칙이 있으면 held-out 전에 기록·고정한다.
8. 별도 independent-evaluation config, seed namespace, ledger 및 출력 위치를 봉인한다. Held-out 실행은 별도 명시 승인 후 수행하며, 평가 결과 열람 후 N·정책·주 contrast를 변경하지 않는다.

최종 Development 실행 명령은 `python scripts/run_research_c_runner.py --mode research --approved-config <config.json> --execution-manifest <manifest.json>`이다. 이는 Gate 통과 즉시 proposal stage를 시작한다. 검증 전용은 위 `--mode preflight`만 사용한다. 현재 승인 Bundle은 없으며 실제 연구 CLI는 계속 차단되어야 한다. 이번 테스트는 test-only synthetic bundle을 임시 디렉터리에서 검증했으며 실제 승인이나 연구 실행이 아니다.

이번 변경의 검증:

```powershell
<isolated-research-c-python> -m unittest tests.test_original_objective_a2_preflight tests.test_original_objective_runner tests.test_original_objective_cohort_runner tests.test_original_objective_e2e_fixture tests.test_original_objective_policy_engine tests.test_original_objective_policy_engine_independent tests.test_original_objective_proposal_stage_gate tests.test_original_objective_structural_pilot_and_ledger -q
```

**80 tests, 모두 통과(당시 기준).** 추가 A2 TEST_ONLY 검증은 오류가 있는 상태에서 FN/FP/REV 및 일부 복합 유형 support가 빠진 경우와 17정책 완전 E2E, Q-common/non-Q-common proposal 표시, no-op 비용 0, 실제 C proposal stage builder 주입, 무오류 G0를 확인했다. P1은 B=2 `S0 Regret − Full Greedy Regret` 수식·부호·공통 truth/data/task/action-grid hashes와 단일 SCM 기록(집계 미수행)을 확인했다. GT 계수/평가 결과를 바꿔도 수정 로그와 추천은 바뀌지 않고 평가 Regret만 달라지는 TEST_ONLY 검사도 통과했다. Manifest preparer는 임시 디렉터리의 test-only config에만 적용했고 proposed 상태 거부를 확인했다. 실제 승인 bundle, research manifest, 연구 SCM 또는 연구 Regret cohort는 생성하지 않았다. 미승인 CLI preflight 차단 테스트도 통과했다.

실행 환경은 Windows CPython 3.11.15, NumPy 2.4.3, pandas 3.0.1, NetworkX 3.6.1, jsonschema 4.26.0이며 `research_c_runtime_lock.txt` 13개 항목이 설치 환경과 모두 일치했다. `python -m compileall -q ...` 및 `git diff --check`도 통과했다.

격리 환경에서 `scripts/validate_original_research_fixture_contract.py`도 통과했다. 고정 fixture 계산·정규화·예산 결과가 기대값과 일치했고, 16개 조합의 실제 결과 다양성과 포화 진단은 TEST_ONLY 설계 검증으로만 기록했다. 새 연구 SCM·관측자료·개입·Regret 결과는 생성하지 않았다.

## 9. 검토 근거 파일

- `RESEARCH_C_EXPERIMENT_CONTRACT_V1.md` — 제안 estimand, task zone, Rule A/B, 지표·utility·비용, Regret 정의, sensitivity, N 제안.
- `RESEARCH_C_FINAL_FEASIBILITY_AND_EXECUTION_GATE.md` — 구조 전용 파일럿(500 proposal, 494 eligible) 및 포화/오류 실현 진단. 기준은 구버전이므로 production 준비 관련 문장은 현재 상태로 해석하지 않음.
- `RESEARCH_C_FINAL_TECHNICAL_GATE_REPORT.md` — 최신 기술 판정, TEST_ONLY 범위, production approval gate 및 전체 테스트 요약.
- `RESEARCH_C_EXECUTION_PLAN.md` — 개발/평가 분리, 분석·실행 계획. 일부 생산 runner 미구현 서술은 d9 기준에선 오래된 설명임.
- `RESEARCH_C_RUNNER_3C_IMPLEMENTATION.md` — 상태/기술 진척 설명이 최종 기술 Gate보다 오래된 IN_PROGRESS 기록이며, 이후 Proposal 자원 격리와 approval-gate 연결을 반영하지 않는다. 최신 구현 판정에는 `RESEARCH_C_FINAL_TECHNICAL_GATE_REPORT.md`를 사용하되, 이 문서의 TEST_ONLY 범위를 넘어 연구 양성 실행을 주장하지 않음.
- `research/original_objective/research_c_candidate_config.schema.json`, `research/original_objective/research_c_approved_execution.schema.json` — proposed/approved bundle의 요구 구조.
- `research/original_objective/research_c_runtime_lock.txt` — Windows CPython 3.11.15에서 실제 설치·테스트한 전체 package lock.
- `tests/test_original_objective_a2_preflight.py` — A2/no-op feasibility와 preflight TEST_ONLY 검증.
- `research/original_objective/policy_engine.py` — `Config`, `classify`, `metrics`, subset utility, `common_penalty`, `run`, `run_all` 실제 정의.
- `research/original_objective/runner.py` — `_validate_supported_research_contract`, `_validate_approved_config_schema`, `run_research_mode` 및 cohort·proposal cap·runtime/manifest 검사.
- `scripts/prepare_research_c_manifest.py` — 기존 승인 config와 clean commit/runtime의 manifest binding. 승인 상태는 생성하지 않음.
- `research/original_objective/execution_limits.py` — `ResourceLimits`와 sampled RSS/사전 저장량 검사의 범위 및 한계.
- `research/original_objective/proposal_pipeline.py` — proposal 생성/assembly와 `run_approved_research_proposal_cohort`.
- `research/original_objective/cohort_runner.py` — proposal ledger, checkpoint, resume, stage time/resource 기록.
- `tests/test_step4_post_freeze_readiness.py`, `tests/test_step4b4_mock_runner.py`, `tests/test_step4c1_production.py` — 재현한 세 실패의 assertion.

## 10. 최종 상태

A2 admission, P1 primary, 계층 Task 추출과 잔여 A/B/C 과학적·운영 계약은 승인되어 문서와 구현에 반영됐다. P1은 B=2 `Regret(S0)-Regret(Full Greedy)`이며 positive가 Full Greedy 개선을 뜻한다. Runner는 SCM별 결과만 기록하고 cohort 추정량/CI는 계산하지 않는다. Manifest preparer는 승인 설정과 source/runtime hash를 결합할 뿐 승인 상태를 발급하지 않는다. 지금은 승인 Config·Manifest와 비실행 Preflight를 준비하며, 별도 승인 전까지 실제 cohort 실행은 차단한다.

**과학적 계약과 운영 상한은 승인됐다. 현재 실행 단계는 승인 Configuration·Manifest 생성 및 비실행 Preflight다. 별도 Development 실행 승인 전까지 proposal·SCM 생성은 차단한다.**

## 10. 승인 계약 및 Development 실행 준비

이 절은 승인된 실행 계약의 정확한 값을 모은다. 미실행 산출·결과와 외부 공개 등록은 별도 상태로 관리한다. Rule B 및 대체 정규화 민감도는 이번 실험 범위에서 제외한다.

### 10.1 A — 모집단과 G0

| 항목 | 승인 설정값 | 코드·계약 대조 및 해석 | 상태/해석 |
|---|---|---|---|
| Topology | 기존 Step 4 생성기의 `chain_mediation`, `fork_branch`, `observed_common_cause`, `multiple_directed_paths` 4종; 6–10 nodes; target edge density `[0.2, 0.4]` | Candidate/approved schema가 이 값으로 제한한다. 기존 SCM/결과 재사용이 아니라 생성 알고리즘 재사용이며 RNG namespace는 새로 둔다. | 값과 템플릿 정의의 사용자 승인 |
| 적격 task 및 추출 분포 | Proposal ID·cohort·master seed로 SHA-256 rejection sampling을 적용해 고정된 20개 strata에 결정적으로 배정한다. 해당 topology 내 strict indirect-only ordered `(X,Y)`를 고르고 `observed_common_cause`의 strict scaffold pair를 우선한다. | 전역 eligible-pair uniform이 아니다. Strata·후보 수·scaffold 우선 및 eligibility/admission 조건화로 분포가 달라질 수 있다. 사후 재가중 없이 합성 생성·적격성 조건부 모집단으로 해석한다. | **APPROVED — 2026-11-23 사용자 승인.** |
| 모집단 gate | **A2 유지:** FN/FP/REV recipe support를 admission 조건으로 요구하지 않음; 무오류 G0 및 recipe 부재도 포함; Q-common은 secondary flag | A2는 승인되어 proposal/admission 구현에 반영됐다. 500개 구조 파일럿의 494개 적격은 이전 조건·구조 진단이며 A2 운영 수율로 사용하지 않는다. | 추가 gate 없음; strict task 구현과 무성과 기반 제외 원칙 승인 |
| SCM 방정식 | signed linear acyclic SCM; 각 계수 절댓값 Uniform `[0.25, 0.8]`, 부호는 독립 fair sign; node noise는 독립 centered Gaussian, 각 SD Uniform `[0.8, 1.2]` | Candidate schema는 family/range/sign/noise를 고정한다. 이는 합성 family이며 실제 제조공정 계수의 추정치가 아니다. | 값 및 독립성 가정 승인 |
| 관측자료 | SCM당 공통 관측표본 `n=512`, centered Gaussian SCM noise에서 관측 생성; 모든 정책·예산에서 동일 자료 사용 | Schema에 `shared_across_policies=true`, `training=common_observational_sample`; 관측 표본 크기가 정밀도 충분성을 입증하지는 않는다. | 값 승인 |
| task/action/loss | eligible `(X,Y)`에서 task를 사전 선택; 행동 grid `[-1,-0.5,0,0.5,1]`; `delta`는 cohort admission ordinal에 따라 `+1,-1` 교대; 표준화된 target-mean squared error; GT 값은 analytic hard-do로 추천 확정 뒤 계산 | Schema/runner의 supported contract와 일치. 이는 합성 평가 손실이며 원화·수율·안전 손실이 아니다. | 값과 `delta` 교대 규칙 승인 |
| G0 참 edge | 각 정답 adjacency의 corruption 제안 확률 `q=0.15`; 제안 시 FN/REV/UNRES 각각 조건부 `1/3` | Proposal 확률, 수락 오류율, 실현 오류율을 각각 기록한다. | 값 승인 |
| G0 거짓 edge | 각 GT-nonadjacent unordered pair의 FP 제안 확률 `r=0.05`; 방향은 fair draw | 한 pair에 단일 상태만 허용. DAG-invalid 제안은 기록 후 거절, 재추출 없음(`retry_limit=0`). | 값 및 처리 승인 |
| 오류 없는 제안·실패 | 오류 0건 G0는 유지. 구조 부적격 proposal은 별도 카운트. strict-task 적격 후 실패는 실패로 보존하고 성능을 보고 대체하지 않음. | 코드의 admission/evaluation ledger는 proposal, admission, 평가 완료와 실패를 분리한다. | 표본·실패 규칙 승인 |
| cohort와 N | Development `target_admissions=64`; independent evaluation `target_admissions=200`. N은 **strict-task 적격 후 admission된 독립 SCM 목표 수**이며 완전 paired 분석 수나 policy-row 수가 아님. 동일 생성 규칙, 독립 `development`/`independent_evaluation` RNG namespace·ledger·출력 root. | 64/200은 연구 C 효과의 검정력 보장이 아니다. 실패가 있으면 complete paired N은 낮아질 수 있으며 보충 추출하지 않는다. | N 목표 및 cohort 분리 승인 |
| Proposal cap | Development 최대 386, Held-out 최대 1,104 proposal attempts; admitted 목표를 먼저 채우면 정지하고 cap shortfall을 그대로 기록 | Generator 상한과 일치하나 A2 수율은 보장하지 않는다. 성능에 따른 SCM 대체는 금지한다. | **APPROVED — Development 64/386, Held-out 200/1,104.** |

### 10.2 B — 수정 정책·비용·정보 접근

| 항목 | 승인 설정값 | 코드·계약 대조 및 해석 | 상태/해석 |
|---|---|---|---|
| 원 지표·정책군 | M1 비과제 FN/support; M2 비과제 FP/추정 비과제 adjacency; M3 비과제 참 adjacency 방향 정확도와 unresolved rate 별도; M4 과제 구역 FN/FP/REV/UNRES 벡터. S0 + 15 nonempty subsets. | 공식 지표의 분자·분모·count·zero denominator NA를 policy utility와 분리한다. M4를 공식 단일 scalar로 축약하지 않는다. | 정의 및 지표 조합 승인 |
| Task zone/FP | 모든 GT `X→Y` directed path edges + 무조건화 open backdoor path edges(내부 collider 없는 경로); FP Rule A는 두 끝점 모두 task-zone node set 안이면 M4 | Rule A는 task-zone node 내부 chord FP도 넓게 귀속할 수 있으며 개입 피해의 대체 정의는 아니다. Rule B는 이번 승인에서 명시적으로 제외되며 실행하지 않는다. | Rule A 승인; Rule B는 이번 scope에서 제외 |
| Greedy | `Score = (P_S(before)-P_S(after))/operation_cost`; G0 고정 opportunity 분모; subset 내 선택 지표 동일 가중치; G0에서 support/error가 있는 M4 FN/FP/REV/UNRES 성분을 active로 하고 활성 성분 β 동일; deterministic tie order는 승인 config와 코드가 지원하는 순서 사용 | 작은 M4 support가 사건당 gain을 키울 수 있다. 이는 확인할 편향 위험이지 M4의 우월성 근거가 아니다. 대체 initial-error-count normalization은 이번 승인 범위에서 제외되어 실행하지 않는다. | 승인됨; 대체 정규화 민감도 제외 |
| 비용·벌점 | add/delete/orient/resolve 각 relative cost `1`; 예산 초과 수정 금지; λ=`1`은 task/off-task event에 같은 총 배수; P_all은 FN/FP/REV/UNRES 사건을 같은 weight로 1회 계산; P_S는 Greedy subset 선택 효용, P_all은 공통 구조 결과, C는 사용 비용, Regret은 별도 행동 결과 | `delete_unresolved=1`은 Schema 호환용 reserved key일 뿐 후보 연산으로 생성·청구하지 않는다. UNRES 삭제는 금지; 방향 resolve는 1. 비용은 실제 통화가 아니다. | 비용·λ·벌점 승인 |
| 예산·기준선 | 실행 grid `[0,1,2,3,4]`: B0 기준, B1 보조, B2 P1 primary, B3/B4 포화 진단. S0, 15 subset policies, Canonical Oracle는 서로 구분 | B0는 각 정책의 미수정 상태에 대한 기준이며 S0는 무수정 정책이다. 그래프가 같아지는 정책은 hash로 식별하고 중복 성능 표본으로 세지 않는다. | 예산 역할 승인 |
| Canonical Oracle | 동일 G0, 후보 오류·GT 구조정보, 비용·예산·DAG 제약을 이용하되 지표 gain 점수 대신 고정 canonical ordering으로 수정 | GT SCM 계수, 개입 손실, GT 최적 action, Regret은 접근하지 않는다. Oracle diagnostic baseline일 뿐 전역 최적해·Regret 상한·배포 정책이 아니다. | 정보 범위 승인 |

### 10.3 C — UNRES·결과·통계·실패

| 항목 | 승인 설정값 | 코드·계약 대조 및 해석 | 상태/해석 |
|---|---|---|---|
| UNRES | 최종 구조 그래프에는 보존; 학습 DAG에는 directed parent/child edge로 넣지 않는 abstention encoding; 무료 방향 복구·수정비용 0 또는 GT 방향 보완으로 세지 않음; 두 그래프 hash 별도 기록 | 구조 지표는 원 구조 그래프에서 계산한다. 무방향 정보 손실로 UNRES가 많은 정책에 학습 불이익이나 fit failure가 생길 수 있으므로 성공률도 정책별 보고한다. | 주 처리 방식 승인; 다른 encoding은 결과를 보기 전 별도 민감도 계약 없이는 시행하지 않음 |
| P1 | 이미 승인: B2 `Full Greedy(M1+M2+M3+M4)` 대 S0. SCM별 `delta_i=Regret_i(S0,B2)-Regret_i(FullGreedy,B2)`; 양수면 Full Greedy 유리. 효과량은 admitted population에서 완전 paired SCM의 `mean(delta_i)`로 보고 | 동일 SCM/자료/task/행동 grid/GT evaluator. P1의 cohort 추정은 실행 산출물에서 아직 미계산이다. | P1은 승인됨 |
| Secondary | Full Greedy–Canonical; S0 대 나머지 14 subset; 정책별 구조개선·비용·기회·action change·Regret; B1 보조, B3/4 포화, B0 기준; Q-common 및 수정기회가 있는 사례 조건부 요약 | subset 비교는 탐색적이고 multiple-policy search를 primary로 승격하지 않는다. Development 선택 규칙은 Held-out 전에 봉인한다. | Secondary 범위 승인 |
| 불확실성 | 권고: Primary 95% paired-t CI; 보조 SCM-level paired percentile bootstrap 10,000회, 2.5/97.5 percentile CI. | 재표집 단위는 SCM paired row. Bootstrap seed와 분석 코드 버전을 Held-out 결과 열람 전에 고정한다. Runner는 현재 CI를 계산하지 않는다. CI 포함 여부를 유효/무효 효과의 증명으로 해석하지 않는다. | 통계 규칙 승인됨; 분석 코드는 Held-out 열람 전 고정 필요 |
| 표본·분석분모 | N=64 Development, N=200 Held-out admitted SCM 목표; cap 386/1,104. N은 admitted 목표이지 complete-pair 수가 아니다. 기존 `s_max/h` 자동 증액은 이번 권고에서 사용하지 않는다. | Complete-pair·policy-complete 수 및 실패를 별도 보존·보고한다. 동률/0차이는 유지; 실패 Regret=0 대체 및 성과 기반 대체 금지. Cap 미달은 shortfall로 남긴다. | 목표 N/cap 및 실패 규칙 승인됨 |
| Held-out 잠금 | 동일 모집단 생성 규칙·설정/실행 코드; 독립 seed namespace; 개발 결과로 고를 수 있는 것은 사전 지정된 탐색 절차 내 선택뿐. Held-out 결과를 열기 전에 정책/분석법/primary/N을 고정하고 이후 변경 금지 | Development와 Held-out는 다른 SCM이며 Step 5/6 표본을 재사용하지 않는다. | 절차 승인됨 |

### 10.4 Runtime·Production 운영 Gate

| 항목 | 확인된 현재값/구현 | 승인 권고와 차단 |
|---|---|---|
| Runtime | CPython `3.11.15`; `research_c_runtime_lock.txt`의 13개 패키지 버전 | 승인된 lock 환경에서 실행하고 OS/machine fingerprint를 Manifest에 바인딩한다. Step 4 fingerprint 상태는 별도다. | **APPROVED; 현재 실행 Manifest에 fingerprint 결합 예정.** |
| RNG | protocol `step4-rng-v1`; config cohort namespace `development` 또는 `independent_evaluation`; master seed는 비음수 정수 필수 | Development master seed는 `2026112301`로 승인되었으며 실행 Config에 고정한다. 같은 cohort 내 topology/SCM/관측/G0 stream은 분리하고 held-out namespace와 분리한다. |
| Proposal/SCM worker timeout | 코드 필드는 `unit_timeout_seconds` 하나로 proposal/SCM worker 양쪽에 적용 | TEST_ONLY proposal worker 최대 `0.594s`, SCM worker 최대 `0.767s`. 승인값 `30s` 공통 unit timeout(각 관측 최대의 약 50×/39×). 별도 proposal/SCM timeout을 지정하려면 코드 수정이 필요하므로 이번에는 같은 값으로 제안. |
| SCM/campaign active time | `scm_active_seconds`, `cohort_active_seconds`로 누계 관리 | 승인값 `60s`(관측 최대의 약 78×); 승인값 `3,600s`(1시간). 386 proposal×0.594s + 64 SCM×0.767s의 보수적 선형 산식은 약 `278s`; 1시간은 이 산식의 약 12.9×. 운영·재개·외부 대기 전체 wall-time 보장은 아님. |
| Sampled RSS | 격리 worker의 주기 표본을 보고 cap 초과 시 종료 | 승인값 `536,870,912 bytes`(512 MiB); benchmark 최대 `71,589,888 bytes`의 약 7.5×. 표본 사이 overshoot가 가능하고 OS hard quota가 아님. |
| 파일/ledger/cohort 저장량 | 사전 쓰기 검사·SQLite checksum/원자 저장. filesystem quota 아님 | 승인값 result `4,194,304 bytes`(4 MiB; max 관측 351,861 bytes의 약 11.9×), 개별 SQLite ledger `268,435,456 bytes`(256 MiB; Dev 선형 추정 cohort ledger 약 21.8 MB의 약 12×), cohort directory `536,870,912 bytes`(512 MiB; proposal 포함 추정 약 24.0 MB의 약 22×). 모두 중단 경계이지 용량 보장치가 아님. |
| 최소 여유 디스크 | 실제 실행 직전 free-space 검사 | 승인값 `5,368,709,120 bytes`(5 GiB). 측정 당시 C: free `29,991,530,496 bytes`(약 27.94 GiB); 당시 조건이면 임계치 이후 약 22.94 GiB가 남음. 다른 실행 환경에는 같은 여유가 보장되지 않음. |
| 동시성 | `max_concurrent_scms=1`만 지원하고 runner는 직렬 실행 | 사용자 승인값 `1`. |
| Proposal cap | generator hard maximum은 development `386`, independent evaluation 내부 generator cohort `confirmation` `1,104`; config는 그 이하만 허용 | 승인 cap은 386/1,104. A2 생산 수율을 입증한 값은 아니며 cap에서 부족해도 확장·재추출 없이 shortfall을 보고한다. `independent_evaluation`→`confirmation` 내부 binding은 config/manifest에 고정해야 한다. |

**측정 근거:** `scripts/benchmark_research_c_resources_test_only.py`가 사전에 고정한 4 topology × node count 6/10 × 3 proposal assignment를 사용해 동일한 24 TEST_ONLY 입력을 동일 seed `9,721,100`으로 세 번 실행했다. 72 SCM-run, 6,120 정책 평가(17×B0–4), 적격 proposal 72/72, 평가 실패 0, resource stop 0이다. 24개의 고유 SCM 입력 중 오류 없는 G0는 4개(16.7%); 모든 입력을 결과에 유지했다. 반복 간 결과 hash는 모두 같았다. 수정 기회 수 범위는 M1 0–2, M2 0–2, M3 0–2, M4 0–4였다. 이는 작은 TEST_ONLY 구조에서 기회가 부족하거나 없는 경우가 실제로 포함됨을 보여줄 뿐, 연구 정책 성능 근거가 아니다.

관측 요약: proposal worker `0.438–0.594s`(중앙값 `0.500s`), proposal-stage wall time/24건 `12.494–12.732s`; SCM active worker `0.590–0.767s`(중앙값 `0.638s`), cohort wall/24 SCM `16.910–17.023s`. generation 함수 최대 시간은 SCM parameters `0.000602s`, observations `0.000650s`, G0 `0.000984s`. SCM당 17정책×5예산 aggregate stage 최대는 구조 수정 `0.0836s`, fit/recommend `0.0174s`, GT evaluation `0.0089s`, result validation/serialization `0.0926s`, atomic commit `0.0292s`. Proposal RSS 최대 `71,589,888 bytes`; SCM worker RSS 최대 `70,934,528 bytes`. 최대 결과 JSON row `351,861 bytes`; proposal SQLite ledger 최대 `118,784 bytes`; cohort SQLite ledger 최대 `8,159,232 bytes`; 24 SCM 전체 output 최대 `8,281,410 bytes`이다. raw 기록에는 run별 값과 code/runtime hash가 있다.

Development 64 admitted SCM과 cap 386으로의 계산은 위 max 관측치를 선형 적용한 계획치다. proposal worker `386×0.594s≈229s`, SCM worker `64×0.767s≈49s`, 합계 약 `278s` active worker time이다. storage는 24 SCM 관측치에 `64/24`를 곱한 뒤 386/24 proposal ledger 증가를 더해 cohort output 약 24 MB를 추정했다. 실제 수율, 장시간 tail, coordinator overhead, 장애 재개 비용은 보장되지 않는다. 따라서 위 numerical profile은 **보수적 중단 후보**이지 resource sufficiency 인증이 아니다. profile을 초과하면 해당 실패를 기록하고 안전 중단하며, SCM을 결과에 따라 교체하지 않는다. RSS는 sampled monitoring이고 저장량은 pre-write 검사이므로 OS 메모리 quota 또는 파일시스템 quota로 표현하지 않는다. Production profile은 이번 사용자 승인으로 확정된 중단 상한이며 TEST_ONLY 실측으로 최악값/성능 보장을 뜻하지 않는다.

원시 계측: [resource_benchmark_f78952d_final.json](research/original_objective/test_outputs/resource_benchmark_f78952d_final.json). TEST_ONLY 실행 저장소는 `C:\DAT_TEST_ONLY\research-c-resource-benchmark-20261123-v4`이며 source checkout 밖에 있다. 이 산출물은 연구 표본 수에 포함되지 않는다.

### 10.5 승인 기록과 남은 실행 Gate

| 결정 | 권고 선택 | 현재 상태 |
|---|---|---|
| A2 모집단 | strict indirect-only, recipe-support gate 없음, 무오류·no-op 포함 | **APPROVED** |
| P1 | B2 Full Greedy vs S0, `Regret(S0)-Regret(FullGreedy)` | **APPROVED** |
| Task sampling | 고정 20개 topology×node-count strata의 hash rejection 배정 후 topology 조건부 strict indirect pair 선택, observed-common-cause strict scaffold 우선 | **APPROVED — 이전 사용자 지시.** |
| A 잔여 | 4 topology, 6–10 nodes, SCM/noise/action/loss, q=.15/r=.05, FN/REV/UNRES conditional 1/3, no-redraw DAG rejection, Development 64/386 및 Held-out 200/1,104 | **APPROVED — 2026-11-23 사용자 승인.** |
| B 잔여 | M1–M4·15 subset+S0·Canonical Oracle structural-only, Rule A only, G0-fixed opportunity only, 동일 metric/M4 활성 성분 가중치, add/delete/orient/resolve 비용 1, λ=1, B=0–4. Rule B·대체 정규화 민감도 제외. | **APPROVED — 2026-11-23 사용자 승인.** |
| C 잔여 | residual UNRES abstention; SCM 단위 complete-pair P1 mean; 95% paired-t CI 및 보조 SCM bootstrap 10,000회; shortfall/failure 무대체; `s_max/h` 자동 증액 없음; held-out 분석 잠금 | **APPROVED — 2026-11-23 사용자 승인.** |
| Runtime/seed | CPython 3.11.15 + exact 13-package lock; Development master seed `2026112301`; run-specific platform fingerprint bound in Manifest | **APPROVED.** Runtime versions verified; this run’s fingerprint is to be bound in the Manifest prepared below. |
| Production resource profile | unit timeout 30s(shared); SCM active 60s; cohort active 3,600s; sampled RSS 536,870,912 B; result 4,194,304 B; ledger 268,435,456 B; cohort storage 536,870,912 B; min free disk 5,368,709,120 B; concurrency 1 | **APPROVED.** RSS는 sampled monitor, storage는 사전 검사 경계이며 OS/filesystem quota가 아님. |

**두 단계 중 계약 승인은 완료됐다.** 이번 사용자 메시지로 과학적 계약과 Production resource profile이 확정됐다. 지금은 승인된 Configuration·Manifest를 clean commit, runtime fingerprint, source commit/tree·code hash와 결합하고 비실행 Preflight만 수행한다. Development 실행은 Preflight 성공 후 별도 실행 확인을 받을 때까지 금지한다. 벤치마크 입력은 24개 TEST_ONLY SCM뿐이므로 resource limits는 안전 중단 경계이지 처리량·성공 보장이 아니다.

**승인 기록 — 2026-11-23 (실행 승인 아님):**

**사용자 승인 기록 — 2026-11-23:** A2, P1, 계층 Task sampling과 §10.1–10.4의 나머지 A/B/C 과학적 계약·Production resource profile 승인. Development 64 admitted/cap 386, Held-out 200 admitted/cap 1,104, seed `2026112301`, 95% paired-t CI, 보조 SCM-level bootstrap 10,000회, 실패·shortfall 무대체를 확정했다. Rule B 및 대체 정규화 민감도는 이번 필수 범위에서 제외했다. 이 승인은 내부 계약을 확정하며 외부 registry 등록이나 Development 실행 승인이 아니다.

2026-11-23 사용자 메시지가 이 표의 A/B/C 계약, Development master seed `2026112301`, 표본 목표·cap, 통계 및 실패 규칙, Production 자원 상한을 승인했다. Rule B 및 대체 정규화 민감도는 명시적으로 제외됐다. 이 승인은 내부 계약 고정으로 기록하며 외부 공개 registry 등록을 의미하지 않는다. Configuration·Manifest·비실행 Preflight 후 Development 실행은 별도 승인받는다.

`MODIFY`를 선택할 때는 승인 문안의 해당 정확한 값만 바꾸고 계약/config/schema/hash를 다시 대조한다. `DEFER`된 과학 결정이 있으면 해당 항목이 해소되기 전 cohort proposal 생성은 금지한다. 특히 resource profile을 채우기 위해 TEST_ONLY 값을 승격하지 않는다.

### 10.6 승인 후 명령 순서

승인 config/manifest는 이 승인 문서를 반영한 커밋 이후 생성한다. 아래 단계에서 `--mode preflight`까지만 실행하며, research mode는 별도 실행 승인이 있어야 한다. `--mode research`는 gate 통과 시 proposal 생성 즉시 시작하므로 preflight 전 실행하지 않는다.

```powershell
# 1) 승인 config가 있고 runtime/코드가 clean 고정된 뒤 manifest를 바인딩한다.
python scripts/prepare_research_c_manifest.py --approved-config <approved-config.json> --output <execution-manifest.json>

# 2) 연구 proposal을 생성하지 않는 사전 검증
python scripts/run_research_c_runner.py --mode preflight --approved-config <approved-config.json> --execution-manifest <execution-manifest.json>

# 3) 별도 실행 승인 이후에만 Development 코호트를 실행한다.
python scripts/run_research_c_runner.py --mode research --approved-config <approved-config.json> --execution-manifest <execution-manifest.json>
```

Manifest preparer는 이미 USER_APPROVED/PREREGISTERED config의 값과 source/runtime hash를 결합할 뿐이다. 승인 상태를 발급하지 않는다. Schema의 `PREREGISTERED` 문자열 검증은 외부 registry URL/ID 검증이 아니므로, 외부 공개 preregistration을 선택한다면 URL/ID 및 시각을 별도 승인기록에 보존한다. 실행 후 proposal, strict eligible, admitted, complete policy vector, complete paired SCM 분모와 실패율을 각각 보고한다.

**최종 판정: `CONTRACT_APPROVED / CONFIGURATION_AND_PREFLIGHT_PENDING / EXECUTION_NOT_AUTHORIZED`.** 외부 공개 사전등록은 수행하지 않았다. Approved config와 manifest를 준비하고 비실행 Preflight만 통과시킨다. Development 실행은 별도 승인 전까지 차단하며 연구 SCM/Regret은 생성하지 않았다.

# Research C — A/B/C 최종 과학적 계약 검토 및 승인 브리프

**기준 커밋:** `d9f0f0f4dd7943aa0084bd1af4b9ba62a3e735fd`
**상태:** 승인 요청용 제안. 사용자 승인·사전등록·연구 코호트 실행은 완료되지 않았다.
**범위:** 기존 문서·코드·테스트 검토만 수행했다. 새 SCM, 관측자료, 개입 결과 또는 연구 Regret을 만들지 않았다.

이번 정합화 변경은 두 JSON Schema의 설명(description)만 보완하고 본 승인 브리프를 갱신한다. Python 정책 엔진, Runner 실행 동작, 기존 TEST_ONLY payload 및 과학적 수치는 변경하지 않는다. 최종 상태는 **READY_FOR_USER_DECISION / APPROVAL_REQUIRED**다.

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
| Topology·크기 | 4종: chain mediation, fork branch, observed common cause, multiple directed paths; 노드 6–10; density `[0.2, 0.4]` | 승인 schema가 상수로 제한. 기존 Step4 topology generator 재사용은 새 SCM 데이터가 아니라 생성 규칙 재사용임. 네 template의 의미와 구현을 사전등록 부록에 고정할 것. | APPROVE |
| Task | 20 strata에서 균등 stratum을 제안하고, strict indirect-only ordered pair 중 선택. direct `X→Y` 금지, `delta`는 admission ordinal에 따라 ±1 교대. | Stratum/tie RNG 및 선택 구현은 Step4 generator를 새 cohort namespace로 재사용. proposal과 admission ordinal은 저장됨. | 기본 task 규칙 승인 |
| **추가 Q-common support 적격성** | Schema의 `task_rule`은 strict indirect-only만 선언. 그러나 실제 `build_structural_proposal()`은 task 선택 후 `q_common_eligibility()`로 FN·FP·REV 각각에 대한 competition recipe support가 1개 이상이어야 `accepted=True`를 준다. | **실질적 모집단 차이 / 승인 차단:** 지원이 없는 topology/task는 `missing_same_type_two_candidate_support`로 거절되고 다음 proposal을 진행한다. 모집단이 strict indirect-only 전체가 아니라 세 오류 유형의 recipe support가 모두 있는 구조에 조건화된다. 500→494 파일럿은 이 추가 gate를 실행한 생산 proposal builder가 아니므로 생산 acceptance rate를 보증하지 않는다. | 아래 결정표에서 명시 승인 필요 |
| SCM 구조·계수 | signed linear acyclic; 계수 절댓값 `[0.25,0.8]`, 독립 fair sign | 설정은 제안 상수. 이 합성 family 밖 제조 공정으로 일반화 불가. | APPROVE |
| 관측자료·잡음 | SCM당 공통 관측자료 `n=512`; 독립 centered Gaussian noise, SD `[0.8,1.2]`; 정책별 동일 관측자료 | 계수/잡음/표본 생성용 RNG를 분리하고 seed namespace 기록. `n=512`는 효과 추정 정밀도를 보장한 근거가 아님. | APPROVE |
| 행동·목표·손실 | 사전 선택 task, action grid `[-1,-.5,0,.5,1]`; standardized target mean squared error; GT 평가는 analytic hard-do | 동일 action grid와 손실을 전 정책에 적용. 실제 수율·안전·비용 함수가 아님. | APPROVE |
| G0 오류 주입 | 참 adjacency 손상 `q=.15`, 손상 시 FN/REV/UNRES 각 1/3; GT nonadjacent pair FP 제안 `r=.05`, 방향 무작위 | q/r은 제안 확률이지 실현 오류율이 아님. 구조 전용 파일럿의 494 strict-task eligible 중 오류 없는 G0 55 (11.1%); 이는 Q-common 추가 적격성을 통과한 생산 모집단의 비율이 아님. 오류 제안 1,190 중 DAG 수락 1,044·거절 146. | 오류 생성 규칙 승인; 생산 G0분포/지원 조건은 별도 결정 |
| DAG 거절·재추출 | DAG-invalid 오류 제안은 기록 후 거절, 재추출 없음 | 파일럿과 schema 제안이 일치. proposal 수와 accepted/rejected를 모두 분모와 함께 보존. | APPROVE |
| Task zone·backdoor | 모든 X→Y 단순 유향 경로와 무조건화 상태의 open backdoor 경로; collider 내부 노드가 없는 backdoor만 open. Rule A FP 귀속 | 경로 기반 구조 표식은 실제 개입 손실 자체가 아님. 무조건화 backdoor 한정이며 특정 조건화 집합은 다루지 않음. Rule A는 양 끝점 모두 task-zone node set 내 FP를 task로 태깅하여 내부 chord를 넓게 포함할 수 있음. | APPROVE 주 규칙; Rule B는 고정 민감도 선택으로 별도 승인 |
| 오류 없는 G0·표본 흐름 | G0 오류 0건도 admitted 모집단에서 제외하지 않음. proposal, strict-task, 추가 support gate, admitted, full-policy-complete SCM을 각각 분리 기록 | Feasibility 파일럿은 strict-task population에서 11.1% zero-error G0. 오류가 없는 그래프를 빼면 다른 estimand가 됨. 목표 admissions 미달 시 보고, 임의 대체 금지. | APPROVE 분모 규칙; support gate는 사용자 결정 |
| Cohort | Development / `independent_evaluation`(표시상 held-out); 별도 seed namespace·ledger·output; 제안 N=64/200 | Schema에는 `independent_evaluation`, generator는 proposal namespace로 `confirmation` 사용. 외부 이름과 내부 RNG binding의 매핑을 manifest에서 고정해야 함. N은 power 보장이 아님. | APPROVE 분리; N은 C 묶음에서 별도 결정 |
| 모집단 분모 | `target_admissions`는 구조 적격 proposal 목표. 완료 SCM/완전 paired SCM 수를 뜻하지 않는다. `proposal_cap`까지 outcome-blind proposal을 진행하고 미달 shortfall은 보존. | Admission 후 정책 평가 실패는 다른 SCM으로 교체하지 않음. 실패율과 완전 평가 분모를 분리한다. generator 상한은 development 386, confirmation 1,104 proposal attempts. | APPROVE 분모 규칙; 실제 cap은 실행 전 설정에서 확정 |

파일럿의 포화 진단에서 B=3/4 후보 선소진은 각각 87.6%/94.7%였으므로 이를 주 성능 예산으로 두기보다 포화 기술 결과로 보는 것이 타당하다. 권고는 B=2 주 비교, B=1 저예산 보조, B=3/4 후보 포화 기술 진단, B=0 S0 기준선이다.

## 4. B — 오류 수정 정책 및 비용

| 항목 | 구현·제안 계약 | 권고 및 해석 제한 |
|---|---|---|
| 원 지표 | M1 비과제 FN / 비과제 참 adjacency support. M2 비과제 FP / 추정 비과제 adjacency. M3 비과제 참 adjacency의 방향 정확도와 unresolved rate를 각각 보고. M4 task-zone FN/FP/REV/UNRES 벡터와 component support를 보존. | 공식 분자·분모/count는 policy utility와 별도로 기록. 분모 0은 NA. M2 분모만 늘어난 비율 하락과 REV→UNRES만으로 M3 정확도 수치가 오르는 현상은 repair gain으로 인정하지 않음. |
| 16개 조합 | S0 무수정 + M1–M4 비공집합 부분집합 15개 | 이 전략군은 어떤 지표 subset에 repair 후보를 제한하는지 나타냄. 명목 16개가 서로 다른 그래프를 보장하지 않음. |
| Canonical Oracle | 지표 gain 순위가 아닌 고정 canonical 순서로 같은 structural candidate pool을 수정; 같은 GT 구조정보·G0·비용·예산·DAG 제약 | 구조 라벨을 이용하는 oracle 진단 기준선. GT 계수·행동별 손실·최선 GT action·Regret은 쓰지 않음. 전역 최적해, regret upper bound, 배포 정책이 아님. |
| Greedy | 매 단계 `(P_S(before)-P_S(after))/edit_cost`; 실제 오류 사건이 사라지는 gain만 인정; 매 수정 뒤 후보·DAG·비용 재계산; deterministic tie order | Myopic 구조 대리목적의 탐욕 정책이며 `P_S` 전역 최소화나 최소 Regret을 보장하지 않음. 정답 DAG로 후보를 찾는 Oracle-assisted 진단임. |
| 정규화·가중치 | G0-fixed opportunity 분모, subset 내 지표 동일 가중, M4의 G0 active FN/FP/REV/UNRES components 동일 β | 작은 support는 사건당 상대 gain을 키울 수 있다. 파일럿과 별도 민감도 없이는 공정성/중립성 보장으로 표현 금지. 초기-error-count 정규화는 사전 고정 민감도 대안. |
| 비용·벌점 | `C≤B`; add/delete/orient/resolve 각각 1 상대 비용. `P_all=Σ_r w_r(E_off,r+λE_task,r)`, 모든 `w=1`, `λ=1`은 task 사건에 주는 총 배수(누적 `1+λ` 아님). `P_S`와 `P_all`, Decision Regret 별개. | 단위는 연구상 상대 자원이며 원화/제조 비용 추정이 아니다. `λ=1`은 task/off-task 동일 벌점. 비용과 벌점 같은 수정에 중복 부과 금지. |
| 미확정 간선 수정 | 제안 허용은 true-edge add, FP delete, REV orient, UNRES resolve. `delete_unresolved` 키는 `Config`의 호환성 검증값으로만 요구됨. | 후보 생성 함수는 FN→add, FP→delete, REV→orient, UNRES→resolve만 만든다. `delete_unresolved`는 candidate pool에 나오지 않고, 우선순위·실제 지출 비용·정책 결과에 사용되지 않는다. 두 Schema에 이를 **비활성 예약 키**로 명시했다. 주 계약의 수정 연산은 바꾸지 않았다. |
| 예산 | 현재 runner/schema는 `[0,1,2,3,4]` 전체를 실행한다. 분석 역할은 B=0 S0/reference, B=1 보조, B=2 주 후보, B=3/4 포화 진단이다. | 이는 모순이 아니다. Schema 설명을 보완했다. Runner는 예산별 결과를 실행·저장하고 통계 contrast를 계산하지 않는다. 그러므로 분석 역할은 승인된 분석 계약/사전등록에 고정해야 한다. |

정답 그래프 접근은 Oracle-assisted 구조 후보 식별에 한정한다. 학습·추천에 허용된 입력은 공통 관측자료와 정책별 repaired graph다. 추천 행동을 고정한 다음에만 GT analytic evaluator가 실제 손실과 최선 action을 계산한다. 이 firewall이 실제 구현된다고 현재 기술 Gate 보고서와 runner 경로가 주장하지만, 실제 코호트에서의 무누출은 아직 실행 검증 전이다.

## 5. C — 평가·UNRES·통계·실패

**주 비교 권고:** SCM별 B=2에서 전체 M1+M2+M3+M4 Greedy와 Canonical Oracle의 paired 차이를 둔다.

`D_i = R_i(full-metric Greedy, B=2) − R_i(Canonical Oracle, B=2)`; `D_i<0`이면 full-metric Greedy Regret이 낮고, `D_i>0`이면 Canonical Regret이 낮다. 이 대비는 이번 승인 브리프에서 사용자 결정 대상으로 제시한다. **계약 V1의 문구는 `R(i,p,b)−R(i,S0)`를 primary paired contrast라 부르므로, 문서 간 estimand 명칭 충돌은 아직 해소되지 않았다.** 사용자가 B2 Greedy–Canonical을 primary로 승인하면 사전등록 전에 계약의 다음 버전에서 이를 primary로 명시하고, S0 대비 `D_i,p^S0=R_i(p,B=2)−R_i(S0)`를 secondary로 기록해야 한다. 반대로 기존 계약 V1을 유지하면 그 primary를 그대로 따른다. 승인 전 어느 쪽도 동결하지 않는다. 모든 15 subset은 고정 B별 기술 결과로 보고하고 테스트 결과를 본 뒤 승자를 고르지 않는다.

평균/중앙값/표준편차/사분위수 및 SCM 단위 개선·악화·동률 수를 보고한다. **불확실성 요약의 최종 방식은 아직 승인되지 않았다.** 기존 실행 계획의 후보는 개발 SCM에서 사전 지정된 contrast의 SCM-level `s_max`와 사용자 승인 기술 정밀도 half-width `h`를 사용해 `N=ceil((1.96*s_max/h)^2)`를 계획하는 것이다. 이 precision 규칙 및 `h`를 승인할지 결정해야 한다. 이는 우월성 검정이나 power 보장이 아니다. Step5/6 SD는 C의 분산 또는 표본 충분성 근거로 대체 사용할 수 없다.

| C 결정 | 제안/코드 상태 | 승인 권고 |
|---|---|---|
| 잔여 UNRES | 구조 그래프에는 UNRES 유지; 학습 DAG에서는 방향 부모/자식으로 쓰지 않는 abstention encoding. GT 방향으로 채우지 않고 무료 구조 복구로 세지 않음. | APPROVE 주 처리로 제안; 정보 손실로 인해 UNRES 보유 정책에 학습 불이익 가능성을 한계/민감도에 명시. 대체 encoding은 사전 한정 민감도 또는 후속 연구로 제한. |
| 결과·표본 단위 | 독립 SCM; 같은 SCM 내 정책/예산은 반복 측정. B2 full Greedy vs Canonical paired SCM 차이. B1 보조, B3/B4 포화, B0 S0. | 주 contrast와 부호를 승인. 같은 graph/action/regret를 반복 표본처럼 세지 않는다. 동일 action이면 동일 GT 손실/Regret이어야 함. |
| 개발/평가 N | 64 development 및 200 held-out은 제안 목표. Proposal 상한 config 입력; feasibility가 500 proposal 중 494 eligible였으나 이 한 seed pilot 비율은 모집단 보증이 아님. | N=64/200을 잠정 운영 목표로 유지하되 power 확보 N이라고 승인하지 않음. 개발의 blinded-to-evaluation variability 및 처리 자원으로 평가 N/정밀도 규칙을 사전에 결정. Held-out 열람 뒤 N·정책·주 결과 변경 금지. |
| 실패·complete-case | Proposal/admission/전 정책 완료/paired 벡터 수 각각 보존. 정책 일부 실패 SCM은 paired 주 비교에서 제외하되 전체 제안 분모와 원인별 실패율 보고. 실패 Regret=0 대체 금지, admitted SCM 사후 대체 금지. | APPROVE. 실패가 정책 의존적이면 complete-case 선택편향 위험을 결과 한계로 평가; 평가 실패율 차이가 심각하면 효과 결론을 보류. |
| 추정·불확실성 | Runner는 policy·budget별 Regret 기록을 제공할 뿐 통계 분석이나 신뢰구간을 계산하지 않는다. 실행 계획은 development SCM-level `s_max` 및 승인된 정밀도 half-width `h` 기반 N 계획 후보를 제시함. | SCM을 독립 단위로 paired summary. N=64/200은 후보이며 power 보장 아님. 평가 열람 전 불확실성 요약/정밀도 규칙과 primary contrast를 계약에 적어야 함. |
| 환경·실행 승인 | 현재 CPython 3.11.15, NumPy 2.4.6, pandas 3.0.3, NetworkX 3.6.1. 저장소 `requirements.txt` 및 Step4 readiness 기대값은 NumPy 2.4.3, pandas 3.0.1, NetworkX 3.6.1. Runner는 config runtime fingerprint와 manifest fingerprint가 현재 런타임과 완전히 같아야 통과. | 권고는 `requirements.txt`에 고정된 환경에서 Research C 회귀군을 재실행하고 그 fingerprint를 승인 config/manifest에 묶는 것. 현재 실제 연구 CLI는 환경과 bundle이 맞지 않으면 거부됨. |
| Gate·운영 | config의 승인/사전등록 상태, 지원된 과학 설정, proposal/admission 수, budgets, runtime, hashes, output 및 resource limits를 Runner가 검사한다. Resource RSS는 sampled monitor, 저장량은 사전 검사. 실제 bundle 없음. | JSON Schema 파일은 Runner가 직접 로드/검증하지 않는다. Runner는 지원 섹션의 exact-value 비교와 별도 type/resource 검사로 fail-closed 한다. Manifest 생성기와 validate-only CLI도 없음. 외부 공개 preregistration 증명/디지털 서명은 schema·gate가 검증하지 않으므로 사용자 절차에서 따로 기록해야 함. |

### 표본 크기와 자원

64/200은 실행량 제안이지 최소 검정력이나 정밀도 보증이 아니다. 기존 계약은 Step5/6 paired SD 0.0824를 단순 대입한 숫자를 참고로만 제시하며, C의 분산에 적용된다고 주장하지 않는다. runner의 계획 workload는 예산 전체에서 SCM당 최대 65개 고유 graph/model 경로 전후(중복 그래프는 캐시·공유 가능)이고, 실제 시간은 topology 적격률, 오류 후보, 적합 실패와 민감도 수에 따라 달라진다. 생산 상한은 사용자 승인 runtime에서 먼저 작은 승인된 개발 실행의 계측을 본 후 고정해야 한다; 이 기술 검토만으로 N=200의 완료 가능성/통계력은 확정 못 한다.

## 6. 핵심 결정 요청

각 묶음에 대해 하나를 선택하고 필요한 수정값을 승인 기록에 명시해야 한다. 아래 권고값은 편의를 위한 **제안**일 뿐 잠정 계약을 동결하지 않는다.

| 묶음 | 권고 선택 | 사용자 응답 |
|---|---|---|
| **A — 모집단/G0** | 네 topology, 노드 6–10, strict indirect-only, 512 shared observations, signed-linear SCM, q=.15/r=.05, DAG rejection/no redraw, zero-error G0 유지. **추가 선택:** (A1) 현재 코드의 FN/FP/REV recipe-support gate를 승인해 그 조건부 모집단을 대상으로 함; (A2) strict indirect-only 모집단과 일치하도록 C proposal path를 정합화하고 지원 부재를 자연적 zero-candidate 상태로 기록 | `[ ] A1 APPROVE` `[ ] A2 MODIFY (권고)` `[ ] DEFER` |
| **B — 정책/비용** | Rule A + 열린 무조건화 backdoor task zone, S0+15 subsets+Canonical, G0-fixed opportunity 주 분석 및 초기-error sensitivity, 동일 subset metric weights 및 M4 active-component β, 단위 비용/λ=1, B2 primary·B1 보조·B3/4 saturation·B0 reference | `[ ] APPROVE 권고안` `[ ] MODIFY (값 명시)` `[ ] DEFER` |
| **C — 평가/운영** | 잔여 UNRES abstention encoding; B2 `full Greedy − Canonical` paired SCM contrast(음수는 Greedy 유리); 별도 S0 변화; N64 dev/N200 evaluation은 계획 목표로만; complete paired only, 실패/shortfall 전체 보고; 기술 precision rule 및 uncertainty interval을 평가 열람 전에 고정 | `[ ] APPROVE 권고안` `[ ] MODIFY (값 명시)` `[ ] DEFER` |
| **실행환경** | CPython 3.11.15; `requirements.txt`의 NumPy 2.4.3 / pandas 3.0.1 / NetworkX 3.6.1 환경을 권고 | `[ ] APPROVE 권고안` `[ ] MODIFY (버전 명시)` `[ ] DEFER` |
| **운영** | Development admissions 목표 64, Held-out 200은 후보. Generator attempt 상한 386/1,104; 실행별 실제 proposal cap·resource cap은 config에서 사전 고정. Proposal shortfall 및 admitted 후 실패는 보존·대체 금지. | `[ ] APPROVE 권고안` `[ ] MODIFY (수치 명시)` `[ ] DEFER` |
| **상태** | 본 문서는 결정 가능한 제안이며 어떠한 설정도 자동 동결하지 않음. 과학적 A/B/C 상태는 APPROVAL_REQUIRED. | `[ ] READY_FOR_USER_DECISION` |

개별적으로 확정이 필요한 세부값: (1) A의 추가 Q-common support gate(A1/A2), seed master, 목표 admissions별 proposal cap/shortfall stop; (2) B의 Rule B 민감도 수행 여부와 제한된 민감도 시나리오, β/λ/정규화·비용값; (3) C의 primary contrast, N/precision 규칙 및 `h`, paired 결과의 불확실성 보고 방식, production resource limits 및 held-out 결과 접근 시점. Proposal cap 상한은 코드의 topology generator가 development 386, independent-evaluation 1,104로 제한하지만, 이것은 허용 가능한 최대치이지 연구별 승인 cap이 아니다. 어떤 값도 본 문서로 승인되었다고 간주하지 않는다.

A에 대한 권고는 **A2**다. 원 연구 질문은 strict indirect-only task 모집단에서 오류 위치의 우선순위를 비교하는 것이므로, 각 오류 유형의 topology-level recipe가 반드시 존재해야 한다는 조건으로 모집단을 선별하지 않고 지표별 수정 기회 0건도 결과로 포함하는 편이 목표에 더 잘 맞는다. A1을 선택하면 논문 모집단을 “FN/FP/REV recipe support가 모두 있는 Q-common subset”으로 제한해 명시해야 하며, 구조 파일럿 494/500을 그 수율 추정치로 사용하지 않는다.

## 7. 테스트 실패 및 보고 정정

1. **의존성 fingerprint 불일치:** Step4 readiness만 실패, 동결 계약에서 요구하는 Python 패키지 조합과 현재 환경이 다름. Research C 이전에 일치 runtime으로 전환해야 하는 실행환경 게이트.
2. **Step4B4 raw-ledger SHA 불일치:** Git blob 예상 SHA는 보존, raw-byte 테스트와 Windows CRLF checkout 간 차이. frozen 원본 수정 없이 재현환경/개행 핸들링을 별도 정비할 수 있음. 현재 판단상 Research C 계산 격리.
3. **Step4C1 WORK_LOG SHA stale:** 개발용 `NOT_FROZEN` manifest의 기록 파일 해시가 이후 WORK_LOG 추가로 낡음. Step4C2 frozen manifest 및 Research C 데이터/코드는 영향 근거 없음. manifest를 고쳐 통과시키지 않음.

따라서 이 세 건은 현 근거상 Research C 계산 결함을 나타내지 않지만, 첫 번째는 승인 runtime을 고정하기 전에 정리할 재현환경 문제다. 현재 C Runner는 승인 config와 manifest가 **현재** runtime fingerprint와 같으면 실행되므로 Step4 pinned runtime이 C 실행의 코드상 강제값인 것은 아니다. 단, 재현 가능한 승인 환경을 만들기 위해 `requirements.txt` 환경을 권고한다. 어떠한 기준 SHA/동결 원자료도 수정해서는 안 된다.

이전 기술 Gate 보고서의 “positive 경로에서 전체 schema 검증”은 정확도를 낮춰 읽어야 한다. `runner.py`에는 `jsonschema` 호출이 없고 standalone execution manifest schema도 없다. positive gate 테스트는 fixture config를 만들고 Runner의 custom exact-contract, field, hash, runtime, cohort, resource 검사를 지나 TEST_ONLY orchestration hook으로 연결한다. 따라서 JSON 문서의 문법/스키마 자체 검증과 production runtime gate 검증은 별도다. 아래 절차에서 Schema validator를 실행하고, 실행 CLI가 적용하는 custom gate도 별도 설명한다. 실제 CLI에는 preflight-only 모드가 없어 그 CLI 명령은 검증 직후 연구 실행을 시작한다.

## 8. 승인 Bundle 준비 및 승인 후 순서

승인 bundle은 만들지 않았다. 현재 승인 schema는 config에 `USER_APPROVED`, `PREREGISTERED`, cohort, run ID/output, target admissions/proposal cap, 전체 `[0,1,2,3,4]` budgets, population/SCM/task/G0/repair/evaluation, RNG, resource limits, runtime fingerprint를 요구한다. manifest는 승인 상태와 config/manifest/code/commit/tree/runtime/cohort/RNG/resource hash를 묶는다. `PREREGISTERED`는 설정의 상태 문자열이고, public registry URL/ID를 검사하지 않는다. 사용자 제공 승인 bundle 외에 테스트 hook/임시 테스트 승인 객체를 production에서 사용할 수 없다.

계약 v1 및 실행 Gate의 차이를 먼저 승인 기록에 반영하고, 다음 순서로 진행한다.

1. 이 문서의 A/B/C와 실행환경·운영 항목에 사용자가 APPROVE/MODIFY/DEFER로 응답한다.
2. 응답에 맞춰 계약, 분석 계획, 실패/precision/resource 규칙을 업데이트하고 사용자가 검토 가능한 승인본을 만든다. 로컬 연구계약 동결과 외부 preregistration은 구분한다.
3. 승인된 운영 환경(현재 Step4 runtime이면 pinned requirements 설치 후 3개 실패 재검증)을 확정하고, clean commit/tree와 런타임을 기록한다.
4. 승인된 config/manifest를 생성한다. 현재 저장소에는 manifest generator가 없으며, 테스트 helper의 `_approved_bundle`은 TEST_ONLY 테스트에서만 쓰고 복사하지 않는다. Config에는 승인 상태 외에 schema가 요구하는 모든 fields와 실제 사용자 응답을 기록한다. Manifest에는 `approval_status`, `manifest_version`, config/contract/resource hashes, cohort/run/output, runtime, `excluded_untracked_paths=[".build_reframed/"]`, source commit/tree 및 code hashes를 묶는다. 해시는 최종 clean source commit/runtime에서 만든다.
5. Schema 문서는 JSON syntax로 검사하고 JSON Schema validator로 config를 검사한다. Runner 자체는 schema validator가 아니라 custom gate를 실행한다. 실제 연구 CLI에는 validate-only 옵션이 없으므로 다음 명령은 사전검사 명령이 아니라 **Development 코호트 실행 명령**이다. `target_admissions`는 eligible SCM 수 목표이며 완료/paired 수는 실패 후 더 작을 수 있고, `proposal_cap`은 최대 시도 수(현재 generator 상한 development 386)다. 승인된 cap에 도달해도 target 미달이면 shortfall로 종료·기록하고 post-admission 평가 실패 SCM을 대체하지 않는다.
6. Development cohort 실행 후 proposal/admission/failure/complete/paired 수와 resource 측정을 확인한다.
7. 개발 자료에서 사전 허용된 정밀도/실행성 요약과 정책 선택만 수행한다. 선택 규칙이 있으면 held-out 전에 기록·고정한다.
8. 별도 independent-evaluation config, seed namespace, ledger 및 출력 위치를 봉인한다. Held-out 실행은 별도 명시 승인 후 수행하며, 평가 결과 열람 후 N·정책·주 contrast를 변경하지 않는다.

최종 Development 실행 명령은 실제 CLI와 일치한다: `python scripts/run_research_c_runner.py --mode research --approved-config <config.json> --execution-manifest <manifest.json>`. 이 명령은 config/manifest 검증 후 즉시 proposal stage를 시작한다. 승인 전 실행하거나 dry-run으로 오용하지 않는다. 승인 config/manifest가 없는 현재에는 proposal 생성 전에 차단되어야 한다. 이 보고서 작성은 승인 또는 실행 권한을 주지 않는다.

이번 정합화에서 실행한 검증:

```powershell
python -m unittest tests.test_original_objective_proposal_stage_gate tests.test_original_objective_runner tests.test_original_objective_cohort_runner tests.test_original_objective_e2e_fixture tests.test_original_objective_policy_engine tests.test_original_objective_policy_engine_independent tests.test_original_objective_structural_pilot_and_ledger -q
```

**65 tests, 모두 통과.** 두 Schema의 JSON syntax 및 Draft 2020-12 meta-schema 적합성도 통과했다. 이는 Schema 인스턴스에 대한 `jsonschema` 검사를 production Runner가 수행한다는 뜻은 아니다. 미승인 CLI 확인은 `python scripts/run_research_c_runner.py --mode research`에서 `RESEARCH_MODE_BLOCKED: approved config and matching execution manifest are required`로 차단됐다. config/manifest가 없어 proposal/SCM 생성은 일어나지 않았다.

`python scripts/validate_original_research_fixture_contract.py`도 통과했다. 기존 결정적 Fixture 계산, 정규화·예산 케이스를 확인했으며 스크립트가 새 SCM/관측자료/개입/Regret을 생성하지 않았다고 명시했다.

## 9. 검토 근거 파일

- `RESEARCH_C_EXPERIMENT_CONTRACT_V1.md` — 제안 estimand, task zone, Rule A/B, 지표·utility·비용, Regret 정의, sensitivity, N 제안.
- `RESEARCH_C_FINAL_FEASIBILITY_AND_EXECUTION_GATE.md` — 구조 전용 파일럿(500 proposal, 494 eligible) 및 포화/오류 실현 진단. 기준은 구버전이므로 production 준비 관련 문장은 현재 상태로 해석하지 않음.
- `RESEARCH_C_FINAL_TECHNICAL_GATE_REPORT.md` — 최신 기술 판정, TEST_ONLY 범위, production approval gate 및 전체 테스트 요약.
- `RESEARCH_C_EXECUTION_PLAN.md` — 개발/평가 분리, 분석·실행 계획. 일부 생산 runner 미구현 서술은 d9 기준에선 오래된 설명임.
- `RESEARCH_C_RUNNER_3C_IMPLEMENTATION.md` — 상태/기술 진척 설명이 최종 기술 Gate보다 오래된 IN_PROGRESS 기록이며, 이후 Proposal 자원 격리와 approval-gate 연결을 반영하지 않는다. 최신 구현 판정에는 `RESEARCH_C_FINAL_TECHNICAL_GATE_REPORT.md`를 사용하되, 이 문서의 TEST_ONLY 범위를 넘어 연구 양성 실행을 주장하지 않음.
- `research/original_objective/research_c_candidate_config.schema.json`, `research/original_objective/research_c_approved_execution.schema.json` — proposed/approved bundle의 요구 구조.
- `research/original_objective/policy_engine.py` — `Config`, `classify`, `metrics`, subset utility, `common_penalty`, `run`, `run_all` 실제 정의.
- `research/original_objective/runner.py` — `_validate_supported_research_contract` (123행 이후), `run_research_mode` (291행 이후), cohort·proposal cap·runtime/manifest 검사.
- `research/original_objective/execution_limits.py` — `ResourceLimits`와 sampled RSS/사전 저장량 검사의 범위 및 한계.
- `research/original_objective/proposal_pipeline.py` — proposal 생성/assembly와 `run_approved_research_proposal_cohort`.
- `research/original_objective/cohort_runner.py` — proposal ledger, checkpoint, resume, stage time/resource 기록.
- `tests/test_step4_post_freeze_readiness.py`, `tests/test_step4b4_mock_runner.py`, `tests/test_step4c1_production.py` — 재현한 세 실패의 assertion.

## 10. 최종 상태

이 문서는 사용자가 결정할 A/B/C 및 실행환경·운영 선택을 한 표로 제공한다. Schema는 전체 budget execution grid를 요구하고 분석 우선순위는 구분한다. `delete_unresolved`는 비활성 예약 키로 문서화했으며 엔진 동작은 변경하지 않았다. 세 실패 중 2건은 기존 Step4 영역에 격리됐고, 하나는 Step4 fingerprint와 현재 환경 차이다. 더 중대한 미해결 사항은 **현재 production proposal path의 Q-common FN/FP/REV support gate가 schema의 strict indirect-only 모집단 선언에 반영되지 않는 점**이다. 이 gate와 B2 Greedy–Canonical 대 V1의 S0 primary contrast를 사용자가 결정하고 계약에 반영하기 전까지 연구 실행은 차단해야 한다. Schema generic validation, manifest builder, validate-only CLI도 현재 없다.

**연구 C는 사용자 승인과 일치하는 config/manifest가 없으므로 연구 SCM 실행 미승인 상태다. 이 문서 작성은 A/B/C 승인, 사전등록, 기술적 승인 bundle 발급 또는 연구 결과 생성이 아니다.**

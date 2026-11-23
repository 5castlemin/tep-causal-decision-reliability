# Research C — A/B/C 최종 과학적 계약 검토 및 승인 브리프

**기준 커밋:** `d9f0f0f4dd7943aa0084bd1af4b9ba62a3e735fd`  
**상태:** 승인 요청용 제안. 사용자 승인·사전등록·연구 코호트 실행은 완료되지 않았다.  
**범위:** 기존 문서·코드·테스트 검토만 수행했다. 새 SCM, 관측자료, 개입 결과 또는 연구 Regret을 만들지 않았다.

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
| Task | eligible ordered pair에서 균등 선택, strict indirect-only, 직접 `X→Y` 금지 | Schema 표기와 task helper의 정확한 적격 판정을 함께 고정. Task가 코호트 안에서 사전 선택되어야 함. | APPROVE |
| SCM 구조·계수 | signed linear acyclic; 계수 절댓값 `[0.25,0.8]`, 독립 fair sign | 설정은 제안 상수. 이 합성 family 밖 제조 공정으로 일반화 불가. | APPROVE |
| 관측자료·잡음 | SCM당 공통 관측자료 `n=512`; 독립 centered Gaussian noise, SD `[0.8,1.2]`; 정책별 동일 관측자료 | 계수/잡음/표본 생성용 RNG를 분리하고 seed namespace 기록. `n=512`는 효과 추정 정밀도를 보장한 근거가 아님. | APPROVE |
| 행동·목표·손실 | 사전 선택 task, action grid `[-1,-.5,0,.5,1]`; standardized target mean squared error; GT 평가는 analytic hard-do | 동일 action grid와 손실을 전 정책에 적용. 실제 수율·안전·비용 함수가 아님. | APPROVE |
| G0 오류 주입 | 참 adjacency 손상 `q=.15`, 손상 시 FN/REV/UNRES 각 1/3; GT nonadjacent pair FP 제안 `r=.05`, 방향 무작위 | q/r은 제안 확률이지 실현 오류율이 아님. 구조 파일럿에서 eligible 494/500, 오류 없는 G0 55/494 (11.1%); 오류 제안 1,190 중 DAG 수락 1,044·거절 146. FP task/off-task 거절률이 달라 기회 수 기록이 필수. | APPROVE — 이 수치를 고정하고 사후 조정 금지 |
| DAG 거절·재추출 | DAG-invalid 오류 제안은 기록 후 거절, 재추출 없음 | 파일럿과 schema 제안이 일치. proposal 수와 accepted/rejected를 모두 분모와 함께 보존. | APPROVE |
| Task zone·backdoor | 모든 X→Y 단순 유향 경로와 무조건화 상태의 open backdoor 경로; collider 내부 노드가 없는 backdoor만 open. Rule A FP 귀속 | 경로 기반 구조 표식은 실제 개입 손실 자체가 아님. 무조건화 backdoor 한정이며 특정 조건화 집합은 다루지 않음. Rule A는 양 끝점 모두 task-zone node set 내 FP를 task로 태깅하여 내부 chord를 넓게 포함할 수 있음. | APPROVE 주 규칙; Rule B는 고정 민감도 선택으로 별도 승인 |
| 오류 없는 G0·표본 흐름 | G0 오류 0건도 원 proposal/admitted 모집단에 유지. proposal, eligible, admitted, full-policy-complete SCM을 분리 기록 | Feasibility 파일럿은 11.1% zero-error G0. 제거하면 오류율이 있는 구조에 조건부인 다른 연구 질문이 됨. 목표 admissions 미달 시 보고, 임의 대체 금지. | APPROVE |
| Cohort | Development / `independent_evaluation`(표시상 held-out); 별도 seed namespace·ledger·output; 제안 N=64/200 | Schema에는 `independent_evaluation`, generator는 proposal namespace로 `confirmation` 사용. 외부 이름과 내부 RNG binding의 매핑을 manifest에서 고정해야 함. N은 power 보장이 아님. | APPROVE 분리; N은 C 묶음에서 별도 결정 |

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
| 미확정 간선 수정 | 제안 허용은 true edge add, FP delete, REV orient, UNRES를 GT 방향으로 resolve. `delete_unresolved`는 주 후보가 아님. | **승인 전 해소할 schema 불일치:** `research_c_candidate_config.schema.json`은 `delete_unresolved:1`을 required cost table에 포함하지만 계약은 이 연산을 후보에서 제외하고, policy engine은 비용 키를 요구한다. 승인 config는 비용표와 허용 연산을 분리하거나 의미를 명시해야 한다. 이를 실제 사용 비용이라고 오인하면 안 됨. |
| 예산 | 현재 runner/schema는 `[0,1,2,3,4]` 전체 평가를 요구. 계약 v1은 B=1–4 grid, B=0 reference; 최신 feasibility는 B=2 주, B=1 보조, B=3/4 포화 진단을 제안. | 구현이 계산하는 예산과 사전 지정 primary estimand는 다른 개념이다. 분석 우선순위를 승인 config/manifest와 계약에 일치시켜야 함. 권고: B2 주, 나머지는 역할을 위와 같이 사전 지정. |

정답 그래프 접근은 Oracle-assisted 구조 후보 식별에 한정한다. 학습·추천에 허용된 입력은 공통 관측자료와 정책별 repaired graph다. 추천 행동을 고정한 다음에만 GT analytic evaluator가 실제 손실과 최선 action을 계산한다. 이 firewall이 실제 구현된다고 현재 기술 Gate 보고서와 runner 경로가 주장하지만, 실제 코호트에서의 무누출은 아직 실행 검증 전이다.

## 5. C — 평가·UNRES·통계·실패

**주 비교 권고:** SCM별 B=2에서 전체 M1+M2+M3+M4 Greedy와 Canonical Oracle의 paired 차이를 둔다.

`D_i = R_i(full-metric Greedy, B=2) − R_i(Canonical Oracle, B=2)`; `D_i<0`이면 full-metric Greedy Regret이 낮고, `D_i>0`이면 Canonical Regret이 낮다. 이것은 최신 feasibility 문서가 명시적으로 주 비교 하나로 확정한 값은 아니므로 승인할 contrast다. 계약 v1의 기존 primary는 `R(i,p,b)−R(i,S0)`로 정의돼 있어 불일치가 있다. S0 대비 변화는 별도 `D_i,p^S0=R_i(p,B=2)−R_i(S0)`로 보고한다. 모든 15 subset은 고정 B별 결과로 기술 보고하고, 테스트 결과를 본 뒤 승자를 고르지 않는다.

평균/중앙값/표준편차/사분위수 및 SCM 단위 개선·악화·동률 수를 보고하고, **사용자 승인 전 불확실성 구간 방식은 확정되지 않았다.** 권고 가능한 옵션은 paired SCM 차이를 독립 단위로 재표집하는 사전 고정 bootstrap percentile 구간이며, 사용할 경우 반복 횟수·seed·구간 수준을 미열람 전에 고정한다. 이를 confirmatory p-value나 우월성 검정으로 바꾸지 않는다. Step5/6의 SD는 Research C의 검정력 보장이 될 수 없다.

| C 결정 | 제안/코드 상태 | 승인 권고 |
|---|---|---|
| 잔여 UNRES | 구조 그래프에는 UNRES 유지; 학습 DAG에서는 방향 부모/자식으로 쓰지 않는 abstention encoding. GT 방향으로 채우지 않고 무료 구조 복구로 세지 않음. | APPROVE 주 처리로 제안; 정보 손실로 인해 UNRES 보유 정책에 학습 불이익 가능성을 한계/민감도에 명시. 대체 encoding은 사전 한정 민감도 또는 후속 연구로 제한. |
| 결과·표본 단위 | 독립 SCM; 같은 SCM 내 정책/예산은 반복 측정. B2 full Greedy vs Canonical paired SCM 차이. B1 보조, B3/B4 포화, B0 S0. | 주 contrast와 부호를 승인. 같은 graph/action/regret를 반복 표본처럼 세지 않는다. 동일 action이면 동일 GT 손실/Regret이어야 함. |
| 개발/평가 N | 64 development 및 200 held-out은 제안 목표. Proposal 상한 config 입력; feasibility가 500 proposal 중 494 eligible였으나 이 한 seed pilot 비율은 모집단 보증이 아님. | N=64/200을 잠정 운영 목표로 유지하되 power 확보 N이라고 승인하지 않음. 개발의 blinded-to-evaluation variability 및 처리 자원으로 평가 N/정밀도 규칙을 사전에 결정. Held-out 열람 뒤 N·정책·주 결과 변경 금지. |
| 실패·complete-case | Proposal/admission/전 정책 완료/paired 벡터 수 각각 보존. 정책 일부 실패 SCM은 paired 주 비교에서 제외하되 전체 제안 분모와 원인별 실패율 보고. 실패 Regret=0 대체 금지, admitted SCM 사후 대체 금지. | APPROVE. 실패가 정책 의존적이면 complete-case 선택편향 위험을 결과 한계로 평가; 평가 실패율 차이가 심각하면 효과 결론을 보류. |
| 추정·불확실성 | 현재 문서/runner는 paired Regret과 S0 contrast 제공. 전역 검정·다중비교 보정은 확정되어 있지 않음. | 모든 subset/예산은 탐색·기술 통계. 우월성 가설검정은 본 Gate에 포함하지 않음. bootstrap 옵션 및 사전 고정 세부값은 명시적으로 결정. |
| 운영·실행 승인 | Schema는 USER_APPROVED+PREREGISTERED config/manifest, commit/runtime/hash, cohort/RNG/resource binding을 요구. 실제 USER_APPROVED bundle은 없음. Resource 측정은 sampled RSS이며 hard OS quota 아님; storage는 검사이지 filesystem quota 아님. | 실제 runtime fingerprint를 고정·맞춘 뒤 별도 실행 승인을 해야 함. 현재 Research Mode는 미승인으로 차단된 상태를 유지. |

### 표본 크기와 자원

64/200은 실행량 제안이지 최소 검정력이나 정밀도 보증이 아니다. 기존 계약은 Step5/6 paired SD 0.0824를 단순 대입한 숫자를 참고로만 제시하며, C의 분산에 적용된다고 주장하지 않는다. runner의 계획 workload는 예산 전체에서 SCM당 최대 65개 고유 graph/model 경로 전후(중복 그래프는 캐시·공유 가능)이고, 실제 시간은 topology 적격률, 오류 후보, 적합 실패와 민감도 수에 따라 달라진다. 생산 상한은 사용자 승인 runtime에서 먼저 작은 승인된 개발 실행의 계측을 본 후 고정해야 한다; 이 기술 검토만으로 N=200의 완료 가능성/통계력은 확정 못 한다.

## 6. 핵심 결정 요청

각 묶음에 대해 하나를 선택하고 필요한 수정값을 승인 기록에 명시해야 한다. 아래 권고값은 편의를 위한 **제안**일 뿐 잠정 계약을 동결하지 않는다.

| 묶음 | 권고 선택 | 사용자 응답 |
|---|---|---|
| **A — 모집단/G0** | 네 topology, 노드 6–10, strict indirect-only, 512 shared observations, Gaussian signed-linear SCM, q=.15/r=.05, true-edge error mix 균등, DAG rejection/no redraw, zero-error G0 포함 | `[ ] APPROVE 권고안` `[ ] MODIFY (값 명시)` `[ ] DEFER` |
| **B — 정책/비용** | Rule A + 열린 무조건화 backdoor task zone, S0+15 subsets+Canonical, G0-fixed opportunity 주 분석 및 초기-error sensitivity, 동일 subset metric weights 및 M4 active-component β, 단위 비용/λ=1, B2 primary·B1 보조·B3/4 saturation·B0 reference | `[ ] APPROVE 권고안` `[ ] MODIFY (값 명시)` `[ ] DEFER` |
| **C — 평가/운영** | 잔여 UNRES abstention encoding; B2 `full Greedy − Canonical` paired SCM contrast(음수는 Greedy 유리); 별도 S0 변화; N64 dev/N200 evaluation은 계획 목표로만; complete paired only, 실패/shortfall 전체 보고; 기술 precision rule 및 uncertainty interval을 평가 열람 전에 고정 | `[ ] APPROVE 권고안` `[ ] MODIFY (값 명시)` `[ ] DEFER` |

개별적으로 확정이 필요한 세부값: (1) A의 seed master 및 proposal cap/shortfall stop, (2) B의 Rule B를 민감도로 실행할지, 승인 config에서 `delete_unresolved` 키를 허용 연산과 분리하는 방식, 정확한 β/λ/정규화·비용 시나리오, (3) C의 uncertainty interval/bootstrap 세부값, N/precision stopping rule, production resource limits 및 held-out 공개 시점. 어떤 것도 본 문서로 승인되었다고 간주하지 않는다.

## 7. 전체 테스트 세 실패 — 최종 판정

1. **의존성 fingerprint 불일치:** Step4 readiness만 실패, 동결 계약에서 요구하는 Python 패키지 조합과 현재 환경이 다름. Research C 이전에 일치 runtime으로 전환해야 하는 실행환경 게이트.
2. **Step4B4 raw-ledger SHA 불일치:** Git blob 예상 SHA는 보존, raw-byte 테스트와 Windows CRLF checkout 간 차이. frozen 원본 수정 없이 재현환경/개행 핸들링을 별도 정비할 수 있음. 현재 판단상 Research C 계산 격리.
3. **Step4C1 WORK_LOG SHA stale:** 개발용 `NOT_FROZEN` manifest의 기록 파일 해시가 이후 WORK_LOG 추가로 낡음. Step4C2 frozen manifest 및 Research C 데이터/코드는 영향 근거 없음. manifest를 고쳐 통과시키지 않음.

따라서 이 세 건은 현 근거상 Research C 계산 결함을 나타내지 않지만, 첫 번째는 Research C를 실행할 승인 runtime 고정 문제로 남는다. 어떠한 기준 SHA/동결 원자료도 수정해서는 안 된다.

## 8. 승인 Bundle 준비 및 승인 후 순서

승인 bundle은 만들지 않았다. 현재 승인 schema는 config에 `USER_APPROVED`, `PREREGISTERED`, cohort, run ID/output, target admissions/proposal cap, 전체 `[0,1,2,3,4]` budgets, population/SCM/task/G0/repair/evaluation, RNG, resource limits, runtime fingerprint를 요구한다. manifest는 승인 상태와 config/manifest/code/commit/tree/runtime/cohort/RNG/resource hash를 묶는다. 사용자 제공 승인 bundle 외에 테스트 hook/임시 테스트 승인 객체를 production에서 사용할 수 없다.

계약 v1 및 실행 Gate의 차이를 먼저 승인 기록에 반영하고, 다음 순서로 진행한다.

1. 이 문서의 A/B/C에 사용자가 APPROVE/MODIFY/DEFER로 응답한다.
2. 응답에 맞춰 계약, 분석 계획, 실패/precision/resource 규칙을 업데이트하고 사용자가 검토 가능한 승인본을 만든다. 로컬 연구계약 동결과 외부 preregistration은 구분한다.
3. 승인된 운영 환경(현재 Step4 runtime이면 pinned requirements 설치 후 3개 실패 재검증)을 확정하고, clean commit/tree와 런타임을 기록한다.
4. `research_c_approved_execution.schema.json`을 충족하는 config와 대응 manifest를 생성·해시 검증한다. `delete_unresolved` 의미와 budget primary grid의 차이는 먼저 제거한다.
5. Development cohort만 별도 명시적 실행 지시 후 실행한다. proposal/admission/failure/complete/paired 모든 수와 자원을 보존한다.
6. 개발 자료에서 사전 허용된 정밀도/실행성 요약과 정책 선택만 수행한다. 선택 규칙이 있으면 held-out 전에 기록·고정한다.
7. 별도 independent-evaluation config, seed namespace, ledger 및 출력 위치를 봉인한다. Held-out 실행은 별도 명시 승인 후 수행하며, 평가 결과 열람 후 N·정책·주 contrast를 변경하지 않는다.

현재 CLI 형식은 `python scripts/run_research_c_runner.py --mode research --approved-config <config.json> --execution-manifest <manifest.json>`이다. 승인 config/manifest가 없는 현재 상태에서 해당 명령은 proposal 생성 전에 차단되어야 한다. 이 보고서 작성은 승인 또는 실행 권한을 주지 않는다.

## 9. 검토 근거 파일

- `RESEARCH_C_EXPERIMENT_CONTRACT_V1.md` — 제안 estimand, task zone, Rule A/B, 지표·utility·비용, Regret 정의, sensitivity, N 제안.
- `RESEARCH_C_FINAL_FEASIBILITY_AND_EXECUTION_GATE.md` — 구조 전용 파일럿(500 proposal, 494 eligible) 및 포화/오류 실현 진단. 기준은 구버전이므로 production 준비 관련 문장은 현재 상태로 해석하지 않음.
- `RESEARCH_C_FINAL_TECHNICAL_GATE_REPORT.md` — 최신 기술 판정, TEST_ONLY 범위, production approval gate 및 전체 테스트 요약.
- `RESEARCH_C_EXECUTION_PLAN.md` — 개발/평가 분리, 분석·실행 계획. 일부 생산 runner 미구현 서술은 d9 기준에선 오래된 설명임.
- `research/original_objective/research_c_candidate_config.schema.json`, `research/original_objective/research_c_approved_execution.schema.json` — proposed/approved bundle의 요구 구조.
- `research/original_objective/policy_engine.py` — `Config`, `classify`, `metrics`, subset utility, `common_penalty`, `run`, `run_all` 실제 정의.
- `research/original_objective/runner.py` — `_validate_supported_research_contract` (123행 이후), `run_research_mode` (291행 이후), cohort·proposal cap·runtime/manifest 검사.
- `research/original_objective/proposal_pipeline.py` — proposal 생성/assembly와 `run_approved_research_proposal_cohort`.
- `research/original_objective/cohort_runner.py` — proposal ledger, checkpoint, resume, stage time/resource 기록.
- `tests/test_step4_post_freeze_readiness.py`, `tests/test_step4b4_mock_runner.py`, `tests/test_step4c1_production.py` — 재현한 세 실패의 assertion.

## 10. 최종 상태

이 문서는 사용자가 결정할 단일 A/B/C 권고안을 압축한다. 승인할 핵심 통계 대비는 B=2에서 full-metric Greedy 대 Canonical Oracle로 제안하며, 계약 v1에 기재된 S0 대비와 그 역할을 구분했다. Config/schema의 비용 키 및 budget-grid 차이는 실행 전 정합화가 필요하다. 테스트 실패 중 1건은 실행환경을 고정해야 한다는 선행조건이며 두 manifest 문제는 기존 Step4 영역에 격리됐다고 판단한다.

**연구 C는 사용자 승인과 일치하는 config/manifest가 없으므로 연구 SCM 실행 미승인 상태다. 이 문서 작성은 A/B/C 승인, 사전등록, 기술적 승인 bundle 발급 또는 연구 결과 생성이 아니다.**

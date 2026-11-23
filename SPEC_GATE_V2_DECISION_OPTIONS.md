# Specification Gate V2 — 결정 옵션과 승인 대기

**상태: 검토자료. 아래 어느 선택도 사용자 승인 또는 사전등록으로 해석하지 않는다.**

| ID | 결정 | Option A | Option B/대안 | 현재 권고와 근거 |
|---|---|---|---|---|
| Z1 | M4 backdoor zone | 모든 X-in arrow로 시작하는 simple X–Y paths (collider 포함) | 지정 conditioning set에서 open/active paths | Outcome estimand와 conditioning policy를 먼저 정의해야 함. 무조건 “confounder”라고 부르는 오류 방지. |
| Z2 | FP task tag | 두 끝점이 task zone node set 내부 | A + 관련 boundary edge가 causal/open-backdoor route 새로 생성 | 둘 다 동일한 구조 fixture로 sensitivity 가능. 결과 보고 선택 금지. |
| Z3 | M3 unresolved | `Q/(C+R+Q)` rate와 count 동시 보고 | 별도 unresolved odds/risk summary | 원문 denominator 모호. 정확도 단독 사용은 금지. |
| Z4 | M4 scalar | vector-only reporting | 정규화된 component weighted sum | 기본은 vector. Scalar 선택 시 `α`를 사전 승인. |
| P1 | Equal quota A | equal edit-count slots from `floor(B/c_ref)`; actual C≤B hard constraint | equal cost subbudgets per metric | Edit-count 후보는 B=1의 S15=S1 예측 가능. Cost subbudget는 fractional/stranded cost 규칙이 더 필요. |
| P2 | Shared greedy B | `ΔU_S / cost` on shared remaining budget | Pareto frontier then fixed tie/weight rule | Cross metric normalization과 M3/M4 scalar 없이 실행 불가. |
| P3 | Multi-metric event | 한 edit 비용 한 번, quota를 initiating metric에 귀속, 모든 score 재계산 | 같은 edit이 개선한 여러 metric quota 모두 채움 | 후자는 quota를 더 빠르게 소진시키고 전략 의미가 바뀜. 둘 중 하나를 고정해야 함. |
| C1 | M4 error penalty | event-wise `w_r×λ` 한 번 적용, no extra α | M4 aggregate α plus other error weights | A는 double-count 위험이 적음; unresolved term도 별도 결정해야 함. |
| C2 | λ interpretation | task-zone total multiplier λ | base + incremental multiplier `1+λ` | 비용 DOCX 문언만으로 불명. 수식 의미를 사용자 확인. |
| C3 | orientation costs | `c_ori/c_add={1,2,3}`; no edit if unaffordable | common-support B stratum additionally reports costs | 원 민감도 범위 보존; B/cell infeasibility 공개. |
| C4 | Best policy | minimum among 16 registered catalog only | add exhaustive edit-sequence oracle as separate upper bound | 전역 최적 claim 금지; oracle 정보량/계산범위 명시. |

## 고정 원칙

- M1 비과제 누락률, M2 비과제 허위 연결률, M3 비과제 conditional direction accuracy + unresolved, M4 causal-path/confounder zone errors를 유지한다.
- 15 nonempty subsets + no-edit baseline 유지.
- existing 14 FN/FP/REV order policies는 다른 연구 질문이므로 재사용하지 않는다.
- 구조 잔존 penalty 최소화 subject to `C≤B`와 downstream Decision Regret을 분리한다.
- 평가자 oracle와 정책 정보는 분리한다. GT effect/regret은 eligibility, edit ranking, coefficient/weight selection에 쓰지 않는다.
- Step 5/6은 이미 열람·보고됐으므로 이 복원 연구의 미열람 validation set으로 재사용하지 않는다.
- 신규 SCM/Regret/cost estimation은 이번 Gate에서 생성하지 않는다.

## 구현/사전등록 전 Gate

1. Z1–Z4와 P1–P3/C1–C4 중 정의 결정.
2. 수작업 fixture에서 formulas, denominators, DAG validity, exact-once bucketing 일치 확인.
3. `C`, `P`, `R` scale와 M4/unresolved penalty 처리 결정.
4. 정책 A/B의 utility, tie, budget, fail/unused rule을 코드 전 문서화.
5. 기존 동결 자료와 분리된 development/evaluation 표본 및 sample/analysis contract를 별도 검토.

현재는 `SPECIFICATION REVIEW / NOT PREREGISTERED`다. 이 문서만으로 정책 코드 구현이나 실험 실행이 승인되지 않는다.

# Research E 최종 감사 — C–D–E 과학적 종료

감사일: 2026-11-26. 이 보고서는 기존 결과의 재집계·저장 감사만 포함하며 새로운 SCM, G0, 학습 표본, DRF 또는 개입 응답을 만들지 않았다.

## 판정

- Research E 과학적 Gate는 기존대로 `RESEARCH_E_CORE_COMPLETED_WITH_LIMITATIONS`다. D의 unit-level 확장 분석은 이번 감사에서도 수행되지 않았다.
- 프로젝트 종료 Gate는 C/D의 동결 증거와 E의 정정·통합을 근거로 `PROJECT_RESEARCH_C_D_E_CLOSED_WITH_DOCUMENTED_LIMITATIONS`를 권고한다. 이 Gate에는 PR #44 병합 및 병합 후 CI 확인이 전제된다.
- PR #44는 이 감사 시작 시점에 Open, mergeable이었으며 원격 main은 `bf72d8dd38a2209f365fac7356e8595974509e6c`, Research E head는 `afc09334319a0a9dcbb7aa4093dafc304a2ee4fa`였다. 본 감사에는 후속 커밋이 추가된다.

## 무결성 및 연구 실행 provenance

원래 Research E integrity manifest의 7개 source file hash, 19개 public aggregate hash, 19개 SVG hash가 모두 현재 파일과 일치했다. 별도로 C cohort/proposal SQLite 네 파일과 저장된 D audit summary의 SHA-256을 원 manifest와 대조했고 전부 일치했다. C DB와 D 요약의 digest는 `final_audit_summary.json`에 기록했다. 기존 D audit 요약은 31,584-byte 파일이며 27개 검사가 통과했다고 기록하지만, 이는 이전 검사의 요약 기록이다.

C의 로컬 unit 결과는 unique key 기준 42,704행(Development 8,704 = 64×17×8, Held-out 34,000 = 200×17×10)이었다. Adaptive M4는 2,512행, reference learner는 264행, target sensitivity는 19,800행이며 기대 unit 수와 중복 검사에 통과했다. 원래 B0–4 영역 22,440행의 graph hash, edit log, action 재생 결과를 E2 요약 및 코드에 따라 확인했다. Regret 비교는 실행 코드의 `abs(diff)<1e-12` 허용오차를 사용하므로 부동소수점 bitwise 동일성이라 부르지 않는다.

`run_e2_reconstruction.py`는 truth specification digest, observation-array digest, action/target을 ledger binding과 비교한다. G0를 별도 독립 digest와 대조하지는 않으며, 원 payload의 초기 graph를 사용한 B0 결과 graph hash/edit/action 대조를 통한 간접 확인이다. `run_e2_reconstruction.py`와 `run_e3_exploratory.py`는 출력 파일을 `w` 모드로 기록하여 기존 경로를 덮어쓸 수 있다. 이 감사는 해당 실행기를 재호출하지 않았다. 이번 감사 스크립트는 출력 파일이 이미 있으면 실패하도록 `x` 모드를 사용하고 분석 결과 파일도 새 경로에 분리했다. 과거 E 실행 revision 및 산출물은 변경하지 않았다.

현재 Research D 지정 외부 경로 `C:/DAT_RESEARCH/research-d`에는 `final-reaudit-20261126.json`만 발견했다. 원시 response vectors, recommendation rows, training frame은 없어 새 독립 분석을 재현하지 않았다. 이전 C–D closeout의 27개 원시자료 검사는 기존 보고서에 남아 있지만 이번에는 이를 재실행한 것으로 표현하지 않는다. 따라서 D 관련 E 예산 확장, D adaptive 분석, unit-level two-source 재계산은 미실행으로 유지한다.

## 정정 결과

### 구조 복원과 잔여 오류

Bmax에서 M4가 완전히 reference graph를 복원한 비율은 Development 18/64 (28.125%), Held-out 80/200 (40.0%)다. 나머지 46/64 및 120/200에는 잔여 오류가 있었다. M2+M4의 완전 복원은 27/64 (42.1875%), 109/200 (54.5%)였고 잔여 오류는 37/64, 91/200이다. 평균 잔여 오류 수는 M4 1.421875/1.38, M2+M4 0.71875/0.655다. 정책 후보 소진을 구조 복원으로 잘못 부르지 않는다.

### DAG constraint saturation

constraint saturation은 여러 policy/cohort 조합에서 관찰됐다. Development에서는 M1, M1+M3, M1+M3+M4, M1+M4가 각각 1/64였다. Held-out에서는 M1 1/200, M1+M3 2/200, M1+M3+M4 4/200, M1+M4 3/200, M3 1/200, M3+M4 3/200, M4 2/200이었다. 이 비율은 candidate exhaustion 및 complete restoration과 다른 종료 상태다. 전체 값은 `corrected_saturation_rates.csv`에 있다.

### B=3 cohort 혼동 및 확장 곡선

C Held-out B=3에서 M4 regret/cost는 0.00143536/0.760, Adaptive M4는 0.00096391/0.780, M2+M4는 0.00463471/1.350, Full Greedy는 0.00816650/1.790이다. 앞서 Adaptive 보고서의 1.325는 Research D Full Greedy의 B=3 비용이므로 정정했다.

M4 평균 regret은 B3→4에서 0.001435로 같았으나 B5에서 0.001299로 낮아졌다. 따라서 B3은 일반 포화점이 아니다. B5–9 Held-out에서 M4는 0.00129902, Full Greedy/M2+M4/Adaptive는 0.00082758이다. 비용·편익은 cohort 평균이며 unit별 비단조 결과를 감추지 않는다.

## Reference learner와 적응형 정책

동일하게 복원된 관측 학습자료를 쓴 reference-DAG learner는 Development 평균 Regret 0.00255992, 중앙값 0, 양의 regret 1/64, grid-optimal action 일치 63/64였다. Held-out은 평균 0.00082758, 중앙값 0, 양의 regret 2/200, 일치 198/200이었다. 이는 reference structure 진단이지 decision-optimal oracle가 아니다. Bmax에서 Full Greedy와 Canonical Oracle은 reference learner 행동과 264/264 일치했다. M2+M4도 잔여 구조 오류가 있는데 264/264 일치했고, M4는 263/264 일치했다. 표본 learner action의 일치가 구조적 완전성을 뜻하지 않는다.

Adaptive M4는 제한된 one-blocker heuristic이다. Held-out B3에서 Adaptive−M4 regret 차이는 −0.000471447 (paired SCM bootstrap 95% interval [−0.001414341, 0]); 개선 1/200, 악화 0/200, 동률 199/200, 평균 edit 차이 +0.020이다. blocker edit는 B3부터 두 개의 SCM에서 총 2회 발생했지만 이를 두 건의 개선으로 계산하지 않는다. Development blocker edit는 0건이다. 선택된 한 사례를 해결한 설계 동기와 별개로 보편적 우월성은 검증되지 않았다.

## 확장 비용–성능 분석

추가 집계는 기존 C unit-level 결과와 Adaptive 결과만으로 18개 repair 정책(원래 17 + Adaptive) 및 모든 cohort-budget 조합을 재구성했다. Bmax Held-out의 fixed-budget frontier는 S0@B9 (cost 0, regret .093439), M3@B9 (.425, .092477), M4@B9 (.790, .001299), Adaptive M4@B9 (.810, .000828)다. Cross-budget frontier에는 같은 좌표를 공유하는 B0 무수정 정책들이 tie로 보존되며, 그 밖에 M3@B1, M4@B1–3, Adaptive M4@B3 및 Adaptive M4@B5–9가 포함된다. Full Greedy는 관측 mean cost/loss 좌표에서 frontier에 들지 않는다. Frontier는 관측 평균의 기술적 비교이며 통계적 우월성이 아니다.

C held-out `Jλ = mean regret + λ × mean edit count` lower envelope에 Adaptive를 추가하면 λ=0 구간 최저 loss는 Adaptive M4 B5–9 tie, 이후 관측 선택은 λ≈0.0045445에서 Adaptive B3, λ≈0.0235724에서 M4 B3, λ≈0.0392675에서 M4 B2, λ≈0.1287068 이후 no-edit policies tie다. 정확한 경계와 모든 동률 label은 `expanded_lambda_lower_envelope.csv`에 있다. λ는 가상 edit penalty이고 금전 비용이 아니다. 각 pair 교점이 lower envelope를 바꾸는 것은 아니므로 전환점만 보고한다.

확장 Pareto 안정성은 cohort unit을 paired로 재표집한 2,000회 bootstrap (seed 2026112699)에서 경험적 frontier 포함 빈도로 기록했다. 이는 post-hoc 표본 민감도 기술량이지 확률적 정책 우월성이나 새로운 독립 표본의 증거가 아니다. CSV는 `expanded_pareto_bootstrap_stability.csv`다. B0의 다수 identical zero-edit 후보는 좌표 tie로 모두 frontier에 남으므로 inclusion 1.0도 성능 차이를 뜻하지 않는다.

Research D에서 graph-free baseline은 B=2에서 edit-count 0 및 loss 0.789362로 Full Greedy와 동일 loss다. 이 좁은 좌표에서는 Full Greedy를 지배한다. D unit-level 예산 확장이 불가능해 전체 D Pareto 비교로 확대하지 않았다.

## 목표값 민감도

δ=0은 모든 C SCM에 공통 target `mean(Y_train)`을 쓰는 특수한 평균 편차 최소화 과제다. M4 B2는 모든 Development 64개 및 Held-out 200개에서 standardized k=0을 추천했다. True grid optimum은 각각 58/64 및 185/200에서 내부 action이었다. 선택 행동과 최적 행동 일치는 각각 42/64와 138/200이었다. 따라서 이 민감도 결과는 target/task 정의의 의존성을 보여주지만 여러 효과크기나 제조 목표에 대한 일반 강건성을 입증하지 않는다.

## 해석 및 종료 범위

C는 동결된 계약 내 synthetic SCM confirmatory Primary, M4는 Development-selected Secondary다. Mechanism은 원본 Ledger를 재검증한 post-hoc 분석이다. D는 단일 DRF-based external semisynthetic DGP의 조건부 강건성이다. E는 이미 결과를 본 뒤 수행한 post-hoc 예산·비용·adaptive·target 확장이다. C의 독립 SCM과 D의 graph corruption draws를 합치지 않고 각 loss scale도 비교하지 않는다. Reference/Oracle 구조를 제공한 조건, 고정 action/target, 모델링 및 원자료 불확실성 미포함, 두 D 정밀도 기준 미달, graph-free baseline의 경쟁력, edit count만 비용으로 셈한 점은 결론에 남는다.

연구 결과는 제한된 수정 예산의 배분이 task 및 목표와 오류 구조에 따라 달라질 수 있음을 시사한다. 실제 제조 운영비, 생산성, 안전성 또는 현장 효과를 입증하지 않는다. Research F/G/H는 이번 프로젝트에서 설계·실행하지 않는 향후 방향으로만 남긴다.

## 재현 및 감사 산출물

- `final_audit_summary.json`: provenance hash, row counts, corrected rates, reference learner, paired contrasts, bootstrap seed/범위, D audit 접근 제한.
- `expanded_pareto_frontiers.csv`, `expanded_lambda_lower_envelope.csv`, `expanded_lambda_breakpoints.csv`, `expanded_pareto_bootstrap_stability.csv` and figures E9/E10.
- `reference_learner_summary.csv`, `corrected_saturation_rates.csv`, `adaptive_blocker_counts.csv`.
- `research/budget_adaptive_repair/final_audit.py`: 기존 로컬 결과만 읽는 aggregate auditor. 연구 표본 생성 기능 없음.

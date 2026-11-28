# 불완전한 인과그래프, 어디부터 고칠 것인가?

> **Canonical taxonomy:** 이 최종 서술은 Research 0–4를 사용합니다. 기존 실행 ID는 원본 계약과 provenance 추적을 위해 유지합니다. 상세 매핑과 숫자순 자료 경로는 [Research Naming Map](docs/RESEARCH_NAMING_MAP.md) 및 [Research Index](research/README.md)를 참조하세요.

## 의사결정 중심의 오류 수정 우선순위와 제한된 자원의 배분

영문 제목 후보: **Beyond Structural Accuracy: Decision-Oriented Repair Prioritization in Imperfect Causal Graphs**  
팀: 닦고조이고기름치자  
상태: C–D–E, S4/S5 및 S6 사후 재분석을 통합했다. S6 B=1 policy matrix를 Development 80/replication 160 저장 SCM records에서 보완 재집계했다. S7 본 실행은 0/400 G0, 0/24,000 recommendations로 끝났으며 evaluator는 시작하지 않았다. 마지막 supervisor resource report가 없어 실행 cap 적용 여부와 종료 사유는 검증되지 않았다. 별도 exact task-zone feasibility만 성공했다. 전체 상태와 한계는 [S6–S7 closeout](research/supplementary_validation/S6_S7_CURRENT_CLOSEOUT.md), [S6 policy matrix](research/supplementary_validation/s6/S6_B1_POLICY_MATRIX_CLOSEOUT.md), [S7 computational closeout](research/supplementary_validation/s7/S7_COMPUTATIONAL_CLOSEOUT.md)에 기록한다.

## 1. Executive Summary

The canonical narrative uses Research 0–4; legacy experiment IDs in source artifacts remain for provenance. See the [naming map](docs/RESEARCH_NAMING_MAP.md) for the complete mapping.

이 연구는 인과그래프를 전체적으로 더 정확하게 만드는 일과, 주어진 조작 과제의 추천 손실을 줄이는 일이 같지 않다는 문제에서 출발했다. 최종 질문은 **불완전한 그래프에서 제한된 수정 예산을 어떤 구조 오류에 배분할 때 의사결정 손실이 어떻게 달라지는가**이다.

동결된 Research C 합성 평가의 Held-out 200 SCM에서 B=2 Full Greedy는 무수정 대비 평균 regret을 0.07483636 낮췄다(95% paired-t CI [0.05089822, 0.09877450]). Development에서 선택된 M4는 Held-out에서 더 적은 편집으로 낮은 평균 regret을 보였지만, 이는 보조적 정책 비교이며 모든 환경의 우월성을 뜻하지 않는다. 원본 Ledger에 대한 사후 메커니즘 분석은 과제 관련 경로와 효과 방향이 중요할 수 있음을 보였고 동시에 off-task 오류가 DAG 제약을 풀거나 유효한 경로를 끊는 반례도 확인했다.

Research D 및 신규 S5는 서로 다른 Station1 반합성 실행이다. S5는 단일 DRF DGP와 고정 학습자료에 조건부인 200 G0 corruption draws다. B=2의 S0−M4 평균 tracking-loss 차이는 +0.00685175였지만, action Monte Carlo를 포함한 두 구간은 0을 포함했다. Graph-free association의 평균 손실은 M4보다 조금 낮았다. S4의 T5 독립 복제는 점 추정치가 M4보다 낮았지만 160 SCM paired interval이 0을 포함하고 사전 정밀도 목표를 약간 놓쳤다.

Research E의 기존 C 확장은 예산 편익이 비단조이고 최적 정책·예산이 가상 수정 비용 λ에 따라 바뀔 수 있음을 보였다. 이번 최종 extension은 저장된 S4/S5 단위 자료를 재집계했지만 새 B=5–9 replay는 수행하지 않았다. 그러므로 비용 기반 선택은 표본 내 기술적 민감도이며 기업의 실제 경제적 최적값은 아니다.

**최종 답:** 참조 구조와 과제가 주어진 실험에서는 과제 관련 구조 정보가 적은 수정 예산의 후보 순위를 정하는 데 유용할 수 있다. 다만 구조 오류 유형·위치·대체 경로·DAG 제약 및 목표함수에 따라 실제 편익이 달라지며, T5의 추가 가치, 보편적 최적 예산, graph-based 방법의 graph-free 대비 우월성, 현장 효과는 확정되지 않았다.

## 2. 연구 배경과 질문의 발전

초기 TEP 연구는 정상 운전 관측자료에서 여러 causal discovery 방법의 그래프를 참고 구조와 비교했다. 그러나 참고 구조는 완전한 물리적 인과 ground truth로 확증되지 않았고, 관측 예측 적합도나 F1/SHD가 실제 개입 효과를 보증하지 않았다. 공개 TEP 데이터·시뮬레이터와의 실행·개입 정합성 역시 본 프로젝트에서 완전한 물리 검증 기준으로 확립되지 않았다.

통제 가능한 참 구조와 개입 손실이 필요해 연구는 합성 SCM으로 이동했다. 이 전환은 TEP 제조공정 효능을 증명하기 위한 것이 아니라 연구 질문을 식별 가능한 실험으로 제한하기 위한 것이었다. 초기 합성 분석에서 비슷한 전역 구조 점수를 가진 그래프도 task 경로의 오류 위치에 따라 추천 행동과 regret이 달라질 수 있다는 사례가 나타났다. 이후 연구 초점은 “어떤 discovery 알고리즘이 F1이 높은가?”에서 “알려진 오류를 제한 예산으로 어떻게 고칠 것인가?”로 이동했다.

### 최종 Research Question

> 불완전한 인과그래프에서 제한된 수정 예산으로 의사결정 손실을 최소화하려면, 어떤 구조적 오류를 어떤 순서로, 어디까지 수정해야 하는가?

본 프로젝트에서 평가한 M1–M4 및 T1–T6 repair는 참조 DAG 또는 task-zone 정보를 이용하는 **oracle-assisted** 절차다. 참 구조를 모르는 배포 환경에서 오류를 처음 발견하는 문제를 완전히 해결하지 않았다.

## 3. 공통 수학적 틀과 용어

그래프 (G)에서 조작 변수 (X)를 후보 행동 (a)로 설정하고 목표변수 (Y)의 손실 (L(a))를 평가한다. 선택 정책의 regret은

\[
R(G)=L(a_{\mathrm{selected}}\mid G)-\min_{a\in\mathcal A}L(a)
\]

로 정의한다. C/S4의 analytic SCM regret과 D/S5의 bias-corrected standardized tracking loss는 다른 estimand와 척도이므로 서로 합산하거나 같은 표본으로 취급하지 않는다. 편집 예산 (B)는 허용 가능한 원자 그래프 수정 상한이며 실제 편집 수 (C\leq B)와 다르다. 비용 효율성에서 사용하는 λ는 편집 1회에 대한 가상 손실 가중치다. S1/S3/S4의 γ는 조작 강도 (k)에 대한 목적함수 penalty이며 λ와 다르다.

한 번의 오류 수정 편익은 (V(e\mid G)=R(G)-R(G\oplus e))로 표현할 수 있다. 이를 구조 지표 gain과 비교하는 것은 순위의 설명력 분석이며, 오류 유형 간 평균 차이를 인과효과로 해석하지 않는다.

## 4. 연구별 구성과 근거

### Research 0 — 구조 정확도와 의사결정 성능의 불일치

초기 TEP 구조 탐색 및 합성 SCM 단계에서 전역 그래프 일치도와 downstream 의사결정 결과가 서로 다른 평가 대상임을 확인했다. TEP 참고 그래프와 관측자료의 한계 때문에 이 단계의 결과는 제조설비에서의 인과효과 검증이 아니다. 초기 탐색, source 회수 및 환경 적격성 이력은 [`RESEARCH_EVOLUTION.md`](RESEARCH_EVOLUTION.md), [`RESEARCH_JOURNEY_AND_TEAM_HANDOFF.md`](RESEARCH_JOURNEY_AND_TEAM_HANDOFF.md), `docs/research_design/`에서 확인한다.

### Research 1 — WHERE: 어느 영역의 오류를 고칠까?

**Research C.** 64 Development SCM으로 정책을 구성하고 200 independent synthetic SCM Held-out에서 frozen primary를 평가했다. B=2에서 S0 mean regret 0.09343898, Full Greedy 0.01860262, primary S0−Full Greedy +0.07483636 (95% paired-t CI [0.05089822, 0.09877450]); better/worse/tie 45/1/154. M4 secondary mean regret 0.00398775, mean edit cost 0.695이며 Full Greedy보다 적은 수정을 사용했다. M4는 Development-selected secondary라 사후 선택의 영향을 받는다.

M1은 task-zone 밖 FN, M2는 task-zone 밖 FP, M3는 task-zone 밖 REV/UNRES, M4는 task-zone 내 오류 구성요소를 대상으로 한다. 이 정의는 참조 구조를 필요로 한다. 전체 구조를 더 정확하게 만드는 것과 실제 결정 개선은 항상 일치하지 않았으며 off-task 오류가 task edit를 방해하거나 기존 경로를 손상한 반례가 관찰됐다.

**S1/S2.** 사후 보강은 objective와 task-zone 구조 지표의 연관 및 nested predictive feature 비교를 다뤘다. Held-out gamma=.2, B=2에서 S0/Full Greedy/M4/M2+M4 평균 regret은 .117959/.092235/.087253/.090312. gamma=.5에서는 Full Greedy 평균이 M4보다 낮았고 gamma=1에서는 비교 정책들이 모두 (k=0)을 선택했다. S2 nested feature model B/E/F의 Held-out MAE는 .06966/.06153/.03768이었다. 이는 task 관련 feature의 연관성을 보여주는 post-hoc 결과이며 repair 정책의 인과효과와 동일하지 않다.

### Research 2 — WHAT & WHY: task 내부에서 무엇을 먼저 고칠까?

**S3.** T1–T6 지표의 Greedy/lookahead 분석은 구현 정정 및 재분석 이후에도 exploratory historical evidence다. 정정 전 수치는 superseded로 보존한다. 여러 지표 조합의 선택은 후보 부족, metric redundancy, tie-break 및 cohort에 따라 달랐다.

**S4 재구축.** 기존 PC에서 새로 구축한 Development 80과 독립 replication 160은 서로 분리한다. 다른 PC의 과거 Unified S4/S4-3 실행은 단위 자료가 확보되지 않아 `REPORTED_COMPLETED_NOT_INDEPENDENTLY_VERIFIABLE`로 남는다. 현재 확인된 replication은 Q-common-admitted strict-indirect 모집단이며 C unconditional population과 같지 않다.

Replication의 frozen primary는 B=1, gamma=0에서 T5-guided M4 − M4 = −0.008664, 95% paired SCM interval [−0.020398, 0], better/worse/tie 4/1/155였다. interval은 0을 포함하고 목표 half-width .010을 약간 넘었다. T5 superiority와 Full T 대비 noninferiority 모두 입증되지 않았다. S4 unit records에서 재집계한 B=2 M4 mean regret은 Development .009218 (0.888 edits), replication .020615 (0.863 edits); replication Full Greedy .040878 (1.600 edits). 이는 별도 cohort 내부의 descriptive analytic results다.

직접 outside-task 편집 진단에서 747개 합법 수정 중 77개 outside-task FN 편집은 해당 관측 단위들에서 regret/action 변화 0을 보였다. 이 77은 독립 SCM 수가 아니며 편집하지 않은 오류의 가치가 0임을 뜻하지 않는다. 이번 통합에서 미실행 상태인 S4 gamma sensitivity, matched corruption, formal interactions는 완료로 표시하지 않는다.

### Research 3 — GENERALIZATION: 외부 반합성 환경에서도 관찰되는가?

**Historical Research D**는 한 DRF 기반 Station1 semisynthetic DGP에서 fixed training frame과 200 G0 corruption draws를 평가했다. B=2에서 S0 평균 loss는 .823587, Full Greedy는 .789362, M4는 .790592였다. 따라서 사전 primary contrast는 **S0−Full Greedy = +.03422490**이며, two-source 95% interval은 [.00617347, .06535080]이다. 이 구간은 0을 포함하지 않지만 사전 action-MC 및 two-source precision targets는 충족하지 못했다. 이 수치를 S0−M4로 귀속하지 않는다. 표시된 평균에서 S0−M4는 약 +.032995다. 원시 D unit artifacts는 이번 최종 재감사에서 이용할 수 없었다.

**S5**는 Research D의 정확한 재현이 아니라 새로 조건을 고정해 만든 conditional external semisynthetic reconstruction이다. 한 DRF DGP, 512행 training frame, 200 G0, 22,000 recommendations, action당 4,999 response rows(총 24,995; 별도 smoke 1개)다. B=2 S0−M4 = +0.00685175; G0-only CI [0.00486307, 0.00902371], Action-MC-only CI [−0.00889635, 0.02319934], two-source CI [−0.00926095, 0.02273504]. graph-free association mean loss .867868은 M4 .868384보다 낮았고 edge edit 비용은 0으로 셌다. 이는 total modeling cost 0이 아니다. S5의 200개는 독립 SCM이 아니라 동일 DGP 아래의 corruption draws다.

### Research 4 — HOW MUCH: 언제까지 수정하는가?

기존 Research E C 확장은 64 Development/200 Held-out의 budget curves를 B=0–7/0–9까지 분석했다. Held-out M4 regret은 B0 .093439, B1 .029327, B2 .003988, B3 .001435, B4 .001435, B5–9 .001299; 실제 평균 편집 수는 각각 0, .515, .695, .760, .780, .780이다. 따라서 B3→4의 plateau 뒤 B5에서 추가 개선이 있었으며 B3을 일반 포화점이라 부를 수 없다. Adaptive/M2+M4와 cost-weighted results는 [`RESEARCH_E_FINAL_AUDIT.md`](research/final_integration/RESEARCH_E_FINAL_AUDIT.md) 및 `research/budget_adaptive_repair/outputs/`에 보존돼 있다.

이번 extension은 저장된 S4 Development 80, replication 160 및 S5 200 G0의 16,560 policy-budget unit rows를 B=0–4 범위에서 재집계했다. 예컨대 S4 Development M4 regret은 B2 .009218에서 B3 .015830으로 올라갔다가 B4 .003325로 낮아졌다. S5 M4/T5는 B1–4 평균이 동일했고 B2 이후 mean edit count도 .295에 머물렀다. 이는 저장된 범위의 plateau이지 최적 중단 규칙은 아니다. S4/S5 B5–9는 sealed unit recommendation/evaluator 결과가 없어 미실행이다.

Pareto frontier와 (J_\lambda=\bar L+\lambda\bar C) lower envelope는 관측 표본 내 기술적 최적점이다. λ는 가상 edit penalty이며 실제 금액·인력시간이 아니다. S5 graph-free는 counted edit가 0인 baseline으로 frontier 해석에 포함한다. 비용·성능 관계로 보편적인 예산 B를 정할 수 없다.

## 5. 핵심 검증 결과표

| 근거 | 분석 단위와 조건 | 핵심 추정치 | 불확실성/증거 지위 |
|---|---|---|---|
| C primary | 독립 Held-out SCM 200, B2 | S0−Full Greedy +0.07483636 | paired-t 95% CI [0.05089822, 0.09877450], frozen-contract confirmatory |
| C M4 secondary | Held-out SCM 200, B2 | mean regret .00398775, cost .695 | Development-selected secondary |
| S4 replication primary | SCM 160, B1, gamma0 | T5−M4 −.008664 | paired 95% CI [−.020398, 0], 4/1/155; superiority 미확립 |
| S5 external primary | G0 200, B2 | S0−M4 +.00685175 | G0-only CI excludes 0; Action-MC/two-source CI include 0 |
| E C extension | C Held-out, M4 B0–9 | .093439 → .001299 with nonmonotonic plateau | post-hoc |
| E S4/S5 extension | 80/160 SCM and 200 conditional G0; B0–4 | 저장 unit rows 재집계 | paired bootstrap is cohort-specific; S5 G0-only fixed evaluator table |
| S5 baseline | G0 200, B2 | graph-free .867868; M4 .868384 | conditional mean, not total-cost comparison |

시각자료와 출력: [`FINAL_RESULTS_TABLES.md`](research/final_integration/FINAL_RESULTS_TABLES.md), `research/budget_adaptive_repair/figures/E_extension_*.svg`, 기존 C E figure files, S4/S5 public output directories.

## 6. 학술적 기여 및 경영학적 의미

현재 근거가 뒷받침하는 기여는 (1) 구조 정확도와 downstream decision regret을 분리해 평가하는 연구문제, (2) 참조 구조가 알려진 제한 예산 repair에서 task-zone prioritization을 비교한 결과, (3) repair value가 경로·방향·대체 경로·DAG 제약과 목적함수에 따라 달라지는 post-hoc 메커니즘 증거, (4) 예산 및 edit count와 decision loss의 비단조 trade-off를 cohort별로 기록한 결과, (5) 외부 반합성 조건에서 긍정 대비와 uncertainty 및 graph-free baseline을 동시에 제시한 것이다.

경영학적으로는 전문가가 검토할 그래프 오류를 우선순위화하고 검증 자원을 배분하는 문제를 정식화한다. 다만 edit count는 인건비, 검증 시간, 오류 위험, 배포 비용을 측정하지 않았다. 따라서 실제 비용 절감, 생산성 향상 또는 제조 안전 개선이 입증된 것은 아니다.

## 7. 반례와 해석 한계

- M4가 모든 budget, objective 또는 cohort에서 우월하지 않다. C 예산확장에는 비단조성이 있다.
- T5의 replication 점 추정은 유리하지만 불확실하며 정밀도 목표를 미달했다. S5에서 T5와 M4의 선택은 관측상 동일했다.
- Graph-free association은 S5에서 구조 수리 정책과 경쟁했다.
- 일부 off-task 오류는 DAG feasibility를 막거나 기존 task path를 손상할 수 있다.
- 완전한 참 그래프 복원이 최적 행동·정확한 효과크기·0 regret을 보장하지 않는다.
- C/S4의 synthetic SCM 및 S5의 single-DGP G0 draws는 실제 제조 모집단 표본이 아니다.
- 추천 정책은 oracle-assisted structural error knowledge를 전제로 한다.
- 표본 내 λ 최적화는 독립적인 정책 선정/평가가 아니다. 다중 pointwise interval은 동시 구간이 아니다.
- Research D와 S5의 raw artifacts/조건은 같지 않다. S5는 exact D reproduction이 아니다.
- 다른 PC에서 보고된 Unified S4 및 과거 S4-3 자료는 독립 검증 불가한 history로 남는다.

주장별 자세한 분류와 사용 가능한 문장은 [`FINAL_RESEARCH_EVIDENCE_MATRIX.md`](FINAL_RESEARCH_EVIDENCE_MATRIX.md), [`FINAL_RESEARCH_CLAIMS_AND_LIMITATIONS.md`](FINAL_RESEARCH_CLAIMS_AND_LIMITATIONS.md), [`FINAL_SCIENTIFIC_INTEGRITY_REVIEW.md`](FINAL_SCIENTIFIC_INTEGRITY_REVIEW.md)를 참조한다.

## 8. 재현성 및 핵심 파일

공개 저장소에는 contracts, code, aggregate results, analysis scripts, SVGs, hashes와 run manifests가 있다. Research C 원본 SQLite, S4/S5 raw unit records, training frame, recommendation rows, response vectors 및 fitted native DRF objects는 private local archive 외부에 보존되며 GitHub 공개 자료만으로 완전한 원자료 재실행을 보장하지 않는다. S5 private archive는 same-device copy이고 off-device backup은 완료되지 않았다.

- Research C contract/results: [`RESEARCH_C_EXPERIMENT_CONTRACT_V1.md`](RESEARCH_C_EXPERIMENT_CONTRACT_V1.md), [`RESEARCH_C_HELDOUT_V1_RESULTS.md`](RESEARCH_C_HELDOUT_V1_RESULTS.md)
- Research D/S5: [`S5 synthesis`](research/within_task_repair_prioritization/s4_reconstruction/RESEARCH_D_S5_INTEGRATED_SYNTHESIS.md)
- Research E: [`Research E audit`](research/final_integration/RESEARCH_E_FINAL_AUDIT.md), [`E extension results`](research/budget_adaptive_repair/RESEARCH_E_EXTENSION_RESULTS.md)
- S4: [`S4 closeout`](research/within_task_repair_prioritization/s4_reconstruction/S4_S5_CLOSEOUT.md), [`S4 replication`](research/within_task_repair_prioritization/s4_reconstruction/S4_REPLICATION_PRIMARY_RESULTS.md)
- E extension script/data: [`extend_final_e.py`](research/budget_adaptive_repair/extend_final_e.py), `research/budget_adaptive_repair/outputs/final_extension_v1/`

## 9. 최종보고서 구성안

| 장 | 답할 질문과 핵심 내용 | 근거표/그림 | 연결 논리 |
|---|---|---|---|
| 1. 제조 인과발견의 한계 | 구조 점수와 개입 품질은 왜 다른가? | 초기 TEP 적격성·한계 문서 | 관측 구조 비교만으로 결정 효과를 알 수 없어 합성 통제환경으로 전환 |
| 2. 연구 질문과 프레임 | 제한 예산의 구조 수리 문제를 어떻게 정의하는가? | Decision Regret 수식, 연구 mapping | 전체 정확도에서 task decision quality로 초점 이동 |
| 3. Research 0 → Research 1 | task-zone 수리가 무수정보다 나은가? | C primary 결과표, policy comparison figure | WHERE 질문의 frozen synthetic evidence |
| 4. S1/S2: 목적·구조 정보 | 효과 목표에 따라 구조 지표와 예측이 어떻게 달라지는가? | gamma별 regret 및 nested feature MAE | 과업 정의 의존성 제시 |
| 5. S3/S4: 오류 내부 우선순위 | task 내부 오류 중요도와 T5의 추가 가치는 확인됐는가? | S4 paired CI, metric-selection 결과, edit-value table | WHAT & WHY; 우월성 미확립도 포함 |
| 6. Research 3 | 외부 반합성 환경으로 어떤 범위까지 일반화되는가? | S5 uncertainty 표와 action loss | conditional external evidence, graph-free 기준선 |
| 7. Research 4 | 예산과 편집 비용의 한계편익은 어떠한가? | budget/regret, cost, Pareto, λ figures | HOW MUCH; 비단조성과 서로 다른 척도 |
| 8. 통합 토론 | 어떤 결론은 가능하며 무엇은 미입증인가? | Evidence Matrix | 네 연구의 조건부 결론 및 경영 시사점 |
| 9. 한계와 결론 | 실제 적용 전 어떤 증거가 부족한가? | Integrity Review, Claims & Limitations | reference DAG·실측개입·경제비용 부재를 명확히 함 |

## 10. 최종 발표자료 구성안

스토리라인은 연구 진행 일지 순서가 아니라 **배경의 한계 → 문제 발견 → 연구 질문 → WHERE → WHAT & WHY → GENERALIZATION → HOW MUCH → 결론 및 경영 시사점**으로 구성한다.

| 슬라이드 | 제목 및 메시지 | 발표 근거 | 배치 |
|---|---|---|---|
| 1 | 불완전한 그래프, 어디부터 고칠 것인가? | 연구 제목·RQ | 본편 |
| 2 | 높은 구조 점수만으로 개입 결정의 질을 알 수 없다 | TEP→SCM 연구 전환과 한계 | 본편 |
| 3 | Decision Regret과 제한 편집 예산 | (R(G)), B, 실제 비용 정의 | 본편 |
| 4 | Research 1 — 전체가 아니라 과제 영역을 본다 | C S0 vs Full Greedy B2 평균·CI | 본편 |
| 5 | M1–M4는 서로 다른 오류 영역을 우선한다 | 오류 영역 도식, 대표 반례 | 본편 |
| 6 | 구조 수정의 가치는 오류 위치와 과제에 따라 달라진다 | 원본 ledger 사례 / S1 gamma 결과 | 본편, 사후 분석 표기 |
| 7 | Research 2 — T5의 추가 가치는 아직 불확실하다 | S4 replication −.008664, CI [−.020398,0] | 본편 |
| 8 | Research 3 — 외부 반합성 결과도 조건부다 | S5 primary 3개 구간 | 본편 |
| 9 | Graph-free 기준선도 경쟁한다 | S5 .867868 vs M4 .868384 | 본편 |
| 10 | Research 4 — 더 많이 고치는 것이 항상 낫지는 않다 | C B0–9, S4/S5 B0–4 curves | 본편 |
| 11 | 예산 선택은 손실과 가정한 편집 비용의 trade-off | Pareto, λ lower envelope | 본편, λ 가상값 명시 |
| 12 | 최종 답: 우선순위는 조건부이며 현장 효능은 미입증 | 핵심 주장·한계·의의 | 본편 |
| 부록 A | 정책·metric 정의, 모든 budget tables | 완전 결과표 | 부록 |
| 부록 B | bootstrap 방법·S5 two-source uncertainty | pointwise 구간과 분모 | 부록 |
| 부록 C | S4 미확보 historical evidence, 미실행 분석 | closeout/manifest | 부록 |

### 예상 질의와 방어

- **실제 공장에서 검증했나?** 아니다. synthetic 및 semisynthetic 환경이며 물리적 개입·배포 효과는 검증하지 않았다.
- **왜 참 그래프를 쓰나?** 현재 repair prioritization 실험에서 구조 오류 위치를 정의하는 실험적 기준이다. 현장 오류 발견을 위한 oracle-free 문제는 해결하지 않았다.
- **M4 또는 T5가 최선인가?** 항상 그렇지 않다. T5 replication CI는 0을 포함했고 S5에서 T5/M4 선택은 같았다.
- **왜 B를 하나로 권고하지 않나?** 평균 편익은 비단조이고 비용 선호도는 가상 λ 및 cohort/objective에 따라 바뀐다.
- **Graph-free가 더 나은데 왜 그래프를 쓰나?** S5 한 고정 learner/DGP에서 손실이 유사했고 graph-free mean이 조금 낮았다. 이는 범용 우월성이나 총 개발비 비교가 아니다.
- **통계적으로 유의하지 않으면 동등한가?** 아니다. 정밀도 목표와 비열등성 입증 여부를 별도로 보고한다.
- **S4 다른 PC 보고 수치는 포함했나?** 단위 자료를 검증하지 못해 quantitative evidence로 직접 사용하지 않고 historical reported-only로 분리했다.

## 11. 발표 준비 checklist와 팀 handoff

최종 보고서/발표 작성 시 모든 수치를 `FINAL_RESEARCH_EVIDENCE_MATRIX.md`와 실제 결과 파일에서 다시 인용하고, C regret와 S5 tracking loss를 같은 축에 두지 않는다. 반례, pointwise 구간, sample unit, reference DAG 정보 가정을 발표 본편에서 숨기지 않는다. 새 실험·F 확장·PPTX/PDF 제작은 이번 closeout 범위가 아니다.

기존 기록에서 확인되는 역할만 사용한다: 오성민은 기존 연구 설계·실험·통합 및 Research D/S4/S5 실행 기록을 담당했고, 정창민은 Research C M1–M4 post-hoc mechanism 분석 및 PR #40을 수행했다. 황주희의 기여는 기존 인수인계 기록을 보존하되 확인되지 않은 과거 실험 역할을 추가 귀속하지 않는다. 남은 업무는 자료를 바탕으로 최종 보고서 문장 검토, 발표 디자인/연습, 질의응답 분담 및 동일 수치의 최종 대조다.

## 12. S6 저장 결과 재분석과 S7 외부 검증 상태

S6는 기존 S4 Development 80 및 independent replication 160의 저장 후보별 결과를 다시 집계했다. Replication에서 single-edit 평균 regret 감소량은 FN .08915, FP −.03782, REV .11401, UNRES .04956이었다. 이 값은 후보가 존재한 SCM들에 조건부이고 오류 유형의 인과효과가 아니다. v6에서 Type-ranked M4−Frozen M4의 B1 차이는 −.002204 (95% paired SCM bootstrap [−.009283, .003545], better/worse/tie 2/1/157; Holm-adjusted paired-t p=1.0)로 불확실했다. T5−Frozen M4는 −.008664 (pointwise 95% common-index SCM bootstrap [−.020398, 0], better/worse/tie 4/1/155; Holm-adjusted paired-t p=1.0)였다. T5의 관측 평균은 이 replication 정책행렬에서 가장 낮았지만 우월성·동등성·비열등성은 확립되지 않았다. 후보는 SCM 안에 중첩되어 있고 S6는 post-hoc evidence다.

S7은 Station2/Station3 task strata에서 하나의 98-node, 485-edge full-line causalAssembly DRF DGP를 공유하도록 설계했다. Lock은 G0 400개와 recommendation 24,000건을 예정했으나 마지막 신뢰 가능한 관측에서도 persisted G0와 recommendation은 각각 0이었다. Recommendation seal이 없으므로 evaluator는 실행되지 않았고 안전한 completed-unit checkpoint도 없어 재개할 수 없다. 마지막 supervisor report 부재로 실제 종료 시각·종료 원인·cap 적용 및 최종 peak RSS는 검증되지 않았다. 별도 task-zone feasibility는 machine-readable JSON에서 0.7613초, closeout 서술에서 1.474초로 기록되어 측정값이 불일치한다. 실행 측정 범위 차이를 증빙으로 해소하지 못했으므로 어느 값을 단일 확정 runtime으로 선택하지 않고 양쪽을 함께 기록한다. 추가 정적 검토에서는 `s7_external_runner.py`가 canonical unordered pair key를 learner fitting에 전달하는 방향 손실 결함도 확인했다. 실제 recommendation이 저장되지 않았으므로 성능 결과에 대한 영향은 발생하지 않았으며 frozen runner는 수정하지 않았다. 최적화 feasibility는 구현 점검일 뿐 S7 외부 성능 근거가 아니다.

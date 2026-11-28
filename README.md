# DAT 제조공정 인과그래프 수리 연구 — Research 0–4

> **현재 최종 상태 (2026-11-28):** 연구 문서는 PR #51에서 최종 통합 검토 중입니다. S6 저장 결과 사후 재집계가 완료됐고, S7 full-line 작업은 recommendation 0/24,000으로 외부 성능 결과가 없습니다. S7 종료 telemetry와 task-zone 시간 기록에는 미해결 한계가 있습니다. main 기준 최종 통합 여부는 PR #51 병합 뒤 갱신합니다. 이 저장소는 실제 제조설비 개입 효능이나 경제성을 입증하지 않습니다.

## 최종보고서 및 발표자료 작성 가이드

현재 프로젝트의 공식 명명 체계는 **Research 0–4**입니다. [연구 전체 index](research/README.md)에서 숫자 순서대로 탐색하고, 이전 연구 ID와 원본 근거 경로는 [naming map](docs/RESEARCH_NAMING_MAP.md)을 확인하세요. 원본 계약·결과 파일의 legacy ID는 재현성과 provenance를 위해 유지합니다.

권장 순서:

1. [팀 가이드](FINAL_RESEARCH_TEAM_GUIDE.md): 연구 동기, 개념, 연구 흐름을 빠르게 파악합니다.
2. [최종 연구 framework](FINAL_RESEARCH_FRAMEWORK.md): Study 구성, 수식, 결과, 보고서 목차와 발표 스토리라인을 확인합니다.
3. [Evidence Matrix](FINAL_RESEARCH_EVIDENCE_MATRIX.md): 각 주장에 연결된 단위, 추정량, 불확실성 및 근거 파일을 인용합니다.
4. [최종 연구 보고서 참고본](research/final_integration/FINAL_RESEARCH_REPORT.md)과 [결과표](research/final_integration/FINAL_RESULTS_TABLES.md)를 사용합니다.
5. [발표 증거 가이드](research/final_integration/FINAL_PRESENTATION_EVIDENCE_GUIDE.md), [주장 및 한계](FINAL_RESEARCH_CLAIMS_AND_LIMITATIONS.md), [무결성 검토](FINAL_SCIENTIFIC_INTEGRITY_REVIEW.md)로 슬라이드와 결론을 교차 점검합니다.
6. 저장소 상태 및 연구 브랜치 복구는 [Repository final closeout](REPOSITORY_FINAL_CLOSEOUT.md), [archive index](archive/ARCHIVE_INDEX.md), [pre-cleanup inventory](archive/REPOSITORY_PRE_CLEANUP_INVENTORY.json), [branch decisions](archive/BRANCH_CLEANUP_DECISIONS.csv)을 확인합니다.

위 자료는 보고서와 발표자료 제작을 위한 근거 문서이며, 확정되지 않은 정책 우월성·현장 효능·실제 경제효과를 주장하지 않습니다. S6/S7의 최종 상태는 아래 요약과 linked closeout에서 확인하십시오.

## 문제와 최종 연구 질문

이 프로젝트는 불완전한 인과그래프를 제한된 수정 예산으로 수리할 때, 어떤 구조 오류를 우선 고쳐야 downstream 의사결정 손실을 줄일 수 있는지 연구한다. 핵심은 그래프 정확도를 높이는 일과 실제 결정 품질을 높이는 일을 구분하는 것이다.

## 핵심 발견

1. 동결된 합성 계약의 독립 Held-out 200 SCM에서 B=2 Full Greedy는 S0보다 평균 Regret이 0.07483636 낮았다(95% paired-t CI [0.05089822, 0.09877450]).
2. 원본 Ledger 기반 사후 분석은 경로 가용성과 효과 방향이 일부 결정 차이를 설명함을 보였으나, off-task 수정도 경로를 만들거나 DAG 제약을 해소할 수 있었고 구조 수정 뒤 성능이 악화된 반례도 있었다.
3. Research D의 단일 외부 반합성 DRF 생성환경에서는 조건부 양의 대비가 관찰됐으나 graph-free baseline이 Full Greedy와 같은 손실이었고 정밀도 목표는 미달했다. Research E의 사후 확장에서는 예산 편익이 비단조이고 정책 선택이 비용 선호도와 목표값에 따라 달라졌다.

## 세 증거 층위

- **Research C:** 사전 동결된 통제 합성 SCM 실험. Held-out 표본 단위는 독립 synthetic SCM 200개다. [계약](RESEARCH_C_EXPERIMENT_CONTRACT_V1.md) · [Held-out 결과](RESEARCH_C_HELDOUT_V1_RESULTS.md)
- **메커니즘 분석:** Research C 저장 Ledger를 이번 통합에서 read-only로 재검증한 사후 탐색 분석. 정창민의 PR #40 기여 및 커밋 이력을 보존한다. 재생성본의 SCM별 전체 결과는 원본과 완전 대조할 수 없었다.
- **Research D:** 공개 반합성 자료에 재적합한 단일 DRF DGP, 고정 학습 프레임, 200 graph-corruption draws에 조건부인 평가. 실측 개입/독립 외부 SCM 검증이 아니다.
- **Research E:** 같은 C cohorts의 예산 B 확장, edit-count Pareto/lambda 분석, 제한적 Adaptive M4 및 target sensitivity. 이미 본 C 결과의 post-hoc 확장이고 새 SCM cohort가 아니다. [최종 감사](research/final_integration/RESEARCH_E_FINAL_AUDIT.md) · [E9 Pareto](research/final_integration/research_e_audit/figures/E9_expanded_pareto.svg) · [E10 λ](research/final_integration/research_e_audit/figures/E10_lambda_lower_envelope.svg)
- **S6:** 저장된 S4 Development 80/replication 160 candidate records를 이용해 B=1 정책행렬 v6를 사후 재집계했다. Replication의 T5−Frozen M4는 −.008664 (common-index SCM bootstrap 95% pointwise CI [−.020398, 0], better/worse/tie 4/1/155; Holm-adjusted paired-t p=1.0)였고 우월성은 확립되지 않았다. Type-ranked M4−Frozen M4는 −.002204 (CI [−.009283, .003545], 2/1/157; Holm p=1.0)였다. [S6 closeout](research/supplementary_validation/s6/S6_B1_POLICY_MATRIX_CLOSEOUT.md)
- **S7:** 98-node/485-edge full-line recommendation run에서 저장 완료 0/400 G0, 0/24,000 recommendations였고 evaluator는 시작하지 않았다. 마지막 supervisor report가 없어 종료 원인/cap 적용 여부는 확인할 수 없다. 별도 계산 최적화 feasibility는 통과했지만 JSON과 closeout에 기재된 수행시간(.761초와 1.474초)이 달라 해소되지 않았다. 전체 S7 평가는 미완료다. [S7 closeout](research/supplementary_validation/s7/S7_COMPUTATIONAL_CLOSEOUT.md)

## 결과 요약

| 분석 | 단위·대비 | 결과 | 제한 |
|---|---|---|---|
| Research C Held-out | 200 independent synthetic SCMs, B=2 S0−Full Greedy Regret | +0.07483636; 95% CI [0.05089822, 0.09877450] | 합성 계약 내 결과 |
| Research C M4 | B=2 평균 edit 수 | M4 .695; Full Greedy 1.435; 동일 행동 193/200 | Development-selected Secondary; edit count는 현장 비용이 아님 |
| Research D | 고정 DRF DGP·학습 프레임의 200 G0, B=2 S0−FG loss | +0.03422490; two-source CI [0.00617347, 0.06535080] | 단일 반합성 DGP; MC 정밀도 목표 미달 |
| Research D M4 / baseline | B=2 | M4−FG loss +0.00122956; 비용 .335 vs 1.160; graph-free loss=FG | M4의 trade-off와 baseline 동률을 함께 해석 |
| Research E | C Held-out B=5–9 | M4 regret .00129902; Adaptive/M2+M4/FG .00082758 | Post-hoc; budget effect nonmonotone; no new SCMs |
| Research F-Lite | Reused C Held-out, B=4 query policies | Decision-weighted .016281 regret; Random .081223; Fit .003770; Suspicion .006061 | Post-hoc on known SCMs; combined heuristic loses to simpler baselines |
| Research E Adaptive M4 | C Held-out B=3 | 1/200 better, 0 worse, 199 tie; +.020 mean edits vs M4 | one-blocker exploratory heuristic; no general superiority |

## 주장 범위와 한계

Research C와 D는 모두 reference DAG를 활용한 oracle-assisted 구조 수리다. 현장처럼 참 구조를 모르는 상황의 오류 발견을 해결하지 않는다. D의 200개는 독립 SCM이 아니라 하나의 DGP에서 뽑은 graph-corruption draw다. 어느 실험도 실제 공장 개입, 안전성, 실제 전문가 시간·금전 비용, 배포 가능성을 입증하지 않는다. M4의 보편적 우월성 및 graph-based 방법의 보편적 우월성은 주장하지 않는다. Research E와 F-Lite는 기존 입력을 재사용한 post-hoc 확장이다. F-Lite에서 decision-weighted query policy는 Held-out에서 Random보다 낮은 regret을 보였지만 fit-based 및 suspicion-only보다 높았고 impact-only와 거의 같았다. 따라서 결합 heuristic의 추가 이점은 확인되지 않았다. 기존 targeted causal elicitation 연구와의 중복도 커서 새 개념의 최초성을 주장하지 않는다. G/H는 향후 연구 제안으로만 남기며 수행하지 않았다. 수치와 주장별 근거·반례는 [C–D 최종 결과표](research/final_integration/FINAL_RESULTS_TABLES.md), [F-Lite 결과](research/decision_oriented_verification/RESEARCH_F_FINAL_RESULTS.md), [F-Lite 주장–근거 매트릭스](research/decision_oriented_verification/RESEARCH_F_CLAIMS_EVIDENCE_MATRIX.md), [최종 보고서](research/final_integration/FINAL_RESEARCH_REPORT.md)에 있다.

## Research 0–4

공식 연구 탐색은 [숫자순 index](research/README.md)에서 시작합니다. 기존 연구 ID와 세부 연구의 결과 경로는 [naming map](docs/RESEARCH_NAMING_MAP.md), [machine-readable taxonomy](docs/RESEARCH_TAXONOMY.json), [Markdown inventory](docs/MARKDOWN_DOCUMENT_INVENTORY.json)에 정리했습니다. 원본 실험 자료와 frozen 계약은 기존 경로에 유지됩니다.

## 저장소 구조와 재현성

- Research C 계약·결과: 루트 `RESEARCH_C_*.md`, `research/original_objective/`.
- Research C 메커니즘: `research/research_c_mechanism_analysis/`.
- Research D 조사·실행 산출물: `research/external_validation/`.
- Research F-Lite 사후 query-policy prototype, 결과 및 민감도: `research/decision_oriented_verification/`; [한국어 최종 보고서](research/decision_oriented_verification/RESEARCH_F_FINAL_REPORT_KO.md).
- 통합·발표·최종 감사 자료: `research/final_integration/` (E 감사: `RESEARCH_E_FINAL_AUDIT.md`, 집계: `research_e_audit/`).
- 현재 운영 현황: `docs/research_state_current.json`, `docs/current/`.
- Research C 원본 SQLite와 Research D raw response vectors 및 fitted native object는 공개 저장소에 없다. 보존한 hash와 aggregate는 출처·무결성 확인에 쓰이며, 공개 저장소만으로 원자료 전체 재실행을 보장하지 않는다.

새 연구 실행은 승인된 계약과 별도 권한을 요구한다. 이 통합은 새로운 SCM, 평가 표본 또는 물리 실험을 만들지 않는다. 재현·보존 원칙은 [AGENTS.md](AGENTS.md), [CONTRIBUTING.md](CONTRIBUTING.md)를 따른다.

## 팀

- **오성민:** 연구 설계·실험·통합 및 Research D; 최종 보고와 발표 조율.
- **정창민:** Research C M1–M4 메커니즘 분석 및 PR #40.
- **황주희:** 기존 기록에서 확인된 기여만 보존한다. 발표 준비 우선 기록은 있으며, 미확인 과거 연구 기여를 새로 귀속하지 않는다.

세부 인수인계와 발표 준비는 [팀 인수인계](RESEARCH_JOURNEY_AND_TEAM_HANDOFF.md), [기여·발표 체크리스트](research/final_integration/TEAM_CONTRIBUTION_AND_HANDOFF.md)를 참조한다.

F-Lite 최종 저장자료 감사 및 지표 정정은 [감사 보고서](research/decision_oriented_verification/RESEARCH_F_FINAL_AUDIT.md)와 [집계 JSON](research/decision_oriented_verification/outputs/final_audit_aggregate.json)에 기록한다. Random B4 Held-out 평균 반복별 행동 변경률은 4.09%이며 기존 27%는 32회 중 한 번이라도 변경된 SCM 비율이다.

## 과거 연구 및 실측 검증 상태

프로젝트는 TEP 구조 탐색과 인과발견 비교에서 출발했다. TEP 및 CausalMan 환경은 연구 계약에 필요한 reference/intervention 조건을 충족하지 못해 보류되었고, Causal Chambers의 Mk2/Wind Tunnel도 현재 연구 질문에 적합한 실측 정책 비교로 채택되지 않았다. 해당 이력은 제거하지 않고 `docs/research_design/`과 `research/external_validation/`에 보존한다. 이번 최종 연구는 실측 제조 검증이 아니다.

> Historical status snapshot (2026-11-26): the C–D–E–F-Lite closeout was then recorded at PR #46. It is retained as project history; the current status is the S6/S7 and final integration summary above.

## 최종 통합 업데이트 — S4/S5 및 Research E extension

2026-11-28 기준 후속 S4 재구축(Development 80, 별도 replication 160)과 S5 conditional external semisynthetic reconstruction(단일 DRF DGP, 200 G0 draws)이 별도 cohort로 완료되어 있다. 기존 Research E C 예산 확장에 더해 이번 최종 extension은 저장된 S4/S5 B=0–4 unit results 16,560행을 재집계했다. 신규 SCM/G0/관측·개입표본은 만들지 않았다. S4/S5 B=5–9는 저장된 sealed results가 없어 실행하지 않았으며 외삽하지 않는다.

최종 연구의 연구 질문·Study mapping·결과·한계·최종보고서 및 발표 구성은 [FINAL_RESEARCH_FRAMEWORK.md](FINAL_RESEARCH_FRAMEWORK.md)에서 확인한다. [증거 행렬](FINAL_RESEARCH_EVIDENCE_MATRIX.md), [팀 가이드](FINAL_RESEARCH_TEAM_GUIDE.md), [무결성 검토](FINAL_SCIENTIFIC_INTEGRITY_REVIEW.md), [주장과 한계](FINAL_RESEARCH_CLAIMS_AND_LIMITATIONS.md)도 함께 읽는다. Research C의 frozen primary는 유지되고, S4/S5 및 E extension은 각자의 조건과 post-hoc/conditional 증거 수준으로 구분한다. S5의 action-MC 및 two-source interval은 0을 포함하며 graph-free baseline은 M4와 경쟁했다. T5 우월성은 입증되지 않았다.

Research E extension 결과와 집계는 [E extension report](research/budget_adaptive_repair/RESEARCH_E_EXTENSION_RESULTS.md), [marginal benefit](research/budget_adaptive_repair/RESEARCH_E_MARGINAL_BENEFIT_REPORT.md), [cost-weighted analysis](research/budget_adaptive_repair/RESEARCH_E_COST_WEIGHTED_POLICY_REPORT.md), [S5 budget analysis](research/budget_adaptive_repair/RESEARCH_E_EXTERNAL_BUDGET_ANALYSIS.md), `research/budget_adaptive_repair/outputs/final_extension_v1/`에 있다. C regret과 S5 standardized tracking loss는 통합하거나 같은 척도로 비교하지 않는다. Same-device private archive는 외부 장치 백업이 완료되지 않았다.

## Supplementary S1/S2 audit correction

PR #48 보강 감사에서는 S1 Full Greedy를 실제 정책 `M1+M2+M3+M4`로 재식별하고 `CANONICAL_ORACLE`과 분리했다. Original target, gamma=.2, B=2 Held-out에서 S0/Full Greedy/M4/M2+M4 평균 Regret은 .117959/.092235/.087253/.090312이며, Full−S0와 M4−Full의 공유 SCM bootstrap pointwise 95% 구간은 각각 [−.03798,−.01463], [−.01077,−.00038]이다. gamma=.5에서는 Full Greedy가 M4보다 낮고 gamma=1에서는 네 비교 정책 모두 k=0을 선택한다. S2 nested B/E/F 모델의 Held-out MAE는 .06966/.06153/.03768이다. 이 모든 보강은 post-hoc이며 C의 frozen primary를 변경하지 않는다. 자세한 정정, 지표 정의와 한계는 [보강 최종 결과](research/final_supplementary_validation/SUPPLEMENTARY_FINAL_RESULTS.md), [계약 정정 V2](research/final_supplementary_validation/SUPPLEMENTARY_CONTRACT_CORRECTION_V2.md), [S1/S2 보고서](research/final_supplementary_validation/S1_DECISION_OBJECTIVE_ROBUSTNESS.md)에서 확인한다.

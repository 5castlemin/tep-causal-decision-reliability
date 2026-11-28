# 최종 발표 증거 가이드

> 슬라이드의 공식 흐름은 Research 0 → Research 1 (WHERE) → Research 2 (WHAT & WHY) → Research 3 (GENERALIZATION) → Research 4 (HOW MUCH)입니다. 원래 실행 이름은 근거 경로 추적에만 사용합니다. [Research Index](../README.md) · [Naming Map](../../docs/RESEARCH_NAMING_MAP.md).

## 발표 중심축

질문은 “한정된 그래프 수정 예산을 어떤 오류에 배분해야 의사결정 성능을 효율적으로 개선할 수 있는가?”로 둔다. 현장 적용 성과가 아니라, oracle-assisted 구조 수리 정책을 통제된 synthetic/semisynthetic 조건에서 비교한 연구다.

## 권장 흐름과 증거

1. **문제와 동기:** 그래프 정확도만으로는 실제 의사결정 가치를 보장할 수 있다는 문제 설정. 근거: 최종 보고서 §1–3.
2. **방법:** FN/FP/REV/UNRES, task zone, M1–M4, 고정 edit 비용, S0/Full Greedy 비교. 근거: Research C contract 및 최종 보고서 §4.
3. **핵심 실험:** C Held-out B=2, 200 independent SCM; delta +0.07484, CI [0.05090, 0.09877]. 근거: `FINAL_RESULTS_TABLES.md`.
4. **메커니즘:** path absence/flat prediction, 효과 부호, DAG 제약의 사례. 5/6 M4 우세 disagreement는 경로 복원이고 사례 …000139는 기존 경로에서 행동 방향 차이. 근거: 원본 Ledger 감사.
5. **외부 강건성:** 단일 DRF DGP의 200 G0, delta +0.03422, interval [0.00617, 0.06535]; 두 정밀도 목표 미달. 근거: D 재감사.
6. **반례·기준선:** M4의 더 낮은 edit count와 약간 높은 손실, graph-free baseline의 동률, C/D의 조건부 한계.
7. **기여·한계:** 비용 제약 구조 수리라는 의사결정 중심 framing. Oracle-assisted, synthetic/semisynthetic, 외부 실측 부재, 일반화 제한.

## 그림·표 제안

- C의 예산별 Regret 곡선과 paired CI.
- D의 정책별 손실/비용을 서로 다른 축·척도로 제시(절대 loss를 C와 직접 비교하지 않음).
- 대표 사례 3개: 경로 복원, 기존 경로 효과 방향 차이, 구조 수정 후 악화.
- 결과표에는 모집단/조건, 분석 단위, estimand, CI, 반례를 함께 표기.

## 예상 질문

- **실제 공장에서 검증했나?** 아니다. D도 제조공정 기반 공개 반합성 표본에 DRF를 다시 적합한 단일 생성환경이다.
- **200개 D 표본은 독립 공정인가?** 아니다. 고정 DGP/학습 프레임의 200 graph-corruption draw다.
- **M4가 최선인가?** 보편적으로 그렇지 않다. edit 횟수는 줄였지만 D 손실은 FG보다 약간 컸고 C에도 반례가 있다.
- **왜 graph-free를 비교했나?** 무작위화 생성환경에서 직접 연관성 기반 모델이 경쟁 기준이 되며, D에서 FG와 동률이었다.
- **수정 비용은 현장 비용인가?** 아니다. 단위 간선 수정 횟수만 측정했다.
- **메커니즘은 확증됐나?** 아니다. 원본 ledger로 검증한 사후 탐색 설명이다.

각 슬라이드의 주장 강도는 `FINAL_CLAIMS_EVIDENCE_MATRIX.md`를 따른다. 새 분석 결과나 확인되지 않은 팀 기여를 추가하지 않는다.


## Research 4: 사후 예산·비용 확장 슬라이드

그림으로는 [확장 Pareto (E9)](research_e_audit/figures/E9_expanded_pareto.svg) 및 [λ 선택 구간 (E10)](research_e_audit/figures/E10_lambda_lower_envelope.svg)을 사용할 수 있다.

8. **예산 포화와 비단조 편익:** B3→4에서 M4 평균이 그대로였지만 B5에서 다시 낮아짐. 정책 후보 소진·완전 구조 복원·DAG 제약·decision saturation을 분리. 근거: `RESEARCH_E_FINAL_AUDIT.md`, `corrected_saturation_rates.csv`.
9. **비용–성능 선택:** C Held-out expanded frontier 및 λ lower envelope. Adaptive B3와 B5–9 포함, Full Greedy가 mean frontier에 없다는 사실과 no-edit tie 보존. λ는 가상 edit penalty. 근거: `expanded_pareto_frontiers.csv`, `expanded_lambda_lower_envelope.csv`.
10. **Adaptive M4의 희소성:** B3에서 1/200만 개선, 199 동률, 평균 비용은 M4보다 .020 높음. 근거: `e3_adaptive_paired_comparisons.csv`, `adaptive_blocker_counts.csv`.
11. **Reference learner 및 target 의존성:** reference graph learner를 최적 oracle로 부르지 않는다. δ=0은 특수한 평균 편차 목표. 근거: `reference_learner_summary.csv`, `target_sensitivity_unit_results.csv`(로컬 전용; 공개 요약만 사용).

E는 이미 Held-out을 본 뒤의 탐색 분석이므로 C Primary 대체나 신규 확증 결과로 발표하지 않는다. Research D의 원시 response는 이번 closeout에서 다시 열 수 없었고 기존 audit summary와 공개 집계까지만 인용한다.

## Research F-Lite 최종 감사 슬라이드

12. **질의 정책 비교:** Held-out B4 Decision-weighted regret .016281은 Random .081223보다 낮지만 Fit-based .003770 및 Suspicion-only .006061보다 높고 Impact-only .017270에 가깝다. 분석 단위는 재사용된 200 SCM이며 post-hoc이다.
13. **Random action 변화 정의:** 반복별 평균 변경률 4.09%와 SCM 중 최소 한 번 변경 비율 27.0%를 별도 막대/표기로 제시한다. 기존 27%를 반복별 평균으로 발표하지 않는다.
14. **자원과 정보 경계:** B4에서 질의는 모두 4회지만 평균 edit는 Fit 1.905, Suspicion 1.885, Impact .425, 제안 .450, Random .305다. Query 비용과 graph edit 비용을 구분하고 실제 시간·금액 비용이라고 하지 않는다. 인터페이스에서 정책은 reference-blind지만 simulated expert는 reference를 본다.

근거: `research/decision_oriented_verification/RESEARCH_F_FINAL_AUDIT.md`, `outputs/final_audit_aggregate.json`, `outputs/random_action_change_audit.csv`. C/D/E/F-Lite의 서로 다른 loss와 분석 단위를 하나의 축으로 직접 비교하지 않는다.

15. **보강 S1/S2:** Full Greedy (`M1+M2+M3+M4`)와 Canonical Oracle을 분리하고 gamma=.5 순위 역전 및 gamma=1의 동일 `k=0`을 제시한다. S2 nested MAE는 B_original .06966, E_nested .06153, F_nested .03768이다. 근거: `research/final_supplementary_validation/SUPPLEMENTARY_FINAL_RESULTS.md`, `outputs/s1_corrected_primary_contrasts.csv`, `outputs/s2_nested_model_validation.csv`. 반드시 post-hoc, saved C rows, pointwise uncertainty라고 표시한다.

## Final framework and slide story update

Use [`FINAL_RESEARCH_FRAMEWORK.md`](../../FINAL_RESEARCH_FRAMEWORK.md) as the current narrative blueprint. It includes the final-report chapter plan, slide-by-slide messages, evidence files, counterexamples and defense Q&A. The main story is problem limitation → decision-focused question → WHERE → WHAT & WHY → conditional GENERALIZATION → HOW MUCH → bounded conclusion; do not list runs chronologically. S4 T5 evidence is inconclusive, S5 uncertainty includes zero in the two-source interval, and the S5 graph-free baseline is competitive.

## Research 2.4 / 3.3 closeout use

Keep Research 2.4 (legacy S6) in the Research 2 appendix or a compact main-text qualification slide: the saved-data B=1 replication matrix gives T5−Frozen M4 `−.008664`, common-index pointwise SCM-bootstrap 95% CI `[−.020398,0]`, better/worse/tie `4/1/155`; Type-ranked M4−Frozen M4 is `−.002204`, CI `[−.009283,.003545]`, `2/1/157`. Both are retrospective on reused S4 data and neither establishes superiority. Keep the outcome-privileged ex-post oracle separate from implementable policies.

State S7 as a computationally limited, incomplete external evaluation: 0/400 persisted G0, 0/24,000 recommendations, no seal/evaluator, and unverifiable termination telemetry. The separate task-zone feasibility has inconsistent reported elapsed time (`.7613 s` JSON vs `1.474 s` prose). Static review confirmed the runner passes unordered canonical pair keys into a learner expecting directed edges; no recommendation outcome exists, and the frozen code was not changed. Cite the [S7 closeout](../supplementary_validation/s7/S7_COMPUTATIONAL_CLOSEOUT.md); do not show S7 as external validation evidence.

# 최종 검증 결과표

> 표의 legacy ID는 결과 원본을 식별하기 위한 것입니다. 최종 연구 흐름에서의 canonical 위치는 [Research Naming Map](../../docs/RESEARCH_NAMING_MAP.md) 및 [Research Index](../README.md)를 참조하십시오.

## Research C — frozen synthetic SCM study

| 결과 | Development V1 | Held-out V1 |
|---|---:|---:|
| 독립 synthetic SCM 수 | 64 | 200 |
| B=2 S0 평균 Regret | 0.10085173 | 0.09343898 |
| B=2 Full Greedy 평균 Regret | 0.02564084 | 0.01860262 |
| B=2 M4 평균 Regret (Development-selected Secondary) | 0.00292777 | 0.00398775 |
| Primary `Regret(S0)−Regret(Full Greedy)` | +0.07521089 | +0.07483636 |
| Primary paired-t 95% CI | [0.03223, 0.11819] | [0.05089822, 0.09877450] |
| 개선 / 악화 / 동률 | 14 / 1 / 49 | 45 / 1 / 154 |
| Full Greedy 평균 atomic edit count (B=2) | 1.453 | 1.435 |
| M4 평균 atomic edit count (B=2) | 0.656 | 0.695 |
| M4와 Full Greedy 동일 추천 행동 | 61/64 | 193/200 |

Research C Primary는 계약대로 B=2의 Full Greedy 대 S0다. M4는 Development를 본 뒤 지정한 Secondary이며 Held-out M4−Full Greedy 결과를 확증적 우월성으로 해석하지 않는다. 정책×예산 행은 반복 측정이지 독립 표본이 아니다. Development의 원본 Ledger `selected_k` 대조에서 M4와 실제 Full Greedy (`M1+M2+M3+M4`)는 61/64 SCM에서 같은 행동을 추천했고 3/64에서 달랐다. 이전 46/64 표기는 정정한다.

## Research C mechanism analysis — post-hoc

| 관찰 | 원본 Ledger 결과 | 해석 범위 |
|---|---:|---|
| Held-out S0에서 positive regret | 55/200 | 사후 메커니즘 진단 |
| 그중 learner X→Y path가 없는 경우 | 49/55 | 현재 선형 learner/task contract에서 path absence와 flat prediction이 함께 나타남 |
| 그중 path가 있으나 추천 부호가 맞지 않은 경우 | 6/55 | 이 사례 집합에서 확인 |
| Held-out task-zone error가 있는 G0 | 103/200 | Rule A 및 reference-relative task definition |
| Full Greedy 평균 task/off-task 수정 수 (B=2) | 0.555 / 0.880 per SCM | 노동시간·금전 비용 아님 |
| M4 평균 task 수정 수 (B=2) | 0.695 per SCM | M4는 task-zone metric subset |
| M4가 Full Greedy보다 낮은 regret을 보인 action-disagreement | 6/7 | 5 path restoration, 1 existing path with action-sign difference |
| Full Greedy 우세 반례 | `…000076` | off-task FP가 남아 있으면 task 방향 수정이 DAG 제약에서 거부됨 |

경로/flat 관계는 22,440개의 저장 정책×예산 관측에서 discordance 0이었다. 이는 두 승인 cohort와 현재 learner에 대한 경험적 결과다. 22,440개의 독립 SCM 또는 모든 DAG에 대한 수학적 법칙이 아니다.

## Research D — conditional external semisynthetic robustness

| 결과 (B=2 unless stated) | 추정값 | 95% interval / 추가 정보 |
|---|---:|---|
| S0 mean bias-corrected tracking loss | 0.823587 | 고정 DGP·학습 frame |
| Full Greedy mean loss | 0.789362 | 고정 DGP·학습 frame |
| Primary `L(S0)−L(Full Greedy)` | +0.03422490 | G0 `[0.02664478,0.04180501]`; MC `[0.00650999,0.06284998]`; two-source `[0.00617347,0.06535080]` |
| M4 mean loss | 0.790592 | M4−Full Greedy `+0.00122956`; two-source `[0.00000000,0.00391596]` |
| Full Greedy / M4 mean edit count | 1.160 / 0.335 | M4 edit-count reduction 71.1%; 현장 인건비 추정 아님 |
| 동일 행동 (Full Greedy vs M4) | 198/200 | M4 action-disagreement 2건 모두 더 높은 손실 |
| S0 대비 Full Greedy 행동 변화 | 56/200 | 개선 56, 동률 144, 악화 0 |
| Graph-free association baseline | 0.789362 | Full Greedy와 같은 action loss; 인과효과 학습기 아님 |
| task-zone error / no task-zone error G0 | 64 / 136 | 단일 DGP 내 기술적 하위집단 비교 |
| MC-only / two-source 반폭 목표 | 0.02817 / 0.02959 | 목표 0.020 / 0.025 모두 미충족 |

다섯 action의 평가표본 평균은 각각 14.0688, 14.0112, 13.9644, 14.0040, 13.9980이고 고정 target은 15.4600이었다. 이는 2,500-row/action finite sample 요약이다. 모집단 목표 불가능성이나 제조 제어 한계를 입증하지 않는다.

## S6/S7 — supplementary closeout

S6는 기존 S4 저장 candidate artifacts의 B=1 post-hoc 재집계다. SCM이 분석 단위이고 후보행은 SCM 내에 중첩된다.

| S6 replication 정책 | Mean regret (160 SCM) | Paired 차이 대 Frozen M4 | 95% pointwise paired SCM bootstrap | Better / worse / tie | Holm-adjusted paired-t p |
|---|---:|---:|---:|---:|---:|
| Frozen M4 | .038817 | reference | — | — | — |
| Type-ranked M4 (Development-selected) | .036613 | −.002204 | [−.009283,.003545] | 2 / 1 / 157 | 1.0 |
| T5-guided M4 | .030152 | −.008664 | [−.020398,0] | 4 / 1 / 155 | 1.0 |
| Full T1–T6 | .031391 | −.007426 | [−.019693,.002789] | 4 / 1 / 155 | 1.0 |
| Ex-post single-edit oracle | .012907 | −.025910 | [−.044657,−.010495] | 10 / 0 / 150 | .053712 |

S6는 신규 독립 확인 실험이 아니다. Oracle은 realized regret을 이용하는 비실행 가능 진단이다. T5의 평균은 가장 낮았지만 우월성·동등성·비열등성은 확립되지 않았다.

S7에는 98-node/485-edge full-line 그래프와 하나의 shared DRF DGP에서 Station2/Station3 task strata가 있었다. 계획 400 G0·24,000 recommendation 중 persisted 0·0, recommendation seal 없음, evaluator 미실행이다. 종료 telemetry가 없어 cap 준수와 종료 사유를 확인할 수 없다. task-zone feasibility 시간은 JSON `.7613s`, closeout prose `1.474s`로 다르며 정합이 미해결이다. 정적 검토에서 frozen runner가 canonical unordered pair key를 directed-edge learner 입력에 전달하는 방향 손실 경로가 확인됐다. 실제 recommendation이 없어 성능 결과는 없다. 전체 세부사항은 [S6 closeout](../supplementary_validation/s6/S6_B1_POLICY_MATRIX_CLOSEOUT.md) 및 [S7 closeout](../supplementary_validation/s7/S7_COMPUTATIONAL_CLOSEOUT.md)에 있다.

## C와 D 사이의 직접 수치 비교 금지

Research C는 독립 synthetic SCM 단위의 analytic GT regret, Research D는 하나의 DRF DGP·고정 학습 frame 아래 G0 corruption draws를 공유 action-level Monte Carlo tracking loss로 평가했다. 서로 다른 task, 구조, loss, 표본 단위 및 생성 메커니즘이므로 두 Primary의 절대 크기 차이를 특정 모델 요소의 효과로 해석하지 않는다.


## Research E — 사후 예산·비용 확장

### C Held-out의 주요 policy budget curve

| B | Full Greedy regret | M4 regret | M2+M4 regret | Adaptive M4 regret |
|---:|---:|---:|---:|---:|
| 0 | .09343898 | .09343898 | .09343898 | .09343898 |
| 1 | .04605265 | .02932712 | .03870103 | .02932712 |
| 2 | .01860262 | .00398775 | .01267397 | .00398775 |
| 3 | .00816650 | .00143536 | .00463471 | .00096391 |
| 4 | .00096391 | .00143536 | .00096391 | .00096391 |
| 5–9 | .00082758 | .00129902 | .00082758 | .00082758 |

### Held-out B=3 cost correction and sparse Adaptive contrast

| Policy | Mean regret | Mean edit count |
|---|---:|---:|
| M4 | .00143536 | .760 |
| Adaptive M4 | .00096391 | .780 |
| M2+M4 | .00463471 | 1.350 |
| Full Greedy | .00816650 | 1.790 |

Adaptive−M4 paired difference −.000471447; SCM bootstrap 95% interval [−.001414341, 0]; better/worse/tie 1/0/199. The Full Greedy cost is Research C’s 1.790; 1.325 was a Research D value.

### Bmax restoration, reference learner, and target sensitivity

| Quantity | Development (64) | Held-out (200) |
|---|---:|---:|
| M4 fully restored / residual cases | 18 / 46 | 80 / 120 |
| M2+M4 fully restored / residual cases | 27 / 37 | 109 / 91 |
| Reference learner mean regret (median 0 in both) | .00255992 | .00082758 |
| Reference learner selected grid optimum | 63/64 | 198/200 |
| δ=0; M4/B2 recommends k=0 | 64/64 | 200/200 |
| δ=0; true grid optimum interior | 58/64 | 185/200 |

At Bmax, Full Greedy and Canonical Oracle actions agreed with the reference-DAG learner in 264/264 units; M2+M4 also agreed in 264/264 despite residual graph errors, and M4 in 263/264. The reference learner is not a decision oracle.

### C Held-out observed Pareto and lambda envelope

Cross-budget mean-coordinate frontier (ties at no-edit coordinates retained): S0/no-edit at (0, .093439), M3 B1 at (.350, .092477), M4 B1/B2/B3 at (.515, .029327)/(.695, .003988)/(.760, .001435), Adaptive M4 B3 at (.780, .000964), and Adaptive M4 B5–9 at (.810, .000828). Full Greedy is not on the observed frontier. Fixed Bmax frontier is S0 B9, M3 B9, M4 B9, and Adaptive M4 B9. Frontier status is descriptive, not inferential.

For `Jλ=mean regret+λ×mean edit count`, observed lower-envelope switches occur near λ=.0045445, .0235724, .0392675, and .1287068. The winning sequence is Adaptive M4 B5–9, Adaptive M4 B3, M4 B3, M4 B2, then tied zero-edit candidates. λ represents hypothetical edit-count penalty, not money. Exact boundaries and ties: `research_e_audit/expanded_lambda_lower_envelope.csv`. A joint paired unit bootstrap (2,000 resamples, seed 2026112699) gives empirical frontier inclusion frequencies, not probabilities of superiority.

### D boundary

At D B2 only, graph-free association baseline has mean loss .789362 and 0 graph edits, equal loss to Full Greedy. D raw per-G0 artifacts were unavailable in this closeout, so there is no extended D frontier or Adaptive analysis. C regret and D target-tracking loss are not pooled.

## Supplementary S1/S2 — post-hoc objective and metric validation

S1's original target, gamma=.2, B=2 Held-out mean regrets are S0 `.11795863`, Full Greedy (`M1+M2+M3+M4`) `.09223511`, M4 `.08725290`, M2+M4 `.09031225`, and reference-graph learner `.08635285`. The latter uses reference structure and is a diagnostic, not a deployable oracle. Shared-index paired SCM-bootstrap pointwise 95% intervals: Full Greedy−S0 `−.02572 [−.03798,−.01463]`; M4−Full Greedy `−.00498 [−.01077,−.00038]`. `CANONICAL_ORACLE` is a separate diagnostic, not Full Greedy. At gamma=.5 Full Greedy mean regret `.08216346` is below M4 `.08359752`; gamma=1 policies select the same action `k=0` in all saved units. These are post-hoc objective sensitivities, not changes to C's frozen primary.

The S1 `GRAPH_FREE` rows are now named `EMPTY_DAG_LEARNER`: they are predictions from the existing learner supplied an empty graph. They are not Research F's X–Y association learner. The latter's already-saved gamma-zero regret is `.02939` Development and `.03873` Held-out; it was not evaluated on the additional S1 objectives.

S2's corrected nested saved-feature comparison reports Held-out SCM-balanced MAE `.06966` for B_original, `.06153` for E_nested, and `.03768` for F_nested. Paired B−E MAE difference `.00813` (pointwise 95% SCM bootstrap `[.00209,.01390]`); E−F `.02386` `[.01674,.03116]`. This post-hoc refit uses common Development SCM-grouped folds and does not tune on Held-out.

## Research F-Lite final audit corrections

| Audit item | Development | Held-out | Definition |
|---|---:|---:|---|
| Random B4 mean action change across 32 repeats | 5.08% | 4.09% | SCM별 32개 Random recommendation 중 S0와 다른 비율의 평균 |
| Random B4 SCM changed at least once | 28.13% | 27.00% | 기존 `action_change_rate`; 32회 중 한 번 이상 변경 |
| Fit-based B3/B4 same action | 63/64 | 200/200 | Unit-level action comparison |
| Final pending rows, four deterministic query policies at B4 | 2/256 | 4/800 | Stored answers replayed; individually DAG-feasible on final graph: 0 in both cohorts |

The historical graph-free `mean_remaining_errors=9.52` is a raw diagnostic only. Structural residual error is `n/a` for a learner with no repair graph. Shared-index 10,000-resample pointwise intervals and saved-input/hash checks are in [`RESEARCH_F_FINAL_AUDIT.md`](../decision_oriented_verification/RESEARCH_F_FINAL_AUDIT.md). The verified Development M4–Full Greedy action agreement is 61/64 (3/64 differ); this is distinct from the mechanism report's 46 Held-out off-task selections (including three score ties).

## Final S4/S5 and Research E extension addendum

The last E extension re-aggregated saved S4 Development 80 SCM, S4 replication 160 SCM and S5 200 conditional G0 unit results for B=0–4. It added no generated research units. Data: `research/budget_adaptive_repair/outputs/final_extension_v1/budget_policy_aggregate.csv`; uncertainty: `paired_bootstrap_uncertainty.csv`. Research C retains the only inherited B=0–9 curve. S4/S5 B=5–9 is not run. S5 uncertainty and graph-free baseline remain explicit; all loss scales stay separate. For the complete verified table and report/presentation layout, see [`FINAL_RESEARCH_FRAMEWORK.md`](../../FINAL_RESEARCH_FRAMEWORK.md) and [`FINAL_RESEARCH_EVIDENCE_MATRIX.md`](../../FINAL_RESEARCH_EVIDENCE_MATRIX.md).

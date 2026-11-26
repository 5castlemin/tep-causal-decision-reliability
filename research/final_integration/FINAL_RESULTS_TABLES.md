# 최종 검증 결과표

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
| M4와 Full Greedy 동일 추천 행동 | 46/64 | 193/200 |

Research C Primary는 계약대로 B=2의 Full Greedy 대 S0다. M4는 Development를 본 뒤 지정한 Secondary이며 Held-out M4−Full Greedy 결과를 확증적 우월성으로 해석하지 않는다. 정책×예산 행은 반복 측정이지 독립 표본이 아니다.

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

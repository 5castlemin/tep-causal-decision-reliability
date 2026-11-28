# DAT 제조공정 프로젝트 최종 연구 보고서

팀: 닦고조이고기름치자

상태: Research C 실험·감사, 원본 Ledger 메커니즘 재검증, Research D 외부 반합성 평가, Research E 사후 예산·비용 확장 감사 완료. Research D/E 일부 자료 접근 제한을 아래에 구분한다. 본 문서는 새 실험을 보고하지 않는다.

## 1. 연구 배경

제조공정의 인과관계를 이해하려는 초기 연구는 TEP 관측자료에서 여러 Causal Discovery 알고리즘이 추정한 그래프와 참고 구조의 일치도를 살펴보는 데서 출발했다. 하지만 참고 그래프가 완전한 물리적 인과 Ground Truth라는 증거가 제한적이었고, 관측 예측 성능만으로 실제 조작의 효과를 검증할 수 없었다. 공개 TEP 시뮬레이터·기록 데이터 사이의 실행 및 개입 정합성도 입증되지 않았다.

이에 따라 연구 초점은 알고리즘별 F1/SHD 순위에서 구조 오류가 조작 관련 경로에 놓였는지, 그리고 오류를 고치면 의사결정이 달라지는지로 이동했다. Research C는 이 질문을 확인 가능한 합성 SCM 계약으로 제한해 실험했고, Research D는 실제 제조자료를 대체하지 않는 외부 반합성 생성환경에서 조건부 강건성을 점검했다.

## 2. 연구 질문의 발전과 최종 질문

현재 연구 질문은 다음과 같다.

> **한정된 인과그래프 수정 예산을 어떤 구조 불일치에 배분할 때, downstream 의사결정 손실이 어떻게 달라지는가?**

“전체 그래프를 더 정확히 만드는가?”와 “주어진 조작 과제의 추천 행동과 손실이 개선되는가?”를 분리한다. 본 연구는 참조 DAG가 주어진 Oracle-assisted 오류 수리 설정을 다루며, 참 구조를 모르는 현장 자동 오류 발견 문제까지 해결했다고 주장하지 않는다.

## 3. 오류와 정책 비교 방법

각 실험 단위에서 reference DAG, 조작변수 X, 목표변수 Y와 strict indirect-only task를 정하고 초기 그래프 G0에 FN, FP, REV, UNRES 불일치를 만든다. 원자 수정은 누락 간선 추가, 가짜 간선 삭제, 역방향 간선 방향 수정, 미결정 간선 확정이며 각 비용은 1이다. 이 비용은 실제 수정 시간이나 금액이 아니라 edit count다. 구조 수리 예산은 B=0–4다.

Research C의 M1–M4는 다음 구조 오류 지표다.

- **M1:** task zone 밖의 참 인접성 누락(FN).
- **M2:** task zone 밖의 가짜 인접성(FP).
- **M3:** task zone 밖의 방향 반전과 unresolved.
- **M4:** task-zone 오류의 FN/FP/REV/UNRES 구성요소와 각각의 support.

공식 보고 지표와 Greedy 선택 점수는 다르다. Greedy는 선택된 metric subset의 G0 고정 opportunity support로 나눈 잔여 오류율을 같은 가중으로 평균한 `P_S` 감소량을 원자 수정 비용으로 나누어 후보를 매 단계 다시 평가한다. M4 proxy는 G0에서 오류와 support가 양수인 활성 성분의 비율을 같은 가중으로 평균한다. 따라서 task 오류 정의와 실제 수리 우선순위는 구조 점수이지 예상 regret 자체가 아니다. FP Rule A는 FP 양끝 노드가 task-zone node set에 모두 속할 때 task-related로 분류한다. 이 규칙상 off-task FP도 X/Y에 연결되어 경로를 만들거나 DAG 수리 가능성을 바꿀 수 있다.

비교 정책은 무수정 S0, M1–M4의 15개 비공집합 metric subset, Full Greedy(M1+M2+M3+M4), Canonical Oracle로 구성된다. Canonical Oracle은 참 구조에 기반한 고정 순서 구조 진단 기준선이며 regret-optimal 정책이 아니다. 참 DAG와 task zone은 오류 판정·수리 후보에 쓰일 수 있지만, 추천은 공통 관측 학습자료와 수정 graph를 사용한다. GT 행동별 loss와 optimal action은 추천을 잠근 뒤 평가에만 사용한다.

## 4. Research C 설계와 핵심 결과

Research C는 64개의 Development synthetic SCM으로 정책·계약을 개발하고, 200개의 독립 synthetic SCM Held-out cohort로 동결 Primary를 평가했다. 각 SCM 안에서 정책들은 같은 관측자료, task, 후보 행동 및 analytic GT evaluator를 공유한다. Primary는 B=2에서 `Regret(S0)−Regret(Full Greedy)`의 SCM paired 평균이다. 양수는 Full Greedy의 regret이 낮다는 뜻이다.

Held-out 평균 regret은 S0 `0.09343898`, Full Greedy `0.01860262`였고 Primary는 `+0.07483636` (95% paired-t CI `[0.05089822, 0.09877450]`)이었다. 개선/악화/동률은 45/1/154다. 이 결과는 사전 동결된 합성 SCM 계약 안에서 제한된 수리가 무수정보다 평균 regret을 낮출 수 있다는 증거다.

M4 평균 regret `0.00398775`는 Development에서 선택한 Secondary로 유지한다. M4는 B=2 평균 edit count `0.695`, Full Greedy `1.435`였고 행동은 193/200 SCM에서 같았다. 이 비교는 사후/선택 영향을 받을 수 있어 M4의 보편적 우월성 증거가 아니다.

## 5. 메커니즘 분석

정창민의 M1–M4 기여는 PR #40의 지표 정의 리뷰, 정책 분석, 집계표, 사례 및 분석 스크립트다. 초안은 원본 Ledger 접근 불가로 재생성 Ledger를 이용한 사후 탐색으로 시작했다. 이번 통합에서 승인된 원본 Development/Held-out SQLite를 read-only로 확인했다. DB run ID, seed, 승인 manifest, raw hash, source revision, schema, completed SCM 수, SQLite integrity 및 payload checksum을 대조했다. 원본에서 5,440 및 17,000 정책×예산행을 다시 읽어 85개 policy-budget aggregate와 저장된 정책 불일치 사례를 비교했다. 공개된 PR 집계표는 표시 반올림 정밀도에서 원본 값과 일치했다. 재생성 cohort의 모든 SCM-keyed raw 결과는 PR에 보존되어 있지 않으므로 SCM별 완전 일치를 주장하지 않는다.

Held-out S0에서 regret이 양수인 55개 사례 중 49개는 learner graph에 X→Y 유향 경로가 없었고 6개는 경로가 있었지만 추천 action 방향이 맞지 않았다. 전체 22,440 정책×예산 행에서 path가 있으면 predicted loss가 non-flat, 경로가 없으면 flat인 패턴이 저장된 결과에서 모두 일치했다. 이것은 현 learner와 target-tracking 행동 grid에 대한 경험적 관계다. 독립 표본 22,440개나 보편적 인과 정리로 해석하지 않는다.

메커니즘 사례는 단순한 “task 우선이 항상 낫다”는 설명을 지지하지 않는다. M4가 Full Greedy보다 나았던 Held-out B=2 행동 불일치 6건 가운데 5건은 M4가 X→Y 경로를 복원했고, 1건은 기존 경로가 있었지만 추정 방향과 추천 부호가 달랐다. 반례 `…000076`에서는 off-task FP가 남아 있으면 task 방향 수정이 DAG 순환을 일으켜 M4가 중단됐고 Full Greedy가 FP를 먼저 제거해 더 나았다. `…000141`의 off-task FP는 올바른 방향의 유일 경로를 만들고 있어 삭제가 추천을 악화시켰다. `…000146`에서는 구조 수정 후 경로가 끊기며 원래 맞았던 action이 악화됐다.

Greedy 점수 설명도 수정했다. 같은 subset 안의 공통 `1/|S|` 정규화는 후보 간 상대 순위를 설명하지 않는다. M4의 상대 gain에는 활성 오류 성분 수, 각 성분의 G0 고정 support, 후보 구조 및 DAG 제약, 동점 순서가 함께 작용한다. M4 지표 자체가 잘못 정의됐다는 결론은 내리지 않는다.

이 분석은 Held-out을 열람한 뒤 수행한 post-hoc exploratory analysis다. 원본 Ledger 검증은 출처 정확성을 개선했지만 분석을 사전 등록된 확증 분석으로 바꾸지 않는다.

## 6. Research D 반합성 강건성 평가

실제 물리 검증은 Causal Chamber Mk2와 Wind Tunnel에서 참조 구조·시간 정렬·독립 실험 단위의 근거가 기존 연구 계약을 지원하기에 부족해 보류했다. 다른 dataset 탐색을 이어가지 않고 causalAssembly Station1 외부 반합성 강건성 검증으로 연구 범위를 좁혔다.

Research D는 causalAssembly 1.2.1의 공개 제조공정 기반 반합성 sample 및 official Station1 benchmark DAG에 DRF를 재적합한 **단일 고정 생성환경**을 사용했다. Station1 reference는 6 nodes, 7 directed edges다. Study task는 `Station1_mp_0 → Station1_mp_4`, reference path `mp_0 → mp_1 → mp_4`; 이는 virtual benchmark hard-do다. 고정된 Development training frame 512행, 200 G0 corruption draws, 5 common actions, action당 2,500 evaluator rows를 사용했다. 200개 G0는 200개의 독립 외부 SCM이 아니다.

B=2에서 S0 mean bias-corrected target-tracking loss는 `0.823587`, Full Greedy는 `0.789362`; Primary `+0.03422490`이다. G0-only 95% interval `[0.02664478,0.04180501]`, action-MC-only `[0.00650999,0.06284998]`, two-source `[0.00617347,0.06535080]`. Action-MC 반폭 0.020 및 two-source 반폭 0.025의 사전 보고 정밀도 목표는 모두 미충족했다. 승인 sample size 이후 표본을 늘리지 않았다.

M4 B=2 loss `0.790592`; M4−Full Greedy `+0.00122956`, two-source interval `[0.00000000,0.00391596]`. M4 mean edit count 0.335, Full Greedy 1.160, 동일 행동 198/200. Graph-free observational association baseline의 loss는 `0.789362`로 Full Greedy와 같았다. Graph-free 모델은 causal effect estimator가 아니다.

Independent artifact audit 27/27 checks와 이 문서 작성 시점의 read-only 재감사가 모두 PASS였다. 연구 실행 자원은 약 407.6초, process-tree RSS 표본 peak 약 1.92 GB였다. 이 기술 무결성은 추정 효과 크기의 정밀도 부족이나 단일 DGP 한계를 해소하지 않는다.

## 7. Research C–D 통합 해석

Research C는 독립 synthetic SCM population에서 정해진 구조 수리 절차의 analytic regret을 시험했다. Research D는 다른 topology와 DRF 기반 외부 반합성 생성 메커니즘에서 같은 큰 방향의 양의 정책 대비를 관찰했다. 두 결과는 “구조 정확도 자체”가 아니라 한정된 수리 정책이 이들 계약 안에서 실제 행동 loss에 연관될 수 있다는 점을 보여준다.

두 Primary의 효과 크기는 직접 합산·비교하지 않는다. Task, SCM/DGP, learner-training frame, loss evaluator 및 표본 단위가 다르다. Research D는 유리한 벤치마크를 통과했더라도 graph-free baseline과 같았고 정밀도 목표에 못 미쳤다. C와 D 모두 reference graph를 사용하므로 field deployment에서 참 구조를 모르는 상황의 오류 탐지 성능을 검증한 것이 아니다.

## 8. 경영학적 시사점

이 결과는 의사결정에 가까운 구조 수리 기회를 제한된 분석 자원 배분의 후보 기준으로 삼을 수 있다는 연구 설계상의 시사점을 준다. 다만 본 연구에서 수정 비용은 간선 edit count뿐이다. 전문가 검토 시간, 검증 비용, 생산중단, 안전 리스크, 조직의 데이터 접근 제약 또는 실제 운영손실을 측정하지 않았다. 현장 관리자가 task-zone 점수에 따라 예산을 배분해야 한다는 처방이나 경제적 ROI를 도출하지 않는다.

## 9. 연구 한계

1. **Oracle-assisted repair:** reference DAG로 오류와 task zone을 정의했다. 현장처럼 참 구조를 모르는 graph repair를 해결하지 않았다.
2. **환경:** C는 자체 설계 synthetic SCM, D는 공개 반합성 표본으로 적합한 단일 DRF DGP다. 물리 제조 개입 또는 complete physical GT 검증이 아니다.
3. **통계 단위:** C의 200은 독립 SCM이고 D의 200은 한 DGP에서 graph corruption draws다. D에서 fitted generator·학습 frame의 불확실성은 포함되지 않았다.
4. **정밀도:** D의 action-MC-only 및 combined interval 반폭 목표를 충족하지 못했다.
5. **행동·손실:** 각 환경의 고정 action grid와 target-tracking loss에만 조건부다. D의 모든 관측 action 평균은 target보다 낮았으나 이것은 finite sample 요약이며 population infeasibility 증거가 아니다.
6. **수리비용:** edit count는 노동시간, 비용, 안전·검증 노력을 측정하지 않는다.
7. **Secondary/post-hoc:** M4는 Development-selected Secondary, Changmin 메커니즘 분석은 Held-out 열람 뒤의 탐색이다.
8. **Baseline/반례:** D graph-free baseline은 Full Greedy와 같은 손실을 냈다. off-task FP가 task 수정에 영향을 준 C 반례가 존재한다. M4의 일반 우월성을 주장할 수 없다.
9. **외부 자료 provenance:** causalAssembly sample을 다시 적합한 DRF generator이며 외부 연구진이 물리적으로 확정한 causal mechanism을 그대로 사용한 것이 아니다.

## 10. 결론

동결된 Research C 계약 안에서는 B=2 Full Greedy가 Held-out 200 synthetic SCM에서 무수정보다 낮은 평균 regret을 보였다. 원본 Ledger 후속 감사는 메커니즘 분석이 승인 결과와 연결되는 정도를 높였지만 사후 분석 지위는 그대로다. Research D 단일 외부 반합성 DGP에서도 양의 S0−Full Greedy loss contrast가 관찰됐으나 두 MC 정밀도 목표를 충족하지 못했고, baseline과 같은 손실 및 M4의 일부 악화 사례를 함께 고려해야 한다.

따라서 최종 결론은 “과제 관련 경로 구조를 고려하는 수리가 이 두 연구 계약에서 downstream 결정 손실 개선과 연결될 수 있다”로 제한한다. 실제 제조공정 개입효과, 참 DAG 불확실 환경에서의 자동 repair, M4의 일반적 우월성 또는 현장 경제성·배포 가능성은 아직 입증되지 않았다.

## 재현 문서

- [주장–증거 매핑](FINAL_CLAIMS_EVIDENCE_MATRIX.md)
- [검증 결과표](FINAL_RESULTS_TABLES.md)
- [원본 Ledger 감사](ORIGINAL_LEDGER_MECHANISM_AUDIT.md)
- [Research D 재감사](RESEARCH_D_FINAL_REAUDIT.md)
- [발표 증거 가이드](FINAL_PRESENTATION_EVIDENCE_GUIDE.md)


## 11. Research E — 사후 예산·비용 효율 확장

Research E는 기존 C Development 64 및 Held-out 200 SCM을 동일 입력에 조건부로 사용해 B=5–7/9까지 추가 예산을 살펴본 post-hoc extension이다. 추가 독립 SCM이나 G0는 만들지 않았다. 원래 B0–4 22,440 unit rows의 graph, edit sequence, action 및 analytic regret 재생은 기존 코드의 `1e-12` regret tolerance 아래 일치했다. E 확장 실행 코드는 G0 자체 hash를 별도로 비교하지 않고, 저장 초기 graph로 B0 결과 graph hash·edit/action을 재생해 간접 확인한 점을 provenance 한계로 남긴다.

예산의 평균 효과는 단조 감소하지 않았다. Held-out M4 regret은 B=3과 4에서 0.00143536으로 같았지만 B=5–9에서 0.00129902가 됐다. M2+M4는 B=4에서 Full Greedy와 같은 평균 regret .00096391을 1.440 대 2.005 edits로 냈지만, Adaptive M4는 B=3에서 평균 regret .00096391에 0.780 edits였다. Full Greedy B=3 비용은 1.790이며, 과거 문서의 1.325는 Research D 수치 혼입으로 바로잡았다. 이 평균 비교는 사후 기술 통계다.

Bmax에서 M4가 완전히 복원한 비율은 Dev 18/64, Held-out 80/200이며 나머지는 잔여 구조 오류가 있다. M2+M4는 27/64, 109/200이었다. DAG constraint saturation도 M1 계열 등 여러 policy/cohort에서 드물게 발생해 full table로 정정했다. Reference learner는 평균 regret .002560 (Dev), .000828 (Held-out)였고 grid optimum과 63/64, 198/200에서 일치했다. Bmax의 Full Greedy/Canonical Oracle는 reference learner action과 264/264 일치했으나 잔여 오류가 있는 M2+M4도 264/264 일치했다. 구조 복원과 추천 일치는 다르다.

Adaptive M4 B3의 Held-out paired 차이는 −.000471447이며 구간은 [−.001414341, 0]; 단 1/200 개선, 0 악화, 199 동률이고 평균 edit 수는 M4보다 .020 높았다. 따라서 두 blocker edit가 두 결정 개선을 만든 것으로 표현하지 않는다. C Held-out expanded cross-budget frontier에는 Adaptive M4 B3 및 B5–9가 포함됐고 Full Greedy는 평균 좌표에서 frontier가 아니었다. `Jλ` lower envelope는 λ≈.0045445, .0235724, .0392675, .1287068에서 순차적으로 Adaptive B5–9, Adaptive B3, M4 B3, M4 B2 및 no-edit 동률로 바뀐다. λ는 가상의 edit penalty다.

δ=0 공통 target 민감도는 평균 회귀 과제의 특수 조건이다. M4 B2는 모두 k=0을 추천했으며 grid-optimal action은 Dev 58/64, Held-out 185/200에서 내부 action이었다. 이 결과는 목표값 의존성의 증거지 다양한 제조 목표의 강건성 증거가 아니다. D 원시 evaluator vectors는 이번 E 종료 작업의 지정 저장소에서 발견되지 않아 앞선 27-check D audit 요약만 확인했다. 새 D unit-level 재분석은 없다. 전체 교정·Pareto·입력 hash는 [Research E 최종 감사](RESEARCH_E_FINAL_AUDIT.md)와 `research_e_audit/`에 있다. 확장 Pareto 및 λ 구간 그림은 [E9](research_e_audit/figures/E9_expanded_pareto.svg), [E10](research_e_audit/figures/E10_lambda_lower_envelope.svg)이다.

Research E는 이미 C Held-out 결과를 본 뒤 수행한 사후 extension이다. 예산 민감도와 적응형 규칙의 적용 조건을 설명하는 자료이며 C의 confirmatory Primary를 바꾸지 않는다.

## 12. 프로젝트 종료 및 후속 연구

현재 프로젝트는 Research C, mechanism analysis, Research D, Research E의 문서화된 한계를 보존한 상태로 종료한다. 추가 데이터셋 탐색이나 실험은 계획하지 않는다. Research F (uncertainty-aware graph verification), Research G (안전한 물리 테스트베드 개입), Research H (기업 현장·경제성 검증)는 향후 연구 제안으로만 기록하며 이번 작업에서 설계하거나 실행하지 않았다.

## Research F-Lite final audit addendum

Research F-Lite는 C의 기존 Development/Held-out SCM을 재사용한 post-hoc reference-blind query-policy prototype이다. 저장 결과를 재감사한 결과, B=4 Held-out에서 Decision-weighted Regret `.016281`은 Random `.081223`보다 낮았지만 Fit-based `.003770` 및 Suspicion-only `.006061`보다 높고 Impact-only `.017270`과 거의 같았다. 이는 제안 결합 점수의 일반적 우월성을 지지하지 않는다.

Random의 action-change 지표는 두 정의로 분리했다. Held-out B=4에서 평균적인 32회 반복 변경 비율은 4.09%이고, 최소 한 번 변경된 SCM 비율은 27.0%다. 저장 답변을 G0에서 replay했을 때 B=4 pending 6개 policy–SCM 사례 모두 최종 DAG에서 개별 적용이 불가능했고, 저장된 최종 graph와 replay가 일치했다. 공통 SCM bootstrap index를 공유한 추가 pointwise 재집계는 기존 순차-RNG comparator별 구간과 별도로 보존했다.

F-Lite의 policy input은 allow-list 기반 인터페이스 경계이며 같은 Python process 안에서 실행된다. simulated expert는 참조 구조를 알고 있으며 OS sandbox는 없다. 검증 질의 수와 허용된 간선 수정 수는 서로 다른 비용이다. 실제 전문가 시간, 금전 비용, 공장 성능 또는 안전성은 측정하지 않았다. 연구별 증거 등급과 주장 범위는 [`FINAL_CLAIMS_EVIDENCE_MATRIX.md`](FINAL_CLAIMS_EVIDENCE_MATRIX.md), F 감사는 [`RESEARCH_F_FINAL_AUDIT.md`](../decision_oriented_verification/RESEARCH_F_FINAL_AUDIT.md), 논문 구조는 [`FINAL_PAPER_OUTLINE.md`](FINAL_PAPER_OUTLINE.md)를 참조한다.

## Supplementary S1/S2 audit addendum

S1/S2 are post-hoc supplements using saved Research C results and do not alter the frozen C primary. The S1 comparator was corrected: Full Greedy is `M1+M2+M3+M4`, while `CANONICAL_ORACLE` is a separate structural-only diagnostic. At original target, gamma=.2 and B=2, the corrected Held-out means are S0 .117959, Full Greedy .092235, M4 .087253 and M2+M4 .090312; shared-index paired SCM-bootstrap pointwise intervals for Full Greedy−S0 and M4−Full Greedy are [−.03798,−.01463] and [−.01077,−.00038]. At gamma=.5 Full Greedy mean regret (.082163) is below M4 (.083598); at gamma=1, the four compared policies all choose `k=0`. This objective dependence limits any broad claim that M4 is uniformly best.

The S1 empty-graph learner is named `EMPTY_DAG_LEARNER` and is not the observational association baseline from F. The saved F association baseline is .038725 Held-out at gamma zero; it was not evaluated on the new S1 objective grid. The S2 historical B/E feature groups were not nested; the post-hoc nested refit reports Held-out SCM-balanced MAE .06966 (B_original), .06153 (E_nested), and .03768 (F_nested), with paired pointwise SCM-bootstrap B−E difference .00813 [.00209,.01390] and E−F .02386 [.01674,.03116]. Metric correlations use shared SCM bootstrap draws and weighted Spearman defined as midranks followed by SCM-weighted Pearson. PR-AUC is tied-score-group weighted Average Precision, not trapezoidal area. Details and limits are in [`../final_supplementary_validation/SUPPLEMENTARY_FINAL_RESULTS.md`](../final_supplementary_validation/SUPPLEMENTARY_FINAL_RESULTS.md) and [`../final_supplementary_validation/SUPPLEMENTARY_CONTRACT_CORRECTION_V2.md`](../final_supplementary_validation/SUPPLEMENTARY_CONTRACT_CORRECTION_V2.md).

## Final Research E extension and whole-project integration (2026-11-28)

The later S4 reconstruction and S5 external conditional reconstruction are now incorporated as separate evidence layers. This addendum supersedes only the prior document's project-status statement that the E extension had not started; all original C/D/E/F-Lite results and their historical evidence grades remain unchanged. The saved S4 Development (80 SCM), S4 replication (160 SCM), and S5 (200 conditional G0 draws) unit records were re-aggregated for B=0–4 (16,560 rows). No new SCM, G0, observations, DRF fit, or intervention response was generated. S4/S5 B=5–9 replay was not run because preserved sealed recommendation/evaluation records cover B=0–4; no values were extrapolated.

S4 replication T5−M4 B=1 remained −0.0086644 with a 95% interval including zero; superiority and noninferiority are not established. S5 S0−M4 B=2 remained +0.00685175, with its G0-only interval excluding zero but action-MC-only and two-source intervals including zero. Graph-free association was slightly lower in mean S5 loss than M4. C regret, S4 analytic regret and S5 standardized tracking loss are not pooled. Full integration, reporting and presentation outlines are in [`FINAL_RESEARCH_FRAMEWORK.md`](../../FINAL_RESEARCH_FRAMEWORK.md); see its appended report chapter and slide storyboard.

## S6/S7 supplementary closeout

S6 v6 reaggregated the existing S4 Development 80 and replication 160 candidate records at B=1; it created no new SCMs or observations. In the replication, Frozen M4 mean regret was `.038817`, Type-ranked M4 `.036613`, T5-guided M4 `.030152`, Full T `.031391`, and the outcome-privileged ex-post oracle `.012907`. The Type-ranked−M4 paired difference was `−.002204` (SCM bootstrap 95% pointwise interval `[−.009283,.003545]`, better/worse/tie `2/1/157`, Holm-adjusted paired-t p `1.0`). T5−M4 was `−.008664` (common-index SCM bootstrap interval `[−.020398,0]`, `4/1/155`, adjusted p `1.0`). These post-hoc results do not establish superiority, equivalence or noninferiority.

S7 produced no persisted recommendation units (0/400 G0; 0/24,000 recommendations), no seal and no evaluator results. Final supervisor telemetry is missing, so cap enforcement and termination conditions cannot be verified. Static review found a direction-loss defect in the frozen runner's learner-fitting path: it passes canonical unordered pair keys to a learner that expects directed parent edges. The run did not persist a recommendation, and no new S7 result is inferred. Task-zone feasibility runtime is inconsistent across artifacts (`.7613 s` in JSON; `1.474 s` in prose). Both reported values are retained pending evidence on measurement scope. The frozen runner was not changed. Full scope and source links are in the [S6/S7 closeout](../supplementary_validation/S6_S7_CURRENT_CLOSEOUT.md).

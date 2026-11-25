# Research D External Semisynthetic Robustness — 미승인 계약 초안

이 문서는 Step 0–3 단계의 역사적 제안 초안이다. 2026-11-25 사용자 승인으로 bounded Development Pilot에 한해 현재 유효한 계약은 `research/external_validation/semisynthetic_evaluation/RESEARCH_D_DEVELOPMENT_CONTRACT.md`와 해시 잠금 실행 설정이다. 아래의 미확정 표현은 superseded 기록으로 보존한다.

## 연구 주장 범위

질문은 “외부 제조공정 benchmark 자료와 공식 station DAG에 `fit_drf()`를 적용한 **DRF-based external semisynthetic generator**에서도, 제한 구조 수정 예산의 오류 수정 우선순위가 decision loss에 미치는 방향/크기가 유지되는가?”다. 이는 실제 제조라인 intervention 효과나 제조현장 배포성 평가가 아니며, 단일 benchmark generator에 조건부인 강건성 사례다. 생성 reference는 CausalAssembly의 benchmark DAG이고 정책은 여전히 reference-assisted Oracle repair를 받는다. DRF가 특정 Station1 fit에서 실제로 비선형 함수를 표현한다는 진단은 아직 수행하지 않았으며, 이 설계는 그 주장을 전제하지 않는다.

## 후보 과제와 정보 경계

- 제안 task: `Station1_mp_0` 가상 hard-do → `Station1_mp_4` target-tracking, reference path `mp_0 → mp_1 → mp_4`.
- 이 task는 Research C strict indirect-only의 **반합성 확장 task**로서 직접 경로가 없는 것은 맞지만, 물리 장치에서 `mp_0`을 조작할 수 있다는 증거가 없다.
- 현재 승인된 Development action support: generator-fit source의 `Station1_mp_0` 10/30/50/70/90% quantile. 실제 수치는 개발 설정 잠금 파일에서 기록하며, 공통 evaluator 표본 생성 전에 고정한다. finite float hard-do adapter는 `PASS_FLOAT_HARD_DO_ADAPTER`를 통과했으며 이는 본실험 승인이 아니다.
- 목표 `y*` 및 scale은 별도 generated observational learner-training split에서 target 요약과 척도를 정하는 방안을 검토한다. intervention evaluation response로 결정하지 않는다. 실제 운영 목표라고 해석하지 않는다.
- Task/target은 구조 및 데이터 스키마에 따라 평가값 보기 전에 검토한다. 이 preflight의 exploratory output은 최종 평가에서 제외한다.

## Generator, learner, evaluator 분리

1. **Generator fit set:** pinned 500×98 공개 반합성 benchmark sample 및 pinned official DAG. 논문은 이 generator의 기반이 제조 assembly line에서 수집된 실측 자료와 공정 물리 지식에 기초한 partial causal ground truth이며, conditional DRF들을 결합해 반합성 표본을 만든다고 설명한다. 이 CSV 자체는 제조 원자료가 아니라 공개 반합성 benchmark 표본이다. 이 표본에 기존 `fit_drf`를 재적합하므로 이번 외부 DGP는 **반합성 표본에 다시 적합한 외부 자료 기반 DGP**이며, 외부 연구진이 물리적으로 확정한 causal mechanism을 그대로 사용한 것이 아니다 ([Göbler et al., 2024](https://proceedings.mlr.press/v236/gobler24a.html)). Python/R/DRF 버전과 적합 seed를 기록한다.
2. **Learner train set:** 고정 fitted DRF에서 별도 seed로 생성한 observational sample. Research C의 기존 observational Ridge learner 및 기존 graph recommendation/policy code를 유지한다. 생성 DGP object/DRF, intervention draw 및 `Y(do(a))`를 learner에 전달하지 않는다.
3. **Intervention evaluation:** train set 및 추천 freeze 후 별도 evaluator-only process에서 각 사전 고정 action의 별도 interventional DRF draw를 생성한다. same action-set/common evaluation protocol을 S0와 Full Greedy에 적용한다. 샘플은 smoke-exposed 표본과 분리한다.
4. **Structure repair:** pinned Station1 reference에서 Causal C error-injection / M1–M4 / S0 / Full Greedy / M4 / atomic cost 1을 유지하는 후보. policy engine 코드 변경 없이 existing Research C engine에 mapping하는 별도 adapter를 사용한다. Exact seed/candidate lists and information access must be frozen.

## 오류와 예산 초안

Station1은 6 nodes, 7 edges, 8 absent unordered pairs로 Research C가 사용한 6–10 node range 안이다. 우선 비교는 existing `q=.15`, `r=.05`, B=0–4를 그대로 두는 안이며 primary B=2를 보존한다. Reference edge damage proposal은 평균 1.05, FN/REV/UNRES 균등 제안이면 각 0.35; reference-absent FP proposal은 평균 0.40이다. DAG-invalid proposal은 같은 규칙으로 거절·기록한다. Task zone은 reference path로 정해지고 task-zone true edges=2, absent task pair=1이다. 이 구조로 M1–M4가 모두 활성되지만 seed별 실제 burden과 DAG rejection은 아직 생성하지 않았다. Task error를 강제하지 않는다.

이 제안은 graph size 및 절대 budget에서 Research C와 비교 가능성을 높이나, semi-synthetic source, node distribution, fixed external graph, DRF functional family, one DGP 때문에 Development/Held-out independent SCM population result와 같은 해석이 아니다. G0 q/r이 동일해도 error burden 분산은 C와 동일하다고 가정하지 않는다. 필요하면 predeclared burden strata는 별도 sensitivity만 가능하며 outcome 결과로 정하지 않는다.

## Primary 및 비교군 초안

- Primary candidate: B=2에서 `Δ = Regret(S0) − Regret(Full Greedy)`; 동일 task/action set/training sample/reference/G0/target/scale/evaluation draws로 paired.
- 같은 공통 action set의 population-optimal loss 항은 두 regret의 차에서 상쇄되므로 우선 추정량은 `L_exp(a_S0)-L_exp(a_FullGreedy)`이다.
- loss: `L(a)=(E[Y|do(a)]-y*)²/scale_train²`. 이는 목표 평균추종 손실이지 개별 행 MSE도, 물리 생산성 손실도 아니다.
- M4는 Secondary다. 연속 action 변수에 관측자료의 exact arm-mean을 바로 적용할 수 있다고 가정하지 않는다. 후속 계약은 같은 observational learner training data와 action support를 사용하는 단순 X–Y 회귀 추천 및 사전 고정 비선형 association regression을 graph-free **association** 기준선 후보로 비교 검토한다. 별도 intervention training data가 향후 승인되면 arm-mean을 별도 정보 수준 기준선으로 제안할 수 있지만, 평가 intervention 표본의 arm mean으로 행동을 추천하지 않는다. 이번 adapter preflight에서는 어떤 graph-free learner도 학습·비교하지 않았다.
- 절대 empirical regret은 행동 최솟값 선택 편향과 평가표본 불확실성을 별도 타당화하기 전 Primary로 두지 않는다.

## 분석 단위와 불확실성

한 공식 station reference graph와 한 DRF fit object가 외부 DGP 단위다. 여러 G0 seed와 Monte Carlo evaluation draw는 독립 외부 graph/SCM/물리장치가 아니다. (i) 고정된 graph/DGP 조건부 G0 seed 변동, (ii) generated learner/evaluator sample Monte Carlo 오차를 분리한다. S0/Full Greedy는 paired G0 및 공통 evaluation draws로 비교한다. 단일 DGP에 대한 결과를 외부 제조공정 모집단 확증으로 일반화하지 않는다. 효과 크기, 분산, 요구 정밀도 자료가 없으므로 cohort size를 이 단계에서 확정하지 않는다.

## 실패·제외 및 진입 전 잠금

- float hard-do adapter는 별도 Research D 코드에서 제한된 fixture 및 pinned causalAssembly R/DRF smoke로 기술 검증됐다. 이는 최종 action 집합, learner/evaluator split, 전체 정책 실행, 정보 경계 production gate 또는 본실험 승인이 아니다. 후속 계약 전에는 DAG/reference/variable hash, 공통 action support, generated observational training/evaluation split, evaluator 격리, loss/uncertainty 계약을 잠근다. float adapter의 재현 실패, 정보 경계 침해, 평가자료 누출이면 중단.
- 평가 response를 보고 task, action, target, scale, error strata, budget을 바꾸지 않는다.
- 개발 표본·외부 공개 benchmark 결과를 완전한 미열람 held-out이라고 부르지 않는다.
- 다음 단계 진입 조건: adapter source와 fixture 테스트 리뷰, 단일 hard-do API 범위 승인, 향후 evaluator isolation/seed 및 train/evaluation separation 구현 계약, licensing/attribution 확인, G0 strata와 split contract 승인. 이번 기술 adapter PASS만으로 후속 개발 pilot이나 본실험을 승인하지 않는다. AGPL-3.0 pinned software source를 수정·복제하지 않고 얇은 adapter만 유지한다.

# Research D Step 2: Design Resolution

일자: 2026-11-25. 기준 HEAD: Step 1 `6483c9b49f1eb388ea862eb9ec20564b4f84cff5` (부모 `7c5bd93bfa798eeb2e3b3e3549cb68538f1688b8`); Step 0 `89a49224a997f33aee5a5075842144df48e39d45`는 그 조상에서 두 commit 아래다. 이 작업은 Step 1에서 분기했으며 Research C 및 Step0/1 산출물을 보존한다.

## A. 결정

**추천 OPTION C — `PHYSICAL_CASE_REDESIGN_REQUIRED`.** 공개 Wind Tunnel 자료는 물리 장치의 실제 randomized command blocks이며 기존 Mk2와 달리 블록 단위 배정 구조 및 지원 범위를 재현 가능하게 확인했다. 그러나 기존 M1–M4 정책의 의미 있는 외부 decision validation에는 부족하다. 두 사전 후보 `load_in→rpm_in`, `load_in→pressure_intake`는 참조 graph상 직접 간선이고, 기존 task-zone은 단일 pair, Rule A task-FP 기회는 0이다. 더구나 32-node graph로의 오류 계약과 sequential randomized SET 자료에 대한 학습/평가 계약은 Research C의 6–10 node SCM 및 observational learner와 같지 않다.

따라서 Wind Tunnel을 이 단계에서 Research D 본실험용으로 채택하지 않는다. 다음 진입 전에는 (1) 외부 direct task에 맞춘 정책/오류 범위가 기존 구조 수리 질문을 보존하는지 재정의하고, (2) randomized block 자료용 학습 알고리즘과 estimand를 정하며, (3) target/scale의 운영적 근거와 temporal inference 조건을 결과를 보기 전에 승인해야 한다. 이 설계 재검토는 새 과학 계약 승인 대상이다. `OPTION B`는 기존 M1–M4가 직접 task에서 비교할 가치가 있다는 필수 조건을 충족하지 않아 추천하지 않는다. `OPTION A`는 불완전한 complete physical GT 전제 때문에 부적격, `OPTION D`는 선택 가능한 설계 재구성이 남으므로 아직 선택하지 않는다.

이는 실측 성능 결과가 아니다. 연구 질문은 “제한된 수정 예산에서 어떤 구조 불일치를 고치는 것이 실제 측정자료로 평가한 결정 성능에 도움이 되는가?”로 유지할 수 있으나, 이 데이터에 적용하는 구조 수리 의미/학습자/분석 단위는 재설계되어야 한다. Direct-task 확장은 Research C strict indirect-only의 반복 검증이 아니다.

## B. Mk2 보류

Mk2는 계속 `DEFERRED_PENDING_EXTERNAL_EVIDENCE`. Step 1 이후 공개 근거에서 참조 graph 완전성/negative pair, SET–MSR row timing, device/session/reset/settling provenance를 해결할 새 증거는 확보하지 않았다. 이번에는 같은 자료를 다시 반복 검색하지 않았다. 해결 가능 blocker와 외부 문의 초안은 [요청 초안](MK2_EXTERNAL_EVIDENCE_REQUEST_DRAFT.md)에만 남겼으며 보내지 않았다.

Wind Tunnel 수치 오류·시계열 동작이 Mk2를 소급 해결하지 않는다. 두 후보 모두 공개 reference direct edge이므로 strict indirect-only는 충족되지 않는다.

## C. 실제 프로토콜과 지원

핀된 공식 generator의 2,000 block/100 MSR/8,000 ms wait/seed 42 프로토콜은 archive와 일치한다. 기존 ZIP의 SHA-256 및 크기는 Step0 manifest와 재대조했다. outcome을 제외한 8개 열만 읽었다. 2,000개 flag group은 모두 100행, 각 block 내 load_in 일관, rng seed 42 순서 재현 일치, block 첫 행에 intervention 표식, timestamp block gap은 약 8.25–9.32초였다. 이는 배정 프로토콜의 실제 기록 증거이며 정상상태·물리 actuation telemetry·독립성 증거가 아니다. 상세 근거는 [block audit](WT_BLOCK_AND_ACTION_SUPPORT_AUDIT.md)와 `inspection_wt_blocks.json`에 있다.

5개 예시 행동 수준은 전체 아카이브에서 12–24 block씩만 지원한다. 이는 분할 후 지원량이 아니며 독립 run/session도 아니다. 확정 action set은 없다. outcome 응답값과 action별 평균/효과는 계산하지 않았다.

## D. M1–M4 비교 가치 및 오류 계약

공식 `wt_standard` graph는 32/42 DAG이며 모든 graph node가 CSV schema에 있다. pair는 전체 496, 참조 부재 454, oriented candidates 908. 다만 graph는 모든 부재 pair의 물리 음성 검증이 아니다.

완전 물리 GT 계약은 FAIL, 제한 verified reference는 pair-specific negative evidence가 없어 지금 채택 불가, reference-relative benchmark는 명확한 표현으로 가능하지만 direct task에서 M4가 1개 edge의 FN/REV/UNRES만 처리하고 FP opportunity 0인 구조다. off-task 오류가 실측 action loss를 바꾼다는 증거는 없다. M1–M4의 정책 점수 proxy가 외부 환경에서 유용한 수리 우선순위를 제공한다는 전제가 이 task만으로 평가될 수 없다. 전체 대안은 [reference contract](REFERENCE_RELATIVE_CONTRACT_OPTIONS.md), 구조 fixture 결과는 [preflight](EXTERNAL_STRUCTURE_PREFLIGHT.md)에 기록했다.

## E. 학습–평가와 graph-free comparator

이 자료는 무개입 관측자료가 아니라 block별 SET이 이어지는 randomized command experiment다. 기존 SCM observational fit 입력으로 곧바로 대체할 수 없다. 평가 손실의 목표값과 학습 분산은 평가 응답에서 얻으면 누출이다. 동일 자료를 train/evaluation으로 나누려면 block과 시간 의존성을 고려한 사전 split 및 buffer가 필요하다. 원 연구가 이 공개 benchmark를 사용했으므로 완전히 미열람 외부 held-out이 아니다.

만약 후속 재설계가 action outcome 예측을 포함하면 `GRAPH_FREE_ACTION_BASELINE`은 필수 comparator다. 동일 train blocks, target/scale, common action set, evaluation blocks를 사용하되 arm-mean 모델은 randomized assignment에 직접 학습하므로 구조 모델과 정보 차이를 적는다. 평가 자료로 행동을 추천/튜닝하면 안 된다.

## F. 실험단위·주장 범위

관측된 계층은 물리 시스템/장치 ID(미공개), archive/config `standard`, generator상 한 experiment, 2,000 순차 assignment blocks, block당 100 센서 행, 하나의 task, 향후 여러 G0/policy/budget이다. 이 중 독립 단위 수를 확정할 정보는 없다. 2,000 blocks 또는 G0 seed는 2,000 독립 장치/세션이 아니다. 현재는 기록/설계 사례 검토만 가능하고 무작위화 기반 효과추론도 carryover, actuation alignment 및 serial dependence 가정 때문에 정당화되지 않았다.

## G. 기술 preflight 및 산출물

완료: schema/graph compatibility validator, direct-task zone/FP opportunity 검사, 오류 유형 API를 점검하는 작은 deterministic fixture, outcome-blind block support inspector. 새 validator와 Step1 qualification validator를 root `tests/` discovery에서 실행하도록 했다. `OPTION A/B`가 부적격하여 외부 model fit/evaluator, production graph repair policy adapter, action recommendation, loss evaluator는 구현하지 않았다. Research C 코드/계약은 변경하지 않았다.

## H. 중요한 불확실성/반증 가능성

- 유지된 지점: 공식 generator와 block assignment sequence 일치, 파일 hash 일치, task와 오류 구조를 outcome blind로 평가, 공개 benchmark를 외부 holdout으로 과장하지 않음.
- 부족: 공개 CSV만으로 device/session identity, reset, physical actuation, measurement timing 및 정상상태를 알 수 없음. 변수 정의의 자세한 물리 단위/운영 target 근거도 공개 schema에는 없음.
- 설계 반례: 후속 재계약에서 task zone을 확장하거나 multi-variable path task를 정당화할 수 있고, 보조 로그가 single-device randomized inference를 뒷받침할 수도 있다. 그 경우 이번 중단은 최종 폐기가 아니라 새 검토 대상이다.
- 실패 위험: 하나의 archive split은 시간적 drift/carryover로 train/evaluation 간 일반화가 깨질 수 있다. 그래프 수리 점수와 action response learner의 기여를 분리하지 못하면 핵심 질문에 답하지 못한다.
- 제조 일반화: Causal Chamber bench는 실제 물리 시스템이지만 DAT 제조공정의 공정 변수, 안전성, 비용, 현장 다변이성을 대표하지 않는다.

## I. 다음 진입 절차

다음 단계는 자동 시작하지 않는다. 먼저 새 승인에서 OPTION C에 맞는 명시적 연구 계약, direct task를 쓰는 근거, 참조-relative scope, 목표/scale 근거, action split/support, temporal estimand, learner/graph-free baseline, 독립 단위와 정밀도 계획을 정해야 한다. 외부 maintainer 문의가 승인되면 초안을 검토·발송한 뒤 답변 증거를 갱신한다. 응답/개발 평가값에 접근하기 전에 split과 모든 후보를 고정한다. 이 조건이 불가능하면 `OPTION D`로 실제 자료 기반 성능 검증을 중단한다.

**본실험 승인, 최종 데이터 채택, 실제 정책 Regret 계산, 장치 원격 제어는 이 산출물로 승인되지 않는다.**

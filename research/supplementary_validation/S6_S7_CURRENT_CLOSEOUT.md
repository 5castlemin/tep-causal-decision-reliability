# S6–S7 진행 현황 및 과학적 종료 기록

관측 기준: 2026-11-28 15:05 KST. S7 recommendation worker는 이 기록 시점에도 실행 중이었다. 완료 단위의 마지막 안전한 in-memory snapshot은 14:58 KST이며, 15:05에는 새 stack 및 파일 상태를 확인했다. 이 문서는 S6 결과를 별도로 닫고 S7 상태를 실제 완료 단위로 기록한다.

## S6 — 저장 결과 재집계

S6는 기존 개발 80 SCM과 독립 복제 160 SCM의 candidate value 및 policy 결과를 사용한 post-hoc 분석이다. 새 SCM/G0를 생성하지 않았다. 후보 수정은 SCM 안에 중첩되므로 표본 단위는 candidate row가 아니라 SCM이다.

독립 복제에서 오류 유형별 단일 수정의 SCM-balanced 평균 regret 감소량은 FN 0.08915 (cluster bootstrap 95% CI [0.03491, 0.15449]; 41 SCM, 47 edits), FP −0.03782 ([-0.10056, 0.00297]; 24 SCM, 29 edits), REV 0.11401 ([0.04119, 0.19209]; 39 SCM, 40 edits), UNRES 0.04956 ([0.00027, 0.10336]; 34 SCM, 42 edits)였다. 각 값은 해당 단일 수정 후보가 존재한 SCM들에 조건부인 기술량이며 오류 유형의 인과효과가 아니다.

B=1 replication에서 type-ranked M4−Frozen M4 차이는 −0.002204 (95% 공통-index paired SCM bootstrap [−0.009283, 0.003368], better/worse/tie 1/0/159)였다. T5−M4는 −0.008664 (기존 고정 S4 구간은 0을 포함하고 precision target 미달), 4/1/155였다. Type−T5는 +0.006460 ([−0.001180, 0.017319], 0/3/157)였다. M4와 ex-post single-edit oracle 차이는 +0.02591 ([0.01020, 0.04486])이며 oracle은 실제 regret을 사용한 privileged benchmark다. 이 연구는 사후 탐색이며 오류 유형별 우월성이나 실행 가능한 oracle-free 정책을 입증하지 않는다.

개발 코호트에서 type-ranked policy와 T5의 B1 평균 regret은 같았고, S6에서는 별도 확증 표본 생성/검정을 하지 않았다. 별도 확증을 생략한 이유는 높은 tie mass와 방어 가능한 SESOI/precision 설계의 부재다. 세부 계약, 집계 CSV 및 해시는 `s6/RESEARCH_S6_*`와 `s6/outputs/saved_candidates_v4/`에 있다.

## S7 — live recommendation 상태

실행 ID `s7-causalassembly-two-station-tasks-20261128-v1`, attempt 02. Lock/contract는 변경하지 않았다.

1. 외부환경 기준 그래프: causalAssembly Station1/공식 전체 benchmark가 아니라 고정된 Station2·Station3 task를 뽑은 동일 causalAssembly full-line graph, 98 nodes 및 485 directed edges. 두 task는 동일한 한 full-line DRF DGP를 공유한다.
2. 전체/완료 G0: 400 예정(Station2 200, Station3 200); 14:58의 in-memory snapshot은 0 완료였고, 15:05 파일 검사는 여전히 0 persisted이며 첫 Station2 G0의 task-zone 탐색 stack이 활성 상태임을 보였다.
3. 전체/완료 recommendation: 24,000 예정(12 policies × 5 budgets × 400); 0 완료·봉인. 공개 결과 경로도 비어 있다.
4. 최근 10분의 실제 완료 단위: 0 G0 및 0 recommendation. 실행 로그/저장 artifact 변화로 판단했으며 CPU 시간 증가를 진행으로 계산하지 않았다.
5. 마지막 read-only stack sample(15:04:43)은 `policy_engine.py:92–95`, 재귀 깊이 약 78의 `task_zone.<locals>.visit`에서 첫 `make_g0 → corrupt_graph_candidate → policy_engine.task_zone` 호출 안에 있었다. 전체 98-node truth graph의 simple-path 탐색이 병목이다. DRF fitting은 이미 완료됐고 관측 기록상 약 832.90초였다.
6. 반복 계산 경로는 코드에 존재한다: 동일 task/truth의 `task_zone` 반복, budget별 repair trajectory 재계산, G0마다 graph-free fit 재계산. Ridge action fit은 station+graph hash로 캐시되므로 station 내 동일 그래프 적합을 막지만, station 간 공유 그래프는 중복 적합 가능성이 있다. 첫 G0가 미완료라 실제 duplicate fit/recommendation 횟수는 0이며 중복 recommendation도 0이다. active run에 캐시 최적화는 넣지 않았다.
7. `training.csv`(643,985 bytes; SHA-256 `833c7dbac00a29f896d1fb433d90ff971c412702fe90495a2de5f5e535917245`)만 checkpoint다. G0/recommendation checkpoint와 sealed manifest는 없으므로 단위 경계에서 안전 재개할 수 없다. 저장 training frame만으로는 첫 G0의 부분 진행을 resume할 수 없다.
8. 봉인된 recommendation 이후에도 evaluation-stage DRF fit/input hash 확인, 50,000 intervention response rows(2 strata × 5 actions × 5,000), shared action-loss table, unit/aggregate contrasts 및 G0-only/action-MC/two-source bootstrap (각 잠금 분석 최대 10,000 replicates)이 예정되어 있다. recommendation이 0/24,000이므로 evaluator는 시작하지 않았으며 시작해서도 안 된다.
9. S7 execution lock의 cumulative wall cap 14,400초 및 process-tree RSS cap 4 GiB. 15:05:23 기준 실행 시작 11:46:36부터 11,927초 경과, 2,473초(41분 13초) 남음. RSS는 86,867,968 bytes(약 0.081 GiB)였다. 관측 RSS는 cap 이내였다. 감독 프로세스가 2초 간격으로 process-tree RSS를 샘플링하고 cap 초과 또는 wall cap 도달 시 worker를 종료하도록 잠겨 있다. 최종 resource report는 supervisor 종료 후에만 생성된다.

따라서 S7의 최신 파일 기준 상태는 `RECOMMENDATION_STAGE_ACTIVE_WITH_ZERO_PERSISTED_UNITS`이며, 14:58 마지막 in-memory snapshot도 0/400, 0/24,000이었다. 연구 Gate는 완료가 아니다. 프로세스를 임의 중단하지 않았고, 사전 cap 전에 표본/정책/evaluator를 바꾸지 않는다. cap 종료 시 존재하는 checkpoint와 resource log를 보존하고 `PARTIAL`로 닫는다. 이후 신규 실행은 별도 잠금과 정확성 테스트 없이는 재개하지 않는다. S7은 S6 결과의 상태나 해석을 바꾸지 않는다.

## 한계 및 다음 문서화 원칙

S6 결과는 post-hoc, error candidate가 있는 SCM에 조건부, 다중 비교와 높은 tie 비율을 가진다. S7은 단일 shared DRF DGP의 두 task stratum에 조건부이며 현재는 recommendation 산출조차 완료되지 않았다. 둘 모두 실제 제조라인 인과효과, 독립 제조 모집단 일반화, 실제 금전 비용 또는 안전한 현장 배포를 입증하지 않는다. S7 cap 종료 전까지 E 및 전체 통합 문서는 검증된 S6/S7 진행 상태만 반영하고 미완료 external 결과를 추정해 채우지 않는다.

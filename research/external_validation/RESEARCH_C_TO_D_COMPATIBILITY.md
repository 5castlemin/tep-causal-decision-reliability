# Research C 계약과 외부 검증 호환성

기준은 PR #39로 통합된 main `7742180cef09b506e3d26e56d58a03b3d6a4e37d`이다. 연구 질문은 고정된 편집 예산에서 어떤 구조 오류의 수정이 의사결정 손실을 줄이는가이다. Development 64개와 Held-out 200개 독립 SCM, 17정책 × 5예산을 평가했다. Held-out B=2의 S0−Full Greedy paired delta는 +0.07483636, 95% paired-t CI는 [0.05089822, 0.09877450]이다. 평균 Regret은 S0 0.09343898, Full Greedy 0.01860262, M4 0.00398775다. M4는 Development-selected Secondary다. Development의 낡은 G0 메타데이터 표기는 코드와 실행 계보에서 정정된 기록을 따른다. [계약](../../RESEARCH_C_EXPERIMENT_CONTRACT_V1.md) · [승인 브리프 §10](../../RESEARCH_C_APPROVAL_DECISION_BRIEF.md) · [Development 감사](../../RESEARCH_C_DEVELOPMENT_V1_AUDIT.md) · [Held-out 잠금](../../RESEARCH_C_HELDOUT_ANALYSIS_LOCK.md) · [Held-out 결과](../../RESEARCH_C_HELDOUT_V1_RESULTS.md) · [README](../../README.md) · [팀 인수인계](../../RESEARCH_JOURNEY_AND_TEAM_HANDOFF.md)

## 오류 판정과 정책 점수

모든 비순서 노드 쌍은 absent, unresolved 또는 방향 간선 중 한 상태를 갖는다. 참 adjacency가 빠지면 FN, 참에 없는 adjacency가 생기면 FP, 참 간선과 반대면 REV, 참 adjacency의 방향을 유보하면 UNRES다. 참에 없는 무방향 adjacency는 FP다. Task zone을 M4에 우선 귀속한 뒤 off-task FN/M1, FP/M2, REV·UNRES/M3에 한 번씩 귀속한다. 후보는 참 방향 추가, FP 삭제, REV 재지향, UNRES 해소다. 잔류 UNRES는 채점용 그래프에 남겨두고 학습 DAG에는 제외한다.

| 지표 | 공식 보고 | Greedy 잔존 proxy |
|---|---|---|
| M1 | off-task FN / off-task 참 adjacency | FN / G0 off-task 참 adjacency |
| M2 | off-task FP / 현재 추정 off-task adjacency | FP / G0 추정 off-task adjacency |
| M3 | off-task 올바른 방향 / 방향이 확정된 추정 참 adjacency. UNRES 수 및 matched true adjacency 내 비율 별도 | (REV + UNRES) / G0 off-task 참 adjacency |
| M4 | task-zone FN·FP·REV·UNRES count vector 및 각 support. FN 분모는 zone 참 adjacency, FP는 zone 추정 adjacency, REV는 zone의 방향이 확정된 matched true adjacency, UNRES는 zone matched true adjacency | 각각 G0 count가 양수이고 support가 있는 성분만 활성화. 성분별 G0 고정 support로 나눈 뒤 활성 성분 동일 가중 평균 |

공식 분모 0은 NA와 사유를 출력한다. Proxy의 비활성 항은 0이며 subset의 크기는 그대로다. 선택 subset의 평균 proxy 감소량을 연산 비용으로 나눠 순위를 매긴다. 후보는 오류를 실제로 제거하고 방향부 DAG와 잔여예산을 만족해야 한다. 점수 동률이면 M1→M4, canonical pair ID, 연산 순서를 적용한다. 단가 1의 합은 edit cost이며 공통 구조 벌점 `P_all`은 λ=1에서 모든 잔존 사건을 1회 센다. S0, 15개 비공집합 subset, 별도의 Canonical Oracle을 사용한다. Full Greedy는 전체 집합, M4는 단일 지표다. Canonical Oracle은 동일한 구조정보·후보·DAG·예산을 사용하고 gain 대신 canonical order로 선택한다. 정책 엔진은 전역 최적 성능을 찾지 않는다. [정책 엔진](../original_objective/policy_engine.py) · [독립 경계·순위 테스트](../../tests/test_original_objective_policy_engine_independent.py)

## 코드에서 확인한 정보 접근

| 단계 | 실제 입력과 경계 |
|---|---|
| 과제·손상 | 참 DAG 토폴로지로 strict task를 정의하고 G0를 생성한다. G0 참 edge 제안 q=.15, 손상 시 FN/REV/UNRES 각 ⅓, nonedge FP r=.05와 방향 균등. DAG 부적격이면 재추출 없이 거절하고 무오류 G0는 포함한다. 네 합성 템플릿 6–10개 노드의 층화 추출은 외부 장치에서 재현할 모집단 조건이 아니다. |
| 구조 수리 | `policy_engine.run`은 참 방향과 adjacency, G0, X/Y, B, subset, config를 받는다. 참 계수, GT action loss, 최적 행동, Regret 인자가 없다. |
| 학습·추천 | `e2e_fixture`가 수리 그래프와 학습 DAG 해시를 따로 기록한다. `prepare`는 공통 관측자료와 directed repaired edges로 노드별 standardized linear Ridge α=1을 적합한다. 내부 표준화는 ddof=0이다. `static_mean_response`는 X 방정식을 setpoint로 대체하고 DAG 순서로 잔차 평균 0을 전파한다. 행동은 학습 평균 + k×표본 SD, k=−1,−.5,0,.5,1. 목표는 학습 Y 평균+δ×표본 SD, cohort admission 순서에서 δ=±1 교대. 표준화된 평균 응답 제곱오차를 최소화하고 동률은 `(|k|,k)` 순이다. |
| 평가 | 추천 확정 후 `evaluate`에 signed-linear GT 구조방정식과 계수가 들어간다. 각 행동의 analytic hard-do 평균을 공통 목표·표본 SD로 평가한다. Regret은 선택 손실에서 같은 A의 최소 GT 손실을 뺀 값이다. |
| 통계 | 독립 SCM별 S0−Full Greedy B2 complete pair가 P1 분석 단위다. 실패·shortfall·동률 보존. paired-t와 SCM-level 보조 bootstrap을 사용했으며 정책, 예산, 오류, 행동은 반복 측정이다. |

[코드 README](../original_objective/README.md) · [runner](../original_objective/runner.py) · [G0](../original_objective/g0_candidate.py) · [실제 연결](../original_objective/e2e_fixture.py) · [추천/평가](../budget_aware_refinement/step3_adapter.py) · [학습](../../src/integrated_pilot.py) · [평균 전파](../../src/decision_mvp.py) · [end-to-end 경계 테스트](../../tests/test_original_objective_e2e_fixture.py)

## 이전 항목별 판단

| 구성 요소 | Research C 구현 | 외부 적용 | 필요한 변경 | 해석 영향 |
|---|---|---|---|---|
| GT DAG | 생성 DAG의 모든 쌍과 방향 | Mk2 조건부 | 설정·시간·노드/별칭·음성쌍 심사 | 대조 기준은 물리 모델의 확인 범위에 한정 |
| G0 | q/r 손상과 no-redraw | 엔진 재사용, 분포 이전 재검토 | 결과 비공개 구조 support·수락률 검사 | 오류 모집단과 포화율이 바뀜 |
| Task zone | 모든 X→Y 경로 합집합과 빈 조건화에서 열린 backdoor, 내부 collider 제외 | strict 후보는 Mk2 | 시간·mediator 매핑, 양 끝점이 zone인 FP Rule A 유지 | zone은 구조 관련성으로 해석 |
| M1–M4 | 위 표 | 승인된 전쌍 참조에서 그대로 | 부분 참조만 가능하면 현 계약 보류 | 비간선 미검증을 FP로 간주하면 결론 왜곡 |
| 수정 정책 | S0·15 subset·Canonical | 그대로 재사용 가능 | 외부 ID/그래프 adapter와 blind provenance | reference-assisted 진단 |
| 비용 | 수정당 1, B=0–4 | 상대 예산으로 조건부 | 후보 수·유효 예산·포화 검토 | 실제 전문가 작업량 추정 불가 |
| 관측자료 학습 | 공통 IID 512행 | 공통 자료 사용 가능 | 시간 블록, train-only scale 및 파일·장치 분리 | 실측 무작위 입력 기준분포 안의 추천 능력 |
| SCM 적합 | linear Ridge + static hard-do 평균 | 벤치마크로 조건부 | 상수·중복 채널·시점의 명시적 adapter | 비선형·시차 모델 변경 시 별도 확장 |
| 행동 후보 | 연속 단위의 5개 k | 정확한 실측 정수 수준 가능 | 공통 A를 메타데이터로 잠금, tie 규칙 명시 | 지원된 명령에 대한 제한 최적화 |
| 손실함수 | 표준화된 실험별 평균 응답 오차 제곱 | 동일 형식 가능 | 단위·목표·scale 및 시점 동결 | 목표 가중 및 위험 선호에 한정 |
| Regret evaluator | analytic GT | 블록 실측으로 대체 가능성 | 할당–계측 연결, 독립 평가, 표본오차 분리 | 참 regret 대신 추정치와 정책 대비 |
| 독립 표본 | IID 독립 SCM | 사례 연구 가능성 | 장치·session·배정·seed의 층 분리 | C와 동일한 SCM 모집단 CI 이동 불가 |

Strict indirect-only는 최소 하나의 유향 경로와 X→Y 직접 간선 부재를 모두 요구한다. 센서·중간 상태를 제거할 경우 directed 및 bidirected latent projection을 먼저 검토한다. 투영 후 경로가 직접 간선으로 축약되거나 숨은 공통원인이 남으면 C의 DAG 채점 계약을 그대로 적용할 수 없다.

90노드/142간선 Mk2 도식에서 C의 q/r을 전쌍에 적용하면 DAG 검증 전 제안 수의 기댓값은 참 adjacency 손상 21.3건과 FP 193.15건이다. 6–10노드에서의 두 편집과 회복 기회가 다르다. 도식의 `green→current_led_2_uv` task zone에는 유향 경로상 참 간선 3개와 Rule A chord 비간선 3개가 있다. FN과 UNRES는 참 간선, REV는 반전 후 DAG인 간선, FP는 비간선에서 가능하다. 이 경로에서 `led_2_uv→current_led_2_uv` 단독 반전과 `green→current_led_2_uv` 단독 추가는 DAG를 보존한다. 이는 구조 예시이며 주입 위치를 선택하는 규칙이 아니다. 복수 오류의 순환과 후보 상호작용이 남으므로 수락률, zone / off-zone 기회, 제안과 실현 비율, 유효 B 및 무오류·no-op를 outcome-blind 구조 gate로 검토해야 한다. B 변경에는 새 승인이 필요하다. [Mk2 전사와 후보 경로](inspection_results.json) · [후속 설계](RESEARCH_D_DESIGN_OPTIONS.md)

# 프로젝트 현재 상태

기준일: 2026-10-27. 현재 상태는 이 표와 `docs/research_state.json`에만 정의한다.
과거 문서는 `docs/history/`, 시간순 기록은 `WORK_LOG.md`에 보존한다. 외부 PR의 증거는 병합 여부를 명시한다.

| ID | 연구 흐름 | 상태 | 근거 | 다음 행동 |
|---|---|---|---|---|
| SRC-01 | Final 생성 코드 회수 | BLOCKED | docs/reproducibility/GRAPH_REPRODUCIBILITY.json | FREEZE.code의 algos/run_*.py 및 common/config.py·data_io.py 원본을 해시로 대조하여 회수 |
| SIM-03 | 공개 후보 수치·shutdown 검증 | PARTIAL | PR #4 병합(1e4fcc7): docs/audit/SIMULATOR_RELIABILITY_REPORT.md; experiments/simulator/diagnostics/analysis_20261023_v3/analysis.json | 압력 한계 종료와 제한적 dt 수렴 확인; 동일 모델·controller 독립 기준 대조 및 폐루프 시간 계약 검증 |
| SIM-04 | 공개 후보 새 객체 초기화 계약 | VERIFIED | PR #4 병합(1e4fcc7): docs/audit/SIMULATOR_RELIABILITY_REPORT.md; experiments/simulator/diagnostics/analysis_20261023_v3/analysis.json | 동일 source/backend/seed/mode의 새 객체를 반복 단위로 사용; 같은 객체 reset의 비트 일치 미보장 |
| COMPAT-01 | 공개 후보와 기존 데이터/GT 대응 | PARTIAL | docs/research_design/TEP_ENVIRONMENT_BRIDGE_FEASIBILITY.md | 원환경 계보·정식실행 미확보 유지. 새Python 내부동적 설계안은 별도사용자선택 대상. 기존F1과Python효과 결합금지 |
| SIM-01 | 기존 8월 시뮬레이터 복구 | BLOCKED | docs/SIMULATOR_SETUP.md | 당시 저장소 URL/ZIP·버전·실행 명령·로그의 구체 소재 확보 |
| SIM-02 | 공개 Python 후보 관측·쓰기·Fault smoke | PARTIAL | PR #4 병합(1e4fcc7): docs/audit/SIMULATOR_RELIABILITY_REPORT.md; experiments/simulator/run_20261023_v3/summary.json | 기존 2시간 정상 기록 보존; controller/override·수치 기준·호환성 제한 해결 뒤 Gate 재평가 |
| TASK-01 | 실행 가능한 복구 과제 확정 | BLOCKED | experiments/pilot/TASK_SPEC.md | 모델 호환 후 Fault/Action/Target·복구·안전 기준 사전 확정 |
| EFFECT-01 | 독립 개입·Recovery/Safety 측정 | NOT_RUN | experiments/pilot/PILOT_RESULT.md | 확정 과제로 no-action 대비 동일 조건 실험 |
| DATA-01 | 원자료 취득·권리 | PARTIAL | docs/reproducibility/TEAM_GUIDE.md | 고정 커밋 취득은 검증됨; 재배포 권리 추가 확인 |
| GRAPH-01 | Final 7개 산출물·평가 보존 | VERIFIED | docs/reproducibility/GRAPH_REPRODUCIBILITY.json | 동결 파일 수정 없이 생성 코드 회수와 분리 유지 |
| SCM-01 | 정상 관측 수치 적합 | PARTIAL | experiments/pilot/logs/normal_fit_summary.json | 관측 적합을 독립 효과 검증과 구분 |
| PCMCI-ID | PCMCI+ 순환 식별 | BLOCKED | docs/audit/pre_fitting_final_freeze.json | 동시점 순환의 인과계수 식별 근거 검토 |
| TASK-STRUCT | 12개 구조 평가 후보 | VERIFIED | docs/tasks/structural_task_candidates_v1_1.json | 독립 표본/실제 복구 과제와 구분 유지 |
| DOC-01 | 현재 상태 동기화 | VERIFIED | scripts/check_research_state.py | state JSON 수정 후 문서 생성·일치 검사 |
| GRAPH-GEN | Final 7개 생성 학습 재실행 | BLOCKED | docs/reproducibility/GRAPH_REPRODUCIBILITY.json | 정확한 algos/common 원본 회수 후 환경과 frozen 동일성 검증 |
| BENCH-ENV | 공식 수정 TEP 복원 환경 | BLOCKED | docs/research_design/TRACK_A_RECOVERY_GATE.md | 승인된 MATLAB/Simulink 위치·버전·라이선스 확보; PATH/registry/제품/일반 경로 탐색은 미발견, 라이선스 조회·로딩 NOT_RUN |
| EXPORT-01 | 정상 run과 benchmark export 연결 | BLOCKED | docs/research_design/TRACK_A_RECOVERY_GATE.md | 원시 run·median stride/경계·1499행 생성 코드를 회수; 불가 시 전환 대안의 승인 요청만 준비 |
| REF-B | Track B 참조 구조 타당성 | PARTIAL | docs/research_design/REF_B_MINIMAL_SUBSYSTEM_VALIDATION.md | 최소 내부 상태식 검산 완료; 관측 projection/비간선/알고리즘 의미의 외부 방법론 검토 전 추가 GT·실험 중단 |
| SIM-B | Track B 제어기·잡음 정렬 계약 | PARTIAL | docs/research_design/REF_B_MINIMAL_SUBSYSTEM_VALIDATION.md | 5초 밸브/3step cascade/관측 cache 순서 확인; 방법론 문제 해결 전 장기·Fault 실험 확장 보류 |
| DESIGN-B | Track B 가설 유지·통계 설계 | BLOCKED | docs/research_design/REF_B_MINIMAL_SUBSYSTEM_VALIDATION.md | 관측 수준 참조가 불가하면 원가설 보류/국소 도달성으로 범위 축소 대안을 검토; 전환은 사용자 승인 대상 |
| MVP-TECH | 공통 추천 dry-run·API 기술 파일럿 | VERIFIED | docs/research_design/CAUSAL_METRIC_TO_DECISION_MVP.md | 기존3모델 추천 dry-run/정해진 조작 반복·로거 재사용; 가설 검증으로 해석 금지 |
| ENV-MVP | 구조·추천 평가환경 대응 | PARTIAL | docs/research_design/ENV_MVP_ACCEPTANCE.md | 검증된 합성 범위를 유지하고 제조 환경의 노드·직접 구조·do 의미가 같은지 입증할 채택 계약을 분리; 제조 채택 미승인 |
| POLICY-MVP | 실제 추천 정책 연결 | PARTIAL | docs/research_design/PATH_METRIC_INCREMENTAL_VALIDATION_REPORT.md | 실패24행은 기준 조작0의 실제 이론 손실로 운영 평가; 가용2136/2160·조건부·계산추천1326 분리 유지 |
| EVAL-MVP | 구조 지표–추천 성능 비교 | PARTIAL | docs/research_design/MANUFACTURING_VALIDITY_GATE_REVIEW.md | 낮은F1을 사후튜닝하지 않음. 7graph/84과제·198쌍 검산을 구조 진단으로 유지하고 제조 효과와 결합 금지; 참조·환경계약 선결 |
| ENV-EXAMPLE | 예제 FCM GT·관측·do adapter acceptance | VERIFIED | docs/research_design/ENV_MVP_ACCEPTANCE.md | 고정 source/lock/원시 잡음/배치 검증 재사용. 제조/시간/반사실 검증으로 확대하지 않음 |
| PILOT-IID | 4변수 합성 통합 학습·추천·do 실행 | VERIFIED | docs/research_design/FIRST_INTEGRATED_PILOT_REPORT.md; research_runs/first_integrated_pilot/reproducibility_check.json | 두 잡음군 별도 3학습/1과제 연결 결과를 유지하고 다중 독립 학습 조건 계획에 활용; 제조 채택 아님 |
| PILOT-REPEAT | 합성 독립 반복·4과제·미확정 정책 비교 | VERIFIED | docs/research_design/REPEATED_METRIC_PILOT_REPORT.md | 기존12데이터/36학습 결과 보존. 새8구조 결과는 PILOT-DIVERSE로 분리하며 과거 수치와 혼합하지 않음 |
| PILOT-DIVERSE | 8개 선언 구조의 실제 학습·정책·구조외 예측 | VERIFIED | docs/research_design/DIVERSE_STRUCTURE_PILOT_REPORT.md; research_runs/independent_confirmation/REPLAY_COMPARISON.json | 기존144회 전체 재실행의672기록 핵심 차이0 확인. 과거8구조 산출물은 보존하고 새12구조 확인은 PILOT-CONFIRM으로 분리 |
| PILOT-CONFIRM | 12개 규칙 생성 구조의 독립 확인·방법론 대조 | PARTIAL | docs/research_design/INDEPENDENT_CONFIRMATION_REPORT.md; research_runs/independent_confirmation/analysis_v1/SUMMARY.json | 과거12구조 독립 확인 기록 보존. C01~C12는 이후 모형 개발에 사용됐으므로 새 확인용으로 재사용하지 않음 |
| PATH-MODEL | 과제 특징 예측모형의 개발 안정성 | PARTIAL | docs/research_design/DECISION_RELIABILITY_NEXT_REPORT.md | 고정9후보 중첩 검증은 기본19/경로1 선택. 품질 특징 추가가 이득 아님. 단순 기본모형을 개발 기준선으로 유지하고 MAE 탐색 확장 중단 |
| PATH-PRECISION | 추가 예측력 독립 확인 정밀도·예산 | BLOCKED | research_runs/decision_reliability_next/run_v1/D_precision.json | 이번 저차원 모형 정밀도 거친 추정132구조/1188학습으로30/288 초과. 과거150추정 보존; 작은 정보와 실제 의사결정 이득을 분리한 후속 계약 |
| PATH-CONFIRM | 경로 지표 추가 정보의 새 독립 확인 | NOT_RUN | docs/research_design/PATH_METRIC_INCREMENTAL_VALIDATION_REPORT.md | 정밀도 통과 후에만 새 구조·계수·seed·M0~M6·실패 정책을 고정하고 실제 학습/do 실행 |
| ERROR-DIAG | 합성 개발 자료 오류–응답–선택 대조 | VERIFIED | docs/research_design/DECISION_RELIABILITY_NEXT_REPORT.md | 324실제 오류쌍/162핵심–주변/114경로유지와 반례·동률 보존. 6개 oracle 적합을 발견 graph와 분리 |
| ERROR-CONFIRM | 오류 위치의 조건부 의사결정 영향 독립 계약 | PROPOSED | docs/research_design/DECISION_RELIABILITY_NEXT_REPORT.md | 지표 우세를 목표로 하지 않는 새 오류쌍·효과/오프셋·후보 경계 계약과 예산을 먼저 고정. 기존20구조를 독립 확인으로 재사용하지 않음 |
| MFG-VALIDITY | 제조 연구 타당성·저장 증거 감사 | VERIFIED | docs/research_design/MANUFACTURING_VALIDITY_GATE_REVIEW.md | 검산 완료 범위만 유지:39해시/7점수/84과제/21baseline·시간증거. 제조GO가 아니라 과학적 차단/guard한계를 확인한 감사 |
| ENV-CONTRACT | 구조 점수–개입 결과 metadata 차단 계약 구현 | VERIFIED | src/environment_contract.py; tests/test_environment_contract.py; research_runs/tep_environment_bridge/CONTRACT_RESULTS.json | 15개 계약 사례·실제 파일 해시 검사 완료. 새 join은 environment_contract.require_environment_contract 사용. 과학적 동등성 승인은 아님 |
| TEP-BRIDGE | Python TEP 관측·명령·상태 연결 검산 | PARTIAL | research_runs/tep_environment_bridge/technical_v1/SUMMARY.json; research_runs/tep_environment_bridge/closure_v1/RESULT.json | 실제cache4step 추가로 좁은전이식 확인. 센서 직접/음성참조 미확정으로 L3/L4 BLOCKED; 연구설계 선택을 우선 |
| VALVE-TRANSITION | 좁은 수동 밸브 시간전이 계약 검산 | VERIFIED | research_runs/tep_valve_transition/run_v1/TRANSITIONS.json; research_runs/tep_valve_transition/RECHECKS.json | L1 정상 cache 전이만 검증 완료. 같은기술반복 종료; DYNAMIC-SCOPE에서 내부상태·시간전개 연구설계 검토 여부 결정 |
| DYNAMIC-SCOPE | 내부 상태·시간전개 연구 설계안 선택 | PROPOSED | docs/research_design/TEP_DYNAMIC_REFERENCE_DECISION.md; research_runs/tep_valve_transition/SCOPE_PROPOSAL.json | 우선권고B: 기존31정적센서와별도 namespace의 제한 내부동적 연구설계 검토 여부를 사용자결정. 새GT/본실험 채택은포함안함 |

실행 코드 회수, frozen 산출물 검사, 인과발견 재실행, 관측 적합, 독립 개입 검증을 서로 다른 완료 단계로 취급한다.
이 표의 일관성 검사가 연구 결과의 진실성을 보증하지는 않는다.

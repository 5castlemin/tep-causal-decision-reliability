# 프로젝트 현재 상태

기준일: 2026-10-23. 현재 상태는 이 표와 `docs/research_state.json`에만 정의한다.
과거 문서는 `docs/history/`, 시간순 기록은 `WORK_LOG.md`에 보존한다. 외부 PR의 증거는 병합 여부를 명시한다.

| ID | 연구 흐름 | 상태 | 근거 | 다음 행동 |
|---|---|---|---|---|
| SRC-01 | Final 생성 코드 회수 | BLOCKED | docs/reproducibility/GRAPH_REPRODUCIBILITY.json | FREEZE.code의 algos/run_*.py 및 common/config.py·data_io.py 원본을 해시로 대조하여 회수 |
| SIM-03 | 공개 후보 수치·shutdown 검증 | PARTIAL | [PR #2 commit e5a0291・미병합](https://github.com/5castlemin/tep-causal-decision-reliability/pull/2) | 1788초 종료 원인과 적분 step/Fortran 기준 동등성 조사 |
| SIM-04 | 공개 후보 초기화 검증 | BLOCKED | [PR #2 commit e5a0291・미병합](https://github.com/5castlemin/tep-causal-decision-reliability/pull/2) | 동일 객체 reset 후 관측 불일치의 RNG/state/controller 원인 확인 |
| COMPAT-01 | 공개 후보와 기존 데이터/GT 대응 | PARTIAL | [PR #2 commit e5a0291・미병합](https://github.com/5castlemin/tep-causal-decision-reliability/pull/2) | 모델 revision·controller·운전모드·단위·전처리 계보 대조 |
| SIM-01 | 기존 8월 시뮬레이터 복구 | BLOCKED | docs/SIMULATOR_SETUP.md | 당시 저장소 URL/ZIP·버전·실행 명령·로그의 구체 소재 확보 |
| SIM-02 | 공개 Python 후보 관측·쓰기·Fault smoke | PARTIAL | [PR #2 commit e5a0291・미병합](https://github.com/5castlemin/tep-causal-decision-reliability/pull/2) | PR #2 검토 및 수치·reset 제한 해결 후 장기 운전 확인 |
| TASK-01 | 실행 가능한 복구 과제 확정 | BLOCKED | experiments/pilot/TASK_SPEC.md | 모델 호환 후 Fault/Action/Target·복구·안전 기준 사전 확정 |
| EFFECT-01 | 독립 개입·Recovery/Safety 측정 | NOT_RUN | experiments/pilot/PILOT_RESULT.md | 확정 과제로 no-action 대비 동일 조건 실험 |
| DATA-01 | 원자료 취득·권리 | PARTIAL | docs/reproducibility/TEAM_GUIDE.md | 고정 커밋 취득은 검증됨; 재배포 권리 추가 확인 |
| GRAPH-01 | Final 7개 산출물·평가 보존 | VERIFIED | docs/reproducibility/GRAPH_REPRODUCIBILITY.json | 동결 파일 수정 없이 생성 코드 회수와 분리 유지 |
| SCM-01 | 정상 관측 수치 적합 | PARTIAL | experiments/pilot/logs/normal_fit_summary.json | 관측 적합을 독립 효과 검증과 구분 |
| PCMCI-ID | PCMCI+ 순환 식별 | BLOCKED | docs/audit/pre_fitting_final_freeze.json | 동시점 순환의 인과계수 식별 근거 검토 |
| TASK-STRUCT | 12개 구조 평가 후보 | VERIFIED | docs/tasks/structural_task_candidates_v1_1.json | 독립 표본/실제 복구 과제와 구분 유지 |
| DOC-01 | 현재 상태 동기화 | VERIFIED | scripts/check_research_state.py | state JSON 수정 후 문서 생성·일치 검사 |

실행 코드 회수, frozen 산출물 검사, 인과발견 재실행, 관측 적합, 독립 개입 검증을 서로 다른 완료 단계로 취급한다.
이 표의 일관성 검사가 연구 결과의 진실성을 보증하지는 않는다.

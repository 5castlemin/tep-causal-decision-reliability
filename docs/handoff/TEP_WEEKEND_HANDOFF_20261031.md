# TEP 연구 인계 — 2026-10-31

목표는 인과그래프 구조 지표와 실제 개입 의사결정 성능의 관계를 검증하는 것이다. Manca 정상자료 3회, 기존 1499×31 자료, 28간선, 7개 동결 그래프와 공식 모델을 확보했다. 225 구조 설정·10초 저장에서 초기 약6분은 가깝지만 이후 차이가 남아 동일환경은 미검증이다. 단일 개입의 −0.038°C는 평균 인과효과가 아니다.

공유 코드·결과: `research_runs/tep_dynamics_alignment/`, `research_runs/tep_intervention_probe/`, `research_runs/tep_final_handoff/` 및 관련 연구 보고서. 원본 ZIP과 원시 trajectory는 Git에 없고 기존 사용자 PC의 `data/local/tep_original_data_recovery/`, `data/local/tep_official_validation/run_v1/`, `data/local/tep_dynamics_alignment/run_v1/`, `data/local/tep_intervention_probe/run_v1/`에만 있다. 팀원은 IEEE DataPort의 원본을 정당하게 확보하여 `research_runs/tep_original_data_recovery/RAW_MANIFEST.json`의 해시와 대조해야 한다. 공식 Ricker 모델과 MATLAB/Simulink, C 컴파일러 및 라이선스가 필요하다. `research_runs/tep_dynamics_alignment/prepare_workspace.py`, `run_alignment.m`, `research_runs/tep_intervention_probe/run_probe.m` 및 기존 감시 준비 코드를 확인한다. 공식 모델 원본·바이너리·대형 자료를 Git에 올리지 않는다.

황주희: `research_runs/tep_data_provenance_team/`와 `docs/research_design/TEP_DATA_PROVENANCE_TEAM_REVIEW.md` 소유. 원본→1499행 가공,31변수의 단위·시간·관측/조작 대응,28간선의 양성·비간선·미확정 관계를 근거별 정리한다. 제출물은 해시·변수표·가공 재현 또는 미확인 근거·채점 범위다.

정창민: `research_runs/tep_causal_evaluation_team/`와 `docs/research_design/TEP_CAUSAL_EVALUATION_TEAM_DESIGN.md` 소유. 기존 그래프의 방향·시차·숨은 상태·제어기 및 효과 식별을 점검하고 공통 조작·기준·손실·실패 처리·독립 평가를 설계한다. 제출물은 모델별 가능/차단 표, 평가 계약과 검증 결과다. 원본 및 동결자료를 수정하지 않는다.

공통 Git 기준은 이 인계 PR의 HEAD 커밋이며 정확한 해시는 PR과 최종 보고에서 확인한다. `git fetch origin` 후 각각 `git switch -c feature/tep-provenance-team origin/feature/tep-final-alignment-handoff`, `git switch -c feature/tep-evaluation-team origin/feature/tep-final-alignment-handoff`를 실행하고 `git rev-parse HEAD`를 인계 HEAD와 비교한다. 각 PR base는 `feature/tep-final-alignment-handoff`다. 공통 상태 문서는 양쪽이 동시에 수정하지 않고 소유 영역에 결과를 제출한다. 기존 PR31~34와 main을 자동 병합하지 않는다.

경로 A: 기존 자료·그래프를 활용하되 데이터 가공, 동일환경 및 개입 식별 근거가 필요하다. 경로 B: 공식 모델에서 관측·개입을 새로 생성하되 새 그래프와 정당한 구조 참조가 필요하다. 두 결과를 합치려면 변수·시간·정책·참조 구조 의미 및 독립 평가가 일치해야 한다. 사용자 개인에게 후속 시뮬레이터 작업을 배정하지 않는다.

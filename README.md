# DAT 제조공정 — 제한된 예산에서 인과그래프의 어떤 오류를 고칠 것인가?

**현재 핵심 질문:** 주어진 구조 수정 예산 안에서 어떤 인과그래프 오류를 먼저 고쳐야 downstream 의사결정 손실(Decision Regret)이 줄어드는가? 이 저장소는 초기 TEP 정상 관측자료의 인과발견·구조 일치도 평가에서 출발했지만, 관측 예측과 실제 개입효과는 다르고 TEP 환경 정합성도 검증되지 않아, 정답 구조와 손실을 통제할 수 있는 합성 SCM 연구로 발전했다.

## 현재 연구 상태

현재 연구 브랜치의 Research C Held-out V1 상태는 **`HELDOUT_COMPLETED_AND_AUDITED`**다. 합성 SCM 200개를 평가했고, B=2에서 Full Greedy 대 S0의 평균 paired Decision Regret delta는 +0.07484 (95% paired-t CI `[0.05090, 0.09877]`)였다. 상세 결과와 제한은 [Held-out 결과 및 감사](RESEARCH_C_HELDOUT_V1_RESULTS.md)에 있다.

이는 승인된 합성 모집단에서의 결과다. 실제 제조공정 효과, TEP 개입 성능, 안전성 또는 보편적 정책 우월성을 검증한 것은 아니다. M4는 Development 결과를 본 뒤 지정한 Secondary이며 P1 Primary가 아니다.

> **브랜치 상태:** 이 설명과 Research C 산출물은 2026-11-23 현재 문서 작업 브랜치에서 확인한 내용이며 아직 `main`에 병합되지 않았다. main의 이력·상태와 혼동하지 않는다.

## 처음 읽는 순서

1. [전체 연구 계보와 팀 인수인계](RESEARCH_JOURNEY_AND_TEAM_HANDOFF.md)
2. [Research C 승인 계약](RESEARCH_C_APPROVAL_DECISION_BRIEF.md) 및 [실험 계약 V1](RESEARCH_C_EXPERIMENT_CONTRACT_V1.md)
3. [Held-out 분석 잠금](RESEARCH_C_HELDOUT_ANALYSIS_LOCK.md)과 [최종 결과](RESEARCH_C_HELDOUT_V1_RESULTS.md)
4. [Development 감사](RESEARCH_C_DEVELOPMENT_V1_AUDIT.md) 및 [provenance 정정 기록](RESEARCH_C_DEVELOPMENT_V1_PROVENANCE_CORRECTION.md)
5. [Research C 구현 안내](research/original_objective/README.md)

## 연구 흐름과 주요 자료

- TEP 인과발견과 저장 그래프 감사: [`docs/audit/AUDIT_REPORT.md`](docs/audit/AUDIT_REPORT.md), [`docs/audit/step6_main_table.csv`](docs/audit/step6_main_table.csv), [`docs/reproducibility/GRAPH_REPRODUCIBILITY.json`](docs/reproducibility/GRAPH_REPRODUCIBILITY.json)
- 오류 위치를 본 초기 합성 분석: [`SYNTHETIC_FINAL_RESULTS_AND_CLAIMS.md`](docs/research_design/SYNTHETIC_FINAL_RESULTS_AND_CLAIMS.md)
- 별도 Step 5/6 예산 연구: [`STEP5_STEP6_FINAL_RESULTS.md`](research/budget_aware_refinement/STEP5_STEP6_FINAL_RESULTS.md), [`FINAL_RESEARCH_REPORT.md`](research/budget_aware_refinement/FINAL_RESEARCH_REPORT.md)
- Research C 정책 코드: [`policy_engine.py`](research/original_objective/policy_engine.py); 실행·분석 경로는 `research/original_objective/`, `scripts/`, `tests/`에 있다.
- TEP 환경·개입 브리지의 한계: [`TEP_ENVIRONMENT_BRIDGE_FEASIBILITY.md`](docs/research_design/TEP_ENVIRONMENT_BRIDGE_FEASIBILITY.md), [`TEP_EFFECT_DECISION_FEASIBILITY.md`](docs/research_design/TEP_EFFECT_DECISION_FEASIBILITY.md)

원시 Development/Held-out SQLite 및 감사 파일은 승인된 로컬 `C:\DAT_RESEARCH\research-c\...` 경로에 있으며 Git에 복사하지 않았다. 다른 팀원의 해당 경로 접근 권한은 별도 확인이 필요하다. 자료 위치·권리·재현 절차는 [`data/README.md`](data/README.md)와 [`TEAM_GUIDE.md`](docs/reproducibility/TEAM_GUIDE.md)를 따른다.

## 팀 업무

- **오성민:** 연구 총괄, A/B/C 및 초기 연구 결과 통합, 최종 보고·발표, PR/병합 결정.
- **정창민:** M1–M4 정의와 실제 수정 이력·비용·행동·Regret의 메커니즘 분석. 상세 절차와 산출물은 [인수인계 문서 Part 6](RESEARCH_JOURNEY_AND_TEAM_HANDOFF.md#part-6-팀원-역할과-실행-가능한-업무).
- **황주희:** 이번 주 발표 준비 우선, 필수 연구 과업 없음. 발표 이후 선택적 가독성·예상 질문 검토.

## 재현 및 협업

현재 운영 상태는 [`docs/research_state_current.json`](docs/research_state_current.json)을 원본으로 하며, [`docs/research_state.json`](docs/research_state.json)은 Step 4 동결 당시 스냅샷으로 보존한다. `PROJECT_STATUS.md`, `PRIORITIES.md`는 생성 대시보드다. 기여·브랜치·검토 지침은 [`CONTRIBUTING.md`](CONTRIBUTING.md)와 [`AGENTS.md`](AGENTS.md)를 읽는다. 새 연구 실행은 승인된 Configuration/Manifest와 별도 실행 승인 없이는 시작하지 않는다. 기존 결과·동결 파일은 읽기 전용으로 보존한다.

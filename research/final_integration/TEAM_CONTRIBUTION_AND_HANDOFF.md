# 팀 기여 및 최종 인수인계

## 확인된 기여

- **오성민:** 기존 연구 설계·실험·통합 및 Research D 수행. 최종 통합 보고와 발표 준비를 조율한다.
- **정창민:** Research C M1–M4 메커니즘 분석 및 PR #40 산출물 작성. 최초 분석은 재생성 ledger 기반 사후 분석으로 시작했으며, 이번 통합 감사에서 원본 Ledger를 별도 검증했다. 기존 커밋/작성자 이력은 보존한다.
- **황주희:** 기존 기록에서 확인되는 것은 발표 준비 우선순위와 필수 연구 과업이 없다는 점이다. 구체적인 과거 연구 기여는 현재 자료로 확인되지 않아 추가로 귀속하지 않는다. 향후 선택 업무는 보고서 가독성 검토와 발표 예상 질문 검토다.

## 남은 발표 준비

1. 팀이 최종 보고서의 표현과 발표 분량을 검토한다.
2. 발표자가 결과표의 분석 단위와 제한을 설명할 수 있도록 연습한다.
3. `FINAL_PRESENTATION_EVIDENCE_GUIDE.md`의 예상 질문을 바탕으로 Q&A를 준비한다.
4. 실제 제조 효과, 보편적 M4 우월성, 독립 외부 SCM 모집단이라는 표현은 사용하지 않는다.

## 데이터 및 재현성 인계

Research C 원본 SQLite와 Research D evaluator response vectors는 공개 저장소에 포함하지 않는다. C SQLite digest는 최종 E 감사에서 원 manifest와 재대조했다. D의 직전 27-check audit summary는 별도 로컬 경로에 있었으나 raw response/recommendation/training artifacts는 이번 감사의 지정 경로에서 찾지 못했다. 공개 문서에는 hash와 집계만 남기며 공개 브랜치만으로 원자료 전체를 재실행할 수 있다고 주장하지 않는다.

현재 상태는 `docs/research_state_current.json`과 `docs/current/`에서 확인한다. 과거 frozen state는 수정하지 않는다. Research E는 기존 C 표본으로 수행한 post-hoc 예산·비용·Adaptive M4·target sensitivity 확장이다. Research D unit-level 재확인은 접근 자료 한계로 추가하지 않았다. 새 연구 실험은 종료되었으며 남은 업무는 최종 보고 검토·발표·제출뿐이다. Research F/G/H는 후속 아이디어이며 이번 프로젝트에서 설계·실행하지 않는다.

## Research F-Lite closeout handoff

F-Lite final audit reaggregated saved artifacts only. The audit script deliberately does not call the historical `restore_cohort()` helper because that helper regenerates SCM parameters and observations. The corrected Random rates, common-index bootstrap and pending replay are summarized in `research/decision_oriented_verification/RESEARCH_F_FINAL_AUDIT.md`. Presentation preparation should retain the post-hoc grade, explain that query counts differ from edit counts, and avoid describing the simulated expert as a real participant or the in-process interface as secure isolation. Draft paper structure and defense questions are in `FINAL_PAPER_OUTLINE.md` and `FINAL_DEFENSE_QA.md`.

# 연구 계보: 원본 근거와 후속 해설

기준 2026-11-10. 이 문서는 원래 실험 결과가 아니라 색인과 해설이다. 자세한 수치와 실패는 해당 커밋과 연구 문서를 우선한다.

1. **구조 평가**: TEP 관측자료, 7개 발견 그래프와 28개 참조 간선으로 구조 점수와 의사결정의 관계를 탐색했다. 전체 참조가 물리적 완전 정답인지와 관측·개입 생성환경의 정합성은 미확인이다. 원본: [연구 설계](RESEARCH_DESIGN.md), `docs/research_design/TEP_ENVIRONMENT_BRIDGE_FEASIBILITY.md`.
2. **오류 위치와 의사결정**: 합성 환경에서 같은 전체 구조 점수여도 오류 위치와 과제에 따라 손실이 달라질 수 있는 사례·반례를 검토했다. 이는 지표의 일반적 우월성 증명이 아니다. 원본: `docs/research_design/SYNTHETIC_FINAL_RESULTS_AND_CLAIMS.md`, `docs/research_design/DECISION_RELIABILITY_NEXT_REPORT.md`, `docs/research_design/ERROR_LOCATION_INDEPENDENT_CONFIRMATION_PROTOCOL.md`.
3. **지표 조합에 예산 배분하는 중간 설계**: 4개 구조 지표의 15개 조합은 사전 설계로 제안되었으며 실험 실패 결과가 아니다. 이후 수정 연산·중복을 명확히 하기 위해 전환했다. 원본은 최신 연구 브랜치의 `research/budget_aware_refinement/ARCHIVED_METRIC_COMBINATION_DESIGN.md`.
4. **비용 제약·의사결정 중심 수정**: FN/FP/REV 7개 조합과 Global/Task-Focused 2조건을 사용하는 14개 명목 정책 및 Decision Regret. Step0–3 DONE, Step4 IN_PROGRESS, Step5–7 미실행, Step8 BLOCKED. 최신 근거: PR #36 HEAD `ba35db68c573fd35a21edb42b1bbde354bedf0d8`, `research/budget_aware_refinement/RESEARCH_PROTOCOL.md`, `STEP4_READINESS_AUDIT.md`. 연구 가설 검증 완료 아님.

TEP 공식 실행과 제한 개입은 #27–35에 연결되어 있지만 기존 관측자료와 동일환경을 증명하지 못했다. CausalMan #26은 조건부 재설계이며 GT·개입·식별 문제가 남는다. 두 결과를 정답 효과로 승격하지 않는다.

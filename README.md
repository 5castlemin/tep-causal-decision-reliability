# Cost-Constrained, Decision-Aware Causal Graph Refinement

## Current Research

제한된 구조 수정 예산에서 **누락 간선(FN), 잘못 추가된 간선(FP), 반대 방향(REV)**의 Task-Focused 수정 순서가 ID-ordered Global 기준선과 비교해 의사결정 손실에 어떤 차이를 만드는지 연구한다. 현행 계약은 [동결 프로토콜](research/budget_aware_refinement/STEP4_FROZEN_PROTOCOL.md)과 [활성 계약](research/budget_aware_refinement/STEP4_CURRENT_ACTIVE_CONTRACT.md)이다. 이전 제안은 연구 이력으로 보존한다.

## Research Motivation

합성환경에서는 같은 전체 구조 점수에서도 오류 위치에 따라 추천과 손실이 달라질 수 있었다. 이것은 특정 지표의 일반적 우월성을 증명하지 않는다. 연구는 점수의 상관관계에서 한 걸음 나아가, 제한된 자원으로 무엇을 수정할 때 의사결정이 개선되는지 평가한다.

## Research Evolution

TEP 구조 평가 → 합성환경의 오류 위치와 의사결정 분석 → 네 지표 조합의 예산 설계 → 현재의 오류 유형과 과제 우선순위 연구로 발전했다. 당시의 근거와 한계는 [연구 계보](RESEARCH_EVOLUTION.md), [기존 README](docs/history/README_PRE_REORGANIZATION_2026-11-10.md), [보관 인덱스](https://github.com/5castlemin/tep-causal-decision-reliability/blob/attic/legacy-research-2026-11-10/ARCHIVE_INDEX.md)를 참조한다.

## Methodology

동결된 주 계약은 P에서 strict Q-common 구조 적격성을 만족한 간접 전용 과제, B=1/gamma=1, Task-Focused 대 ID-ordered Global, FN/FP/REV 동일 가중치다. 공통 관측자료로 학습한 모델이 조작을 추천하고, 별도 analytic GT evaluator가 평가한다. 주 결과는 SCM 수준 대응 평균 차이이며, Option B에 따라 기술적 추정과 민감도 보고만 허용하고 확인적 우월성·동등성 주장은 보류한다. 이 계약은 실제 제조공정 개입 효과 검증이나 배포 가능성을 입증하지 않는다.

## Current Progress

Step 0–3 DONE. Step 4는 프로토콜·실행 계약으로 FROZEN됐지만 연구 완료를 뜻하지 않는다. Step 5 개발 코호트와 Step 6 독립 재현은 NOT RUN이며, 개발 코호트 실행에는 PR #38의 별도 통합 및 실행 결정이 필요하다. [연구 상태](research/budget_aware_refinement/RESEARCH_STATUS.md), [동결 프로토콜](research/budget_aware_refinement/STEP4_FROZEN_PROTOCOL.md), [Step 5 사전 실행 Runbook](research/budget_aware_refinement/STEP5_DEVELOPMENT_RUNBOOK.md), [로드맵](research/budget_aware_refinement/ROADMAP.md).

## Reproducibility

Python 3.11 및 `requirements.txt`를 사용한다. 자료 접근과 추가 의존성은 [팀 재현 가이드](docs/reproducibility/TEAM_GUIDE.md)를 따른다. 아래는 저장된 자산과 코드를 확인하는 명령이며 본 연구 실험을 실행하지 않는다.

```powershell
python -X utf8 graphs/final/verify_and_load.py
python -X utf8 scripts/check_research_state.py
python -X utf8 -m unittest discover -s tests -v
```

## Legacy Research and Archived Experiments

기존 TEP 1,499행과 28개 참조 간선, 7개 동결 그래프는 변경하지 않는다. 기존 [합성 결과와 주장](docs/research_design/SYNTHETIC_FINAL_RESULTS_AND_CLAIMS.md), [오류 위치 연구](docs/research_design/DECISION_RELIABILITY_NEXT_REPORT.md), [제조 벤치마크 검토](docs/research_design/INTEGRATED_MANUFACTURING_BENCHMARK_REVIEW.md)를 보존한다. TEP 관련 미병합 작업과 CausalMan 계약은 [보관 manifest](https://github.com/5castlemin/tep-causal-decision-reliability/blob/attic/legacy-research-2026-11-10/LEGACY_BRANCH_MANIFEST.json)와 태그에서 별도 추적한다.

## Limitations

정상 운전의 유사성은 TEP 관측·개입환경 동등성이나 28개 간선의 완전성을 입증하지 않는다. CausalMan의 GT·개입·효과 식별 문제는 미해결이다. 새 연구의 확인 실험과 가설 검증도 미실행이다. main으로의 개발 통합과 연구 완료는 별개의 판정이다. 협업과 기록은 [기여 안내](CONTRIBUTING.md), [상태](PROJECT_STATUS.md), [우선순위](PRIORITIES.md), [작업 기록](WORK_LOG.md)을 따른다.

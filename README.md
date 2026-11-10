# Cost-Constrained, Decision-Aware Causal Graph Refinement

## Current Research

제한된 구조 수정 예산에서 **누락 간선(FN), 잘못 추가된 간선(FP), 반대 방향(REV)**과 조작 과제와의 관련성을 고려한 우선순위가 의사결정 손실을 얼마나 줄이는지 연구한다. 비용 구조와 인과환경에 따라 결과가 달라질 수 있다. 주 계약은 [연구 프로토콜](research/budget_aware_refinement/RESEARCH_PROTOCOL.md)이다.

## Research Motivation

합성환경에서는 같은 전체 구조 점수에서도 오류 위치에 따라 추천과 손실이 달라질 수 있었다. 이것은 특정 지표의 일반적 우월성을 증명하지 않는다. 연구는 점수의 상관관계에서 한 걸음 나아가, 제한된 자원으로 무엇을 수정할 때 의사결정이 개선되는지 평가한다.

## Research Evolution

TEP 구조 평가 → 합성환경의 오류 위치와 의사결정 분석 → 네 지표 조합의 예산 설계 → 현재의 오류 유형과 과제 우선순위 연구로 발전했다. 당시의 근거와 한계는 [연구 계보](RESEARCH_EVOLUTION.md), [기존 README](docs/history/README_PRE_REORGANIZATION_2026-11-10.md), [보관 인덱스](https://github.com/5castlemin/tep-causal-decision-reliability/blob/attic/legacy-research-2026-11-10/ARCHIVE_INDEX.md)를 참조한다.

## Methodology

세 오류 유형의 일곱 비공집합 각각을 전체 위치 우선(Global)과 과제 관련 위치 우선(Task-Focused)으로 나누어 14개 명목 정책을 비교한다. 정답 그래프를 아는 합성환경의 oracle 수정으로, 실제 배포 가능성을 자동으로 뜻하지 않는다. 공통 관측자료로 학습한 모델이 조작을 선택한 뒤 정답 SCM이 사후 평가한다. **Decision Regret**은 선택 조작의 정답 손실과 사전 지정 후보 중 최선의 손실 차이다. 실제 조작 비용과 그래프 수정 예산은 구분한다.

## Current Progress

Step 0–3 DONE, Step 4 사전등록 IN_PROGRESS, Step 5–7 NOT_STARTED, Step 8 외부 검증 BLOCKED, Step 9 NOT_STARTED. Step 4의 표본·실패 처리·생성 조건은 동결되지 않았다. 개발 파일럿은 확인 실험이 아니다. [연구 상태](research/budget_aware_refinement/RESEARCH_STATUS.md), [로드맵](research/budget_aware_refinement/ROADMAP.md), [Step 4 준비도](research/budget_aware_refinement/STEP4_READINESS_AUDIT.md).

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

# 예산 제약 인과그래프 개선 연구 — 제안

이 브랜치는 기존 연구를 보존하면서 최종 연구 설계 후보를 구현하는 공간이다. 정식 연구 질문 변경이나 결과 확정을 뜻하지 않는다.

**질문:** 한정된 그래프 수정 비용에서 어떤 구조적 특성의 개선이 의사결정 후회를 가장 효율적으로 줄이는가?

RQ1 동일 예산에서 수정 정책 비교; RQ2 예산에 따른 정책 변화; RQ3 실제 발견 그래프에서의 유지; RQ4 비선형과 제조환경에서의 유지. 우월한 정책은 미확정이다.

Phase 1 합성 SCM·지표 계약; Phase 2 15개 지표 조합과 무수정; Phase 3 동일 예산 후회 평가; Phase 4 실제 PC-stable/BOSS/DirectLiNGAM 그래프; Phase 5 비선형 강건성 및 조건부 외부 검증. 프로토콜 승인·등록 후 단계별 실행한다. 결과·실패·부정 결과 및 독립 재현 기록을 산출한다. main 병합은 MERGE_CHECKLIST의 연구·검증·리뷰 요건을 충족하고 별도 승인될 때만 가능하다.

기준 main `cdb2c7d6dc499937929ca496ca840b07fb500701`은 PR #25까지 포함한다. PR #26(별도 CausalMan 계약)과 #27~35(TEP 연속 브랜치)는 미병합이며 이 브랜치에 반입하지 않았다. 해당 결과를 문서상 선행 증거로 참조할 때 PR과 HEAD를 명시한다.

기존 근거: `docs/research_design/SYNTHETIC_FINAL_RESULTS_AND_CLAIMS.md`는 동점 구조에서 손실 차이와 반례를 함께 보고한다. 독립 확인 M1–M2 지지와 추가 설명력 불확실성은 다르다. C01~C12는 이후 개발에 재사용되어 새로운 독립 확인 표본이 아니다. 오류 위치 확인 예산은 `ERROR_LOCATION_INDEPENDENT_CONFIRMATION_PROTOCOL.md`에서 REDESIGN_REQUIRED다.

재사용: `src/integrated_pilot.py`의 실제 발견 학습·출력 표현·Ridge 적합, `src/diverse_structure_pilot.py`의 생성·경로·이론응답, `src/decision_reliability_next.py`와 `src/independent_confirmation.py`의 통제오류·구조 단위 분석, `src/environment_contract.py`의 환경 격리. 새 구현 필요: 지표 통일 계약, 15개 수정 정책/비용 장부, 다예산 실험 및 비선형 생성·추정. 이 문서는 구현 완료가 아니다. 기존 `graphs/final/`, 데이터, `research_runs/`, 구조평가 및 `RESEARCH_DESIGN.md`를 변경하지 않는다.

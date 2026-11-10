# 공식 단계와 완료 조건

마지막 문서 검토: 2026-11-10. 상태 값은 NOT_STARTED / IN_PROGRESS / BLOCKED / DONE / SKIPPED_WITH_REASON(선택 외부만). [x] 및 취소선은 증거가 있는 완료에만 사용.

- [x] ~~Step 0: 연구 질문·정보 경계·비용·후회·문헌 검토와 정적 계약 검증~~ — DONE; RESEARCH_PROTOCOL.md, LITERATURE_NOVELTY_MATRIX.md, check_contract.py; 2026-11-10. 실험 증거 아님.
- [x] ~~Step 1: 정책 정의·정보 경계·소형 DAG 열거/구별 가능성~~ — DONE; STEP1_POLICY_SPEC.md 및 소형 fixture 17개 검사 통과, 2026-11-10. Step2 엔진 미구현.
- [ ] Step 2: 엔진·자동 테스트 — IN_PROGRESS; STEP2_ENGINE.md와 국소 테스트, 외부 CI 확인 대기.
- [ ] Step 3: 개발 SCM 파일럿 — NOT_STARTED; 승인된 경량 실행·중복률·비용/시간 기록 후.
- [ ] Step 4: 본실험 사전등록 — NOT_STARTED; 표본수·정밀도·비용·순서·실패·분석 동결 후.
- [ ] Step 5: 합성 본실험 — NOT_STARTED; 사전등록·별도 승인, 모든 실패/반례 보존 후.
- [ ] Step 6: 독립 SCM·발견 검증 — NOT_STARTED; 정책 동결·구조 단위 독립성 및 출력 가정 검증 후.
- [ ] Step 7: 가중 비용·비선형 — NOT_STARTED; 별도 요인 설계·추정 가정 검증 후.
- [ ] Step 8: 선택적 TEP 외부 검증 — BLOCKED; 동일환경/GT/조작/식별 계약; 미충족 시 SKIPPED_WITH_REASON 가능.
- [ ] Step 9: 보고·재현·Merge — NOT_STARTED; 결과와 주장 대조, 재현, CI·리뷰·사용자 승인 후.

Step0 DONE은 계약 문서와 정적 검사 완료만 뜻하며 정책 식별성·연구 가설·실험 성공을 뜻하지 않는다.

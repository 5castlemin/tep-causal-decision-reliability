# 개발 통합과 연구 완료 기준

**Development Integration**은 검증된 진행 중 연구를 main에 통합하는 운영 결정이며 연구 완료나 가설 검증을 의미하지 않는다. 최종 HEAD의 CI, 동결 자산, 상태 및 증거 기반 Self-Review를 확인하고 운영자가 명시적으로 병합을 결정해야 한다. 플랫폼의 필수 외부 리뷰가 있으면 이를 충족해야 한다.

**Research Completion**은 아래 Step4–9의 실제 연구·재현·검토가 끝난 별도 판정이다.

- [x] ~~Step0 계약·문헌·정적 검사~~ — 문서 완료, 연구 가설 미검증.
- [x] ~~Step1 오류 후보·정보 경계·순서 의존성·정책 중복 검증~~ — 소형 DAG fixture 17개 통과; STEP1_POLICY_SPEC.md. 전체 파이프라인 누출 검증은 Step2.
- [x] ~~Step2 엔진과 비용·반전·DAG·동률·실패 테스트~~ — 관련36개 검사, 엔진 commit f1494e7 CI 통과; STEP2_ENGINE.md.
- [x] ~~Step3 승인된 개발 파일럿과 원시 시간/중복 기록~~ — STEP3_SUPPLEMENT_REPORT.md; 연구 가설 확증 아님.
- [ ] Step4 독립 SCM 수, 실질적 차이, 예산, 실패 및 분석 사전등록.
- [ ] Step5~7 실제 분석·반례·신뢰구간·독립 확인과 강건성 검증.
- [ ] Step8 외부 검증은 Gate 통과 또는 사유와 함께 SKIPPED_WITH_REASON.
- [ ] Step9 자료·코드·hash·seed 제3자 재현, 동결 자산 및 CI 검사, 주장 대조.
- [ ] Research Completion을 위한 별도 연구 검토와 판정. PR #36의 사용자 명시 개발 통합 승인은 이 항목을 완료하지 않는다.

PR #36의 개발 통합 Self-Review에는 전체 diff·연구 계약·검사·동결 자산·상태·미해결 위험과 최종 HEAD CI를 기록한다. 이번 사용자 요청은 PR #36에 한정한 명시적 병합 결정이며 후속 PR의 자동 병합 권한이 아니다.

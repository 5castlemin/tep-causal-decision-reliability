# 결정 기록

- 2026-11-05 제안: 비용 제약의 구조 개선 정책과 후회 비교를 별도 연구 후보로 구축. 기존 RESEARCH_DESIGN.md와 완료 결과를 대체하지 않는다.
- 주 제안은 참조를 사용하는 oracle이며 비oracle 정책은 후속 별도 계약. 선택 지표 외 지표의 변화도 허용·기록.
- 균등 몫과 고정 순서를 예시로 사전 제안; 예산의 자유 배분 oracle과 구분. 겹치는 수정은 한 번만 과금. 통계적/계산 예산은 미승인.
- 선형 합성 우선, 비선형 별도 요인 실험; CausalMan과 TEP는 외부 Gate가 충족될 때만. 그 실패를 핵심 합성 연구의 자동 실패로 삼지 않는다.
- 이전 ERROR-CONFIRM의 REDESIGN_REQUIRED, CausalMan acceptance 실패 및 TEP 미검증은 취소되지 않았다. 특정 정책 우월성은 미결정이다.

## 2026-11-10 Step 0 공식 전환
15개 F1 지표 조합은 ARCHIVED_METRIC_COMBINATION_DESIGN.md에 보존하고 FN/FP/REV 7조합×Global/T 14개와 세 baseline으로 전환한다. 4개 기존 지표는 진단으로 유지한다. unit 비용과 표준화 평균반응 후회, 학습 SD ddof=1 및 후보 5수준은 채택; 예산 grid는 Step4에 동결. 실제 효과로 수정 순서 선택 금지. 신규 실험·GT 생성·시뮬레이터 실행 없음.

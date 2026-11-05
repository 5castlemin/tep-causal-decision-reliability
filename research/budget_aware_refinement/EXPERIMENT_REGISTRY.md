# 실험 등록부

모든 행은 PLANNED이며 실행 승인·고정된 프로토콜이나 생성된 데이터가 아니다. 코드 및 결과는 승인 후 기존 공통 코드를 재사용하여 `research/budget_aware_refinement/experiments/<ID>/`와 `results/<ID>/`에 기록한다. 각 manifest에 SCM·구조·seed·데이터 split/hash·그래프 표현·수정 비용과 장부·모델/정책 버전·실패·원시 결과 및 재현 명령을 보존한다.

| ID | 환경·그래프 | 정책/예산 | 상태 | 증거 |
|---|---|---|---|---|
| BAR-01 | 독립 선형 SCM·통제 오류 | 16조건, B 0/1/2/4 제안 | PLANNED | RESEARCH_PROTOCOL.md |
| BAR-02 | 동일 SCM의 실제 PC/BOSS/DirectLiNGAM | 동일 oracle 계약과 사전 고정 비교 | PLANNED | src/integrated_pilot.py |
| BAR-03 | 선형/비선형 DGP × 선형/비선형 추정기 | 동일 구조·예산의 별도 강건성 | PLANNED | 정의·구현 미완료 |
| BAR-EXT | TEP 또는 CausalMan | 환경별 Gate 통과 후만 | BLOCKED | TEP 조건부; CausalMan CONDITIONAL_NOT_ACCEPTED / PR26 CONDITIONAL_REDESIGN |

반복 do 행은 독립 SCM이 아니다. 신규 확인에 S1~S8/C01~C12를 재사용하지 않는다.

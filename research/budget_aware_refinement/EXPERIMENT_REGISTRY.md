# 실험 등록부

아래는 설계이며 데이터·실험 결과는 없다. 실행 단위의 DAG/SCM·seed·훈련/검증·초기 오류·후보/거부/수정 장부·정책 및 비용·실패·원시 do·코드/데이터 hash를 별도 기록한다. 예산은 Step4 전 고정하지 않는다.

| ID | 조건 | 상태 | 선행 조건 |
|---|---|---|---|
| BAR-01 | 개발 SCM 및 14개 오류유형×위치 정책과 세 baseline | PLANNED | Step1~2 및 별도 파일럿 승인 |
| BAR-02 | gamma1, B4 독립 SCM 확인 | PLANNED | 개발 선택 동결·Step4 등록 |
| BAR-03 | 실제 PC/BOSS/DirectLiNGAM 출력 | PLANNED | 추정 대상·부분 방향 계약 |
| BAR-04 | gamma2/3 및 비선형 | PLANNED | 요인 설계·계산 예산 |
| BAR-EXT | TEP, CausalMan | BLOCKED | 환경·GT·개입·식별 Gate |

통계적 독립 단위는 SCM이다. S1~S8/C01~C12를 새 확인 SCM으로 쓰지 않는다. 확정 정책 순서를 평가 결과로 바꾸지 않는다.

Step2 구현·모의 테스트는 실험 실행이 아니다. BAR-01~04/EXT 상태는 변하지 않는다. STEP2_ENGINE.md 참조.

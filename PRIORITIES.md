# 연구 우선순위

확인일: 2026-10-23. 담당자와 기한은 합의 전이므로 지정하지 않는다. 상태는 증거 기준이다.

| ID | 우선순위 | 현재 상태 | 선행 조건 | 다음 구체 행동 | 완료 증거 |
|---|---|---|---|---|---|
| SIM-01 | P0 | BLOCKED | 8월 실행 소스 소재 확인 | 당시 테스트의 소스 저장소/압축본, 버전, 설치 명령, 원시 로그와 제어기 설정을 회수 | 동일 환경에서 정상 운전 2회 재현 로그와 해시 |
| SIM-02 | P0 | BLOCKED | SIM-01 | Fault 주입, XMV 직접 쓰기/설정값 우선순위, XMEAS 기록 인터페이스 확인 | 실제 명령·변수·단위·반응 로그 |
| TASK-01 | P0 | BLOCKED | SIM-02 | 구조 평가 후보와 구분하여 실행 가능한 복구 과제 1개 및 정상·안전 기준 사전 확정 | 결과 열람 전 버전된 과제 계약 |
| EFFECT-01 | P0 | NOT_RUN | TASK-01 | no-action 대비 동일 초기조건 개입 효과의 독립 시뮬레이터 측정 | 원시 trajectory·반복 실행·Recovery/Safety 계산 규칙 |
| SRC-01 | P1 | PARTIAL | 원본 코드 파일·권리 확인 | Slack의 PCMCI+, PC/BOSS, DirectLiNGAM/DAGMA 실행 코드 회수 후 기존 그래프와 대조 | 실행 파일 SHA-256·라이선스·명령·환경·재현 결과 |
| DATA-01 | P1 | PARTIAL | 배포 권리 확인 | CPCaD-Bench 데이터 재배포 허가/라이선스 조사; 그 전에는 고정 커밋 취득 | 권리 근거와 데이터/GT 해시·shape 확인 |
| DOC-01 | P2 | VERIFIED | 없음 | 모든 실질 연구 변경 PR에서 상태·우선순위·작업 기록 동시 갱신 | CI 문서 동기화 검사 통과 |

새 알고리즘·비선형 탐색은 독립 개입 환경 복구보다 뒤에 둔다.

## 2026-10-23 feasibility 후 다음 행동

- P0 SIM-03 (PARTIAL): 공개 Python 후보의 큰 수동 반응/1788초 shutdown에 대해 적분 step·Fortran 기준 수치 동등성과 종료 원인을 확인. 수치 정확성 확인 전 실제 효과 정답 사용 금지.
- P0 SIM-04 (BLOCKED): 동일 객체 reset 후 초기 관측 불일치 원인 조사. 새 인스턴스 재현은 통과했으나 RNG·controller·state 초기화 계약 확인 필요.
- P0 COMPAT-01 (PARTIAL): CPCaD/Manca 모델 revision·운전모드·controller·전처리와 후보 대응 확인. 이름 mapping만으로 동일 구현 판단 금지.
- 기존 SIM-01은 여전히 8월 소스 회수 BLOCKED. 새 후보의 정상 운전/쓰기/Fault smoke는 일부 통과했으므로 SIM-02의 공개 후보 실행 근거는 이번 보고서에 추가한다. TASK-01과 EFFECT-01은 아직 보류한다.
- DOC-02 (VERIFIED): simulator raw CSV의 Git 줄바꿈 정규화 방지 규칙 추가. 새 환경에서 hash 검증으로 바이트 보존을 확인한다.

# Track A — benchmark 원환경 복원 Gate

기준일: 2026-10-23. 결론: **A1 BLOCKED / A2 BLOCKED / A3 NOT_RUN / A4 NO-GO**.
원래 연구 가설은 **INSUFFICIENT_EVIDENCE**이다. 자료 접근과 실행환경이 차단된 현재 상태이며, 복원이 영구적으로 불가능하다고 판정한 것은 아니다.

## 1. GitHub 기준과 보존

사용자의 병합 승인을 받아 PR #4를 `1e4fcc7c91839afd49770fcc8b3380d368e1dea3`로 병합한 뒤 PR #5를 main 대상으로 재정렬했다. 현재/과거 상태 구분을 수정한 PR #5의 `a2dc2b236b8733663c920d3ea06980c187e00728`은 Actions 39960138640에서 성공했다. 이후 PR #5를 병합했다.
기준 main은 `7b166383d4a5d86cdf73dbbec3b060b0ee0e3a24`, 작업 브랜치는 `feature/track-a-recovery-gate`이다. 이번 PR은 자동 병합하지 않는다.
기존 7개 그래프, Step 6, 시뮬레이터 원시 trajectory, 과거 결정 evidence와 RESEARCH_DESIGN.md는 보존한다. 이전 12조건 실험·Slack 전수 감사·Step 6 계산은 반복하지 않았다.

## 2. 실제 확보 자료와 출처

| 자료 | 확보 수준 | SHA-256 |
|---|---|---|
| temexd_mod.zip | 기존 원본 재해시, 변경 없음 | e43227aaded739cfeba1ec281c54ac8a549f60753e064305a669b906c4b16b0d |
| tecode.zip | 기존 원본 재해시, 변경 없음 | 2536e8a80e326c6a15ac2f636b1e2c48e1791e1b21dddc644f0725e87a8db724 |
| Technical_Report_V1_2.pdf | 이번에 실제 회수한 55쪽 기술문서, 5,990,722 bytes | 657307d7119538a0c21bdc49933c4ff31de929038a0213f9f4a8dfc3fde9faf0 |
| DataCite DOI 응답 | 실제 JSON, CC BY 4.0 권리 명세 | 55b947eb0dea326029672f31ba158da35e2c428c572a55bb612badb08b8c438b |
| 3_Normal Steady-State.zip | 목록만 확인, 61.88 MB 표시; 원본 미회수 | UNKNOWN |

모델 출처: [공식 수정 모델 archive](https://depts.washington.edu/control/LARRY/TE/download.html).
데이터·기술보고서 출처: [IEEE DataPort](https://ieee-dataport.org/open-access/tennessee-eastman-process-alarm-management-dataset), [DOI 메타데이터](https://api.datacite.org/dois/10.21227/326k-qr90).
DataCite의 데이터 권리 명세를 별도 모델 archive의 라이선스로 확장하지 않는다. 바이너리와 전체 PDF는 Git에 반입하지 않는다. 로컬 원본과 원시 접근 기록을 지정 아카이브에 보관하고 Git에는 정제된 출처·해시만 남긴다.

## 3. A1 — 원시 계보

공식 DataPort 페이지가 HTTP 200으로 열렸다. 과거 접근 실패를 영구적 비공개로 해석하지 않는다. 정상 ZIP은 목록에 있으나 다운로드는 IEEE 계정 로그인을 요구한다. 로그인·가입·권한 우회는 수행하지 않았다. 직접 다운로드 URL은 미확보다.
공개 기술문서는 오래된 임시 링크에서 403을 받았지만 공개 페이지를 갱신해 제공된 링크로 회수했다. 이는 정상 ZIP 회수가 아니다. 임시 서명 URL은 Git에 저장하지 않았다.

PDF 13쪽(인쇄 11쪽) Table 2.1은 SIMOUT.xlsx·XMV.xlsx·TOUT.xlsx·ALARMS.xlsx를 명시한다. PDF 42쪽(인쇄 40쪽) Figure 6.2는 Tests 폴더의 random_seed.txt와 1_Original/2_Filter/3_Deadband 구조를 보여준다. **정상 ZIP 내부가 동일하다는 검증은 아니다.** PDF 12·13·14·42쪽을 이미지로 확인했다.
PDF Table 1.1의 플래그 비트는 문서상 보고값이다. 합산값 225는 그 표에서 계산한 추론이며 실제 benchmark 실행 플래그를 확인한 값이 아니다. bit 4의 잡음 비활성화 값은 0이다. 무잡음 데이터라고 해석하지 않는다.

새 파일명 단서만 대상으로 Downloads·프로젝트 아카이브·기존 workspace에서 11,971개 파일명을 검사했으나 일치 원본은 없었다. 전체 디스크나 Slack을 재감사한 것은 아니다.
현재 benchmark가 선택한 정확한 정상 run, 원시 timestamp·seed 값, 모델 바이너리, controller 설정, 초기 상태, export 코드, 180초 median의 stride·경계·시작/종료 구간은 **UNKNOWN**이다. 논문의 원측정 0.1 Hz 및 3분 전처리 설명은 기존 문헌 보고이며 이번 원자료 재현 결과가 아니다. 1500/1499 차이도 UNKNOWN으로 유지한다. 행을 추가하거나 필터를 사후 조정하지 않았다.

## 4. A2 — MATLAB/Simulink 실행환경

PATH뿐 아니라 MathWorks registry 3곳, 설치 제품 목록, C/D의 일반 설치경로 20곳, Start Menu, App Paths, 실행 중 프로세스를 검사했다. 해당 범위에서 MATLAB 실행파일·설치 등록을 찾지 못했다. cl/gcc/gfortran/mex도 PATH에서 찾지 못했다. 전역 미설치 또는 라이선스 부재를 확정한 검사가 아니다. 승인된 원격 환경도 아직 제공되지 않았다.
라이선스 조회·Simulink 버전 확인·.mdl 실제 로딩·MEX 컴파일은 모두 **NOT_RUN**이다. 설치·라이선스 우회는 수행하지 않았다.

정적 코드 확인: MultiLoop_mode1.mdl은 ode45, RelTol 1e-6, AbsTol auto, StartTime 0.0, StopTime 72, LoadInitialState on, xInitial을 선언한다. Mode_1_Init.m은 Mode1xInitial을 읽고 초기 조작변수 값을 설정한다. 기존 정적 감사의 Ts_base=0.0005 h, Ts_save=0.01 h는 각각 1.8초/36초이며 benchmark 3분 export와 자동 동일시하지 않는다.
Mode1xInitial.mat의 존재·헤더 및 SHA `40eaebc92badb04ad026e358cfd28ec9c778fcf2d24a1b8f5d85565854da2747`을 확인했지만 MATLAB 로딩은 하지 않았다. S-function temexd_mod의 실제 실행 플래그는 미확인이다. tecode.zip의 오래된 압축 방식은 현재 기본 해제 도구에서 지원되지 않아 전체 원본 바이트를 보존했다.

## 5. A3 — 정상 파일럿

**NOT_RUN**. A2 미통과로 실행하지 않았다. 정상 운전 로그·반복 일치·새 압력/온도 결과는 없다. MATLAB 위치/권리가 확보되고 실제 모델 로딩·컴파일을 확인한 후에만 초기 상태·solver·seed·horizon·sampling·종료 조건을 사전 고정한다. archive의 2800 kPa·65%·122.9°C 설정은 정적 출처값이며 실제 실행 결과가 아니다.

## 6. A4 — 비교 가능성

| 수준 | 상태 | 제한 |
|---|---|---|
| L1 변수·단위 | VERIFIED | 문서·코드의 선언 대응만; 실제 원시 열은 미회수 |
| L2 운전점 | PARTIAL | 공식 설정/문서와 benchmark 평균 근접; 실행 동일성 미확인 |
| L3 모델 revision | PARTIAL | 수정 모델 계열 확보; 실제 생성 바이너리 대응 미확인 |
| L4 controller·개입 | PARTIAL | 정적 배선 단서; do(XMV)/setpoint/manual override 실제 의미 미검증 |
| L5 초기조건·잡음·export | UNKNOWN | 원시 run과 연결 불가 |
| L6 반복 실행 | NOT_RUN | A2 차단 |
| L7 효과 비교 기준 | BLOCKED | 직접 개입 효과 정답 활용 NO-GO |

## 7. 권고와 종료 기준

현재 권고는 요청의 **C: 자료·실행환경 확보 차단을 명시하고 Track B 참조 구조 검증 설계 검토를 제안**하는 것이다. Track B 또는 C로 전환하지 않았고 연구 질문도 변경하지 않았다. 제한적 복원 검색은 여기서 종료한다. 새로운 원본/실행환경이 제공될 때만 재개한다.
원시 ZIP 접근과 합법 실행환경이 해결되면 Track A를 재개할 수 있다. 공정 설정값이나 정상 분포 유사성만으로 효과 참조를 승인하지 않는다. 신규 simulator-native 연구를 검토하려면 관측/개입 동일 환경 계약과 새 참조 구조의 검증 가능성을 별도로 제안하고 사용자 승인을 받아야 한다.

## 8. 다음 3개 작업과 완료 기준

1. 정상 ZIP의 합법적 회수: 정확한 목록·SHA·권리·SIMOUT/XMV/TOUT/seed 실재 확인. 요청 항목은 TRACK_A_RAW_DATA_REQUEST.md 참조.
2. 승인된 MATLAB/Simulink 환경 확보: 버전·라이선스·별도 작업 사본 .mdl/MAT 로딩과 MEX 호환성의 실제 로그.
3. benchmark export 연결: 정상 run 선택·timestamp·median stride/경계·1499행 원인을 코드로 연결. 확보 불가하면 전환 승인을 위한 대안 설계만 작성.

## 9. 재검증과 기록

`python -X utf8 scripts/validate_track_a_recovery.py`는 출처 해시·Gate 계산·과거 산출물 불변을 검사한다. 환경을 새로 검출하거나 MATLAB 실행 성공을 보증하는 검사는 아니다.
`collect_track_a_evidence.py --local-records <로컬 기록 폴더> --output <새 evidence 폴더>`는 이번 읽기 전용 탐색 기록을 정제한다. 개인 경로·임시 서명 링크·전체 PDF는 반입하지 않는다. A1/A2 미검증 불리언 false는 전역 부재의 증명이 아니다.

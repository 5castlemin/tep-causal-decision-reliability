# Track A 원자료·실행환경 요청 초안 — 미발송

외부 연락은 하지 않았다. 발송·계정 생성은 별도 사용자 승인이 필요하다.

## 데이터 보유자에게 필요한 파일

- DOI 10.21227/326k-qr90의 공식 DataPort 정상 패키지 **3_Normal Steady-State.zip** (목록상 61.88 MB). 제공 위치: https://ieee-dataport.org/open-access/tennessee-eastman-process-alarm-management-dataset
- ZIP 원본 SHA-256, 실제 내부 파일 목록, 적용 라이선스/공유 권리.
- benchmark에서 선택한 정확한 정상 run의 측정값과 조작변수, 시간축, seed. 기술보고서에 등장하는 SIMOUT.xlsx/XMV.xlsx/TOUT.xlsx/random_seed.txt가 정상 패키지에도 있는지 먼저 확인. Tests 도식으로 정상 파일 존재를 단정하지 않음.
- 실제 모델 revision/바이너리·flag, controller 파일·설정값·운전 mode, 초기 상태 MAT, solver·tolerance, seed/RNG·잡음·disturbance 조건.
- 0.1 Hz 원자료에서 현재 CPCaD-Bench 1499×31 CSV로 내보낸 코드와 선택 구간. 180초 median의 stride·중앙/후행 창·경계·시작/종료 timestamp, 필터/Deadband 적용 여부, 변수 선택·X27/X31 제외 경위.
- 논문 1500 samples와 공개 CSV 1499 data rows 차이의 근거. 미확인 행을 복구하거나 추가하지 않음.

## 실행환경 보유자에게 확인할 사항

- 합법적으로 사용 가능한 MATLAB/Simulink 설치 또는 승인된 원격 실행 위치, 버전·라이선스 상태.
- temexd_mod.zip의 .mdl/MAT 로딩 및 MEX 컴파일 가능 여부와 도구 버전. 실제 실행 전까지 설치 가능성을 실행 성공으로 기록하지 않음.

## 문의 문안

TEP benchmark 재현을 위해 정상 데이터 패키지의 정확한 run 및 시간축과 공개 benchmark CSV의 생성 관계를 확인하고자 합니다. 위 파일/설정/전처리 코드 중 제공 가능한 자료와 재사용 조건을 알려주실 수 있을까요? 특히 3분 창의 이동 간격과 1499행 생성 경위를 확인하고 싶습니다. 확인할 수 없는 항목은 미확인으로 답해 주셔도 됩니다.

# 시뮬레이터 회수·재현 상태

2026-10-23 현재 Gate A는 **BLOCKED**. 8월 방학 스터디 3주차 보고서 4쪽에는 소스 확보와 Python 연동 기초 테스트가 보고되어 있지만, 현재 접근 가능한 Downloads, 기존 Codex workspace, 관련 프로젝트 폴더, 본 저장소 Git 이력에서는 실행 소스, controller 설정, 재현 명령, 원시 정상 운전 로그를 찾지 못했다. 기존 `tests/smoke/check_simulator.py`는 소스 부재를 기록할 뿐 실제 TEP를 실행하지 않는다. 대화/보고서 진술을 정상 운전 재현으로 승격하지 않는다.

다음 회수 단위는 당시 사용한 원본 저장소 URL 또는 ZIP, commit/version, 라이선스, Python 환경/의존성, 시작 명령, 정상 운전 반복 로그, Fault/IDV 주입 함수, XMV 직접 쓰기와 setpoint/controller 우선순위, XMEAS 기록 형식이다. 이 정보를 확보하면 원본을 별도 읽기 전용 위치에 두고 버전·해시를 고정한 뒤 실제 정상 운전 2회와 제한된 개입 smoke를 수행한다. Fault·Action·Target 및 안전 임계값은 그 결과를 보기 전에 별도 계약으로 확정한다. 본 문서는 미실행 결과를 만들지 않는다.

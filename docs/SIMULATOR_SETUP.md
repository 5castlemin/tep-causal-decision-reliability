# 시뮬레이터 회수·재현 상태

## 최신 검증 — 수치·초기화·호환성

[수치·초기화·호환성 보고서](audit/SIMULATOR_RELIABILITY_REPORT.md)를 현재 판단으로 사용한다. 후보 내부 탐색은 CONDITIONAL, 기존 benchmark 개입 효과 정답으로 직접 사용은 NO-GO이다. 새 객체 동일 seed의 정확 재현 계약은 확인했다. 같은 객체 reset은 약 1e-12 관측 차이를 남긴다. 1788초 종료는 후보의 압력 한계 초과로 재현됐으며 독립 구현 정확성 검증은 남아 있다. 2시간 정상 기록은 기존 데이터와 운전점이 다르다. 아래는 이전 실행의 이력으로 보존한다.

2026-10-23 기존 **8월 원본 구현 복구 Gate A는 BLOCKED**이다. 별도 공개 Python 후보는 PARTIAL이며 아래와 `experiments/simulator/run_20261023_v3/summary.json`을 참조한다. 8월 방학 스터디 3주차 보고서 4쪽에는 소스 확보와 Python 연동 기초 테스트가 보고되어 있지만, 당시 감사한 Downloads, 기존 Codex workspace, 관련 프로젝트 폴더, 본 저장소 Git 이력에서는 8월 당시 구현의 실행 소스, controller 설정, 재현 명령, 원시 정상 운전 로그를 찾지 못했다. 기존 `tests/smoke/check_simulator.py`는 소스 부재를 기록할 뿐 실제 TEP를 실행하지 않는다. 대화/보고서 진술을 정상 운전 재현으로 승격하지 않는다.

다음 회수 단위는 당시 사용한 원본 저장소 URL 또는 ZIP, commit/version, 라이선스, Python 환경/의존성, 시작 명령, 정상 운전 반복 로그, Fault/IDV 주입 함수, XMV 직접 쓰기와 setpoint/controller 우선순위, XMEAS 기록 형식이다. 이 정보를 확보하면 원본을 별도 읽기 전용 위치에 두고 버전·해시를 고정한 뒤 실제 정상 운전 2회와 제한된 개입 smoke를 수행한다. Fault·Action·Target 및 안전 임계값은 그 결과를 보기 전에 별도 계약으로 확정한다. 본 문서는 미실행 결과를 만들지 않는다.

## 2026-10-23 — 공개 후보 실제 실행

기존 8월 구현 복구는 여전히 차단되어 있다. 별도의 공개 Python 후보에서 30분 정상 운전 2회, 변수 기록, 직접 XMV 쓰기와 IDV4 주입은 실행했다. 기존 Gate A를 완전 통과로 승격하지 않는다. 개입 실행의 조기 shutdown과 동일 객체 초기화 불일치, 기존 모델·controller 호환성 미확인 때문이다. 정확한 commit, 실행 명령, 원시 CSV 및 Gate별 판정은 [실행 감사](audit/SIMULATOR_FEASIBILITY_REPORT.md)를 참조한다. 새 후보는 기존 GT의 개입 효과 정답이 아니다.

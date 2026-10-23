# 작업 기록

기록 원칙: 실질 작업마다 날짜, 브랜치/커밋, 실행 명령, 실제 결과, 미수행/차단 사항을 추가한다. 이 문서는 작업 성공을 추정하지 않는다.

## 2026-10-23 — Slack 자산 및 연구 운영 정비

- 브랜치: `feature/slack-assets-research-ops` (커밋/PR은 이 작업 완료 시 Git 이력 참조).
- Slack `#26-2_제조공정` 채널과 주요 thread를 직접 읽고, 파일 링크 및 일부 텍스트 파일 본문을 확인했다. ZIP의 바이트는 Slack connector를 통해 회수하지 않았다.
- 기존 `TEP_step6_results.zip`, `TEP_final_graphs_v1.zip`, 과제 ZIP과 공개 CPCaD-Bench 입력의 로컬 SHA-256을 기존 목록과 대조했다. 기존 frozen graph는 수정하지 않았다.
- CPCaD-Bench 소스 커밋의 데이터·GT를 해시 검증하여 `data/local/`에 받는 독립 명령과 문서 동기화 CI를 추가했다. 배포 권리 불명확으로 데이터 바이트를 Git에 추가하지 않았다.
- 8월 시뮬레이터 보고, 접근 가능한 이전 workspace·Downloads·관련 프로젝트 경로, Git 이력에서 실행 소스/원시 로그를 찾지 못했다. 정상 운전·Fault·XMV 개입은 `NOT_RUN`; Gate A `BLOCKED` 유지.
- 검증 명령과 결과는 이번 PR 설명 및 CI에 기록한다. 새 인과발견/SCM/Recovery 실험은 수행하지 않았다.
- 실제 검증: `python -X utf8 src/acquire_reference_data.py --source-git <로컬 CPCaD-Bench>` 데이터·GT 해시 PASS, `python -X utf8 graphs/final/verify_and_load.py` 39파일 PASS, `python -X utf8 src/verify_recovery.py` 7개 Step 6 수치 대조 PASS, `python -X utf8 -m unittest discover -s tests -v` 5개 PASS, `git diff --check` PASS. 문서 동기화 검사는 커밋 뒤 `origin/main...HEAD`로 다시 실행한다.
- 로컬 PCMCI+ baseline의 실행·축약 코드 두 파일을 발견하고 SHA-256을 확인했다. 현 Final의 재실행 설정과 primary 설정이 다르므로 Final 생성 코드로 반입하지 않았다.

## 2026-10-23 — Simulator feasibility 실제 실행

- 사용자 승인으로 PR #1 병합 (`ceb447d`), main fast-forward 후 `feature/simulator-feasibility` 생성. 기존 동결 그래프 불변.
- pyTEP·TEP Studio·TEP-Rust·Python TEP 후보의 source/license/interface 검토. Studio 설치는 인코딩 오류 해결 후 MSVC 부재로 실패. Python 후보 commit `9a6c8e5fcef4a2850778704e7793c87b0a187005`를 저장소 밖에서 실행.
- 명령: `python -X utf8 experiments/simulator/run_feasibility.py --source ../tep-python-candidate --output experiments/simulator/run_20261023_v3`.
- 정상 운전 2회 exact 동일; 수동 밸브 개입은 1788초 shutdown. IDV4 주입/clear 성공, 같은 객체 reset 관측 복원 실패. 최초 요약은 길이 불일치 오류, 공통 timestamp 비교로 수정; 실패 raw CSV 보존.
- 결과: 후보 실행 가능성 PARTIAL. 기존 GT 효과 oracle·Recovery·Safety는 미검증. raw CSV와 source/환경/hash 및 재현 검증기를 추가.
- 검증: `python -X utf8 experiments/simulator/validate_feasibility.py` PASS (실험 gate는 PARTIAL), `python -X utf8 graphs/final/verify_and_load.py` 39파일 PASS, `python -X utf8 -m unittest discover -s tests -v` 5 tests PASS, `git diff --check` PASS. CI에 원시 결과 hash 검증 추가. 실제 simulator source 없이 저장된 증거를 검사하므로 CI 성공이 새 simulator 실행을 뜻하지 않는다.
- CI 첫 실행에서 CSV SHA 불일치 확인: Windows 원시 CRLF가 Git의 text 정규화로 LF로 저장된 것이 원인. 실험 수치는 수정하지 않고 `.gitattributes`에서 simulator CSV에만 `-text`를 지정해 원본 바이트 보존. 재검증은 최신 CI 참조.

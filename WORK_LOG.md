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


## 2026-10-23 — 미완료 연구 자산 복원과 현재 상태 정합성

- 브랜치 `feature/research-asset-recovery`, origin/main `ceb447d`에서 생성. PR #1 병합 확인; PR #2 open/head `e5a0291`/CI success 확인. PR #2 병합·simulator 재실행·코드 변경 없음.
- Slack 파일 ID 두 개에서 실제 ZIP bytes 회수, 기존 로컬 Step 6/과제 ZIP SHA와 exact 일치. 원본은 저장소 밖 보관; signed URL과 원본 바이너리 반입 없음.
- `FREEZE.code`에 Final 생성 파일 hash는 있지만 Step6 ZIP에는 algos source가 없음을 확인. 정확한 Colab export가 로그인 HTML을 반환한 것도 기록. 과거 PCMCI+/담당B 문서를 현재 Final 코드로 승격하지 않음.
- 새 공개 CPCaD clone·clean venv·빈 destination에서 `src/acquire_reference_data.py` 실행. 데이터/GT hash·shape·순서 확인. 이어 `src/reproduce_step6.py --step6-zip <회수 ZIP> --gt <새 GT> --output <새 결과>` 실행하여 원본 evaluator strict 지표 7개 일치. 원본 생성 학습은 NOT_RUN/BLOCKED.
- `docs/research_state.json`에서 최신 PROJECT_STATUS/PRIORITIES 생성. 과거 본문은 docs/history에 보존하고, 기존 8월 simulator BLOCKED와 PR #2 공개 후보 PARTIAL을 분리. 다음 3개는 SRC-01/SIM-03/SIM-04, 작업 ID 이력 기록.
- 검증 및 PR 최종 정보는 이번 commit/PR과 validation JSON에서 확인한다. 자동 문서 검사는 사실의 진실성을 보증하지 않는다.
- 검증 완료: `scripts/check_research_state.py`, `scripts/check_asset_manifest.py` PASS; unit tests 8개 PASS; frozen verifier 39파일/시계열 3개 재변환 PASS; diff 검사 PASS. 새 venv는 NumPy 2.4.6/pandas 3.1.0, 데이터 1499×31·GT 33×33→28간선 확인. 실제 생성 알고리즘 실행 0개, simulator 재실행 0개.
- GitHub의 이번 feature branch를 새 clone한 경로에서도 전체 가이드 검증 통과 (`validation/team_checkout.json`, 검사 commit `1b63ec7`). 기존 통합 lag converter는 freeze source SHA와 동일함을 확인해 미회수 목록에서 제외했다. 생성 코드 미회수 상태는 그대로다.

## 2026-10-23 — PR #2·#3 임시 통합 검토

- main `ceb447d`, PR #2 `e5a0291`/open/CI success, PR #3 `b2e455f`/open/CI success 확인. 시작 시 사용자 미커밋 변경 없음.
- `feature/pr2-pr3-integration`에서 두 PR을 시험 병합. PROJECT_STATUS/PRIORITIES/WORK_LOG/workflow 4개 충돌 해결. 상태 JSON 구조와 simulator 기록/검사의 합집합 유지.
- 원본 graph 46 tracked 파일, simulator 30파일, Step6 결과표·raw CSV hash·양쪽 작업 기록 불변 검사 PASS. unit 8개, graph verifier, state/asset checker, 원본 evaluator strict 재현 PASS.
- main 병합·기존 PR 종료·기존 PR branch 수정 없음. 검토 보고서 `docs/audit/PR2_PR3_INTEGRATION_REVIEW.md`. 승인 후 #2→#3 순서로 실제 main 통합 및 재검증 예정.

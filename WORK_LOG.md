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

## 2026-10-23 — 미완료 연구 자산 복원과 현재 상태 정합성

- 브랜치 `feature/research-asset-recovery`, origin/main `ceb447d`에서 생성. PR #1 병합 확인; PR #2 open/head `e5a0291`/CI success 확인. PR #2 병합·simulator 재실행·코드 변경 없음.
- Slack 파일 ID 두 개에서 실제 ZIP bytes 회수, 기존 로컬 Step 6/과제 ZIP SHA와 exact 일치. 원본은 저장소 밖 보관; signed URL과 원본 바이너리 반입 없음.
- `FREEZE.code`에 Final 생성 파일 hash는 있지만 Step6 ZIP에는 algos source가 없음을 확인. 정확한 Colab export가 로그인 HTML을 반환한 것도 기록. 과거 PCMCI+/담당B 문서를 현재 Final 코드로 승격하지 않음.
- 새 공개 CPCaD clone·clean venv·빈 destination에서 `src/acquire_reference_data.py` 실행. 데이터/GT hash·shape·순서 확인. 이어 `src/reproduce_step6.py --step6-zip <회수 ZIP> --gt <새 GT> --output <새 결과>` 실행하여 원본 evaluator strict 지표 7개 일치. 원본 생성 학습은 NOT_RUN/BLOCKED.
- `docs/research_state.json`에서 최신 PROJECT_STATUS/PRIORITIES 생성. 과거 본문은 docs/history에 보존하고, 기존 8월 simulator BLOCKED와 PR #2 공개 후보 PARTIAL을 분리. 다음 3개는 SRC-01/SIM-03/SIM-04, 작업 ID 이력 기록.
- 검증 및 PR 최종 정보는 이번 commit/PR과 validation JSON에서 확인한다. 자동 문서 검사는 사실의 진실성을 보증하지 않는다.
- 검증 완료: `scripts/check_research_state.py`, `scripts/check_asset_manifest.py` PASS; unit tests 8개 PASS; frozen verifier 39파일/시계열 3개 재변환 PASS; diff 검사 PASS. 새 venv는 NumPy 2.4.6/pandas 3.1.0, 데이터 1499×31·GT 33×33→28간선 확인. 실제 생성 알고리즘 실행 0개, simulator 재실행 0개.

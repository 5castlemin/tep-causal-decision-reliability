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

## 2026-10-23 — 사용자 승인에 따른 실제 통합

- PR #2를 사용자 승인 후 merge `0549c4d`로 병합. PR #3에 최신 main을 merge하고 사전검토와 동일한 네 충돌을 해결했다.
- state JSON 및 생성 MD, README/소개서의 PR #2 병합 상태를 갱신. CI 양쪽 검사와 원본 작업 기록을 모두 유지.
- simulator/frozen 파일 변경 없음. 검증 unit 8개, graph 39파일, state/asset/raw simulator 검사와 원본 strict evaluator 재현 PASS. 최종 head CI 성공 확인 후 승인 범위 내 PR #3 병합 예정. 실제 병합 여부는 GitHub PR 기록이 기준이다.

## 2026-10-23 — SIM-03/SIM-04/COMPAT-01 실증 진단

- `git fetch origin`, clean 상태·PR #2/#3 병합 확인 후 main `172e84bcafb82dd5074f097fcabfb94f28ff96e3`에 fast-forward 동기화, `feature/simulator-numerical-validation` 생성. main 자동 병합 없음.
- pinned 외부 source `9a6c8e5fcef4a2850778704e7793c87b0a187005`를 수정하지 않고 Python 3.11.15/NumPy 2.4.6에서 실행.
- 실제 명령: `python -X utf8 experiments/simulator/diagnostics/run_diagnostics.py --source ../tep-python-candidate --output experiments/simulator/diagnostics/run_20261023`; 기록 시계 보완 후 같은 명령의 출력만 `run_20261023_aligned`로 변경하여 실행. 두 번째는 2시간 폐루프 정상 조건 포함. stdout은 `experiments/simulator/diagnostics/execution_logs/`.
- 12개 수동 조건: dt=1/.5/.25초, XMV10 600초 +0/+1 pp, 원본 잡음/관측 표준편차 0. 각 모드 fresh/초기화반복/운전후/IDV4후 초기화 등 10경우 실행. 각 plan은 실행 전 저장. 첫 실행의 단일 시계 표본은 보존하고 정렬 분석에서 제외.
- SIM-03: 기존 1788초 종료 및 모든 공통 manual 측정·조작값 exact 재현. 내부 pressure 3000.574119 kPa 초과, 유한 state/미분. dt=.25 원본 잡음에서는 raw2999.986/관측3000.341의 다른 종료 경로 확인. 잡음 통제 후 dt 축소 시 경로 차이 약 절반 감소. 독립 Fortran 대조 NOT_RUN(backend/compiler 미확보).
- SIM-04: process yy/XMV/IDV/RNG/controller 복원. cache와 관측 약 1e-12 차이로 같은 객체 bit reset은 미보장. 새 객체 동일 조건의 60초 경로는 수동·폐루프 모두 exact. 공식 계약을 새 객체 반복으로 한정하여 VERIFIED.
- COMPAT-01: 기존 1499×31 데이터와 새 2시간 정상 기록의 31변수 통계 비교. 온도·압력·level 운전점 차이. 3분 진단 창은 benchmark sliding preprocessing 재현 아님. upstream Dataport 접근 HTTP 오류. 기존 GT를 효과 정답으로 취급하지 않음.
- 분석 첫 시도는 이름 없는 index 열로 NumPy header 해석 실패. csv.reader로 index를 명시적으로 제외하여 수정하고 v2 성공, v3에 공통 관측 시점 반응 추가. 데이터 수정 없음. `analyze_diagnostics.py --dataset data/local/datasetTE.csv --output experiments/simulator/diagnostics/analysis_20261023_v3` 실제 실행.
- 판단: 후보 내부 조건부 탐색 CONDITIONAL / 원래 benchmark 효과 정답 직접 활용 NO-GO. Recovery/Safety 계산 및 새 SCM/discovery 학습 없음.
- `docs/research_state.json` 갱신 후 `python -X utf8 scripts/check_research_state.py --write` 실행. SIM-03/COMPAT-01 PARTIAL, 8월 복구 BLOCKED 유지. 현재 상위 3과제는 COMPAT-01, SIM-03, SRC-01.
- 원시 SHA·시계·분석 재계산 validator와 시계 혼동 방지 단위 테스트 추가. CI의 외부 source 없는 검사와 실제 로컬 실험을 분리. 최종 검증 명령 및 결과는 같은 작업의 후속 기록에 남긴다.

### 이번 진단 최종 로컬 검증

- `graphs/final/verify_and_load.py`: 39개 hash·변수 순서·시계열3종 재변환 PASS. `src/verify_recovery.py`: 데이터/GT 및 점수 독립 대조 PASS.
- `src/reproduce_step6.py --step6-zip ../work/asset_recovery/TEP_step6_results_slack.zip --output ../work/asset_recovery/numerical_validation_step6.json`: 원본 평가기의 7 strict 지표 모두 일치. 결과 사본 `experiments/simulator/diagnostics/step6_verification.json`. 인과발견 학습 재실행 아님.
- 기존 `validate_feasibility.py`, 새 `diagnostics/validate_diagnostics.py`, `check_research_state.py`, `check_asset_manifest.py`, `validate_pr_integration.py`: PASS. 기존 PR2 30파일 및 graph tree 46파일 불변 검증.
- `python -X utf8 -m unittest discover -s tests -v`: 10개 PASS. `git diff --check`: PASS. 상세 명령/출력은 `experiments/simulator/diagnostics/local_verification.json`.
- 외부 simulator 실행은 로컬 검증이며 CI는 source 다운로드 없이 저장된 증거 재계산만 수행한다. CI/PR 결과는 GitHub checks를 따른다.

- `scripts/check_research_docs.py --base origin/main` PASS. 검증기의 기존 recovery_validation 기록 재저장은 원래 바이트/내용으로 복원하여 이번 PR에 포함하지 않았다. 원본 simulator source와 이전 실험·Final 결과 변경 없음.

## 2026-10-23 — Benchmark Compatibility & Research Design Decision Gate

- `git fetch origin` 후 clean 상태 확인. main `172e84b`; PR #4는 OPEN/미병합 head `71c5448ed9a82548d86f40f60be842020f69538d`, CI run39947597305 성공. PR #4를 병합하지 않고 그 head에서 `feature/benchmark-compatibility-decision` 생성. 새 PR은 PR #4 브랜치를 base로 하는 의존 PR이다.
- 기존 source·동결·감사를 재사용. 신규 simulator/discovery/SCM/Recovery/Safety 실행 없음.
- 작성자 공개 Manca 기술보고서 v1.1의 모델·controller·밸브 정책·timestamp 별도 저장 서술을 읽음(REPORTED). 공식 Dataport 원자료 페이지는 접근 실패, 실제 timestamp/seed/정상 원시 Excel은 여전히 미회수.
- 대학 공식 URL의 `temexd_mod.zip` 639921B 및 `tecode.zip` 29307B를 urllib.request로 회수하여 저장소 밖 작업 영역에 보존. SHA/멤버 목록은 `docs/research_design/evidence/local_20261023_v2/local_audit.json` 및 별도 retrieval.json. 권리 미확정 ZIP/source/mex 바이너리를 Git에 반입하지 않음. MATLAB PATH 명령 미확인, 두 모델 실행 NOT_RUN.
- 실제 source의 Constant→TE Plant port→이름 있는 입력을 추적하여 원자로 level65/pressure2800/temperature122.9 확인. 블록 xmv 이름을 MV 번호로 오독하지 않음. archive Ts_base1.8초/Ts_save36초/ode45 기본값은 Manca의 실제 변경 설정과 동일하다고 주장하지 않음.
- `python -X utf8 scripts/audit_benchmark_compatibility.py --benchmark-git ../work/asset_recovery/fresh-CPCaD-Bench --modified-archive ../work/compat_gate_20261023/temexd_mod.zip --original-archive ../work/compat_gate_20261023/tecode.zip --candidate ../tep-python-candidate --output docs/research_design/evidence/local_20261023_v2` 실제 실행 성공. 고정 CSV/GT byte identity 및 공식 NumPy1499×31 exact 일치 확인. 1500/1499 원인은 미확정.
- 첫 로컬 감사는 Windows 긴 경로의 git show stat 실패. 명령 단위 `-c core.longpaths=true`로 수정한 뒤 새 출력 v2에서 성공. 전역 Git 설정·사용자 파일 변경 없음. 초벌 NumPy 탐색의 delimiter 누락은 comma 지정으로 수정. 실패를 데이터 손상·simulator 실패로 해석하지 않음.
- PR4 156변경/145신규/내용16740258B 및 byte중복24그룹(88경로) 확인. 가장 큰 terminal JSON3.81MB. raw/manifest와 반복 증거를 그대로 유지함.
- 현재 가설 Gate D(증거 부족), 다음 A의 제한적 복원 확인 권고. B/C는 제안이며 채택 미실행. RESEARCH_DESIGN.md 불변. 상태 JSON의 COMPAT-01과 BENCH-ENV 및 PR4 미병합 의존성을 기록하고 dashboard 재생성.
- `validate_benchmark_decision.py` PASS, 단위 테스트13개 PASS. 배선 이름/port 혼동·모호한 배선 거부 검증 추가. 최종 기존 증거/동결/문서 동기화 검사와 CI 결과는 후속 기록 및 PR checks를 따른다.

### Benchmark Gate 최종 로컬 검사

- `scripts/validate_benchmark_decision.py`: PR4 156개 파일 inventory hash·설계 불변·외부 코드 정적 근거·주장 수준·상태 일치 PASS.
- 기존 `experiments/simulator/diagnostics/validate_diagnostics.py`: 원시 SHA·시계·reset·분석 재계산 PASS. `graphs/final/verify_and_load.py`: 39개 hash/lag 변환 PASS.
- `scripts/check_research_state.py`, `scripts/check_asset_manifest.py`, `scripts/validate_pr_integration.py`, `scripts/check_research_docs.py --base origin/feature/simulator-numerical-validation`: PASS.
- 단위 테스트13개 PASS, `git diff --check` PASS. 명령/출력은 `docs/research_design/evidence/validation_results.json`. 외부 코드 다운로드·정적 분석은 로컬에서만 수행했고 CI는 고정 증거 및 회귀 검사를 수행한다.
- 기존 `RESEARCH_DESIGN.md`, simulator 원시 tree, 7개 frozen graph, Step6 점수표 불변. 신규 evidence 파일의 byte hash를 Windows checkout에서도 보존하는 속성만 추가했으며 기존 파일의 보존·중복 제거 정책은 변경하지 않았다.

## 2026-10-23 — 승인된 PR4→PR5 병합 준비

사용자의 명시적 승인 후 PR #4 head71c5448을 merge commit 1e4fcc7c91839afd49770fcc8b3380d368e1dea3로 병합했다. PR #5 base를 main으로 조정하고 현재 상태의 미병합 표시를 갱신했다. 작성 당시 decision JSON과 원시 hash는 보존하며 github_current에 실제 상태를 분리했다. 로컬 사용자 변경은 없었다. 선행검토에서 단위 테스트13개와 보존 검사가 통과했으며 CI 재검증 후 PR #5를 병합한다. Track A 신규 조사와 실험은 아직 시작하지 않았다.
# 2026-10-23 Track A 복원 Gate

- 사용자 승인 후 PR #4 병합(1e4fcc7), PR #5 main 재정렬 및 상태 시점 구분 수정(a2dc2b2, Actions 39960138640 성공), PR #5 병합(7b16638). 최신 main에서 feature/track-a-recovery-gate 생성. 사용자 변경사항 덮어쓰기 없음.
- 기존 temexd_mod.zip/tecode.zip SHA 재확인. 원본 재다운로드·수정 없음. 공식 DataCite DOI JSON과 IEEE DataPort 목록 HTTP 200 확인. 정상 패키지 3_Normal Steady-State.zip은 로그인 필요, 원본 미회수.
- 공개 Technical_Report_V1_2.pdf 실제 회수(5,990,722 bytes, SHA 657307d7119538a0c21bdc49933c4ff31de929038a0213f9f4a8dfc3fde9faf0). 오래된 공개 문서 링크 403 후 공개 페이지 갱신 링크에서 200. PDF 12/13/14/42쪽 시각 확인. TOUT.xlsx/random_seed.txt는 문서상 명칭이며 정상 ZIP 실재 검증 아님.
- PowerShell 읽기 전용 PATH/MathWorks registry/제품 목록/C·D 일반 설치경로/Start Menu/App Paths/프로세스 검사: inspected 범위 MATLAB 미발견. 라이선스·Simulink·.mdl 로딩·MEX NOT_RUN. 신규 파일명 단서의 제한적 os.walk 탐색 11,971개 이름, 일치 0. 전수 Slack/전체 디스크 재감사 없음.
- 실제 명령: collect_track_a_evidence.py --local-records <지정 아카이브 기록 폴더>, 일회성 상태 JSON 갱신 후 python -X utf8 scripts/check_research_state.py --write. 개인 경로·서명 URL·PDF 전체는 Git에 반입하지 않음.
- A1/A2 BLOCKED, A3 NOT_RUN, A4 NO-GO. 정상 운전·새 시뮬레이터/SCM/Recovery/Safety 실행 없음. 원시 기록/PDF/시각 확인 이미지는 지정 아카이브의 10_TrackA_원환경_복원Gate에 보존.
- 로컬 검증 통과: validate_track_a_recovery.py, unittest discover(16개), validate_benchmark_decision.py, validate_feasibility.py, validate_diagnostics.py, graphs/final/verify_and_load.py(39 hash), check_asset_manifest.py, validate_pr_integration.py, src/verify_recovery.py. 마지막 명령은 기존 점수 독립 대조이며 새 discovery 실행은 아니다. 12조건 시뮬레이션 재실행 없음.

## 2026-10-24 — Track B 참조 구조 타당성 감사

- git fetch origin 후 사용자 변경 없음 확인. PR #6 OPEN/head5fe3997, Actions39963153945 성공, 변경16파일 검토. main7b16638은 그대로 두고 feature/track-b-reference-validity를 PR6 head에서 분기했다. PR base는 feature/track-a-recovery-gate이다. 자동 병합 없음.
- RESEARCH_DESIGN/상태 JSON/우선순위/Track A·호환성·신뢰성 보고서/GRAPH_REPRODUCIBILITY/TASK_SPEC/PILOT_PLAN 재사용. 원자료 검색·Slack 전수 감사·기존 12조건 실행은 반복하지 않았다. 사용자의 MATLAB/정상 ZIP 위치 모름 답변을 차단 해제로 해석하지 않음.
- 고정 Python source의 simulator/backend/controllers/constants 4파일 SHA를 기존 로그와 대조하고, 상태→측정·명령→밸브·제어기 주기·RNG 조건 분기를 코드로 검사했다. 코드 의존성을 GT로 변환하지 않았다.
- 사전 범위 TRACK_B_SMALL_CHECK_PLAN.md 기록 후 `python -X utf8 scripts/audit_track_b_source.py --source ../tep-python-candidate --output docs/research_design/track_b_evidence/source_probe.json` 실행. 최초는 잘못된 process._process 접근 AttributeError로 실패/결과 파일 없음. 실제 API 직접 process로 고쳐 재실행 성공. 수동/폐루프 기준·조작 4객체 각30step, seed465120799/dt1초/IDV0, step6에 XMV10+0.1pp 1회 명령. 해당 구간 RNG·잡음 digest 일치, 상태 유한/계속 실행. 폐루프는 명령값을 controller가 갱신. 효과/복구/안전 점수 계산 없음.
- 공식 Rieth DataCite/Dataverse API 메타데이터 HTTP200. v1.0 네 RData 목록·provider MD5·custom public-domain 이용 조건 확인. 데이터 본체는 다운로드하지 않았고 CC0로 축약하지 않음. Ricker/CIPCaD/Studio 공식 출처·기존 로컬 LICENSE 정적 확인. 외부 구현 재설치/교체 없음.
- Q1 PARTIAL/Q2 BLOCKED/Q3 BLOCKED/Q4 UNKNOWN/Q5 VERIFIED(결과 분리 설계). 현재 채택 NO-GO, 가설 검증 INSUFFICIENT_EVIDENCE. 연구 질문·RESEARCH_DESIGN·7 frozen·Step6·기존 raw/evidence 미변경. Track B 채택/새 GT 생성 없음.
- canonical JSON에 REF-B/SIM-B/DESIGN-B 및 PR6 미병합 의존성을 추가, `python -X utf8 scripts/check_research_state.py --write` 실행. `validate_track_b_audit.py`, `validate_track_a_recovery.py`, `python -X utf8 -m unittest discover -s tests -v`(16개) 통과. 새 source probe는 외부 source 필요로 CI 재실행과 분리한다.
- 추가 통과: validate_benchmark_decision.py, validate_pr_integration.py, graphs/final/verify_and_load.py(39파일 hash), check_asset_manifest.py, check_research_state.py, check_research_docs.py --base origin/feature/track-a-recovery-gate. SIM-02의 구형 다음 행동 문구는 이미 확보된 2시간 기록 보존으로 정정했다. 작은 probe는 초기 RNG 스냅샷을 별도 저장하지 못한 제한을 보고서에 명시했다.

## 2026-10-24 — REF-B 냉각수 최소 블록 검산 및 중단

- git fetch origin/status 확인: 미커밋 변경 없음, main7b16638, PR6 OPEN/CI39963153945 성공, PR7 OPEN/head8634e5d/CI40076485580 성공. PR7은 PR6 기반 stacked임을 확인. feature/ref-b-minimal-subsystem을 PR7 위에서 생성. 자동 병합 없음.
- 고정 Python source의 backend 상태·열/에너지/밸브 식, 센서식, PI/cascade의 호출 순서·3step 주기를 읽고 source 4파일 SHA를 대조했다. 동일 계보 teprob.f의 대응 식은 정적으로만 대조. source 수정·재설치 없음.
- REF_B_MINIMAL_CHECK_PLAN.md를 먼저 기록한 후 `python -X utf8 scripts/validate_ref_b_subsystem_source.py --source ../tep-python-candidate --output docs/research_design/ref_b_minimal_evidence/local_checks.json` 실행 성공. t0/IDV0/초기점의 전체 process deepcopy에서 17회 고정 평가·2개 epsilon의 편미분, 별도 액체 엔탈피 이분법, 제어기 복사본의 phase 검산 수행. 0 국소 결과를 비간선 정답으로 사용하지 않았다.
- 별도 수동2객체에 XMV10+0.1pp, dt1초, 각6step만 실행. 밸브/W/E 변화와 평가·상태 시계의 차이를 기록. 물리 dead time/총효과 성능으로 해석하지 않음. 원시 선택값·RNG·환경·해시는 새 evidence에 보존. 기존 raw 파일 변경 없음.
- 국소 구현 검산은 PASS, 구조는 CANDIDATE 유지. REF-B PARTIAL로 국소 진전만 기록하며 전체 Q2 BLOCKED/Track B NO-GO 유지. 관측 projection/발견 알고리즘 의미 불일치/정확도·효과 계약 부재로 중단 기준 충족. 추가 GT 후보·실험 확장 없음.
- canonical JSON 갱신 후 `python -X utf8 scripts/check_research_state.py --write` 실행. 기존 감사 JSON·RESEARCH_DESIGN·frozen·Step6·data·시뮬레이터 원시는 보존. 새 GT·precision/F1·새 학습·Recovery/Safety 계산 없음.
- 검증 통과: validate_ref_b_minimal_records.py(저장된 차분/해석식·독립 역산·시간/제어 순서·보존), validate_track_b_audit.py, validate_track_a_recovery.py, validate_benchmark_decision.py, 단위 테스트16개, graph39파일 hash/시계열 재변환, validate_pr_integration.py, check_asset_manifest.py, 상태/문서 동기화 및 git diff --check. 외부 source 단위 검산 실행은 CI 기록 검사와 분리했다.

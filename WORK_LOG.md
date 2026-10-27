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

## 2026-10-24 — 구조 지표→추천 MVP 기술 실행

- git fetch/status 및 PR6/7/8 OPEN·stacked·각 CI 성공 확인. PR8 head d508ab0 위 feature/causal-metric-decision-mvp 생성. main7b16638·기존 사용자 변경 보존, 자동 병합 없음.
- 기존7 frozen/Step6 최종7행·loop_vs_flow 원본 ZIP member와 3개 적합 JSON을 해시로 재사용. 적합·discovery 재실행 없음. 고정12과제×7의 경로 edge recall/완전 복원/confirmed 도달성/직접XY 84행을 별도 benchmark 진단으로 산출. Task 선택은 미리 고정한 냉각수 API/공정 의미만 사용.
- PLAN_v1.json 사전 기록 후 `python -X utf8 scripts/run_decision_mvp.py --source ../tep-python-candidate --step6-archive ../work/asset_recovery/TEP_step6_results_slack.zip --output research_runs/decision_mvp/run_20261024_v1` 실행. 기존 정적3개로 공통 grid/비용/목적 dry-run 추천 생성. 추천은 simulator 미적용. 같은 코드에서 잘못된 연구 환경 join 호출을 실제 거부하고 기록.
- Python 후보에서 사전 지정 baseline/+0.1pp(10초)·수동·IDV0·2seed·2반복·60step의8run 실행. v1 명목 격자를 보완하는 CLOCK_REVISION을 먼저 남긴 후 동일 조건의 v2 별도8run을 실행해 source 실제 평가/상태 시각을 기록했다. 총16run, 최종v2의8run은60step/명령반영/유한값/동일조건 raw byte exact. 시계 보완 외 조건 변경 없음, v1 보존. 기존 방정식 검산·12조건 진단 반복 아님.
- 미확정 X-Y를 비간선 정답으로 인정하지 않도록 파생 표시를 UNRESOLVED/null로 후처리 보완. 보완 전 파생 파일/원시 hash 보존, simulator 추가 실행·모델 추천 변경 없음. v2 실행 코드 hash는 후처리 보완 전 기록이며 현재 코드는 X-Y 처리 보완을 포함한다.
- causalAssembly 공식 commit8da3729의 실제 FCM 소스/README/pyproject와 참조/do/seed API를 읽고 기록. 헤더 AGPL-3.0-or-later, LICENSE URL404 확인. 외부 코드 Git 반입·환경 설치·runtime/생산 generator 실행/채택 없음. 기존 TEP GT 이식 없음.
- G1 BLOCKED/G2 PASS_TECHNICAL/G3 PARTIAL_TECHNICAL_ONLY/G4 NOT_RUN_RESEARCH/G5 BLOCKED. 실제 목표 달성·효과오차·Recovery/Safety·지표 상관/순위는 null. 기술 실행과 가설 검증을 분리. 상태 JSON/현재 MD와 우선순위를 ENV/POLICY/EVAL-MVP 중심으로 갱신. 과거 감사 validator의 고정 상위우선순위 검사는 과거 ID 보존 검사로만 변경하여 현재 우선순위 진화를 허용.
- 검증 통과: 단위 테스트23개, validate_decision_mvp.py(v1/v2 raw hash·시계·명령·반복·84행·재사용·Gate·성능null), Track A/B/REF-B·benchmark validators, graph39파일 hash/lag 재변환, PR integration, asset manifest, canonical 상태/문서 동기화, git diff --check. 16개 raw CSV 약0.93MB는 반복 증거로 보존하며 대용량 외부 데이터는 반입하지 않음.

## 2026-10-24 — ENV-MVP 승인된 예제 acceptance 실행

- git fetch/status: 사용자 변경 없음, PR6→7→8→9 OPEN/stacked·각 최신 CI 성공 확인. main7b16638은 유지하고 PR9 headbaf03e9에서 feature/env-mvp-acceptance 생성. 병합 없음.
- 사용자가 소규모 acceptance 실제 실행을 별도 승인했다. 제조 generator/R/DRF·학습·Track B 채택은 제외. 지정 archive04/로컬실행환경/.venv에 Python3.11 격리 venv 생성(시스템 site-packages false), numpy2.4.6/pandas3.0.3/sympy1.14.0/networkx3.6.1/scipy1.17.1/matplotlib3.11.2 설치. 전역 환경 변경 없음. 원시 설치/실행 console은 로컬 archive에 보존, Git에는 lock과 정제 기록만 반입.
- PLAN_v1을 실행 전에 고정하고 원본 hashc1f1b7f의 models_fcm.py만 직접 import했다. `격리python -X utf8 scripts/run_env_acceptance.py --module <고정 원본> --output research_runs/env_acceptance/run_20261024_v1 --execution-approved` 실행 성공. 원본 파일 수정·전체 package 설치·제조 generator 실행 없음.
- 선언4노드 IID Gaussian FCM의 adjacency/관측 재구성/do A식·부모 대체/원본 구조 보존을 실행 확인. 3seed×3조건×2회=18batch 각64행, hook 없는 원본API9통제 exact(총 sampler27회). train3101/holdout7101·7102 분리, 새seed관측 상이, 같은조건2회 data/noise CSV exact. 각 행 source 잡음으로 재구성 오차0. 이 표본 수는 검정력 근거 아님.
- 같은seed 관측vsdo의 u_R/u_M/u_Y는6비교 모두 행별 불일치, u_A 제거. 분포수준 do만 허용하며 strict counterfactual/물리 시계 검증 안 됨. Action A/Target Y는 무차원 fixture에만 해당. PR9 static_mean_response를 선언 oracle 산술 입력으로 재사용, 환경 guard는 fixture동일계약 수용/CPCaD혼합 거부 확인. 적합/추천 성능 결과 아님.
- 승인 flag 없는 negative CLI를 별도 실행해 PermissionError/exit1로 source 실행 전 거부된 FAILURE.json/source·plan SHA 보존. 정상 acceptance 예기치 않은 실패 없음. 단위 테스트26개 통과; 변조source 거부·잘못된 식 탐지·삭제된 noise 없는 do 재구성 포함.
- 예제 acceptance PASS_EXAMPLE_IID_FCM_ONLY, ENV-EXAMPLE VERIFIED, broader ENV-MVP PARTIAL로 기록. 제조/TrackB 채택·discovery/SCM 학습·Recovery/Safety 없음. 기존 CPCaD GT/frozenF1/적합/진단/과거MVP기록 불변. canonical JSON에서 상태 MD 재생성.
- 추가 검증 통과: validate_env_acceptance.py(저장된 graph/data/noise 식·do·seed/split·hash·negative guard), validate_decision_mvp.py, REF-B/TrackA/TrackB/benchmark validators, graph39파일 hash·lag변환, PR integration, asset manifest, 상태·문서 동기화, git diff --check. CI는 이 기록 검사와 로컬26단위 테스트만 수행하며 후보 실행을 반복하지 않는다.

## 2026-10-24 — 첫 번째 합성 통합 실험
- PR6~10 OPEN/stacked 및 각 최신 CI success 재확인. PR10 ee5e0bd에서 feature/first-integrated-pilot 생성. main/사용자 변경 덮어쓰기 없음.
- 사전 PLAN_v1 고정 후 fresh Gaussian/Uniform sampler·hard do acceptance 통과. 실제 PC-stable/BOSS/DirectLiNGAM 각2잡음군=6학습, train512/validation256, 공통 Ridge·목표1.5·비용0.2A²·5후보 추천을 holdout 전에 SHA 동결.
- 잡음군별 6정책(5후보+독립 기준)×3seed×1024=18432 do 표본 실제 생성. PC/BOSS 확정 경로 부재는 기준0 대체로 기록; Direct는 두군 모두0.5 추천. Gaussian Direct는 비정규성 가정 불일치 진단. Uniform BOSS 준Gaussian 점수 한계 포함.
- 새 격리환경 설치2회 실패 및3번째 성공 로그 보존. 같은 seed 전체 replay 데이터/모형/추천/평가/요약 exact, 독립 표본 수 추가하지 않음. 결과·코드·환경·source SHA와 원시 noise/CSV 보존.
- research_runs/first_integrated_pilot/ 및 한국어 FIRST_INTEGRATED_PILOT_REPORT.md 추가. 기존 src/decision_mvp.py 평균 전개와 pilot_fit.py fit_ridge 재사용, 기존 적합/7 frozen/Step6/TEP data/진단 log/RESEARCH_DESIGN.md 불변. 제조 채택·Recovery/Safety·가설 입증 없음.
- 실제 명령·실패 이력은 해당 README/SETUP_AND_EXECUTION.md. canonical 상태에서 PILOT-IID만 합성범위 VERIFIED; POLICY/EVAL-MVP는 PARTIAL로 업데이트하고 다음 독립 반복/과제 계약을 최우선으로 둔다.
- 최종 검사: 단위31개·신규 raw/통계/native그래프/추천 검증·기존8종 기록검사·39 graph hash·asset/PR 통합·상태/문서 동기화·diff 검사 통과. 하위 subprocess의 다른 Python 선택으로 난 NumPy 미설치 실패는 원시 로그 보존 후 실험 venv 명시 재검사로 해결했다. validation_results.json(첫 실패 요약)/validation_results_final.json(재검사)을 구분한다.

## 2026-10-24 — PR6~11 순차 통합과 반복·다중과제 실제 실행
- 사용자 명시 승인 범위 #6→#7→#8→#9→#10→#11만 최신 main retarget/차이 대조/CI·로컬검사 후 일반 merge. 원래 commit 계보 보존, 보호 설정·공개 여부 변경/강제 push 없음. merge커밋은 docs/research_design/PR6_11_INTEGRATION_RECORD.md 및 integration/merge_commits.json.
- 최종 main34b8dbe tree=원래 PR11 head6d37d09. 단위31·기록/해시/JSON-MD 검사와 main CI40093211965 success 후 로컬 main ff-only 동기화, feature/repeated-metric-pilot 생성. 첫 실험/TEP/frozen/Step6/fit/raw/RESEARCH_DESIGN.md 불변. 실제 local dataset·GT도 고정 원본 SHA 일치.
- 실행 전 PLAN_v1/SHA f04caba2 고정. 2잡음×2표본수(256/512)×3독립데이터×3알고리즘=36학습 실제 완료/실패0. 검증용 seed 별도; 새 API12조건에서 A/R/M do식 대체·hook 통제·정확 반복 확인.
- 4과제×3미확정 정책×36그래프=432추천 모두 SHA 동결 후 55296개 독립 do 표본 생성. 공통 action의 원시 평가를 재사용. 동치류는 skeleton/고정방향/비차폐 충돌/비순환을 보존, GT 없이 열거. 계산된0·경로부재 대체·모호성 보류를 구분.
- 새 실행 약42.523초, 학습 기록 합28.590초. 더 큰 반복/36graph 전체 replay NOT_RUN. 탐색적 Spearman은 사전 변동/cluster 조건에 맞는 층만 계산; LODO범위는 CI 아님. 조건별 독립데이터3개로 공식 지표 순위·p-value·Recovery/Safety 없음. 정책 변경 자체가 손실을 바꾸므로 구조 지표의 인과 효과로 주장하지 않음.
- 실제 명령은 research_runs/repeated_metric_pilot/README.md, 원시 log는 지정 아카이브 2026-10-24/06_순차통합과_반복다중과제에 보존. 신규 PLAN/run_v1/analysis_v1·한국어 보고서·검증코드와 canonical JSON/MD 동기화. 후속 PR은 승인 없이 병합하지 않음.
- 최종 검증: 단위39개, 새36학습/432추천/원시55296행·동치류/손실/통계/해시 및 기존 전종 기록 validators, graph39파일, 원본data/GT hash, 자산/PR통합, JSON→MD·문서 동기화, diff 검사를 모두 통과했다. 12학습CSV hash 모두 다름. 개인경로 미반입 확인. 추가 약15MB는 재사용 do 원시/noise와 모델/추천/분석 기록이며 평가를 그래프별 중복 생성하지 않았다.

## 2026-10-24 — 8개 합성 구조의 실제 비교
- PR12 OPEN/head23d19f5/CI40097602131 success와 clean 작업사본 확인 후 feature/diverse-causal-structures 분기. PR12·main 병합 없음. 연구 질문·TEP/GT/7frozen/Step6/적합/기존원시/첫·반복 실험은 불변.
- PLAN SHA0d010bf8를 실제 생성 전에 고정.5~8변수8개 DAG·모든계수·독립Uniform·양성16과제+음성1·48데이터 seed·144시도·3정책·구조 통째 제외 모형/정규화/한도를 사전 고정.
- S1/S2 source GT·관측/do 식/32표본·새seed/동일seed/hook 통제 통과 뒤 나머지6개 통과, 이후48관측학습/검증 생성. GT 없는 worker 설정과 해시로 PC/BOSS/Direct 실제144학습 완료. 실패/timeout/보조정책 제한0. 고정 모듈/기존 venv 재사용, 외부 source 패치/재설치 없음.
-918개 실제 discovery 정책 추천 및 별도60개 인위적 graph 모형/120추천을 동결한 뒤17고유Action×6조건×3seed×256=78336개 do 표본 생성/재사용. 원래 graph 점수는 정책별 고정, 통제오류 graph/음성대조는 일차 분석 제외.
-8fold LOSO의 imputation/scaling/손실 표준화는7훈련구조만 사용.14개 사전 모형/고정alpha로 계산, 새 결과를 본 뒤 지표나 설정 선택 없음. 경로단독 macroMAE .133671, 연결 .174327, 공변량 조정 후 연결 .147939/경로 .148120. 공식 우월성·p-value·독립 인과효과 주장 없음.
-방향/정규화SHD 상관-.978, 방향/경로 .901;112행렬 full rank/최대condition40.31은 수치 계산 가능성만 의미. Direct 내부경로 지표16과제 상수. 음성대조 baseline 평균구간은목표0 포함, 사전 수치cutoff 통과가 통계적 안정 보장 아님. 기본예측 outcome은 scale 정규화로 유지.
-전체 실행1001.555초.144학습 전체 replay NOT_RUN; API 반복과 모든 원시식/평균/SE/추천/손실/hash/LOSO분리 검증. 코드·도식·표·한국어 보고서 및 실제 명령은research_runs/diverse_structure_pilot와DIVERSE_STRUCTURE_PILOT_REPORT.md. 원시console는지정날짜아카이브07_다양한_인과구조_비교에만 보관.
- 단위49개와 모든 과학적/원시/고정추천/LOSO/기존자산 검사는 통과. 최초 staged diff형식 검사는 Matplotlib SVG의 자동 끝공백·console EOF빈줄로 실패했다. 최초전체로그/SHA를 보존하고 해당 생성SVG/console에만 whitespace 예외를 추가해 원시바이트/hash를 유지했다. 코드/문서 일반형식 검사는 그대로 적용한다.
- 한정된 생성파일 형식예외 적용 후 diff/cached-diff, raw/source/MEC/LOSO 해시 재검사, JSON-MD/문서동기화 재검사 모두 통과. 기존 과학적 검사49단위/전종validators 결과와 최초 형식실패를 별도 기록했다.

### 2026-10-24 — PR #13 clean-checkout CI correction
- First GitHub run 40102302710 failed: two original, SHA-listed PNG figures were excluded by the inherited `*.png` ignore rule. Local files existed, so the local validation had passed.
- Added only the two exact generated PNGs with `git add -f`; no sampling, graph, recommendation, analysis, or hash manifest changed. Research state and priorities are unchanged because this is packaging repair, not a new experiment.
- Preserve the failed CI record; rerun CI and verify the committed tree, rather than reporting the first run as passed.

## 2026-10-25 — 기존144회 실제 재현 + 12구조 독립 확인
- Base: unmerged PR13 a4ae769 above unmerged PR12; branch feature/independent-causal-confirmation. No merges; frozen TEP/Step6/data/fits/previous synthetic records/RESEARCH_DESIGN.md preserved.
- Re-executed original serial 144-learning/recommendation/do/LOSO code with identical installed lock and seeds into a separate archive directory. 672 records compared, scientific numeric difference0, discrete graph/action equality; runtime metadata excluded under prewritten 1e-9 numeric tolerance. Raw replay retained locally; Git stores compact logs/hash comparison without duplicate datasets.
- Before confirmation samples: executed exploratory reason/fixed-action/path-present/algorithm/overlap/incremental checks; fixed5 prediction models on S1..S8 only. Rule-generated12 structures,9 rejected candidates; PLAN c2efb756 and all primary analysis/runner code frozen before sampling. All12 external FCM observation/GT/do/noise/repeat controls passed.
- Actual216 learner calls generated216 graph records, but2 C12 PC outputs have directed cycles and SCM fit was refused. Source graphs preserved; no edge removal or loss imputation. Runner exit2 denotes COMPLETED_WITH_RECORDED_EXCEPTIONS. 214 SCMs usable;3 other PC graphs lack a consistent DAG extension for auxiliary policies. All5184 attempt rows retained:5088 EVALUATED,48 fit-failed,48 policy-blocked. Primary428 rows, actual do184320 samples, separate552 artificial models/1104 control rows.
- Locked primary M1-M2 deltaMAE .014264, structure bootstrap [.002912,.025278],9/12 favor M2; meets predeclared narrow endpoint. Increment beyond M0 (.004668) and beyond M1 (.000965) has intervals including0. Analytic-mean delta .006317 and cost.4 delta .004874 are unclear; do not claim stable incremental superiority or manufacturing validation.
- Fixed do(.5) prediction and path-retaining error contrasts executed; recommendation-selection artifact is not the sole pattern, but algorithm heterogeneity, selection, metric overlap and path-model constraints remain. No fitting on confirmation losses, posthoc clipping, graph repair, new seeds or outcome-based model selection.
- Added code, lossless compressed raw evidence, Korean report and canonical current state; generate status/priority MD from JSON. Old current 144-replay field updated with new evidence while original historical report/outputs remain untouched.
- Pre-sampling tests:54 pass+1 future stored-evidence skip; post-run evidence checks passed before and after528-file lossless compression. An optional system-interpreter check was blocked by missing NetworkX (actual pinned venv unaffected); NetworkX now declared for clean static CI. Initial publication scan found only NumPy wheel builder's path; sanitized metadata with original retained locally. No scientific data changed. Final full checks/CI are recorded with validation results and PR.

### 2026-10-25 — 완료 후 검증
- Pinned venv full55 unit tests passed (no final skips);22 local code/raw/hash/freeze/bootstrap/state/doc/privacy/table/protected-diff checks passed. Same-host replay144 is actually rerun; new216 second replay/other-OS training/manufacturing Recovery/Safety remain NOT_RUN.
- Primary model comparison is narrowly INDEPENDENT_SUPPORT, while broader incremental superiority remains unresolved. Two fit failures and three incompatible-MEC auxiliary blocks are explicit PARTIAL outcomes, not erased by validation PASS.
- Lossless528-record compression preserves both original and compressed SHA. No original TEP or prior run bytes changed. Optional system-interpreter rule check was blocked before sampling by missing NetworkX; clean static CI installs the declared dependency. NumPy wheel-builder metadata path sanitized and original retained locally.
- Staged diff check initially classified preserved CRLF endings in two new Windows-written scripts as trailing spaces because their executed bytes are marked -text. Added only cr-at-eol for those two files; source/plan hashes remain unchanged. Rechecked staged diff after this formatting-policy correction.


## 2026-10-25 — PR12~14 통합과 경로 지표 추가 정보

사용자의 이번3개 한정 검토 예외 승인 후 실제 diff·원시 기록·CI·39/49/55개 단위 검사를 검토하여 #12→#13→#14를 일반 병합했다. 별도 APPROVED 검토 생성 없음. merge94dab9b/5e78b98/e960fa8, main tree=검증 PR14 head. main CI40157415320 성공. 과거 결과·동결 파일 불변.

`run_path_incremental_development.py --output research_runs/path_metric_incremental_validation/development_v1` 및 `run_path_development_supplement.py --output .../development_supplement_v1` 실제 실행: 기존20구조/360graph/2160정책행의 이론 운영 손실, M0~M6 구조 LOSO, 과제 대조·정책·알고리즘·C07 분석. 실패24행은 실제 기준 조작 손실로 평가. M1→M4 .005200, M5→M6 .004642 모두 개발 구간0 포함. 새 독립 확인 정밀도150구조/1350학습 필요 추정으로 사전30/288 범위 초과하여 NOT_RUN. 확인 seed/구조를 만들지 않음.

`run_path_mc_calibration.py --source <verified pinned FCM> --output .../mc_calibration_v1` 실제 실행: 기존3구조 새18 do조건/69120유일표본 및69120재실행 exact 검산. C07 6조건은 상한8192에서도 목표 반폭 미달. 원시 표본/잡음 압축·계획/hash 보존. 제조 검증/새 발견학습 없음. 보고서: `docs/research_design/PATH_METRIC_INCREMENTAL_VALIDATION_REPORT.md`. 정밀도 차단을 성공으로 재분류하지 않음.


## 2026-10-25 — 오류 위치·효과 크기·실제 조작 선택

PR15 OPEN/e769ef5/CI40158875287 success/승인검토0 확인, 병합 안 함. 로컬 validate_path_metric_incremental 재실행PASS. 실무 RESEARCH_COMPASS와 CHECKPOINT 작성, 원 설계 보존. PLAN_v1/SHA 고정 후 `run_decision_reliability_next.py --output research_runs/decision_reliability_next/run_v1` 실제 실행: 기존통제1224행 추천 재계산,720발견행 평가,새C07 정답구조 Ridge6개 진단. 중첩 구조CV9후보 실행. 신규발견학습/do/제조운전0.

`summarize_decision_reliability_next.py --input .../run_v1 --output .../audit_supplement_v1`: 명칭중복108 표시 후324실제오류쌍,162현재과제핵심–주변/114양쪽경로유지쌍. C07 같은F1에서도 손실14.542543 대.36, C03은 핵심오류 쪽이 개선되는 반례. 기본정책720행 중 악화20/큰악화4. 저차원 중첩선택 기본19/경로1, MAE.323129. 추가정보 부호는 기준모형에 따라 상이, 정밀도 거친 추정132구조/1188학습으로 새독립확인NOT_RUN. 소스/계산/실제저장do 근거 분리. 개별5검사(원시/수식/중첩/6적합 재계산 포함)PASS. 제조 평가환경의 정합성 확보 우선, 새제조실험NO-GO 유지.

최종 로컬 검사: 65개 단위검사 PASS(89.755초),39개 동결파일 hash/변수/시차 변환 PASS,Step6 독립 점수 PASS,상태JSON/MD·자산manifest·기존 통합 검사 PASS. `research_runs/decision_reliability_next/validation/`에 실제 명령/로그/hash 보존.

실행/검증 코드 commit eb7f6bd,브랜치 feature/decision-reliability-next push 완료. PR16 생성(base=미병합PR15 브랜치);두PR 자동병합 없음. CHECKPOINT에 실행commit/의존PR/실제 검사 및 다음행동 기록. 새 문서 정리 commit은 실행/계획/SHA를 바꾸지 않는다.


## 2026-10-27 — 제조 타당성 Gate 감사

main e960fa8,PR15 OPEN/e769ef5,PR16 OPEN/d12c6be 및 clean 작업트리 재확인. feature/manufacturing-validity-gate를 PR16 head위에분기. 원설계/동결/원시불변.

`audit_manufacturing_validity.py --output research_runs/manufacturing_validity_gate/review_v4 --step6-zip <고정28824bc2 ZIP>` 실제성공:7graph/84과제/198쌍,원본평가기strict·기존10000draw21조건 재집계,자기상관·id/Boolean guard probe. CSV unnamed index포함/손실F1동률/과도한정밀도가정의3실패를review_v1~v3에보존. 정수TP유일복원으로원래baseline평균/p일치;원표변경없음. 회수평가기5d120b84와Finalfreeze c8af472a hash다름을scope명시. Python후보고정ZIP4source hash일치검산,새운전없음.

PC/BOSS1/12·Direct/DAGMA3/12확정경로;이는조건부기준대체진단이지12과제추천실행아님. Var의GT상비도달133중89도달로밀도위험확인. 현행guard는이름다르면차단하나동일이름+true이면metadata검사없이통과. 다음정확한작업은ENV-CONTRACT 구현제안. 직접제조가설A/B NO-GO,기술인터페이스만CONDITIONAL,권고D. 새발견/SCM/do/시뮬레이터/비선형 fitting0.

이번 로컬 검사15개 단위검사PASS,동결39파일/변수순서·엄격시차3개PASS,REF-B저장차분·시계/명령·TrackA/B/benchmark 및새histogram감사8개script검사PASS. 외부runtime시뮬레이터는실행하지않음. 개인경로·비밀/대용량검사·git diff --check 및기존동결/실험/원설계불변확인.

# 재현성 진단과 독립 확인 실험

이 폴더는 기존 PR #13을 수정하는 장소가 아니다. 기존 S1~S8은 탐색 자료, 새 C01~C12는 사전 규칙으로 생성한 확인 자료다. TEP 데이터·동결 그래프·Step 6·기존 적합과 합성 결과는 그대로 둔다.

## 먼저 읽을 파일

- `../../docs/research_design/INDEPENDENT_CONFIRMATION_REPORT.md`: 실제 결과와 한계를 설명한 한국어 보고서.
- `REPLAY_PLAN.json`, `REPLAY_COMPARISON.json`, `replay_evidence/`: 기존144회 전체 외부 학습·추천·do·분석의 실제 재실행 비교. 동일 seed 재실행을 새 독립 자료로 세지 않는다.
- `DIAGNOSTIC_GATE.json`, `exploratory_diagnostics_v1/`: 새 표본 생성 전 기존 자료만의 진단과 고정 예측모형5개.
- `PLAN_v1.json`, `FREEZE.json`, `generation_acceptance_records.json`: 생성 규칙·직접 간선·계수·seed·24개 기본 과제·4설정·분석·코드 해시. 채택12개와 기각9개 모두 기록한다.
- `run_v1/`: 실제 관측/잡음, 학습 원래 표현, 적합·공통 alpha, 추천 동결, 독립 do 및 실패 기록.
- `analysis_v1/`: 고정 모형의 외부 예측·구조별 차이·구조 bootstrap·고정 조작·알고리즘/정책/통제 오류·민감도·이론 검산.

## 저장 기록 검사

```powershell
python -m pip install -r requirements.txt
python -X utf8 scripts/validate_independent_confirmation.py
python -X utf8 -m unittest discover -s tests -v
python -X utf8 scripts/check_research_state.py
```

CI는 NumPy/Pandas/NetworkX의 가벼운 검사 환경에서 저장된 증거를 재계산한다. 외부 causal-learn/lingam/causalAssembly 학습을216회 다시 실행하는 검사가 아니다. 전체 학습은 아래 고정 실행 환경을 사용한다. 이 작업은 기존 격리 실행 환경을 재사용했으며 새 설치·새 OS의 전체 학습 재현은 별도로 주장하지 않는다.

## 실제 전체 재현 명령

저장소를 clone하고 이 feature 브랜치를 checkout한다. `environment.json`에 기록한 Python3.11.15와 원래 lock(NumPy1.26.4 포함)에 맞춘 별도 가상환경을 준비한다. Git 기본 검사 requirements의 NumPy2 범위를 외부 학습 lock과 혼동하지 않는다. 현재 작업에서는 이미 확보한 동일 가상환경과 고정 모듈을 재사용했다.

```powershell
python -m venv .venv-confirm
.\.venv-confirm\Scripts\python.exe -m pip install -r research_runs/diverse_structure_pilot/run_v1/requirements.lock.txt
New-Item -ItemType Directory -Force data/local/causalassembly
Invoke-WebRequest 'https://raw.githubusercontent.com/boschresearch/causalAssembly/8da3729e6383f0e1cbe7740bb6ab7ac4977ac7f9/causalAssembly/models_fcm.py' -OutFile data/local/causalassembly/models_fcm.py
Get-FileHash data/local/causalassembly/models_fcm.py -Algorithm SHA256

# 1. 원래 변경하지 않은 serial runner의 실제144학습 재현
.\.venv-confirm\Scripts\python.exe -X utf8 scripts/run_diverse_structure_pilot.py --module data/local/causalassembly/models_fcm.py --output data/local/confirmation_replay_a --raw-log-dir data/local/confirmation_replay_console_a
.\.venv-confirm\Scripts\python.exe -X utf8 scripts/analyze_diverse_structure_pilot.py --run data/local/confirmation_replay_a --output data/local/confirmation_replay_analysis_a
.\.venv-confirm\Scripts\python.exe -X utf8 scripts/check_confirmation_replay.py --replay data/local/confirmation_replay_a --analysis data/local/confirmation_replay_analysis_a --output data/local/replay_comparison_a.json
if ($LASTEXITCODE -ne 0) { throw '핵심 재현 실패: 다음 확인 실행 중단' }

# 2. 이미 사전 고정된 PLAN/models를 사용해 새 출력 위치에216회 재현
.\.venv-confirm\Scripts\python.exe -X utf8 scripts/run_independent_confirmation.py --module data/local/causalassembly/models_fcm.py --output data/local/independent_confirmation_a --raw-log-dir data/local/independent_console_a
.\.venv-confirm\Scripts\python.exe -X utf8 scripts/analyze_independent_confirmation.py --run data/local/independent_confirmation_a --output data/local/independent_analysis_a
```

기존 파일이 있는 출력 경로는 거부한다. 재현 결과로 이 폴더의 기존 run·계획·고정 모형을 덮어쓰지 않는다. `prepare_independent_confirmation.py`는 최초 동결용이며 기존 계획이 있으면 실행을 거부한다. 팀원이 계획을 다시 선택하거나 새 확인 결과를 보고 재학습하는 단계가 아니다. 새 모형·지표·seed 선택은 새로운 실험으로 구분해야 한다.

원본 모듈 SHA는 `c1f1b7f6b62c8916ebd23cb0002cdad1e9fcfb995b81cfae9558271987c4290e`이며 실행 전 실제 bytes를 검사한다. 모듈의 AGPL-3.0-or-later 헤더와 고정 공식 출처는 보존하고 원본을 이 저장소에 복사하지 않았다. 예제 FCM의 검증이며 제조 generator 전체의 보증이 아니다.

## 추천·독립 평가 계약

모든 확인용 데이터를 보기 전에 옛8구조만으로 M0~M4의 계수·결측 대체·표준화를 적합하고 고정했다. 새 구조에서 모형은 예측만 한다. 일차는 확정 간선 정책, 기본 직접/경로24과제, 5후보와 비용0.2이다. 9후보·비용0.1/0.4 및 동치류 최악 손실/불일치 보류는 사전 지정 보조 비교다. 모든 추천을 고정한 뒤9개 조작값+독립 기준 실행을 공유해 실제 do를 생성한다. 이론 평균은 그 뒤 검산용으로만 계산한다.

핵심 차이 ΔMAE=M1(기본 조건+연결 F1)−M2(기본 조건+경로). 구조별 오차에 동일 가중치를 준다. 최소0.01 개선과 구조 단위 재표본추출 하한>0을 함께 충족해야 사전 지지로 분류한다. −0.01 이하이고 상한<0이면 반대 증거, 그 외는 차이 불명확이다. 지표 변동·12구조/데이터 평가 조건을 충족하지 못하면 검증 불가다. 이는 예측 비교이지 지표를 개선하는 행위의 인과효과가 아니다.

원시 개입 표본, 반복 데이터, 알고리즘별 그래프 및 여러 과제를 독립 구조 수로 더하지 않는다. 구조군4개씩의 할당과 중복 기각, 옛 모형 불확실성 미포함, 계수·과제·변수 수의 전이, 알고리즘 가정/경로 규칙 차이를 제한으로 남긴다.

## 무손실 압축과 원본 해시

대형 새 JSON과 do/noise CSV는 개별 `.gz`로 저장한다. `run_v1/COMPRESSION.json`은 압축 전 이름·크기·SHA와 압축 파일 SHA를 기록한다. `run_v1/SHA256.json`은 원래 생성 바이트의 해시이며 검사기가 gzip을 풀어 원본 바이트를 대조한다. 로컬 아카이브에는 실행 console 원본을 보존하고 Git에는 경로를 정리한 console과 원본 해시만 남긴다. 동일 do 결과를 그래프마다 복제하지 않는다. 비교 CSV는 사람이 확인할 통합표이고 대형 후보/모형 JSON은 압축하여 중복 용량을 제한한다.

제조공정 고장·Recovery·Safety, 정규 잡음 보조 실험, 새216회 학습의 별도 두 번째 전체 재실행은 이번 완료 범위에 포함하지 않는다. 원래144회는 실제 재실행했으며 새216회는 최초 독립 실행 결과다.

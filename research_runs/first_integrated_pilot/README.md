# 첫 번째 통합 파일럿 — 서로 다른 두 인공 잡음 실험

[한국어 결과 보고서](../../docs/research_design/FIRST_INTEGRATED_PILOT_REPORT.md)를 먼저 읽는다. TEP 데이터·7개 frozen graph·물리 제조 generator의 재현 결과가 아니다. 사용자가 이번 실행을 명시적으로 지시한 범위에서 실제 학습·추천·독립 do 평가를 실행했다.

- `PLAN_v1.json`: 결과 확인 전에 고정한 표본 수·seed·가정·목표·비용·실패 정책.
- `run_v1/gaussian/`, `run_v1/uniform/`: 실제 관측/noise, 학습 native/확정/미확정 그래프, 새 Ridge 모형, alpha 선택, 동결 추천, 후보별 독립 do/noise, 평가 통계.
- `run_v1/summary.csv` 및 `.json`: 그래프/과제 한 행 요약. 직접 A→Y와 간접 도달성은 별도 열이다. 미확정/기준 대체 정책을 포함한다.
- `run_v1/SHA256.json`, `environment.json`, `execution_ledger.json`, `requirements.lock.txt`: 원시 기록 무결성·정확한 환경·실제 단계 순서. 제조/반사실 평가 결과가 아니다.
- `reproducibility_check.json`: 동일 seed 전체 재실행 비교. 새 독립 그래프나 관측 실험으로 세지 않는다. 라이브러리의 ground_truth 반환값도 두 잡음군에서 추가 대조했다.
- `SETUP_AND_EXECUTION.md`: 실패한 설치 두 건과 실제 성공 명령, 원시 console의 해시.

## 팀원 재실행 (PowerShell, Python 3.11)

저장소 루트에서 다음과 같이 별도 환경을 생성한다. 기존 기본 requirements나 과거 fit을 덮어쓰지 않는다. 전체 제조 package/R/DRF는 필요 없다. `semopy==2.3.11`은 설치 과정에서 순수 Python wheel을 만들었다.

```powershell
python -m venv .venv-integrated
.\.venv-integrated\Scripts\python.exe -m pip install --only-binary=numpy,scipy,pandas,scikit-learn,matplotlib numpy==1.26.4 pandas==2.2.3 scipy==1.12.0 matplotlib==3.9.2 sympy==1.14.0 networkx==3.6.1 causal-learn==0.1.4.8 lingam==1.13.0 semopy==2.3.11
# 최초 확인 환경의 전체 간접 의존성까지 고정하려면 다음 lock을 사용한다.
.\.venv-integrated\Scripts\python.exe -m pip install -r research_runs/first_integrated_pilot/run_v1/requirements.lock.txt
New-Item -ItemType Directory -Force data/local/causalassembly
Invoke-WebRequest 'https://raw.githubusercontent.com/boschresearch/causalAssembly/8da3729e6383f0e1cbe7740bb6ab7ac4977ac7f9/causalAssembly/models_fcm.py' -OutFile data/local/causalassembly/models_fcm.py
Get-FileHash data/local/causalassembly/models_fcm.py -Algorithm SHA256
$env:MPLBACKEND='Agg'
.\.venv-integrated\Scripts\python.exe -X utf8 scripts/run_first_integrated_pilot.py --module data/local/causalassembly/models_fcm.py --output research_runs/first_integrated_pilot/local_replay_1
.\.venv-integrated\Scripts\python.exe -X utf8 scripts/check_first_pilot_replay.py --module data/local/causalassembly/models_fcm.py --replay research_runs/first_integrated_pilot/local_replay_1 --record data/local/first_pilot_replay_check.json
```

소스 hash는 `c1f1b7f6b62c8916ebd23cb0002cdad1e9fcfb995b81cfae9558271987c4290e`와 같아야 한다. 다르면 adapter가 거부한다. 원본 모듈의 AGPL-3.0-or-later와 upstream 고지를 확인한다. 이 저장소는 upstream 코드를 vendor하지 않는다.

`run_v1`은 덮어쓸 수 없으며 runner는 기존 출력 경로를 거부한다. 재실행은 다른 경로에서 수행한다. Linux·다른 BLAS에서 비트 단위 수치 동일성은 보장하지 않으며 차이가 있으면 새 결과로 기록한다. 같은 seed 재실행이 다른 독립 표본이라는 뜻은 아니다.

## 외부 소스 없이 기록 검증

```powershell
python -X utf8 scripts/validate_first_integrated_pilot.py
python -X utf8 -m unittest discover -s tests -v
python -X utf8 scripts/check_research_state.py
```

CI는 기록과 계산을 검사한다. 실제 학습/샘플 생성은 위 격리 환경 명령으로 별도 재현한다. 정규 Direct는 가정 불일치 진단, Uniform BOSS는 Gaussian 준점수 한계를 지닌다. Recovery/Safety·상관계수·p-value는 없다.

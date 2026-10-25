# 8개 구조에서 그래프 품질과 추천 성능 비교

[한국어 연구 보고서](../../docs/research_design/DIVERSE_STRUCTURE_PILOT_REPORT.md)

PR #12의 4변수 실험과 다른 신규 실행이다. PR #12가 OPEN인 상태에서 head `23d19f5` 위에 `feature/diverse-causal-structures`를 만들었다. 사용자 승인 없이 PR #12나 이 후속 PR을 병합하지 않는다. TEP/Step6/과거 실험/RESEARCH_DESIGN.md는 변경하지 않는다.

## 무엇을 어디서 확인하는가

- `PLAN_v1.json`: source/8개 수식·계수/48개 새 학습 데이터/17과제/144회 학습 시도/정책/seed/손실·분석·한도 사전 계약.
- `reference_graphs_v1/`: 실제 FCM 반환 GT와 대조한 참조 인접·계수 행렬 및 식/과제. 행=원인, 열=결과. **선언된 합성 참조**이며 TEP의 GT가 아니다.
- `figures_v1/`: 조밀한 그래프의 겹치는 간선을 읽기 쉽게 배치한 그림. 초기 도식도 보존하고 수식/데이터는 바꾸지 않았다.
- `run_v1/acceptance/`: 첫2개→나머지6개 순서의 실제 source GT/관측/do·잡음·seed 반복·hook 없는 통제.
- `run_v1/datasets/`: 실제 학습/검증 CSV+noise, GT가 없는 알고리즘 설정, native/확정/미확정 그래프, solver/모형·worker console.
- `run_v1/recommendations_frozen.json`: 전체 알고리즘·과제·3정책의 추천. 모든 최종 개입 평가 전에 SHA로 동결했다.
- `run_v1/controlled_recommendations_frozen.json`: 명시적으로 인위적 오류를 넣은 별도 실험. 실제 알고리즘이 발견한 그래프가 아니다.
- `run_v1/do_evaluation/`: 구조/조작/후보별 독립 do 원시 표본·noise. 같은 action/값을 고른 모델들은 이 결과를 공유한다.
- `run_v1/comparison.*`: 미실행/실패/정책 제한도 포함하는 전체 시도 행. `EVALUATED`만 실제 성능 수치를 가진다.
- `run_v1/controlled_comparison.*`: 보조 오류 실험. 일차 구조 지표 분석에서 제외한다.
- `analysis_v1/`: 구조·과제·알고리즘·정책별 결과, metric 중복, 구조 통째 제외(LOSO) 예측 및 train-only 변환·rank 기록.

모든 결과는 독립 Uniform 오차의 선형 가산 DAG이며 관측 변수를 빠뜨리지 않았다. DirectLiNGAM 가정에 맞는 생성 조건을 썼지만 BOSS의 Gaussian BIC가 해당 잡음의 정확한 우도라는 뜻은 아니다. PC/CPDAG의 방향 미확정과 방향 오류도 구분한다.

## 환경과 실제 재현 명령

별도 Python3.11 환경에서 실행한다. 전체 causalAssembly 제조 package/R/DRF는 필요 없다. upstream `models_fcm.py`는 고정 commit 원본이며 AGPL-3.0-or-later 고지를 확인해 별도 취득한다. venv나 upstream source를 이 저장소에 복사하지 않는다.

```powershell
python -m venv .venv-diverse
.\.venv-diverse\Scripts\python.exe -m pip install -r research_runs/diverse_structure_pilot/run_v1/requirements.lock.txt
New-Item -ItemType Directory -Force data/local/causalassembly
Invoke-WebRequest 'https://raw.githubusercontent.com/boschresearch/causalAssembly/8da3729e6383f0e1cbe7740bb6ab7ac4977ac7f9/causalAssembly/models_fcm.py' -OutFile data/local/causalassembly/models_fcm.py
Get-FileHash data/local/causalassembly/models_fcm.py -Algorithm SHA256
$env:MPLBACKEND='Agg'
.\.venv-diverse\Scripts\python.exe -X utf8 scripts/run_diverse_structure_pilot.py --module data/local/causalassembly/models_fcm.py --output data/local/diverse_replay_1 --raw-log-dir data/local/diverse_replay_1_console
.\.venv-diverse\Scripts\python.exe -X utf8 scripts/analyze_diverse_structure_pilot.py --run data/local/diverse_replay_1 --output data/local/diverse_analysis_replay_1
```

원본 모듈 SHA는 `c1f1b7f6b62c8916ebd23cb0002cdad1e9fcfb995b81cfae9558271987c4290e`다. 다르면 실행을 거부한다. 같은 이름의 결과/원시 console 디렉터리가 이미 있으면 덮어쓰지 않는다. 새 이름을 사용한다. 전체 재실행은 기존144개 학습과 다른 독립 표본 수로 세지 않으며, 시간/OS/BLAS 차이의 비트 일치를 보장하지 않는다. 재현 실행은 무시된 `data/local/` 아래에 두어 기존 동결 결과를 변경하지 않는다.

학습은 알고리즘마다 별도 worker에서 실행한다. worker 설정의 허용 키는 알고리즘·seed·열 순서·라이브러리 설정·학습 CSV hash뿐이며 GT·계수·과제를 포함하지 않는다. 시도당180초 한도와 실제 실패를 기록한다. 추천·SCM에는 공통 alpha 선택/같은 학습 CSV를 적용한다. 보조 동치류 정책은 미확정12쌍 또는 일관된 DAG128개를 넘으면 `POLICY_BLOCKED`로 남긴다. 처음128개만 고르거나 GT에 맞는 방향을 선택하지 않는다.

## 저장 기록 검사와 실제 실행의 차이

```powershell
python -X utf8 scripts/validate_diverse_structure_pilot.py
python -X utf8 -m unittest discover -s tests -v
python -X utf8 scripts/check_research_state.py
git diff --check
```

CI는 외부 후보를 설치해144개 알고리즘을 다시 학습하지 않는다. 저장된 source·plan·code·data 해시, 실제 원시 식, 추천 재계산·통계·손실, no-GT worker 설정 및 LOSO 구조 단위 분리를 검사한다. 실제 학습 반복 여부와 CI 기록 검사를 구분한다.

## 해석 계약

- 일차: 실제 discovery 결과·양성16과제·확정 간선 정책. 음성 대조1개와 controlled 오류 그래프는 별도 진단.
- LOSO: 한 구조의 모든 데이터·알고리즘·과제를 함께 제외한다. feature 결측 대체·표준화·결과 표준화는 나머지7개 구조에서만 fit한다. metric/alpha/모형을 평가 구조의 성능을 보고 고르지 않는다.
- 독립 단위: 손으로 고정한8개 구조,48개 독립 학습 데이터. 알고리즘144개·과제·정책·평가 표본을 독립 N으로 세지 않는다.
- 상대 regret는 기준 손실이 과제 scale²의1%보다 작으면 null로 기록한다. 구조 간 일차 예측은 안정적인 `regret/scale²`를 사용한다. 기준이 이미 최선에 가까운 경우의 개선율도 별도로 제한한다.
- `relative_regret_status=STABLE`은 사전 수치 하한 통과만 뜻한다. 평균의 신뢰구간이나 참분모의 안정성을 보증하지 않는다. 이번 음성 대조에서는 참기준 평균이0이고 평균 구간이목표0을 포함해도 표본 분모가 하한을 조금 넘었다. 결과를 보고 하한을 바꾸지 않았으며 음성 대조는 일차 분석에서 제외했다.
- 핵심 경로 지표와 경로 없을 때의 기준값 대체는 추천 규칙으로 기계적으로 연결된다. 이를 새 인과 효과로 해석하지 않는다.
- 8개 손설계 구조의 예측 비교는 탐색적이다. 공식 지표 우월성·계수의 독립 인과 효과·제조 Recovery/Safety를 주장하지 않는다.

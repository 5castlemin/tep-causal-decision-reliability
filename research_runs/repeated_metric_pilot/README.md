# 반복 학습·다중 과제 합성 파일럿

[결과 보고서](../../docs/research_design/REPEATED_METRIC_PILOT_REPORT.md) / [선행 PR 통합 기록](../../docs/research_design/PR6_11_INTEGRATION_RECORD.md)

새 실험만 저장한다. 첫 통합 실험·TEP frozen·Step 6·기존 fit은 재생성하지 않았다. 사전 고정한 12개 독립 관측 데이터에서 36개 그래프를 실제 학습하고, 4과제×3정책=432행을 같은 환경의 독립 do로 평가했다. 독립 graph-fit 단위는 12개이며 outcome 행수/rollout 수와 다르다.

- `PLAN_v1.json`: 새 seed·표본 수·설정·과제·미확정 정책·분석 가능 조건을 생성 전에 고정.
- `integration/`: 사용자 승인 PR6→11의 merge 계보와 실제 로컬/CI/원본 보존 검사. main34b8dbe에서 분기.
- `run_v1/datasets/`: 원시 관측/잡음·36개 native 그래프·확정/미확정 쌍·같은 alpha의 기본/동치류 모형.
- `run_v1/api_acceptance/`: A/R/M do의 실제 식 대체·반복·hook 통제.
- `run_v1/recommendations_frozen.json`: holdout 생성 전에 저장한 모든 추천과 후보 목적값.
- `run_v1/do_evaluation/`: 같은 조작값을 모든 그래프/과제가 공유하는 원시 표본/noise. 별도 기준 정책 seed.
- `run_v1/comparison.csv`: 구조 지표·추천 상태·실제 평균/SE/CI·효과/손실/비용/상대 손실의 432행.
- `run_v1/exploratory_associations.*`: 연관을 계산할 수 없는 층도 이유와 함께 기록. LODO는 데이터 cluster 단위 제외 민감도이며 CI가 아님.
- `analysis_v1/`: 균형 요약표·정책 차이·경로 그룹 기술통계·계산시간. 학습이나 추천을 바꾸지 않은 후처리.

## 별도 환경에서 전체 재현

Python3.11, 저장소 루트 PowerShell에서 실행한다. 첫 실험과 동일한 검증된 lock이 새 실행에도 기록되어 있다. 외부 모듈은 AGPL-3.0-or-later 고지를 확인하고 별도 취득한다. 전체 causalAssembly 제조 package/R/DRF는 설치하지 않는다.

```powershell
python -m venv .venv-repeated
.\.venv-repeated\Scripts\python.exe -m pip install -r research_runs/repeated_metric_pilot/run_v1/requirements.lock.txt
New-Item -ItemType Directory -Force data/local/causalassembly
Invoke-WebRequest 'https://raw.githubusercontent.com/boschresearch/causalAssembly/8da3729e6383f0e1cbe7740bb6ab7ac4977ac7f9/causalAssembly/models_fcm.py' -OutFile data/local/causalassembly/models_fcm.py
Get-FileHash data/local/causalassembly/models_fcm.py -Algorithm SHA256
$env:MPLBACKEND='Agg'
.\.venv-repeated\Scripts\python.exe -X utf8 scripts/run_repeated_metric_pilot.py --module data/local/causalassembly/models_fcm.py --output research_runs/repeated_metric_pilot/local_replay_1
```

모듈 SHA는 `c1f1b7f6b62c8916ebd23cb0002cdad1e9fcfb995b81cfae9558271987c4290e`다. 다른 바이트는 실행 전에 거부한다. 기존 출력 경로는 덮어쓸 수 없다. 재실행은 새로운 이름을 쓰고 반복을 독립 데이터로 세지 않는다. OS/BLAS 차이의 비트 일치는 보장하지 않는다. 이번에는 API 정확 반복을 실제 확인했으며 36개 학습 전체 replay는 실행하지 않았다.

## 외부 모듈 없이 저장 기록 검증

```powershell
python -X utf8 scripts/validate_repeated_metric_pilot.py
python -X utf8 -m unittest discover -s tests -v
python -X utf8 scripts/check_research_state.py
git diff --check
```

기본 requirements 환경은 CI 기록 검사에 쓰고, 실제 discovery 재실행은 별도 lock 환경을 쓴다. NumPy2로 기존 환경을 임의 변경하거나 TEP 적합을 다시 실행하지 않는다. source/code/data의 정확한 해시와 UTC 실행 순서는 `environment.json`/`SHA256.json`/`execution_ledger.json`에 있다. 원시 console은 개인 경로를 포함하므로 지정 아카이브에만 보관한다.

정규 Direct의 가정 불일치, Uniform BOSS의 Gaussian 준점수, CPDAG/DAG 차이를 유지한다. 정책 대체/계산된0/불일치 보류를 같은 추천 성공으로 세지 않는다. 새 제조 환경 채택·Recovery/Safety·지표의 인과 효과 입증은 없다. 새 PR은 추가 승인 전 병합하지 않는다.

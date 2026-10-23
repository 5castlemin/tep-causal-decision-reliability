# 팀원용 연구 자산 재현 가이드

이번 버전은 데이터 취득·Final 산출물 검사·원본 평가기 재현을 지원한다. **7개 인과발견 알고리즘의 Final 생성 재실행은 아직 지원하지 않는다.** 원본 생성 코드의 해시는 있으나 해당 바이트가 없다. `GRAPH_REPRODUCIBILITY.json`의 `generation_status`와 `command=null`을 확인한다.

## 1. 저장소와 환경

```powershell
git clone https://github.com/5castlemin/tep-causal-decision-reliability.git
cd tep-causal-decision-reliability
# 승인된 통합 후 최신 main 사용
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Windows 명령 예시다. Linux에서는 `.venv/bin/python`을 사용한다. requirements 범위 설치와 실제 깨끗한 venv 검증 버전은 `validation/clean_environment.json`에 기록했다. 이 환경이 2026-10-05 discovery 환경과 같다는 뜻은 아니다.

## 2. 원본 데이터 취득

원저장소를 작업 저장소 밖에 clone한다. 데이터 재배포 권리를 확정하지 못해 CSV/GT 바이트는 Git에 포함하지 않는다.

```powershell
git clone https://github.com/giovanniMen/CPCaD-Bench.git ../CPCaD-Bench
.\.venv\Scripts\python.exe -X utf8 src/acquire_reference_data.py --source-git ../CPCaD-Bench
```

이 명령은 commit `72b0f5e3d14192478186ee0dc4338b7448087789`에서 두 파일을 읽고 SHA-256을 검증한다. 개인 PC 경로·ZIP 세트가 필요하지 않으며 다른 내용의 기존 파일은 덮어쓰지 않는다. 원저장소 접근 실패 시 네트워크/권한 문제를 그대로 기록한다. `data/local/`은 Git 제외다.

## 3. Final 7개 및 결과표 확인

```powershell
.\.venv\Scripts\python.exe -X utf8 graphs/final/verify_and_load.py
```

39개 frozen 파일·변수 순서·시계열 3개 lag→static 변환을 검증한다. `docs/audit/step6_main_table.csv`는 기존 Initial/Final 결과다. 이 과정은 discovery 학습을 다시 수행하지 않는다.

## 4. 회수한 원본 평가기로 결과 비교

Slack [Step 6 공유](https://hufsdat.slack.com/archives/C0BL2A769MJ/p1791197012282929)에서 `TEP_step6_results.zip` (`F0C6TP4168H`) 원본을 다운로드하여 저장소 밖에 둔다. 이번 실제 Slack 다운로드 바이트는 로컬 기존 ZIP과 동일한 SHA `28824bc2a98acb77ce8fc5f56439ea4910f7dc9f22ed45b7d1391f7f703f6b22`였다. 서명된 임시 다운로드 URL은 저장하지 않는다. 새 팀원도 Slack/로컬 원본 접근 권한이 필요하며, 해당 접근 권한을 GitHub가 제공하지는 않는다.

```powershell
.\.venv\Scripts\python.exe -X utf8 src/reproduce_step6.py --step6-zip ../TEP_step6_results.zip --output ../my_step6_check.json
```

어댑터는 ZIP 전체와 `evaluation/evaluator.py`의 바이트 해시를 확인한 뒤 실제 원본 평가 함수를 호출한다. 원본의 누락된 `common/config.py`를 복원했다고 주장하지 않는다. 새 어댑터가 변수 순서와 빈 control pair 목록을 명시적으로 공급하며 **strict Skeleton F1/Directed F1/SHD만 비교**한다. U규칙·무작위 기준선 10,000회·전체 Initial/sensitivity 실행은 재현하지 않는다. GT는 평가에만 사용하며 graph를 수정하지 않는다. 원본 코드 바이트는 권리 범위가 불명확해 Git에 재배포하지 않고 승인된 입력 ZIP 안에서만 읽는다.

## 5. 알고리즘 생성 재현의 현재 한계

| 알고리즘 | frozen 산출물·config | 생성 코드 | 실행/동일성 |
|---|---|---|---|
| PC-stable | 있음 | `algos/run_pc.py` 미회수 | BLOCKED |
| BOSS | 있음 | `algos/run_boss.py` 미회수 | BLOCKED |
| DirectLiNGAM | 있음 | `algos/run_b_retune.py` 미회수 | BLOCKED |
| DAGMA | 있음 | `algos/run_b_retune.py` 미회수 | BLOCKED |
| PCMCI+ | 있음 | `algos/run_pcmciplus.py` 미회수 | BLOCKED |
| VarLiNGAM | 있음 | `algos/run_varlingam.py` 미회수 | BLOCKED |
| DYNOTEARS | 있음 | `algos/run_dynotears.py` 미회수 | BLOCKED |

`GRAPH_REPRODUCIBILITY.json`에 요구 코드 hash, 실제 config, seed/restart의 확인·미확인 값, freeze의 라이브러리 버전, 데이터 hash를 보존했다. 완전한 lockfile 및 실행 명령은 미확보다. PC/BOSS의 9월 Colab은 Final과 설정이 다르며 원본 다운로드도 로그인으로 차단됐다. 코드가 회수되면 freeze hash 일치→권리/환경 확인→새 출력 경로 실행→frozen 배열 비교 순서로 진행한다. 설정만 보고 과거 코드를 새로 만들거나 GT 점수로 재튜닝하지 않는다.

## 6. 작업 기록과 PR

```powershell
git switch -c feature/my-research-task
# 실제 작업과 검증 후 docs/research_state.json 수정
.\.venv\Scripts\python.exe -X utf8 scripts/check_research_state.py --write
.\.venv\Scripts\python.exe -X utf8 scripts/check_research_state.py
.\.venv\Scripts\python.exe -X utf8 scripts/check_asset_manifest.py
.\.venv\Scripts\python.exe -X utf8 -m unittest discover -s tests -v
```

WORK_LOG에 명령·hash·결과·실패/미실행을 추가한다. PROJECT_STATUS/PRIORITIES는 JSON에서 생성한 최신 상단 표를 유지한다. 코드·문서 검토 후 feature branch commit/push하고 PR을 제출한다. main 직접 push·자동 병합은 금지다. CI는 기록 일관성만 검사하며 실험 성공을 보증하지 않는다.

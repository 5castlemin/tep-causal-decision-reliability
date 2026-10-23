# TEP 인과구조와 공정 의사결정의 신뢰성

추정 인과그래프의 어떤 구조적 정확도가 실제 공정 개입의 효과·복구·안전 성능을 설명하는지 검증하기 위한 협업 저장소다. **현재는 구조 평가를 복원했고 정적 그래프 3개의 정상 관측 데이터 수치 적합만 파일럿으로 수행했다. 실제 시뮬레이터 개입 결과는 없다.**

처음 합류했다면 [팀 소개](introduction.md) → [현재 상태](PROJECT_STATUS.md) → [연구 설계](RESEARCH_DESIGN.md) → [파일럿 계획](PILOT_PLAN.md) 순서로 읽는다.

실무 순서는 [우선순위](PRIORITIES.md), [작업 기록](WORK_LOG.md), [협업 규칙](AGENTS.md)을 따른다. Slack의 파일 목록과 실제 반입 여부는 [자산 감사](docs/audit/SLACK_ASSET_REGISTER.md)에 구분했다.

## 빠른 시작

Python 3.11+와 `numpy`, `pandas`가 필요하다. 원본 CPCaD-Bench의 Git 커밋과 검증된 ZIP 세트가 있는 환경에서만 로컬 입력을 준비한다. 입력 ZIP과 기존 저장소는 수정하지 않는다.

데이터·GT만 필요하면 공개 CPCaD-Bench checkout을 준비한 후 다음 명령을 사용한다. 해시 검증 후 Git 제외된 로컬 폴더에만 쓰며 기존 다른 내용은 덮어쓰지 않는다. 원본 재배포 권리가 명확하지 않아 데이터 바이트는 이 저장소에 포함하지 않았다.

```powershell
python -X utf8 src/acquire_reference_data.py --source-git <CPCaD-Bench Git 경로>
```

```powershell
python -m pip install -r requirements.txt
python src/prepare_local_inputs.py --source-git <CPCaD-Bench 경로> --graph-zip <TEP_final_graphs_v1.zip 경로> --step6-zip <TEP_step6_results.zip 경로> --task-dir <pre_scm_task_selection_v1_1 경로> --freeze-dir <pre_scm_final_freeze 경로>
python -X utf8 graphs/final/verify_and_load.py
python -X utf8 src/verify_recovery.py
python -X utf8 -m unittest discover -s tests -v
python -X utf8 tests/smoke/check_simulator.py --output experiments/pilot/logs/simulator_smoke.json
python -X utf8 src/pilot_fit.py
```

`check_simulator.py`는 실제 소스 경로를 전달하지 않으면 의도적으로 `BLOCKED`를 기록한다. `pilot_fit.py`의 결과는 관측 부모를 이용한 정상 상태 one-step 예측 진단이며 인과효과 검증이 아니다. 원자료의 자동 검색이나 임의 시뮬레이터 설치는 하지 않는다.

## 폴더

- `graphs/final/`: 원본 ZIP에서 검증 후 가져온 7개 최종 그래프·설정·기존 검증기
- `docs/audit/`: 원본 목록, 충돌·공백, 고정된 학습 정책, 기존 Step 6 최종 결과표
- `docs/tasks/`: 12개 **구조 평가 후보**와 선정 고정 기록
- `data/local/`: 해시 검증된 데이터·GT의 로컬 작업 사본. Git에서 제외
- `src/`, `tests/`: 독립 검증과 최소 정상상태 적합 코드
- `experiments/pilot/`: Gate 상태, 수치 진단 요약, 실제 시뮬레이터가 생겼을 때의 검증 자리

원본 자료의 출처와 해시는 [산출물 목록](docs/audit/ARTIFACT_INVENTORY.md)에 있다. 팀원 초대와 브랜치 규칙은 [기여 안내](CONTRIBUTING.md), [협업자 설정](COLLABORATOR_SETUP.md)을 참고한다.

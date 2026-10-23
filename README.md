# TEP 인과구조와 공정 의사결정의 신뢰성

추정 인과그래프의 어떤 구조적 정확도가 실제 공정 개입의 효과·복구·안전 성능을 설명하는지 검증하기 위한 협업 저장소다. **구조 평가를 복원했고 정적 그래프 3개의 정상 관측 수치 적합 및 공개 시뮬레이터의 제한된 개입 smoke를 수행했다. 독립 Recovery/Safety 검증은 미수행이다.**

처음 합류했다면 [팀 소개](introduction.md) → [현재 상태](PROJECT_STATUS.md) → [연구 설계](RESEARCH_DESIGN.md) → [파일럿 계획](PILOT_PLAN.md) 순서로 읽는다.

실무 순서는 [우선순위](PRIORITIES.md), [작업 기록](WORK_LOG.md), [협업 규칙](AGENTS.md)을 따른다. Slack의 파일 목록과 실제 반입 여부는 [자산 감사](docs/audit/SLACK_ASSET_REGISTER.md)에 구분했다.

## 빠른 시작

실제 단계별 명령과 미완료 범위는 [팀 재현 가이드](docs/reproducibility/TEAM_GUIDE.md)를 따른다. Python 환경 생성 후 공개 원본 저장소를 별도 clone하여 고정 커밋의 데이터·GT만 취득한다. 데이터 바이트와 ZIP 전체는 Git에 포함하지 않는다.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
git clone https://github.com/giovanniMen/CPCaD-Bench.git ../CPCaD-Bench
.\.venv\Scripts\python.exe -X utf8 src/acquire_reference_data.py --source-git ../CPCaD-Bench
.\.venv\Scripts\python.exe -X utf8 graphs/final/verify_and_load.py
.\.venv\Scripts\python.exe -X utf8 scripts/check_asset_manifest.py
.\.venv\Scripts\python.exe -X utf8 -m unittest discover -s tests -v
```

회수한 Step 6 ZIP을 제공하면 `src/reproduce_step6.py`로 **원본 strict 평가 함수의 결과**를 비교할 수 있다. ZIP hash·출처·실제 검증 결과는 [복원 보고서](docs/reproducibility/ASSET_RECOVERY_REPORT.md)에 있다. Final 7개 생성 학습 코드는 아직 없어 인과발견 재실행은 BLOCKED다. 설정과 과거 코드로 이를 대신 재구성하지 않는다.

[PR #2](https://github.com/5castlemin/tep-causal-decision-reliability/pull/2)의 공개 simulator는 정상 30분 반복·쓰기·Fault smoke만 부분 통과했다. PR #2는 사용자 승인 후 병합했으며, 동일 객체 reset과 수치·기존 데이터 호환성 문제가 남아 있다. 기존 8월 구현 회수 BLOCKED와 구분한다.

## 폴더

- `graphs/final/`: 원본 ZIP에서 검증 후 가져온 7개 최종 그래프·설정·기존 검증기
- `docs/audit/`: 원본 목록, 충돌·공백, 고정된 학습 정책, 기존 Step 6 최종 결과표
- `docs/tasks/`: 12개 **구조 평가 후보**와 선정 고정 기록
- `data/local/`: 해시 검증된 데이터·GT의 로컬 작업 사본. Git에서 제외
- `src/`, `tests/`: 독립 검증과 최소 정상상태 적합 코드
- `experiments/pilot/`: Gate 상태, 수치 진단 요약, 실제 시뮬레이터가 생겼을 때의 검증 자리

원본 자료의 출처와 해시는 [산출물 목록](docs/audit/ARTIFACT_INVENTORY.md)에 있다. 팀원 초대와 브랜치 규칙은 [기여 안내](CONTRIBUTING.md), [협업자 설정](COLLABORATOR_SETUP.md)을 참고한다.

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

[PR #2](https://github.com/5castlemin/tep-causal-decision-reliability/pull/2)의 공개 simulator는 정상 30분 반복·쓰기·Fault smoke만 부분 통과했다. PR #2는 사용자 승인 후 병합했으며, 후속 [신뢰성 검증](docs/audit/SIMULATOR_RELIABILITY_REPORT.md)에서 2시간 정상 운전, 압력 한계 종료, 새 객체 초기화 계약을 확인했다. 같은 객체 reset은 비트 일치를 보장하지 않으며 수치 기준·기존 데이터 호환성은 여전히 미완료다. 후보 내부 탐색은 조건부이고 기존 데이터의 효과 정답 직접 사용은 보류한다. 기존 8월 구현 회수 BLOCKED와 구분한다.

## 폴더

- `graphs/final/`: 원본 ZIP에서 검증 후 가져온 7개 최종 그래프·설정·기존 검증기
- `docs/audit/`: 원본 목록, 충돌·공백, 고정된 학습 정책, 기존 Step 6 최종 결과표
- `docs/tasks/`: 12개 **구조 평가 후보**와 선정 고정 기록
- `data/local/`: 해시 검증된 데이터·GT의 로컬 작업 사본. Git에서 제외
- `src/`, `tests/`: 독립 검증과 최소 정상상태 적합 코드
- `experiments/pilot/`: Gate 상태, 수치 진단 요약, 실제 시뮬레이터가 생겼을 때의 검증 자리

원본 자료의 출처와 해시는 [산출물 목록](docs/audit/ARTIFACT_INVENTORY.md)에 있다. 팀원 초대와 브랜치 규칙은 [기여 안내](CONTRIBUTING.md), [협업자 설정](COLLABORATOR_SETUP.md)을 참고한다.

## 별도 합성 예제의 통합 실험

[첫 통합 실험 보고서](docs/research_design/FIRST_INTEGRATED_PILOT_REPORT.md)와 [실행 안내](research_runs/first_integrated_pilot/README.md)에 새4변수 IID 환경의 실제 PC/BOSS/Direct 학습·공통 추천·독립 do 평가를 보존했다. Normal/Uniform은 별도 실험이며 Gaussian Direct는 가정 불일치 진단이다. 기존 TEP 7개 그래프·F1·적합과 혼합하지 않는다. 제조 환경/Recovery/Safety/원래 가설의 검증 완료를 뜻하지 않는다.

## 반복·다중 과제 합성 결과

사용자 승인으로 PR6~11은 main34b8dbe에 순차 병합했다. [반복 실험 보고서](docs/research_design/REPEATED_METRIC_PILOT_REPORT.md)에는 새12독립데이터의36학습·4과제·3정책·독립do55296개를 기록했다. 알고리즘/과제 결과는 상관된 관측이며432행을 독립표본으로 세지 않는다. 일부 층의 탐색적 연관만 계산했고 지표 우월성·제조 복구/안전 성능은 입증하지 않았다. 후속 변경은 별도 미병합 PR이며 [실행 안내](research_runs/repeated_metric_pilot/README.md)를 따른다.

## 다양한 구조의 신규 합성 비교

[8구조 보고서](docs/research_design/DIVERSE_STRUCTURE_PILOT_REPORT.md)에 source 검증된8개 합성DAG·48개 독립데이터·144실학습·17과제·918정책행·do78336개 및8회 구조전체holdout 예측을 기록했다. 기존4변수 반복 결과와 구분한다. 경로단독 모형의 평균예측오차는 작았지만 공변량 조정 후 연결지표와 거의 같아 우월성은 미확정이다.8개는 손설계 구조이고 행/rollout을 독립구조로 세지 않는다. [재현 절차](research_runs/diverse_structure_pilot/README.md)를 따르며 PR12 위 stacked 후속작업은 미병합이다. 제조 Recovery/Safety는 검증하지 않았다.

## 2026-10-25 독립 확인 결과
기존144회 전체 재실행 비교를 통과했습니다. 새12구조에서216개 그래프 기록을 생성했고 순환 PC2개를 보정하지 않고214개 SCM으로5088개 추천 결과와184320개 실제 do 표본을 평가했습니다. 사전 주요 비교는 경로 모형의 제한적 지지를 보였으나 기본 조건·연결 F1 이후의 추가 정보, 이론 평균과 고비용 조건의 안정성은 불명확합니다. [한국어 보고서](docs/research_design/INDEPENDENT_CONFIRMATION_REPORT.md)와 [재현 가이드](research_runs/independent_confirmation/README.md)를 참고하십시오. 제조 복구·안전 검증이 아니며 이 feature는 미병합 PR13 위에 있습니다.


현재 추가 정보 평가: [한국어 보고서](docs/research_design/PATH_METRIC_INCREMENTAL_VALIDATION_REPORT.md). PR12~14는 검증 후 병합됐으며, 새 feature에서는 기존20구조의 이론 운영 평가/실제 do 검산을 수행했다. 경로 지표의 안정적 추가 정보는 미확인이고 새 독립 확인은 정밀도·자원 Gate로 미실행이다. 제조공정 검증과 구분한다.


연구의 실무 방향은 [RESEARCH_COMPASS](docs/research_design/RESEARCH_COMPASS.md), 오류 위치·효과 추정·조작 선택의 실제 대조는 [다음 단계 보고서](docs/research_design/DECISION_RELIABILITY_NEXT_REPORT.md)를 참고합니다. 같은 F1에서 악화·개선·동률을 모두 확인했으며, 기존 개발 자료 재분석과 oracle 진단입니다. PR15 위 후속 feature이고 새 독립 제조 검증이 아닙니다.


제조 환경 직접 검증의 한계는 [제조 타당성 Gate](docs/research_design/MANUFACTURING_VALIDITY_GATE_REVIEW.md)에 있습니다. 후속 [환경 연결 검증](docs/research_design/TEP_ENVIRONMENT_BRIDGE_FEASIBILITY.md)에서 metadata·실제 근거 hash 차단 계약을 구현하고 고정 Python 후보8×6step 및3고정점 검산을 실행했습니다. 같은 센서/명령에서 숨은 밸브에 따라 상태 변화가 달라지는 국소 반례를 확인했습니다. 관측 참조/음성쌍 미확정으로 전체 구조–효과 연구는 계속 NO-GO이며 신규 연구환경을 채택하지 않았습니다.

밸브의 실제 적용cache를추가관측한 [동적 참조 결정안](docs/research_design/TEP_DYNAMIC_REFERENCE_DECISION.md)에서는 두조건4step의정상전이를검증했습니다. 과거24step은cache미기록으로완전계약이차단됩니다. L1 VERIFIED/L2 PARTIAL/L3·L4 BLOCKED이며, 다음은기술반복이아니라내부상태·시간전개를포함한제한연구설계안의사용자선택입니다. 새GT/학습/연구전환은없습니다.

[제한 동적 연구계약](docs/research_design/BOUNDED_DYNAMIC_RESEARCH_PROTOCOL.md)은 설계검토 초안(PROPOSED_FOR_REVIEW)이며 판정2·실행NO-GO입니다. 내부4node 냉각수–에너지 부분의 내생 경계와 발견 참조/온도선택 계약이 정당화되지 않았습니다. 새시뮬레이션·학습·GT 없음. 다음은 별도 효과·조작 선택 중심 설계 검토 여부 결정이며,원래 제조 전체F1 가설을 검증한 것으로 보지 않습니다.

[Python 효과·선택 최종 검토](docs/research_design/TEP_EFFECT_DECISION_FEASIBILITY.md)는 **STOP-TEP-EFFECT-TRACK**입니다. runnable manual command와반응성은있지만출처있는정책집합·목표/H·완결손실을정당화하지못했습니다. 현재TEP경로동결,새실험/학습/코드추가없음. 다음은기존합성독립확인·민감도·오류대조를최종주장으로정리하며제조전체F1검증으로혼합하지않습니다.

2026-10-29 최신 합성 결과 통합: [최종 Results·Discussion](docs/research_design/SYNTHETIC_FINAL_RESULTS_AND_CLAIMS.md). 전체 점수 동점의 다른 결정·효과/선택 불일치·정책 영향을 확인했지만,경로의 안정적 추가 정보는 미확립입니다. 기존 자료 재분석이며 새 실험0,TEP 경로 동결 유지.

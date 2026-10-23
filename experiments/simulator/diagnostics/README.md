# 수치·초기화·호환성 진단 재현

현재 결론: 후보 내부 탐색 **CONDITIONAL**, 기존 데이터 개입 효과 정답 직접 사용 **NO-GO**.
해석과 source 행 번호는 [감사 보고서](../../../docs/audit/SIMULATOR_RELIABILITY_REPORT.md)를 따른다.

## 외부 source가 필요한 실제 실행

기존 별도 checkout을 재사용했다. 먼저 `git -C ../tep-python-candidate rev-parse HEAD`가
`9a6c8e5fcef4a2850778704e7793c87b0a187005`이고 `status --porcelain`이 빈 값인지 확인한다.
새 환경의 설치는 upstream README/라이선스를 확인하고 해당 commit에 고정한다. 외부 source는 이 저장소에서 제공하지 않는다.
이번 환경은 Python 3.11.15, NumPy 2.4.6, Windows AMD64이다. `sim.dt`는 hours 단위이며 로그 두 시계는 seconds이다.

실제로 사용한 명령(저장소 루트 기준):

```powershell
python -X utf8 experiments/simulator/diagnostics/run_diagnostics.py --source ../tep-python-candidate --output experiments/simulator/diagnostics/run_20261023
python -X utf8 experiments/simulator/diagnostics/run_diagnostics.py --source ../tep-python-candidate --output experiments/simulator/diagnostics/run_20261023_aligned
python -X utf8 experiments/simulator/diagnostics/analyze_diagnostics.py --dataset data/local/datasetTE.csv --output experiments/simulator/diagnostics/analysis_20261023_v3
python -X utf8 experiments/simulator/diagnostics/validate_diagnostics.py
```

출력 경로는 존재하면 실패하도록 만들었다. 재실행은 새 이름을 사용한다.
첫 실행은 상태 시계만 기록한 코드 revision으로 실행했다. 이후 두 시계 정렬 기록과 2시간 정상 조건을 추가하여 aligned 실행을 수행했다. 최종 runner로 첫 실행의 파일 바이트까지 동일하게 재생성된다고 주장하지 않는다.
각 실행의 `plan.json`은 실행 전 작성됐다. std=0 진단은 사전에 별도 조건으로 지정했고 dt별 결과를 보고 개입량을 조정하지 않았다. 초깃값·시드·모드·intervention 시점은 동일하다.

- `run_20261023/`: 최초 진단 원시 기록. 상태 기준 30초 표본. 관측 시점이 다른 dt끼리 직접 비교하지 않음.
- `run_20261023_aligned/`: 정렬 분석 기준. 12개 수동 조건(3 dt × 2 개입 × 2 잡음), 2시간 폐루프 정상 1회, 초기화 2모드 × 5경우의 60초 기록.
- `analysis_20261023_v2/`: 최초 성공 분석. 이름 없는 index 열 처리 오류를 수정한 결과.
- `analysis_20261023_v3/`: v2와 같은 통계에 동일 평가 시점의 reference 대비 반응을 추가한 현재 분석.
- `execution_logs/`: 실행 stdout, 실패 원인 기록, 환경·backend 정보. NumPy config의 runneradmin/build 경로는 배포 wheel의 빌드 메타데이터이며 로컬 실험 경로가 아님.
- `variable_compatibility.csv`: benchmark Table II와 upstream constants.py의 선언 단위 대응. 수치 scale 보정 없음.

CSV에는 `state_seconds`, `observation_seconds`, XMEAS1..41, XMV1..12, yy1..50의 105열이 있다.
측정은 Euler update 직전, state는 직후이므로 두 시계를 구분한다. dt 변경 시 controller 시간기준 변화가 섞이지 않도록 수동 모드로 비교했다.
정상 2시간의 240개 공통 관측과 40개 3분 진단 창은 benchmark 원자료 집계를 복제한 것이 아니다.

## 외부 source 없는 CI

`validate_diagnostics.py`는 고정 원시 SHA, CSV·JSON 정합성, 시계, reset, 이전 manual 실험의 공통 측정값 일치, 분석 재계산을 검사한다.
실제 simulator 재실행은 위 로컬 절차다. CI 성공을 별도 모델 정확성 검증으로 해석하지 않는다. 독립 Fortran 기준 대조는 NOT_RUN이다.
RNG 고정은 같은 실행 조건에서만 동일 잡음 경로를 뜻한다. dt가 달라지면 RNG 소비도 달라져 std=0 진단과 구분했다.
새 객체가 후속 반복의 초기화 단위이며 같은 객체 reset의 exact 재현은 보장하지 않는다.

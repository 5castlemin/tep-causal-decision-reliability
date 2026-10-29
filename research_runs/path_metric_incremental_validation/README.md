# 경로 지표 추가 정보 — 개발 재분석과 정밀도 중단

보고서: `docs/research_design/PATH_METRIC_INCREMENTAL_VALIDATION_REPORT.md`.

- `integration/`: #12→#13→#14 실제 병합·검증 증거. 일회 사용자 예외이며 별도 승인 리뷰 생성 없음.
- `DESIGN_GATE_PLAN_v1.json`: 개발 분석 전 기록한 정밀도/예산/MC 계약.
- `development_v1/`: S1–S8/C01–C12 **개발 전용** 이론 운영 평가 및 20구조 LOSO.
- `development_supplement_v1/`: 정책/알고리즘 내부, 표본 결과 대조, 원래 5후보 순위 진단. 개발 보조 분석.
- `mc_calibration_v1/`: 새 seed의 실제 외부 FCM do 검산. 기존3구조 18조건, 69,120 유일 표본. 반복 검산은 독립 표본이 아님.
- 새 독립 확인은 정밀도 Gate `BLOCKED_PRECISION_RESOURCE`. 새 구조/학습/독립 확인 결과 없음.

Python 3.11 및 기존 첫 통합 실험 환경을 재사용했다. 외부 sampler는 NumPy1.26.4/Pandas2.2.3/SymPy1.14.0/NetworkX3.6.1. 알고리즘을 새로 설치하거나 학습하지 않았다. CI의 기본 requirements 환경은 저장 증거/이론 평가/CV 재계산이며 외부 FCM 재실행이 아니다.

```powershell
python -X utf8 scripts/run_path_incremental_development.py --output <new-development-directory>
python -X utf8 scripts/run_path_development_supplement.py --output <new-supplement-directory>
python -X utf8 scripts/run_path_mc_calibration.py --source <verified-original-models_fcm.py> --output <new-mc-directory>
python -X utf8 scripts/validate_path_metric_incremental.py
python -X utf8 -m unittest discover -s tests -v
python -X utf8 scripts/check_research_state.py
```

실행기는 기존 출력 디렉터리를 거부한다. 결과를 덮어쓰지 않는다. 외부 원본 SHA가 다르면 실행 불가. 원본 취득 절차와 라이선스는 기존 `research_runs/env_acceptance/` 및 `scripts/run_env_acceptance.py`를 참고한다. pinned commit은 `8da3729e6383f0e1cbe7740bb6ab7ac4977ac7f9`이다. 모듈을 저장소에 재배포하지 않는다.

이론 정답은 평가에만 사용한다. 실패한 추천은 운영 기준 조작 0의 실제 손실로 평가하고 가용률·조건부 성능을 분리한다. 정답을 보고 graph를 보정하지 않는다. 현20구조를 새 독립 확인으로 다시 부르거나, 제조공정 Recovery/Safety 성능으로 해석하지 않는다.

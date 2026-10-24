# 실제 설치·실행 기록

## 격리환경 설치
1. NumPy2.4.6/Pandas3.0.3 + 두 discovery 패키지 설치: FAILED. 의존성 backtracking 후 SciPy 소스/Meson 준비 중 UnicodeDecodeError.
2. NumPy1.26.4/Pandas2.2.3/SciPy1.12.0, 모든 package binary-only: FAILED. semopy wheel 제약과 구버전 portmin 의존성 해석 실패.
3. NumPy1.26.4/Pandas2.2.3/SciPy1.12.0, 큰 수치 라이브러리만 binary-only 및 semopy2.3.11 명시: PASS. semopy pure Python wheel을 빌드, 원본 FCM 패치 없음.

원시 설치·실행 console은 사용자 지정 아카이브 2026-10-24/05_첫번째_통합실험에 보존한다. 파일명·정확 바이트 SHA는 execution_console_provenance.json. 개인 경로는 Git에 넣지 않는다. 정확한 설치 명령은 README와 run_v1/requirements.lock.txt.

## 실제 실행 명령 (개인 절대경로만 역할명으로 대체)
```text
<isolated-venv-python> -X utf8 scripts/run_first_integrated_pilot.py --module <pinned-models_fcm.py> --output research_runs/first_integrated_pilot/run_v1
<isolated-venv-python> -X utf8 scripts/run_first_integrated_pilot.py --module <pinned-models_fcm.py> --output <archive>/반복실행_독립표본아님/run_v1_replay
<isolated-venv-python> -X utf8 scripts/check_first_pilot_replay.py --module <pinned-models_fcm.py> --replay <archive>/반복실행_독립표본아님/run_v1_replay --record research_runs/first_integrated_pilot/reproducibility_check.json
```
두 전체 실행 exit0. 실제 그래프/데이터/모형/추천/holdout/요약 일치. 그래프 runtime 초만 비교 제외. 반복은 독립 표본 아님. BOSS의 local_score_BIC_from_cov 전달 경고는 원시 log에 보존하며 실행 실패는 아니다.

실험 seed와 표본 수, 목적은 첫 실행 이전 PLAN_v1.json에 고정했다. 추천 SHA 동결 단계가 HOLDOUT_EVALUATED보다 앞선다. 참조 구조는 선언된 예제의 acceptance 및 최종 채점에만 쓰며 learner에는 전달하지 않는다. Recovery/Safety/상관계수/p-value는 계산하지 않았다.

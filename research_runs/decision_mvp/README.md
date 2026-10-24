# 구조 지표–추천 기술 MVP

PLAN_v1은 실행 전 고정했다. active 기록은 run_20261024_v2이며 v1은 명목 격자 로거의 과거 실행이다. 각8회, 총16회 짧은 기술 실행을 보존했다. summary의 Gate1/5는 차단이다.

global_metrics_reused/step6_loop_vs_flow_original은 기존 평가의 재사용이다. benchmark_task_metrics의84행은 기존 환경 진단이며 현재 X-Y 미확정은 null이다. before_unresolved_fix 파일은 폐기 대신 보존한 보완 전 파생물이며 분석에 사용하지 않는다. raw CSV는 변경하지 않았다.

recommendations_dry_run은 기존3개 Ridge surrogate 계산이다. 실제 simulator에는 이 추천 대신 사전 지정 동일 정책만 적용했다. 실제 추천 성능·Recovery/Safety·지표 설명력 통계는 없다.

재현은 scripts/run_decision_mvp.py에 외부 고정 source·기존 GT/Step6 ZIP·적합3개 JSON을 제공하고 새 output 폴더를 지정한다. 적합 파일 부재 시 재학습하지 않고 실패 기록을 남긴다. 결과 코드의 --mode research는 현 환경 계약 때문에 거부된다. 외부 source/기존 적합 없이 scripts/validate_decision_mvp.py로 저장 기록의 hash·시계·gating을 검사할 수 있다.

MVP_STATUS와 candidate_source_inventory는 실제 상태와 읽기 전용 후보 소스 검토이다. 후보 runtime·환경 채택은 미수행이다. 기록 검증/CI 통과는 과학적 환경 대응의 증명이 아니다.

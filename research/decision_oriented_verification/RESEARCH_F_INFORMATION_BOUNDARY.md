# Research F-Lite: 정보 경계 및 출처

## 연구 범위

F-Lite는 기존 Research C의 Development 64개 및 Held-out 200개 SCM을 되살려 사용하는 사후 탐색 정책 평가다. 신규 SCM, G0, 관측표본, DRF 적합 또는 개입표본은 생성하지 않았다. 평가 단위는 SCM이며 두 코호트 결과를 합쳐 독립 표본으로 취급하지 않는다.

## 역할별 허용 정보

| 역할 | 허용 입력 | 금지 입력 |
|---|---|---|
| Query policy | 초기 추정 graph, 512행 관측자료, 변수명, X/Y, action grid, target/scale, 현재까지의 질의·응답 | 참조 DAG, corruption log, GT 계수/오류, reference task zone, GT 손실/최적 행동, SCM regret |
| Simulated expert | 참조 DAG와 해당 질의 pair | 전체 그래프 반환, 다른 pair, 효과 크기, 행동 추천 |
| Evaluator | 잠긴 recommendation 및 GT mechanism | 정책의 다음 질의 선택 |

`make_policy_view()`는 허용 필드만 구성한다. 전문가 callback은 질의된 pair의 관계만 돌려준다. recommendation 결과의 해시를 저장한 뒤 analytic evaluator를 호출했다. `saved_output_audit.json`은 추천 산출물에 regret 필드가 없고, lock, 키 완전성 및 질의 선택 점수 재생이 맞음을 기록한다.

## 보안 수준 및 제한

이는 코드 인터페이스와 실행 순서 수준의 정보 분리다. 운영체제 sandbox가 없으므로 프로세스가 참조 DB나 evaluator 자료를 파일시스템에서 직접 읽지 못하도록 강제하는 완전한 보안 격리라고 주장하지 않는다. Coordinator가 expert와 evaluator를 관리하는 단일 Python 환경이므로 악의적 정책 코드에 대한 경계는 아니다.

## Provenance

원본 cohort/proposal DB 네 파일은 로컬 읽기 전용으로 열고, 복원 전후 binding을 검사했다. SHA-256은 `execution_lock.json` 및 실행 audit에 기록되어 있다. 원본 DB, observation arrays, per-SCM recommendation/evaluator JSONL 및 질의 replay는 공개 저장소에 포함하지 않는다. 공개 산출물은 집계 CSV/JSON, 코드 및 hash다.

## 실행 이력

첫 full-run은 64 Development recommendations까지 만들고 Graph-free diagnostic의 stale-view 기술 오류로 evaluator 이전에 멈췄다. 이를 고친 뒤 동일한 입력·seed로 전체 F core 실행을 마쳤다. 완료 뒤 summary writer의 변수 shadowing 오류가 있었으나 저장된 자료를 독립 감사했고 summary-only 수정은 후속 코드에 반영했다. 이를 실행 당시 무결성이 이미 완전 검증된 것처럼 소급하지 않는다.

선택적 expert-noise 단계에서도 첫 시도는 Development의 8,192 recommendation/evaluator rows 저장 후 aggregation 필드 오류로 멈췄다. 저장물을 보존해 재집계하고 동일 seed로 Held-out 단계를 이어갔다. 별도 복구 잠금과 로그에 실제 상태를 남긴다.

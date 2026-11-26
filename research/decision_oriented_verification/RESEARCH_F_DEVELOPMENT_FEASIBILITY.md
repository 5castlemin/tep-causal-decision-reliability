# Research F-Lite 실행 적격성 및 범위

기존 Research C의 Development 64와 Held-out 200 SCM을 각각 별도로 복원했다. 각 단위에 기존 truth specification, observation array, G0, task, action grid, target/scale, B=0 S0 action/regret binding을 대조했다. 원본 SQLite는 읽기 전용이며 신규 생성 데이터는 0이다.

정책 전체는 Development 64, Held-out 200에서 모두 실행됐다. 네 reference-blind deterministic query policy, 32회 Random, S0, Oracle-assisted M4 diagnostic, Graph-free association diagnostic을 포함한 8 policy family를 비교했다. 평가 범위는 기존 source SCM 분포에 조건부인 재사용 분석이다. Held-out C가 원래 Research C의 사전 동결 평가였다는 사실은 F를 시작할 때 이미 알려져 있었으므로 F 결과는 새 held-out 확증이 아니라 post-hoc 재분석이다.

결과 편집 비용은 질의 요청 횟수와 실제 atomic edge edit 수를 분리했다. Expert query는 1회 예산을 쓰며 잘못된 pair를 질의하면 답이 정확해도 edge edit가 0일 수 있다. Oracle M4는 참조 구조가 주어지는 점에서 reference-blind 정책과 비용/정보조건이 같지 않다.

실행 적격성은 입력 provenance 및 내부 파이프라인에 대해 충족됐으나 policy/expert/evaluator 간 완전한 OS 격리와 현실 전문가의 오류 분포는 입증하지 않았다.

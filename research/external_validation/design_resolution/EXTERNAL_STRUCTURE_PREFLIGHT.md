# 외부 구조 preflight

## Graph inventory

검사 입력은 Step 0 `inspection_results.json`의 핀된 `wt_standard` graph다. graph 32 nodes / 42 edges / DAG, 모든 graph node가 `random_loads_intake` CSV 스키마의 데이터 변수 목록과 일치한다. 전체 unordered pair 496, reference-absent 454, oriented absent pair 908이다.

후보 `load_in→rpm_in`과 `load_in→pressure_intake`는 모두 reference edge다. 둘 다 경로 길이 1, `task_zone()` pair count 1, zone nodes 2, Rule A task-FP 후보 0이다. 후보 과제 선택은 이 구조의 사전 검토로 판단되며 outcome 값은 접근하지 않았다.

## 제한 fixture

작은 손작성 DAG fixture에서 Research C 엔진의 `metrics()`를 호출해 task FN/REV/UNRES/FP 및 off-task FN/REV/UNRES/FP를 각각 분류하는 것을 검사했다. Fixture는 정책 추천, 예산 실행, stochastic seed, SCM, 학습 또는 결과를 포함하지 않는다. Fixture의 FP는 fixture reference 기준이며 외부 물리 비간선 검증이 아니다. 이 검사는 기존 코드가 direct-task의 0 분모를 `None`으로 표현하고, off-task 지표들과 분리된다는 API 호환성 확인만 한다.

## M1–M4 의미 판정

엔진의 구조적 동작은 유지할 수 있지만 direct task에서 M4는 단일 reference adjacency의 오류 수정에만 반응하고 M4-FP 구성요소는 정의되지 않는다. 모든 M4 가능한 오류는 동일한 edge에서의 FN/REV/UNRES다. 반면 off-task 41개의 참조 간선과 454 reference-absent pair가 다른 지표 후보 공간을 이룬다. 결과 기반 효용 연결 없이 이 분해를 공정한 M1–M4 경쟁이라고 해석할 수 없다. 이는 `OPTION B`의 적격 요건을 충족하지 못한다.

## 오류 burden과 예산 사전 분석

Research C `q=.15`, `r=.05`를 32/42 graph에 적용하면 DAG 검사 전 기대 제안은 true adjacency corruption 6.3건, reference-absent pair FP proposal 22.7건이다. FN/REV/UNRES 기대값은 각 2.1건이다. DAG rejection은 추가로 부담을 낮추며 이 수치만으로 최종 G0 burden을 알 수 없다.

1 edit = graph operation 비용인 기존 의미는 유지할 수 있으나 전문가 시간 또는 물리적 위험 비용은 아니다. B=2는 임의의 reference discrepancy 두 개까지 고칠 수 있다는 의미일 뿐 90-node Mk2의 절대 예산과 동등하지 않다. 32-node에서도 q/r 오류를 그대로 쓰면 총 제안 burden이 매우 커지고 task edge 하나는 손상 확률 .15다. 고정 오류 strata로 task 오류를 강제하면 M4를 위한 편향이 되므로 허용하지 않는다.

이번에는 stochastic G0 seed cohort를 만들지 않았다. 구조 지원을 확인하기 위한 실제 production edge correction은 하나의 pair에 대한 no-op 또는 1회 수정밖에 없어, 다수 seed를 만들어도 M1–M4의 외부 결정 가치를 더 밝혀 주지 않는다. 손작성 fixture가 오류유형별 API smoke check를 대신한다. 후속 설계가 새로 승인되기 전 large-scale error injection, policy recommendation 및 regret는 진행하지 않는다.

## Graph-free baseline

무작위 배정은 graph-free arm-mean 모델에 직접 행동 지원을 준다. 그래프 수리 pipeline은 구조/reference와 아마 별도 response model을 요구하므로 정보가 동등하지 않다. 동일 block train split, 같은 action set·target·scale·평가 blocks에서 비교하고 graph-free 모델의 추가 직접 supervision을 명시해야 한다. 모델 성능은 이번에 계산하지 않았다. 정책 기반 비교를 다음 단계에서 고려하려면 이 baseline은 필수 comparator 검토 대상이다.

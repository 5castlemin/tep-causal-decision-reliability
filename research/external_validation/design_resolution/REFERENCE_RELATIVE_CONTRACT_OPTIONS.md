# Reference-relative 계약 선택지

## 세 안의 판단

| 안 | 기준 구조 | 오류 뜻 | Step 2 판단 |
|---|---|---|---|
| A. Complete physical GT | 모든 496 unordered pair의 존재/부재와 방향을 물리적으로 검증 | FN/FP/REV/UNRES가 물리 참 구조의 오류 | **FAIL**. 공식 도식은 positive 관계를 제시하지만 모든 미기재 간선의 부재를 보증하지 않는다. |
| B. Restricted verified reference | pair별 증빙된 양성·음성만 채점, 나머지는 unknown | 제한된 pair universe 내 오류 | 현재 **추가적인 pair-level negative 증거 부족**. FP 분모가 특히 제한되며 M1–M4 분모와 후보군 재설계 필요. |
| C. Reference-relative controlled corruption | 핀된 공식 도식을 benchmark 참조로 고정 | 도식과의 불일치; 물리 GT 오류를 의미하지 않음 | 용어상 가장 정직한 구조 benchmark지만 direct task에서는 task zone 1 edge, task FP 0이라 M1–M4 외부 결정 가치가 빈약함. **채택 보류**. |

## Pair universe와 오류 라벨

32 node / 42 adjacency에서 전체 unordered pair는 496, 참조 부재 pair는 454, 부재 pair 두 방향 기준은 908개다. 검증되지 않은 참조 부재는 물리적 비간선으로 라벨할 수 없다. C 계약을 택하더라도 `reference-relative FN`, `reference-relative FP`, `reference-relative REV`, `reference-relative UNRES`라 표기해야 한다. 참조에 없는 추가 방향은 `reference-relative FP`일 뿐 실제 FP의 주장이 아니다. DAG 조건은 benchmark 속성으로 검사할 수 있지만 물리 그래프 완전성을 증명하지 않는다.

## 정책 이전

Research C의 정책 엔진 자체를 바꾸지 않는 wrapper는 가능하다. 다만 기존 `task_zone()`을 그대로 사용하면 direct task의 zone은 단일 edge다. M4 task-FP 기회는 0이다. M4는 task edge의 누락·역전·미정향만의 지표로 축소된다. M1은 비-task reference edge FN, M2는 off-task FP, M3는 off-task 방향/미해결 오류를 대상으로 한다. 이 분할은 코드상 정의 가능하지만 실측 decision value와의 연결은 아직 입증되지 않았다.

공식 도식을 C로 고정하여 하는 실험은 의도적으로 주입한 reference discrepancy를 고치는 controlled benchmark다. complete physical ground truth에 대한 수리정확성, 현장 causal discovery의 성능, 배포 자동수리를 주장하지 않는다. B는 verified pair 집합, unknown pair 마스킹, 분모와 abstention semantics가 필요하므로 기존 M1–M4의 정확 반복이 아니다.

## 선택

이번에는 A/B/C 중 어느 것도 본실험 계약으로 채택하지 않는다. OPTION C(물리 사례 재설계) 판정은 이 세 계약의 평가 이력과 다른 정책/estimand를 먼저 명시해야 한다는 의미다. 앞으로 graph benchmark만 수행하면 C를 별도 benchmark 계약으로 승인해야 하며, Research C를 변경하는 것이 아니다.

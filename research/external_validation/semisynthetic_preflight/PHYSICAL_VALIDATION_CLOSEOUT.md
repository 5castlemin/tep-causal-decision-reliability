# Research D: 실측 검증 보류 결정

## 판정

- Mk2: `DEFERRED_PENDING_EXTERNAL_EVIDENCE`
- Wind Tunnel: `PHYSICAL_CASE_REDESIGN_REQUIRED`
- 현재 실측 정책 평가: `DEFERRED`
- 본 문서가 대상으로 삼는 별도 연구 유형: `EXTERNAL_SEMISYNTHETIC_ROBUSTNESS`

이는 Causal Chamber가 인과 연구에 부적합하다는 판단이 아니다. 현재 Research C의 strict indirect-only 정책 비교를 물리 실측자료로 정당화할 계약이 Mk2와 Wind Tunnel에서 확보되지 않았다는 뜻이다. Mk2 및 Wind Tunnel의 원자료, 미해결 증거와 기존 판정은 그대로 보존한다. 추가 데이터셋 탐색이나 장치 제어는 하지 않았다.

## 외부 실측 검증이 보류된 이유

Mk2는 Step 1 이후 해결되지 않은 reference negative-pair 범위, SET–MSR alignment, carryover, 장치·세션·reset provenance blocker가 남아 있다. Wind Tunnel은 block 배정이 재현되지만 후보 과제가 reference direct edge이고 M4 task-FP 지원이 없으며, 실험 run을 독립 장치·세션으로 셀 수 없다. 이는 각각 [Step 1 판정](../qualification/RESEARCH_D_QUALIFICATION_DECISION.md) 및 [Step 2 설계 결정](../design_resolution/RESEARCH_D_DESIGN_RESOLUTION.md)에 기록되어 있다.

반합성 검토는 별개의 조건부 후보다. causalAssembly는 제조 데이터와 공정 지식에서 구성한 참조 DAG에 DRF 조건부 분포를 적합해, 그래프에 Markov인 표본을 만든다. 따라서 제조기반 비선형 생성환경에서 구조 오류 수정 우선순위의 강건성을 시험할 수 있지만, 물리 장치의 실제 개입효과나 DAT 제조 현장으로의 전이를 시험하지 않는다.

## 다음 경계

현재 반합성 판단은 **`CONDITIONAL_SEMISYNTHETIC`**이다. 실제 패키지 및 DRF fit과 관측표본 생성은 동작했다. 하지만 제조 측정값의 in-support 연속 hard intervention을 causalAssembly의 pinned sampler가 생성하지 못했다. 숫자형 float는 `intervene_on()`에 저장되지만 sampler는 `int` 또는 SymPy `RandomSymbol`만 처리하고 float에서 `NotImplementedError`를 낸다. 지원되지 않는 out-of-support 정수 조작을 대신 실행해 이 제한을 숨기지 않았다.

후속 진입은 한 가지 해결로 한정한다. 별도 Research D adapter에서 finite numeric hard intervention을 올바르게 전달하고, 합성 fixture 및 작은 Station1 smoke test로 intervention 값 고정, graph mutilation, fresh-object reset, seed 재현을 확인한다. adapter의 코드 검토와 별도 개발용 평가자료 생성 승인이 선행되어야 한다. 이 해결 후에도 새 실험 계약 승인이 필요하며, 이번 판정은 본실험 승인이 아니다. 해결이 추가적인 외부 패키지 수정/지원 의존 없이 완료되지 않으면 `STOP_EXTERNAL_VALIDATION`으로 종료한다.

smoke test가 만든 탐색용 관측 응답 표본은 총 25행(8 + 5 + 4 + 4 + pinned archive 기준 2×2)이다. target 값을 포함한 응답행이 내부에서 생성되었지만 그 값이나 평균은 출력·비교·정책 선정에 쓰지 않았다. intervention response는 0행 반환됐다. 이 개발 표본은 최종 평가에서 폐기하고, 승인 후 독립적으로 다시 생성해야 한다.

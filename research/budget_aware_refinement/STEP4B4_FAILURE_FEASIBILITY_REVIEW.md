# Step 4B-4 failure feasibility review

**판정: 상태분류와 fallback은 mock 검증; 전체 결측 중단 규칙은 실용성 위험을 드러냄.** 구조 부적격은 Q 표본수율/시도 분모이며 SCM 분석 결측이 아니다. `NO_CANDIDATE`, `UNUSED_BUDGET`, `CYCLE_REJECT`는 정상 결과다. Ridge/recommend 실패는 training/truth 유효하고 k=0이 공통 action grid일 때만 k=0 intention-to-handle fallback. 원 실패 상태와 fallback을 모두 기록한다. GT 평가 실패는 fallback 없이 missing으로 둔다.

## N=200 MCAR complete probability

아래 독립 MCAR 시나리오는 수식 `(1-r)^(200*m)`의 민감도 진단이지 실제 실패율 추정이 아니다. m=1은 SCM primary row별 독립 event, m=3은 FN/FP/REV cell별 독립 event다. 실제 결측이 SCM, 정책, 결과에 의존·군집하면 값은 맞지 않는다.

| event 결측률 | 200 SCM rows 모두 완전 (m=1) | 600 type cells 모두 완전 (m=3) |
|---:|---:|---:|
| 0.1% | 81.865% | 54.865% |
| 0.5% | 36.696% | 4.941% |
| 1.0% | 13.398% | 0.241% |
| 2.0% | 1.759% | 0.001% |

0.1% per type-cell 결측만으로도 600개 모두 완전할 확률은 54.865%; 0.5%면 4.941%다. strict stop은 편향 방지에 보수적이나 확인 분석 완료 가능성을 낮춘다.

## 처리 대안

A. 하나라도 미복구 primary row가 있으면 확인 추론 보류. B. transient IO/system만 같은 입력·같은 RNG key로 1회 재시도. 재시도 성공은 같은 unit 복구이며 독립 실패로 간주해 실패율을 제곱하지 않는다. C. 영구 결측이면 실패율과 원인을 공개하고 complete case는 기술통계로만 제시한다. 유한 contrast bound가 있을 때만 bound-based sensitivity를 추가한다. 현재 Regret 차이에 정당한 유한 범위가 없어 C로 확인적 추론을 복구할 수 없다.

정책별 실패 결과는 성공 실행 평균에서 빼지 않는다. 허용 fallback의 비율 및 정책별 failure 차이를 보고한다. 사전 생성 reserve 후보는 outcome-blind rule과 target weight 영향이 확정되기 전 사용하지 않는다.

JSON: `step4b4_failure_feasibility_v2.json`; mock logic: `step4b4_failure_rules.py`; 테스트는 같은 key retry, type vector 완전성, shortfall, fallback 조건을 검증한다.

# 발표 재구성 근거 감사

**기준:** 브랜치 `research/original-research-fixture-validation-v1`, 커밋 `77b4122f7048acd67b69ed8ac5d6caf78264935c`. 이 문서는 발표 편집용 근거표다. 결과 재계산이나 새 실험은 수행하지 않았다.

## 정량 수치의 출처와 허용 해석

| 발표 수치/주장 | 근거 파일 | 상태·분모 | 허용되는 표현 | 금지되는 표현 |
|---|---|---|---|---|
| 연구 A: 162쌍 중 손실 악화 93, 개선 4, 동률 65 | `docs/research_design/SYNTHETIC_FINAL_RESULTS_AND_CLAIMS.md`, Results 2; `CLAIM_EVIDENCE_MATRIX.json` 참조 | 기존 합성 통제 비교, 14구조의 graph-pair 비교. 162개 독립 공정이 아님 | 점수·오류량 일치 쌍에서도 오류 위치와 손실이 다를 수 있다는 존재 증거 | 모든 구조 점수는 무의미, 경로 지표가 항상 우월, 실제 TEP 효과 확인 |
| C07 핵심 누락 loss 14.542543 vs 주변 누락 0.360000 | 동일 합성 결과 문서 C07_n512_r1/path 항목 | 한 설명 사례 | 오류 위치 민감성의 예시이며 일반 효과 아님 | 전형적 제조 사례 또는 평균 효과 |
| C03 반례 loss 0.050204 vs 0.360000 | 동일 합성 결과 문서 C03_n256_r3/path | 반대 방향 예시; 핵심 오류가 더 나은 결과 | 결과 방향이 단일하지 않다는 반례 | 지지 사례에서 제외하거나 숨김 |
| Step 5 N=64, mean D=0.0146604849, median 0, signs 6/1/57 | `research/budget_aware_refinement/STEP5_STEP6_FINAL_RESULTS.md`; `STEP5_STEP6_CROSS_CHECK.md`; `step5_development_v1/STEP5_DEVELOPMENT_SCM_SUMMARY.csv` | 개발 SCM 단위, 별도 코호트 | 개발 기술통계 | 확인적 우월성 또는 Step 6과 합산한 N=264 |
| Step 6 N=200, mean D=0.0200725113, median 0, signs 25/8/167 | `research/budget_aware_refinement/STEP5_STEP6_FINAL_RESULTS.md`; `STEP5_STEP6_CROSS_CHECK.md`; `step6_confirmation_v1/STEP6_CONFIRMATION_SCM_SUMMARY.csv` | 독립 confirmation namespace, SCM 단위. Option B | 별도 코호트에서 유사한 양의 기술적 평균과 다수 동률이 관찰됨 | 통계적 우월성 입증, 보편적 Task-Focused 효과 |
| Step 5/6 proposal 수 211 / 675, admission 64 / 200, 완전 평가 64/64 / 200/200 | `STEP5_STEP6_CROSS_CHECK.md`; 실행 보고서 | Proposal 분모를 admission·완전 평가와 구분 | 각 단계 분모를 별도 표시 | 구조 거절을 SCM 실패로 합산 또는 admission을 결과완료와 동일시 |
| Step 6 그래프가 다른 횟수 FN/FP/REV = 76/109/93; k가 다른 횟수 14/3/25 | `STEP5_STEP6_FINAL_RESULTS.md`; `FINAL_RESEARCH_REPORT.md` §4 | 각 유형별 분모 200, 동일 Action은 과제 고정 | 그래프 차이가 k/Regret 차이보다 흔했음 | 그래프 편집 차이를 정책 성과 차이로 해석 |
| Step 5 유형 평균 FN/FP/REV = .0058258/0/.0381557; Step 6 = .0307732/.0021787/.0272656 | `STEP5_STEP6_FINAL_RESULTS.md` | 동일 SCM 내 반복 오류 유형; 유형별 n은 독립 SCM 수 아님 | 기술적 유형별 패턴이 코호트 간 달랐음 | 오류 유형의 보편적 중요도 순위 |
| Step 6 최댓값 +.6097471, 최솟값 −.1447869; 상위 두 건 합 기여 29.4% | `STEP5_STEP6_FINAL_RESULTS.md`; 사례 문서 `CASE_STUDY_POSITIVE_NEGATIVE.md` | 민감도 요약 및 설명용 사례 | 평균은 희소한 비영 사례에 민감 | 극단 사례를 전형적인 효과로 제시 |
| Step 6 template counts chain/fork/multiple-path/common-cause = 49/28/88/35 | `STEP5_STEP6_FINAL_RESULTS.md` | 기술적 하위집단 구성 | 템플릿 비중과 불균형을 설명 | 사전 층화 효과 또는 모집단 가중 평균 |
| Fixture: S15와 S1이 B=1에서 같을 수 있음; 새 초기-error normalization에서 A/B 동일 subset 결과 16/16, 이전 hardcoded gain은 10/16(B=1), 14/16(B=2) | `ORIGINAL_RESEARCH_FIXTURE_VALIDATION.md`; `scripts/validate_original_research_fixture_contract.py` | 결정론적 hand-built DAG; scheduler sanity check | 라벨 수가 다른 정책 결과의 차이를 보장하지 않는 설계 진단 | Regret, SCM 성능, 연구 C의 정책 우위 |
| Fixture: M2 denominator-only 감소 및 M3 unresolved 회피 반례 | 같은 fixture validation 문서 및 스크립트 | 산술 반례 | 단순 비율만 목적화할 때 점수 왜곡 가능성 | 해당 왜곡이 본 연구 데이터에서 발생했다고 주장 |

## 연구 C의 지표·전략·목적함수 표현

| 항목 | 근거 | 발표 표기 상태 |
|---|---|---|
| M1 과제 외 누락률 | `ORIGINAL_FOUR_METRIC_SPEC_V2.md` | 계산 정의 후보; 분모·작은 support 운영 승인 대기 |
| M2 과제 외 허위 연결률 | 동일 문서, FP assignment options | FP 귀속 규칙 A/B 미결. 추가 간선으로 분모만 늘어도 rate가 떨어지는 점에 유의 |
| M3 방향 정확도 및 unresolved rate | 동일 문서 | 함께 보고하는 후보. unresolved 분모와 policy proxy 미승인 |
| M4 FN/FP/REV/UNRES 벡터 | 동일 문서 | 구성요소를 보존; scalar β 미승인 |
| S0 + 15 nonempty subsets | `METRIC_TO_REPAIR_POLICY_SPEC_V2.md`; `ORIGINAL_RESEARCH_CONTRACT_CANDIDATE.md` | 연구 C 정책 카탈로그 후보. 기존 Step 4 정책 14개와 별개 |
| 비용 C, subset 벌점 P_S, 공통 P_all, Decision Regret | `COST_AND_PENALTY_SPEC_V2.md` | 서로 다른 수량으로 분리. 계수·정규화 OPEN |
| 초기 후보 cost c_add=c_del=c_ori=1, w_FN=w_FP=w_REV=1, λ=1 | 비용 명세 | 기준 시나리오 후보; 승인된 실증 추정치나 동결값 아님 |
| 방향 비용 비율 1/2/3, w_FN/w_FP 범위 등 | 원 비용 제안이 반영된 `COST_AND_PENALTY_SPEC_V2.md` | 민감도 후보 범위; 실험 실행 또는 최종 선택 아님 |
| Oracle-assisted | `ORIGINAL_RESEARCH_CONTRACT_CANDIDATE.md` | 진단 연구 후보. GT 구조 정보만 수정 후보 작성에 사용; 효과·loss·Regret은 정책 선택에 비공개 |

## 완료된 것과 아직 하지 않은 것

### 실제 완료 결과

- 초기 TEP/합성 구조평가 자료 및 합성 오류 위치 결과가 기록돼 있다. 참조 그래프의 완전성, 동일한 생성환경, 실제 공정 개입효과는 미검증이다.
- 초기 합성자료에서 지표와 추천/손실 관계를 탐색했다. 일부 초기 예측력 결과는 후속 분석에서 안정적이지 않았고, 원래 네 지표 우선순위를 비용 제약으로 직접 비교한 것은 아니다.
- Step 5 개발 64 SCM 및 Step 6 독립 namespace 200 SCM은 동결된 FN/FP/REV ordering 질문의 완료 코호트다. 두 결과는 기술통계 및 독립 원시 감사와 함께 보존돼 있다.

### 설계/fixture 검증

- Specification/contract 문서에는 M1–M4 계산 후보, 단일 오류 귀속, 비용 제약, 16개 전략의 후보 규칙이 있다.
- 고정 소형 DAG에서 산술, M2/M3 반례, 일부 정책 궤적 및 A/B graph 동일성을 검증했다. 이는 실행 코드가 시험한 fixture에 일관적인지 확인하며 정책 성능 추정이 아니다.

### 미실행

- 네 지표를 사용한 새 SCM 코호트 생성 및 평가.
- 비용/피해 가중치의 데이터 기반 추정 및 그에 필요한 별도 훈련 자료.
- 네 지표 subset별 비용 제약 정책의 Decision Regret 비교.
- 새 독립 평가 코호트, 최종 표본 수·검정 계획 및 사전등록.
- 실제 제조공정 수율·안전·경제적 결과의 검증.

## 허용 주장과 금지 주장

**허용:** “기존 합성 연구는 동일하거나 비슷한 전체 점수 아래에서도 오류 위치와 손실이 달라질 수 있는 사례를 보였다.” “기존 Step 4–6은 정답 기반 후보 수정 순서의 제한된 비교였고, Step 6에서 167/200이 동률이었다.” “새 연구는 네 지표 조합과 비용 제약을 평가하도록 제안됐지만 현재는 계약·fixture 단계다.”

**금지:** “Task-Focused가 일반적으로 우월하다.” “경로 정확도가 최선의 지표다.” “16개 중 특정 전략이 최적이다.” “현재 fixture가 Regret 개선을 입증했다.” “새 연구 C에서 비용 최적화나 Decision Regret 감소가 이미 검증됐다.” “TEP 제조공정의 실제 수율·안전·경제효과가 개선됐다.”

## 발표자료 상태

실제 PPTX가 `research/budget_aware_refinement/final_presentation/DAT_Causal_Decision_Reliability_Final_Presentation.pptx`에 존재한다. 이 편집안은 해당 파일을 덮어쓰거나 재생성하지 않는다. 수치는 저장된 교차검증 보고서의 반올림 수준으로만 옮기며, 본 자료 작성 중 원시 SCM·Regret을 다시 계산하지 않았다.

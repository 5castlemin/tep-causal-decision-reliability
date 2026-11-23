# 원 연구 설계 Specification Gate — Decision Log

**기준:** `research/original-objective-recovery-audit-v1`의 감사 산출물 및 원문 DOCX 사본.
**상태:** `SPECIFICATION REVIEW / NOT PREREGISTERED / NO EXPERIMENT AUTHORIZED`
**범위:** 정의와 후보 계약 정리. Step 4 동결 계약과 Step 5/6 결과는 그대로 유지한다.

## 확인한 증거

- 지표 DOCX의 확인 사본 SHA-256 `fe83334f7d8b34fb555d6e60e7e3bd2fd8ec2b51e913d57bd046853865cbe165`.
- 비용 DOCX의 확인 사본 SHA-256 `a3d26fe83b736a6950c64ce54e2fca7b131582e6da19e3ea6e6aedbdef7c0818`.
- `ORIGINAL_OBJECTIVE_VS_FINAL_STUDY_AUDIT.md`: 완료 Step4–6은 원 네 지표·비용 최적화 질문과 다른 추정 대상.
- `FOUR_METRIC_IMPLEMENTATION_GAP.md`: 일부 F1/path 구성요소만 존재; 원 네 지표 통합 계산·TEP ④ 적용 근거 없음.
- `COST_MODEL_IMPLEMENTATION_GAP.md`: `c`, `w`, λ, ρ tradeoff 및 15-subset 정책 실험 미실행.
- `ORIGINAL_RESEARCH_RECOVERY_PLAN.md`: 새 지표·비용 계약 및 독립 평가 필요.

## 정의 가능한 원칙 — 문서화됨, 실험 계약 승인 아님

1. 원 지표 네 개는 Skeleton F1/Directed F1/Path F1/Ancestor F1과 다른 정의다.
2. ①–③은 과제 구역 밖, ④는 task zone 오류를 대상으로 한다.
3. 원 비용 구상은 수정비용과 잔존 오류 피해를 구분한다. 주 목적은 `min penalty s.t. cost≤B`, 보조 목적은 `cost+ρ·penalty`다.
4. 15개 nonempty metric subset과 no-edit baseline은 총 16전략을 뜻한다. 기존 FN/FP/REV 14개 정책과 다르다.
5. Decision Regret은 정책 성능의 별도 평가량이며 잔존 구조 벌점과 동치가 아니다.
6. 원문에서 단일 표준 비용 단가는 없다고 했다. 실제 제조 경제 단위는 독립 자료 없이 주장할 수 없다.

## 미결 선택 및 권고 — 사용자/연구책임자 결정 필요

| ID | 선택이 필요한 내용 | 현재 후보/주의 |
|---|---|---|
| D1 | GT backdoor/confounder task-zone 알고리즘 | X→Y causal paths + X로 들어오는 X–Y simple backdoor paths 후보. 원문은 세부 알고리즘·공통원인 경계 미확정. |
| D2 | FP의 과제 구역 귀속 | 내부 `V_T` endpoint 규칙 A vs path-relevant boundary 포함 규칙 B. ②의 denominator와 ④도 함께 달라짐. |
| D3 | M3 unresolved denominator | 원문 “맞게 찾은 연결”이 모호. 후보 `Q/(C+R+Q)`, 개수는 항상 표시. |
| D4 | M4 aggregate | FN/FP/REV/unresolved 구성요소 별도 보고 우선. Scalar 필요 시 `α` weights를 승인해야 하며 임의 합 금지. |
| D5 | 원자 연산 | add/delete/orient/reverse 및 unresolved 처리, 다중 지표 동시 개선의 단일 과금 여부. |
| D6 | 전략 quota·normalization | equal quota 후보는 archived A–D 제안의 실행 규칙. 지표 스케일이 달라 normalization 없이 개선량 비교 불가. metric-level quota가 edit 수인지 비용 단위인지 미결. |
| D7 | 단가·예산 grid | `c_add=c_del=c_ori=1` 기준, `c_ori/c_add={1,2,3}` 민감도. B의 확정 grid 미정; B=1에서 c_ori=2/3은 reversal 불가. |
| D8 | `w_FN,w_FP,w_REV,λ` | DOCX 제안 회귀 추정, 개발/평가 분리 필요. 추정자료·모형·불확실성 미결. |
| D9 | ρ | 보조 trade-off 곡선 domain과 unit normalization 미결. |
| D10 | 정책 정보 접근 | 참조 graph tag를 정책 후보에 쓰는 oracle 평가인지, graph estimate만 쓰는 비-oracle 방법인지 estimand 별로 분리. |
| D11 | 최종 outcome 및 관계 | 구조 벌점 최소화가 주 목적, Decision Regret을 별도 결과로 둘지, 단위 SCM 등 분석 단위/추론 계약은 후속 설계 필요. |
| D12 | 새 표본과 holdout | Step5/6 재사용 불가한 새 개발 및 독립 평가 범위·N·seed를 결과 열람 전에 정해야 함. 이번 gate에서 수치 선정 안 함. |

## 확인하지 않은 것

- 새 지표의 실행 코드/계산 결과, TEP 7개 그래프 재채점, metric correlation/VIF.
- 16개 전략 실행, 비용 시나리오, 가중치 추정, regret 또는 제조 효용.
- 독립 비용 자료, 표본 수, 검정력/추론 계획.

## 결론 및 변경 영향

이 gate는 계산 계약 후보와 unresolved decisions를 문서화했을 뿐 승인된 연구 계획을 만들지 않았다. 어떤 미결 항목도 이미 사용자가 확정했다고 기록하지 않는다. 다음 단계는 D1–D12를 책임자가 결정하고 별도 protocol/analysis plan을 검토하는 것이다. 그 결정 전까지 **사전등록 미완료, 새 실험 금지, Step4 Frozen 불변**이다.

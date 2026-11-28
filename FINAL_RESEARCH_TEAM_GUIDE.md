# 팀 연구 가이드 — 질문에서 최종 결과까지

## 왜 이 연구를 시작했나?

초기에는 TEP 관측자료에서 causal discovery 그래프가 참고 구조와 얼마나 비슷한지 비교했다. 하지만 전체 그래프 F1/SHD나 관측 예측 성능만으로 실제 조작 결과가 좋아지는지 알 수 없었다. TEP의 참고 구조와 시뮬레이터 개입을 본 연구의 완전한 물리 ground truth라고 놓기에도 근거가 부족했다. 그래서 구조와 개입 결과를 통제할 수 있는 합성 SCM을 이용해 더 좁고 검증 가능한 질문으로 바꿨다.

## Decision Regret은 무엇인가?

가능한 조작 행동 중 정책이 추천한 행동의 손실과, 같은 후보 가운데 최선 행동의 손실 차이다. 예를 들어 5개의 setpoint 후보에서 추천이 가장 좋은 후보와 같으면 regret은 0이다. 추천이 나빠질수록 regret이 커진다. **관측값 예측이 정확한지**와 **추천 행동이 좋은지**는 다른 질문이다.

## M1–M4는 무엇인가?

참조 DAG 및 주어진 X→Y task zone에 비추어 오류 유형/위치를 분류하는 구조 repair prioritization 지표다. M1은 task 밖 FN, M2는 task 밖 FP, M3는 task 밖 REV/UNRES, M4는 task 관련 오류 구성요소를 다룬다. 이들은 참 구조 정보를 이용하므로 실제 현장에서 오류를 자동으로 발견하는 oracle-free 방법은 아니다. 원자 수정 1회당 비용은 분석상 1이며 실제 작업시간이나 금액이 아니다.

## Greedy는 어떻게 고치나?

정책은 현재 그래프의 합법적 후보 수정 중 구조 점수 개선량을 비용으로 나눈 값이 큰 수정을 선택하고, 변경된 그래프에서 다음 후보의 적법성을 다시 확인한다. 실제 개입 결과의 regret은 정상 정책 추천 단계의 입력이 아니다. Ex-post optimal 같은 사후 진단은 evaluator 결과를 사용하므로 실행 가능한 정책으로 보면 안 된다.

## T1–T6와 T5의 역할은?

S3/S4는 과제 관련 구조 지표가 오류 내부의 우선순위를 더 잘 가릴 수 있는지 살폈다. T5-guided M4는 task-ancestor F1 gain을 사용하며 기존 M4 gain을 tie-break로 쓴다. S4의 새 독립 replication에서 점 추정치는 T5 쪽이었지만 interval에 0이 포함되고 precision 목표를 미달했다. 이를 “T5가 이겼다”라고 말하지 않는다. S5에서는 저장된 200 G0 전부에서 T5와 M4 첫 편집이 같았다.

## Research C와 D/S5의 차이는?

C는 여러 독립 synthetic SCM에서 analytic true-SCM regret을 비교한 frozen contract 실험이다. D는 별도의 DRF 기반 Station1 semisynthetic DGP 평가였고, S5는 D 자료를 정확히 재현한 것이 아니라 같은 공개 benchmark 소스를 쓴 신규 conditional reconstruction이다. S5의 분석 단위는 독립 SCM이 아니라 단일 DGP에 조건부인 G0 corruption draw다. 둘의 절대 loss/regret은 직접 비교하거나 합산하지 않는다.

## Research E가 경영학적으로 중요한 이유는?

실제로 오류를 고치는 일에는 제한된 전문가 시간과 검증 자원이 필요하다. 이 연구는 최대 허용 budget, 실제 사용된 edit count, regret 개선량을 분리해 비용-성과 trade-off를 보여준다. 다만 λ는 편집 수에 붙인 가상 가중치다. 금액·인건비·안전 비용을 측정하지 않았으므로 산업 비용 절감은 입증되지 않았다.

## 최종적으로 무엇을 알았나?

동결된 C 실험에서는 제한된 수정이 무수정보다 평균 regret을 낮췄다. task 중심 구조 수정은 적은 수정으로 유용할 수 있지만, 오류 가치와 budget 편익은 비단조·목표 의존적이며 M4나 T5의 보편적 우월성은 확인되지 않았다. 외부 반합성 S5에서는 M4의 point estimate가 유리했지만 two-source uncertainty는 0을 포함했고 graph-free 기준선이 경쟁했다.

S6는 기존 S4의 Development/replication candidate 기록을 재사용한 사후 B=1 비교다. Replication에서 T5의 평균 regret은 .030152, Frozen M4는 .038817이었고 paired 차이 −.008664의 95% 구간은 [−.020398, 0]이었다(4/1/155; Holm-adjusted p=1.0). Type-ranked 정책도 Frozen M4 대비 차이 −.002204, 95% 구간 [−.009283,.003545]으로 불확실했다. 이 결과는 같은 160-SCM replication 자료의 재집계이며 신규 독립 확인 실험이 아니다.

S7 full-line recommendation 계산은 예정 400 G0·24,000 recommendations 중 저장 완료가 0이었다. Seal과 evaluator 결과가 없으며 종료 telemetry도 누락됐다. 또한 정적 코드 검토에서 학습기 입력에 방향이 제거된 canonical pair를 넘기는 경로를 확인했다. 따라서 S7은 external performance study를 완료하지 못했고 그 결과를 추정하거나 일반화 증거로 사용하지 않는다. 자세한 판정은 [S6/S7 closeout](research/supplementary_validation/S6_S7_CURRENT_CLOSEOUT.md)에서 확인한다.

## 무엇을 입증하지 못했나?

- 참 구조를 모르는 실제 현장에서 어떤 오류를 발견할지.
- 실제 제조라인에서 개입이 생산량·품질·안전을 개선하는지.
- 독립 제조공정 모집단에 대한 일반화.
- 정책 전체를 결합한 통합 production algorithm.
- 실제 전문가 시간/금전 비용 또는 universal optimal B.
- T5 superiority/noninferiority 또는 graph repair의 graph-free 대비 우월성.

## 팀 사용 절차

1. 이 문서와 [`FINAL_RESEARCH_FRAMEWORK.md`](FINAL_RESEARCH_FRAMEWORK.md)를 읽어 전체 질문과 스토리를 파악한다.
2. 발표 수치는 [`FINAL_RESEARCH_EVIDENCE_MATRIX.md`](FINAL_RESEARCH_EVIDENCE_MATRIX.md) 및 링크된 원 결과물에서 인용한다.
3. 연구보고서는 framework의 9장 구성안, 발표는 10장 슬라이드 구성을 따른다.
4. 모든 표·그림에 cohort, unit, budget, loss, CI type 및 evidence status를 표시한다.
5. 결론은 “조건부로 유용할 수 있다”의 범위로 두고, 실제 공장 효과·경제성·안전을 주장하지 않는다.

기존 기록에서 확인된 역할은 오성민의 연구 설계/실험/통합, 정창민의 Research C M1–M4 사후 메커니즘 분석 및 PR #40 기여다. 황주희의 과거 역할은 기존 기록을 보존하되 확인되지 않은 기여를 새로 만들어내지 않는다. 남은 팀 업무는 원고 검토, 그림·표 배치, 발표 연습과 질의응답 분담이다.

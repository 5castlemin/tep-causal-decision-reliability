# 최종 발표 증거 가이드

## 발표 중심축

질문은 “한정된 그래프 수정 예산을 어떤 오류에 배분해야 의사결정 성능을 효율적으로 개선할 수 있는가?”로 둔다. 현장 적용 성과가 아니라, oracle-assisted 구조 수리 정책을 통제된 synthetic/semisynthetic 조건에서 비교한 연구다.

## 권장 흐름과 증거

1. **문제와 동기:** 그래프 정확도만으로는 실제 의사결정 가치를 보장할 수 있다는 문제 설정. 근거: 최종 보고서 §1–3.
2. **방법:** FN/FP/REV/UNRES, task zone, M1–M4, 고정 edit 비용, S0/Full Greedy 비교. 근거: Research C contract 및 최종 보고서 §4.
3. **핵심 실험:** C Held-out B=2, 200 independent SCM; delta +0.07484, CI [0.05090, 0.09877]. 근거: `FINAL_RESULTS_TABLES.md`.
4. **메커니즘:** path absence/flat prediction, 효과 부호, DAG 제약의 사례. 5/6 M4 우세 disagreement는 경로 복원이고 사례 …000139는 기존 경로에서 행동 방향 차이. 근거: 원본 Ledger 감사.
5. **외부 강건성:** 단일 DRF DGP의 200 G0, delta +0.03422, interval [0.00617, 0.06535]; 두 정밀도 목표 미달. 근거: D 재감사.
6. **반례·기준선:** M4의 더 낮은 edit count와 약간 높은 손실, graph-free baseline의 동률, C/D의 조건부 한계.
7. **기여·한계:** 비용 제약 구조 수리라는 의사결정 중심 framing. Oracle-assisted, synthetic/semisynthetic, 외부 실측 부재, 일반화 제한.

## 그림·표 제안

- C의 예산별 Regret 곡선과 paired CI.
- D의 정책별 손실/비용을 서로 다른 축·척도로 제시(절대 loss를 C와 직접 비교하지 않음).
- 대표 사례 3개: 경로 복원, 기존 경로 효과 방향 차이, 구조 수정 후 악화.
- 결과표에는 모집단/조건, 분석 단위, estimand, CI, 반례를 함께 표기.

## 예상 질문

- **실제 공장에서 검증했나?** 아니다. D도 제조공정 기반 공개 반합성 표본에 DRF를 다시 적합한 단일 생성환경이다.
- **200개 D 표본은 독립 공정인가?** 아니다. 고정 DGP/학습 프레임의 200 graph-corruption draw다.
- **M4가 최선인가?** 보편적으로 그렇지 않다. edit 횟수는 줄였지만 D 손실은 FG보다 약간 컸고 C에도 반례가 있다.
- **왜 graph-free를 비교했나?** 무작위화 생성환경에서 직접 연관성 기반 모델이 경쟁 기준이 되며, D에서 FG와 동률이었다.
- **수정 비용은 현장 비용인가?** 아니다. 단위 간선 수정 횟수만 측정했다.
- **메커니즘은 확증됐나?** 아니다. 원본 ledger로 검증한 사후 탐색 설명이다.

각 슬라이드의 주장 강도는 `FINAL_CLAIMS_EVIDENCE_MATRIX.md`를 따른다. 새 분석 결과나 확인되지 않은 팀 기여를 추가하지 않는다.

# Research F-Lite 최종 보고서

## 연구 질문과 범위

참조 인과그래프를 검증 정책에 공개하지 않을 때, 제한된 전문가 질의 예산을 어떤 관계에 배분하면 downstream Decision Regret을 줄일 수 있는지 조사했다. Research C의 Development 64 SCM과 기존 Held-out 200 SCM을 재사용했다. 새 SCM/G0/관측자료는 생성하지 않았고 Research D의 개입 평가도 수행하지 않았다. Held-out 결과는 F-Lite 설계 이전부터 이미 알려져 있었으므로 본 결과는 사후 탐색이며 새로운 확증 평가가 아니다.

## 정책과 정보 경계

비교 대상은 무작위, local Gaussian BIC fit-based, BIC 대안 상대가중치 기반 suspicion-only, Ridge 예측 중요도 impact-only, suspicion×impact 결합 정책이다. 모든 reference-blind 정책은 전체 unordered pair를 후보로 보며 한 쌍당 질의비용은 1, 예산은 B=0–4다. 질의 상태는 `U→V`, `V→U`, `NO_EDGE`이며 순환을 만드는 답은 pending으로 보류하고 DAG 합법성을 재검사한다.

Policy에는 G0, 관측 학습자료, 과제와 행동/목표 계약만 전달한다. 모의 전문가는 참조 그래프를 알고 요청받은 pair의 답만 반환한다. Evaluator는 추천을 잠근 뒤에만 호출한다. 이는 인터페이스 수준 분리이며 OS sandbox나 실제 맹검 전문가 실험은 아니다. BIC 의심도는 확률이 아니고 impact는 현재 misspecified learner 예측에 대한 점수다.

## 핵심 결과: perfect simulated expert, B=4

Held-out 평균 Regret은 S0 0.093439, Random 0.081223, Fit-based 0.003770, Suspicion-only 0.006061, Impact-only 0.017270, Decision-weighted 0.016281이었다. 제안 정책과 Random의 paired 차이(Random−제안)는 +0.064942 (95% SCM bootstrap [0.045436, 0.086207])로 제안 정책에 유리했다. 반면 Fit-based−제안은 −0.012511 [−0.023669, −0.003856], Suspicion-only−제안은 −0.010220 [−0.019854, −0.002602]로 더 단순한 두 정책이 낮은 손실을 보였다. Impact-only−제안은 +0.000988 [0, 0.002881]이며 200개 중 198개 SCM에서 동률이었다. 그러므로 결합 점수의 추가 이점은 확인되지 않았다.

제안 정책은 4회 질의 중 평균 0.45회 간선 수정, 평균 1.72개 잔여 오류, 20% action 변경을 보였다. Fit-based/Suspicion-only는 각각 약 1.9회 수정으로 잔여 오류가 0.27–0.29개였고 regret도 더 낮았다. 이는 오류 발견·구조 수정·의사결정 가치가 서로 다른 결과임을 보여준다. Oracle-assisted M4의 regret은 0.001435지만 참조 DAG를 사용하므로 동등 정보의 blind 경쟁자가 아니다. Graph-free association은 0.038725였다.

## 가상 전문가 오류 민감도

정확도 .9/.8, SCM당 16회, B=4의 별도 가상 categorical corruption 결과에서도 Held-out decision-weighted regret은 각각 0.038087/0.060056이었다. Random보다 낮았지만 Suspicion-only(0.021620/0.039240)보다 높았다. 두 accuracy 모두에서 suspicion-only−제안 paired nested bootstrap 구간은 각각 [−0.027095, −0.007539], [−0.031251, −0.011203]이었다. 이는 실제 전문가 오류율 추정이 아니다. 오류 답변 중 최종 그래프에 반영된 수, 최종 오류로 남지 않은 수, 새 relation 오류 및 pending 상태를 별도 감사했다.

## 검증·실행 이력

저장된 core 추천/평가행은 Development 12,480/12,480, Held-out 39,000/39,000이며 4,224개 선택 질의의 score replay가 모두 정책 argmax와 일치했다. Core 최초 실행은 Development 추천 단계의 stale-view 문제로 evaluator 전에 중단되어 같은 입력·seed로 수정 후 실행했다. 성공 실행은 모든 산출물을 저장한 뒤 summary 변수 shadowing으로 종료됐으며, 이후 저장 결과를 독립 감사하고 summary-only 오류를 수정했다.

선택 F3 첫 실행은 Development 8,192 recommendation/evaluator rows를 저장한 다음 summary schema 오류가 발생했다. 자료를 보존해 read-only 재집계하고 같은 seed로 Held-out만 완료했다. 총 F3 trajectory는 Development 8,192개 저장본 재사용과 Held-out 25,600개 실행이다. 현 실행 wall time 2,343초, 선행 Development attempt 648초, 관측 peak process RSS 468 MiB였다. 새 입력표본은 0이다.

## 해석과 결론

F-Lite는 기존 SCM을 이용해 reference-blind-at-the-interface query prototype의 평가 가능성을 보여준다. 제안된 결합 점수는 무작위 질의보다 나았지만 fit-based·suspicion-only보다 성능이 낮았고 impact-only와 거의 같았다. 전문가 응답 정확도 민감도에서도 이 상대적 한계는 유지됐다. 따라서 F-Lite의 결과는 의사결정 중요도와 구조 의심도를 결합한 정책의 우월성 증거가 아니라, 단순 heuristic 비교에서 그 추가 가치가 확인되지 않았다는 사후 진단이다.

가까운 선행연구로 downstream 최적화용 Targeted Causal Elicitation (Ibrahim et al., 2022), iterative Expert-In-The-Loop Causal Discovery (Ankan & Textor, 2025), noisy expert 응답을 쓰는 Bayesian Causal Preference Elicitation (Bonilla et al., 2026)이 있다. 따라서 targeted causal elicitation 일반의 새로움이나 최초성을 주장하지 않는다. [관련 연구 검토](RESEARCH_F_RELATED_WORK_AND_NOVELTY.md)

## 제출 자료

정책·정보 경계·실행 감사·결과·주장 매트릭스·발표 그림은 이 디렉터리의 계약 및 보고서 파일에 있다. 공개 저장소에는 집계자료, 코드, hash와 SVG만 포함하며 per-SCM 응답·추천 파일은 로컬에 보존한다. Research C–D–E 동결 자산과 기존 종료 상태는 변경하지 않았다.

## 최종 저장결과 감사 추가

후속 read-only 감사는 원본 C DB의 payload와 저장된 F-Lite recommendation/evaluator/query-score 파일을 직접 읽었다. C SCM 및 관측 배열을 seed로 재생성하는 `restore_cohort()`는 이번 감사에서 호출하지 않았다. 4개 C DB 해시와 저장 F 입력 해시가 기대값과 일치했고, 감사 전후 C DB hash도 동일했다. 상세 비교와 범위는 [최종 감사](RESEARCH_F_FINAL_AUDIT.md), 기계 결과는 `outputs/final_audit_aggregate.json`이다.

기존 Random `action_change_rate`는 32회 중 한 번이라도 변경된 SCM 비율이었다. Held-out B=4에서 그 값은 27.0%이며, SCM별 32회 중 평균 변경 비율은 4.09%다. 두 값은 별도 지표다. 공통 SCM bootstrap index를 사용해 재집계한 Held-out pointwise 95% 구간은 Random−제안 `[0.045611,0.086164]`, Fit−제안 `[-0.023466,-0.004040]`, Suspicion−제안 `[-0.020108,-0.002814]`, Impact−제안 `[0,0.002881]`이다. 기존 comparator별 순차 RNG 구간은 역사 결과로 보존했다.

저장 answer를 재생한 B=4 pending audit에서는 deterministic policy–SCM 1,056행 중 6행에 pending relation이 남았고, 최종 DAG에서 개별적으로 적용 가능한 pending은 0건이었다. 재생 결과는 저장 graph/pending 수와 모두 일치했다. Graph-free 9.52는 원 aggregate에 남은 historical diagnostic이며, 구조 수리 비교에서 잔여 오류 수는 `n/a`로 해석한다. Oracle-assisted M4와 query policy의 질의 비용은 같은 자원이 아니다.

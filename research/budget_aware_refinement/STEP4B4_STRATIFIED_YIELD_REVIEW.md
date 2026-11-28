# Step 4B-4 stratified Q-common yield review v2

**판정: 층화 수율 분석 보완, 운영 상한은 자원 통합검증 전 미동결.** 원본 2,000회 고정층 원시 결과는 보존한다. 균등 층 target 추정량 `p_hat = sum_h (1/20) p_hat_h`. 이번 층별 n은 모두 100이므로 637/2000 = 31.85%와 같다. Plug-in 층화 SE=.008581.

Bonferroni 조정 exact Clopper–Pearson 층별 구간의 가중 endpoints가 이루는 보수적 95% 동시 구간은 [22.316%, 43.749%]이다. 이는 weighted mean의 직접 exact 구간이 아니라 모든 층을 동시에 덮는 보수적 구간이다. 5층은 0/100, 1층은 100/100; 경계 표본도 참 수율 0 또는 1을 증명하지 않는다.

| Template | 노드 수 | 성공/100 | 비율 | 층별 CP 95% |
|---|---:|---:|---:|---:|
| chain_mediation | 6 | 0 | 0.0% | [0.000, 0.036] |
| chain_mediation | 7 | 0 | 0.0% | [0.000, 0.036] |
| chain_mediation | 8 | 17 | 17.0% | [0.102, 0.258] |
| chain_mediation | 9 | 34 | 34.0% | [0.248, 0.442] |
| chain_mediation | 10 | 56 | 56.0% | [0.457, 0.659] |
| fork_branch | 6 | 0 | 0.0% | [0.000, 0.036] |
| fork_branch | 7 | 0 | 0.0% | [0.000, 0.036] |
| fork_branch | 8 | 0 | 0.0% | [0.000, 0.036] |
| fork_branch | 9 | 35 | 35.0% | [0.257, 0.452] |
| fork_branch | 10 | 34 | 34.0% | [0.248, 0.442] |
| observed_common_cause | 6 | 11 | 11.0% | [0.056, 0.188] |
| observed_common_cause | 7 | 17 | 17.0% | [0.102, 0.258] |
| observed_common_cause | 8 | 23 | 23.0% | [0.152, 0.325] |
| observed_common_cause | 9 | 56 | 56.0% | [0.457, 0.659] |
| observed_common_cause | 10 | 57 | 57.0% | [0.467, 0.669] |
| multiple_directed_paths | 6 | 100 | 100.0% | [0.964, 1.000] |
| multiple_directed_paths | 7 | 62 | 62.0% | [0.517, 0.715] |
| multiple_directed_paths | 8 | 50 | 50.0% | [0.398, 0.602] |
| multiple_directed_paths | 9 | 44 | 44.0% | [0.341, 0.543] |
| multiple_directed_paths | 10 | 41 | 41.0% | [0.313, 0.513] |

## 미래 추출과 cap planning

후속 후보마다 20개 template×node-count 층 중 하나를 확률 1/20로 독립 추출하고 Q eligibility를 적용한다. 고정된 층별 수율에서 acceptance indicator는 weighted mean 수율의 iid Bernoulli가 된다. 이는 진단 행렬의 100개씩 고정 할당과 다르다. 모든 층을 유지하며 적격 구조를 빠짐없이 채택해 P | Q-common 조건부 목표 모집단을 지킨다. 성공이 높은 층에 quota를 사후 배정하지 않는다.

Cap planning은 Bonferroni 97.5% simultaneous CP lower bound 21.745%와 conditional target-attainment 97.5%를 결합한다. N=64 cap 362, N=200 cap 1,036. 안정된 층별 수율과 미래 균등 무작위 층 추출에서의 planning 계산이지 무조건 보장 또는 승인된 운영 상한은 아니다. 이 두 실패확률의 union bound가 약 5% 이내가 되도록 한 보수적 기준이다.

고정 표본의 p_hat(1-p_hat)/n plug-in 분산은 0/100층에서 0이 된다. 이를 알려진 무불확실성으로 취급하지 않는다. CP confidence set 안에서 p(1-p)를 최대화한 별도 upper variance도 코드에 두었다. 층별 n=100은 구간이 넓고, 0 성공층을 제외할 근거가 아니다.

설정 SHA `6cbfa721bc0107f19b2b8957fc44a9e2679a467fd2096bcd4ac9dfc466e232fe`, raw source SHA `c0ce611bf7aeca025407d884111fa919175c5bd091f9d55537de022948aa406e`, v2 JSON SHA `1a7d7e37e373ed8f128d938dab794a34d5be9658009720f7e4b6a424a73c38c6`.

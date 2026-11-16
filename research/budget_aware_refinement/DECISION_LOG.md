# 결정 기록

- 2026-11-05 제안: 비용 제약의 구조 개선 정책과 후회 비교를 별도 연구 후보로 구축. 기존 RESEARCH_DESIGN.md와 완료 결과를 대체하지 않는다.
- 주 제안은 참조를 사용하는 oracle이며 비oracle 정책은 후속 별도 계약. 선택 지표 외 지표의 변화도 허용·기록.
- 균등 몫과 고정 순서를 예시로 사전 제안; 예산의 자유 배분 oracle과 구분. 겹치는 수정은 한 번만 과금. 통계적/계산 예산은 미승인.
- 선형 합성 우선, 비선형 별도 요인 실험; CausalMan과 TEP는 외부 Gate가 충족될 때만. 그 실패를 핵심 합성 연구의 자동 실패로 삼지 않는다.
- 이전 ERROR-CONFIRM의 REDESIGN_REQUIRED, CausalMan acceptance 실패 및 TEP 미검증은 취소되지 않았다. 특정 정책 우월성은 미결정이다.

## 2026-11-10 Step 0 공식 전환
15개 F1 지표 조합은 ARCHIVED_METRIC_COMBINATION_DESIGN.md에 보존하고 FN/FP/REV 7조합×Global/T 14개와 세 baseline으로 전환한다. 4개 기존 지표는 진단으로 유지한다. unit 비용과 표준화 평균반응 후회, 학습 SD ddof=1 및 후보 5수준은 채택; 예산 grid는 Step4에 동결. 실제 효과로 수정 순서 선택 금지. 신규 실험·GT 생성·시뮬레이터 실행 없음.

## 2026-11-10 Step1 유형 일정 교란 수정
Global 유형순 대 T 전체 위치순은 혼재이므로 공통 seed 회전 균형 유형 일정과 유형 내 위치 tie로 변경. 유형별 실현 수는 DAG·예산 때문에 다를 수 있어 별도 기록한다. 과거 Step0 규칙과 같은 estimand로 혼합하지 않는다. 소형17개 테스트 통과, 전체 엔진·기준선은 미구현.

## 2026-11-10 Step2 구현
Step1 계약을 policy_engine 및 graph_adapter로 구현. 명시적 스키마와 oracle graph-only 필드 경계를 채택하고 모델 및 평가기와 분리한다. 추가 참조 경로를 읽는 Path F1 기준선을 같은 정보량 정책으로 표시하지 않는다. 기존 계획·실험 결과 변경 없음; CI 확인 전 Step2 미완료.

2026-11-10: 엔진 커밋 f1494e7의 GitHub Actions 42777224302 및 관련36개 소형 검사를 확인해 Step2 DONE. mock 경계와 실제 Step3 SCM 연동의 검증은 분리한다. 연구 파일럿 미실행.

2026-11-10: 승인된 Step3 개발 파일럿은 S1/S7 첫 직접 과제와 기존 remove_key 조건을 결과 확인 전 고정했다. 전부 후회 0이며 단일 FN이어서 정책 우열을 주장하지 않는다. 실제 SCM 어댑터에서 추천 뒤 정답을 평가한다. Step3 IN_PROGRESS: 재현 및 CI 미완료.

2026-11-10: 기존 직접 과제의 삭제 간선은 조작 상류이며 예측 불변임을 재분석했다. 기존 경로 과제와 사전 명세된 복합 오류 보완 456회는 기존 자료 해시를 보존하는 탐색 진단이며 확인 실험이 아니다. CI 확인 전 Step3 IN_PROGRESS.

2026-11-10: Step3 완료 — 구현 531486a의 전체 149개 로컬 검사와 GitHub Actions 42780815082 성공, 사전계획된 보완 결과 보존. 두 개발 SCM 결과는 확인적 주장이 아니며 Step4 등록에서 표본·비용·실패·분석 규칙을 결정한다.

2026-11-10: Step4에서는 선택 정책과 동일한 오류 유형·일정의 matched Random 및 matched Path-F1 기준선을 제안한다. 기존 Step3 full-pool 결과는 유지한다. 64/200과 0.10은 후보이며 생성 적격성·자원·실패 규칙 미검증으로 동결하지 않는다. STEP4_READINESS_AUDIT.md.

2026-11-10: 사용자는 검증된 진행 중 개발물을 main의 공식 기준으로 통합하도록 지시했다. Development Integration은 Step4–9 완료나 연구 가설 검증이 아니다. 최소 1명 검토와 CI·동결 자산 확인을 유지한다. 기존 인과 결과와 미병합 연구는 보관한다.

## 2026-11-15 Step 4B-1 critical design audit (additional review, not frozen)

- Preserve historical v1/v2 outputs. Create a separate v3 feasibility matrix that checks all six atomic orders for disjoint one-each FN/FP/REV recipes. C requires mixed types and related plus peripheral errors, but does not require path survival or an on-route FN. Failed cells are never replaced with another error type.
- The outcome-blind B type schedule yielded FN 13/66, FP 67/67, REV 11/67. Under the current path-preserving recipe, direct-only FN/REV are infeasible. Do not interpret a pooled B mean as a fair type comparison.
- Across 17,185 graph-only matched Global/Task-Focused pairs, 97.2% lack two DAG-valid same-type candidates; final graphs differed in 12 (0.07%). The present topology matrix cannot identify H2 as a primary confirmatory effect. Any H2 challenge cohort must be preregistered with separate target-population weights.
- Fixed positive-control fixtures test policy distinguishability for all three error types; they are not policy performance evidence. Matched Random/Path-F1 comparisons do not substitute for an H2 Global-versus-Task-Focused contrast. Resolve H1/H2 status, estimands, and weights in Step 4B-2. Step 4B-1 and Step 4 remain IN_PROGRESS / NOT FROZEN.

## 2026-11-15 Step 4B-2 population and hypothesis design proposal (not frozen)

- Correct C recipe eligibility to enumerate all six atomic edit orders for each one-FN/one-FP/one-REV recipe. The fixed-order prefix could reject a recipe with a valid alternate intermediate-DAG order; preserve v3 and write the corrected result as v4.
- Keep the general topology population P and the structural two-candidate H2 cohort Q separate. Q eligibility uses only topology, fixed task roles, error locations, DAG-valid individual corrections, surviving path, and budget 1; no policy outcome, SCM effect, or regret enters selection.
- Define the primary selected-policy-vs-matched-Random estimand separately from H1 error type/location and H2 Global-vs-Task-Focused ordering. H1 has no current clean type-only support because direct FN/REV are absent and FP must occupy a non-truth dyad. H1 is proposed as conditional/type-location exploratory reporting. H2 in P is a population-average paired contrast; H2 in Q is a distinct conditional contrast, structurally exposed at budget 1 but not yet powered or confirmed.
- Retain C path-survival strata (v4 133/200 survive, 67/200 disconnect), and overlapping location tags. Upstream-of-Action labels do not imply harmlessness under hard-do(X).
- The 64/200 SCM sizes, inferential tests, missingness/failure rules, compute caps, and target weights remain candidates for later Step 4B work; no final sample or analysis contract is frozen.

## 2026-11-15 — Step 4B-3 주 추정량 및 RNG 설계안 (미동결)

- 보존된 v4 P 구조 행렬에서 P/B=4의 14개 정책 각각과 Matched Random 5개 seed를 대응 실행한 34,370쌍 모두 최종 그래프가 같았다. 이 결과는 regret 비교가 아니므로 P/B4를 보조·탐색적 벤치마크로 낮추고, Q-common/B=1의 Global 대 Task-Focused 대응 H2 질문을 계획상 주 확인 질문으로 제안한다.
- Q-common은 동일 SCM/task가 FN·FP·REV 세 구조 적격성을 모두 통과하는 outcome-blind subset이다. 유형별 1/3 동일 가중으로 SCM당 1개 대응값을 구성하며, 현재 진단에서는 34/100 topology ID만 공통 지지에 포함됐다. 64/200 eligible SCM은 현재 수율만으로 보장할 수 없고 목표 모집단 가중치·attempt cap·shortfall은 Step 4B-4에 남긴다.
- RNG는 protocol/cohort/master seed/SCM ID/template/node count/attempt/stream/replicate 키의 canonical JSON SHA-256 domain separation으로 파생한다. 이는 재현 가능한 명명 스트림 분리이지 수학적 독립성 증명은 아니다. Global/Task-Focused는 같은 type schedule seed를 공유하고 Random draw seed만 분리 가능하도록 Step 2 엔진에 선택적 인자를 추가했다.
- 새 context-keyed feasibility 결과는 v1 별도 파일로 보존한다. v1-v4 및 B2 원시는 변경하지 않았다. RNG 키 체계 변경과 B 행렬이 세 오류유형을 모두 시도하는 설계 변경이 함께 적용되어 과거 수치와 단순 RNG-only 비교는 하지 않는다.
- Step 4 전체는 IN_PROGRESS / NOT FROZEN. 표본·정밀도/검정력·추론/CI·실패·resource cap 동결은 수행하지 않았다.

- Step 4B-3 gate is DONE for the primary-estimand recommendation, P+B4 distinguishability audit, context-keyed structural feasibility, raw/report consistency, tests, frozen assets, exact-head CI, and Self-Review. This does not mark Step 4B-1/2 or Step 4 overall complete; Step 4B-4 inferential/sample/failure/resource contracts remain required.


## 2026-11-15 — Step 4B-4 추론·표본·실패 계약 부분 검증

- 주 설계 후보 Q-common/B=1/H2는 유지하되 아직 추론 계약으로 동결하지 않는다. P 생성분포에 20개 층 균등 확률로 제안하고 구조적 Q 적격만 rejection하는 방식을 권고한다. 2,000개 topology-only 후보 중 637개 적격(31.85%, exact 95% CI 29.81–33.94%); 층별 0–100% 수율 및 작은 층 표본 때문에 64/200 목표의 운영 cap은 확정하지 않는다. 원시 결과와 설정 hash는 STEP4B4 sampling contract에 기록.
- SCM 단위 `D_i=(D_FN+D_FP+D_REV)/3`와 type 1/3 가중은 계획 추정량으로 구체화. 모든 세 유형 값이 필요하며 누락 시 평균 분모를 바꾸지 않는다. Ridge/recommend failure의 k=0 fallback은 학습·truth 입력 유효 및 common grid 조건에만 허용하며 원 실패를 보존한다.
- Outcome-free calibration에서 n=200 paired t의 zero-heavy skew type-I 0.136, CI coverage 0.864; percentile bootstrap coverage 0.8545였다. 두 방법 모두 주 분석으로 선택하지 않는다. 대칭성을 요구하는 sign-flip도 mean 검정으로 대체 채택하지 않는다.
- 이 단계는 계획 기반 표본·자원 초안의 부분 증거이며 Step 4B-4/Step4를 완료하지 않는다. 새 SCM/관측/효과/Regret/confirmation은 생성하지 않았다.


## 2026-11-15 — Step 4B-4 remediation v2: calibration and resource decisions

- The v1 alternative CI coverage field is wrong (checked zero, not true .10); v1 raw retained. Corrected v2 tracks null and alternative true means separately and detects exact constant rows before NumPy variance.
- Independent-seed zero-heavy-skew Type I .13635/.13415, CI coverage .86365/.86585 at n=200. This is finite-sample t/bootstrap calibration failure, not the v1 coverage-reference bug. No mean-inference method is selected; Q-common/B1/H2 estimand remains unchanged.
- Replace pooled CP interpretation with fixed-stratum point estimate and Bonferroni simultaneous exact CP endpoint interval [.2232,.4375]. Future uniform-random strata plus Q rejection is the prospective target sampler. Caps 362/1,036 are planning only.
- Missingness scenarios show 0.1% independent type-cell MCAR -> 54.865% probability all 600 cells observed; infrastructure retry remains one same-key replay. No complete-case confirmatory fallback or zero imputation.
- A 512x10 numeric dummy matrix (not SCM observations) measured Ridge/prediction path; provisional caps 30min total, 2sec per unit, 512MiB RSS and 100MiB disk are proposals only pending actual runner enforcement. Step4B4 remains IN_PROGRESS.

## 2026-11-15 — Step 4B-4 Final Decision Gate

- **Inference: Option B.** Preserve Q-common / indirect-only / B=1 / gamma=1 / Task-Focused vs ID-ordered Global; SCM-level `D_i=(D_FN+D_FP+D_REV)/3` remains the target. The current generation/loss contract implies neither a proven finite range nor a variance/tail bound. Paired t and bootstrap fail the severe zero-heavy-skew calibration stress. Stop searching for a universal small-sample mean test; suspend confirmatory superiority/equivalence claims. Report the arithmetic mean, SCM distribution, denominator and type-specific summaries. T-based intervals may be shown only as assumption-dependent reference estimates.
- Keep N=64 development and N=200 confirmation as fixed operational targets for descriptive estimation, not power guarantees. Development does not tune N after confirmation access. Uniform 1/20 template×node-count proposal plus acceptance of every structurally Q-common candidate defines the P|Q-common target; no post-hoc quota weights. Pilot template counts 107/69/164/297 (Chain/Fork/Common Cause/Multiple Paths) are descriptive composition only.
- Adopt candidate-attempt ceilings 362 development / 1,036 confirmation as finite planning stop limits, not yield guarantees. Preserve every rejection; shortfall means no target-population inference and no outcome-driven replacement. Missing FN/FP/REV makes the SCM composite missing; no zero imputation, denominator change or complete-case replacement.
- Added the fsynced mock stage ledger and graph/Ridge/recommendation/truth-test-double runner. Forced child-process termination/resume, torn-tail repair, duplicate/conflict rejection, policy and GT failures, incomplete vector, disk stop and stage-boundary wall/unit checks are covered. Disk ceiling is enforced; wall/unit overrun is recorded after a stage; RSS is best-effort monitoring only. These limits are not preemptive OS containment; process-isolated hard timeout/RSS controls remain a Step 4C gate.
- Step 4B-4 design decision may be marked DONE after final CI/Self-Review; Step 4 overall remains IN_PROGRESS / NOT FROZEN. No new SCM, observation, effect, regret, confirmation SCM or Step 5 run.

## 2026-11-16 — Step 4C-1 runner remediation (NOT FROZEN)

The integrated mock runner previously skipped checkpointed stages but held prerequisite graph/model state only in process memory. It now restores integrity-checked stage outputs from JSONL; fitted model state is JSON-serializable. A spawned-process interruption after Graph, Fit, or Recommend resumes in a fresh process and yields a byte-identical final ledger to uninterrupted execution. Event and output canonical hashes, run/config/input/RNG binding, ordering and terminal checks were added. SCM composite rejects invalid/nonfinite numbers and incomplete FN/FP/REV vectors. Spawned stage timeout can terminate the worker; RSS is sampled including native process working set and terminated when observed over the cap, so overshoot remains possible. Total wall cap is still stage-boundary detection. Production SCM generation and GT evaluator are not implemented; mock truth output is not an evaluation. The active contract pointer now distinguishes current Q-common/B1/H2 Option B from superseded P/B4 proposals. Step 4C-1 remains IN_PROGRESS; no Step 5 or confirmation SCM run.

## 2026-11-16 — Step 4C-1 production integration follow-up (NOT FROZEN)

- Failed stage attempts are separate from successful completed-stage checkpoints. Requery after Ridge/GT failure, timeout, RSS, disk, or wall limit returns the recorded failure and does not promote it to success. Recovery validates event/output digests and run/SCM/cohort/config/input/RNG bindings; only a torn final JSONL line is recoverable.
- Active per-SCM stage wall time accumulates across restarts; downtime is excluded. Child timeout duration records observed elapsed time. This is not a cohort-wide time cap. Unit timeout uses spawned-child termination; RSS is sampled with kill-on-detection and may overshoot; ledger bytes are checked before append.
- Add a structural proposal interface (fixed-probability 20 strata, topology/task/Q-common checks, error recipes) and a paired Step 3 recommendation/GT adapter. They are outcome-blind and fixed-fixture validated only. No coefficients/noise/observations or new Step 4 SCM GT evaluation occurred.
- Do not claim production-ready: `STEP4_SCM_GENERATION_SPEC.md` still leaves coefficient sign assignment, numeric eligibility thresholds, and duplicate SCM definition/admission unresolved. The active Q-common/B1 Option B estimand and targets remain unchanged; Step 4C-1 remains IN_PROGRESS and Step 4 remains IN_PROGRESS / NOT FROZEN.
## 2026-11-16 — Step 4C-1 strict task and production integration (not frozen)

- Resolve the active `indirect-only` definition literally: require an Action→Target path of length at least two and exclude a direct Action→Target edge. Keep direct-only and direct-plus-indirect classifications distinct. The common-cause scaffold pair is a preference only when it is genuinely indirect-only; otherwise choose from the indirect-only class. This clarifies the current intended population; it does not add a task class.
- Preserve the historical 2,000-cell Step 4B-4 Q-yield raw. In a new v2 structure-only replay using the same seed/candidate cells, strict eligibility is 595/2,000 (29.75%) rather than 637/2,000 (31.85%). All 42 removed acceptances are common-cause preferred pairs with a direct edge. Same-rule planning caps change from 362/1,036 to 386/1,104. These remain estimates, not guarantees. Settings SHA `b5fc9bb2f3767d1592aa560626c985eb7c853a4969cba2f5d5e899645564d52b`; raw gzip SHA `959078f02df14f54af5915327115bab6d78e1b19f010c285cea2eb0f9de79ae3`.
- Implement the existing proposed linear SCM parameters: sorted-edge coefficient assignment, magnitude Uniform[.25,.8], independent fair signs, node noise SD Uniform[.8,1.2], independent centered Gaussian disturbances, and one shared 512-row observational matrix. No total effect or outcome-based filtering; zero/small/cancelling effects remain. Numerical rejection currently covers nonfinite values and zero sample variance only.
- Add analytic intervention means via the SCM equations; intervention replaces the action equation and cuts its incoming edges. Connect a one-proposal production path and validate only with explicit fixed equations/noise. No study SCM, cohort, or Decision Regret experiment is generated.
- Integrated-path child-process interruption after SCM, policy-graph, recommendation, and GT checkpoints resumes with the same terminal result SHA as uninterrupted execution. Remaining before 4C-2: durable cross-ledger duplicate/ID registry, exact Python 3.11 CI and asset verification. Step 4C-1 and Step 4 remain IN_PROGRESS / NOT FROZEN.

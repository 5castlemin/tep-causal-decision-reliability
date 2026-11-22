# Research C SCM/G0 및 End-to-End Fixture 검증

**상태: 구현된 TEST_ONLY 통합 후보 / 계약 미승인 / 미사전등록 / 연구 코호트 미실행**

이 작업은 고정 계수·고정 그래프·결정론적 자료만 사용했다. 개발/독립 평가 SCM 코호트와 연구 성능 결과는 생성하지 않았다. 모든 GT 손실·Regret 값은 테스트 출력에만 존재하며 `TEST_ONLY`로 표시한다.

## 1. 기존 구현에서 재사용한 경로

- `research/budget_aware_refinement/step4_topology_generator.py`: 4개 scaffold template, 6–10 nodes, target edge density 0.2–0.4, 최대 부모 3의 구조 생성기. direct/indirect task 후보가 모두 필요하므로 Research C에는 strict indirect-only pair를 별도로 추출해야 한다.
- `step4c1_scm.py`: signed linear acyclic SCM, edge coefficient magnitude Uniform[0.25, 0.8], independent fair signs, centered Gaussian disturbances, node SD Uniform[0.8, 1.2], 공통 512행 관측자료. Step 4 코호트 generator를 그대로 호출하지 않고, 아래 fixture는 명시 계수와 결정론적 외생값으로만 만들었다.
- `step3_adapter.py`: 관측 평균/표준편차 표준화, 5개 행동 후보 `k∈{-1,-0.5,0,0.5,1}`, Ridge 적합 이후 예측 손실 최소 행동 선택.
- `step4c1_gt.py`와 `step3_adapter.evaluate`: 추천을 고정한 후에만 analytic hard-do response와 GT candidate loss/Regret을 평가한다.
- `src/integrated_pilot.py::fit_model` 및 `src/decision_mvp.py::static_mean_response`: graph-conditioned Ridge와 학습 모델 기반 평균 반응 예측에 재사용했다. 이 학습 예측은 정답 효과가 아니다.

기존 Step 4의 durable ledger/resume runner는 Research C 정책·학습·평가 경로에 아직 결합하지 않았다. 기존 resume 테스트 성공을 새 통합기의 프로세스 중단 복구 증거로 간주하지 않았다.

## 2. SCM/task 모집단 및 G0 설계 후보

`research/original_objective/research_c_candidate_config.schema.json`은 아래 내용을 `PROPOSED_NOT_APPROVED`로 보관하고 cohort execution을 `false`로 고정한다.

### SCM 및 task 후보

기존 4개 topology scaffold와 각 6–10개 노드 조합(20개 strata)을 출발점으로 삼고, Research C에서는 새 domain-separated RNG namespace를 사용한다. Target density는 기존 topology generator의 0.2–0.4 후보 범위, 최대 부모 수는 3이다. 계수는 독립 부호를 가진 signed linear DAG, 절댓값 Uniform[0.25, 0.8], 외생오차는 독립 centered Gaussian 및 노드 SD Uniform[0.8, 1.2]로 후보화했다. SCM당 관측자료는 512행 하나를 생성해 모든 정책·예산에서 공유한다.

Task는 정답 DAG에서 길이 2 이상 유향 경로가 존재하고 `X→Y` 직접 간선은 없는 strict indirect-only ordered pair 전체에서 균등 추출한다. 선택에는 계수, 총효과, GT 손실을 사용하지 않는다. 적격 pair가 없으면 이유를 남긴 구조 거절로 처리한다. 별도 관측자료 holdout은 제안하지 않는다. 추천은 공통 512행 관측자료의 모델 기반 예측으로, 평가는 별도 analytic GT로 수행한다. 따라서 결과의 해석 대상은 이 합성 SCM·행동 격자 안의 의사결정이지, 새 제조 배치로의 예측 일반화가 아니다.

현재 scaffold는 chain, fork/branch, observed common cause, multiple directed paths를 포함한다. 공통원인·다중경로는 template로 등장할 수 있고 collider와 peripheral connection은 augmentation에서 생길 수 있으나, 각 SCM 안에 모든 motif가 존재하도록 강제하지 않는다. motif 발생 수는 기록해야 한다.

### G0 오류 부식 후보

`research/original_objective/g0_candidate.py::corrupt_graph_candidate`는 다음 한 가지 구체적 scenario를 실행 가능하게 구현했다.

1. 각 정답 adjacency를 독립적으로 확률 0.15로 손상 시도한다.
2. 손상 시도 조건부로 FN, REV, UNRES를 각각 1/3로 선택한다.
3. 각 정답 nonadjacent unordered pair마다 확률 0.05로 FP를 시도하고 방향은 1/2씩 선택한다.
4. pair별 domain-separated hash stream을 사용한다. 그래프 입력, task ID, master seed가 같으면 같은 이벤트를 재현한다.
5. reversal 또는 FP가 cycle을 만들면 DAG-invalid로 기록하고 적용하지 않는다. 재추출·재시도는 하지 않는다.
6. 모든 attempted/applied/rejected 이벤트와 pair 위치를 기록한다. 오류 유형·위치가 특정 지표에 맞춰지도록 결과 기반으로 보정하지 않는다.

이는 관측 오류 발생률에 대한 경험적 모델이 아니라 **고정 corruption scenario 후보**다. true-edge 오류 기회는 adjacency 수에, FP 기회는 nonadjacency 수에 비례한다. 따라서 FN/REV/UNRES와 FP의 기대 개수는 같지 않다. DAG 거절은 REV·FP의 실현 비율도 바꿀 수 있으므로 attempted 수와 applied 수, DAG 거절을 별도 분모로 보존해야 한다.

### M4 편향 및 기회 차이

G0는 task-zone과 off-task pair에서 같은 true-adjacency 오류 확률을 쓰고, 어떤 오류 유형도 반드시 생기게 하지 않는다. 그러므로 G0 자체가 M4 후보를 강제하지는 않는다. 다만 task zone 크기와 topology motif에 따라 M4의 후보 수는 달라진다. 현재 정책 엔진의 G0-fixed opportunity 점수는 support가 작은 active component의 사건 하나에 더 큰 정규화 개선량을 줄 수 있다. M4 support가 off-task support보다 작으면 동일 사건 수라도 M4 subset의 greedy 점수가 상대적으로 커질 수 있다. 동일한 기본 손실 가중치가 이 정규화 효과를 상쇄하지 않는다.

따라서 주 결과에서 초기 opportunity와 applied error counts를 `metric × error type × task/off-task`별로 보고한다. matched-opportunity 통제 분석은 topology 내 가능한 후보 수/오류 발생 수가 유사한 조건을 사전 지정해 별도 분석해야 한다. 그 통제는 자연 모집단 주 분석을 대체하지 않는다. 정책 Regret 결과를 보고 corruption rate를 조절해서는 안 된다.

## 3. 구현한 End-to-End 경로와 경계

`research/original_objective/e2e_fixture.py::run_fixed_fixture`는 다음을 수행한다.

`고정 GT DAG/SCM 및 G0 → M1–M4 구조 수정(S0 + 15 subset + Canonical Oracle) → 수정 directed graph와 공통 관측자료를 이용한 Step 3 Ridge 적합 → 공통 행동 격자의 예측 손실 및 행동 선택 → 선택 동결 → analytic GT hard-do 평가 → TEST_ONLY regret 기록`

- `policy_engine.run`에는 DAG 구조만 제공한다. 계수, 개입 효과, GT 손실/최적 행동, regret은 호출 서명·점수·동률 처리에 없다.
- `step3_adapter.prepare`에는 관측자료, task, 수정 그래프 및 기존 Ridge/response 함수만 넘긴다. GT spec은 넘기지 않는다.
- 추천 후보를 보존한 뒤 `step3_adapter.evaluate`에 정답 방정식을 넘겨 동일 action grid의 GT 선택 손실과 최선 손실, regret을 구한다.
- 자료 해시·최종 그래프 해시·task·delta·행동 grid·Ridge alpha를 fit cache key에 포함한다. 캐시는 메모리 내 TEST_ONLY이고 정책별 레코드는 각각 보존한다.
- 같은 action 및 `k`는 같은 GT 데이터/목표에서 같은 regret을 가져야 한다. 실행 중 assertion으로 점검한다.
- 남은 UNRES adjacency는 Step 3 fitting adapter에서 표현할 모델 계약이 없다. 이를 조용히 absent로 처리하지 않고 `GRAPH_INPUT_UNSUPPORTED`로 fail closed 한다. UNRES를 허용하는 fitting 해석과 resolve/delete 비용 결정은 실험 전 승인/구현 Gate다.
- `NO_INITIAL_ERRORS`, `NO_REPAIR_CANDIDATES`, graph 입력 미지원, fit 실패, recommendation 실패, GT 평가 실패를 별도 상태로 기록하도록 확장했다. 실패 policy를 평균에서 성공 처리하지 않는다.
- `run_research_cohort()`는 항상 `PermissionError`로 중단한다. 이 브랜치에는 연구용 proposal loop/durable registry/checkpoint-resume가 없다.
- `delete_unresolved` 비용 항목은 config candidate에 있지만 정책 엔진은 이를 repair candidate로 생성하지 않는다. 연구 계약은 UNRES resolve/delete 허용 여부와 남은 UNRES에 대한 learner 입력 해석을 함께 정해야 한다.

## 4. 테스트 fixture 실행 및 수치

테스트 input은 8개 노드, 명시 계수 6개인 고정 선형 DAG다: peripheral `A→B`, `C→D`, task path `X→M→Y`, observed common cause `Z→X` 및 `Z→Y`. 512행 외생값은 고정된 사인/코사인 수열로 산출하고 RNG를 사용하지 않았다. G0에는 `A→B` 누락(M1), `C→D` 반전(M3), task path `X→M` 누락과 `Z→X` 반전(M4), GT에 없는 `A→Y` 경계 연결(M2)이 포함된다. 이건 단일 손계산·코드 연결 fixture이며 SCM 표본이 아니다.

재현 명령:

```powershell
uv run --python <CPython-3.11.15-path> --with-requirements requirements.txt python -m unittest tests.test_original_objective_e2e_fixture -v
uv run --python <CPython-3.11.15-path> --with-requirements requirements.txt python scripts/run_original_objective_e2e_fixture.py
```

Windows CPython 3.11.15 및 저장소 `requirements.txt`의 pinned NumPy 2.4.3/pandas 3.0.1/NetworkX 3.6.1 환경에서 한 번 실행한 결과:

- 최종 직접 fixture 테스트: 10/10 통과. 정책 엔진·독립 감사·Step 3 회귀를 포함한 최종 관련 테스트 명령은 34/34 통과.
- B=0,1,2,3,4 × 17개 전략 레코드 = 85 policy-budget 기록. 전부 `TEST_ONLY_OK`; 연구 코호트 0개.
- 최종 graph/data/task/fit 설정이 다른 in-memory model fit cache 항목: 24개. 여러 policy가 동일 hash의 graph를 공유했지만 각 policy 기록은 유지.
- 이 단일 실행에서 측정한 정책 실행 wall time: 0.0544초(모듈 import 전처리 제외), Windows 프로세스 peak working set: 67,260,416 bytes, serialized JSON 결과: 369,634 bytes.
- Registry 및 checkpoint 사용량은 0 bytes가 아니라 **이번 fixture runner에 해당 저장 경로가 없어서 생성되지 않음**. cohort resume는 시험하지 않았다.

단일 fixture 수치는 nearest-rank percentile 또는 SCM별 worst case가 아니며, 코호트 운영 상한이나 추정치로 사용하지 않는다. 크기/밀도/topology별 변동, topology rejection 비용, Registry/ledger I/O, crash resume, 운영 자원 caps를 재지 않았다.

결과 파일: `research/original_objective/test_outputs/e2e_fixture_v1.json`. 모든 regret은 TEST_ONLY로 식별된다.

저장소 전체 테스트는 CPython 3.11.15와 pinned requirements 임시 uv 환경에서 291개 실행, 288 pass, 2 fail, 1 error였다. 실패/오류 3건은 기존 Step 4 보존/준비 검사에서 발생했다: (1) Step 4B4 raw JSONL은 Git blob/manifest SHA `9c12a2…`와 일치하지만 Windows worktree의 CRLF raw-byte SHA는 `e8a1c6…`로 불일치, (2) Step 4C1 `WORK_LOG.md`는 실제 정규화 SHA `351869…` 대 manifest 기대 `608efe…` stale binding, (3) Step 4 production-readiness 테스트는 현재 수정/미추적 파일이 있는 dirty worktree를 거부했다. 세 파일/manifest는 이번 작업에서 수정하지 않았다. 이 전체 테스트 실행 이후 추가된 G0 cycle rejection 및 fit-failure 테스트는 최종 관련 suite에서 통과했다.

## 5. 실행량 및 표본 목표 후보

기본 예산 B=1–4에서 15 subset + Canonical Oracle은 최대 `16 × 4 = 64` 정책·예산 graph variants이고, S0는 공통 초기 graph 1개이므로 캐시 전 모델 적합 경로의 상한 후보는 SCM당 65개다. 실제 distinct graph 수는 보통 이보다 작을 수 있으나 미리 가정하지 않고 graph hash로 계산한다. S0를 매 예산마다 기록해도 동일 model을 중복 적합할 필요는 없지만 비교 레코드는 예산별로 둘 수 있다.

민감도 후보(초기 오류 수 normalization, FP Rule B, orient cost 2 및 3, λ 0.5 및 2, M4 β stress 2종)는 각 B=2에서 최대 8개의 대안 설정이다. 각 설정의 16개 수정 policy variant(15 subset + canonical)를 모두 다른 graph라고 가정하면 main 65 + sensitivity `8 × 16 = 128`, 최대 193 fit graph/settings 경로/SCM이다. 실제로는 hash-identical graph가 cache 될 수 있다. 이 계산에는 proposal 생성/거절, ledger 비용, 고장 재개, 조사/분석 처리를 포함하지 않는다.

64 development 및 200 independent evaluation SCM은 **운영 계획 후보**만 제시한다. 기존 B의 64/200은 실행 경험이지 C의 통계적 sufficiency 증거가 아니다. 독립 분석 단위는 SCM이고, SCM 내부 policy/budget/repeated task는 반복 측정이다. proposal cap은 C task/G0 생성률을 구조 전용으로 사전 점검하기 전까지 설정할 근거가 없다. 단일 fixture의 자원 관측치로 cohort wall/disk cap을 확정하지 않는다.

## 6. 최종 실험 전 사용자 승인 묶음

아래 결정이 내려지기 전에는 실행이 차단된다.

| 승인 묶음 | 이번 후보 | 결정이 결과에 미치는 영향 |
|---|---|---|
| Population/SCM/task | Step 4 signed-linear family 재사용, 20 topology×node strata, strict indirect-only task pair 균등추출, 계수·잡음·512행/공통 자료·5개 action grid·delta 규칙 | 지원 모집단·task mix·행동 비교·추정 불확실성 |
| G0/corruption | true adjacency q=.15, conditional FN/REV/UNRES equal; absent pair FP r=.05; DAG-invalid event 기록 후 non-redraw; zero-support 허용 | 각 metric/event opportunity, M4와 다른 metric의 후보 수·정책 점수 |
| Repair/economic proxy | Rule A, G0 fixed opportunity; equal selected-M weights, M4 active-component β equal; edit cost=1; `P_all` equal event weight, λ=1 total multiplier; B=1–4; canonical baseline | subset trajectory와 실제 수정 예산. 금액/제조비용으로 해석하지 않음 |
| Estimand/analysis/cohort | SCM-level paired regret, S0 대비 변화 및 동일 예산 정책 대비; 64/200은 proposal, cohort-specific namespaces; 다중 정책·예산의 기술 보고; 독립 평가 N/cap은 미확정 | 정책 비교 및 일반화 주장 범위 |
| Operational gate | UNRES 잔존 처리, crash-safe registry/checkpoint, 실패·shortfall/no-replacement, OS/runtime/resource caps, 원시 인벤토리/코드 binding | 재현성·운영 실행 가능성 |

각 표의 값은 승인을 받은 계약으로 기록되어 있지 않다. 특히 candidate config의 rates와 fixture status만으로 연구를 시작해서는 안 된다.

## 7. 기존 데이터 보호 및 구분

Step 4 FROZEN 파일, Step 5/6 원시 Registry/JSONL과 A/B 결과, 이전 발표자료는 수정하지 않았다. 연구 C의 산출물은 새 package, 테스트, TEST_ONLY JSON 및 새 보고서에 한정한다. 이 fixture 결과는 원래 Step 5/6 실험이나 연구 C 가설 결과로 합산될 수 없다.

## 8. 판정 및 다음 단계

구조 정책→기존 Ridge/공통 행동 격자→analytic GT 평가 연결은 고정 fixture에서 작동한다. 하지만 이 상태를 production cohort 준비 완료로 보기는 어렵다. 특히 UNRES가 잔존한 그래프의 학습 의미, 실제 SCM/task/G0 법칙과 proposal cap, cohort durable resume/registry, 자원 cap과 평가 분석계약은 승인 또는 미구현이다.

**새 개발 SCM 실험 진입: 현재는 불가.** 다음 한 단계는 위 승인 묶음에서 최소 다섯 범주의 값을 명시 승인하는 것이다. 승인 뒤에만 구조 전용 모집단/G0 feasibility dry-run과 자원 계획을 별도 실행하고, 그 결과를 검토한 뒤 새 코호트 실행을 따로 승인한다. 어떠한 단계도 연구 C를 preregistered라고 자동 표시하지 않는다.

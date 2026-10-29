# 동일환경 제조 인과–개입 벤치마크 적합성 검토

2026-10-29. **최종 판정: CONDITIONAL-CANDIDATE — CausalMan을 한 번의 제한된 재현 acceptance 대상으로 우선한다.** 현재 원래 연구의 전체 흐름이 검증됐다는 완전한 YES는 아니다. 공식 채택·새 환경 실험 승인이 아니며,다른 후보를 연결하기 위해 없는 GT나 simulator 동등성을 가정하지 않았다.

이번에는 공식 원문·고정 소스·Git tree/작은 배치 메타데이터만 읽었다. 외부 패키지 설치/import,모델 pickle 로딩,대형 데이터 다운로드,시뮬레이션,발견 학습,SCM 적합,do 연구실험은 모두0이다. 외부 소스 파일을 이 저장소에 복사하지 않았다. 연구 산출물은 이 보고서와 `CANDIDATES.json`,`DECISION.json`뿐이며,상태·연구 기록은 저장소 규칙에 따라 별도 갱신한다.

## 1. 기존 TEP가 원래 가설을 검증하지 못한 정확한 이유

CPCaD의1499×31 관측 자료·28간선 참조·7개 frozen graph의 구조 채점은 보존된다. 그러나 그 자료를 만든 모델/제어기/초기화/시간 집계와 별도 Python TEP가 동일하다는 생성 계보가 없다. 내부 상태 의존성은 센서 직접 DAG와 다르고,숨은 밸브/제어기 기억을 센서 현재값에서 제거할 수 없다. 따라서 기존 F1을 Python의 조작 결과에 붙이면 환경 차이와 구조 오류를 분리할 수 없다.

PR21의 별도 효과 연구 STOP은 GT 부재만 때문이 아니다. 명령 API와 국소 반응은 있어도 출처 있는 후보 정책·비자명한 목표/H·실패 포함 손실을 정당화하지 못했다. PR23의 합성 오류 위치 계약은 정밀도/자원 및 종단 비용 근거로 REDESIGN_REQUIRED다. **이번 탐색은 어느 과거 판정도 수정하거나 TEP를 재개하지 않는다.**

## 2. 고정한 공식 출처와 조사 수준

| 후보 | 고정 소스/자료 | 실제 조사 |
|---|---|---|
| CausalMan | [Bosch commit 17529da](https://github.com/boschresearch/CausalMan/tree/17529dad5ec8b8c691494c617b9af4533aa44bf8),package0.1.0;[논문 v1](https://arxiv.org/abs/2502.12707v1) | Python 소스/선언/투영/GT·개입 호출 경로 및 작은 CSV 메타데이터 정적 확인 |
| Causal Chambers | [package0.2.8 commit 9fb5d82](https://github.com/juangamella/causal-chamber-package/tree/9fb5d82e391bb91a89a64f2e1c9b6ae8e7aed6d6);[data commit 0c8a77e](https://github.com/juangamella/causal-chamber/tree/0c8a77ea14bd4437b1fdd79adc1aa91ac2342569) | GT 모듈/제한 simulator/실물 API/데이터 생성 문서 확인,연결·다운로드 없음 |
| PenSimPy | [commit e08fc71](https://github.com/Mohan-Zhang-u/PenSimPy/tree/e08fc71fef193448f3ee9a304187dc92b88f3acc);[IndPenSim 데이터 v2](https://data.mendeley.com/datasets/pdnjz7zz5x/2) | reset/step/recipe/Gym·제어 경로와 데이터 출처 확인,ODE 실행 없음 |
| Industrial Benchmark | [Siemens commit afeed69](https://github.com/siemens/industrialbenchmark/tree/afeed6933ed1aff760a350f6300ae963bfc7bc04);[공식 논문](https://arxiv.org/abs/1709.09480) | visible/Markov state·action/reward·seed·source/license 확인 |
| causRCA | [commit d932ab7](https://github.com/causalgraph/causRCA/tree/d932ab7ad91abe889b67e4d87186d0fccec7fbc1);[데이터 DOI](https://doi.org/10.5281/zenodo.15876410) | real/HIL 구분,expert graph,시간 제약,공개 실행 자산 확인 |

상태의 VERIFIED는 **해당 좁은 사실을 소스에서 확인**했다는 뜻이다. 예를 들어 API 정의 존재의 VERIFIED가 API 실행 PASS를 뜻하지 않는다. PARTIAL은 특정 근거는 있으나 핵심 연결 미확인,BLOCKED는 현재 주장에 필요한 자산/의미가 미확보,UNKNOWN은 판단 근거 부족이다. 각14항목의 구체적인 소스 경로·행·링크·Git blob hash와 미확인 조건은 `CANDIDATES.json`에 있다. 어느 후보도 이번에 REPRODUCIBLE로 승격하지 않았다.

## 3. 14개 적합성 항목

| 항목 | CausalMan | Chambers | PenSimPy | Industrial Benchmark | causRCA |
|---|---|---|---|---|---|
| 1. 공정·실제/합성 | VERIFIED | VERIFIED | VERIFIED | VERIFIED | VERIFIED |
| 2. 공식 데이터/시뮬레이터 출처 | VERIFIED | VERIFIED | VERIFIED | VERIFIED | VERIFIED |
| 3. 논문·소스·데이터 버전 계보 | PARTIAL | PARTIAL | UNKNOWN | PARTIAL | PARTIAL |
| 4. 관측·내부·잠재 변수 | PARTIAL | PARTIAL | PARTIAL | VERIFIED | PARTIAL |
| 5. GT 관계 정의 | PARTIAL | PARTIAL | BLOCKED | BLOCKED | PARTIAL |
| 6. F1/Directed F1/SHD 가능성 | BLOCKED | PARTIAL | BLOCKED | BLOCKED | PARTIAL |
| 7. Action/Target·물리적 의미 | PARTIAL | VERIFIED | VERIFIED | VERIFIED | PARTIAL |
| 8. 동일 조건 복수 조작 | PARTIAL | PARTIAL | PARTIAL | PARTIAL | BLOCKED |
| 9. 독립 개입 효과 평가 | PARTIAL | PARTIAL | PARTIAL | PARTIAL | BLOCKED |
| 10. 비자명한 후보/목표/손실 | UNKNOWN | UNKNOWN | PARTIAL | PARTIAL | UNKNOWN |
| 11. 독립 실행·학습/선택/평가 분리 | PARTIAL | PARTIAL | PARTIAL | PARTIAL | PARTIAL |
| 12. 용량·실행·메모리·라이선스 | PARTIAL | PARTIAL | PARTIAL | PARTIAL | PARTIAL |
| 13. 기존 방법론 호환성 | PARTIAL | PARTIAL | BLOCKED | BLOCKED | PARTIAL |
| 14. 차단 조건·해결 가능성 | PARTIAL | BLOCKED | BLOCKED | BLOCKED | BLOCKED |

위 표의 근거는 아래 후보별 분석이다. API/문서가 존재하는 상태와 같은 환경의 데이터–GT–독립 개입이 실제 일치하는 상태를 분리했다.

## 4. CausalMan: 가장 유망하지만 정합성 acceptance가 필요하다

### 4.1 원래 질문과 가장 가까운 이유

생산라인의 물리 모델·조건부 공정 모드·부분 관측을 SCM으로 정의하고,관측과 개입을 공통 FCM 경로로 샘플링한다. 실제 공장 원시 관측이 아니라 **전문가/물리 기반의 합성 제조 벤치마크**다. 원문은 혼합 변수·비선형·잠재 원인을 명시하고 일부 제품에서 다른 개입 반응을 다룬다. 그러나 논문의 실험은 발견graph→공통 추천→독립 손실이라는 우리 전체 파이프라인의 완료 증거는 아니다. [논문 §4–6](https://arxiv.org/html/2502.12707v1#S4)

실제 호출은 `intervention_dict`→`sample_batch`→`sample_CausalGraph`→`FCM.intervene_on`으로 이어진다. `intervene_on`은 유입 간선을 제거하고 대상 식을 고정값으로 바꾸며,선택한 graph의 위상 순서로 후속 식을 평가한다. 수학적 hard do의 구체적인 소스 근거다. 실행·모든 branch의 정합성을 증명한 것은 아니다. [sample 경로709–758행](https://github.com/boschresearch/CausalMan/blob/17529dad5ec8b8c691494c617b9af4533aa44bf8/causalman/utils/graph.py#L709),[식 대체516–570행](https://github.com/boschresearch/CausalMan/blob/17529dad5ec8b8c691494c617b9af4533aa44bf8/causalman/fcm.py#L516)

### 4.2 현재 소스에서 확인한 중요한 불일치

1. **반환값 충돌:** 실제 `sample`은 `obs,mag,admg,full,dag,int_table`의6개를 반환한다. README quick start114행과 생성 CLI75/113행은4개를 unpack한다. 현재 고정 버전에서는 정적 계약 충돌이며,실제로 예외를 실행·관측한 것은 아니다. 다음 검사는6개 API를 직접 사용해야 하며 기존 CLI를 작동하는 재현 명령이라고 주면 안 된다. [실제 반환278–285행](https://github.com/boschresearch/CausalMan/blob/17529dad5ec8b8c691494c617b9af4533aa44bf8/causalman/causalman.py#L278),[CLI75행](https://github.com/boschresearch/CausalMan/blob/17529dad5ec8b8c691494c617b9af4533aa44bf8/causalman/generate_causal_inference_data.py#L75)
2. **이름만 intervention인 메서드:** `apply_interventions`87–89행은 dictionary를 비우고 반환한다. README의 직접 `intervention_dict` 경로와 구분한다. 이 메서드 이름만 보고 개입 PASS로 처리하지 않았다.
3. **샘플링 graph와 반환 GT 단계:** `sample_batch.py`144–177행은 conditional function 일부가 hardcode돼 있다는 주석과 함께 level1을 샘플링하고 level2를 참조로 읽는다. 경로/배치 결과를 합치지만 반환 graph는 마지막 경로/배치의 level2다. 모든 생성행을 그 graph 하나가 설명하는지 확인해야 한다. `dag2fcm`366–408행은 term에 없는 간선과 식이 없는 노드도 제거한다. 이를 무시하고 반환 DAG를 실제 샘플 식의 직접 부모 정답으로 확정하면 안 된다. [sample_batch](https://github.com/boschresearch/CausalMan/blob/17529dad5ec8b8c691494c617b9af4533aa44bf8/causalman/sample_batch.py#L144),[dag2fcm](https://github.com/boschresearch/CausalMan/blob/17529dad5ec8b8c691494c617b9af4533aa44bf8/causalman/utils/graph.py#L366)
4. **관측 노드 집합 변동:** `causalman.py`228–249행은 상수인 비개입 변수를 숨기고 개입 대상은 상수가 돼도 남긴다. 따라서 seed/정책마다 노드가 달라질 수 있다. 자료를 보고 임의로 GT 노드를 지우지 말고 훈련 전 고정 관측 universe와 처리 규칙을 계약해야 한다.
5. **작은 반환 N≠작은 실행:** `sample(n_samples=N)`은 먼저 최소 한 배치를 생성한 후 내려 뽑는다.32행 요청이32행의 계산만 한다는 보장은 없다. core import/construct만 확인하는 기존 test는 관측–GT–do acceptance가 아니다.

### 4.3 잠재변수 투영과 기존 F1의 관계

반환 DAG는 잠재 상태를 포함한다. 원래 관측 노드만 남긴 induced DAG는 정답이 아니다. `graph_projections.py`는 latent path로 연결되는 directed edge와 공통 잠재 원인의 bidirected edge를 **서로 다른 타입**으로 보존하는 MultiDiGraph를 만든다. 두 reciprocal arc로 표시된 bidirected 관계를 방향 순환2개로 오독하면 안 된다. ADMG에는 directed+bidirected가 같은 쌍에 있는 bow도 있을 수 있다. [투영164–225행](https://github.com/boschresearch/CausalMan/blob/17529dad5ec8b8c691494c617b9af4533aa44bf8/causalman/graph_projections.py#L164)

MAG 변환은 inducing adjacency를 추가하고 ancestry에 따라 방향을 정한다. 그러므로 MAG directed edge는 원래 물리 방정식의 직접 부모와 같지 않다. FCI 등의 PAG는 다시 관측적으로 식별되는 동치류와 미확정 endpoint를 나타낸다. 정답을 보고 circle/미확정 방향을 유리하게 채우지 않는다. 관측-only라면 같은 universe의 reference MAG/PAG와 adjacency/endpoint·typed distance를 정해야 한다. **기존 Strict Directed F1/SHD 및 핵심 물리 직접 경로 점수를 그대로 붙일 수 없다.**

full 데이터로 모든 내부 상태를 쓴 진단은 별도의 privileged-state 합성 실험이다. 실제 센서 관측 연구라고 부르지 않으며,full 반환과 level2/활성 식이 일치하는지도 먼저 확인해야 한다. 이런 진단을 관측-only 결과와 합쳐 점수 순위를 만들지 않는다. 구조 품질–의사결정이라는 넓은 질문은 유지할 수 있지만 채점 대상 변경은 별도 설계 명시가 필요하다.

### 4.4 규모·설치·권리

| 규모 | README의 관측변수 규모(미실측) | 고정 Git tree의 model-object 크기 |
|---|---|---:|
| micro | 24,single product | 144,812,833bytes |
| small | 약50,multiple products | 199,156,432bytes |
| medium | 약180 | 673,007,331bytes |
| large | 400 초과 | 7,194,286,371bytes |

이는 파일 메타데이터 합이며 내려받아 hash를 확인한 binary나 실행 메모리가 아니다. 네 규모 model objects 합은8,211,262,967bytes(약7.65GiB),저장소 tree 전체 blob 합은8,486,569,298bytes다. 기본 설치는 모든 objects를 package에 포함하므로 micro만 쓴다고 micro 크기만 설치되는 것이 아니다. 소스/설치본·Git 이력·venv를 함께 보관할 공간은 README의 단순8GB 안내보다 커질 수 있다. 공식적으로 검증한 micro-only 설치 절차는 없다. SymPy/NumPy/Pandas/NetworkX 등이 core이고,Graphviz·browser·R/dagitty 등은 선택 기능이다. 현재 wrapper의 투영은 pure Python 경로이나 설치·실행시간·peak RSS는 NOT_RUN이다. [패키징](https://github.com/boschresearch/CausalMan/blob/17529dad5ec8b8c691494c617b9af4533aa44bf8/pyproject.toml#L11)

코드 LICENSE는 AGPL-3.0이고 외부 코드를 이 저장소에 넣지 않았다. 논문에 표시된 CC BY-NC-SA4.0과 software/data 권리를 혼동하지 않는다. `3rd-party-licenses.txt`13–20행은 generic Awesome Project 기재로 실제 data/pickle의 권리 inventory를 확인해 주지 못한다. [Zenodo v1](https://zenodo.org/records/13871097)·[v2](https://zenodo.org/records/14697668)는11.2/11.3GB 기록이며 렌더링된 License 항목에 명확한 조건이 보이지 않았다. 따라서 제3자 데이터 사용·재배포 권리는 UNKNOWN으로 남긴다. 상업 사용 금지나 무조건 사용 허가를 임의 추론하지 않는다. [작은 공식 README](https://zenodo.org/records/13871097/files/README.txt?download=1)는 ID 제외·잠재 투영/비정규화 주의만 제공하며 archive와 현재 generator의 동일성을 입증하지 않는다.

## 5. 나머지 후보가 지금 통합 원가설 환경이 되지 못하는 이유

**Causal Chambers:** 실제 장치의 조작 가능한 광원/편광판/팬/해치와 센서,설정별 참조 graph와 개입 캠페인이 있어 실제 물리 인과 검증의 좋은 후보다. `ground_truth/main.py`는 edge 목록을 제공하고 공개 `lt_interventions_standard_v1`에는 reference/분포 변경 실험과 checksum·generator가 있다. 다만 패키지의 기본 GT는 Mk1이고 새 remote Mk2는 별도 configuration/version을 맞춰야 한다. 원문의 참조는 시간·다른 변수 고정 개입의 의미를 갖고 pressure-control은 피드백도 포함한다. 무조건 정적 DAG로 채점하지 않는다. [GT 소스](https://github.com/juangamella/causal-chamber-package/blob/9fb5d82e391bb91a89a64f2e1c9b6ae8e7aed6d6/causalchamber/ground_truth/main.py#L202),[버전 경고](https://raw.githubusercontent.com/juangamella/causal-chamber-package/9fb5d82e391bb91a89a64f2e1c9b6ae8e7aed6d6/README.md)

패키지 simulator는 fan/pressure 또는 광학 현상의 일부를 결정론적·확률적으로 근사한다. 실제 데이터의 전체 참조 graph와 같은 생성 모델이라는 증거가 아니다. 새 실물 개입은 credentials/장치/설정/세션과 [remote access](https://www.causalchamber.ai/)가 필요하며 이번에 접속·실험을 하지 않았다. 제조 생산라인과 다른 testbed라는 외적 타당성도 남는다. MIT code/CC BY4.0 data,선택 image/torch weights와 실제 lab의 비용은 구분한다. [simulator 범위](https://github.com/juangamella/causal-chamber-package/blob/9fb5d82e391bb91a89a64f2e1c9b6ae8e7aed6d6/causalchamber/simulators/README.md)

**IndPenSim/PenSimPy:** 발효의 feed/aeration/pressure·recipe·PID와 yield라는 현실적인 조작 목적이 있다. `PenSimEnv.reset`은 seed에 따른 초기화,`step`은 제어/ODE 경로,`PenSimEnvGym.step`은6개 조작과 yield reward를 제공한다. 그러나 검토한 공개 트리에서 관측변수 수준 causal GT/시차 비간선 정답을 확보하지 못했다. ODE의 내부 참조를 센서 DAG로 자동 바꾸지 않는다. [reset/step](https://github.com/Mohan-Zhang-u/PenSimPy/blob/e08fc71fef193448f3ee9a304187dc92b88f3acc/pensimpy/peni_env_setup.py#L29),[Gym](https://github.com/Mohan-Zhang-u/PenSimPy/blob/e08fc71fef193448f3ee9a304187dc92b88f3acc/pensimpy/peni_env_gymwrapper.py#L136)

Mendeley v2는 원 IndPenSim의100개 배치·약2.5GB이며 여러 운전/제어·fault regime을 포함한다. 특정 Python commit과 같은 모델/제어/잡음/export로 생성됐다는 연결 manifest가 없다. 따라서 기존 archive와 Python 효과를 연결하면 TEP 문제를 반복할 수 있다. code MIT/data CC BY4.0과 fastodeint C++ 설치 의존성을 확인했으나 설치하지 않았다. 소스는 fast 모드를 검토하더라도 fastodeint를 import하므로 순수 Python fallback이 설치 문제를 자동 해소한다고 단정하지 않는다. [데이터 원출처](https://data.mendeley.com/datasets/pdnjz7zz5x/2)

**Industrial Benchmark:** Siemens의 연속3조작·상충 비용·지연/부분 관측을 갖춘 RL 환경이라 선택 문제 자체는 강하다. 그러나 visibleState와 전체 Markov state가 다르고,검토한 자산에서 관측 노드의 causal direct/lag GT를 확보하지 못했다. latent/history 방정식이 공개됐다고 전체 센서 F1을 만들 수 없다. root Apache2와 Python 파일 MIT header가 다르므로 해당 부분의 notice를 보존해야 한다. [IDS](https://github.com/siemens/industrialbenchmark/blob/afeed6933ed1aff760a350f6300ae963bfc7bc04/industrial_benchmark_python/IDS.py#L86),[공식 설명](https://github.com/siemens/industrialbenchmark/blob/afeed6933ed1aff760a350f6300ae963bfc7bc04/README.markdown)

**causRCA:** 실제 선반 운전과 HIL fault 자료,expert graph/subgraphs가 있어 구조 발견·RCA에 유용하다. 그러나 같은 OPC UA schema라는 사실이 실제 장치와 twin의 DGP 동등성을 보장하지 않는다. 공개 `simulate.py`는 일반 Bayesian-network/random-DAG 도구이지 선반 twin이 아니다. 새 정책/seed로 조작 손실을 평가할 실시간 twin/action API는 이번 조사에서 확보하지 못했다. CNC timestamp는 변수 간 실제 변화 순서를 보장하지 않는다는 제한도 있다. Apache2로 공개됐다는 사실과 fresh 개입 환경의 확보를 분리한다. [공식 데이터 방법](https://github.com/causalgraph/causRCA/blob/d932ab7ad91abe889b67e4d87186d0fccec7fbc1/data/README_DATASET.md#L100),[generic simulator](https://github.com/causalgraph/causRCA/blob/d932ab7ad91abe889b67e4d87186d0fccec7fbc1/src/causrca/cd_models/pkgs/simulate.py#L1)

## 6. 기존 방법론의 이식 범위

| 단계 | 재사용 | 수정·조건 또는 불가능한 이식 |
|---|---|---|
| 발견 알고리즘 | 데이터/설정/실패/seed 기록 방식 | PC/BOSS의 충분관측·점수 가정,DirectLiNGAM의 선형 비정규 가정을 mixed/nonlinear/latent 환경에서 충족한다고 가정하지 않음. 관측-only latent-aware 출력/CI가 필요 |
| 전체 구조 채점 | 명시적 universe·미확정·오류량·분모 기록 | DAG 직접 간선과 ADMG/MAG/PAG edge/endpoint는 다름. typed/equivalence-aware scoring 필요. 기존7graph/28간선/F1 불가 |
| 핵심 경로·위치 오류 | 현재 과제 기준의 경로/주변 정의,중복 쌍 제거 | MAG ancestry/가능·확정 PAG 경로를 직접 물리 경로로 부르지 않음. bidirected는 causal action 경로로 세지 않음 |
| 공통 수치 SCM | train-only 처리/공통 fitting rule/실패 기록 | 정적 Ridge는 diagnostic baseline일 뿐 비선형 혼합/잠재 confounding의 효과 식별기가 아님. graph representation에 맞는 식별·모형 필요 |
| 고정 효과 예측 | 조작 선택과 독립한 효과 크기·부호 평가 | 관측 regression MSE≠do 효과. ID/overlap/외삽 가정을 먼저 명시 |
| 추천·보류 | 같은 후보/목표·추천 hash/실패 a0와 가용률 분리 | latent 구조에서 식별 불가이면 임의 DAG 완성으로 point effect를 만들지 않음. 모든 모델 보류로 퇴화하면 제한 보고 |
| 독립 do 평가 | fresh object/학습–선택–참조–최종 분리 | 같은 seed≠행별 동일 잡음. CausalMan CLI의 root 재사용을 미사용 final로 인정하지 않음. 실제 장치와 simulator 결과 혼합 금지 |
| 선택 손실 | 기준 개선/추가 손실/가용 조건부·운영 손실 분리 | 기존합성 목표0.6·비용0.2를 새 공정에 복사하지 않음. binary 품질의 비적합 확률은 다른 손실 |
| 구조–선택 통계 | 구조/자료/graph/과제/정책의 중첩과 보유 구조 제외 | 한 micro topology의 여러seed/알고리즘은 여러 공장이 아님. 새 독립성·분산·예산이 필요 |

후보의 논문에서 PC/LiNGAM을 실행했다는 사실 자체가 해당 가정이나 우리 추천 파이프라인의 인과적 타당성을 보증하지 않는다. 새 환경에서는 새 관측으로 graph를 새로 학습해야 하며 이번에는 어느 알고리즘도 학습하지 않았다.

## 7. 단 하나의 조건부 파일럿 시나리오

**CausalMan micro의 press-fitting force→binary 품질**을 하나만 제안한다. tolerance LTL이나 quality flag를 바꿔 합격 여부를 재표시하는 task는 실제 생산 조작의 주 비교로 선택하지 않는다.

| 항목 | 조건부 계약 |
|---|---|
| 버전/자료 | 위 고정 commit의 새 micro 자료. 현재Zenodo small/medium을 같은 자료로 혼용하지 않음 |
| 발견 입력 | baseline에서 검증 후 고정하는 V*.Force/ProcessResult가 실제 관측·변동 노드로 있어야 함.없거나 상수면 실패,억지 추가/삭제 안 함 |
| GT/채점 | 경로·배치의 활성 식과 맞는 참조를 확인한 뒤 같은 V*의 ADMG/MAG/PAG 의미로 채점. 기존 직접DAG F1로 축소 금지 |
| Action/Target | `PF_M1_T1_Force` / `Sec_C2_Machine1_ProcessResult` |
| 후보/기준 | source task의16000/30000 두 값,독립 do(16000)가 a0.물리 단위·허용 actuator 정책은 추가 확인 사항 |
| API | fresh `CausalMan(name="causalman_micro",seed=s,parallelize=False)`,dictionary에 force 지정,실제6개 반환값 사용. source signature만 확인/실행안함 |
| 손실 | binaryY가1=True이면 `L(a)=E[1-Y^a]`:비적합 확률.비용 근거가 없으므로 비용항을 생략하며 실제 비용0이라고 주장하지 않음 |
| 효과 | 독립 arm 평균 `E[Y^30000]−E[Y^16000]`,batch/part 구조에 맞는 불확실성.고정 효과 오차와 최종 선택 손실 분리 |
| 분리 | Dtrain512,Vselect256,Rreference arm별512,Ffinal arm별1024 **반환행의 가안**.disjoint effective-seed/whole-part·batch namespace.아직 생성 안함 |
| 선택 평가 | R에서 유한2후보 reference를 정한 뒤 모형/추천 고정,F에서 선택 손실 비교.F자체 최솟값을 unbiased oracle로 부르지 않음 |
| 실패/비자명성 | schema/GT/식/seed/finite 검산 실패 시 착수 중단.식별·추천 실패는 가용률과 a0 운영 손실.결과를 보고 후보를 추가하지 않음 |

원문 task의 높은 force는 이상/범위 밖 스트레스 조건일 수 있다. 이를 안전한 공장 action이라고 인증하지 않는다. source에 hard do가 있다는 사실과 실제 force controller로 구현되는 정책이라는 사실은 별개다. 더구나 잠재 confounding과 관측 support 밖 force의 효과는 구조만 알아도 자동 식별되지 않는다. 유효한 ID/외삽 가정 없이 SCM이라는 이름으로 추천하면 안 된다.

두 후보의 품질 차이와 모형별 선택 변동은 아직 UNKNOWN이다. 언제나 a0가 최선이거나 모든 모델이 같은 조작/보류를 선택한다면 그 사실을 결과로 남기고,원래 지표 비교가 가능한 다양성을 확보했다고 주장하지 않는다. 이 표는 **실행 가능한 완성 계획이 아니라 차단 조건을 명시한 한 시나리오**다.

## 8. 최종 판정과 다음 실제 검증 하나

**CONDITIONAL-CANDIDATE. 가장 유망한 후보는 CausalMan이지만 완전한 YES는 아니다.** 핵심 차단 조건은 둘이다.

1. **고정 artifact–변수–참조 구조 계약:** 허용된 model artifacts/권리·설치 자원,실제6반환 API,경로/배치별 level1 활성 식–level2 참조,고정 관측 mask·정확한 잠재 투영/채점,독립 effective seed를 일치시켜야 한다.
2. **식별 가능한 조작–선택 계약:** force-do의 의미·Target 변동·관측 support/식별과 모형 표현·유한 후보의 비자명한 품질 선택을 정당화해야 한다. hard do를 실제 actuator나 허위 point effect로 바꿔 해석하지 않는다.

**다음 한 가지는 별도 승인 후,고정 micro의 GT–관측–do acceptance를 한 번 수행하는 것**이다. 발견 학습/SCM 적합/정책 연구는 포함하지 않는다. 버전/objects hash·권리/자원을 먼저 확인하고,6개 반환·동일 노드와 활성 식/비간선·투영·force 방정식 대체·후속 재계산·fresh seed/재현·품질 범위를 실제 로그로 판정해야 한다. 실제 output과 cached graph가 다르거나 Force/품질 과제가 성립하지 않으면 실패로 종료한다. source를 조용히 바꿔 통과시키지 않는다.

고정 force–품질 질의에 대해 참조 ADMG의 식별 가능성과 관측 support도 이 acceptance의 과제 Gate로 확인해야 한다. 수치적인 do 샘플 생성 성공만으로 관측 기반 효과 추정·추천이 가능하다고 판정하지 않는다.

소량 N을 명목상 정해도 full batch 비용이 있으므로 현재 small-runtime 완료 명령을 만들어 제공하지 않는다. 기본 설치/대형 pickle 획득·실행은 이번 범위 밖이다. 위 acceptance가 통과하기 전에는3알고리즘 학습·공통 추천기 본연결로 진행하지 않는다. 이것은 또 다른 광범위한 후보 목록/감사 루프가 아니라 한 후보의 구체적 계약을 기각 또는 재현할 검증이다. 통과해도 한 physics-based 합성 생산라인의 기술/방법론 근거이지 실제 제조 복구·안전 검증이 아니다.

## 9. 보존·검사·GitHub 상태

시작시 PR23은OPEN/head1728d85,base PR22였고 main은e960fa8이었다. clean checkout에서 `feature/integrated-manufacturing-benchmark-search`를 분기했다. 기존 PR15~23을 병합하지 않았다. 과거 연구A 결과·TEP STOP·PR23 정밀도/예산·원설계·frozen/Step6는 변경하지 않는다.

이번 소스 조사로 확인한 것은 API/반환/graph 경로의 정적 사실이며,어떤 외부 후보도 실행 PASS가 아니다. 기존 저장소 검사·상태/보존 검사의 실제 결과는 `DECISION.json/validation`에 기록한다. 외부 코드/학습/시뮬레이터 acceptance를 실행한 것으로 표현하지 않는다.

실제 기존 전체 단위검사96개 PASS(66.685초,신규 검사0),상태·동결39개 SHA/변수순서/시계변환·asset·환경계약15case가 PASS했다. 기존5215개 보호 파일과 과거 workstream/연구A·TEP STOP·PR23 판정은 불변이다. JSON 근거 식별자 누락으로 첫 정적 assertion은 실패했으며,기존 note의 식별자를 저장한 뒤70항목/보고서/보존 대조는 PASS했다. CLI가 과거 로그를 덮어쓰는 verify_recovery 본실행은 하지 않았다. GitHub CI는 새 PR의 실제 결과를 별도 확인한다.

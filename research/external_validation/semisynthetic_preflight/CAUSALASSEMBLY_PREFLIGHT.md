# causalAssembly 외부 반합성 Preflight

## 출처와 자료

Step 0의 외부 소스 checkout 및 다운로드 산출물을 재사용했다. causalAssembly 저장소는 commit `8da3729e6383f0e1cbe7740bb6ab7ac4977ac7f9`에 고정되어 있으며 공식 package version은 `1.2.1`이다. 이 checkout의 `LICENSE.txt`는 AGPL-3.0을 선언한다. 별도 파일별 데이터 이용조건을 찾지 못했으므로 후속 배포 시 출처 표시와 라이선스 조건을 검토해야 한다. 원자료와 외부 코드의 사본은 이 저장소에 추가하지 않았다.

공식 논문은 generator 기반이 assembly-line 제조 측정자료이며 physics-informed partial causal reference와 node-wise DRF 조건부를 사용해 공개 semisynthetic samples를 만든다고 설명한다 ([Göbler et al., 2024](https://proceedings.mlr.press/v236/gobler24a.html)). 따라서 아래 CSV는 제조 원자료가 아니라 해당 공개 generator의 반합성 출력이다. 이번 preflight의 DRF 적합은 이 출력에 대한 재적합이므로 외부 자료 기반 **2차 fit generator**라고 표현한다. 그래프는 생성 benchmark/reference이며 98개 모든 간선이 독립 물리 실험으로 입증된 완전한 실제 인과 GT라는 뜻은 아니다.

| 핀된 자료 | 크기/스키마 | SHA-256 |
|---|---:|---|
| `assembly_reference--ground_truth.json` | 44,027 bytes, 공식 graph 자료 | `86378888c66089aebb94616dce121b5e8400414112eb221b78dff3a4ca84cab8` |
| `assembly_sample--assembly_line_500.csv` | 628,862 bytes; 500 × 98, 결측 0 | `afc079bfca962a4746afd316713743d7702ebc7ea00f98255cd8289d72ecef0e` |

이 두 기존 Step 0 다운로드 파일을 다시 다운로드하지 않고 smoke에 직접 사용했다. upstream 코드의 `get_data()`/`get_ground_truth()` 기본 URL은 mutable `main`을 가리키므로 재현 스크립트는 API calls를 `--data-root`에 지정한 해시 검증 파일로 향하게 했다. causalAssembly code checkout은 별도로 pinned commit에서 설치한다.

## 정적 구조 검사

공식 loader로 98개 노드/485개 간선 DAG를 얻었고 모든 graph node가 500×98 자료의 컬럼과 대응했다. 공식 station `Station1`은 6개 노드/7개 내부 간선이다. 원 graph에서 이 station 노드들로 들어오는 외부 parent가 없고 station 전용 임의 projection이 아니다. 제안 후보 `Station1_mp_0 → Station1_mp_4`는 direct edge가 없는 strict indirect path `mp_0 → mp_1 → mp_4`다.

Research C task-zone 정의를 그대로 적용하면 task zone에는 reference edge 2개와 zone node 3개가 있다. Rule A 아래 task-zone 안에는 endpoint `mp_0, mp_4`의 false adjacency opportunity 1개가 있다. off-task 참 adjacency는 5개이고 off-task absent unordered pair는 7개다. 따라서 M1–M4 모두 구조상 오류 유형/분모가 존재한다. 기존 metric engine에서 reference graph 상태의 support는 M1=5, M2=5, M3=5, M4(FN/FP/REV/UNRES)=2/2/2/2로 산출됐다. 이는 구조적 기회 수 검사이지 오류 seed별 정책 선택이나 결과 지표가 아니다.

station1 task는 전체 후보 중 정책 성능을 보고 뽑은 것이 아니다. 작고 공식 station으로 구분되며, 외부 parent가 없고 strict indirect path가 존재한다는 사전 구조조건으로 제한한 예시다. 변수명 `mp_*`의 개별 물리 단위나 장비 조작 가능성은 공개 자료에서 확정하지 못했다. 후속 `do()`는 **반합성 graph의 가상 조작**이며 실제 제조 장비 조작이 아니다.

## 고정 소스에서 확인한 API 계약

| API | 코드에서 확인한 기능·입출력 | Preflight 결과 및 한계 |
|---|---|---|
| `ProductionLineGraph.get_data()` | 무인자 호출, `DATA_DATASET`에서 CSV를 읽어 pandas DataFrame 반환 | 기본 URL은 mutable `main`; 이번에는 pinned Step 0 CSV 경로로 리다이렉트 |
| `ProductionLineGraph.get_ground_truth()` | 무인자 호출, ground-truth JSON에서 다섯 station을 구성한 `ProductionLineGraph` 반환 | 기본 URL은 mutable `main`; 이번에는 pinned Step 0 JSON으로 리다이렉트 |
| `fit_drf(graph, data)` | 각 노드의 부모가 없으면 KDE, 있으면 `P(node|parents)`의 DRF를 적합하고 노드→모델 dict 반환 | R `drf`; 기본 2,000 trees, `min_node_size=15`, `FourierMMD`. `fit_drf` 함수에 seed 인자는 없어서 R global `set.seed`를 명시 |
| `sample_from_drf(size, smoothed)` | 적합한 노드 모델과 DAG factorization에서 DataFrame 표본 생성 | Python NumPy `random_state` 재설정으로 같은 fitted object 표본 재현 확인 |
| `intervene_on(nodes_values)` | intervention node의 incoming edges를 제거한 DAG와 intervention 값을 객체에 저장 | float를 문서상 허용하지만 fixed float do는 아래 sampler 제한 때문에 실제 생성 불가 |
| `sample_from_interventional_drf(which_intervention, size, smoothed)` | 저장된 intervention을 반영해 DataFrame 표본 생성 | `int` hard constant와 `RandomSymbol` soft intervention만 구현; finite float hard constant은 `NotImplementedError` |

`ProductionLineGraph`에는 public `reset_intervention()`이 없다. intervention마다 fresh graph object를 만들고 fitted DRF dict를 연결하는 것이 가능한 초기화 방법임을 코드 및 새 객체 smoke check로 확인했다. Station API 자체는 `ProcessCell`이라 `intervene_on`을 제공하지 않아, pinned 공식 Station1 cell을 구조 변경 없이 `ProductionLineGraph.from_nx` wrapper에 담아 실험 API를 연결했다.

## 실제 실행 결과

다음 재현 실행에서 full graph/자료 loader, Station1 model fit, 관측 표본 생성 및 sample seed 재현을 확인했다.

```powershell
python -m venv ..\causalassembly-preflight-venv
..\causalassembly-preflight-venv\Scripts\python.exe -m pip install -e ..\assembly
..\causalassembly-preflight-venv\Scripts\python.exe -m pip install -r ..\assembly\requirements.txt
$env:R_LIBS_USER = (Join-Path (Resolve-Path ..\causalassembly-preflight-venv).Path 'R-library')
@'
from rpy2.robjects import r
from rpy2.robjects.packages import importr
utils = importr("utils")
utils.install_packages("drf", repos="https://cloud.r-project.org/", lib=r('Sys.getenv("R_LIBS_USER")')[0])
'@ | ..\causalassembly-preflight-venv\Scripts\python.exe -
..\causalassembly-preflight-venv\Scripts\python.exe -X utf8 `
  research/external_validation/semisynthetic_preflight/run_causalassembly_smoke.py `
  --source-root ..\assembly --data-root ..\data `
  --smoke-rows 2 --seed 2031
```

실행 환경은 Python 3.11.15, causalAssembly 1.2.1, NumPy 2.2.6, pandas 2.3.1, NetworkX 3.4.2, SciPy 1.15.3, R 4.5.3, CRAN `drf` 1.3.1이다. Python 의존성은 causalAssembly pinned checkout의 `requirements.txt`로 별도 venv에 설치했다. CRAN 의존성은 venv 밑 별도 `R_LIBS_USER`에 설치했고 repo의 frozen `requirements.txt`는 수정하지 않았다. 전역 R library에는 설치하지 않았다.

`ProductionLineGraph.get_ground_truth()`, `get_data()`, `fit_drf()`를 실행했다. pinned archive 기준 재현에서 6개 station node 모델의 fit은 약 22.3초 걸렸다. 같은 fit object와 같은 NumPy seed로 2개 관측행을 두 번 생성한 결과가 일치했고, 모든 값은 finite였다. `ProductionLineGraph`는 생성자에서 intervention state가 비어 있는 새 객체를 만들어 재사용 가능한 fitted DRF를 연결할 수 있다.

이 실행 시점에는 연속 action 지원 확인이 실패했다. Station1 `mp_0`의 학습자료 중앙값(관측 범위 안의 float)은 `intervene_on()`에는 저장되지만 `sample_from_interventional_drf()`가 `NotImplementedError: Currently only hard and soft interventions are implemented`를 반환했다. 소스는 hard constant intervention을 `int`만 반복 생성하고, 그 외 실수값은 지원하지 않는다. 제시된 변수의 데이터 값은 연속 float이므로 임의 정수 조작은 in-support action 검증으로 볼 수 없다. `RandomSymbol` soft intervention도 fixed hard do와 estimand가 다르므로 대체로 쓰지 않았다. 이후 별도 adapter의 실제 통과 결과는 `../semisynthetic_adapter/HARD_DO_ADAPTER_QUALIFICATION.md`에 기록했다. 이 수정은 upstream API 실패를 덮거나 원자료 검사를 바꾸지 않는다.

DRF R package 설치와 적합은 별도 venv/R library에서 정상 동작했다. R startup은 Windows에서 ABI 모드로 fallback하고 locale warning을 냈지만 적합 및 관측 샘플 생성에는 영향을 주지 않았다. smoke test는 generator fit에 R `set.seed(2031)`, 표본 추출에 NumPy `default_rng(2031)`를 썼다. pinned API의 기본 ProductionLineGraph RNG는 seed 2023이며 sampling RNG를 바꿀 수 있다. `fit_drf()` 함수 자체에는 seed 인자가 없어 재현 스크립트가 R 전역 RNG를 설정했다.

## 정보 노출

500×98 source sample은 generator fitting input으로 읽었다. `mp_0` action support/quantile은 이 input에서만 조사했다. `mp_4`의 training-only support(범위 11–18, distinct 값 8개)도 지원범위 기록에서만 노출됐으며 target/목표는 고정하지 않았다. 응답 평균, 정책 추천, action별 개입 반응 또는 loss/regret은 계산하지 않았다.

API smoke 중 탐색 목적 관측 응답행 25개(8, 5, 4, 4, 그리고 pinned-archive 재현에서 2×2)가 메모리에서 생성됐다. 값은 출력·파일 저장되지 않았고, target의 평균 또는 비교를 하지 않았다. sampler가 float do에서 반환한 개입 결과 행은 없다. 이 노출은 요약 JSON에 기록했으며, smoke 표본은 향후 held-out 평가에 재사용하지 않는다. 공개 논문을 읽었으므로 causalAssembly 전체가 미열람 외부 held-out이라고 하지 않는다.

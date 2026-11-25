# Research D finite numeric hard-do adapter qualification

## 판정과 범위

**`PASS_FLOAT_HARD_DO_ADAPTER` — adapter 기술 적격성만 통과.** causalAssembly의 연속 numeric constant hard-do가 별도 adapter로 실행되는 것을 결정론적 fixture, pinned upstream integer 비교, 실제 pinned Station1 R/DRF smoke로 확인했다. 이 결과는 Research D 분석 계약, 개발 코호트, 평가자료 생성, 정책 비교 또는 Decision Regret 실행 승인이 아니다.

실측 정책 평가 상태는 계속 `DEFERRED`이며, Research C 계약과 동결 산출물은 변경하지 않았다. 이 benchmark는 반합성 참조에 조건부인 외부 robustness 후보이지 실측 제조 개입 검증이 아니다.

## 확인한 upstream 원인

Pinned causalAssembly `8da3729e6383f0e1cbe7740bb6ab7ac4977ac7f9` (`1.2.1`)의 `intervene_on()`은 입력을 intervention map에 보관하고 intervention graph 복사본에서 해당 노드의 incoming edges를 삭제한다. `sample_from_interventional_drf()`는 **원본 객체의 `causal_order`**를 따라 순회하고 intervention 노드에서 메커니즘 호출을 건너뛴다. downstream 노드는 원본 graph에서 얻은 부모 목록 순서로 새 parent DataFrame을 만들어 기존 fitted DRF를 호출한다. hard constant 분기는 `isinstance(value, int)`만 받으므로 Python float와 NumPy 실수 scalar는 sampler에서 거부되며, NumPy 정수도 Python `int`와 같다고 보장되지 않는다.

`DRF.produce_sample(newdata, random_state, n=1)`은 주어진 parent DataFrame과 RNG를 사용한다. root 노드는 `fit_drf()`가 반환한 SciPy `gaussian_kde`를 사용한다. upstream의 fitted node→mechanism mapping을 변경하거나 root/conditional fit을 다시 하지 않아도 이 API를 통해 intervention factorization을 샘플링할 수 있다.

## Adapter 계약

`float_hard_do_adapter.py::sample_hard_do()`는 원본 객체의 graph, fitted model map, RNG, intervention dictionary를 바꾸지 않는 순수 함수형 단일-node sampler다.

- Python `int`, `float` 및 NumPy real numeric scalar를 받는다. bool, NaN/±Inf, 문자열/복소수, 잘못된 size, 누락 node/mechanism, non-DAG 및 implicit RNG를 거부한다.
- 개입 graph 복사본에서 incoming edges만 자르고 outgoing edges를 보존한다. root의 기존 KDE 또는 개입 노드의 conditional DRF 메커니즘은 실행하지 않는다.
- 원본 DAG의 위상 순서는 간선 제거 뒤에도 유효하다. 나머지 노드는 원본 학습 parent order로 fitted KDE/DRF를 사용하고, 개입값과 이미 생성한 parent 값을 전달한다.
- explicit `numpy.random.Generator`가 KDE와 conditional DRF 양쪽에 전달된다. 반환 열은 모델의 `nodes` 순서이며 개입 열은 행마다 정확히 고정된다.
- multi-node intervention, soft intervention, intervention-state mutation, data fitting, support selection은 의도적으로 제공하지 않는다.

Adapter는 finite 값 검증을 수행하지만 action support 판정기는 아니다. 실제 후속 과제에서는 각 action의 관측 support 및 외삽 위험을 평가 결과를 보지 않고 별도로 사전 고정해야 한다.

## 결정론적 fixture

명령 `..\ci-venv\Scripts\python.exe -m unittest tests.test_research_d_float_hard_do_adapter -v` — **7 tests PASS**.

1. `X→M→Y` root `do(X=.125)`의 수학적 값과 downstream 입력 검증.
2. `Z→X→M→Y` non-root do에서 `Z→X` 메커니즘 생략, Z 및 downstream 메커니즘 보존.
3. non-descendant 메커니즘/결과의 보존.
4. `do(X=a)`, `do(X=b)` 후 별도의 observational sampling에서 intervention 상태 오염이 없음.
5. 같은 seed 재현, 다른 seed의 비개입 stochastic root 표본 변화.
6. bool/nonfinite/문자열/복소수/표현범위 초과 정수 invalid 값, 잘못된 size/RNG, missing node/mechanism fail-closed.
7. `smoothed=False` root bootstrap의 replacement sampling 및 seed 재현.

추가 검사에서 개입 graph는 incoming edge만 삭제하며 원 graph는 그대로였다. graph topology와 fitted mechanism 객체를 보존했다.

## Pinned upstream integer 호환성

동일한 개발용 `Dev_X→Dev_Y` graph, 동일 SciPy KDE와 conditional mechanism, action `do(Dev_X=1)` (개발 fixture support 안), sample size 5, `smoothed=True`, 동일한 seed 상태로 upstream `intervene_on()` + 공식 sampler와 adapter를 비교했다. DataFrame 값·행·열이 정확히 일치했다. conditional mechanism이 받은 parent 열 순서는 `Dev_X`였다. intervention adjacency에서도 incoming edge가 제거되고 outgoing edge가 유지됐다.

## 실제 R/DRF integration smoke

합성 fixture 6개와 정수 호환 검사를 통과한 뒤, 기존 pinned 파일을 다시 사용해 Station1의 DRF 6개를 적합했다. 개발 전용 노드는 task 후보 action/target과 구분한 `Station1_mp_2`; 값은 training sample 중앙값으로 정하고 문서·출력에 수치를 노출하지 않았다. seed `2718`, draw당 2행, 동일 seed 반복 2회, **총 최대 4행**으로 고정했다. 두 반환 표본은 전부 finite였고, 개입 값은 정확히 고정됐으며, 열 순서와 fitted mechanism identity 및 original graph 보존, state 비누출, 같은 seed 재현을 확인했다.

실행 명령:

```powershell
$env:R_LIBS_USER = (Join-Path (Resolve-Path ..\causalassembly-preflight-venv).Path 'R-library')
..\causalassembly-preflight-venv\Scripts\python.exe -X utf8 `
  research/external_validation/semisynthetic_adapter/run_adapter_integration.py `
  --source-root ..\assembly --data-root ..\data --seed 2718 --rows 2
```

실제 실행 결과: causalAssembly `1.2.1`, Python `3.11.15`, NumPy `2.2.6`, pandas `2.3.1`, NetworkX `3.4.2`, R `4.5.3`, R `drf` `1.3.1`; 최종 bounded run의 Station1 fit은 12.568 s, 두 번의 2행 샘플링은 41.555 s였다. 최종 smoke 코드를 확장해 fitted training data와 native R fit object 보존을 추가 검사했고 통과했다. 이 작업에서 성공한 두 번의 adapter smoke 실행은 각각 최대 4행, 누적 **8 response rows**를 생성했다. 두 실패한 실행은 response sampling 전에 종료되어 개입 표본을 만들지 않았다. Windows R 환경은 ABI mode fallback 및 locale/`sh` 경고를 냈지만 성공 실행은 exit code 0으로 끝났다. stdout에는 요약 메타데이터만 포함했고 센서 response 값이나 평균은 출력하지 않았다. 누적 8행 모두 exploratory smoke exposure로 폐기하며 개발·평가자료로 재사용하지 않는다.

## 정보 경계와 남은 조건

이 코드는 fitted generator를 evaluator 전용 함수에만 전달한다. 어떤 policy learner/recommender도 이 모듈에 import되거나 호출되지 않았고 추천·학습·평가 stage 자체를 이번에 구현하지 않았다. 따라서 실제 future train/evaluation split, policy freeze, process-level access control의 end-to-end 통합 시험은 **미실행**이다. 초안 계약은 evaluator 전용 generator sampling을 추천 입력으로부터 분리하고, 별도 RNG를 쓰도록 제안한다. 이를 본실험 전에 구현·검증해야 한다.

공식 paper는 원 데이터가 제조 assembly-line 측정자료이며 graph의 partial causal ground truth는 공정 physics 분석을 통해 구성됐고, conditional DRF를 결합해 공개된 semisynthetic samples를 만든다고 설명한다 ([Göbler et al., 2024](https://proceedings.mlr.press/v236/gobler24a.html)). 이번에는 해당 공개 sample에 DRF를 재적합했다. 따라서 fitted DGP는 **외부 제조자료 기반 반합성 표본에 대한 두 번째 적합**이다. 물리 GT 또는 외부에서 독립적으로 확정한 실 mechanism이라고 하지 않는다. pinned source repo는 AGPL-3.0을 선언한다. adapter는 upstream 소스를 복제하거나 수정하지 않고 공개 API와 fitted model object를 사용했다.

다음 진입점은 별도 검토·승인을 받은 연구 계약 초안이다. 특히 supported actions, learner-training/evaluator sample separation, task/loss/scale, graph/error/seed cohort, uncertainty와 one-generator conditional claim을 잠가야 한다. 이 adapter의 기술 PASS가 외부 robustness study를 자동 승인하지 않는다.

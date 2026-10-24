# ENV-MVP acceptance — 승인 실행 결과

2026-10-24. **PASS_EXAMPLE_IID_FCM_ONLY**: 직접 선언한4노드 검증 fixture에서 참조 그래프·관측·실제 do를 같은 계약으로 연결했다. 제조 generator/실물 공정의 검증이나 Track B 채택은 아니다.

## 실행과 재현

사용자가 별도로 승인한 소규모 실행만 수행했다. PR6→7→8→9는 모두 OPEN/stacked이고 최신 각 CI 성공을 확인했다. PR9 head `baf03e900a021d3d646779da219fd6bbd0de14ad`에서 `feature/env-mvp-acceptance`를 분기했다. main7b16638·기존 frozen/Step6/적합/원시는 변경하지 않는다.

source: causalAssembly commit `8da3729e6383f0e1cbe7740bb6ab7ac4977ac7f9`의 무변경 `causalAssembly/models_fcm.py`, SHA `c1f1b7f6b62c8916ebd23cb0002cdad1e9fcfb995b81cfae9558271987c4290e`. 이전에 실제 회수한 파일을 읽었다. 전체 package 대신 이 모듈만 직접 import한 시험이다. R/rpy2/DRF·생산라인 generator는 설치/실행하지 않았다. 원본 코드 패치 없음.
[고정 원본 모듈 취득 URL](https://raw.githubusercontent.com/boschresearch/causalAssembly/8da3729e6383f0e1cbe7740bb6ab7ac4977ac7f9/causalAssembly/models_fcm.py). 재현자는 이 파일의 SHA를 대조해 --module로 제공한다.

별도 venv에서 Python3.11.15, NumPy2.4.6, pandas3.0.3, SymPy1.14.0, NetworkX3.6.1, SciPy1.17.1, Matplotlib3.11.2를 사용했다. 전역 환경을 변경하지 않았다. 전체 lock은 실행 폴더에 있다. 재현 절차:

1. 새 Python3.11 venv 생성, `research_runs/env_acceptance/run_20261024_v1/requirements.lock.txt` 설치.
2. 공식 고정 module을 취득하고 위 SHA 확인. source의 AGPL-3.0-or-later 헤더 보존; 외부 구현을 이 저장소에 반입하지 않음.
3. 실행 승인 후 `python -X utf8 scripts/run_env_acceptance.py --module <고정 원본> --output <새 폴더> --execution-approved` 실행.
4. 외부 라이브러리 실행 없이 저장 기록만 재검증: `python -X utf8 scripts/validate_env_acceptance.py`.

`--execution-approved`는 실제 승인 기록을 대신하지 않는 운영 guard다. 승인 flag 없이 호출한 별도 negative 시험은 source 실행 전에 PermissionError/exit1로 거부됐다. 예상 거부의 FAILURE.json에 source/plan SHA를 기록했다. 정상 acceptance의 예기치 않은 실패는 없었다.

## 고정 fixture·실제 결과

사전 계획 PLAN_v1: R=u_R, A=2R+u_A, M=3A+u_M, Y=M+R+u_Y. 잡음은 각각 Normal(0,1), Normal(0,0.5), Normal(0,1), Normal(0,0.25)로 명시했다. 이는 이 검사에서 선언한 예제이며 공식 제조 기본 모델이라는 주장이 아니다. 직접 간선은 R→A, A→M, M→Y, R→Y이다.

Action=A, Target=Y, do값−0.1/+0.1, 단위는 무차원이다. 실제 밸브/물리 목표·Fault/Recovery/Safety는 정의하지 않았다. 예약 train seed3101, holdout7101/7102를 분리했다. 여기서 train은 데이터 역할 이름이며 알고리즘 학습은 하지 않았다.

| 필수 항목 | 실제 검사 | 결과 |
|---|---|---|
| 선언 직접 구조=반환 GT | 4×4 adjacency의4간선과 나머지 비간선·노드 순서를 대조 | PASS, 이 fixture 범위 |
| 관측이 같은 FCM에서 생성 | 원본 sampler 호출을 관찰해 잡음 저장·행별 선언식 재구성. hook 없이도 같은 seed/조건 API 재실행 대조 | PASS, 최대 절대 재구성 오차0; hook 통제9건 exact |
| do가 식 대체 | R→A 제거·A식 상수 대체·A샘플 고정·나머지식/원래 graph 보존 및 do샘플 재구성 | PASS |
| 변수·시계 | 관측/do 모두 R,A,M,Y·동일 단위·64개 sample index 확인 | PASS_IID_SCHEMA. 물리 시계/시간 지연은 해당 없음·미검증 |
| 새 seed 반복·분할 | 3seed×3조건×2회=18batch, 각64행. 각 조건 data/noise CSV exact·서로 다른 seed 관측은 상이, train/holdout seed 분리 | PASS. 반복을 독립 그래프 수로 세지 않음 |
| 실제 Action/Target | do(A=−0.1/+0.1) 원본 API로 적용, Y 원시 샘플 기록 | PASS_EXAMPLE_ONLY |

주 기록18batch 외 hook 없는 원본 API 통제9회, 총 sampler27회다. 이는 소규모 acceptance이며 표본 정밀도나 가설 검정력의 근거가 아니다. 원시 data/noise CSV·반환 reference·모든 batch metadata·환경 lock·hash를 보존했다.
exact 반복은 시험한 Windows/lock 환경 내 결과다. 다른 OS·dependency 변경 시 새 acceptance가 필요하다. 현재 train seed의 do배치도 시험 기록일 뿐 학습 자료가 아니다. 다음 learner는 train의 observational 배치만 읽고 중복 repeat를 제거해야 하며 do/holdout/GT는 튜닝에 유입하지 않는다.

## 잡음 정렬의 제한

동일 seed의 관측 vs do에서 u_A는 제거되고, 공통 u_R/u_M/u_Y도6개 비교 모두 행별로 달랐다. do로 그래프/샘플링 순서와 RNG 소비가 바뀌는 소스 동작과 일관된다. 따라서 sample_id는 배치 내 순번이며 서로 다른 정책의 동일 개체·동일 외생 실현을 뜻하지 않는다.
현재 허용 범위는 **IID 분포의 do(A=a)에서 Y 응답**이다. 같은 seed만으로 strict counterfactual/paired-noise 효과를 계산하지 않는다. 미래 평가에서 자연 관측 기준과 고정 do 기준 중 무엇을 비교할지 사전 명시하고, 필요하면 독립 Monte Carlo batch의 평균/불확실성으로 평가해야 한다. 물리적 horizon·복구 시간으로 해석할 수 없다.

## PR9 코드 재사용과 Gate 의미

PR9의 `static_mean_response`에 선언식의 알려진 계수만 입력해 do평균의 산술 일치를 점검했다. 회귀 적합/인과발견·추천 성능 시험이 아니다. `require_research_environment`도 재사용하여 같은 fixture 계약은 수용하고 CPCaD→fixture 혼합은 거부하는 것을 실행했다. 이 guard 호출은 예제 계약 연결의 코드 확인이며 연구 채택 승인이 아니다.
기존 TEP grid 추천기의 XMV 단위/0..100 제약은 이 무차원 Action에 자동 이식하지 않는다. 다음 정책 adapter는 공통 목적·tie rule을 재사용하되 단위/허용값/비용을 환경 계약에서 받아야 한다.

## 다음 단계 — 아직 실행하지 않음

1. **범위·데이터 계약:** 이 IID 예제를 소규모 연결 파일럿으로 사용할지 승인받고 Action 후보·목표·비용·관측/holdout seed·평가 estimand를 고정한다. 현재 Gaussian fixture는 DirectLiNGAM의 비정규 오차 가정을 만족하지 않는다. 연결 시험과 공정한 성능 비교를 구분하고, 다른 잡음 family를 택하면 새 계약/acceptance로 명시한다.
2. **같은 환경의3개 학습:** 승인된 새 관측 데이터에서 PC-stable/BOSS/DirectLiNGAM의 공식 구현·버전·검정/score/seed를 별도 namespace로 고정하고 실제 학습한다. 참조는 평가에만 사용하고 튜닝에 사용하지 않는다. 기존7개 frozen/과거 F1과 혼합하지 않는다. 이번에는 실행하지 않았다.
3. **공통 추천·독립 평가:** 같은 표본 분할·전처리/Ridge 규칙·Action/목적/비용으로 PR9 추천기를 연결한다. 동일 환경의 holdout do batch에서 실제 목표 달성/효과 예측을 평가하고 graph-fit/Task/batch 키로 연결한다. Recovery/Safety·제조 일반화는 이 예제의 범위 밖이다.

결론: **예제의 GT–관측–do adapter acceptance는 통과**했다. 제조 generator 검증은 NOT_RUN, 새 연구 환경 채택/학습은 미승인·미실행이며 원래 TEP 환경 대응 차단도 해소하지 않았다. 또 다른 광범위 감사 대신 다음 선택은 승인된 범위의3개 학습·정책 연결 실행이다.

# 구조 품질 지표 → 개입 추천 성능: 최소 평가환경·파이프라인

기준일: 2026-10-24. **구체적 결과: 독립된 기술 파일럿 실행 완료. 원래 가설의 직접 검증은 Gate1/Gate5 차단으로 미실행**이다. 기존 자료의 완벽한 복원을 최종 목표로 삼지 않고, 비교 가능한 환경에서 실제 추천을 검증하는 데 필요한 최소 연결 코드를 구현했다.

## 1. 연구 목적·GitHub 기준

질문: 불완전한 인과그래프에서 어떤 구조적 품질 지표가 공통 프레임워크의 실제 개입 추천 성능을 잘 설명하는가? 전체 Skeleton F1, Strict Directed F1, 핵심 방향 경로, 특정 X–Y, SHD 및 공정 흐름 지표를 후보로 둔다. 지표 설명력의 비교와 지표를 인위적으로 개선하면 성능이 향상된다는 인과 주장은 다르다.
이번에는 추천/실행 연결의 기술적 토대를 만든다. RESEARCH_DESIGN.md, frozen graph, 기존 Step6·적합·원시 진단은 수정하지 않았다. Track B 채택이나 새 GT 생성도 하지 않았다.

PR6→PR7→PR8은 모두 OPEN이며 각각 CI39963153945/40076485580/40077615216 성공을 확인했다. PR7은6 기반, PR8은7 기반이다. main7b16638은 그대로 두고 PR8 head `d508ab071f8e153698552ce69225a6eaf17a7150`에서 `feature/causal-metric-decision-mvp`를 분기했다. 이번 PR base는 `feature/ref-b-minimal-subsystem`이다. 선행 병합 후 base 재정렬·재검증 필요, 승인 없는 병합 없음.

## 2. 원래 가설 기준 A~H 현재 상태

| 단계 | 상태 | 실제 자산·미완료 부분 |
|---|---|---|
| A 최종 그래프 | 완료(산출물) | frozen7개 확보/해시 검증. 생성 원본 코드 전체 회수·재학습은 BLOCKED |
| B 전체 구조 지표 | 완료(기존 benchmark) | Step6 최종7행 재사용. 이번에 점수를 다시 만들지 않음 |
| C 핵심 경로·X–Y 지표 | 완료(기존 benchmark 진단) | 고정12과제×7그래프84행 신규 산출. 실제 개입환경 참조로 승격하지 않음 |
| D 공통 구조별 SCM 적합 | 부분 완료 | 기존 PC/DirectLiNGAM/BOSS Ridge 계수·공통 alpha·scaler를 해시 확인 후 재사용. 신규 적합 없음. 나머지/동적/식별은 별도 |
| E 공통 Fault–Action–Target | 차단(본실험) | X32→X9 기술 후보만 사용. Fault 복구·정상 범위·안전 계약 미확정 |
| F 추천 Action | 부분 완료 | 3모델의 동일 목적·격자 dry-run 실제 계산. 공정에 적용할 타당한 추천으로 승인하지 않음 |
| G 실제 개입 결과 | 부분 완료(기술) | 고정 Python TEP의 사전 지정 조작 원시 기록. 모델 추천 적용·독립 효과 정확도/복구·안전 평가는 미수행 |
| H 지표–추천 성능 관계 | 차단 | 환경 대응 없으므로 연구 join 거부. 상관·p-value·설명력 순위 없음 |

기존 experiments/pilot/PILOT_RESULT.md는 10월23일 당시 복원 기록이다. 그 문서의 소스 미확보 진술을 현재 공개 후보의 부재로 읽지 않는다. 현재 사실은 이 문서와 canonical state/생성 dashboard를 따른다.

### 재사용과 이번 경로 지표

global_metrics_reused.json은 Step6 원본 최종행의 sk_F1/dS_F1/SHD_S/간선 수를 복사하고 출처 SHA를 기록한다. 기존 ZIP의 loop_vs_flow.csv도 고정 ZIP SHA와 원래 member SHA를 확인해 그대로 추출했다. 그 안의 과거 p-value 등은 원본 기록이며 이번 추천 성능 통계가 아니다.

benchmark_task_metrics.json의84행은 다음을 구분한다.

- GT 경로 edge recall = 해당 과제에 속하는 고유 GT 방향간선 중 A_dir에서 복원한 비율.
- 완전 경로 비율 = 저장된 GT 방향 경로 중 모든 간선이 복원된 경로의 비율.
- confirmed Action→Target reachability = 추정 A_dir 전체에서 연결 가능 여부. GT와 다른 매개경로로도 참일 수 있으므로 위 지표와 다름.
- 직접 X–Y의 GT 여부/confirmed 여부/일치 여부. 거의 모두 음성일 수 있는 직접 관계 일치율을 단독 성능으로 쓰지 않음.

직접 X–Y가 미확정 쌍이면 상태 UNRESOLVED·정확도 null로 둔다. 최초 파생 표시의 confirmed-only 비교가 미확정을 비간선 정답으로 오해시킬 수 있어, 원시 trajectory 변경 없이 후처리로 보완했다. 이전 파생 파일은 before_unresolved_fix 이름으로 보존하며 사용하지 않는다. 새 simulator 실행·추천 변경은 없고 DERIVED_METRIC_REVISION.json에 원시 hash 불변을 기록했다.

미확정 간선을 방향화하지 않았고 경로 recall을 precision/F1이라고 부르지 않는다. temporal3종에 대해서는 기존 **static evaluation projection**의 진단이며 native lag 정확도가 아니다. 과제 선택 후에 산출했으며 점수로 과제를 바꾸지 않는다. 기존12개는 독립 표본이 아니다.

## 3. 공통 추천 파이프라인 — 실제 코드

`src/decision_mvp.py`와 `scripts/run_decision_mvp.py`가 다음을 수행한다.

1. frozen 변수/방향과 기존 적합 JSON·scaler·alpha·부모 집합을 검증한다. 적합 파일이 없으면 오류를 기록하고 중단한다. 자동 재적합 없음.
2. 정적 DAG를 위상 순서로 계산한다. 동일 선형 가산 식·저장된 intercept/계수를 사용하고 잔차0의 평균 전개를 한다. Action 식만 값으로 대체한다. 이는 구현된 do 연산자 형식의 **미검증 surrogate**이며 causal identification 또는 factual abduction을 뜻하지 않는다.
3. 공통 Action 격자 {-0.1,0,+0.1}pp를 benchmark train Action 평균 주위에 두고, 공통 Target·비용·목적으로 선택한다. cycle/lag/알 수 없는 부모는 실패로 남기며 간선을 고치지 않는다.
4. 연구 실행 전 환경 계약을 검사한다. 모델·controller 동일성, 변수/개입 대응, 참조 구조, 독립 평가 계약과 환경ID 모두 필요하다. 같은 문자열ID만 넣어 우회할 수 없다. 이 소프트웨어 gate가 과학적 검증을 대신하는 것은 아니다.
5. 현재 Gate1이 막혀 **추천값은 dry-run 파일에만 저장**한다. Python TEP에는 그 값이 아니라 사전에 고정한 baseline/+0.1pp 기술 정책만 실행한다. dry 추천과 simulator 원시는 별도 파일/환경ID로 저장한다.

공통 debug 목적은 J(a)=((예측X9−debug목표)/train표준편차)^2+0.01*(명령변화/0.1pp)^2이다. debug목표는 공통 train X9평균−0.01°C로 사전 고정했다. 공정 정상/성공 기준이나 실제 조작 비용이 아니다. 정확한 동률이면 |조작량|이 작은 후보, 이후 값 순서로 결정한다. GT·실제 반응을 보고 목적·계수·범위를 조절하지 않았다.

이번 dry 선택은 PC−0.1pp, DirectLiNGAM0pp, BOSS−0.1pp였다. **선택 차이는 추천 성능 차이가 아니다. 이 값을 공정에 적용하지 않았다.** 모델이 사용하는 benchmark Action 평균과 Python 초기 명령 자체가 다르므로 절대 명령을 자동 전달하면 안 된다.

기존 적합은 정상 관측 one-step 회귀이며 인과계수로 검증되지 않았다. 잔차0 평균 전개를 strict counterfactual로 표현하지 않는다. 실제 운전점·Fault 관측에 대한 abduction/초기화·반복 정책·horizon 예측은 향후 별도 계약이 필요하다. 정적3개 비교를 먼저 유지하고 DAGMA는 같은 정책 적합 승인 후, VarLiNGAM/DYNOTEARS는 native 시간 계약 후, PCMCI+는 식별 해결 후에만 확대한다.

## 4. 최소 평가환경 경로 비교

| 경로 | 현재 가능 범위 | 직접 가설 검증 조건/판정 |
|---|---|---|
| A 기존 TEP 연결 | 기존 구조·정상 적합과 후보 API 자산 재사용 | 기존 모델/controller/운전점·전처리·개입 대응 미확보. 직접 비교 NO-GO. 이번에 Track A 검색을 재개하지 않음 |
| B 새 통제 환경 | 실제 제조 데이터 기반 도구 causalAssembly의 고정 소스·FCM API를 검토 | 후보 검토만. 실행·도입 미승인/미실행. 새 생성 구조의 의미·동일 do 평가·반복·비교 계약을 증명하고 채택 승인 필요 |
| C 기술 파일럿 | 이번에 추천 dry-run+사전 지정 TEP 조작·로깅·반복 실행 | 기술 실행만 가능. 환경ID가 달라 H의 연구 join 거부. 구조 정확도 설명력 가설의 증거로 사용 금지 |

### 경로 B 후보의 실제 확인과 선결 작업

[boschresearch/causalAssembly](https://github.com/boschresearch/causalAssembly) commit **8da3729e6383f0e1cbe7740bb6ab7ac4977ac7f9**의 README/models_fcm.py/pyproject를 실제 회수해 읽고 SHA를 기록했다. `models_fcm.py`는 선언한 방정식으로 DAG를 구성하는 `input_fcm`(237행), `ground_truth`(143행), `sample`(307행), `intervene_on`(616행), `interventional_sample`(358행), seed RNG(64행)를 제공한다. 이는 관측에서 추정한 graph를 자기 GT로 삼는 구조와 다르다.
소스 헤더는 AGPL-3.0-or-later를 명시한다. 해당 commit의 LICENSE URL은404였으므로 파일을 회수했다고 쓰지 않는다. Git에 외부 구현을 vendoring하지 않았고, 배포 전 권리 확인이 필요하다. 설치 의존성은 SymPy/NetworkX/SciPy/Matplotlib/rpy2 등이며 현재 Python에서 일부가 없다. **런타임/반복성은 NOT_RUN**, 원래 R/DRF 기반 제조 generator까지 설치·실행됐다고 주장하지 않는다.
후보의 선언 FCM은 생성 모델의 참조가 될 수 있지만, 실제 제조 공정의 완전한 GT라는 뜻은 아니다. [원논문](https://proceedings.mlr.press/v236/gobler24a.html)은 부분 물리 정보로 반합성 제조 데이터를 구성하는 배경을 설명한다. FCM 예제 검증과 생산라인 generator 검증을 분리해야 한다.

필요한 **다음 구현**은 격리 환경에서 고정 source adapter를 작성해 (a) author 예제의 선언 노드/간선과 반환 reference 일치, (b) do가 해당 부모 식을 제거하는지, (c) 새 객체·seed 반복, (d) 관측/효과 noise 및 독립 평가 seed 분리, (e) 선택 생산 블록의 실제 Action/Target/범위를 검증하는 acceptance suite다. 이 검토가 통과해도 연구 환경 채택·질문 적용 범위는 별도 승인 대상이다. 과거 TEP28간선/7 frozen F1은 절대 이식하지 않는다.

## 5. 최소 Fault–Action–Target 계약

기존 `reactor_cooling_idv4_candidate`(X32→X9)를 **기술 후보**로 선택했다. 선정 근거는 냉각수 공정 의미와 이미 확인한 XMV10 쓰기·XMEAS9 로깅이다. 기존12개를 재선정하거나 graph별 F1/추천을 보고 고른 것이 아니다.

| 항목 | 현재 계약 |
|---|---|
| Fault | 본실험 미확정. IDV4는 주입 API만 이전 smoke에서 확인했으나 이번에는 주입하지 않음 |
| Action | 수동 XMV10 명령. source0..100 clipping은 API 한계일 뿐 안전 허용범위 아님. 기술 정책은 초기 명령+0.1pp, 10초 nominal step 직전1회 지정·유지 |
| Target | XMEAS9 실측 기록. 정상 범위/목표 달성 기준 미확정. debug모델 목표와 물리 목표를 분리 |
| no-action | 동일 초기점·seed·수동 mode·IDV0에서 추가 명령 없음 |
| 초기조건·horizon | 매 run 새 객체·initialize, dt1초, 평가60step, action step10. 기존 source 초기값 사용 |
| 비용 | dry 목적의 정규화 명령량 제곱만 존재. 실제 비용 정의 미확정 |
| Recovery/Safety | 정상 범위·지속·안전 임계값 미확정. 모든 결과 null; wrapper shutdown을 연구 안전 위반으로 채점하지 않음 |
| 독립성 | 같은 seed가 모든 조건의 외생 경로를 보장하지 않음. 이번에는 동일 조건 반복 exact만 확인. 효과 holdout 계약 미충족 |

## 6. 실제 파일럿 Gate·실행 결과

사전 계획 `research_runs/decision_mvp/PLAN_v1.json` 이후 다음 명령을 실행했다. 기존 적합·그래프는 읽기만 했다.

`python -X utf8 scripts/run_decision_mvp.py --source <고정 Python TEP> --step6-archive <해시 고정 기존 ZIP> --output research_runs/decision_mvp/run_20261024_v2`

위 경로는 실제 실행 기록이며 재현 시에는 **새 output 폴더**를 지정한다. 기존 결과를 덮어쓰지 않는다. 입력으로 기존3개 적합 JSON과 고정 source/GT/Step6 ZIP이 필요하다. 적합 JSON은 원래 experiments/pilot/results/의 Git 제외 자산이므로 새 팀원은 지정 아카이브의 SHA 대조 사본을 승인된 경로로 받아야 한다. 이 부재를 자동 재적합으로 숨기지 않는다. CI 기록 검사는 이 외부 입력이나 simulator 없이 실행 가능하다.

seed465120799/465120800 × baseline/+0.1pp ×2반복=**최종8회**, 각60step. 모든 run에서 명령 유지·유한 상태·60step 기록을 확인했고 같은 조건의 두 raw CSV가 바이트 단위로 일치했다. 41측정·12명령·밸브 상태·RNG·IDV4·두 시계를 기록했다. 실제 효과 오차·성공률은 계산하지 않았다.
앞선 v1도8회 실행했으며 정수 명목 시계를 기록했다. 정확한 wrapper 시계와 혼동하지 않도록 CLOCK_REVISION.md를 먼저 남긴 뒤 **조건 변경 없이 v2를 별도 실행**했다. v1은 삭제/덮어쓰지 않았다. 전체 실제 실행은16회이며 최종 판정은 v2를 따른다. 이는 이전 방정식 검산/12조건 진단의 재실행이 아니다.

| Gate | 판정 | 의미 |
|---|---|---|
| 1 평가환경 타당성 | BLOCKED | benchmark 구조 참조와 Python TEP 효과환경 동등성 미확립 |
| 2 개입 API | PASS_TECHNICAL | 사전 지정 명령 반영·Target 관측·짧은 반복 로깅 확인 |
| 3 공통 평가 계약 | PARTIAL_TECHNICAL_ONLY | 정적3개 동일 추천 계산 및 공통 dispatcher 동작. 연구 목적/비용/성공 기준·추천의 실제 적용은 미확정 |
| 4 독립 평가 | NOT_RUN_RESEARCH | 추천을 계산하지 않은 조건의 실제 효과 성능을 채점하지 않음 |
| 5 지표–결과 연결 | BLOCKED | 실제 join 호출이 GATE1_BLOCKED로 거부됨. 분석용 성능표/순위 없음 |

## 7. 최종 분석 계약 — 실제 성능 확보 후에만

하나의 분석 레코드 키는 `environment_version, graph_fit_id, task_policy_id, evaluation_batch_id`이다. graph_fit은 학습 데이터/분할·알고리즘 구현/seed/설정/graph hash·SCM 정책을 포함한다. 구조 지표와 결과가 같은 참조·정책·노드/시간 의미를 갖는 경우에만 연결한다.

구조 측면은 global F1/방향F1/SHD·밀도와 고정 핵심 경로 recall/완전 복원·직접XY를 분리한다. 응답 측면은 효과 예측 오차, 실제 목표 달성, 복구 성공·시간, 안전 위반, 물리 조작 비용을 각각 사전 정의한다. 서로 대체하지 않는다. 측정 불가/식별 실패/추천 실패/실행 종료도 분모와 상태로 보존한다.
동일 관측 데이터/전처리/공통 alpha 규칙/모형 family/Action 공간/목적/비용/초기조건/seed/horizon/참조정책을 통제한다. 정적·동적 또는 식별 가정이 다르면 subgroup·별도 결과로 제시하며 불가한 모델은 사유를 명시한다.
7개 알고리즘은 독립 표본7개가 아니다. rollout은 graph 수를 늘리지 않는다. 독립 학습 데이터·운전 조건/seed의 graph-fit 변동과 과제 family의 중첩을 고려하고, 평가 seed는 학습·튜닝/Task 선택에서 분리한다. graph-fit 및 task family 단위 paired/cluster 분석과 out-of-sample 설명력 비교를 검토한다. 밀도·표현군·모형 식별·도메인 이동이 주요 혼란 요인이다. pilot 분산과 최소 의미 차이로 정밀도 조건을 사전 고정한 후 holdout을 잠근다. 지금은 표본수/검정력 수치·상관계수·p-value·지표 순위를 만들지 않는다.
추천 성능과 지표의 연관성을 얻더라도 해당 지표를 인위적으로 높이는 조작의 인과효과를 입증했다고 주장하지 않는다.

## 8. 현재 차단 사항과 다음 실제 구현 3개

1. **ENV-MVP:** A의 실질 연결 근거 또는 승인된 B acceptance adapter로 Gate1을 해결한다. 완벽 복원을 위한 무한 검색을 하지 않는다. B를 선택하려면 위 고정 후보의 reference/do/repeat 검증 계획과 환경 채택을 승인받는다. 완료 기준은 같은 생성환경의 reference와 독립 효과 batch가 대응하는 로그다.
2. **POLICY-MVP:** 승인된 환경에서 단일 Action/Target·허용범위·물리 목표/비용·no-action·horizon을 먼저 고정하고, 기존 공통 grid 추천을 실제 simulator dispatcher에 연결한다. 처음에는 효과 예측/목표 달성만 검증하고 Fault/Recovery/Safety는 출처 조건을 충족한 뒤 추가한다.
3. **EVAL-MVP:** 승인된 환경의 새 관측 데이터에 정적3개 구현·공통 Ridge를 별도 namespace로 실행한다. 기존 frozen 재현으로 오인하지 않도록 생성 코드/버전·seed·실패를 기록한다. 실제 추천을 holdout batch에서 평가하고, Gate5 승인 후 동일 graph-fit/Task 키로 구조 지표를 연결한다.

새 환경의 실험은 공식 라이브러리의 새 구현·버전 고정을 사전 등록해 진행할 수 있다. 과거 Final 생성 코드 전체를 완벽히 회수할 때까지 무조건 기다릴 필요는 없다. 단, 그 결과를 기존 frozen 재생성이나 기존 F1의 검증이라고 부르지 않는다.

## 9. GO/NO-GO

**현재 기술 MVP는 실행 확인, 원래 가설의 직접 검증은 NO-GO**다. 다음에 해야 할 일은 새 감사 문서를 늘리는 것이 아니라 Gate1을 통과할 환경의 adapter acceptance 실행을 선택·승인한 뒤, 이미 만든 공통 추천기와 실제 평가기를 그 환경에서 연결하는 것이다. 환경 변경 승인 전에는 B로 전환하지 않는다.

검증은 tests/test_decision_mvp.py 및 scripts/validate_decision_mvp.py로 기록·gating·재사용·시계를 검사한다. CI는 외부 source 실행을 반복하지 않고 저장된 raw/hash를 검사한다. CI 통과는 환경의 과학적 동등성 증명이 아니다.

# Track B 참조 인과구조 타당성 감사

기준일: 2026-10-24. **현재 Track B 채택은 NO-GO**이다. 감사 완료와 연구 가설 검증 완료는 다르다. 원래 질문을 유지하며 RESEARCH_DESIGN.md와 기존 산출물을 변경하지 않았다.

## 1. 목적·기준 브랜치·판정 범위

연구 질문은 전체 구조 정확도와 과제 관련 핵심 경로 정확도 중 어느 것이 실제 개입 효과·복구·안전 성능을 더 잘 설명하는가이다. 이번에는 simulator-native 환경에서 이 질문의 검증 조건을 갖출 수 있는지 감사했다. Track B 채택 승인은 아니다.

PR #6은 OPEN/미병합, head `5fe3997d79a8244f4b156d5a335013337833b166`, Actions `39963153945` 성공이다. 변경 파일 16개는 Track A 문서·근거·Gate 코드·상태 관리에 한정됨을 Git diff로 확인했다. origin/main은 `7b166383d4a5d86cdf73dbbec3b060b0ee0e3a24`이다. 새 `feature/track-b-reference-validity`는 PR #6 head에서 분기하고 PR base도 `feature/track-a-recovery-gate`로 둔다. main 반영으로 표현하지 않으며 PR #6을 병합하지 않는다. PR #6 병합 후 base 변경·재검증이 필요하다.

기존 28간선 참조·7개 frozen graph·정상 관측 적합과 새 환경의 효과 참조는 구분한다. 사용자는 원시 ZIP/승인된 MATLAB 환경의 추가 위치를 모른다고 답했다. 이는 전역 부재의 증거가 아니며 Track A 차단을 해소하지 않는다. Slack 감사·원자료 로컬 검색·기존 12조건 실험은 반복하지 않았다.

## 2. 참조 구조 후보와 출처

아래는 참조 **후보**이다. 이번 감사에서 새 adjacency, GT 파일 또는 F1을 생성하지 않았다.

| 후보 | 노드·출처·controller | 간선/효과·feedback·잠재변수 | 사용할 근거와 현재 한계 |
|---|---|---|---|
| 공정 방정식·제어기 기반 확장 상태 구조 | 고정 Python source의 물질/열 상태·밸브 상태, PI 기억, 지연 cache, 입력/외생항을 분리 | 업데이트 식의 직접 부모를 방정식 수준에서 정의해야 함. 제어기와 시간 전개를 포함. 측정값은 상태의 함수이지 동일 노드가 아님 | 소스 존재·정적 계산 순서는 확인. 함수 호출/AST 의존성은 후보만 제공. 물리식·대수 중간항·외생 잡음·개입 의미 검토와 독립 검산 없이는 GT 아님. **PARTIAL** |
| 외부 기계적 구조 | CPCaD 기계적 관계 및 Ricker 공정/제어 문서 | 공정 흐름과 제어 피드백의 관계; 직접/간접 구별·시차가 불완전할 수 있음 | 원래 benchmark 채점 참조는 보존. 새 Python revision/controller와 동일하지 않아 28간선 승계 불가. 새 환경 전체 참조로 **BLOCKED** |
| 명시적 동적 구조 | 공정·센서·제어기를 함께 시간 전개한 노드 | 1초 수치 업데이트, 센서 관측 시각, 제어기 주기, 실제 지연을 구분. 같은 시점의 계산/대수 관계와 물리 지연은 다름 | 시간 전개 계약은 설계 가능하나 관측 31변수로 주변화·집계했을 때의 정확한 그래프 미확립. **PARTIAL**, 채점 참조는 미승인 |
| 실제 개입으로 검증한 국소 경로 | 사전 지정 XMV/설정값과 측정 결과 | 짝지은 개입의 총효과는 도달 가능성의 근거가 될 수 있으나 직접 간선/유일 매개경로를 판별하지 못함 | 조작 smoke는 존재. 다경로 상쇄·포화·시간창·검정력 때문에 무반응이 간선 부재를 뜻하지 않음. 특정 매개 측정값 do API도 없음. 전체 F1 참조로 **BLOCKED** |

코드 출처는 [고정 Python 구현](https://github.com/jkitchin/tennessee-eastman-profbraatz/tree/9a6c8e5fcef4a2850778704e7793c87b0a187005)이다. constants.py는 50상태·41측정·12조작변수·20외란을 선언한다. 관측 31변수는 이 상태와 제어 기억을 모두 포함하지 않는다. 실제 source 4파일 SHA는 기존 진단과 대조했다(`track_b_evidence/source_probe.json`).

[CIPCaD 원논문 IV-A](https://arxiv.org/html/2208.01529#S4.SS1)는 기계적 관계로 TE 참조 구조를 구성하며 선택 정상 데이터에서 인과 지연을 결정하지 못했다고 보고한다. 이는 새 구현의 지연 GT를 보증하지 않는다. [Ricker 공식 archive](https://depts.washington.edu/control/LARRY/TE/download.html)는 수정 모델과 제어 코드·외란 응답을 제공하지만, 새 후보와의 동일성 검증 또는 관측 수준 GT 증명은 아니다.

## 3. 식별·표현상의 핵심 문제

### 3.1 측정·상태·명령을 분리해야 한다

python_backend.py 814–840행에서 물질/에너지 상태와 밸브 위치를 읽고, 1134–1156행에서 측정값을 계산한다. 1251–1254행은 명령과 밸브 위치 사이의 동역학을 포함한다. 따라서 XMV 명령은 실제 유량이나 내부 밸브 위치와 동일하지 않다. XMEAS의 값을 강제로 바꾸는 조작은 물리 상태 do와도 다르다.

관측변수만 남기면 내부 조성·열 상태·PI 기억이 숨은 공통 원인/기억으로 작용할 수 있다. 그 결과 정확한 주변 그래프는 단순한 31-node DAG가 아니라 숨은 변수·시차·혼합 그래프 표현을 요구할 수 있다. 이는 아직 계산으로 확정한 새 GT가 아니라 식별 위험이다.

### 3.2 시간 해상도와 제어기

simulator.py 308–326행은 측정값→controller→명령 갱신→미분 평가→Euler 상태 갱신 순이다. controllers.py 413/468/487행은 3/360/900 step 주기를 사용하고 자체 1초 dt를 가진다. backend의 조성 측정은 별도 지연·갱신 주기를 포함한다. 기존 진단의 적분 후 상태 시각과 평가 시각 차이를 그대로 기록해야 한다.
연속시간 미분 의존성, 수치 적분 그래프, 3분 median 관측 그래프는 서로 다른 대상이다. 집계하면 매개변수 제거·aliasing·장기 기억이 생길 수 있다. 새 환경에 기존 최대 lag=5 또는 3분 창을 자동 적용하지 않는다. 미확정 간선을 비간선으로 채점하지 않으며 검증된 양성 목록만으로 precision/F1 분모를 만들지 않는다.

### 3.3 총효과와 직접 경로·동시점 식별

두 실행의 Target 차이는 해당 정책/초기점/시간창의 총반응이다. 매개변수 경로가 여러 개면 서로 상쇄될 수 있다. 총반응만으로 직접 간선, 매개 순서 또는 경로 부재를 확정할 수 없다. 정책이 바뀌면 controller→XMV의 구조도 달라진다. 수동 개입과 폐루프 관측을 섞으면 구조 오류와 정책 이동이 혼재된다.
관측 회귀의 예측력은 인과 식별을 보증하지 않는다. 폐루프 내생성·숨은 상태·동시점 순환은 Ridge나 비선형 회귀로 자동 해결되지 않는다. PCMCI+의 기존 순환 계수 식별 차단은 유지한다. 새 알고리즘 실행의 순환 구조도 별도 식별 검토 대상이다.

### 3.4 참조 독립성의 의미

참조는 학습된 그래프나 그 SCM 예측으로 정하지 않는다. 방정식 검토자는 discovery 결과·효과 점수에 눈가림하고, 참조 후보·불확실 영역·수치/시간 규약을 결과 전에 고정해야 한다. simulator 실행은 SCM 예측과 독립된 계산 참조가 될 수 있지만 같은 시뮬레이터의 모델 편향까지 검증하는 외부 물리 정답은 아니다. 불확실 영역만 제외한 부분 채점은 전체 F1 주장과 구분해야 한다.

## 4. 기존 데이터와 신규 환경·7개 그래프 활용 범위

A는 1499×31 CPCaD 관측 데이터의 동결 구조 평가 기록, B는 다른 환경에 기존 그래프를 적용하는 외부 전이, C는 새 데이터에서 새로 학습한 구조이다. A와 C는 같은 Final이 아니다. 기존 F1을 C의 구조 정확도나 B의 환경 적합도로 연결하지 않는다.

| 알고리즘 | A: 현재 재사용 | C: 승인 후 필요한 최소 구현·재현 조건 |
|---|---|---|
| PC-stable | frozen·평가 확인 가능; 생성 BLOCKED | 미회수 run_pc/common 원본·독립성 검정·시계열 자기상관 처리·유효표본수·방향 미확정 규칙. 기존 n_eff를 새 데이터에 이식 금지 |
| BOSS | 동일 | run_boss/common·Tetrad/Java 버전·score penalty·starts/seed·자료 순서 고정 |
| DirectLiNGAM | 동일; 기존 정상 관측 적합은 별도 | run_b_retune/common·패키지 버전·전처리·순서/외생 독립성 가정·동일성 검증 |
| DAGMA | 동일 | run_b_retune/common·버전·정규화/손실·정규화 계수·seed/수렴 기준·threshold |
| PCMCI+ | 동일; 기본 SCM 식별 보류 | run_pcmciplus/common·Tigramite·검정·tau/alpha/부모 정책·순환/미확정 표현과 별도 식별 계약 |
| VarLiNGAM | frozen 및 lag 변환 평가 확인 가능; 생성 BLOCKED | run_varlingam/common·차수/seed·계수 threshold·현재/과거 방향 규약·안정성 |
| DYNOTEARS | 동일 | run_dynotears/common·라이브러리/환경·lag/order·정규화/threshold·최적화/seed·현재/과거 tensor 규약 |

알고리즘별 원본 코드 hash·설정은 GRAPH_REPRODUCIBILITY.json의 기록을 따른다. 7개 모두 정확한 생성 bytes/실행 대응은 미확보이며 이번에 새 코드를 Final 원본처럼 복원하지 않았다. 향후 새 구현을 승인하면 새 namespace·입력 hash·버전·seed·명령·실패 기록을 가진 **새 실험**으로 운영한다. 우선 실행 범위/제외 사유를 결과 전에 확정하고 7개를 모두 재현했다고 주장하지 않는다.

## 5. 작은 실제 코드 검증

계획은 TRACK_B_SMALL_CHECK_PLAN.md에 먼저 기록했다. `python -X utf8 scripts/audit_track_b_source.py --source <고정 source> --output <새 JSON>`을 실행했다. 최초 시도는 backend wrapper를 잘못 접근해 AttributeError로 중단했고 출력 결과는 생성되지 않았다. 실제 API를 확인해 직접 process에 관찰 함수를 연결한 뒤 재실행했다. source는 수정하지 않았다.

Python 3.11.15/NumPy 2.4.6, seed 465120799, dt 1초, IDV=0, 수동/폐루프 각각 새 기준·조작 객체로 30 step만 실행했다. index 6에 XMV10 +0.1 pp를 한 번 명령했다. 네 실행 모두 30 step의 상태가 유한했고 종료하지 않았다. 초기 yy는 각 쌍에서 exact 일치했다. 매 step RNG 호출과 측정 잡음 반환값을 감싸 기록한 digest가 이 구간에서 일치했다. 추가 관측 평가를 호출하여 RNG를 소모하지 않았다.
계획의 초기 RNG 스냅샷은 이번 출력에 별도 저장하지 못했다. seed 기록과 이후 호출 비교로 대체한 제한이 있으며, 완전한 초기 상태 동일성 검증으로 표현하지 않는다.

수동 모드는 41.20581288% 명령을 유지했다. 폐루프 step 6 뒤 실제 XMV10은 기준 41.43309067389297%, 조작 41.530110678098445%로 controller가 갱신했다. 따라서 폐루프 `set_mv` 1회와 지속 고정 override를 구분해야 한다. 반응 정확도/효과 크기를 판정한 실험은 아니다.
backend 1177–1180행은 time>0 및 shutdown 아님 조건에서 측정 잡음을 소모한다. 조성 갱신·disturbance의 RNG 경로도 존재한다. **같은 seed만으로 종료/Fault/dt/장기간의 잡음 경로를 보증하지 않는다.** 이번 결과로 그 조건들을 통과시켰다고 주장하지 않는다.

## 6. 필요한 최소 실험 계약 — 초안, 미승인·미실행

참조 검증이 해결되지 않았으므로 확정된 본실험 계약이 아니다. 숫자·성공 기준을 사후 선택하지 않도록 다음 선결 항목을 결과 열람 전에 채워야 한다.

| 항목 | 최소 계약 및 현재 보류 조건 |
|---|---|
| 노드 | 31개 공통 관측변수는 비교 후보. 실제 41측정·12명령·50상태·PI/cache는 감사 로깅 후보. 노드 의미/단위·숨은 변수·채점 가능한 쌍 목록을 독립 검증 후 확정 |
| representation | 방정식 수준 직접 구조/관측 주변 구조/총효과 도달성 중 무엇을 채점하는지 명시. 불확실 쌍 마스크·시차 범위·미확정 처리와 분모를 고정 |
| mode | 관측 생성과 평가의 mode/controller/운전점을 같게 함. 수동 명령 검증은 수동 참조와 비교. 폐루프는 보상/설정값/override 정책과 시간 순서를 별도 검증 |
| 초기화·noise | 새 객체·source/backend·초기 yy/controller·IDV·관측 시계 고정. seed 목록과 스트림 역할을 사전 고정. 실제 호출/외생 잡음 정렬 검증; 불가능하면 독립 잡음 반복 평균의 estimand로 구분. seed가 같다고 동일 잡음이라고 기입 금지 |
| 관측 생성 | 승인된 mode·워밍업·sampling·window/stride·horizon·여러 seed/운전 구간을 사전 등록. 데이터/분할 hash, 누락·shutdown 규칙 저장. 정책이 일정해 입력 변동이 부족하면 positivity/식별 차단을 기록. 외생 excitation은 별도 승인·출처 범위 필요 |
| discovery | 새 데이터 seed 단위 train/validation/holdout 분리. train-only scaler. 공통 튜닝 규칙은 관측 검증만 사용; GT·효과 holdout으로 튜닝 금지. 구현 범위/실패 처리 선등록 |
| 구조 지표 | 참조가 승인된 경우에만 동일 노드/간선 의미의 Skeleton F1·strict Directed F1·SHD. 동적 구조는 lag별 및 공통 projection을 분리. projection F1을 native 정확도처럼 표현 금지 |
| 핵심 경로 | 환경에서 검증된 Action–Target의 참조 경로/조상 관계를 사전 선택하고 정확도 정의 고정. 여러 경로·nested·동일 Action 군집을 기록. 효과를 본 뒤 중요한 경로를 선택하지 않음 |
| Action–Target | 탐색 API 후보 XMV10→XMEAS9. 기존 12개 과제 승계/확정이 아니며 Action 크기·허용 범위·시간창은 아직 미확정. 제어기 명령 XMV10과 actual valve/flow를 분리 |
| estimand | 고정 정책 π에서 τ_j(h,a)=E_U[Y_j(t0+h;do_π(a),s0)−Y_j(t0+h;reference_π,s0)]. paired noise일 때도 실제 외생항 정렬 확인. 시각별 총효과와 누적 효과는 별도 사전 선택 |
| 기준 정책 | 동일 초기점·mode·IDV·controller에서 추가 명령 없는 참조. 폐루프 참조와 수동 조작을 혼합하지 않음. 조작 전부터 같은 경로인지 검사 |
| 독립 평가 | simulator raw 반응과 SCM 예측을 별도 파일로 저장. 학습에 쓰지 않은 초기점/seed/조작 조건으로 오차 측정. 원시 종료/비유한 상태는 삭제하지 않고 실패로 기록 |
| 복구·안전 | Fault·회복 정상 범위·지속시간·허용 제어량·비용·안전 한계의 출처 확인 후 사전 고정. 후보 shutdown 한계를 곧바로 연구 Safety 기준으로 승격 금지. 현재 평가 NOT_RUN |

최소 **다음 확인**은 참조 표현/노드의 수작업 검증 가능한 작은 블록 한 개를 정의하는 것이다. 새 GT 생성·학습·개입 sweep은 현재 승인 범위가 아니다. 국소 reachability만 확인 가능하면 연구 질문을 전체 F1 비교에서 좁혀야 하므로 별도 승인이 필요하다.

## 7. 통계적 실험 단위·검정 가능성

독립 단위는 단순 31변수·시점·개입 반복 횟수가 아니다. 새 관측 데이터 seed/운전 조건→학습 그래프→과제 계열→평가 seed의 계층을 구분해야 한다. 같은 그래프의 반복 rollout은 효과 추정의 Monte Carlo 오차를 줄이지만 구조 지표의 독립 표본을 늘리지 않는다. 같은 Action/Target/nested 경로도 독립 표본으로 세지 않는다.
7개 알고리즘은 7개의 무작위 독립 그래프 표본이 아니다. 알고리즘과 그래프 밀도·시간 표현·모형 family가 함께 바뀌면 구조 품질 설명력과 혼재된다. 여러 독립 학습 seed/데이터 조건의 변동과 공통 SCM 정책이 필요하며 static/temporal 표현군은 분리 해석한다. 필요 시 밀도·식별/적합 실패·표현군을 함께 보고하되 작은 표본에서 통제했다고 단정하지 않는다.
추론 계획은 그래프 학습 단위 군집과 과제 family를 고려한 paired 비교/계층 분석 또는 cluster resampling 후보이다. seed와 과제 수, 최소 의미 있는 차이, 실패율·분산 기반 precision/power 기준은 **미확정**이다. 이번에 N·p-value·상관계수·유의성을 만들지 않았다. 파일럿으로 측정 오차를 추정한 뒤 독립 holdout을 잠그는 설계가 필요하다. 현재 Q4는 UNKNOWN이다.

## 8. 대안 자료 — 공식 메타데이터와 실제 확보를 구분

| 후보·원본 출처 | 권리/확보 | 실제 조작·controller·변수·참조 | 활용과 남은 검증 |
|---|---|---|---|
| [Rieth TEP 데이터 DOI](https://doi.org/10.7910/DVN/6C3JR1) | 공식 DataCite/Dataverse API HTTP200, v1.0 메타데이터 확보. 사용자 약정은 public-domain dedication/면책/비보증·비후원 조건. 단순 CC0라고 축약하지 않음. 4개 RData 본체 미다운로드 | 55열, Fault/run/sample과 52공정변수, 여러 RNG run과 3분 sampling·Fault 시작 시점은 **공식 보고**. Fault는 제어 조작에 대한 최적 복구 action 실험과 다름. 동일 controller 설정·Action 크기·쌍별 잡음·참조 그래프는 미검증 | Fault 검출/반복 변동성 조사 후보. 독립 복구·안전 및 전체 구조 GT 자동 확보 아님 |
| [Ricker 대학 archive](https://depts.washington.edu/control/LARRY/TE/download.html) | 기존 코드 ZIP hash 보존, 모델 재배포 권리 별도 확인 필요 | IDV 응답 archive 목록·제어 자료 존재. 이는 외란 응답이며 XMV 추천 action에 대한 paired 효과 자료인지 미확인 | 모델/제어 검산 후보. MATLAB 차단·원시 계보 불명 유지. 추가 ZIP 다운로드/실행 없음 |
| [현재 Python 후보](https://github.com/jkitchin/tennessee-eastman-profbraatz/tree/9a6c8e5fcef4a2850778704e7793c87b0a187005) | 고정 source와 원래 저작권/3조건 허용 문구 확인; 원본 문구 유지 필요 | 수동 쓰기/Fault와 제한 반복 실행 근거 존재. 41측정/12명령, 실제 GT 미검증 | 이번 30초 API/RNG 확인만 추가. 공정 모델의 물리적 정답/31변수 GT로 승격 불가 |
| [TEP Studio](https://github.com/khalidlabs/tep-studio) | 기존 로컬 commit 852f0c69ab974540750d61bd1dbfafd56bfd80bb, LICENSE BSD-3-Clause 정적 확인 | README는 수정 C 기반 controller/trajectory 도구를 설명. 실제 실행·세부 API·참조 인과구조는 이번에 미검증 | 합법 source 조사 후보. 기존 설치 실패 기록을 보존하고 재설치/새 시뮬레이션은 안 함. 구현 문서의 causal 명칭이 GT 검증을 뜻하지 않음 |

Rieth API에는 4개 파일의 이름·크기·provider MD5가 있으나 이는 다운로드 바이트 검증이 아니다. 가장 큰 파일은 약 837 MB이다. 메타데이터 원본 SHA와 선택 필드는 `track_b_evidence/source_inventory.json`에 기록했다. 대규모 데이터 회수·환경 교체·새 논문에 근거한 연구 확장은 하지 않았다. 새 후보를 기존 CPCaD와 동일 자료로 취급하지 않는다.

## 9. Q1~Q5 및 채택 Gate

| 질문 | 판정 | 근거·해제 조건 |
|---|---|---|
| Q1 동일 simulator에서 관측/개입 독립 생성 | PARTIAL | 기존 smoke·이번 짧은 probe 가능. 안정 운전 범위·폐루프 API·외생 잡음 통제·독립 효과 측정 계약 미확정 |
| Q2 타당한 참조 구조 정의·평가 | BLOCKED | 관측 노드에 대한 직접/시차/잠재변수 참조 미확립. 28간선 자동 승계 및 코드 의존성 GT화 금지 |
| Q3 동일 단위의 경로 정확도/의사결정 비교 | BLOCKED | Q2 선결, 과제·estimand·실행 범위·안전 기준 미고정 |
| Q4 충분한 반복·통계 검증 | UNKNOWN | 독립 graph-fit 변동성·표본 규모/검정력 근거 없음; rollout 수로 대체 불가 |
| Q5 기존/신규 결과 구분 해석 | VERIFIED | A/B/C namespace와 frozen 재사용 한계를 문서화한 설계 수준. 새 연구 결과를 실제 얻었다는 뜻 아님 |

**Track B 채택 NO-GO**, 향후 조건부 가능성은 검토 수준이다. 데이터와 반응을 같은 simulator에서 생성하는 것만으로 Q2를 해결하지 못한다. 원래 가설은 연구 질문으로 **유지**할 수 있으나 현재 Track B에서 타당하게 검증할 수 있다고 결론내리지 않는다. 충분한 참조를 만들지 못하면 전환을 권고하지 않는다. 제한적 국소 총효과 연구는 질문 범위 변경이므로 별도 승인 대상이다.

## 10. 다음 3개·승인 사항·금지 주장

1. REF-B: 노드/시간/정책/숨은 변수/직접 간선의 정의와 검증 가능한 참조 범위를 수작업 검토안으로 작성. 독립 검산과 불확실 쌍 처리까지 해결되어야 해제. 새 GT 생성은 별도 승인 후.
2. SIM-B: controller 및 외생 잡음 정렬·관측 시계·안정 horizon의 최소 검증 계약을 사전 확정. 종료/Fault/개입 조건에서도 CRN이 가능한지 확인하기 전 동일 seed 보장을 금지.
3. DESIGN-B: 독립 graph-fit/과제 family/seed 분할·공통 지표·표본 precision 기준을 완성하고 연구 가설 유지 가능성 재심의. Q2 미해결이면 채택 요청을 하지 않음.

Track A 원자료/환경 요청은 별도로 남는다. 대화상 위치 미확인 외 새 단서가 없어 재검색하지 않았다. 메일/Slack 연락·연구 전환·데이터 교체·대규모 학습은 승인하지도 수행하지도 않았다.
금지 주장: 코드 의존성=GT, 무반응=간선 없음, Fault 데이터=복구 action 효과, 동일 seed=모든 잡음 동일, 7개×12개×시점=독립 표본, 기존 F1=새 환경 F1, 작은 smoke=물리적 인과 정답, GT 없이 구조 F1 설명력 입증.

### 재검증

`python -X utf8 scripts/validate_track_b_audit.py`는 기록·hash·작업 범위 보존을 검사한다. 참조 구조의 과학적 타당성을 자동 증명하지 않는다. optional source probe는 외부 고정 source가 필요하며 CI에서 재실행하지 않는다. 실제 명령/실패/환경은 WORK_LOG와 JSON에 보존한다.

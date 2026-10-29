# CausalMan micro 동일환경 수용 검사

2026-10-29. **CONDITIONAL_NOT_ACCEPTED. 고정 버전은 현재 연구 파이프라인에 연결하지 않는다.**
공식 채택·발견 학습·SCM 학습·F1/SHD·추천/최적화는 수행하지 않았다. 실행 실패와 과학적 부적합을 구분하며, CausalMan 전체 또는 모든 다른 과제가 불가능하다는 판정은 아니다.

## 1. 무엇을 실제로 실행했는가

PR24 `bc46dc924f2cf5171144c6e73e7a48373d83dc34` 위에서 분기했다. 외부 소스는 [Bosch 17529da](https://github.com/boschresearch/CausalMan/tree/17529dad5ec8b8c691494c617b9af4533aa44bf8), Git root tree는 `07d305edf35d07b3caa9b1ebabeb3f244cdc5dc9`다. 공식 Git metadata의 전체 tree를 재해싱하고 실제 취득 파일의 Git blob/SHA-256을 대조했다.

| 단계 | 실제 결과 | wall / 관측 최대 job RSS |
|---|---|---|
| micro+소스 취득 | 1,049파일 검증, micro 1,018파일·144,812,833 bytes | 98.375초 |
| 초기 venv 실행 | 검증기 job의 단일 프로세스 제한이 Windows interpreter 위임을 막음;실패 보존 | 0.313초 |
| 격리 venv/필수 wheel 준비 | 성공;모든 interpreter child에 동일 job 메모리 cap 적용 | 5.063+22.531+47.062초 |
| 외부 import/생성자 | 성공,아직 pickle load 없음 | 7.015초 / 130.55MiB |
| 관측 seed42 첫 시도 | `ValueError: Failed to import scipy`,반환 표본 없음 | 3.891초 / 155.87MiB |
| 의존성 보완 | SciPy1.14.1 wheel 취득/설치,upstream 소스 변경 없음 | 14.968+11.688초 |
| fresh 관측 seed42 | 내부14,813행·101경로,32행 반환 | 146.781초 / 507.98MiB |
| fresh do(16000),seed1042 | 내부14,813행·101경로,32행 반환;do graph 검사 실패 | 197.500초 / 458.68MiB |
| fresh do(30000),seed2042 | 앞선 그래프 결함 확인 시 중단;최소44완료경로/6,149행 진행 기록 | 중단까지 약105.050초 / 중단 시304.27MiB |
| replay42 / distinct43 | NOT_RUN:과학적 계약 중단 후 실행하지 않음 | 미실행 |

합계 **sampling 호출4회,완료2회(관측1·do16000 1),반환64행**이다. 내부 완료29,626행과 중단 시점의 진행 행은 독립 개입 연구 표본 수가 아니다. do30000의 최종 표본·효과는 없다.

계약은 import/sampling 전에 저장했다. SciPy는 CausalMan core dependency에 없으나 SymPy의 기본 확률 샘플러가 요구했다. 첫 실패와 원계약 SHA를 보존하고 **환경 의존성 한 번 보완**을 CONTRACT의 명시적 부록으로 기록했다. 조작값/seed/손실/기대값을 바꾸지 않았다. do graph 결함 이후에는 재시도·외부 패치·다른 조작을 하지 않았다.

## 2. 소스·권리·격리·비용 Gate

기본 `pip install .`을 사용하지 않았다. 필요한 고정 Python 소스와 micro 객체만 외부 디렉터리에 두고 별도 venv에서 source-path import했다. 다른 규모·Zenodo archive·기존 TEP 원자료는 취득하지 않았다. Python3.11.15, NumPy1.26.4, Pandas2.2.3, NetworkX3.6.1, SymPy1.14.0, Matplotlib3.9.2, Pyvis0.3.2, tqdm4.70.1, 추가 SciPy1.14.1이다. transitive wheel 버전/해시는 RESULT에 있다.

권리 판단은 공식 README가 precomputed objects를 소프트웨어 패키지 구성품으로 명시하고 프로젝트 AGPL 선언을 적용한 **해당 묶음의 로컬 실행 범위**다. 별도 제3자 데이터/Zenodo 재사용·바이너리 재배포 권리가 모두 해결됐다는 주장은 아니다. 원본 notice를 보존했고 외부 소스·pickle·wheel을 연구 Git에 복사하지 않았다. [README](https://github.com/boschresearch/CausalMan/blob/17529dad5ec8b8c691494c617b9af4533aa44bf8/README.md),[LICENSE](https://github.com/boschresearch/CausalMan/blob/17529dad5ec8b8c691494c617b9af4533aa44bf8/LICENSE),[packaging](https://github.com/boschresearch/CausalMan/blob/17529dad5ec8b8c691494c617b9af4533aa44bf8/pyproject.toml)

609 pickle의 opcode를 실행 없이 조사했다. GLOBAL opcode는0,STACK_GLOBAL은13,828이었다. 이것은 안전성 증명이 아니다. 공식 파일 provenance/hash 검증,격리 venv/경로,worker의 network/subprocess·외부 read/write 차단,Windows job 제한을 함께 적용했다. 임의 pickle에 대한 보안 보증이나 OS의 완전한 hostile-code sandbox라고 부르지 않는다.

- 확인된 다운로드 파일/API payload+wheel: **270,118,144 bytes(257.60MiB)**. pip index/HTTP metadata overhead는 완전히 계량하지 않았으므로 총 네트워크 바이트의 정확한 값은 아니다.
- 측정 작업 디스크: **898,101,516 bytes(856.50MiB)**. 대형 객체를 Git/최종 연구 ZIP에 추가하지 않는다.
- 측정 최대 job RSS: **532,656,128 bytes(507.98MiB)**.
- 취득/설치/import/실패/완료/중단 실행의 누적 측정: **약667.253초(11분7초)**.
- RSS는0.1초마다 job 구성 프로세스의 PeakWorkingSetSize를 합친 관측 최대다. 별도로2GiB job commit cap을 적용했으며 commit과 RSS는 같은 척도가 아니다. 계측 한계와 정확한 명령/receipt는 RESULT에 남겼다.
- 시작 가용 디스크 약48GiB·가용 메모리 약4.5GiB 이상에서 진행했다. 상한 초과가 관측되지 않았고 이번 중단 원인은 자원 부족이 아니다.

## 3. 실제6반환·행·변수 계약

성공한 두 호출은 정확히 `DataFrame,MultiDiGraph,MultiDiGraph,DataFrame,DiGraph,DataFrame`을 반환했다. 순서는 observed,MAG,ADMG,full,DAG,intervention table이다. 4-unpack CLI와 `apply_interventions`는 사용하지 않았다.

| 항목 | 관측 | do16000 |
|---|---:|---:|
| observed | 32×24 | 32×22 |
| full | 32×158 | 32×158 |
| intervention table | 32×0 | 32×1 |
| 결측/수치 비유한값 | 0/0 | 0/0 |
| observed=full의 해당 열·동일 행 | 일치 | 일치 |
| 개입 indicator | 없음 | 정확한 Force 열,32행 모두1 |
| Force | float64,변동 있음 | 전체 내부 생성에서16000 고정 |
| 품질 Y | float64의0/1 | float64의0/1 |

반환 graph는157노드이며 full의 추가 `partID`는 식별자이지 새 인과 노드가 아니다. 배치/경로 정보는 fixed batch CSV와 로드한 경로별 모델 이름에서 추적했다. 품목/배치/경로는 재샘플링되는 IID 센서값과 구분한다. partID/사전 타임스탬프를 공정 연속시간 인과관계로 해석하지 않았다. 이 micro에서 관측·적분의 실시간 clock을 보장하는 실행 계약은 없다.

baseline24열을 **do 이전에 V***로 동결했다. 원래 경로별 Observable 선언은 모든101경로에서 같은53개였고,전체 생성 후 상수 제거로24개가 남았다. 반환32행 안에서는 일부 열이 다시 상수일 수 있다.

do16000에서는 `PF_M1_T1_Fmax_MpGood`,`PF_M1_T1_Force_MpGood`이 빠졌다. 이는 수치 개입 자체의 실패가 아니다. baseline V* 전체는 do full에 있으므로 향후 계약에서 고정 baseline 센서 의미로 정렬할 가능성은 있다. 그러나 호출별22/24노드와 각 MAG를 서로 다른 구조 정답으로 채점하면 안 된다. 이번에 GT를 바꾸거나 새 F1을 계산하지 않았다.

Force의 물리적 단위는 반환 node metadata에 명시되지 않았다. 모델-native 숫자로 기록하며 임의로 N·안전범위·실제 actuator 정책을 확정하지 않는다.

## 4. 활성 방정식과 Level2 참조

실제 생성한101경로의 Level1/Level2 파일 식별자·SHA를 기록했다. 모든 경로에서:

- Level1과 변환 후 활성 FCM은 **157노드·170간선**,노드/간선 집합이 같았다. 이번 micro에서는 FCM 변환에 의한 추가 pruning이 관측되지 않았다.
- Level2는 **157노드·251간선**이고 활성 전용 간선은0,Level2 전용 간선은81이었다.
- Level2의 directed topology는 모든 경로에서 같았다. 따라서 “마지막 경로가 다른 topology라서 전체를 대표하지 못한다”는 반례는 이번 실행에서 발견하지 못했다. 같았던 것은 topology이며 경로별 파라미터가 같다는 뜻은 아니다.
- 관측의 결정론적 식35,518개 row-node 대조가 일치했다. do16000에서는 Force를 제외한35,217개 대조가 일치했다. 이는 각 식의 처음 최대3행 검산이며 전체 분포·참조 GT의 증명은 아니다.

81개는 공급업체·부품 종류·경로에 따른 분포/파라미터 선택 관계 등을 포함한다. 원본 `sample_batch.py`144–160행과 논문 AppendixC/D1은 이 조건부 계층을 별도로 설명한다. 따라서 **170≠251만으로 버그라고 판정하지 않는다.** [원본 설명](https://github.com/boschresearch/CausalMan/blob/17529dad5ec8b8c691494c617b9af4533aa44bf8/causalman/sample_batch.py#L144),[조건부 계층](https://arxiv.org/html/2502.12707v1#A4.SS1)

그러나 이번 실행만으로81개 조건부 부모와 비간선을 모두 닫힌 방정식/라우팅 계약으로 재구성·정당화하지는 못했다. 활성 식의 정답과 조건부 혼합 자료의 참조를 같은 의미로 취급할 수 없다. 현재 **전체 관측 구조 채점 계약은 PARTIAL/BLOCKED**다. 원참조에서81개를 삭제해 GT를 새로 만들지 않는다.

원래 Force 식을 do로 바꾸었으므로,do trace에 남은 원래 Force 식301개 불일치는 post-do 물리 실패로 세지 않는다. 원식은 더 이상 해당 개입의 기대식이 아니다. 실제 고정값과 개입 graph의 term은 따로 검산했다.

## 5. 실제 hard-do: 수치 치환과 그래프 삭제를 분리

do16000의101개 활성 모델 모두 Force term이16000으로 바뀌었다. 내부14,813행에서 Force는 상수였고 반환32행도 정확했다. 8,080번의 후속 표현식 평가와 위 결정론적 재계산은 단순한 Y 라벨 바꾸기가 아니라 후속 계산이 수행됐다는 근거다.

**실패는 `self.mutilated_dags`의 실제 간선 제거다.** 모든101개 개입 graph에 다음 두 incoming edge가 남았다.

- `MV1_LmvPF → PF_M1_T1_Force`
- `PF_M1_T1_KstiffPF → PF_M1_T1_Force`

`fcm.py`564–566행에서 `in_edges`가 반환한 (parent,target) tuple 자체를 old로 받아,삭제 대상이 ((parent,target),target) 꼴이 된다. 존재하지 않는 간선 삭제가 조용히 무시된다. [원본 함수](https://github.com/boschresearch/CausalMan/blob/17529dad5ec8b8c691494c617b9af4533aa44bf8/causalman/fcm.py#L560)

이는 반환 baseline GT가 원래 구조로 남아 있는 현상과 혼동한 것이 아니다. 실제 FCM의 mutilated graph를 전후 비교했다. 다만 **stale parent edge가 남았다는 사실만으로 숫자로 생성한 do 평균까지 틀렸다고 결론내리지 않는다.** 상수 치환으로 수치 효과를 만들 수 있어도 요구한 graph 계약은 통과하지 못했다.

이 결함을 확인한 시점에 이미 진행 중인 두 번째 arm을 중단했다. 최종 runner에는 해당 snapshot 실패 시 다음 단계로 넘어가지 않는 guard를 추가하고 소프트웨어 fixture로 검사했다. guard 추가 후 외부 모델을 재실행하거나 upstream을 패치해 성공으로 만들지 않았다.

## 6. 품질·잠재 투영·효과 식별

조작 대상 Force는 원래 길이와 강성에서 계산되는 물리량이다. 수학적 hard-do 변수 조작을 실제 설비의 force command/setpoint 또는 검증된 안전 조작으로 취급하지 않는다.

품질은 측정치가 하한 이상/상한 이하이면1인 flag들의 곱(AND)으로 생성된다. 반환 관측 Y는1이27행/0이5행,do16000은1이28행/0이4행이다. 이 수치는 API 진단이며,서로 다른 seed의 작은 반환 표본으로 효과 개선을 주장하지 않는다. 모델 내 양품 부호화이므로 `E[1-Y]`라는 비적합 확률 손실은 형식적으로 가능하다. 두 번째 arm이 완료되지 않아 ATE·손실 비교·최선 정책은 계산하지 않았다.

baseline24노드 ADMG에는 directed40개·고유 bidirected127쌍(상호 arc로 저장)·bow22개가 있었다. MAG는 directed90개·bidirected96쌍,bow0이다. directed 성분은 비순환이었다. 양방향 arc를 DAG의 방향순환2개로 세지 않았다. MAG의 adjacency/arrow는 물리 직접 부모와 같지 않다.

관측 ADMG에서 아래 작은 **hedge(같은 관측 분포만으로 효과를 구분할 수 없음을 보이는 부분 구조)**를 실제 typed edge로 확인했다.

- A=`PF_M1_T1_Force`
- M=`PF_M1_T1_Force_MpGood`
- Y=`Sec_C2_Machine1_ProcessResult`
- directed A→M→Y와 bidirected A↔M↔Y.
- F={A,M,Y},F'={M,Y}는 Y-rooted C-forest이고 F만 A를 포함한다.

반환 ADMG가 유효한 참조라는 조건에서,이는 일반 비모수적 `P(Y|do(A))`의 graph-only 식별을 막는 충분한 증거다. 전체 ID 알고리즘을 구현·실행한 것은 아니며 특정 충분 certificate를 검사했다. **알려진 물리 함수/추가 기능 제약을 허용한 좁은 모형에서도 불가능하다는 증명은 아니다.** 그러한 제약은 현재 관측-only 학습 계약에 자동으로 넣지 않는다. [Shpitser–Pearl2006,Definition7/Theorem4](https://ftp.cs.ucla.edu/pub/stat_ser/r327.pdf#page=4)

관측 내부14,813행의 Force 범위는 **7974.5685~22249.8301**이다.16000은 내부,30000은 경험 범위 밖이다. 이것은 수학적 지지집합 밖이라는 증명이 아니며 유한 자료의 외삽/실용적 positivity 문제로 분리한다.

101경로는61개의 effective seed만 사용했다. 규칙 `root+10000+30*subbatch+300*path` 때문에 중복이 생겼다. 관측42와 do1042의 실제 effective-seed 집합은 겹치지 않았지만,그 사실만으로 모든 행/경로가 독립이라는 증명은 아니다. 재현·distinct-seed 실행은 중단되어 미검증이다. fresh 객체의 개입 dictionary가 비어 있음은 확인했고 객체를 arm 간 재사용하지 않았다. 같은 객체 재사용의 carryover 시험은 하지 않았다.

## 7. 최종 판정과 다음 결정 하나

**CONDITIONAL_NOT_ACCEPTED**,RESOURCE_BLOCKED가 아니다. 실행 일부와 수치 치환이 성공했으나 모든 연구 연결 Gate가 통과하지 않았다. 핵심 차단 조건은 두 가지다.

1. **고정 버전의 hard-do graph 결함:** 원래 두 부모 간선이 제거되지 않는다. 공식 근거 있는 수정 버전 또는 명시적인 semantics 검토가 필요하며 조용한 로컬 수정은 하지 않는다.
2. **타당하고 식별 가능한 관측 연구계약:**81개 조건부 계층의 참조 계약,관측 ADMG의 hedge와30000 외삽,경로/RNG의 독립 단위가 해결되지 않았다. 표본을 늘리거나 위 한 줄만 고쳐도 원래 연구가 자동 성립하지 않는다.

고정 버전의 구조 점수–효과–선택 본연결은 착수하지 않는다. 그렇다고 모든 CausalMan 연구를 과학적으로 영구 기각하지도 않는다. TEP/기존 합성 결과와 섞거나 공식 환경으로 채택하지 않았다.

**향후 딱 하나는 연구계약 결정이다:** 관측-only 자료와 그래프만으로 점효과를 식별해야 한다는 조건을 유지할지 결정한다. 현재 조건을 유지한다면 이 micro 과제로 학습/추천에 진입하지 않는 것을 권고한다. privileged state·알려진 물리식·부분식별/보류를 허용하는 대안은 별도의 승인 대상이며 이번 결과를 보완한 새 독립 성공으로 포장할 수 없다. 새 smoke test·자동 패치·대규모 재실행을 다음 작업으로 만들지 않는다.

## 8. 재현·보존·검사

실제 실행은 외부 `prepare.py`,격리 venv의 core wheel/SciPy 설치,그리고 `scripts/run_causalman_micro_acceptance.py --workspace <EXTERNAL_WORKSPACE>` 및 같은 worker의 fresh-run 호출로 수행했다. 초기 launcher/미선언 SciPy 실패,수정 전 CONTRACT와 SHA,실행시 runner SHA,각 단계 command/receipt·stderr·진행 기록은 외부 작업공간에 보존했다. 개입 raw CSV·pickle·외부 소스는 Git에 넣지 않았다.

현재 Git의 prepare/runner는 재검토·tree 인증·자동 중단 guard를 포함한다. 실제 do16000 당시 runner SHA는 RESULT에 명시했으며,추가 guard를 외부 재실행으로 검증했다고 주장하지 않는다. source leaf/tree의 사후 재검산은 전체1,049개 불변이었다.

관련 소프트웨어 fixture 테스트,기존 전체 suite·frozen·환경계약·상태·diff 검사 결과는 RESULT의 repository_validation에 기록한다. 기존 suite의 과거 적합/CV 재검산은 이번 신규 연구 학습과 구분한다. 기존 PR15~24와 이번 PR을 자동 병합하지 않는다.

최종 로컬 검사는 **전체105개(기존96+신규 소프트웨어 fixture9) PASS,104.220초**다. 동결39SHA·변수순서·시계변환·환경계약15case·asset·상태·JSON/보존·diff 검사도 PASS했다. 새 추가파일 guard의 검사 순서 때문에 한 fixture가 먼저 실패했고,원래 기대값을 유지한 채 코드 순서를 고친 뒤 통과했다. 이전 보호5218파일은 불변이다. 이 검사 성공은 외부 acceptance 미수용 판정을 바꾸지 않는다.

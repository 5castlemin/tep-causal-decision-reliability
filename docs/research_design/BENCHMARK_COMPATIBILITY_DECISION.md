# Benchmark 호환성과 연구 경로 결정 Gate

기준일: 2026-10-23. **현재 가설 검증 Gate: 증거 부족(D). 다음 최소 복원 경로 권고: Track A.**
새 Primary 연구로 전환하지 않았다. `RESEARCH_DESIGN.md`는 변경하지 않는다.
Track B/C 채택 및 연구 범위 변경은 아래 근거를 검토한 사용자 승인 이후 별도 계약으로 다룬다.

## 1. GitHub 기준과 증거 수준

[PR #4](https://github.com/5castlemin/tep-causal-decision-reliability/pull/4)는 확인 시 OPEN/미병합, head `71c5448ed9a82548d86f40f60be842020f69538d`, CI run `39947597305` 성공이다. main은 `172e84bcafb82dd5074f097fcabfb94f28ff96e3`이다.
이번 브랜치 `feature/benchmark-compatibility-decision`는 PR #4 head에 의존한다. 새 PR의 base도 PR #4 브랜치로 둔다. PR #4나 이번 PR을 자동 병합하지 않는다. PR #4 병합 후 이번 PR의 base를 main으로 조정하여 검증한다.

- **VERIFIED:** 확보한 바이트·해시, 읽은 실제 코드의 정적 설정, 이미 실행된 원시 기록에서 직접 확인한 사항. 코드 설정 확인이 실행 재현을 뜻하지 않는다.
- **REPORTED:** 출처가 해당 생성 조건을 보고하지만 실제 생성 경로·실행을 독립 재현하지 못한 사항.
- **INFERRED:** 복수 근거와 일관되는 해석으로, 직접 확인한 원인이 아니다.
- **UNKNOWN:** 확인 가능한 대응 자료가 없다. 부재 증거와 혼동하지 않는다.

출처별 주장·상태는 `evidence/provenance_claims.json`, 실제 계산은 `evidence/local_20261023_v2/`에 있다.

## 2. 기존 benchmark 데이터 생성 환경

### 확인된 입력과 공개 저장소

고정 공개 commit `72b0f5e3d14192478186ee0dc4338b7448087789`의 CSV/GT와 현재 로컬 입력은 바이트가 동일하다(VERIFIED).

| 입력 | SHA-256 |
|---|---|
| datasetTE.csv | `52ae445b4355201db9591822282381c8de861afe49bdbc9452db08b01e7d3711` |
| TEGroundTruth.txt | `238542dbdde50887b5944fb3acc64a792b19a0c56bbfa06e3b267261f2fe6c43` |
| 공식 datasetTENumpy.txt | `2d0c99e87fe9d6fc13c3620f78e383ebe171ca87b0cd272e33866ba4256dabb4` |

CSV는 index 열 외 1499×31이며 모두 유한값이다. **공식 NumPy 배포본도 1499×31이고 CSV와 값이 정확히 일치**한다. 두 파일 모두 첫 데이터가 같다. 현재 로더에서만 header를 소모하여 한 행을 잃었다는 설명으로 해결되지 않는다. 업로드 전 처리에서 한 행이 빠졌는지는 여전히 UNKNOWN이다. 1500으로 맞추는 보간·추가·행 삭제는 하지 않았다.

고정 Git tree에는 데이터/그림/README만 있고 생성·전처리 스크립트는 없다. CSV 파일 이력은 `51308e9` 업로드 1건이다. 따라서 이 범위의 Git 이력만으로 seed·원시 파일·집계 코드를 회수할 수 없다. 다른 장소에도 없다고 주장하지 않는다.

### 논문과 upstream 계보

[CIPCaD 논문 IV-A/Table II·III](https://arxiv.org/html/2208.01529)는 Manca 정상 데이터를 사용하며 원측정 0.1Hz, 75시간의 3분 sliding median, 최종 빈도 3분과 1500 samples를 보고한다(REPORTED). 33변수에서 분산 0 변수를 제거했다는 설명도 있다. GT는 공정의 기계적 관계를 바탕으로 만든 구조 참조이며, 정상 데이터로 지연을 확정하지 못했다. 새 후보의 효과 정답으로 직접 연결하는 근거는 아니다.

새로 읽은 [Manca 작성자 기술보고서 v1.1](https://www.researchgate.net/publication/355917633_Tennessee-Eastman-Process_Alarm_Management_Dataset_-_Technical_Report) §1.2–1.3/§2.1은 Ricker(1996) 제어 구조, 2015 수정 Simulink 모델, 0.1Hz 및 별도 시간 파일을 보고한다. MV5·MV9는 닫고 MV12는 100으로 유지하는 조정 운전점을 설명한다(REPORTED). 현 CSV가 그중 어떤 원시 파일·seed·필터 계열에서 추출됐는지는 UNKNOWN이다.

### 시간·집계·누락의 정확한 상태

| 항목 | 상태 | 현재 판단 |
|---|---|---|
| CSV/공식 NumPy 순서·값 동일성 | VERIFIED | 1499행에서 완전 일치. index는 0..1498이며 timestamp가 아님 |
| 정상 원자료 0.1Hz | REPORTED | 논문 및 upstream 보고서 서술. 현 CSV와 행별 대응 미확인 |
| sliding window 길이 3분 | REPORTED | 논문 설명 |
| 최종 빈도 3분 | REPORTED | 논문 Table III. 기존 BENCHMARK_DEFINED 유지 |
| window stride/center/경계 처리/첫 sample | UNKNOWN | 최종 빈도가 개별 구현의 stride·경계 코드를 모두 확정하지는 않음 |
| 원시 timestamp / 시작·종료 구간 | UNKNOWN | 현재 입력과 연결되는 시간 파일 미확보 |
| 1500 vs 1499 | UNKNOWN | 공개 CSV와 NumPy 모두 1499인 것은 확인. 원인 미확정 경고 유지 |
| X27/MV5·X31/MV9 제외 | VERIFIED(현재 부재), 원인 연결은 INFERRED | 논문의 분산 0 제거와 upstream 밸브 정책이 일관되지만 제거 전 33열의 분산을 직접 검사하지 못함 |
| 시간순 사용 가능성 | 기존 VERIFIED_MODERATE 유지 | raw timestamp 직접 검증으로 승격하지 않음 |

## 3. 새로 확보한 공식 코드와 Python 후보

### Track A의 구체적 복원 단서

[Ricker 공식 대학 아카이브](https://depts.washington.edu/control/LARRY/TE/download.html)에서 두 ZIP을 실제 회수했다. 바이너리·source는 별도 로컬 작업 영역에 보존하고, 재배포 권리가 불명확하여 Git에는 넣지 않는다. source hash와 정적 추출값만 기록한다.

| archive | 바이트 | SHA-256 | 실행 |
|---|---:|---|---|
| temexd_mod.zip | 639921 | `e43227aaded739cfeba1ec281c54ac8a549f60753e064305a669b906c4b16b0d` | NOT_RUN |
| tecode.zip | 29307 | `2536e8a80e326c6a15ac2f636b1e2c48e1791e1b21dddc644f0725e87a8db724` | NOT_RUN |

현재 archive의 C 모델은 버전 1.3.3을 선언한다. `.mdl`의 ComputedModelVersion 1.124는 다른 버전 필드로 구분한다. 문서에서 지목한 모델 계열·버전 문자열과의 일관성은 있지만 **Manca가 사용한 파일과 바이트가 같은지는 UNKNOWN**이다.

실제 `MultiLoop_mode1.mdl`의 상수→TE Plant 입력 port→이름 있는 setpoint 연결을 추적했다. `xmv3` 같은 외부 블록 이름을 실제 XMV 번호로 오독하지 않았다.

| 실제 설정 입력 | port | archive 값 | benchmark 평균 | Python 후보 설정/초기값 및 기존 로그 |
|---|---:|---:|---:|---|
| Reactor Press Setpoint | 5 | 2800 kPa | X7 2800.002156 | 초기 압력 약 2705; 2시간 평균 2708.451115 |
| Reactor Level Setpoint | 4 | 65% | X8 65.004262 | controller 75%; 2시간 평균 74.920368 |
| Reactor Temp Setpoint | 9 | 122.9°C | X9 122.900131 | controller 120.40°C; 2시간 평균 120.401024 |
| 냉각수 조작값(설정 온도와 별개) | — | 여기서 동등성 미확인 | X32 35.946906% | 초기 41.10581288%; 2시간 평균 41.055246% |

평균과 archive 설정값의 근접성은 **복원 후보를 좁히는 INFERRED 근거**이다. 같은 표본을 생성했다는 증명은 아니다. 이를 이유로 Python setpoint만 바꾸는 튜닝을 하지 않았다.

archive의 `Mode_1_Init.m`에서 `Ts_base=0.0005h`(1.8초), `Ts_save=0.01h`(36초), `.mdl`에서 `ode45`를 직접 확인했다. 이는 **현재 회수 archive의 기본값**이며 Manca가 실행한 sampling 10초와 동일하다고 할 수 없다. `load Mode1xInitial`이 초기 설정을 덮어쓰므로 literal u0만 복사해서 복원했다고 주장할 수 없다.
README는 해당 multiloop 모델에 override loops가 없다고 설명한다. 후보 Python controller에는 pressure override 코드가 있어 추가 차이이다. 현재 PATH에서 MATLAB 실행 명령을 찾지 못했고, Simulink 정상 운전·개입·반복은 NOT_RUN이다. 다른 위치의 설치 부재까지 단정하지 않는다.

대학 아카이브는 원본 Fortran과 수정 모델을 구분하고 원본의 variable-step 사용에 관한 주의를 제공한다. 이를 이번 고정 step Euler 결과가 틀렸다는 직접 증거로 사용하지 않는다. 두 수치 계약은 다르다.

### 현재 Python 후보에서 직접 확인한 범위

source `9a6c8e5fcef4a2850778704e7793c87b0a187005` 및 controller SHA는 로컬 감사 JSON에 있다. 이전 실행과 source hash가 같고 source 작업 사본은 clean이다. Python Euler 1초, yy 50, XMEAS 41, XMV 12, 초기 MV5=22.21/MV9=47.44573456/MV12=50이다. 단일 RNG `_g`를 사용한다.
이전 실험에서 정상 30분 및 2시간, 수동 XMV10 명령, IDV4와 새 객체 반복을 실행했다. 이번에는 이를 재실행하지 않고 원시 해시와 분석을 검증했다. 3 step의 제한적 수렴 경향은 독립 기준 정확성 검증을 대체하지 않는다.

## 4. 동등성·차이·불확실성

| 차이 요인 | 실제 증거 | 결론 |
|---|---|---|
| 변수 이름/선언 단위 | 기존 대응표와 source | 대응 가능. 물리적 scale·개입 동일성은 별도 |
| 운전점 | archive setpoint 및 양쪽 실제 평균 | 차이의 구체적 설명 후보 확보; 유일한 원인 분해는 미완료 |
| 제어기 | archive multiloop/override 설명, Python 실제 PI/override 코드 | 동일하다고 볼 수 없음. 기존 정상 MV는 외생 무작위 개입이 아님 |
| sampling·집계 | archive 기본 36초, upstream 보고 10초, benchmark 3분, 후보 진단 기록 30초 | 서로 다른 층위. 후보 40개 비중첩 중앙값은 원 preprocessing 재현 아님 |
| scale | X19 benchmark 약 0.5, Python 약 230인 기존 기록; 선언 단위는 동일 | 닫힌 증기 정책과 일관되는 가설이 있으나 단위오류·잡음·모델 효과를 분리하지 못함. 임의 배율 보정 금지 |
| 잡음/disturbance | upstream 별도 seed 서술, 후보 `_g`/xns 및 기존 원시 plan | 동일 realization·RNG 구조·선택 seed 미확인. 정상이라고 잡음이 없지는 않음 |
| 모델 revision | 수정 C 1.3.3과 후보의 Fortran 유래 Python 식 | 계열 차이 확인; 방정식 수준 동등성·원시 실행 버전은 미검증 |
| GT 범위 | 33-node 참조에서 현 31×31/28간선 채점 | 구조 채점에 사용 가능. 새 controller 포함 동적 구조·효과·식별 정답 자동 승계 불가 |

정규화로 운전 정책·제어기 피드백·잡음·개입 의미가 같아지지 않는다. 현재 환경 차이는 구조 오차와 섞인다. 정상 관측 Ridge 적합이 존재한다는 사실도 이를 해결하지 않는다.

## 5. Track A/B/C 비교와 가설·식별 위험

| 기준 | A: benchmark 환경 복원 | B: simulator-native 재설계 | C: 외부 전이 |
|---|---|---|---|
| 원 질문과 일치 | 동일 생성환경 복원 성공 시 가장 직접적 | 새로운 환경과 유효한 참조 구조를 확정하면 가능 | 다른 환경 일반화 질문. 원 질문의 직접 검증 아님 |
| 실제 근거 | 공식 코드 회수, setpoint 3개 근접, 보고서 계보 | 기존 후보 실행·재현은 있음. 신규 관측 데이터와 새 GT는 없음 | 기존 graph와 새 후보는 있음. 동등성 없음 |
| 인과 식별 | 동일 환경이어도 관측 closed-loop 내생성·SCM 가정 별도 점검 | controller 포함 구조·누락변수·동시점 정책 명시 필요 | 원 환경 구조 오차와 domain shift 분리 어려움 |
| 독립 평가 | 복원 환경의 실제 조작 결과 확보 필요 | SCM 예측과 별도로 새 seed/실행의 simulator 반응 측정. 동일 코드 내부 검증의 한계 병기 | 외부 반응은 측정 가능하나 원래 GT 대비 효과 정답은 아님 |
| 기존 자산 | 데이터·7 frozen graph 최대 보존 | 기존 7개는 과거 자산. 새 학습 graph는 별도 이름·manifest 필수 | 기존 graph 활용 높음, 원 GT 점수 해석 제한 |
| 실행성 | source는 회수. MATLAB/Simulink·정확 원시 계보 미확보 | Python 실행 가능. 수치 검증·원본 알고리즘 코드·새 참조 구조가 선결 | 제한적 탐색은 가능하나 과제/API·단위·운전점 계약 필요 |
| 재현성 | 아직 NOT_RUN | 기존 초기화 계약 있음; 신규 생성/학습 프로토콜 미작성 | 기존 기록만 재현 가능, 전이 실험은 미실행 |
| 주요 위험 | 알려지지 않은 export/seed와 controller 설정을 사후 맞춤 | 잘못된 GT를 만들어 구조 F1 타당성 상실 | 혼란요인 미통제로 구조 지표 설명력 과장 |
| 구현 부담 | source/환경·초깃값·집계 복원 중심 | 데이터 생성, 동일 환경 discovery 재실행, GT 타당성의 큰 추가 범위 | 비교적 작은 탐색이나 원 가설의 증거 강도 낮음 |

공통 식별 주의: 환경을 맞추는 것은 필요조건이다. 관측계수의 개입 해석, 제어기 유지/절단 정책, 독립 seed 및 reference no-action, 효과 estimand까지 자동 해결하지 않는다. 7 graph·종속된 과제만으로 일반적 설명력을 단정하지 않는다.

## 6. 권고와 승인 Gate

**현재 결론은 D(원래 가설을 검증할 증거 부족). 다음 작업은 A의 제한적 복원 확인을 우선 권고한다.** 이유는 이제 공식 코드와 맞는 운전점 단서가 실제로 확보됐기 때문이다. A가 완성됐다는 의미가 아니다.

- Primary 질문·기존 구조 평가 체계는 유지한다. A의 완료 조건은 모델/초기화/제어기 대응, 원시 시간·집계 대응, 실제 개입 API, 같은 조건 반복, 잔여 차이 문서화이다. 하나라도 빠지면 직접 효과 정답 사용은 계속 금지한다.
- B는 **대안 제안**으로 남긴다. 사용자가 재설계를 승인하기 전 대규모 데이터 생성·7개 학습을 시작하지 않는다. 특히 새 환경의 관측 범위·controller·시차를 반영한 참조 구조를 어떻게 검증할지 먼저 승인해야 한다. 28간선을 그대로 복사하지 않는다.
- C는 **Secondary 탐색 제안**이다. 사용자가 별도 전이 질문과 혼란요인 통제를 승인한 뒤 진행한다. Primary 가설의 검증으로 계산하지 않는다.
- 이번 Gate는 A/B/C를 한 점수로 순위화하지 않는다. 즉시 실행 가능한 코드의 존재만으로 B를 Primary로 확정하지 않는다.

## 7. 다음 최소 검증과 중단 조건

1. 원시 파일 회수 요청안을 준비한다. 필요한 것은 benchmark 작성자가 선택한 정상 파일명/기간, `SIMOUT.xlsx`, `XMV.xlsx`, 별도 시간 파일, seed 파일, model flag·수정 controller/initial state 및 median export 코드이다. 외부 연락은 사용자 별도 승인 없이 보내지 않는다.
2. 회수 archive의 MATLAB/Simulink 실행환경 위치·라이선스와 버전 호환 여부를 확인한다. 접근 가능하면 결과를 보기 전 짧은 정상 실행 계획을 고정하고 반복·시간·MV 정책을 검사한다. 이 단계에서 새로운 알고리즘을 실행하지 않는다.
3. 1·2를 확보하지 못하면 A의 불확실성을 유지하고 B의 **참조 구조 타당성 감사만** 할지 사용자 결정을 받는다. 출처 없는 setpoint 튜닝·원시 행 복원으로 A를 통과시키지 않는다.

## 8. PR #4 자산 검토와 보존

156개 변경 중 145개 신규 파일, 변경 후 내용 합계 16,740,258 bytes이다. 최대 파일은 2시간 terminal JSON 3,809,278 bytes, CSV 1,263,432 bytes이다. 전체 파일별 hash·크기·중복은 `pr4_asset_review.json`에 있다.
바이트 동일 그룹은 24개(88개 경로)이다. 반복 실험의 동일 결과, 초기화 snapshot, 빈 terminal 및 v2/v3 동일 통계가 포함된다. **88개가 모두 불필요하다는 뜻이 아니다.** 같은 blob은 Git에서 공유한다. 첫 run은 시계 보완 이전 이력이고 v3는 반응 시계열이 추가되어 v2 전체의 단순 복사도 아니다.
표현·표본 범위의 중복은 확인했으나 원시 hash manifest와 검증기가 이력을 참조하므로 이번에는 삭제·이동하지 않았다. 향후 단일 canonical 출력+이력 참조로 줄이는 정책은 별도 검토 대상이다. 새로운 대용량 source/ZIP을 Git에 추가하지 않는다.

## 9. 허용하지 않는 결론

- TEP라는 이름·변수 대응·setpoint 근접성만으로 같은 데이터 생성기라고 주장하지 않는다.
- 분포 차이의 원인을 단일 요인으로 확정하거나 정규화로 해결했다고 주장하지 않는다.
- 후보 수렴 경향을 실제 공정의 물리 검증으로 승격하지 않는다.
- 새 simulator에 기존 28간선 GT를 정답으로 부여하거나 새 graph와 frozen graph를 혼합하지 않는다.
- 외부 전이 결과로 원래 구조 정확도–효과 신뢰성 가설을 입증했다고 주장하지 않는다.
- 이번에 SCM 학습·신규 인과발견·Recovery/Safety·Simulink 실행을 수행했다고 기록하지 않는다.

## 10. 이번 Gate에서 실제 수행한 것

공식 source ZIP 두 개 회수/해시, 고정 CSV·GT와 공식 NumPy 값 비교, Simulink 정적 설정 배선 및 source 검토, PR #4 파일 크기·동일 바이트 검토, 기존 진단 validator·동결 산출물·상태 문서 검사를 수행했다. 신규 시뮬레이션은 **NOT_RUN**이다. 기존 `RESEARCH_DESIGN.md`, 그래프, Step 6, simulator 원시 CSV/manifest는 변경하지 않았다.

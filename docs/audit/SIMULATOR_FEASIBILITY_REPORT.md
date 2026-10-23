# Simulator feasibility — 2026-10-23

PR #1은 사용자 승인 후 merge commit `ceb447deb03f5532dc274cb97de2cd7f317349e7`로 병합했다. 최신 main의 AGENTS.md를 확인하고 `feature/simulator-feasibility`에서 작업했다.

## Track A: 기존 실행 자료

기존 감사 범위를 반복 검색하지 않았다. 8월 보고서의 소스 확보/기초 연동 주장은 여전히 REPORTED_ONLY이며 구체 저장소·버전·명령 단서가 없다. 당시 실행자에게 필요한 질문은 “사용한 저장소 URL 또는 ZIP 이름, commit/version, Python 환경, 정상 운전 명령, controller 설정과 원시 로그를 제공할 수 있는가?”이다. 새 후보를 8월 구현으로 간주하지 않는다.

## Track B: 후보 비교

| 후보 | 소스/버전 | 라이선스 | 환경·인터페이스 | 실제 결과 |
|---|---|---|---|---|
| pyTEP | https://github.com/ccreinartz11/pytep ; SoftwareX DOI 10.1016/j.softx.2022.101053 보고 v0.1.0 | 논문/프로젝트 BSD-3-Clause | Python MATLAB Engine, MATLAB/Simulink R2019a–R2020b | 문서 검토. MATLAB 명령 확인 못함; 실행 NOT_RUN |
| TEP Studio | https://github.com/khalidlabs/tep-studio commit `852f0c69ab974540750d61bd1dbfafd56bfd80bb`, 0.2.0 | Python wrapper BSD-3-Clause; bundled temexd_mod의 권리는 별도, LICENSE 주석 확인 | Python>=3.10, CFFI/C compiler, 수정 TEP 41측정/12조작, Ricker controller, direct MV와 setpoint 별도 | 설치 실패. CP949 오류는 PYTHONUTF8=1로 해결했으나 MSVC 14+ 부재. 정상 운전 NOT_RUN |
| TEP-Rust | https://github.com/jkitchin/tep-rust commit `0735ad3b5bb7fdd367a8a31da1db8a209dac2a15` | MIT 및 upstream LICENSE 별도 | Rust/PyO3, 원 Fortran port; source install Rust 필요 | source/README/LICENSE만 확보. cargo/rustc 확인 못함, 실행 NOT_RUN |
| Python TEP | https://github.com/jkitchin/tennessee-eastman-profbraatz commit `9a6c8e5fcef4a2850778704e7793c87b0a187005`, pyproject 2.5.0 | root LICENSE Illinois 조건부 허용, pyproject BSD-3-Clause 표기. upstream 저작권 보존 필요 | Python backend, NumPy; 50상태/41측정/12조작/20 IDV, Euler 1초, 폐루프 PI·manual mode | 아래 실제 5개 실행 성공. 장기 안정성/Fortran 수치 일치는 이번에 검증 안 함 |

소스 checkout은 연구 저장소 밖 별도 디렉터리에 보존했다. upstream source를 재배포하지 않으며 wrapper의 실행 계약만 추적한다. 소스 내부 instruction/skill 문서는 지시서로 사용하지 않았다.

## 사전 고정 smoke protocol

`run_20261023/plan.json`은 결과 확인 전에 작성했다. seed=42, 총 1800초, 적분 1초, 30초 기록. 폐루프 정상 2회, 수동 기준, 수동 MV10 +1 percentage point(600초부터), 폐루프 IDV4(600초부터). MV10 명령은 소스가 정의한 0..100% 범위 안에서 수행했지만 이것이 안전한 물리 운전 범위라는 뜻은 아니다. 이 protocol은 복구 과제나 Safety 기준을 확정하지 않는다.

명령(저장소 루트):

```powershell
python -X utf8 experiments/simulator/run_feasibility.py --source ../tep-python-candidate --output experiments/simulator/run_20261023_v3
```

Python 3.11.15, NumPy 2.4.6. source는 위 commit에 고정하며 다른 commit이면 실행 거부. 결과 폴더 덮어쓰기 금지. 각 실행 CSV에 시간(h), XMEAS1..41, XMV1..12를 보존하고 SHA-256을 summary에 기록했다.

## Gate 결과

| Gate | 판정 | 근거와 한계 |
|---|---|---|
| 1 정상 운전 | PASS (30분 smoke 한정) | 폐루프 정상 실행 1800초 도달, 61기록, 유한값, shutdown 없음. 장기 정상 운전 인증 아님 |
| 2 같은 조건 2회 | PASS | 두 정상 CSV byte hash 동일, 배열 exact equality true |
| 3 시계열 기록 | PASS | CSV 5개, 전체 변수·단위 schema, source commit·seed·시간 단위 기록 |
| 4 조작 반영 | PASS (manual 직접 XMV) | MV10 41.10581288→42.10581288; 자동 제어기 우선순위를 피하기 위해 manual mode 사용. setpoint 조작은 NOT_RUN |
| 5 반응 기록 | PASS (반응 관측); horizon 완주 FAIL | 수동 reference 대비 온도 차이 관측. intervention은 1788초 shutdown, 1770초 마지막 공통 관측. 인과효과의 물리 정확성·안전성은 미검증 |
| 6 Fault/초기화 | PARTIAL | IDV4 active=1 확인, 30분 완주. clear+initialize 후 IDV=0·time=0 확인. 그러나 동일 초기 관측 복원 false. 새 인스턴스 반복은 Gate2 통과하나 동일 객체 reset은 추가 검증 필요 |
| 7 기존 데이터/GT 호환 | PARTIAL / effect oracle BLOCKED | 31변수 이름 대응 가능. 동일 모델·제어기·운전모드·잡음·전처리 계보는 확인 못함 |

첫 실행은 길이가 다른 trajectory를 뺄 때 broadcast error로 요약 작성이 실패했다. 원시 CSV/plan은 `run_20261023/`에 보존했다. v2는 공통 timestamp로 비교하도록 수정했고, v3는 terminal measurement와 Fault/reset 진단을 추가했다. 개입 값·시작 시점·모드는 바꾸지 않았다. v3는 같은 shutdown을 재현했다.

## 변수·단위·호환성

기존 mapping source `benchmark_reference_mapping.csv`(논문 Table II)를 별도 복사하고 SHA를 기록했다. X1..X22 = XMEAS(1..22), X23..X33 = XMV(1..11), X27/X31 제외는 각각 XMV5/XMV9 제외다. 이 규칙으로 graphs/final/variables.csv 31개를 매핑한다. X32는 MV10 reactor cooling water, X9는 XMEAS9 reactor temperature(°C). simulator의 전체 53개 관측/조작 변수 중 일부를 투영하는 것이며, 미포함 변수에 대한 동역학은 그대로 남는다. XMV12 agitator와 조성 측정은 평가 GT에 없다.

이름·단위 대응은 구현의 물리·인과적 동등성을 입증하지 않는다. CPCaD-Bench/Manca 데이터의 실제 controller·모델 revision과 동일함을 입증하지 못했다. 이번 CSV는 30초 기록이며 기존 benchmark-defined 3분 sliding-window median 결과와 같지 않다. 기존 GT의 개입 정답으로 사용할 수 없다. 원래 Final graph, GT, 12개 structural task는 변경하지 않았다.

## 남은 위험과 다음 관문

1. manual 개입의 큰 온도 반응과 조기 shutdown: 적분 step 민감도, upstream reference/Fortran 비교 및 종료 원인 확인 전 효과 크기를 연구 결과로 해석하지 않는다.
2. 동일 객체 reset의 관측 불일치: RNG·상태·controller reset 계약을 조사해야 한다. 현재 재현 단위는 새 인스턴스다.
3. 30분 smoke는 긴 정상 안정성과 Fault 복구 가능성을 검증하지 않는다.
4. 공통 비교 전에 모델/운전모드/controller/단위/전처리 대응을 확인해야 한다. Safety/Recovery 임계값은 아직 미확정이다.
5. 우선순위는 위 수치·reset 검증과 데이터 생성 모델 확인이다. 새 알고리즘·비선형 SCM은 추가하지 않는다.

추가 시간표현 한계: 후보 `step()`는 현재 시각에서 측정값을 계산한 뒤 Euler로 상태와 시간을 전진시킨다. 따라서 반환 측정값과 `sim.time` 사이에 최대 1 적분 step의 시점 차이가 있을 수 있다. CSV는 API가 반환한 값을 그대로 기록했으며 이 정렬을 개선·확인하기 전 정밀한 시차 효과를 주장하지 않는다.

## 재현 환경 준비

저장소의 상위 폴더에서 아래처럼 후보 소스를 별도로 취득한다. 이미 소스가 있으면 새로 덮어쓰지 않고 commit을 확인한다. 실행 코드는 `--source`의 commit을 검증한다.

```powershell
git clone https://github.com/jkitchin/tennessee-eastman-profbraatz.git tep-python-candidate
git -C tep-python-candidate checkout 9a6c8e5fcef4a2850778704e7793c87b0a187005
```

Python 3.11.15 + NumPy 2.4.6로 실제 실행했다. 본 연구 저장소의 requirements와 분리한 환경에서도 NumPy만으로 pure Python backend를 불러올 수 있다. upstream 컴파일·pip 설치 없이 해당 checkout의 src를 import한다. compiler가 필요한 Fortran backend는 사용하지 않았다. 구현별 신뢰성 주장은 upstream 문서의 주장과 이번 검증을 구분해야 한다.

# 공개 TEP 시뮬레이터 탐색과 실행 비교

2026-10-29. **동일 생성환경으로 확인된 후보는 아직 없다.** 잠정 상태는 `CLOSE_CANDIDATE_BUT_UNVERIFIED`이며 조사 전체 완료 판정은 아니다. 공식 2015 모델이 문헌상 가장 가까우나 실행 환경과 원본 데이터 계보가 부족하다. 일부 실행 가능한 후보까지 비교를 완료하지 못했으므로 공개 후보 전체가 부적합하다고 주장하지 않는다. 다섯 가지 일치 조건이 모두 확인된 후보가 없어 즉시 종료 규칙은 발동하지 않았다.

## 조사 범위와 분류

공식 보관소, GitHub, NIST와 관련 논문을 21개 후보 항목으로 정리했다. 이 수에는 시뮬레이터 본체 외 인터페이스·복제본·논문상의 모델도 포함된다. 중복을 감안해 **6개 보수적 구현 계열**로 묶었지만, 이는 서로 독립적인 화학 방정식 6개가 증명됐다는 뜻이 아니다. 분류는 `CANDIDATE_INVENTORY.csv`, 출처와 검색 질의는 `SEARCH_EVIDENCE.json`에 있다. 더 많은 공개 구현의 존재를 배제하지 못한다.

- [공식 Ricker 2015와 다른 제어 버전](https://depts.washington.edu/control/LARRY/TE/download.html): Manca 문헌의 생성모델과 연결되는 가장 강한 후보. 현재 MATLAB/Simulink가 없어 본 모델을 실행하지 못했다.
- [TEP Studio](https://github.com/khalidlabs/tep-studio): 공식 C·헤더·초기 상태 세 파일과 바이트 일치하며 앞선 실제 실행을 재사용했다. 제어/시계/원본 계보는 미확정이다.
- [pyTEP](https://github.com/ccreinartz11/pytep), [COSTEP](https://github.com/kennyuren/COSTEP), [DVCP-TE](https://github.com/satejnik/DVCP-TE), [TEP Attack](https://github.com/pwwl/tep-attack-simulator), [TEP Plus](https://github.com/gustavoleitao/tennessee-eastman-process-plus): Simulink 또는 그 인터페이스/파생 구현으로, 현재 필수 상용 실행환경이 없어 미실행. pyTEP 자체를 독립 Python 공정 모델이라고 계산하지 않는다.
- [profBraatz Python](https://github.com/jkitchin/tennessee-eastman-profbraatz), [tep2py](https://github.com/camaramm/tep2py), [tep-rust](https://github.com/jkitchin/tep-rust), Braatz/Chiang Fortran: 원래 Fortran 계열과 그 이식·수정이다. `tep2py`는 격리 복사본에 단계별 측정 제약 감시를 삽입해 3분 한 행을 실행했다. 원본 소스는 변경하지 않았고 패치는 별도 기록했다. 감시는 모든 상태와 모든 무한값을 검증하지 못한다.
- [AgentTwin](https://github.com/alqithami/AgentTwin)의 기본 실행기는 기존 Python 구현과 공정 backend, simulator, controllers, constants 네 파일의 SHA가 모두 같아 같은 시험을 중복 실행하지 않았다. 주변 제어·학습 환경의 동일성까지 주장하지 않는다. APMonitor의 브라우저 구현도 기존 Python backend의 번역으로 설명된다.
- [NIST TESIM](https://github.com/usnistgov/tesim)은 C++ 실행기를 제공하지만 공개 README의 Windows Visual Studio/Boost 구성을 현재 로컬에서 실행하지 못했다. Linux 이식 가능성은 미확인이다. [Modelica 논문](https://www.nist.gov/publications/implementations-tennessee-eastman-process-modelica)은 두 라이브러리를 제시하나 실행 가능한 소스/환경은 확보하지 못했다. Aspen HYSYS는 문헌상의 구현으로 상용 라이선스와 실제 모델 파일은 확보하지 못했다.
- [Green Cinnamon tep-plant](https://github.com/Green-Cinnamon-Labs/tep-plant)는 공개 설명에 따르면 유량·열·측정 부분이 미구현이어서 현재 완성된 TEP 정상 실행으로 취급하지 않는다. 이는 프로젝트 전체의 영구적 부적합 판정이 아니다.

## 실제 실행 및 비교

공통 기준 CSV는 1499×31, SHA-256 `52ae445b4355201db9591822282381c8de861afe49bdbc9452db08b01e7d3711`이다. 기존 변수 대응은 `VARIABLE_MAPPING.csv`에 **잠정**으로 보존한다. 특히 X19와 X16의 단위 및 시간 대응을 재확인해야 한다. 31변수의 평균·표준편차·분위수·자기상관과 이전 Python/Studio 평균은 `COMPARISON_RESULTS.csv`, Rust와 원본의 상관행렬은 `RUST_SUMMARY.json`에 있다. 원본 처리·시계가 미확정이므로 비교용 수치가 공식 재현 검정은 아니다.

| 관측 변수 | 원본 1499행 평균 | Rust 기본 10분 | 기존 Python 기본 10분 | Studio 기본 2시간 |
|---|---:|---:|---:|---:|
| 압력 X7 kPa | 2800.002 | 2705.571 | 2704.525 | 2705.967 |
| 액위 X8 % | 65.004 | 75.006 | 74.988 | 74.624 |
| 온도 X9 °C | 122.900 | 120.401 | 120.398 | 120.399 |

Rust 고정 commit `0735ad3b5bb7fdd367a8a31da1db8a209dac2a15`를 격리 Linux에서 컴파일해 36초와 10분을 순차 실행했다. 10분 600행은 유한했고, 수신된 1초 간격 측정에서 정의한 압력·온도·액위 제약 위반은 없었다. 표준 출력 버퍼 때문에 검사 시점이 실제 계산보다 늦을 수 있어 **내부 모든 단계의 즉시 차단을 보증하지 않는다**. native shutdown은 별도 종료를 사용했다. seed는 465120799이고 독립 반복이 아니다. Rust 10분 CSV SHA-256 `e4a38685a9e430772cbce269c57c92a8d8df5f3d04b0a13d71517c2ebde09888`, 원시 파일은 Git 제외 `data/local/tep_simulator_search/`와 [실행 기록](https://github.com/5castlemin/tep-causal-decision-reliability/actions/runs/40894701896)에 있다.

선행 PR #29 Studio B는 1.519시간에 스트리퍼 액위 측정 제약을 초과하므로 그 이후 자료는 안전한 정상 운전의 증거로 취급하지 않는다. 위 표의 원본은 약 75시간 가공 자료이고 나머지는 10분 또는 2시간 과도 자료다. 원본 가공 규칙과 개별 독립 반복이 없어 평균·상관 차이를 생성환경 동일성의 통계적 판정으로 해석할 수 없다. **수치 동등성 허용오차를 결과 전에 정량 지정하지 못했으므로 별도 수치 동등성 검정도 미실행**이다. 기존 다섯 필수 조건 중 생성 계보·제어·변수/가공 조건이 입증되지 않아 후보를 일치로 선언할 수 없다.

`tep2py` 고정 commit `3098351caed95dfed2168a3ddbd681e9a65f8710`은 격리 Linux에서 Fortran을 컴파일했다. 첫 시도는 함수 인자 오류로 실행 전 실패했고 호출 방식만 수정해 한 번 재시도했다. 원본을 보존하고 별도 소스 사본에 제약 감시와 초기 출력 sentinel을 삽입한 180초 실행은 유한한 출력 한 행을 생성했으며, 압력·액위·온도는 2706.356 kPa·74.639%·120.396°C였다. 출력 시계는 180번째 적분 직전의 약 179초다. 감시는 특정 액위·압력·온도와 측정 NaN을 확인했으나 모든 상태 및 다른 변수의 무한값까지 포함하지 않는다. 따라서 장기 안전성은 미확인이고 추가 연장은 하지 않았다. [실행 기록](https://github.com/5castlemin/tep-causal-decision-reliability/actions/runs/40895387262), 단일 행 SHA-256 `b5e162c467ba61e4bf2f12b4e4f71f7ad9223012cc2208c42410f769fbd32535`, 패치 SHA-256 `19b54f7e54826039f8e097b5e517bd1561d45caddbf6bba94c5fc168ee280c04`. 한 행은 분산·상관을 계산할 수 없으며 동등성 근거가 아니다.

## 판정과 다음 단계

공식 2015 환경은 가장 유력한 계보 후보이며 Studio는 동일한 공정 파일을 사용하는 실제 실행 후보지만, 어느 쪽도 원본 데이터의 제어기 기억, 고정 명령, 잡음, 시간 및 가공 계보가 완성되지 않았다. 기존 7개 그래프 및 28개 간선은 과거 벤치마크 결과로 보존하지만 새 개입 결과에 연결할 수 없다. 구조 참조의 완전성은 별도 문제다. 사용자의 연구환경 변경 승인이나 새로운 데이터 생성·인과발견·효과 실험은 수행하지 않았다.

후보 탐색과 실행 비교가 아직 완료되지 않아 이번 산출물의 B 판정은 **잠정**이다. NIST의 빌드 가능성은 실제 시험하지 않았다. 다음 하나의 실질 작업은 **NIST TESIM의 격리 Windows 빌드와 단계별 제약을 감시할 수 있는 짧은 정상 실행을 검증하는 것**이다. 수행 전 원본 버전·정확한 명령·안전 중단과 31변수 매핑·비교 허용 기준을 고정한다. 실행이 불가능하면 원인을 기록하고 다음 후보로 넘어간다. 공식 Manca 원시 trace와 메타데이터 확보도 동일환경의 최종 판정을 위해 별도로 필요하다.

기존 연구 가상환경 단위검사 105건, 동결 39개 해시·변수 순서 및 기존 환경·구조 검사를 실행한다. 새 Rust 실행기와 비교는 1회용 branch/commit 표식에만 연결해 이후 push에서 반복하지 않는다.

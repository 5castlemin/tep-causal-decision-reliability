# MATLAB/Simulink 로컬 환경과 공식 TEP 실행 검증

2026-10-30. **로컬 Windows 접근은 가능하지만 공식 모델 실행은 차단 상태다.** MATLAB 명령, 일반 설치 폴더와 설치 프로그램 등록 정보를 확인한 범위에서 MATLAB·Simulink를 찾지 못했고, PATH 및 일반 설치 위치에서 사용 가능한 C 컴파일러도 찾지 못했다. 다른 비표준 위치의 설치가 전혀 없다고 증명한 것은 아니다. MATLAB 자체가 실행되지 않아 버전, Simulink 제품·라이선스, `mex -setup c` 및 컴파일러 호환성은 미확인이다.

Windows 11 Pro 64비트, i3-1315U, 메모리 약 15.7 GiB, 확인 시 사용 가능한 메모리 약 3.1 GiB, C: 여유 약 47.1 GiB다. 기존 Python 가상환경을 읽어 검사를 실행했으며 패키지와 시스템 전역 환경은 변경하지 않았다. 학교 계정의 라이선스 보유 여부는 알 수 없다. [MathWorks 학교 라이선스 개인 PC 안내](https://www.mathworks.com/academia/campus/resources/user-guide.html)와 해당 버전의 [컴파일러 지원표](https://www.mathworks.com/support/requirements/supported-compilers.html)를 참조해 사용자가 공식 로그인·설치를 해야 한다.

## 공식 소스와 자료

보관된 공식 `temexd_mod.zip` SHA-256 `e43227aaded739cfeba1ec281c54ac8a549f60753e064305a669b906c4b16b0d`과 Studio 고정 소스의 C, 헤더, Mode1 초기 상태 세 파일을 직접 다시 대조해 일치했다. `.mdl`, 초기화 스크립트와 라이브러리를 포함한 개별 해시는 `SOURCE_MANIFEST.json`에 있다. 공식 ZIP 원본과 분리된 Git 제외 `data/local/tep_matlab_local_validation/staged_20261029/`에 8개 필요한 파일을 실제 준비했다. ZIP의 구형 prebuilt MEX는 실행·복사하지 않았다.

공식 README는 R2014b에서 시험한 모델, `PreLoadFcn=Mode_1_Init`, `StopFcn=TEplot`, Mode1에 override 부재를 기술한다. `Mode_1_Init.m`은 `Mode1xInitial.mat`을 읽으며 제어 주기 0.0005시간과 저장 주기 0.01시간을 정의한다. 모델은 ode45를 사용한다. 이 보관본과 Manca가 사용한 실제 바이너리·제어기 초기 기억·난수·전처리 코드의 바이트 동등성은 확인되지 않았다. [공식 모델 출처](https://depts.washington.edu/control/LARRY/TE/download.html), [Manca 기술보고서](https://www.researchgate.net/publication/355917633_Tennessee-Eastman-Process_Alarm_Management_Dataset_-_Technical_Report).

원본 `datasetTE.csv`는 1499×31, SHA-256 `52ae445b4355201db9591822282381c8de861afe49bdbc9452db08b01e7d3711`. `COMPARISON_31.csv`는 원본만 수록하고 공식 출력은 `NOT_RUN`이다. 기존 X1–X33 후보 대응은 `VARIABLE_MAPPING.csv`에 **잠정**으로 남긴다.

## 실행 상태 및 안전 차단

공식 MATLAB 설치·라이선스 확인, MEX 컴파일, 모델 로드, 10분·2시간·6시간 실행, 공식 출력 및 31변수 비교는 모두 **NOT_RUN**이다. 따라서 공식 모델의 압력·액위·온도 값과 컴파일 호환성에 대한 결과는 없다. 기존 Rust·Python·Studio 결과를 MATLAB 결과로 재분류하지 않는다. 다른 Simulink 후보도 라이선스 환경이 없으므로 미실행이며 모델 자체가 부적합하다는 뜻이 아니다.

자료 준비기·Windows 확인기·MATLAB preflight·기술 비교기는 `research_runs/tep_matlab_local_validation/`에 있다. Windows 확인과 소스 스테이징을 실제 실행했다. MATLAB preflight는 이 PC에서 실행하지 못한 초안이며, `tep_official_run.m`은 측정·내부 상태·명령에 대한 온라인 중단 감시가 검증되기 전에는 의도적으로 실패한다. **즉시 10분 실행 가능한 안전 감시 코드는 아직 준비되지 않았다.** 선행 Studio B에서 native 종료 신호 없이 센서 제약이 초과된 점 때문에 종료 신호만으로 시험을 허용하지 않는다.

문헌상의 XMV5/9 폐쇄와 XMV12=100은 조정 운전의 보고이며 현재 CSV의 특정 실행·명령 경로와 직접 연결되지 않았다. 공식 모델 실행을 해도 31개 변수의 시간·단위·가공과 전체 구조 참조는 별도 검증이다. 적합 후보 미발견 상태이므로 다른 후보 탐색의 즉시 종료 조건은 발동하지 않았다.

## 검사와 다음 단계

동결 39개 해시·변수 순서, Step 6, 자산·환경 계약 검사를 실행했다. 전체 단위검사 결과와 실행 명령은 작업 기록에 남긴다. `INSTALLATION_GUIDE.md`에 공식 학교 계정 로그인과 설치, 컴파일러 설정 및 staging·preflight 명령을 기록했다. 설치 완료 후 가장 먼저 MATLAB/Simulink 라이선스 및 MEX 컴파일·모델 로드를 확인하고, 그 다음 실제 신호별 온라인 중단 감시를 검증해야만 10분 시험으로 넘어간다. 기존 7개 그래프·28개 참조 간선 및 원본 자료는 변경하지 않았다.

이번 코드 검사: 기존 연구 가상환경에서 `python -X utf8 -m unittest discover -s tests -q` 106건 통과. 임시 모의 ZIP으로 해시 불일치 및 기존 경로 덮어쓰기 거부를 검증했다. MATLAB 코드는 MATLAB 부재로 미실행이다.

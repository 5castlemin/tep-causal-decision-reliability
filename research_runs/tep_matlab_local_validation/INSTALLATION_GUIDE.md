# MATLAB/Simulink 설치 및 로컬 검증 안내

공식 [학교 라이선스 개인 PC 안내](https://www.mathworks.com/academia/campus/resources/user-guide.html)에 따라 소속 학교의 MATLAB 캠퍼스 포털을 열고 학교 이메일이 연결된 MathWorks 계정으로 로그인한다. 학교의 MATLAB Individual 라이선스 제공 여부는 이 PC에서 확인되지 않았다. 라이선스가 제공되면 공식 설치 프로그램으로 MATLAB과 Simulink를 선택한다. 다운로드·로그인·라이선스 활성화 및 관리자 권한 요청은 사용자가 직접 진행한다. 비공식 파일과 인증 우회는 사용하지 않는다.

공식 TEP archive는 R2014b에서 시험했다고 기술한다. 이것이 최신 Windows에서 해당 버전을 설치하거나 라이선스를 사용할 수 있다는 뜻은 아니다. 학교가 제공하는 버전과 MathWorks의 해당 버전용 [Windows 지원 컴파일러 목록](https://www.mathworks.com/support/requirements/supported-compilers.html)을 확인하고, 해당 릴리스와 호환되는 C 컴파일러를 선택한다. MinGW 또는 Visual C++가 지원되는지는 **설치한 MATLAB 릴리스 기준**으로 확인한다. 설치 후 MATLAB에서 다음을 실행한다.

```matlab
version
ver
license('test','Simulink')
mex -setup c
```

공식 ZIP은 이미 `archive_manufacturing`에 있으나 원본을 직접 수정하지 않는다. 별도의 새로운 폴더에 파일을 준비할 경우 저장소 루트에서 다음을 실행한다. 이미 존재하는 대상 폴더는 거부한다.

```powershell
python -X utf8 research_runs/tep_matlab_local_validation/prepare_official_source.py --archive "<temexd_mod.zip 경로>" --destination "<새 빈 작업 폴더 경로>"
```

현재 작업에서 이미 `data/local/tep_matlab_local_validation/staged_20261029/`에 검증된 사본이 준비돼 있으므로 다시 만들 필요가 없다. 해당 폴더와 별도의 새 출력 폴더를 사용할 수 있다. MATLAB 작업 디렉터리를 저장소 루트로 맞춘 후:

```matlab
addpath(fullfile(pwd,'research_runs','tep_matlab_local_validation'))
model_dir = fullfile(pwd,'data','local','tep_matlab_local_validation','staged_20261029');
out_dir = fullfile(pwd,'data','local','tep_matlab_local_validation','preflight');
if exist(out_dir,'dir') ~= 7, mkdir(out_dir); end
tep_official_preflight(model_dir,out_dir)
```

이 명령은 라이선스와 선택된 컴파일러를 확인하고 **별도 복사본**에서 MEX 빌드와 모델 로드만 시도한다. MATLAB이 없는 현재 PC에서 코드를 실행하지 못했으므로 버전별 호환성은 미검증이다. 최초 실행 실패 시 로그를 보존한다. 공식 archive의 Windows용 오래된 prebuilt MEX는 복사하거나 실행하지 않는다.

`tep_official_run.m`은 현재 **의도적으로 실행을 차단하는 초안**이다. 모델이 실제로 내보내는 측정·명령·내부 상태 신호를 runtime에서 식별하고, 해당 값의 제약 초과·비유한값·종료 시 적분 중 즉시 중단하는 감시기를 검증해야 실행을 허용할 수 있다. `StopFcn=TEplot`, `PreLoadFcn=Mode_1_Init`, 저장 주기 0.01시간 및 자동 로드되는 초기값도 확인해야 한다. 현재 10분 시뮬레이션·CSV 생성까지 즉시 실행 가능한 검증된 프로그램은 제공하지 못한다.

실제 출력에 `time_hours`와 기존 X 열을 정당하게 대응시킨 후 `compare_official.py --benchmark <datasetTE.csv> --simulation <출력 CSV> --output <새 결과 폴더>`로 기술 통계를 생성할 수 있다. 이 코드는 대응 및 시간·전처리의 타당성을 자동 인증하지 않는다. 원본과 유사한 숫자만으로 동일환경이라고 판정하지 않는다.

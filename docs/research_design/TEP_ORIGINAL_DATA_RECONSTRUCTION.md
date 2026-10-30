# Manca 원본 데이터 복원

2026-10-30. 단계 판정은 **ORIGINAL_DATA_ACCESS_BLOCKED**다. 현재 archive_manufacturing과 Downloads 등 확인 범위에서 정상 원본 ZIP·SIMOUT/XMV/TOUT를 찾지 못했다. 기술보고서 V1_2 PDF는 로컬에 있다. 전 PC에서 파일 부재를 증명한 것은 아니다.

## 실제 접근 및 확보

공식 IEEE DataPort 페이지 https://ieee-dataport.org/open-access/tennessee-eastman-process-alarm-management-dataset (DOI 10.21227/326k-qr90)를 로컬 HTTP로 실제 내려받아 HTTP200·66144바이트 페이지를 읽었다. 목록에 `3_Normal Steady-State_zip`을 확인했고 사이트는 데이터 다운로드에 로그인이 필요하다고 명시했다. 정상 ZIP과 그 내부 엑셀 파일은 확보하지 못했다. 로그인 우회는 하지 않았다. 브라우저는 계정 생성 페이지가 열린 것으로 확인됐으며 인증 과정은 사용자에게 맡겼다. 원본 ZIP을 내려받은 경로를 알려달라는 요청을 전달했다.

CPCaD-Bench를 공개 upstream commit `72b0f5e3d14192478186ee0dc4338b7448087789`에서 받아 가공된 CSV와 텍스트를 실제 대조했다. 현재 CSV와 upstream CSV SHA-256은 모두 `52ae445b4355201db9591822282381c8de861afe49bdbc9452db08b01e7d3711`로 **바이트 일치**한다. NumPy 텍스트도1499×31이며 최대값 차이 약9.1e-13이다. 이 저장소의 조사 범위에서 전처리 실행 코드는 없었다. 이는 가공 자료의 전달 계보를 확인한 결과이며 Manca 원본으로부터 재생성한 것은 아니다.

33→31 축소의 원인, X27/X31의 제거 전 분산, 3분 중앙값의 방향·stride·경계·시작시간, 1500→1499의 실제 변환은 미확정이다. 논문 설명을 특정 원시 파일에서 실행한 코드와 동등하게 취급하지 않는다. 원본 없이 이를 추정 최적화하는 전처리 코드는 작성하지 않았다. `verify_upstream.py`는 현재 파일과 공개 가공 파일의 동일성만 재계산하며 `RECOVERY_RESULT.json`에 범위와 해시를 기록한다.

## 필요한 사용자 조치

공식 IEEE 페이지에 직접 로그인한 뒤 정상 운전 ZIP을 다운로드하고 로컬 저장 경로를 제공하면 된다. 로그인 정보는 전달하거나 저장할 필요가 없다. 이후 실제 압축 내용·시간·seed·model flags를 확인하고 전처리 계약을 고정한 후 재생성 가능성을 평가한다. 현 단계에서는 원본 재생성·새75시간 운전·개입 파일럿을 실행하지 않았다.

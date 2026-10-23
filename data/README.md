# 로컬 입력 데이터

정상 데이터 `datasetTE.csv`와 원본 `TEGroundTruth.txt`는 `src/prepare_local_inputs.py`가 지정된 CPCaD-Bench Git 커밋에서 읽어 SHA-256을 검증한 뒤 `data/local/`에 쓴다. 이 폴더는 Git에서 제외한다. 필요한 경로와 해시는 `docs/audit/ARTIFACT_INVENTORY.md`를 참고한다. GT는 구조 비교 참조이며 시뮬레이터 조작 효과의 절대 정답이 아니다.

두 입력만 독립적으로 준비하려면 `python -X utf8 src/acquire_reference_data.py --source-git <CPCaD-Bench Git 경로>`를 실행한다. 소스 commit과 SHA-256이 코드에 고정되어 있으며, 기존 파일 내용이 다르면 덮어쓰지 않고 실패한다. 원본 README의 인용 요청만으로 재배포 허가를 추정하지 않으므로 `data/reference/`에 원본 바이트를 추적하지 않는다.

# 로컬 입력 데이터

정상 데이터 `datasetTE.csv`와 원본 `TEGroundTruth.txt`는 `src/prepare_local_inputs.py`가 지정된 CPCaD-Bench Git 커밋에서 읽어 SHA-256을 검증한 뒤 `data/local/`에 쓴다. 이 폴더는 Git에서 제외한다. 필요한 경로와 해시는 `docs/audit/ARTIFACT_INVENTORY.md`를 참고한다. GT는 구조 비교 참조이며 시뮬레이터 조작 효과의 절대 정답이 아니다.

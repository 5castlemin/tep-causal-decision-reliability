# 검증 기록

기준 main은 `7742180cef09b506e3d26e56d58a03b3d6a4e37d`이며 GitHub API에서 PR #39 merged 및 merge SHA 일치를 직접 확인했다.

| 검증 | 결과 |
|---|---|
| 핀된 원자료와 참조 | 9개 챔버의 공식 MD5 일치, ESS reduced 게시 MD5와 ZIP CRC 일치, PyPI wheel 게시 SHA-256 일치. 개별 SHA-256과 bytes는 [manifest](dataset_manifest.json). |
| 오프라인 검사 재실행 | `python -X utf8 research/external_validation/inspect_support.py --data <external> --catalog <pinned-catalog> --output <recheck>` 통과. 저장된 JSON과 재실행 SHA-256 모두 `64b6ec4a1d278cab4d76ef979b4f13fb9469f4284723ca9312447011306d3d28`. |
| 신규 테스트 | `python -X utf8 -m unittest discover -s tests -p test_external_validation_support.py -v` 5개 통과. SHA 검증, strict·cycle 판정, Mk2 경로, 블록/행 구분, 배정과 평가값 경계. |
| 첫 로컬 전체 검증 | `.github/workflows/verify.yml`의 Python 작업을 Windows 3.11.15에서 실행. 당시 checkout은 `core.autocrlf=true`와 작업 중 파일을 포함했다. 그래프·자산 해시 검사 등 4개 validator 실패. unittest 361개 중 1 failure(과거 원시 바이트 hash), 1 error(clean worktree guard). exact-head clean 검증과 구분한다. |
| 동결 자료 | 감사와 live 상태 4파일 및 신규 테스트만 변경 경로로 허용했다. 기존 Research C/Step 4 manifests, ledger, 코드, 요구사항 및 과거 상태 문서는 base Git tree와 대조한다. |

기존 CI의 checkout, Python 3.11 및 freeze guard는 그대로 사용한다. GitHub 브랜치의 exact-head 검증 상태는 [Actions 실행 목록](https://github.com/5castlemin/tep-causal-decision-reliability/actions/workflows/verify.yml?query=branch%3Aresearch%2Fresearch-d-external-validation-feasibility)에서 확인할 수 있다.

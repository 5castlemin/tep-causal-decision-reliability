# 협업 안내

`main`에는 검증된 개발 상태만 둔다. 새 작업은 `feature/<주제>`, `repair/<주제>` 또는 `docs/<주제>` 브랜치에서 작성하고, 소유자가 생성하는 Pull Request에 목적, 원본 해시, 실행 명령, 통과·실패 결과, 연구 해석의 한계를 기록한다. 현재 기본 개발·연구 승인자는 저장소 운영자이며, PR마다 아래 Self-Review를 수행한 뒤 운영자의 명시적 병합 결정에 따라 병합한다. 협업 형태가 바뀌면 리뷰 정책을 다시 결정한다.

현재 연구 상태를 실제로 바꾸는 작업은 `docs/research_state_current.json`을 갱신하고 `python -X utf8 scripts/check_research_state.py --write`를 실행해 `docs/current/PROJECT_STATUS_CURRENT.md`와 `docs/current/PRIORITIES_CURRENT.md`를 생성한다. 새로운 연구 작업 기록은 `docs/current/WORK_LOG_CURRENT.md`에 남긴다. 과거 Step 4 Manifest에 고정된 루트 `PROJECT_STATUS.md`, `PRIORITIES.md`, `WORK_LOG.md`, `docs/research_state.json`, `requirements.txt`는 절대 수정하지 않는다. PR CI의 상태 검사도 현재 문서와 현재 상태 원본을 확인한다. 파일 존재나 검사 통과만으로 연구 결과의 진실성이 보증되지는 않는다.

## Solo Research Self-Review

PR마다 (1) 변경 목표, (2) 전체 diff와 영향 파일, (3) 기존 연구 계약, (4) 테스트와 최종 HEAD의 CI, (5) 동결 데이터·원시 결과 무결성, (6) 연구 상태와 문서 기록, (7) 미해결 위험과 제한 사항을 확인한다. 실제 수행한 검사와 미수행 항목을 구분해 PR Conversation 댓글 또는 검토 보고서에 기록한다. 그 다음 운영자가 병합 여부를 명시적으로 결정한다. 검토하지 않은 항목은 완료로 표시하지 않는다.

Self-Review는 GitHub의 공식 승인으로 위장하지 않는다. PR 작성자 자신의 가짜 APPROVE, 타 계정 승인 가장, 필수 보호 규칙 우회는 금지한다. 플랫폼이 외부 승인을 요구하면 충족 전 병합하지 않는다.

일반 CI는 Python 3.11과 `requirements.txt` 및 `requirements-research-c-ci.txt`를 함께 설치한다. 이는 승인된 Windows Held-out 실행 환경을 동일하게 재현했다는 뜻이 아니다. 새 코드가 필요할 때는 작은 함수와 실제 오류를 잡는 검증을 우선한다. 인과발견 최종 그래프와 동결 설정을 수정하면 기존 파일을 덮어쓰지 않고 새 버전·근거·변경 이력을 남긴다. 평가 GT로 미확정 방향을 정하거나 과제를 결과에 맞춰 바꾸지 않는다.

현재 GitHub 저장소는 Public이다. 공개 범위 변경은 소유자가 별도로 결정한다. 대용량 원자료, 개인 경로, 자격 증명, `.env`, 캐시, 실험 임시 결과는 커밋하지 않는다. 공유 산출물에는 입력 해시, 소프트웨어 버전, 난수 시드, 목표 행과 분할, 실패 상태를 남긴다. 수치가 없는 단계는 `미수행/차단`으로 표시한다. GitHub PR에서는 우선 `python -X utf8 src/verify_recovery.py`와 `python -X utf8 -m unittest discover -s tests -v`가 통과하는지 확인한다.

## 개발 통합과 연구 완료

`main`은 현재 연구의 검증된 개발 통합 기준이다. main 병합만으로 연구 가설이 확인되거나 Step4–9가 완료된 것은 아니다. 다음 단계는 최신 main에서 짧은 `feature/step4-...`, `feature/step5-...` 등의 브랜치를 만들고 CI와 Self-Review 후 명시적 결정으로 병합한다. 이전 연구와 실패·보류 증거는 attic 보관 인덱스 및 태그로 추적한다. 활성 또는 열린 PR의 head/base 브랜치는 임의로 삭제하지 않는다.

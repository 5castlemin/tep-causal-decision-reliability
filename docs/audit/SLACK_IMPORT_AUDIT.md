# Slack 자산 반입 감사 — 최신 상태

2026-10-23. 이전 감사는 `docs/history/SLACK_IMPORT_AUDIT_before_asset_recovery.md`에 보존했다.

- 실제 Slack 원본 바이트 회수: Step 6 ZIP `F0C6TP4168H`와 과제 ZIP `F0C7E97KXEC` 2개. 각각 기존 로컬 SHA와 exact 일치했다. 원본은 저장소 밖 작업 폴더에 보존했다. signed transport URL은 커밋하지 않았다.
- Git에 원본 ZIP/CSV/알고리즘 코드를 추가하지 않았다. 데이터·원본 코드 재배포 권리 UNKNOWN이므로 해시 고정 입력 경로 및 새 평가 adapter만 통합했다.
- Step 6 ZIP의 원본 평가기 bytes/hash를 확인하고 strict 3지표×7개 Final 결과를 새 환경에서도 재현했다. 기존 단순 점수 독립 계산과 구분되는 원본 평가 함수 실행이다. 전체 공통 평가 pipeline은 누락된 common/config 및 Initial/sensitivity 파일 때문에 재현했다고 주장하지 않는다.
- 데이터·GT는 공개 저장소 새 clone/새 venv/빈 destination으로 취득하여 해시·shape·변수 순서를 검증했다. 개인 경로나 이전 로컬 clone에 의존하지 않았다.
- Final 생성 `algos/run_*.py`는 여전히 미회수. 기대 hash는 `docs/reproducibility/MISSING_FINAL_SOURCES.json`. 과거 PCMCI+ local baseline은 Final 생성 코드로 반입하지 않았다.
- PC/BOSS Colab 정확 링크는 확보했지만 export 요청이 로그인 HTML을 반환했다. notebook 다운로드로 표시하지 않는다. Track A/B 및 담당B 설명 본문은 읽었으나 Slack 원본 바이트와 로컬 문서의 동일성은 입증하지 못했다.
- 수준별 근거·회수 요청·실행 명령·라이선스 한계는 `docs/reproducibility/ASSET_RECOVERY_REPORT.md`, 팀 절차는 `TEAM_GUIDE.md`를 따른다.

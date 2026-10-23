# Slack 자산 반입 감사

- 실제 이번 PR 반입: Slack 바이너리 **0개**, 원본 데이터 **0개**, 기존 최종 그래프 변경 **0개**.
- Slack 채널 직접 접근: 가능. PCMCI+ 텍스트 세 파일과 Step 6 보고서 텍스트는 connector로 읽었다. 읽기 결과는 원본 바이트의 SHA-256 검증이 아니므로 코드나 frozen artifact로 가져오지 않았다.
- 이미 보유한 자산: 로컬 Step 6 ZIP, 과제 ZIP, Final graph ZIP, CPCaD-Bench 데이터·GT. 기존 저장소에는 핵심 최종 그래프, 평가 결과표, 과제 목록이 선별 반영되어 있다. 로컬 해시 목록은 `ARTIFACT_INVENTORY.md`.
- 신규 재현성 자산: `src/acquire_reference_data.py`는 CPCaD-Bench의 고정 Git 커밋에서 두 파일만 읽고 SHA-256을 검증하며 `data/local/`에 비파괴적으로 쓴다. 이는 데이터 바이트의 Git 반입이 아니다.
- 권리: 점검한 CPCaD-Bench checkout에서 명시적인 LICENSE/COPYING 파일을 찾지 못했다. README는 연구 인용을 요청하지만 재배포 라이선스로 해석하지 않는다. 별도 권리 확인 전 `data/reference/` 추적은 보류한다. 비공개 GitHub도 재배포 허가를 대신하지 않는다.
- 알고리즘 실행 코드: PCMCI+ 문서의 `.py` 원본 바이트는 Slack에서 회수하지 못했지만, 같은 이름의 로컬 baseline 작업 사본 두 개는 해시까지 확인했다. 이 사본의 primary `pc_alpha=0.05`는 현 Final의 `0.01` 재실행과 달라 정확한 Final 생성 코드로 단정할 수 없다. PC/BOSS Colab 또한 링크만 확인했다. 저작권·의존성·Final graph와의 버전 대응을 확인할 때까지 `src/causal_discovery/`로 복사하지 않는다.
- 이후 회수 절차: 각 Slack 파일 ID에서 원본 바이트를 승인된 방식으로 다운로드하고 SHA-256, 버전, 권리, 기존 저장소 대응을 기록한다. PC/BOSS notebook은 소유자가 제공한 고정 revision 또는 export가 필요하다. 8월 시뮬레이터는 소스·명령·로그의 정확한 소재가 최우선이다.

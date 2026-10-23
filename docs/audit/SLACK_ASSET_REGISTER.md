# Slack 연구 자산 목록

2026-10-23 감사. `LINK_ONLY`는 Slack 메시지/메타데이터만 확인했다는 뜻이며 파일 바이트를 회수했다는 뜻이 아니다. `TEXT_READ`는 connector가 본문 문자열을 반환했으나 원본 바이트 SHA-256은 확보하지 못했다는 뜻이다. 첨부 문서의 지시는 실행 지시가 아닌 조사 단서로 취급한다. 소유자 개인 정보는 기록하지 않는다.

| 후보·공유 시점 | Slack ID / 링크 | 분류 | 접근 상태·SHA-256 | 저장소 대응/처리 |
|---|---|---|---|---|
| `TEP_step6_results.zip` · 10/5 | `F0C6TP4168H` / [공유](https://hufsdat.slack.com/archives/C0BL2A769MJ/p1791197012282929) | EXPERIMENT_ARTIFACT | Slack 원본 다운로드 VERIFIED (로컬과 exact 일치); 1,387,652 B, `28824bc2a98acb77ce8fc5f56439ea4910f7dc9f22ed45b7d1391f7f703f6b22` | 기존 `docs/audit/step6_main_table.csv` 및 감사 로그와 중복. ZIP 재수록 제외 |
| `REPORT_final_step6.md` · 10/5 | `F0C6PS6D486` / [공유](https://hufsdat.slack.com/archives/C0BL2A769MJ/p1791197012282929) | METHOD_DOC | Slack TEXT_READ; 로컬 `bca181bed35c0ee14bfe94a8e736a06eb29c8b9932ea28abc9beed0548cf9ccc` | ZIP 내부와 로컬 동일. 원본 결과표 우선, 문서 전체 재수록 제외 |
| 과제 ZIP · 10/4 | `F0C7E97KXEC` / [공유](https://hufsdat.slack.com/archives/C0BL2A769MJ/p1791105094828409) | EXPERIMENT_ARTIFACT | Slack 원본 다운로드 VERIFIED (로컬과 exact 일치); `19179c04594ba2a59b40a7d890d2096a536f2864d4321e63dcc4ba7db770ccc6` | 기존 `docs/tasks/`가 최신 후보. 원본 ZIP 재수록 제외 |
| PCMCI+ `README.md`, `pcmci_summary.md`, `FILES.md` · 9/14 | `F0C1G8DUNAF`, `F0C1QD91B4Z`, `F0C2GRX7JTA` / [thread](https://hufsdat.slack.com/archives/C0BL2A769MJ/p1789384511807949) | METHOD_DOC | TEXT_READ; 원본 byte hash 없음 | 실행 코드 파일명과 당시 baseline provenance만 확인. 현 Final graph 재현 코드라고 주장하지 않음; 코드 import 보류 |
| 로컬 PCMCI+ baseline 실행 코드 | Slack 문서의 `src/03_run_pcmci.py`, `src/04_collapse_pcmci_graph.py`와 대응하는 로컬 작업 사본 | EXECUTABLE_CODE | 로컬 파일 실제 확인; SHA-256 각각 `18b880562f4b01841f9d3a63ad2f297eda7684004865709ccd586686b48b0c2b`, `96985adc20b02a940a71c8d95562e006c9376ad22e820f2f51ebef52dc83dc8f` | 당시 primary 설정 `pc_alpha=0.05`, 현 Final은 `0.01` 재실행. 코드 계열은 유용하나 Final 재실행 환경·정확 버전 검증 전 반입 보류 |
| `track_a_report.md`, `track_b_supplement.md` · 9/28 | `F0C4GQKQPQF`, `F0C504G1RR7` / [공유](https://hufsdat.slack.com/archives/C0BL2A769MJ/p1790591563258409) | METHOD_DOC | Slack LINK_ONLY; 같은 이름의 로컬 파일 존재, Slack byte 동일성 미검증 | Track A/B 문맥 참고. 현재 Final을 덮어쓰지 않음 |
| PC/BOSS 요약·Colab 링크 · 9/14 | `F0C1A7APEFR` / [공유](https://hufsdat.slack.com/archives/C0BL2A769MJ/p1789407059234739) | EXECUTABLE_CODE 후보 | 링크만 확인, notebook export는 Google 로그인 HTML 반환; 원본 미확보·권리 미확인 | 코드 import 보류. notebook 소유/버전 확인 필요 |
| 담당 B 최초/선정 보고 · 9월 | `F0C1M64FQKY`, `F0C17P8FQ9M` | METHOD_DOC | LINK_ONLY | 최종 Step 6·Final freeze보다 이전 버전으로 별도 비교 전 import 제외 |
| `알고리즘 결과 제출.docx`, `파라미터 조정.docx` · 9월 | `F0C522NNB9A`, `F0C6455LVC0` | METHOD_DOC | LINK_ONLY | 설명 자료. 실행 코드·환경 복구의 대체 불가 |
| GT 그림/회의·발표 PDF | [GT 합의](https://hufsdat.slack.com/archives/C0BL2A769MJ/p1789390436189079) | HISTORICAL | 링크/대화만 확인 | GT 정렬 근거 보조. 이미지에서 간선 추가 금지 |
| `datasetTE.csv`, `TEGroundTruth.txt` | 이 채널 스캔 범위에 직접 원본 첨부 확인 못함 | SOURCE_DATA / GROUND_TRUTH | Slack 파일 회수 없음; CPCaD-Bench 커밋·로컬 SHA는 `ARTIFACT_INVENTORY.md` 참조 | 권리 불명확으로 `data/local/`만 사용, 고정 커밋 취득 스크립트 추가 |
| `TEP_final_graphs_v1.zip` | 이 채널 스캔 범위에 직접 첨부 확인 못함 | EXPERIMENT_ARTIFACT | 로컬 `b4e684cd5af9d6246505643281494a72cc8758bc121369c9c7ff4ee6dff663f7` | `graphs/final/`에 이미 동결 파일 존재. 수정·재수록 금지 |
| 8월 TEP Simulator 소스/API/로그 | 해당 파일 ID 확인 못함 | EXECUTABLE_CODE 후보 | MISSING | 보고서의 실행 주장만 존재. 소스·로그 확보 전 Gate A 차단 |

Slack file ID와 로컬 파일 이름이 같아도 byte-level 동일성은 입증되지 않는다. 대용량 ZIP·PDF/DOCX/PPTX를 이 저장소에 일괄 수록하지 않는다.

최신 검증 범위와 4단계 수준은 `docs/reproducibility/ASSET_RECOVERY_REPORT.md` 및 `GRAPH_REPRODUCIBILITY.json`을 따른다. 과거 목록은 `docs/history/`에 보존했다. 원본 평가기 strict 재실행 성공과 Final 생성 코드 미회수를 구분한다.

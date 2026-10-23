# 원본 산출물 목록

확인일: 2026-10-23. 이 문서의 `%USERPROFILE%`은 조사한 Windows 계정의 사용자 폴더를 뜻한다. 공개 저장소에 개인 홈 디렉터리 이름을 기록하지 않기 위해 경로를 이 표기로 정규화했다. 원본은 읽기 전용으로 취급하며 새 저장소에 중복 ZIP을 복사하지 않는다.

| 원본 경로 | 용도와 최종본 판정 | 크기 / SHA-256 | 재현 또는 확인 명령 | 주의 |
|---|---|---|---|---|
| `%USERPROFILE%/Downloads/TEP_final_graphs_v1.zip` | 7개 최종 그래프. 내부 `FREEZE.json`·`MANIFEST.csv` 및 `stage=Final`로 최종본 판정 | 77,766 B / `b4e684cd5af9d6246505643281494a72cc8758bc121369c9c7ff4ee6dff663f7` | `python -X utf8 graphs/final/verify_and_load.py` | 시계열 정적 투영과 원래 시차 구조 구분. 포함된 `__pycache__`는 이관하지 않음. |
| `%USERPROFILE%/Downloads/TEP_step6_results.zip` | 공통 구조 평가 코드·결과 묶음 | 1,387,652 B / `28824bc2a98acb77ce8fc5f56439ea4910f7dc9f22ed45b7d1391f7f703f6b22` | `python src/verify_recovery.py`의 수치 대조 | Final graph의 `FREEZE.json`과 동결 해시가 같음. 무작위 기준선 재실행은 별도. |
| `%USERPROFILE%/Downloads/REPORT_final_step6.md` | Step 6 최종 보고서. 위 ZIP 내부 보고서와 동일 | 25,673 B / `bca181bed35c0ee14bfe94a8e736a06eb29c8b9932ea28abc9beed0548cf9ccc` | ZIP 내부 문서와 해시 비교 | 문서 해석은 실행 결과 CSV보다 후순위. |
| `%USERPROFILE%/Downloads/tep_task_relevant_work_2026-10-04_181036.zip` | 초기 과제 묶음. 이후 12개 후보 선정의 출발점 | 73,669 B / `19179c04594ba2a59b40a7d890d2096a536f2864d4321e63dcc4ba7db770ccc6` | 기존 `pre_scm_audit` 문서 참고 | 과거 PCMCI+ 그래프는 현재 Final과 다름. |
| `%USERPROFILE%/OneDrive/바탕 화면/닦고조이고기름치자/CPCaD-Bench/TenneseeEastman/datasetTE.csv` | 정상 운전 입력. 공개 CPCaD-Bench 파일과 바이트 동일하다는 기존 출처 감사 기록 | 661,664 B / `52ae445b4355201db9591822282381c8de861afe49bdbc9452db08b01e7d3711` | `python src/verify_recovery.py` | 1,499행×31 분석변수. 무명 인덱스 열은 제외. 원자료 시각과 행별 대응은 미검증. 대용량 데이터는 커밋하지 않음. |
| `%USERPROFILE%/OneDrive/바탕 화면/닦고조이고기름치자/CPCaD-Bench/TenneseeEastman/TEGroundTruth.txt` | 33×33 원본 GT | 2,211 B / `238542dbdde50887b5944fb3acc64a792b19a0c56bbfa06e3b267261f2fe6c43` | `python src/verify_recovery.py` | X27·X31 제외 뒤 31×31, 간선 28개. 구조 참조이지 개입 효과 정답이 아님. |
| `pre_scm_audit/PRE_SCM_MANIFEST.json` | 변수·그래프·과제 정합성 감사 | SHA는 `pre_fitting_final_freeze.json`에 기록 | 기존 검증기 참조 | 7개 그래프 31변수 정렬 PASS WITH WARNINGS. |
| `pre_scm_task_selection_v1_1/task_selection_freeze_v1_1.json` | 198→65→12 구조 평가 후보 고정 | SHA는 최종 학습 freeze에 기록 | 기존 검증기 참조 | 12개는 사람이 대표성을 고려해 선정 후 코드 검증; 독립 12표본이 아님. |
| `pre_scm_final_freeze/pre_fitting_final_freeze.json` | 학습 전 조건 고정 | 2026-10-06 생성 | `python src/verify_recovery.py` | 학습 설계의 통과가 실제 SCM 적합 완료를 뜻하지 않음. |
| `%USERPROFILE%/Downloads/3주차 방학스터디 최종 보고서_조이고닦고기름치자.pdf` | 8월 시뮬레이터 소스 확보·파이썬 연동 기초 테스트에 관한 **보고** | 129,644 B / `b1ca5dbe00c5b2ecb6ff68538df46ff2cb9a53ff721e90ec312f160d5a17dac3` | PDF 4쪽 원문 확인 | 실행 코드·명령·로그·버전이 함께 보관되어 있지 않아 현재 재현은 미확인. |
| `%USERPROFILE%/Downloads/TEP_Codex/introduction.md` | 팀 소개 초안 | 8,319 B / `2a3a1e41b6b66a310b9c02d5653ba8b3300209e18ad9f99b6ada349e2e6cf6b2` | 현재 저장소 소개문과 대조 | 실제 완료와 제안을 구분하여 개정. |

원본 CPCaD-Bench Git 상태는 `main...origin/main`, 미커밋 변경 없음이며 원격은 `https://github.com/giovanniMen/CPCaD-Bench.git`이다. 로컬 최신 커밋 `72b0f5e3d14192478186ee0dc4338b7448087789`(2022-11-02)로 확인했다. 원본 저장소를 수정하지 않았다.

## 2026-10-23 Slack 교차 확인

Slack 메시지에 Step 6 ZIP(`F0C6TP4168H`), 과제 ZIP(`F0C7E97KXEC`), PCMCI+ 실행 설명 3개가 공유된 사실을 확인했다. ZIP의 Slack 원본 바이트는 다운로드하지 않았으므로 위 로컬 ZIP과 *Slack 첨부 자체*의 해시 동일성은 아직 미검증이다. 기존 Final graph, Step 6 표, 과제 freeze는 수정하지 않았다. 상세 상태는 `SLACK_ASSET_REGISTER.md`와 `SLACK_IMPORT_AUDIT.md`에 기록했다.

공개 CPCaD-Bench checkout에서 LICENSE/COPYING 파일을 찾지 못했고 README의 인용 요청만 확인했다. 따라서 데이터·GT 원본은 계속 `data/local/`에서만 사용한다. `src/acquire_reference_data.py`가 고정 커밋과 두 SHA-256을 검증하며 재배포 권리 확인 후에만 추적 저장을 재검토한다.

## 자산 복원 추가 검증 — 2026-10-23

Slack Step 6/과제 ZIP의 원본 바이트를 회수하여 위 로컬 SHA와 exact 일치를 확인했다. 새 공개 clone·빈 환경 데이터 취득 및 회수한 원본 strict 평가기 실행 결과는 `docs/reproducibility/validation/`에 있다. ZIP 내부 파일 hash는 `STEP6_ARCHIVE_CONTENTS.json`에 보존한다. 생성 코드의 기대 hash는 존재하지만 bytes 미회수인 상태를 `MISSING_FINAL_SOURCES.json`에 명시했다. 원본 ZIP/코드/CSV 바이트는 이 저장소에 새로 반입하지 않았다.

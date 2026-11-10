# 저장소 정리 감사 — 2026-11-10

## 조사 기준 및 현재 범위

병합 전 원격 main `cdb2c7d6dc499937929ca496ca840b07fb500701`, 최신 연구의 변경 전 HEAD `ba35db68c573fd35a21edb42b1bbde354bedf0d8`. 원격 38개 브랜치·열린 PR 11개·기병합 PR 25개였다. #36은 main 대상이고 #26은 독립, #27–35는 순차적 TEP 적층이다. 상세 분류·각 SHA·ahead/behind·PR 관계: [보관 manifest](https://github.com/5castlemin/tep-causal-decision-reliability/blob/attic/legacy-research-2026-11-10/LEGACY_BRANCH_MANIFEST.json), [PR manifest](https://github.com/5castlemin/tep-causal-decision-reliability/blob/attic/legacy-research-2026-11-10/LEGACY_PR_MANIFEST.md). `feature/pr2-pr3-integration`은 여러 merge base를 가지므로 diff 파일 집합은 단일 자동 결과로 확정할 수 없다.

분류: ACTIVE 2개(main, 최신 연구), MERGED_LEGACY 25개, REVIEW_REQUIRED 11개(열린 PR head 10개 및 PR 없는 통합 브랜치). 열린 연구가 비활성·팀 미사용이라는 증거는 확보되지 않았다. UNMERGED_ARCHIVE로 일방 분류하지 않았다. 열린 PR #26–35를 닫거나 브랜치를 지우지 않았다.

## 보관 및 복구

병합 전 원격 main에 기반해 `attic/legacy-research-2026-11-10`을 만들고 최신 commit `b868fa371dee38b9fea7ee9675900633e9490ecd` (최초 인덱스 `24a307c4a18d0ee5995beeadd9bf1b2c5833240e`)를 원격에 푸시해 조회했다. 기존 38개 각 브랜치 HEAD에 `attic/2026-11-10/<원래 브랜치명>` annotated tag를 생성하고 원격 `^{}`가 원래 SHA와 모두 일치함을 확인했다. 현재 39개 브랜치(보관 브랜치 추가), 열린 PR 11개다. [복구 절차](https://github.com/5castlemin/tep-causal-decision-reliability/blob/attic/legacy-research-2026-11-10/RECOVERY_GUIDE.md). 로컬 무시 데이터나 외부 패키지는 Git 태그에 포함되지 않는다.

## 검증과 남은 gate

기존 39개 동결 파일 해시·변수 순서와 시계열 재변환, 자산 manifest 및 연구 상태 검사를 통과했다. 151개 단위검사 통과. 보관 및 명칭 정리는 연구 성공 판정이 아니다. PR #36 개발 통합은 현재 제안 상태이며, `CONTRIBUTING.md`의 최소 1명 검토와 최신 HEAD의 CI 검증을 충족한 뒤에만 진행한다. 사용자 지시의 main 승격은 연구 완료가 아니며 Step4 IN_PROGRESS, Step5–7 미실행, Step8 BLOCKED다.

최종 main 병합 SHA·병합 후 CI·삭제 목록은 실제 실행 전이므로 아직 없다. 병합 전 정리의 일부 결과만 기록했으며, 이후 새 원격 상태를 다시 조회해야 한다.

문서 변경 중 기존 RESEARCH_DESIGN.md에 안내 문구를 추가했을 때 세 동결 실험 검사가 문서 변경을 탐지해 실패했다. 해당 문서를 원복하고 전체 151개 검사가 통과했다. 보호 규칙이나 원시 결과는 변경하지 않았다.

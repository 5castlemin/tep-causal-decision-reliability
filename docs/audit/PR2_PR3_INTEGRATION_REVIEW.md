> 이 문서는 승인 전 사전검토 이력이다. 승인 후 진행은 `PR2_PR3_APPROVED_INTEGRATION.md`와 GitHub PR 상태를 참조한다.

# PR #2·#3 통합 사전 검토 — 2026-10-23

**판정: 임시 통합 검증 통과. main 통합은 미실행이며 사용자 승인 대기.**

## 확인한 원격 상태

| 대상 | 상태 | 최신 commit | CI |
|---|---|---|---|
| main | PR #1 병합 이후 | ceb447deb03f5532dc274cb97de2cd7f317349e7 | 이번 작업에서 직접 변경 안 함 |
| PR #2 | open, unmerged | e5a0291e48d5426628c0dde8a122fe8ab6b6e195 | 39924152760 success |
| PR #3 | open, unmerged | b2e455fd37d1e236aa30fe246e4944142bef4bab | 39927575613 success |

작업 시작 시 로컬 미커밋 변경 없음. 원격 fetch 후 두 PR source ref를 기준으로 검토했다. 타인 변경을 강제 덮어쓰지 않았고 기존 PR branch를 수정·종료하지 않았다.

## 검토한 변경 범위

PR #2는 38파일(시뮬레이터 실행 코드·plan·CSV·schema/hash·실패 로그·감사/상태·CI), PR #3은 28파일(자산 회수 adapter·검증 JSON·재현 guide·상태 JSON/생성기·문서·CI)이다. 각 PR과 main의 변경 파일 목록을 대조했다. 공통 변경은 다음 4파일이며 실제 merge conflict가 모두 발생했다.

| 파일 | 의미적 해결 |
|---|---|
| PROJECT_STATUS.md | PR #3 생성 구조 채택; JSON에 공개 simulator 실제 PARTIAL 근거를 로컬 summary와 연결하고 main 미병합 표기. GRAPH-GEN BLOCKED 별도 명시 |
| PRIORITIES.md | PR #3 JSON 단일 대기열 유지; SIM-01/02/03/04·COMPAT-01 분리. append 중복 제거 |
| WORK_LOG.md | 공통 base 기록 1회 + PR #2 추가 기록 전체 + PR #3 추가 기록 전체. 어느 쪽도 삭제하지 않음 |
| .github/workflows/verify.yml | simulator 원시 증거 검사 + state checker + asset checker + 기존 그래프/테스트/doc-sync 검사의 합집합 |

`docs/SIMULATOR_SETUP.md`의 최초 소스 부재 문장을 **8월 원본 구현**에 한정하여 별도 공개 후보 PARTIAL과 충돌하지 않게 했다. simulator 코드·plan·CSV와 frozen 평가 파일은 수정하지 않았다.

## 보존한 현재 연구 상태

- 기존 8월 원본 구현: BLOCKED
- 공개 Python 후보: PARTIAL (30분 반복/관측/쓰기/IDV 확인; shutdown·reset·수치 호환성 한계)
- Final 7개 산출물·strict 구조 평가 재현: VERIFIED
- Final 7개 생성 학습 재실행: BLOCKED (정확한 source 미회수)
- PC/BOSS/DirectLiNGAM 정상 관측 적합: PARTIAL
- 독립 Recovery/Safety 검증: NOT_RUN

## 실제 실행 검사

- `python -X utf8 scripts/validate_pr_integration.py`: 원본 그래프 추적 46파일, simulator 30파일 Git blob 동일; raw CSV 작업 사본도 원본 byte 동일, 양쪽 WORK_LOG 추가 내용 보존.
- `python -X utf8 experiments/simulator/validate_feasibility.py`: CSV hash·반복·시간·실패 한계 검증 PASS. simulator를 새로 가동했다는 뜻 아님.
- `python -X utf8 graphs/final/verify_and_load.py`: 동결 39파일, 변수 순서, 시계열 3개 변환 PASS.
- `python -X utf8 scripts/check_research_state.py`: 상태 JSON/MD·ID·의존성 PASS.
- `python -X utf8 scripts/check_asset_manifest.py`: config·원본 코드 미회수·평가 재현 기록 정합성 PASS.
- `python -X utf8 -m unittest discover -s tests -v`: 8개 PASS.
- `python -X utf8 src/reproduce_step6.py --step6-zip <회수한 원본 ZIP> --output <새 출력>`: 7개 strict 결과 일치. 새 출력은 저장소 밖 `work/asset_recovery/integration_evaluation.json`에 보존.
- README/introduction/팀 guide의 미병합 표기와 완료/미완료 구분 점검. 데이터 취득·원본 evaluator의 실행 경로는 PR #3과 동일하며 이번 통합에서도 위 evaluator 실행으로 확인했다.

문서 비교에서 OS 줄바꿈 차이로 생기는 가짜 불일치를 피하기 위해 일반 파일은 Git blob 기준, simulator raw CSV는 Git blob과 실제 작업 사본 양쪽을 검사한다. 원본 CSV hash 검사를 완화한 것은 아니다.

## 승인 후 순서

1. PR #2 head/CI 변화 여부 재확인 후 병합.
2. PR #3에 최신 main을 반영하고, 여기 검증한 의미적 해결을 적용. 임시 통합 commit을 별도 PR 대신 main에 바로 넣지 않음.
3. JSON의 임시/main 미병합 표기를 실제 병합 상태로 갱신하고 MD 재생성. CI 검사 합집합 유지.
4. 전체 검사와 PR #3 CI 재확인 후 PR #3 병합.
5. main 동기화·원본 hash·상태 검사 후 main에서 다음 simulator 검증 branch 생성.

승인 전에는 `feature/pr2-pr3-integration`이 검토용 기준일 뿐 후속 연구의 main 기준이 아니다. 통합 main 준비 완료/실제 병합 완료라고 보고하지 않는다.

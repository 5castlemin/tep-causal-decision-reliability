# PR #6~#11 승인 순차 통합 기록

2026-10-24 사용자가 #6~#11의 순차 병합만 명시적으로 승인했다. 이 기록과 후속 반복 실험의 변경은 새 `feature/repeated-metric-pilot`에서 관리하며 추가 승인 없이 병합하지 않는다.

| 순서 | PR | 보존한 원래 head | 최종 일반 병합 커밋 |
|---|---|---|---|
| 1 | #6 | 5fe3997d79a8244f4b156d5a335013337833b166 | cdb959cbe7f4685a53e9e47e89869cd25a2d6660 |
| 2 | #7 | 8634e5dce66460dc26441fc40e930c34ebc73af7 | 9d68932fa83ed66bad77d1daff17402495eed880 |
| 3 | #8 | d508ab071f8e153698552ce69225a6eaf17a7150 | 53f893d95da3c753896c75a12576bc9eef4816f0 |
| 4 | #9 | baf03e900a021d3d646779da219fd6bbd0de14ad | 8578fac2c69d0490d4fd2846aeaf8c62be072876 |
| 5 | #10 | ee5e0bd83b78a753bf78d2b72b835fcce8ca2813 | c2d3a5c37a62d5dc28c204d31cf77081d6666bd6 |
| 6 | #11 | 6d37d095998bf45bc532606fe8113fedd1b8f913 | 34b8dbecdc6ecb1d5d850a3d46b0190ed29dc0b2 |

최초 main은 `7b166383d4a5d86cdf73dbbec3b060b0ee0e3a24`, 최종 통합 main은 **`34b8dbecdc6ecb1d5d850a3d46b0190ed29dc0b2`**다. squash/rebase/강제 push 없이 각 원래 head를 두 번째 부모로 갖는 일반 merge commit을 만들었다. 다른 PR은 병합하지 않았다.

## 실제 검사와 병합 절차

각 PR을 최신 main으로 retarget하고, Git의 `origin/main...HEAD` 파일 목록이 원래 선행 head와 해당 head의 차이와 같은지 확인했다. 선행 병합 main의 tree가 선행 원래 head의 tree와 정확히 같은지도 검사했다. 중복 변경·누락·충돌은 없었다. PR의 최신 CI와 mergeable/clean 상태를 읽고, 최신 main의 push CI도 success인지 확인한 뒤 다음 단계로 진행했다. 예상 head SHA를 지정해 GitHub merge API를 호출했다.

각 head에서 해당 시점 workflow의 로컬 검증 명령과 최신 main 기준 문서 동기화 검사, diff 검사를 실제 실행했다. 새 실험용으로 검증된 격리 Python을 명시했으며 외부 TEP/이전 FCM 실험을 재생성하지 않았다. 과거 CSV·잡음·해시·반복 기록을 검증한 것과 실제 외부 시뮬레이션 재실행을 구분했다.

최종 main에서 단위 테스트 31개, 39개 그래프 파일 무결성, 첫 통합 실험 원시 do/noise/모형/추천·손실 검사, 기존 acceptance·자산 manifest·PR 통합·상태 JSON/MD 동기화와 diff 검사를 통과했다. [최종 main Actions](https://github.com/5castlemin/tep-causal-decision-reliability/actions/runs/40093211965)도 success였다. 모든 검사 이후 로컬 main을 fast-forward로 맞추고 후속 브랜치를 생성했다.

## 보존과 상태 해석

최종 main의 전체 tree는 PR #11 원래 head `6d37d09`와 정확히 같다. 기존 TEP 데이터·7개 frozen graph·Step 6·정상 관측 적합·시뮬레이터 원시 CSV·해시·RESEARCH_DESIGN.md는 최초 main 대비 변경되지 않았다. 첫 합성 실험과 이전 MVP/acceptance도 그대로 보존했다.

GitHub는 main을 `protected=false`로 반환했다. private 저장소의 protection/rulesets API는 요금제 기능 제한 HTTP403을 반환했다. 공개 전환·보호 해제·관리자 우회·필수 승인의 우회는 수행하지 않았다. 사용자의 이번 명시적 승인을 병합 권한으로 적용했다.

과거 보고서의 OPEN/stacked 표기는 당시의 기록으로 보존한다. 현재 병합 상태는 `docs/research_state.json`의 `github_current`와 이 통합 기록을 따른다. 첫 합성 연결 실험 완료는 실제 제조공정 가설 검증 완료를 뜻하지 않는다.

세부 명령·검사 결과와 바이트 보존의 증거는 `research_runs/repeated_metric_pilot/integration/`에 있다. 연구 상태·후속 결과 갱신은 새 PR로 제출하므로, 그 PR의 변경까지 main에 반영됐다고 주장하지 않는다.

# 미완료 자산 복원 결과 — 2026-10-23

## 범위와 Git 상태

PR #1 실제 병합 확인 (`ceb447d`). PR #2는 open/unmerged, head `e5a0291`, 최신 CI 성공(39924152760)으로 확인했다. 이번 브랜치는 origin/main에서 생성했으며 PR #2의 simulator 코드·CSV를 가져오거나 수정하지 않았다. simulator 최신 상태는 PR #2를 외부 증거로 명시하여 현재 상태에 반영한다. 병합 승인 범위에 PR #2는 포함되지 않는다.

## 실제로 새로 확보한 바이트

- Slack `F0C6TP4168H` Step 6 ZIP: signed transport로 다운로드, SHA `28824bc2a98acb77ce8fc5f56439ea4910f7dc9f22ed45b7d1391f7f703f6b22`, 기존 Downloads 사본과 exact 일치.
- Slack `F0C7E97KXEC` 과제 ZIP: 다운로드, SHA `19179c04594ba2a59b40a7d890d2096a536f2864d4321e63dcc4ba7db770ccc6`, 기존 사본과 exact 일치. 최신 12개 후보로 덮어쓰지 않음.
- 공개 CPCaD-Bench를 새 checkout으로 clone하고 새 venv/빈 destination에 데이터·GT 취득. 기존 개인 경로에 의존하지 않은 해시 검증 성공.
- 원본 평가기 `evaluation/evaluator.py` SHA `5d120b8404b1a897e8fd69a022e749815f892c59751b6f05bbbd9fc0beba4ef2`를 확보. 새 어댑터에서 strict 3지표를 7개 Final에 계산하여 기존 표와 일치.

ZIP 바이트는 저장소 밖 `work/asset_recovery/`에 보존했다. 소스/데이터 재배포 권리를 확정하지 못해 ZIP·원본 코드·원본 CSV 자체를 Git에 추가하지 않았다. 고정 hash 입력과 새 adapter·검증 결과·가이드를 통합했다.

## 자산 수준 구분

| 자산 | 현재 수준 | 팀 재사용 범위·한계 |
|---|---|---|
| 데이터·GT | VERIFIED; 취득 절차 INTEGRATED | 새 clone/venv에서 실제 취득·schema/hash 검증. 배포 권리 UNKNOWN |
| Final 7개 | INTEGRATED (산출물) | frozen 배열/변환 검사 가능; 생성 학습은 BLOCKED |
| Step 6 원본 평가기 | REPRODUCIBLE (strict 평가); adapter INTEGRATED | 실제 원본 함수 호출해 7개 지표 일치; ZIP 접근 권한 필요 |
| Step 6 raw 결과 CSV/JSON | VERIFIED | ZIP 내부 존재·hash 기록, 기존 표 중복. 원본 전체 재수록 안 함 |
| PCMCI+ 로컬 baseline source | VERIFIED (로컬 바이트) | 이전 목록의 SHA 유지. Final 생성 파일 경로/hash와 다름; 역사 버전, 생성 실행 NOT_RUN |
| Track A/B·PC/BOSS·담당B 설명 문서 | LOCATED + TEXT_READ | connector 본문 확인. 로컬 같은 이름 파일은 별도 hash; Slack 원본 byte 동일성 미입증 |
| Final algos/run_*.py·common 모듈 | LOCATED (freeze의 경로/hash) | 실제 코드 바이트 미회수. 무리한 재구현 안 함 |
| PC/BOSS Colab | LOCATED / ACCESS_REQUIRED | 아래 링크 export가 Google 로그인 HTML을 반환해 ipynb 바이트 미회수 |

## 미회수 파일과 정확한 회수 요청

[PC/BOSS Colab](https://colab.research.google.com/drive/1pR_eseg0C1f3njCTWiAgx08hsSPQW-C7)은 9/14 Slack thread `1789407059.234739`에서 확인. 공개 export 요청은 HTTP 200이지만 content-type text/html, Google 로그인 페이지였다. 성공 다운로드로 기록하지 않는다. 소유자의 notebook `.ipynb` export와 Final revision이 필요하다.

담당 B 문서는 `b_directlingam_dagma.py`, `requirements_B.txt`, `run_manifest.json`을 가리키지만 이번 scoped 검색에서 해당 바이트를 찾지 못했다. 이들은 9월 최초 코드이며 Final의 `B-tune-v2 (재구성 재실험)`과 동일하다고 가정하지 않는다.

최종 생성에는 `FREEZE.json.code`의 `algos/run_pc.py`, `run_boss.py`, `run_b_retune.py`, `run_pcmciplus.py`, `run_varlingam.py`, `run_dynotears.py`와 `common/config.py`, `common/data_io.py` 등 shared source가 필요하다. 정확한 hash 목록은 `MISSING_FINAL_SOURCES.json`. `TEP_local_run.zip`도 동결 기록에 이름/hash가 있으나 채널 대상 검색에서는 찾지 못했다. 이름·코드 검색 결과가 없다는 것은 전체 Slack에 없다는 증명은 아니다.

PCMCI+ README/FILES가 가리킨 로컬 src와 config는 baseline 계열로 확인됐으며 Final 경로/hash와 연결되지 않았다. 소스팩 ZIP에는 `.py/.ipynb`가 없고, Step 6 ZIP은 evaluation 4개 및 report script만 포함했다. 기존 작업 폴더의 관련 파일명과 알려진 Downloads/소스팩만 조사했으며 전체 대화를 다시 수집하지 않았다.

## 방법론상 확인된 차이

- 9월 PC/BOSS 문서는 nominal 표본과 starts=10/seed=2026를 사용했다. Final BOSS config는 starts=1/seed=20261005, penalty=8.495...이다. 과거 notebook이 있더라도 Final 생성 코드로 즉시 승격할 수 없다.
- 최초 담당B 보고의 n_eff 약410과 Final 약114.36은 서로 다른 시점의 보고값이다. 새 유효표본수 계산이나 재튜닝은 하지 않았다.
- PCMCI+ 과거 Robust와 Final은 동일 설정을 일부 공유하지만 Final metadata에 원동결 파일 유실 후 재실행이 명시되어 있다. 설정 일치만으로 raw 동일성을 주장할 수 없다.
- 원본 Step 6 Directed precision은 확정+미확정 전체 추정 쌍을 분모로 쓴다. 현재 adapter는 이 strict 규약을 그대로 호출하며 초기 문서의 confirmed-only precision과 구분한다.

## 현재 완료 범위

모든 7개는 산출물 검사와 strict 평가 재현이 가능해 `PARTIALLY_REPRODUCIBLE`이며 **생성 학습은 전부 BLOCKED**다. 원본 코드와 정확한 환경이 없으므로 새로운 discovery 실행은 하지 않았다. seed·threshold·library version의 확인값은 Final config/freeze 원문에 근거하여 JSON에 기록했고 미확인은 null로 남겼다. U규칙/무작위 기준선 재실험은 이번 범위 밖이다.

문서 상단은 `docs/research_state.json` 하나에서 생성하며, 이전 상단/하단 충돌 문서는 `docs/history/`로 보존했다. 기존 8월 simulator BLOCKED와 PR #2 공개 후보 PARTIAL을 다른 ID로 유지한다. 우선 작업은 SRC-01, SIM-03, SIM-04다. 새 연구 결론이나 효과/Recovery/Safety 결과는 만들지 않았다.

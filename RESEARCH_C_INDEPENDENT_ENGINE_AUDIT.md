# 연구 C 정책 엔진 독립 감사

**대상 커밋:** `910301b4c589c4969dc7db959d4addafcf04a456` (감사 시작 기준)

**판정:** **CONDITIONAL PASS — 정책 엔진의 구조 계산·선택 로직은 고정 손그래프에서 검증됨. 실험 계약 논의는 가능하지만, 계약 승인이나 새 SCM 실험 준비 완료를 뜻하지 않음.**

## 범위

이번 검토는 명시 계수나 난수로 새 SCM을 만들지 않았고, 관측자료·개입 효과·정책 성능 순위·Decision Regret도 생성하지 않았다. 고정된 작은 DAG만 사용했다. Step 4 동결 자료, Step 5/6 원시 자료 및 결과는 수정하지 않았다. 기존 `fixture_run_v1.json`은 읽기만 했다.

감사 대상은 `research/original_objective/policy_engine.py`, 그 README·fixture·기존 테스트와 `scripts/validate_original_research_fixture_contract.py`, 후보 계약·결정 등록부·fixture 검증 보고서였다.

## 1. 코드와 계약 일치성

| 영역 | 코드 근거 | 감사 결과 |
|---|---|---|
| 오류 분류와 단일 귀속 | `policy_engine.py`: `task_zone` 68행, `classify` 137행 | 정답 X→Y 유향 경로와 무조건화 open backdoor 후보를 구조적으로 구한다. 각 참 인접쌍은 FN/REV/UNRES 또는 정답 방향 일치로 분류되고, 참에 없는 추정 인접쌍은 FP로 분류된다. 분류된 오류는 M1/M2/M3/M4 중 한 bucket만 받는다. FP Rule A는 task-zone node set 내부의 쌍, Rule B는 여기에 사전 명시한 boundary pair를 추가한다. |
| 지표·분모 | `metrics` 157행 | M1은 비과제 참 인접쌍 중 FN, M2는 비과제 추정 인접쌍 중 FP, M3 방향 정확도는 방향이 정해진 참 비과제 인접쌍 중 정방향 비율, unresolved rate는 추정된 참 비과제 인접쌍 중 UNRES 비율이다. M4는 FN/FP/REV/UNRES 벡터와 각 support를 보존한다. 0 분모는 `None`과 `zero_denominator` 사유로 기록된다. |
| Greedy gain | `burden` 213행, `run` 248행 | 수동 GAINS 상수 없이 현재/후보 후 오류 사건을 다시 분류하고 선택 subset의 정규화 잔존 부담 차이를 수정 비용으로 나눈다. M2 분모 변화만으로 생긴 비율 개선은 직접 오류 사건 감소가 아니므로 후보 gain을 받지 않는다. M3는 REV+UNRES 부담을 사용해 REV→UNRES를 복구로 보상하지 않는다. |
| M4 scalar | `burden` 213행 | 오류 성분 벡터를 보고용으로 유지하며, 활성 성분만 β로 재정규화해 subset scheduler의 단일 점수에 사용한다. 기본 동일 β는 잠정값이다. 활성 β 질량이 0인 경우 가짜 0 부담이 되지 않도록 오류를 던지게 보강했다. |
| 수정·비용·DAG | `candidates` 189행, `apply` 203행, `run` 248행 | FN add, FP delete, REV orient, UNRES resolve 후보를 만든다. 후보별로 잔여 예산과 DAG를 검사하고, 허용 가능한 양의 gain 후보 중 `gain/cost` 최고를 고른다. 동률은 metric 순서, 정렬된 pair, operation 순서로 결정된다. 적용 키로 같은 후보의 중복 적용·청구를 막는다. 실패 후보에는 비용이 청구되지 않는다. |
| 기록·평가 경계 | `run` 248행, `evaluation_record` 320행 | 전후 graph hash, 수정 로그, 비용·잔여 예산, stop reason, 지표·counts, `P_S`, `P_all`을 기록한다. `P_S`는 subset별 정규화 부담이며, `P_all`은 전체 이벤트 수에 유형 가중치와 M4 task multiplier를 한 번 곱한 공통 비정규화 값이다. 두 값은 같은 양이 아니다. policy 함수 인자에 계수·개입 효과·GT loss·Regret이 없고 평가 결과 필드는 null로 남는다. |
| 전략 집합 | `catalog` 242행, `run_catalog` 309행 | 무수정 S0 + 15개 비공집합 지표 조합을 실행한다. 별도 `CANONICAL_ORACLE`은 같은 GT 구조, 초기 그래프, 후보 분류, 비용·예산·DAG 제약을 받는 구조 정보 기반 단순 순서 기준선이다. 기존 Step 4 Global 정책과 동일시하지 않는다. |

### 계약 후보와 맞지 않거나 아직 별도 승인이 필요한 부분

- README와 코드의 Rule A, fixed-opportunity normalization, 단위 비용, 동일 M4 β·유형 가중치는 모두 **미승인 fixture 기본값**이다. 연구 계약을 동결하지 않는다.
- 고정 opportunity 정규화는 작은 support를 가진 오류 성분의 사건당 gain을 크게 만든다. 이는 계산 오류는 아니지만 실질적인 정책 우선순위 선택이다. 아래 fixture에서 M1보다 M4의 점수가 커지는 것을 확인했다.
- M4 FP 귀속은 task-zone node set을 포함하는 규칙이다. 이 구조적 구역은 실제 개입 손실 피해와 동치가 아니다. Rule A/B 선택은 모집단의 오류 분류 자체를 바꿀 수 있다.
- `P_all`은 원 계약의 λ 해석을 `M4` 전체 배수로 구현한다. λ를 “task 총 배수”로 해석할지, 비과제 피해에 더하는 증분으로 해석할지는 OPEN이다. UNRES·유형 가중치도 아직 경험적으로 정당화되지 않았다.
- Greedy는 현재 subset 부담을 줄이는 myopic 휴리스틱이다. 전역 최소 비용 수정열 또는 Decision Regret 최적화를 보장하지 않는다.
- 같은 최종 graph를 만든 정책이 여러 개일 수 있다. 이는 정상적으로 hash로 비교 가능하지만, nominal policy count를 독립적 결과 수로 세면 안 된다.
- 엔진은 단일 명시 graph에서 실행 가능한 구조 진단기다. 아직 연구 C의 SCM 적합·행동 추천·별도 정답 SCM 평가기와 연결된 실행 pipeline이 아니다.

## 2. 추가 독립 Fixture 테스트

신규 파일 `tests/test_original_objective_policy_engine_independent.py`의 9개 테스트는 기존 검증 스크립트와 다른 테스트 assertion을 사용하고, 각 기대값은 작은 graph의 사건 수·분모를 손계산했다.

| 테스트 사례 | 수작업 기대값 | 관찰 결과 |
|---|---|---|
| 동일 M1 지표의 FN 후보 2개 | 각 gain `1/2`, 비용 동일 시 canonical pair A–B 선택 | A–B 선택, score 0.5 |
| M4에 FN/FP/REV/UNRES 모두 활성 | support `(4,4,2,3)`, 동일 활성 β. REV repair의 subset 점수 `(1/2)/4=1/8`, FN은 `(1/4)/4=1/16` | REV 선택, score 0.125 |
| 정규화 역전 | 오류 개수 정규화 M1 `1` 대 M4 `1/2`; 고정 기회 정규화 M1 `1/10` 대 M4 `1/3` | B=1에서 오류 개수 방식 M1, 고정 기회 방식 M4 선택 |
| 비용상 실행 불가 | add 비용 2, 예산 1 | 수정·청구 없음, 잔여 예산 1, `no_feasible_candidate` |
| cycle 후보와 안전 후보 | 먼저 안전한 A→B를 적용한 뒤 Y→X는 기존 X→C→Y 경로 때문에 cycle | 안전 수정만 비용 1로 적용, 반복 검토된 cycle reject 2회, 최종 DAG 유지 |
| 서로 다른 subset 같은 결과 | M1-only와 M1+M2+M3+M4, B=1 | 최종 hash 동일 |
| 결과 정보 접근 | `run` 공개 인자에는 구조·task·예산·subset/config만 존재 | GT loss/Regret 인자 없음, GT 평가 필드 null |
| S0와 canonical 기준선 | 동일 초기 graph와 B, 서로 다른 정책 ID | S0 무수정, canonical 구조 순서 수정, 같은 실행 조건 |
| 잘못된 수치 설정 fail-closed | 무한 예산, 활성 M4 성분 β 질량 0 | `ValueError`로 거부 |

마지막 항목은 감사 중 발견한 잘못된 입력 방어 문제를 수정해 검증했다. 이전에는 무한 예산이 유효한 수치로 통과할 수 있었고, 활성 M4 성분의 β 질량이 0이면 burden이 0으로 조용히 처리될 수 있었다. `Config`도 비용 누락·중복, 잘못된 벡터 길이, 비유한 수를 거부하도록 보강했다.

## 3. 테스트 환경과 실행 결과

### 환경

- CPython 3.11.15 (Windows, 64-bit)
- `requirements.txt` 고정 그대로: NumPy 2.4.3, pandas 3.0.1, NetworkX 3.6.1
- 관리 Python에 무단 설치하지 않고 `uv run --python <CPython 3.11.15> --with-requirements requirements.txt`로 임시 실행 환경을 사용했다.

### 실행 명령 및 결과

- `uv run --python <py311.15> --with-requirements requirements.txt -- python -X utf8 -m unittest tests.test_original_objective_policy_engine tests.test_original_objective_policy_engine_independent -v` — **17/17 통과**.
- `uv run --python <py311.15> --with-requirements requirements.txt -- python -X utf8 scripts/validate_original_research_fixture_contract.py` — 통과. M1–M4 수작업값, Rule A/B, denominator illusion, 두 normalization 및 선택 역전, 복수 후보, 비용, DAG rejection, subset/budget fixture를 재현했다.
- `uv run --python <py311.15> --with-requirements requirements.txt -- python -m compileall -q research/original_objective tests/test_original_objective_policy_engine.py tests/test_original_objective_policy_engine_independent.py` — 통과.
- 전체 `uv run --python <py311.15> --with-requirements requirements.txt -- python -X utf8 -m unittest discover -s tests -v` — **283개 실행, 280개 통과, 2개 실패, 1개 오류**. NumPy 등 의존성 로드는 정상화됨. 전체 성공으로 보고하지 않는다.

## 4. 기존 실패의 독립 조사

### Step 4B4 raw ledger hash 테스트

파일: `research/budget_aware_refinement/step4b4_mock_pipeline_run_v2.jsonl`.

- 동결 manifest 기대값: `9c12a2b9d7d8fe15b886783be9f53b0486d137a742c467d0f00b653b62905c21`.
- `git show HEAD:<path>`에서 얻은 원본 blob: 1,408 bytes, SHA-256이 manifest와 **정확히 일치**.
- Windows 작업 파일: 1,413 bytes, SHA-256 `e8a1c6144d1c40351469754d16b956647ce9e812dea64ebca84f8dd5f18c783a`.
- 작업 파일은 5개 LF가 CRLF로 체크아웃되어 있고 CRLF→LF 정규화 후 원본 Git blob과 byte-for-byte 동일하다. `core.autocrlf=true`, Git은 파일을 `i/lf w/crlf`로 보고한다.
- 실패 테스트는 `.jsonl`을 `read_bytes()`로 바로 해시해 텍스트 줄바꿈을 정규화하지 않는다.

**판정:** 원시 동결 파일 자체의 변경이 아니라 플랫폼 줄바꿈에 취약한 테스트 비교다. 동결 원시 파일·manifest·테스트 기준 해시는 수정하지 않았다.

### Step 4C1 production manifest 테스트

`tests/test_step4c1_production.py`는 text 파일에 CRLF 정규화를 적용한 뒤 `WORK_LOG.md`를 비교한다. 정규화된 현재 파일 및 Git blob SHA-256은 `351869ebe1af9893cc6b149ded13cc0e972a18659eb9510dec1553e317ea7d7d`이나, `step4c1_production_manifest.json`의 기대값은 `608efe6ad1619267aae66e0d90dcdef39dc5ff057880bad288bfe534740ad6f1`이다. 따라서 이 불일치는 CRLF만으로 설명되지 않고 manifest 내용 해시가 현재 저장소와 맞지 않는다. 해당 manifest는 `NOT_FROZEN` 후보 상태이며, 이번 감사에서 변경하지 않았다.

### Step 4 production readiness 양성 경로

전체 suite 안의 양성 경로 테스트는 `assert_production_ready`가 checkout의 clean tree를 요구해, 사용자가 보존하도록 한 미추적 `.build_reframed/`와 감사 미커밋 변경 때문에 `production cohort entry requires a clean worktree`에서 오류가 났다. 동일 커밋 `910301b4c589c4969dc7db959d4addafcf04a456`을 별도 detached clean worktree로 체크아웃해 다음 테스트를 재실행했고 **1/1 통과**했다: `uv run --python <py311.15> --with-requirements requirements.txt -- python -X utf8 -m unittest tests.test_step4_post_freeze_readiness.PostFreezeReadinessTests.test_exact_clean_revision_passes_production_readiness_without_generating_data -v`. 임시 worktree는 검증 뒤 제거했고 원래 `.build_reframed/`는 그대로 보존했다. 따라서 생산 준비 양성 경로 자체는 기준 커밋의 clean checkout에서 통과하며, 원 작업 디렉터리에서만 청결 조건으로 막혔다.

## 5. 과학적·운영상 위험

### 확인된 설계 특성

- fixed-opportunity normalization은 고정된 G0 support로 나누므로, M4의 희소 오류 성분이 더 작은 denominator를 가지면 단일 수정 gain이 M1–M3보다 커질 수 있다. 독립 반례에서 M1 `0.1`, M4 `0.333…`이 되어 선택이 뒤집혔다. 이는 코딩 오류가 아니라 어떤 기회 집합을 동등하게 볼지에 대한 연구 설계 선택이다.
- M1–M3와 M4의 후보 수와 support가 다르므로, 결과 해석에는 raw 오류 수·분모·후보 수·비용·unused budget·최종 그래프 hash를 병기해야 한다. subset 선택은 수정 가능한 기회 자체도 바꾼다.
- `P_S`가 줄어도 `P_all`이 같은 비율로 줄거나 Decision Regret이 줄어든다고 보장하지 않는다. 현 엔진은 GT outcome을 읽지 않으므로 Regret 링크는 아직 미검증이다.
- 16개 명목 전략의 결과 충돌을 분석할 수 있지만, fixture의 충돌 빈도를 연구 모집단의 정책 동등성으로 일반화할 수 없다.
- canonical 기준선은 oracle structural error event와 candidate를 공유해 비교 정보·비용·예산 조건은 맞춘다. 다만 정답 구조 정보를 사용하는 진단 baseline이며, Step 4의 ID-ordered Global이나 배포 가능한 오류 탐지 정책과 다르다.

### 잔여 과학적 결정

Task zone 및 backdoor conditioning, FP Rule A/B, M1–M3 공식 보고와 M2/M3 분모, M4 β, normalization, 비용, event-level 오류 가중치·λ·UNRES 벌점, tie tolerance, 비용 제약·예산 grid, baseline 비교, 개발/가중치 추정/평가 자료 분할과 표본·분석계획은 여전히 OPEN이다. 현재 코드가 이 항목들을 임의로 승인하지 않는다.

## 6. 최종 판단과 실행 준비

**CONDITIONAL PASS.** M1–M4 사건 분류 및 분모, 후보 gain/cost, DAG·예산 제한, 결정적 tie 처리, 기록, 구조 outcome firewall은 독립 손그래프 테스트에서 동작했다. 수정한 fail-closed 수치 검증도 통과했다. 전체 저장소 테스트 결과는 Step 4의 줄바꿈 취약 해시 assertion, stale NOT_FROZEN manifest assertion, 그리고 dirty worktree readiness assertion 때문에 완전 통과가 아니다. 이들을 숨기거나 오래된 자산을 수정하지 않았다.

정책 엔진의 타당성 검토를 넘어 **실험 계약 확정 논의 단계**로 이동할 수 있다. 신규 SCM 실험은 아직 시작하면 안 된다. 연구 C의 SCM/관측자료/효과 추정/조작 추천/정답 평가/Decision Regret production path도 이 정책 엔진과 연결되어 검증되지 않았다. 계약 결정·분할·평가 경로를 별도 확정하고, 위 저장소 baseline 문제와 clean-checkout readiness를 해결·재검증한 뒤 별도 승인을 받아야 한다.

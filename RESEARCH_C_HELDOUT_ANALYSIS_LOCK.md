# Research C Held-out 분석 계획

**상태: `APPROVAL_REQUIRED / PROPOSED_NOT_FROZEN`**

이 문서는 Held-out 결과를 보기 전 분석 규칙을 고정하기 위한 제안이다. bootstrap seed가 아직 승인되지 않았고 Held-out 실행도 별도 승인 대상이므로, 외부 공개 사전등록 또는 계약 동결을 뜻하지 않는다.

## 1. 기준 자료와 계보

| 자료 | 식별자 |
|---|---|
| Research C 정책 실행 소스 | commit `01473797e8edd9e01935a7bee57107b63a4d53ca`, tree `3a1577c806ef0e6eff02fc1ffaa020f490ef6be9` |
| Development 사후 감사 기준 | commit `cabd61ed7a4528aad073652568d1801fd1840b6c` |
| Development run | `development-20261123-seed-2026112301-v1` |
| 승인 Config canonical SHA-256 | `96267e6f6004bc4255ae3765c8b4a939f3511690b1d4c34d2fd8195a8294b3f4` |
| 승인 Config file SHA-256 | `5a22f5601705bae7c8d1675ef37807964bbf6c7382779fb0216e5b5169159819` |
| 승인 Manifest canonical SHA-256 | `d992806153622173644edf470e3b79f41f29bc547fc588922f6e96bd9f3273ac` |
| 승인 Manifest file SHA-256 | `97ba1d89e75751d932b81e0a2ae1e07c797cdee93eaa1eeed7d7b5d491640c61` |
| Development cohort DB SHA-256 | `dd4264d5085adbabe9510bf99b564ec6c2b33e35d4eeb346a079cc4ccfb9b716` |
| Development proposal DB SHA-256 | `1d00d1790788c342e15a81a0c405768e5e2a3e46ee75c57c0bbe34f8c0fcb584` |
| Runtime | CPython 3.11.15, 13개 패키지 버전은 `research/original_objective/research_c_runtime_lock.txt` |
| Runtime lock SHA-256 | `8d2eeed082646ca3ea2eb437e9f313c0ecd4165807b59548f2ed0810c460e2a7` |

Development 실행 소스, 감사 코드, 이번 분석 코드, 향후 Held-out 실행 소스는 서로 다른 계보 식별자로 보존한다. Development 원시 Ledger·G0·Config·Manifest는 수정하지 않았다. Held-out Manifest는 실행 시점의 별도 source commit/tree, code map, runtime, 승인 Config를 결합해야 한다.

## 2. 잠정 분석 코드와 읽기 전용 검증

`research/original_objective/analysis.py`는 SCM 단위 paired 계산, paired-t 요약, percentile bootstrap을 제공한다. `scripts/analyze_research_c_cohort.py`는 승인 Config·Manifest의 상호 해시와 cohort/run/seed, ledger source/code/runtime, proposal-stage binding, SQLite 무결성, 행 checksum, 정책별 공통 입력 및 G0 설정을 검증하고 DB를 `mode=ro`와 `query_only=ON`으로 연다. 결과는 원본 DB 바깥의 새 JSON에 원자적으로 쓴다.

Development read-only 실행 예:

```powershell
python scripts\analyze_research_c_cohort.py `
  --cohort-db C:\DAT_RESEARCH\research-c\development\development-20261123-seed-2026112301-v1\research_c_cohort.sqlite `
  --proposal-db C:\DAT_RESEARCH\research-c\development\development-20261123-seed-2026112301-v1\research_c_proposal_stage.sqlite `
  --approved-config C:\DAT_RESEARCH\research-c\approvals\development-v1-approved.json `
  --manifest C:\DAT_RESEARCH\research-c\approvals\development-v1-manifest.json `
  --bootstrap-seed 2026112302 --bootstrap-replicates 10000 `
  --output C:\DAT_RESEARCH\research-c\analysis\development-v1-analysis-v11.json
```

위 seed는 재현성 점검에 사용한 **PROPOSED 후보**일 뿐 승인 분석 seed가 아니다. 최종 분석 소스 해시와 본 문서를 포함한 commit은 이번 변경 커밋 이후 고정한다. Held-out 분석을 열기 전에는 seed와 분석 계획의 명시적 승인이 필요하다.

## 3. Development 분석 재현값

64 admitted SCM 모두 완료되었고 64개 P1 및 M4 pair가 완성되었다. 64 proposals는 모두 eligible였고 proposal cap에는 도달하지 않았다. 5,440개 정책×예산 평가에서 실패는 0건이다. 18개 SCM은 Q-common, 무오류 G0는 7개다.

### 승인된 Primary P1

예산 B=2에서 `Full Greedy = M1+M2+M3+M4`와 S0를 비교한다.

`delta_i = Regret_i(S0,B=2) - Regret_i(FullGreedy,B=2)`

양수는 Full Greedy의 Regret이 낮음을 뜻한다. 독립 분석 단위는 SCM이며, 주 효과량은 complete pair의 평균이다.

| 통계 | Development 재계산 |
|---|---:|
| complete pair | 64 |
| 평균 S0 Regret | 0.1008517293 |
| 평균 Full Greedy Regret | 0.0256408438 |
| 평균 delta | +0.0752108855 |
| 중앙값 / SCM 간 표본 SD | 0 / 0.1720756403 |
| 95% paired-t CI | [0.0322276695, 0.1181941016] |
| 자유도 / 표준오차 / 임계 t | 63 / 0.0215094550 / 1.9983405425 |
| 개선 / 악화 / 동률 | 14 / 1 / 49 |
| 행동 변경 / 동일 행동 | 15 / 49 |
| Full Greedy 평균 수정 수 / 비용 | 1.453125 / 1.453125 |

이는 Development 탐색 결과다. 동률 49건을 제거하지 않았다. 이 49건 모두 추천 행동이 같았다. 그중 무오류 G0이면서 Full Greedy가 no-op인 동일 SCM은 7건이고, 나머지 42건은 그래프가 변했어도 행동과 Regret은 같았다.

### Bootstrap 민감도

제안 절차는 SCM delta 전체를 복원 추출하고, 표본 평균 10,000개에서 선형 보간 2.5/97.5 분위수를 취하는 paired percentile bootstrap이다. Development에서 후보 seed `2026112302`, CPython `random.Random` MT19937로 두 번 실행했으며 두 산출물의 canonical analysis payload SHA가 일치했다. 점검상 bootstrap 구간은 `[0.0368331451, 0.1209794588]`이었다. **seed 미승인 상태이므로 이 값은 공식 민감도 분석 결과가 아닌 재현성 검사용 출력이다.** Paired-t CI가 승인된 주 불확실성 요약이며 bootstrap으로 대체하지 않는다.

### Development-selected M4 비교

M4는 Development 결과를 확인한 뒤 주목한 정책이므로 아래 비교들은 사후 선택된 secondary family다. 원래 가설 또는 Primary로 표현하지 않는다. 양수는 비교 대상 정책의 Regret이 M4보다 큼을 뜻한다.

`delta_M4_i(other) = Regret_i(other,B=2) - Regret_i(M4,B=2)`

| 비교 대상 | 평균 차이 | 개선 / 악화 / 동률 | 같은 그래프 | 같은 행동 |
|---|---:|---:|---:|---:|
| Full Greedy | +0.0227131 | 3 / 0 / 61 | 19/64 | 61/64 |
| S0 | +0.0979240 | 17 / 1 / 46 | 33/64 | 46/64 |
| Canonical Oracle | +0.0531192 | 9 / 0 / 55 | 18/64 | 55/64 |
| M1+M4 | 0 | 0 / 0 / 64 | 44/64 | 64/64 |
| M2+M4 | 0 | 0 / 0 / 64 | 33/64 | 64/64 |
| M3+M4 | +0.0184347 | 2 / 0 / 62 | 43/64 | 62/64 |

M4는 평균 0.65625 edits/cost, Full Greedy는 1.453125이었다. M4의 42개 수정은 모두 task-zone(FN 12, FP 6, REV 11, UNRES 13)이었고, Full Greedy는 task-zone 32건 및 off-task 61건을 수행했다. M4와 M1+M4, M2+M4의 Regret이 이 Development 표본에서 모두 동률이었다. 이는 독립적인 64× 정책 증거가 아니라 동일 SCM의 중첩 비교다. 선택 편향과 다중 비교 가능성을 함께 기술한다. 어느 정책이 Held-out에서 더 좋을 것이라고 가정하지 않는다.

### 구조→행동→Regret 기술 분석

Full Greedy 대 S0, B=2에서 공통 구조 벌점 `P_all`은 57 SCM에서 낮아졌다. 그중 하나는 Regret이 악화했다. 그래프·행동·Regret 교차는 (변경, 변경, 변경) 15건, (변경, 동일, 동률) 42건, (동일, 동일, 동률) 7건이었다. 행동은 바뀌었지만 Regret이 동률인 사례는 0건이다. 한 건의 `P_all` 감소와 Regret 악화가 함께 나타나 구조 개선을 의사결정 개선으로 대체할 수 없음을 보여준다.

이전 감사의 “P_all 개선 43건” 표현은 개선 전체 수로 읽힐 수 있다. 본 SCM별 재계산에서 전체 P_all 개선은 57건이다. 이전 문장의 43건은 그중 Regret이 개선되지 않은 경우(동률 42 + 악화 1)를 뜻한다. 과거 감사 원문은 보존하고 본 분석에서 전체 개선과 Regret 방향을 분리한 값을 기준으로 해석한다.

## 4. Held-out 분석 제안

다음 규칙은 A/B/C 승인 계약 및 기존 P1을 유지하는 제안이며, 별도 Held-out 실행 승인도 필요하다.

1. **P1 변경 금지:** B=2 Full Greedy 대 S0, SCM-level complete-pair 평균 `delta`, 양수는 Full Greedy 유리. 양측 95% paired-t CI, SCM 단위 자유도 `n-1`을 사용한다.
2. **Complete-pair 분모:** 목표 모집단은 A2 admitted SCM이다. 실제 P1 추정치는 S0와 Full Greedy가 모두 정상 완료된 SCM의 complete pairs다. 실패는 정책별·단계별 원인과 전체 admitted 대비 비율로 별도 보고한다. 누락 Regret을 0으로 치환하거나 결과에 따라 재추출·대체하지 않는다. complete-case 평균을 admitted 모집단 평균으로 자동 일반화하지 않는다.
3. **Bootstrap:** seed 승인 후 SCM delta 10,000 paired percentile resamples, 복원추출, 선형 분위수 방법. RNG seed는 SCM cohort RNG와 분리한다. bootstrap seed와 분석 코드 hash는 Held-out 결과 열람 전에 잠근다. Paired-t가 Primary이고 bootstrap은 보조 민감도다.
4. **사전 지정 secondary:** B=1 보조, B=3/4 포화 진단, B=0 기준선. 15개 부분집합과 Canonical Oracle은 전체 표의 기술 분석으로 보존한다. 다수 비교를 독립 표본으로 취급하거나 정책별 최솟값을 확증 결과로 고르지 않는다.
5. **Development-selected M4 family:** B=2에서 M4를 Full Greedy, S0, Canonical Oracle, M1+M4, M2+M4, M3+M4와 SCM paired 비교한다. `Regret(other)-Regret(M4)`를 정의하고 mean/median/SD, sign counts, Regret, graph/action 일치, 수정 비용 및 task/off-task/error-type 구성을 모두 보고한다. 이는 Development 확인 후 선택한 secondary family임을 명시하고 P1을 대체하지 않는다.
6. **구조-행동 진단:** 그래프/행동/Regret 변화 조합, no-op, 오류 기회, 수정 횟수·비용, `P_all`을 분리 기록한다. 미관측 범주는 0건으로 보고하고, SCM 사례를 결과에 유리하게 고르지 않는다.
7. **Held-out 표본:** A2 admitted SCM 200개 목표, proposal cap 1,104. 실패 및 cap shortfall을 보존하며 실패 이후 대체하지 않는다. Development/held-out seed, namespace, Manifest, Ledger, 출력 경로는 분리한다. Held-out seed는 아직 미승인이다.
8. **정보 경계:** GT DAG는 계약이 허용한 구조오류 분류·수정에만 쓰인다. GT SCM 손실과 최적 행동은 정책 순위나 추천 확정 전에 사용하지 않는다. GT 평가는 추천 확정 후 별도 계층에서 실행한다. Canonical Oracle은 structural-only 기준선이며 regret 상한선이 아니다.

## 5. Provenance 판정과 Held-out 재발 방지

Development의 오래된 G0 레이블 `PROPOSED_NOT_APPROVED`와 `not_authorized`는 이전 감사에서 `METADATA_ONLY_CONFIRMED`로 판정되었다. 현재 분석은 원본 G0 레코드를 수정하지 않는다. 공식 실행 출처는 승인 Config/Manifest, run Ledger의 source/code/runtime/config binding, proposal-stage config/checksum, SCM별 `cohort_binding`, `source_revision`, `code_sha256`, `runtime_fingerprint`로 확인한다. 새 read-only 결과에서 승인 실행 provenance가 있는 행은 64/64, 승인된 G0 설정이 일치하는 행은 64/64, 레거시 레이블이 남은 행은 64/64다. 따라서 해당 레이블은 올바른 승인 상태로 해석하지 않고 낡은 helper 출력 문구로 취급한다.

Held-out용 별도 승인 Bundle은 새 Held-out run ID와 독립 RNG namespace/seed, `independent_evaluation` cohort, 승인 Config, 현재 실행 source commit/tree 및 전체 Manifest code hash, Python/runtime fingerprint, 제안된 자원 상한, output root를 결합해야 한다. 기존 Development Manifest를 수정하거나 재사용하지 않는다. 새 분석 전용 코드 추가가 실행 코드 hash map에 포함되는 경우에도 Held-out Manifest에는 해당 시점의 전체 hash map을 고정한다.

## 6. 결과 열람 전 잠금 조건과 분리된 승인

Held-out를 열기 전에 다음을 충족해야 한다.

- 제안 seed `2026112302` 및 bootstrap 방법에 대한 명시적 승인
- 본 문서와 분석 코드가 든 Git commit 및 분석 파일 SHA-256 고정
- Held-out 실행 source commit/tree, runtime lock, 승인 Config/Manifest, 독립 seed 및 output 경로 검증
- 비실행 Preflight 통과
- Held-out 실행에 대한 별도의 사용자 승인
- 실행 완료 후 Ledger/hash/complete-pair 검증; 이 검증 이후 분석 결과 접근

내부 Git commit 기반 분석 잠금은 외부 공개 사전등록과 다르다. 현재 문서는 둘 중 어느 것도 승인·완료 상태라고 주장하지 않는다. 승인되지 않은 값이 있으면 분석 및 코호트 실행을 차단한다.

## 7. 검증된 산출물

| 항목 | 값 |
|---|---|
| Read-only Development report | `C:\DAT_RESEARCH\research-c\analysis\development-v1-analysis-v11.json` |
| Canonical analysis payload SHA-256 | `5eb3988413cf6a7f8fc5e96576e94959a25278ee687dba24e6215197a8aeab3e` |
| Report file SHA-256 | `f0591789d2cb6d63acae4c51fbd6969ade87834ffd801023699f15c258042e5e` |
| Analysis module SHA-256 | `4002be37f20ee5cf86e736acbEE52c05d1397e2f4c4c29cf517ca414eb16fb71` |
| Analyzer script SHA-256 | `93d8f153011dcc80bc0fe438c774bd9df898d5be7986462e404165ababc883fc` |
| Repeated run | 동일한 payload 및 파일 SHA-256 |
| Held-out | 실행되지 않음; 결과/SCM 없음 |

이 문서의 최종 상태는 `APPROVAL_REQUIRED`다. bootstrap seed와 Held-out 실행은 사용자 승인 전까지 잠기거나 실행되지 않는다.

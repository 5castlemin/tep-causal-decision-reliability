# Research C 원본 Ledger 기반 메커니즘 분석 감사

감사일: 2026-11-26. 저장된 Research C 산출물을 read-only로 열어 확인한 후속 사후 분석 감사다. 신규 SCM, 관측자료, 학습자료, intervention response 또는 정책 코호트는 생성하지 않았다.

## 원본 식별과 무결성

| 항목 | Development | Held-out |
|---|---|---|
| run ID | `development-20261123-seed-2026112301-v1` | `independent-evaluation-20261123-seed-2026112303-v1` |
| master seed | 2026112301 | 2026112303 |
| 공식 원본 cohort DB SHA-256 | `dd4264d5085adbabe9510bf99b564ec6c2b33e35d4eeb346a079cc4ccfb9b716` | `37b3c265ecb65b09a97eda91d29411844c3a3851c9fbff6cfa06445f919a3eba` |
| proposal-stage DB SHA-256 | `1d00d1790788c342e15a81a0c405768e5e2a3e46ee75c57c0bbe34f8c0fcb584` | `59f1abcf5661a5b3d0658d0db0f7e6afe601ebd09997035228df0716800538d6` |
| 승인 manifest 파일 SHA-256 | `97ba1d89e75751d932b81e0a2ae1e07c797cdee93eaa1eeed7d7b5d491640c61` | `f13b954850044a9c6b1b1c1812a855363f5772c1dc703ab7bec916a403a21357` |
| manifest canonical SHA-256 | `d992806153622173644edf470e3b79f41f29bc547fc588922f6e96bd9f3273ac` | `654bce9349d9d70bc2ce7db10d179a9e80a0fb9aa43fb23bcee619a261f4a379` |
| 저장 audit | `development-v1-audit-v7.json`, payload SHA `72a5a8c2ed6deb9f902324ef43631746b644194b9f95b92a20c18a5951b8bc31` | `heldout-v1-integrity-v1.json`, status `PASS` |
| 원본 cohort DB 검사 | SQLite `integrity_check=ok`; 64/64 completed | SQLite `integrity_check=ok`; 200/200 completed |
| 실행 source revision | `01473797e8edd9e01935a7bee57107b63a4d53ca` | `0ffcaeb0c2cf7213e34f05ce1db1dd967ec72de3` |

원본 cohort 및 proposal-stage DB의 해시를 분석 전후 확인했다. cohort DB에 WAL/SHM sidecar는 없었다. SQLite는 `mode=ro`와 query-only 모드로 조회했다. `result_json` payload digest와 Ledger의 `result_sha256` 결합을 확인한 결과 두 cohort 모두 checksum 오류 0, 중복 `(SCM, policy, budget)` 키 0이었다. Development 5,440행과 Held-out 17,000행이 각각 64×17×5 및 200×17×5에 맞았다.

## 재집계 및 PR #40 결과와의 대조

정창민 PR #40의 `mechanism.py`, `analyze.py`, `ties.py`, `pathcheck.py`, `flat.py`를 읽기 전용으로 적용했고, 별도 SQL/JSON 순회 집계로 주요 평균·paired 대비·경로/flat 관계를 독립 재계산했다. 원본 공식 감사 및 PR #40에 보존된 표/행동 불일치 사례와 대조했다.

- 두 cohort의 85개 정책×예산 셀이 공개 반올림 정밀도에서 모두 일치했다. 평균 regret 8자리와 일부 평균 수정/오류 수 3자리의 반올림 차이는 불일치와 구분했다.
- B=2 Primary 평균 `Regret(S0)−Regret(Full Greedy)`: Development `+0.0752108855`, Held-out `+0.0748363574`.
- Held-out B=2 S0/Full Greedy/M4 평균 Regret: `0.0934389768 / 0.0186026193 / 0.0039877460`; Full Greedy 평균 edit count `1.435`, M4 `0.695`; 행동 일치 `193/200`.
- 원본에서 Full Greedy 대비 action이 달랐던 B=2 Held-out 7건은 PR 표의 7건과 key 기준 일치했다.
- 경로 존재와 predicted loss가 flat인지의 대조는 Development 5,440행에서 `path+non-flat 4,627`, `no-path+flat 813`, discordance 0; Held-out 17,000행에서 `14,191`, `2,809`, discordance 0이었다. 이는 이 두 실행과 learner의 경험적 일치이며 보편적 정리가 아니다.
- Greedy step replay는 저장 edit sequence를 결정론적으로 재검산했다. 정책 엔진의 바이트 hash는 실행 당시 Ledger에 기록된 hash와 맞았다.

Held-out B=2에서 action이 달랐던 7개 사례 중 M4는 6개에서 낮은 regret을 보였다. 이 중 5개(`…000041`, `…000053`, `…000125`, `…000140`, `…000158`)는 G0에서 X→Y 경로가 없고 M4가 경로를 복원해 최적 부호 action을 선택했다. 여섯 번째 `rep-scm-confirmation-proposal-000139-a0138`은 처음부터 X→Y 경로가 있었고 M4와 Full Greedy 모두 경로를 보존했지만 M4는 `k=+1`, Full Greedy는 `k=−1`을 선택했다. 그러므로 6건 전부를 경로 복원으로 설명하지 않는다. Full Greedy가 우세한 `…000076`에서는 남은 off-task FP와 task 방향 수정이 DAG 순환을 만들었고 M4는 DAG 제약에서 정지했다.

## 남은 비교 한계

PR #40은 당시 원본 Ledger에 접근하지 못해 재생성 Ledger를 사용했다. 해당 재생성 cohort DB 및 22,440행 전체 SCM×policy×budget 원시 결과는 공개 PR에 보존되어 있지 않다. 그러므로 재생성 실행의 모든 SCM key·graph hash·edit sequence·result를 원본과 완전 대조했다고 말할 수 없다. 확인 범위는 원본 Ledger의 전체 승인 코호트와 checksum, PR에 저장된 정책×예산 집계표, 일부 행동 불일치 사례, 동점/Greedy replay 산출물 및 대표 사례다. 재생성본을 승인된 연구 결과로 승격하지 않으며, 분석은 원본 대조 후에도 **Held-out 결과 열람 뒤 수행한 사후 탐색**으로 남는다.

## M1–M4 해석 정정

공식 지표와 Greedy proxy의 구분은 유지한다. `P_S`의 `1/|S|`는 같은 subset의 모든 metric 후보에 공통이므로 M4의 상대 점수 열세를 단독 설명하지 않는다. 단일 M4 성분 편집 gain은 `(1/|S|)(1/K)(1/support_j)`이고 비-M4 metric 오류 하나는 `(1/|S|)(1/support_m)`이다. 두 후보 비교에서 공통 `1/|S|`는 상쇄된다. 상대 순위에는 M4 활성 성분 수 `K`, 각 성분의 G0 고정 support, 오류 위치, 현재 구조, DAG 허용성 및 tie-break가 작용한다. 이 설명은 코드 `burden()`의 수식과 원본 수정 로그에 맞춘다.

Off-task 오류는 Rule A의 구조적 분류상 task zone 밖이라는 뜻이다. 인과적으로 무관하거나 행동에 영향이 없다는 뜻이 아니다. 원본 예시 `…000141`에서는 Y에 붙은 FP가 유일한 X→Y 경로를 만들었고 제거 후 추천이 악화됐다. `…000076`에서는 off-task FP가 DAG 제약을 통해 task 방향 수정을 막았다. `…000146`에서는 task 오류 수정이 이미 맞던 추천을 악화시켰다.

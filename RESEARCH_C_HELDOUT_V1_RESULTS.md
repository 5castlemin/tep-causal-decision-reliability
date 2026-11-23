# Research C Held-out V1 결과 및 감사

**최종 상태: `HELDOUT_COMPLETED_AND_AUDITED`**
**실행일: 2026-11-23**
**외부 공개 사전등록: 확인되지 않음. 본 문서는 내부 Git 기반 실행·분석 기록이다.**

## 1. 연구 질문과 해석 범위

제한된 수정 예산에서 불완전한 그래프의 구조 오류를 수정하고, 수정된 그래프에서 적합한 SCM으로 행동을 추천했을 때 Decision Regret이 어떻게 달라지는지 평가했다. 모집단은 승인된 합성 SCM 생성기, 계층적 task 추출 및 A2 strict indirect-only 적격성에 조건부인 모집단이다. 이는 실제 제조공정 전체나 전역 eligible `(X,Y)` 쌍의 균등 모집단으로 일반화되지 않는다.

개별 SCM이 독립 분석 단위다. 같은 SCM의 정책·예산 결과는 반복 측정이지 추가 독립 표본이 아니다. GT DAG에 기반한 오류 분류·수정은 승인된 Oracle-assisted 구조 정책의 일부다. 실제 GT 개입 손실과 최적 행동은 추천 확정 이후 평가했다. 따라서 결과는 정답 그래프가 없는 현장에 바로 배포 가능한 정책의 성능을 입증하지 않는다.

## 2. 승인 계약 및 실행 식별자

| 항목 | 실행값 |
|---|---|
| Cohort / run ID | `independent_evaluation` / `independent-evaluation-20261123-seed-2026112303-v1` |
| 실행 소스 | commit `0ffcaeb0c2cf7213e34f05ce1db1dd967ec72de3`, tree `74ee2486e6f1262733e305f5196672189eaff215` |
| 승인 Config | `C:\DAT_RESEARCH\research-c\approvals\heldout-v1-approved.json` |
| Config canonical / file SHA-256 | `20d6041b0a52e0552096e5a816d256ada24cf43648fac8f2a9a5f3d26693f8b8` / `4400cde7b20fa5e914691d49c082893334c9de15cb85a7a717de5cd3c2f83656` |
| 승인 Manifest | `C:\DAT_RESEARCH\research-c\approvals\heldout-v1-manifest.json` |
| Manifest canonical / file SHA-256 | `654bce9349d9d70bc2ce7db10d179a9e80a0fb9aa43fb23bcee619a261f4a379` / `f13b954850044a9c6b1b1c1812a855363f5772c1dc703ab7bec916a403a21357` |
| Master seed / bootstrap seed | `2026112303` / `2026112302` |
| 분석기 / 분석 모듈 SHA-256 | `b88bacbaaaf5bccfcfa6ebe9e82229de904cae5d334176a43055de39846be7b8` / `001ede1032b94878d1917db78f4d2ce0bea55ff5a891776b0301fc167dc1ba88` |
| Runtime | Windows CPython 3.11.15; 승인된 13개 패키지 lock. NumPy 2.4.3, pandas 3.0.1 |

사전 실행 Preflight는 `validated=true`로 통과했고 proposal/SCM 생성은 시작하지 않았다. Research 실행 명령은 이후 한 번 실행했으며 재개는 필요하지 않았다. 실행 중 결과를 열람해 조기 중지하거나 조건을 변경하지 않았다. 외부 공개 사전등록 완료를 주장하지 않는다.

## 3. Proposal, admission 및 원본 무결성

| 분모·상태 | 수 |
|---|---:|
| Topology proposal | 202 |
| Strict-task 적격 | 200 |
| 구조 부적격 | 2 |
| Q-common | 57 |
| Admitted SCM | 200 / 목표 200 |
| 무오류 G0 | 34 |
| 완료 SCM | 200 |
| 전체 17 정책 × 5 예산 평가 | 17,000 / 17,000 |
| P1 complete pairs | 200 / 200 |
| 실패 / 자원 초과 / shortfall | 0 / 0 / 0 |

모든 완료 SCM에 85개 정책·예산 행이 있으며 모두 성공했다. 동일 SCM 내 정책의 GT SCM, 관측자료, task, action grid 및 평가 식별자가 일치했다. S0 B=0과 B=2는 200개 모두 동일했다. Q-common은 보조 기술통계이며 모집단 필터로 사용하지 않았다.

Ledger 무결성 검사에서 두 SQLite DB 모두 `integrity_check=ok`, 외래키 위반 0, proposal checksum 202/202, 결과 checksum 및 공식 provenance binding 200/200이었다. G0 설정 일치도 200/200이었다. 내부 G0 레코드에는 오래된 `PROPOSED_NOT_APPROVED` 및 `not_authorized` 라벨이 200개 모두 남아 있다. Development 감사에서 같은 helper의 고정 출력 라벨은 metadata-only로 판정되었다. 이번 실행도 승인 Config/Manifest, run ID, source/code/runtime binding 및 G0 계약 기록으로 승인 실행과 연결되며, 이 라벨을 승인 상태로 해석하지 않았다. 원본 레코드는 수정하지 않았다.

Topology 분포(적격 admitted): chain mediation 48, observed common cause 57, fork branch 54, multiple directed paths 41. 노드 수 6/7/8/9/10의 수는 40/41/49/38/32다. 이 층별 수는 생성·적격성 절차의 기술통계이며 층별 정책 우월성 분석의 근거로 사용하지 않는다.

**원본 결과 위치 및 SHA-256**

- Cohort Ledger: `C:\DAT_RESEARCH\research-c\heldout\independent-evaluation-20261123-seed-2026112303-v1\research_c_cohort.sqlite` — 65,884,160 bytes; `37b3c265ecb65b09a97eda91d29411844c3a3851c9fbff6cfa06445f919a3eba`
- Proposal Ledger: 같은 디렉터리의 `research_c_proposal_stage.sqlite` — 544,768 bytes; `59f1abcf5661a5b3d0658d0db0f7e6afe601ebd09997035228df0716800538d6`
- Integrity audit: `C:\DAT_RESEARCH\research-c\audits\heldout-v1-integrity-v1.json` — SHA-256 `dedfc61d81f49194a0eefe0c0d57afb072f6f82f101634e8910f325f884c80e3`
- Read-only analysis: `C:\DAT_RESEARCH\research-c\analysis\heldout-v1-analysis-v1.json` — file SHA-256 `9e283ff1b6312a11959d92eab3089795b4b52f181e9480a00b771e96bf429420`; canonical payload SHA-256 `3c074c50b37229af61aeefd4933bb6766447b29ddae5f10a94f89b73ca17990c`

## 4. Primary P1: Full Greedy 대 S0, B=2

정의는 `delta_i = Regret_i(S0,B=2) - Regret_i(FullGreedy,B=2)`이며 양수는 Full Greedy의 Regret 감소를 뜻한다. 분석은 complete pair 200개에 한정한다.

| 통계량 | 결과 |
|---|---:|
| S0 평균 Regret | 0.09343898 |
| Full Greedy 평균 Regret | 0.01860262 |
| 평균 paired delta | **+0.07483636** |
| 중앙값 / 표본 SD | 0 / 0.17167541 |
| 95% paired-t CI | **[0.05089822, 0.09877450]** |
| 자유도 / SE / 임계 t | 199 / 0.01213928 / 1.97195654 |
| 개선 / 악화 / 동률 | 45 / 1 / 154 |
| 추천 행동 변경 | 46 / 200 (23.0%) |
| 동일 최종 그래프 / Full Greedy no-op | 34 / 34 |
| Full Greedy 평균 수정 횟수 / 비용 | 1.435 / 1.435 |

보조 SCM 단위 paired percentile bootstrap은 10,000회 복원추출, seed `2026112302`, `random.Random` MT19937, 선형 보간 분위수를 사용했다. 95% CI는 **[0.05225464, 0.09971651]**이고 bootstrap 평균은 0.07493758이다. Paired-t CI가 승인된 주 불확실성 요약이다.

이 추정치는 완전 paired SCM에서의 개발·평가 프로토콜상 평균 차이다. 이 자료만으로 전체 실 제조공정 또는 다른 생성 모집단에 일반화하지 않는다. 평가 실패가 없어서 complete-case 선택 문제는 이번 코호트에서 관측되지 않았지만, 이 한 번의 실행이 미래 실패의 무작위성을 보장하지 않는다.

## 5. M4 Development-selected Secondary

비교는 `delta_M4_i = Regret_i(FullGreedy,B=2) - Regret_i(M4,B=2)`다. 양수는 M4 Regret이 낮다는 뜻이다. M4는 Development 결과를 본 뒤 선택한 비교이므로 사후 선택된 Secondary이며 P1을 대체하지 않는다.

| 통계량 | 결과 |
|---|---:|
| 평균 Full Greedy / M4 Regret | 0.01860262 / 0.00398775 |
| 평균 paired delta_M4 / 중앙값 / SD | +0.01461487 / 0 / 0.09030863 |
| M4가 낮음 / 높음 / 동률 | 6 / 1 / 193 |
| 동일 추천 행동 / 동일 repaired graph | 193/200 / 83/200 |
| 평균 비용 Full Greedy / M4 | 1.435 / 0.695 |
| 수정 비용 차이 Full Greedy − M4 | 0.740 |

수정 로그상 M4는 139회 수정했다(FN 44, FP 14, REV 32, UNRES 49; 모두 task zone). Full Greedy는 287회 수정했다(FN 70, FP 82, REV 58, UNRES 77; task 111, off-task 176). 이 구성은 이 합성·Oracle-assisted 설정의 관찰이며 M4의 일반적 우월성을 증명하지 않는다.

M4와 Full Greedy 외 개발 선택 비교의 평균 `Regret(other)-Regret(M4)`는 S0 +0.08945123, Canonical Oracle +0.05141071, M1+M4 +0.00196206, M2+M4 +0.00868622, M3+M4 +0.00229139이다. 이 가족 비교는 개발 결과를 보고 선택된 탐색적 분석이며, 별도의 확증으로 세거나 정책 순위로 해석하지 않는다.

## 6. 15개 지표 조합 및 기준선의 기술 결과

아래는 각 정책의 평균 Regret을 예산별로 나타낸 기술표다(각 칸은 200 SCM 평균, 낮을수록 이 표본에서 관측된 Regret이 작음). 이것은 정책 우월성에 대한 별도 검정이나 순위 확정이 아니다.

| 정책 | B=0 | B=1 | B=2 | B=3 | B=4 |
|---|---:|---:|---:|---:|---:|
| Canonical Oracle | .09344 | .07856 | .05540 | .04104 | .01893 |
| M1 | .09344 | .09344 | .09344 | .09344 | .09344 |
| M1+M2 | .09344 | .09826 | .10047 | .10089 | .10089 |
| M1+M2+M3 | .09344 | .09454 | .09454 | .10047 | .10089 |
| M1+M2+M3+M4 (Full Greedy) | .09344 | .04605 | .01860 | .00817 | .00096 |
| M1+M2+M4 | .09344 | .03879 | .01267 | .00817 | .00096 |
| M1+M3 | .09344 | .09248 | .09248 | .09248 | .09248 |
| M1+M3+M4 | .09344 | .04032 | .00824 | .00144 | .00144 |
| M1+M4 | .09344 | .02941 | .00595 | .00144 | .00144 |
| M2 | .09344 | .09826 | .10047 | .10089 | .10089 |
| M2+M3 | .09344 | .09454 | .09454 | .10047 | .10089 |
| M2+M3+M4 | .09344 | .04597 | .01860 | .00463 | .00096 |
| M2+M4 | .09344 | .03870 | .01267 | .00463 | .00096 |
| M3 | .09344 | .09248 | .09248 | .09248 | .09248 |
| M3+M4 | .09344 | .04023 | .00628 | .00144 | .00144 |
| M4 | .09344 | .02933 | .00399 | .00144 | .00144 |
| S0 | .09344 | .09344 | .09344 | .09344 | .09344 |

Canonical Oracle는 structural-only 기준선이다. GT 구조를 이용해 오류 후보를 구조적으로 다루지만 GT 개입 손실을 선택에 쓰지 않으므로 regret의 이론적 상한선이 아니다. B=0에서 모든 정책은 무수정 기준선으로 같은 평균을 보인다.

## 7. 그래프·행동·Regret 연결

P1에서 그래프·행동·Regret이 모두 변한 경우 46건, 그래프는 변했지만 행동 및 Regret은 동률인 경우 120건, 그래프·행동·Regret이 모두 같은 경우 34건이었다. 행동이 달랐지만 Regret이 동률인 경우는 0건이다. P1 동률 154건은 모두 같은 행동이었다. 그중 무오류 G0 34건은 Full Greedy no-op 34건과 동일한 SCM 집합이었다. 나머지 120건은 그래프가 바뀌어도 행동이 같았다.

공통 구조 벌점 `P_all`은 166 SCM에서 개선되었으며, 그중 1건은 Regret이 악화되었다. 이는 구조 점수 개선과 Decision Regret 개선이 같은 결과가 아님을 보여주는 사례 집계다. 모든 경우를 구조 지표 하나로 대체하지 않고 각각 보존했다.

## 8. Development와 Held-out 비교

| 지표 | Development V1 | Held-out V1 |
|---|---:|---:|
| Admitted / complete P1 pairs | 64 / 64 | 200 / 200 |
| 평균 S0 Regret | 0.10085173 | 0.09343898 |
| 평균 Full Greedy Regret | 0.02564084 | 0.01860262 |
| 평균 P1 delta | +0.07521089 | +0.07483636 |
| 95% paired-t CI | [0.03222767, 0.11819410] | [0.05089822, 0.09877450] |
| 개선 / 악화 / 동률 | 14 / 1 / 49 | 45 / 1 / 154 |
| 평균 M4 Regret | 0.00292777 | 0.00398775 |
| 평균 Full Greedy Regret − M4 | +0.02271307 | +0.01461487 |

이 비교는 사전 승인된 동일 정의 아래 독립 코호트의 기술 비교다. 두 코호트를 합쳐 새 Primary를 만들지 않았다. M4는 Development 결과 확인 후 선택되었으므로 Held-out 방향이 같더라도 사후 선택된 Secondary라는 성격은 유지된다. Development는 64개 SCM, Held-out은 200개이며 Q-common 비율은 각각 18/64 (28.1%), 57/200 (28.5%)였다.

## 9. 실패, 자원 사용량 및 제한

평가 실패, shortfall, 중단, 재개 및 자원 제한 초과는 없었다. Proposal cap 1,104에 도달하기 전에 200 admissions를 확보했다(202 proposal). 승인 상한을 바꾸지 않았다.

| 자원 기록 | 관측값 |
|---|---:|
| End-to-end wall time | 276.64초 |
| Proposal-stage 누적 활성 시간 / stage wall | 114.56초 / 119.82초 |
| Proposal worker 최대 / RSS peak | 0.703초 / 71,520,256 bytes |
| Cohort ledger 누적 활성 counter | 264.02초 (초기 proposal 활성 시간 포함) |
| Cohort phase wall (run 생성→마지막 SCM 완료) | 156.65초 |
| SCM 활성 시간 최대 / 평균 | 0.958초 / 0.747초 |
| SCM sampled RSS peak | 70,815,744 bytes |
| 최대 결과 JSON 행 | 361,789 bytes |
| Cohort DB / proposal DB | 65,884,160 / 544,768 bytes |
| 전체 출력 디렉터리 | 66,428,930 bytes |
| 측정 시 남은 디스크 | 약 31.22 GB (29.1 GiB) |

`cohort_active_seconds`는 ledger의 누적 활성시간 counter이며, run 초기화 시 proposal 활성시간을 포함한다. 따라서 이를 phase wall time과 같은 시계로 해석하면 안 된다. Wall time, proposal 누적시간, cohort ledger counter는 서로 다른 운영 지표다. RSS는 주기 표본 관측값이지 OS 강제 메모리 quota가 아니다. 작은 합성 코호트 한 번의 관측은 다른 하드웨어나 장기 실행에서의 최악값을 보장하지 않는다.

## 10. 원본 경로·검증 명령·재현

최종 보고서 작성 전에 사용한 명령은 다음과 같다(기존 잠금 분석기, 원본 DB는 읽기 전용):

```powershell
python scripts/run_research_c_runner.py --mode preflight --approved-config C:/DAT_RESEARCH/research-c/approvals/heldout-v1-approved.json --execution-manifest C:/DAT_RESEARCH/research-c/approvals/heldout-v1-manifest.json
python scripts/run_research_c_runner.py --mode research --approved-config C:/DAT_RESEARCH/research-c/approvals/heldout-v1-approved.json --execution-manifest C:/DAT_RESEARCH/research-c/approvals/heldout-v1-manifest.json
python scripts/analyze_research_c_cohort.py --cohort-db C:/DAT_RESEARCH/research-c/heldout/independent-evaluation-20261123-seed-2026112303-v1/research_c_cohort.sqlite --proposal-db C:/DAT_RESEARCH/research-c/heldout/independent-evaluation-20261123-seed-2026112303-v1/research_c_proposal_stage.sqlite --approved-config C:/DAT_RESEARCH/research-c/approvals/heldout-v1-approved.json --manifest C:/DAT_RESEARCH/research-c/approvals/heldout-v1-manifest.json --bootstrap-seed 2026112302 --bootstrap-replicates 10000 --output C:/DAT_RESEARCH/research-c/analysis/heldout-v1-analysis-v1.json
```

Ledger 원본 무결성 감사는 별도 읽기 전용 검증 단계로 수행했고 그 결과를 위 integrity JSON에 보존했다.

원본 DB를 분석할 때 read-only/query-only 연결을 사용했고 분석 JSON은 별도 경로에 기록했다. 현재 실행 소스의 Manifest code hash map은 승인 Held-out Manifest와 일치하며, source commit/tree와 runtime fingerprint도 일치한다. Held-out은 한 번 실행되었고 재실행·재개하지 않았다. Development 원본·감사 기록, Step 4 및 연구 A/B frozen 자료는 변경하지 않았다. `.build_reframed/`도 건드리지 않았다.

## 11. 미검증 주장과 결론

이번 실행은 승인된 합성 모집단에서 P1 paired 평균 차이가 양수였고, 이 코호트에서는 Full Greedy의 평균 Regret이 S0보다 낮았음을 보인다. 154/200 SCM에서 P1 regret 차이는 동률이었으며, 그 동률은 모두 추천 행동이 같았다. M4의 낮은 관측 평균은 Development-selected Secondary 결과이며 일반 우월성의 증거나 새 Primary가 아니다. 결과는 실제 제조공정, 다른 SCM 분포, 관측자료 조건 또는 정답 DAG를 사용할 수 없는 환경으로 직접 일반화되지 않는다.

원시 데이터 변경, 분석 규칙 변경, 결과 기반 재추출은 없었다. Held-out V1 실행과 감사가 완료되었다. 후속 작업은 이 보고서와 원시 Ledger를 검토·보존하는 것이며, 추가 코호트 실행은 별도 승인 대상이다.

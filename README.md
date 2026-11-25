# DAT 제조공정 인과그래프 수리 연구

## 문제와 최종 연구 질문

이 프로젝트는 불완전한 인과그래프를 제한된 수정 예산으로 수리할 때, 어떤 구조 오류를 우선 고쳐야 downstream 의사결정 손실을 줄일 수 있는지 연구한다. 핵심은 그래프 정확도를 높이는 일과 실제 결정 품질을 높이는 일을 구분하는 것이다.

## 핵심 발견

1. 동결된 합성 계약의 독립 Held-out 200 SCM에서 B=2 Full Greedy는 S0보다 평균 Regret이 0.07483636 낮았다(95% paired-t CI [0.05089822, 0.09877450]).
2. 원본 Ledger 기반 사후 분석은 경로 가용성과 효과 방향이 일부 결정 차이를 설명함을 보였으나, off-task 수정도 경로를 만들거나 DAG 제약을 해소할 수 있었고 구조 수정 뒤 성능이 악화된 반례도 있었다.
3. Research D의 외부 반합성 단일 DRF 생성환경에서 같은 방향의 조건부 차이가 관찰됐지만, graph-free baseline은 Full Greedy와 같은 손실을 보였고 두 정밀도 목표도 충족되지 않았다.

## 세 증거 층위

- **Research C:** 사전 동결된 통제 합성 SCM 실험. Held-out 표본 단위는 독립 synthetic SCM 200개다. [계약](RESEARCH_C_EXPERIMENT_CONTRACT_V1.md) · [Held-out 결과](RESEARCH_C_HELDOUT_V1_RESULTS.md)
- **메커니즘 분석:** Research C 저장 Ledger를 이번 통합에서 read-only로 재검증한 사후 탐색 분석. 정창민의 PR #40 기여 및 커밋 이력을 보존한다. 재생성본의 SCM별 전체 결과는 원본과 완전 대조할 수 없었다.
- **Research D:** 공개 제조공정 기반 반합성 자료에 재적합한 하나의 DRF DGP, 고정 학습 프레임, 200 graph-corruption draws에 조건부인 강건성 평가. 실측 제조 개입이나 독립 외부 SCM 검증이 아니다.

## 결과 요약

| 분석 | 단위·대비 | 결과 | 제한 |
|---|---|---|---|
| Research C Held-out | 200 independent synthetic SCMs, B=2 S0−Full Greedy Regret | +0.07483636; 95% CI [0.05089822, 0.09877450] | 합성 계약 내 결과 |
| Research C M4 | B=2 평균 edit 수 | M4 .695; Full Greedy 1.435; 동일 행동 193/200 | Development-selected Secondary; edit count는 현장 비용이 아님 |
| Research D | 고정 DRF DGP·학습 프레임의 200 G0, B=2 S0−FG loss | +0.03422490; two-source CI [0.00617347, 0.06535080] | 단일 반합성 DGP; MC 정밀도 목표 미달 |
| Research D M4 / baseline | B=2 | M4−FG loss +0.00122956; 비용 .335 vs 1.160; graph-free loss=FG | M4의 trade-off와 baseline 동률을 함께 해석 |

## 주장 범위와 한계

Research C와 D는 모두 reference DAG를 활용한 oracle-assisted 구조 수리다. 현장처럼 참 구조를 모르는 상황의 오류 발견을 해결하지 않는다. D의 200개는 독립 SCM이 아니라 하나의 DGP에서 뽑은 graph-corruption draw다. 어느 실험도 실제 공장 개입, 안전성, 실제 전문가 시간·금전 비용, 배포 가능성을 입증하지 않는다. M4의 보편적 우월성 및 graph-based 방법의 보편적 우월성은 주장하지 않는다. 수치와 주장별 근거·반례는 [최종 결과표](research/final_integration/FINAL_RESULTS_TABLES.md), [주장–근거 매트릭스](research/final_integration/FINAL_CLAIMS_EVIDENCE_MATRIX.md), [최종 보고서](research/final_integration/FINAL_RESEARCH_REPORT.md)에 있다.

## 저장소 구조와 재현성

- Research C 계약·결과: 루트 `RESEARCH_C_*.md`, `research/original_objective/`.
- Research C 메커니즘: `research/research_c_mechanism_analysis/`.
- Research D 조사·실행 산출물: `research/external_validation/`.
- 통합·발표 자료: `research/final_integration/`.
- 현재 운영 현황: `docs/research_state_current.json`, `docs/current/`.
- Research C 원본 SQLite와 Research D raw response vectors 및 fitted native object는 공개 저장소에 없다. 보존한 hash와 aggregate는 출처·무결성 확인에 쓰이며, 공개 저장소만으로 원자료 전체 재실행을 보장하지 않는다.

새 연구 실행은 승인된 계약과 별도 권한을 요구한다. 이 통합은 새로운 SCM, 평가 표본 또는 물리 실험을 만들지 않는다. 재현·보존 원칙은 [AGENTS.md](AGENTS.md), [CONTRIBUTING.md](CONTRIBUTING.md)를 따른다.

## 팀

- **오성민:** 연구 설계·실험·통합 및 Research D; 최종 보고와 발표 조율.
- **정창민:** Research C M1–M4 메커니즘 분석 및 PR #40.
- **황주희:** 기존 기록에서 확인된 기여만 보존한다. 발표 준비 우선 기록은 있으며, 미확인 과거 연구 기여를 새로 귀속하지 않는다.

세부 인수인계와 발표 준비는 [팀 인수인계](RESEARCH_JOURNEY_AND_TEAM_HANDOFF.md), [기여·발표 체크리스트](research/final_integration/TEAM_CONTRIBUTION_AND_HANDOFF.md)를 참조한다.

## 과거 연구 및 실측 검증 상태

프로젝트는 TEP 구조 탐색과 인과발견 비교에서 출발했다. TEP 및 CausalMan 환경은 연구 계약에 필요한 reference/intervention 조건을 충족하지 못해 보류되었고, Causal Chambers의 Mk2/Wind Tunnel도 현재 연구 질문에 적합한 실측 정책 비교로 채택되지 않았다. 해당 이력은 제거하지 않고 `docs/research_design/`과 `research/external_validation/`에 보존한다. 이번 최종 연구는 실측 제조 검증이 아니다.

> 통합 브랜치의 PR/merge 상태는 GitHub에서 확인한다. 문서 작성 시점의 main 상태를 과거 Research C 병합 이전으로 표현하지 않으며, 최종 통합 PR의 결과는 실제 원격 상태 확인 뒤 current dashboard에 기록한다.

# 원 연구 복원 설계 — 결정 등록부

**상태: 검토 목록. 모두 OPEN / 미승인. 본문은 사용자의 결정을 대신하지 않는다.**

| ID | 결정 항목 | 제안 후보 | 미결 영향 | 상태 |
|---|---|---|---|---|
| D1 | Task zone causal | 정답 X→Y directed paths의 edge union | 과제 경로 정의 | OPEN |
| D2 | Backdoor zone | 빈 conditioning에서 open backdoor vs 모든 X-in 단순 path vs 별도 conditioning set | collider 및 confounder 귀속이 달라짐 | OPEN |
| D3 | FP assignment | A: zone 내부 node-pair; B: A + 사전 정의 route-creating boundary FP | M2/M4 분자·분모·대상오류 집합 변화 | OPEN |
| D4 | M1/M2 denominator | M1 reference non-task adjacency; M2 current predicted non-task adjacency | M2는 true adjacency 추가로 분모만 증가해 rate 개선 가능 | OPEN |
| D5 | M3 reporting | conditional orientation accuracy + unresolved rate/count 동시 보고 | unresolved 분모 원문 모호; rate와 policy utility 구분 | OPEN |
| D6 | M4 output | FN/FP/REV/UNRES vector, per-component support | Scalarization 필요 시 `β` 및 normalization 요구 | OPEN |
| D7 | Shared greedy utility | subset metric mean of baseline-denominator event burden gains / edit cost | M3 proxy, M4 β, M1/M2 support, cross-metric equal weights 필요 | OPEN |
| D8 | Greedy vs quota | Shared cost greedy 후보; equal edit-count quota comparator | Winner/primary schedule 및 quota slot/transfer 규칙 | OPEN |
| D9 | Cost units | `c_add=c_del=c_ori=1` baseline; c_ori ratio 1/2/3 sensitivity | resolve/unresolved operation type costs 미정 | OPEN |
| D10 | Residual penalty | event-level `w_r×zone factor` once + explicit unresolved penalty | λ total vs incremental, unresolved, M4 α double count | OPEN |
| D11 | Weights | initial equal weights + λ=1 reference scenario candidate; DOCX sensitivity preserved | not empirical; training split and uncertainty needed | OPEN |
| D12 | ρ | cost–penalty curve as auxiliary | units and interpretation depend on scale | OPEN |
| D13 | Catalog comparison | minimum among 16 as catalog-relative; no global claim | exhaustive edit-sequence oracle would be separate policy | OPEN |
| D14 | Information access | Oracle-assisted structural diagnosis; non-oracle separate work | deployability and oracle knowledge differences | OPEN |
| D15 | Data separation | weight/policy development distinct from untouched evaluation | new sample and sample/statistical plan needed; Step5/6 unavailable as untouched | OPEN |
| D16 | Outcome link | evaluate Decision Regret separately from structural penalty | no equivalence assumed; new independent data required | OPEN |

## 고정 보호 원칙 (설계 원칙이지 새 연구 승인 아님)

- M1 비과제 누락률, M2 비과제 허위 연결률, M3 비과제 방향 정확도와 미확정률, M4 task-zone error vector를 유지한다.
- 15 nonempty metric subset + S0 no-edit 유지; 기존 FN/FP/REV 14 order policies로 치환하지 않는다.
- 수정비용 `C`, 잔존 구조벌점 `P`, downstream Decision Regret `R`을 별도 quantity로 둔다.
- GT effect/loss/regret은 수정 후보·priority·weight를 정하지 않는다.
- 구조적 관련 tag는 실제 causal decision damage와 동일시하지 않는다.
- 기존 Step4 FROZEN, Step5/6 결과·원시자료·발표물은 immutable이며 새로운 코호트/SCM/Regret은 이 단계에서 만들지 않는다.
- 사용자 승인 및 별도 preregistration 전까지 모든 numerical choices OPEN이다.

## 다음 Gate 전 필요한 결정 순서

1. D1–D5: task zone, FP assignment, denominator, unresolved handling.
2. D6–D8: M4/M3 utility, normalization, scheduling policy/ties/quota comparator.
3. D9–D12: operation costs, penalty mapping, weight/λ/ρ grid and training provenance.
4. D13–D16: catalog/oracle labels, information firewall, independent evaluation and sample/analysis contract.

이 등록부는 사전등록이 아니며 정책 코드나 실제 연구 실행을 승인하지 않는다.

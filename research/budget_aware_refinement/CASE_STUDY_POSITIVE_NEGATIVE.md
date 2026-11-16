# Step 6 사례 연구: 수정 위치에서 regret까지

이 두 사례는 모집단을 대표하는 예시로 선정된 것이 아니라, 관찰된 양·음의 극단값을 원시 기록에서 설명하기 위한 사례다. 코드 실행, 값 재계산, 표본 선택 변경은 하지 않았다. 제시된 값은 confirmation raw ledger의 stage 결과를 그대로 읽은 것이다.

## 사례 1 — `confirmation-proposal-000238`: Task-Focused가 유리

**설계 정보:** 7노드 `multiple_directed_paths`; Action V04, Target V02; delta −1; SCM `rep-scm-confirmation-proposal-000238-a0000`. 정답 주요 간선은 V04→V03, V03→V02, V04→V06, V06→V02다. 따라서 Action에서 Target까지 두 간접 경로가 있다.

### FN

FN 후보 누락은 V03→V01과 V04→V03이었다. 두 번째 간선은 과제의 두 경로 중 하나에 직접 놓인다. B=1에서 ID-ordered Global은 `[FN, V03, V01]`을 복구했고 Task-Focused는 `[FN, V04, V03]`을 복구했다. 이 정책 순서 차이는 선택 `k`로 이어졌다.

| 정책 | 선택 편집 | 예측 목표 평균 | 선택 k | 선택 k의 GT loss | 최적 격자 k/loss | regret |
|---|---|---:|---:|---:|---:|---:|
| Global | V03→V01 복구 | −0.001810 | +1 | 1.469444 | −1 / 0.554824 | 0.914621 |
| Task-Focused | V04→V03 복구 | −0.058987 | −1 | 0.554824 | −1 / 0.554824 | 0 |

### FP

후보 FP는 V05→V00 및 V04→V05였다. 두 정책 모두 V04→V05를 제거했고 선택 `k=−1`, regret 0으로 같았다. 같은 SCM 안에서도 오류 유형별 정책 차이가 없을 수 있다.

### REV

오류 방향은 V01→V05 및 V02→V03이었다. 정답 방향은 각각 V05→V01 및 V03→V02. Global은 V01→V05를 반전했지만 Task-Focused는 과제 경로에 있는 V02→V03을 반전해 복구했다. Global은 `k=+1`, Task-Focused는 `k=−1`을 선택했다. 각 regret은 FN과 동일하게 0.914621 대 0이었다.

세 유형 차이는 `(0.914621 + 0 + 0.914621)/3 = 0.609747`로 SCM composite와 일치한다. 이 사례는 Task-Focused의 전체 보편 효과를 뜻하지 않는다. 이 SCM의 관측 자료·계수·후보 격자 조건에서 편집 ordering, Ridge 추천 및 analytic GT loss가 연결된 한 예다.

## 사례 2 — `confirmation-proposal-000606`: Global이 유리

**설계 정보:** 8노드 `observed_common_cause`; Action V03, Target V02; delta −1; SCM `rep-scm-confirmation-proposal-000606-a0000`. 정답 과제 경로는 V03→V04→V02와 V03→V06→V02이며 V05는 V03와 V02의 공통 원인이다.

### FN

후보는 V04→V02와 V05→V03. 두 정책 모두 V04→V02를 복구했고 같은 `k=−1`, regret 0.434361을 냈다. 이 최적화 grid에서는 참 최선 `k=+1`, loss 0.700153보다 선택 loss 1.134514가 컸다.

### FP

오류 간선은 V01→V02와 V01→V06이었다. 두 정책 모두 첫 간선을 제거했고, 같은 `k=−1`, regret 0.434361이었다.

### REV — 음의 정책 차이의 원인

잘못된 방향 V01→V04와 V06→V03의 정답은 각각 V04→V01과 V03→V06이다. 두 번째는 V03→V06→V02 과제 경로 위에 있다. Global은 V01→V04를 반전하고 `k=+1`을 추천했다. Task-Focused는 V06→V03을 반전해 과제 경로를 복구했지만 `k=−1`을 추천했다.

| 정책 | 선택 편집 | 선택 k | 선택 k의 GT loss | 최적 격자 k/loss | regret |
|---|---|---:|---:|---:|---:|
| Global | V01→V04 반전(정답 V04→V01) | +1 | 0.700153 | +1 / 0.700153 | 0 |
| Task-Focused | V06→V03 반전(정답 V03→V06) | −1 | 1.134514 | +1 / 0.700153 | 0.434361 |

SCM 차이는 `(0 + 0 − 0.434361)/3 = −0.144787`로 composite와 일치한다. 이 반례는 구조적으로 과제 경로에 더 가까운 편집을 했더라도 해당 계수·공통 학습자료 아래의 추정 및 선택이 더 좋은 GT 손실을 보장하지 않음을 보여준다. 정책 순서가 결과에 작용한 기전의 사례이지, 반대 정책이 일반적으로 우월하다는 근거는 아니다.

## 원시 근거

각 사례는 `C:\DAT_STEP6_RUNS\step6-confirmation-v1\ledgers\rep-scm-confirmation-proposal-000238-a0000.jsonl` 및 `...000606-a0000.jsonl`의 `proposal`, `scm`, `error_graphs`, `policy_graphs`, `recommendations`, `gt_evaluation`, `composite` 이벤트에서 확인했다. Proposal 238은 admission ordinal 53, proposal 606은 175이며 Registry에 기록된 delta는 둘 다 −1이다. 분석 요약 CSV는 `research/budget_aware_refinement/step6_confirmation_v1/STEP6_CONFIRMATION_SCM_SUMMARY.csv`다.

확인 시 파일 크기와 SHA-256: proposal 238, 103,384 bytes, `45ba97a12f5f565b85304b6cc79830f3571ae9de1befa253834ab16dfbbcf121`; proposal 606, 114,489 bytes, `0a4a488a9da5b1b26da4916fd8086a401aeb32a513b2d35ff916ff3914f2d913`.

전체 간선·계수/표본 값을 모두 본문에 복사하지 않았다. 그림은 과제 관련 경로와 각 정책의 선택 편집만 강조한다. 주변 구조가 생략되어 있으므로 전체 DAG 재현도라고 해석하지 않는다.

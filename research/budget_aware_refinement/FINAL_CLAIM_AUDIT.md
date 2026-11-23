# Step 8 최종 주장 감사

판정 목적: 보고서·발표에서 주장 범위를 원자료와 동결 프로토콜 안으로 제한한다. Step 5/6 데이터는 읽기 전용으로 사용했다.

| 문장/주장 | 상태 | 근거 및 필요 문구 |
|---|---|---|
| 두 코호트에서 평균 D가 양수였다. | 허용: 기술적 사실 | Step 5 n=64 mean .0146605, Step 6 n=200 mean .0200725. “확인적 우월성”을 덧붙이지 않는다. |
| Task-Focused가 전반적으로 우월하다. | 불허 | Option B는 superiority/equivalence inference를 보류. 평균은 희소 동률과 극단값에 민감하다. |
| 재현 코호트 대부분에서 Task-Focused가 이겼다. | 불허 | Step 6 positive 25/200, negative 8/200, exact zero 167/200. 평균 부호와 승리 빈도는 다르다. |
| 독립 재현이 됐다. | 한정 허용 | 독립 namespace, proposal/SCM ID 및 RNG keys의 중복 없음, 별도 cohort에서 계약대로 실행. “확증적 통계 재현” 또는 “우월성 확증”을 뜻하지 않는다고 함께 쓴다. |
| 서로 다른 그래프는 다른 결정을 만든다. | 불허 | Step 6에서 그래프는 FN/FP/REV 76/109/93건 달랐지만 selected k는 14/3/25건만 달랐다. |
| Action 일치가 Task-Focused 성과를 지지한다. | 불허 | Action은 같은 task pair에서 사전 고정되어 200/200 일치. 성능 증거가 아니다. |
| Task-Focused가 중요 경로 오류를 고치면 regret이 낮아진다. | 과도 일반화 불허 | proposal 238의 사례는 이를 보인 한 케이스. proposal 606 REV는 경로 간선 복구에도 regret이 더 커진 반례다. |
| REV는 FN보다 중요하다 (또는 그 반대). | 불허 | 최고 유형 평균은 개발에서 REV(.03816), 재현에서 FN(.03077)으로 달랐다. 유형은 SCM 내부 반복 측정이며 하위그룹 검정이 아니다. |
| 어떤 구조 점수가 최선인지 밝혀졌다. | 불허 | 원 연구의 metric prediction question과 Step5/6 ordering question은 다른 추정 대상이다. 후속 안정적 incremental prediction은 미확립. |
| 본 결과가 제조 복구·안전·경제 효익을 보여준다. | 불허 | 실제 제조 intervention/recovery/safety/economic outcomes는 실행하지 않았다. |
| Step 6 max 사례는 일반적 결과다. | 불허 | 최대 D=.6097471 사례는 설명용 극단 사례이며 모집단 대표 표본이 아니다. |
| Oracle repair 실험이 실제 오류 탐지 시스템을 검증한다. | 불허 | 알고리즘은 주어진 정답 기반 오류 후보 중 ordering을 비교한다. 후보 발견 성능을 평가하지 않았다. |

## 수식과 분모 점검

- `D_i,type = Regret_Global,type − Regret_TaskFocused,type`.
- SCM `D_i`는 세 유형 차이의 고정 동일 가중 평균. 한 SCM의 세 오류 유형은 반복 측정이다.
- regret 자체는 같은 GT의 고정 후보 격자 최솟값 대비 정책 선택 GT loss로 정의되므로 0 이상이다. 정책 간 차이는 양·음·0 가능.
- Step5/6의 n=64/200은 별도 코호트 admission이자 완전 결과 수다. 두 개를 합쳐 새 확인 n=264로 세지 않는다.
- 동일 action + 동일 k이면 같은 GT action과 같은 grid/target/scale 아래 같은 GT loss다. k가 다르더라도 손실이 반드시 달라지는 것은 아니므로 일반적으로 역방향 함의를 주장하지 않는다.

## 원시 사례 대조

Raw ledgers:

- `rep-scm-confirmation-proposal-000238-a0000.jsonl`
- `rep-scm-confirmation-proposal-000606-a0000.jsonl`

Step 6 디렉터리 외부 경로는 `C:\DAT_STEP6_RUNS\step6-confirmation-v1\ledgers\`이다. 두 파일에서 proposal/SCM, 오류 후보, Global/Task-Focused edit sequence, recommendations, GT evaluation 및 composite 이벤트를 대조했다. 사례 문서의 type differences `[0.9146206785, 0, 0.9146206785]`와 `[0, 0, -0.4343606576]`는 composite `.6097471190` 및 `-.1447868859`와 일치한다.

## 재현 및 파일 무결성

- 기존 inventory 대조 및 CSV 재집계 기록: `STEP5_STEP6_CROSS_CHECK.md`.
- 그림은 `scripts/render_step8_figures.py`로 요약 CSV 및 명시적 원시 사례 추출을 시각화했다. 새로운 결과 계산/SCM은 생성하지 않는다.
- SVG 원본은 `figures/step8_*.svg`에 있으며, PNG/PDF 변환은 이번 범위에서 하지 않았다.

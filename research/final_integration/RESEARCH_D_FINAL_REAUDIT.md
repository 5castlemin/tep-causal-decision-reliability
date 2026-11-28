# Research D Final 저장 산출물 독립 재감사

감사일: 2026-11-26. 최종 Research D 실행이나 평가 표본 생성은 재수행하지 않았다. 기존 로컬 evaluator-only artifact, recommendation, response vector만 read-only로 사용했다.

## 실행 원본과 산출물

- 실행 source commit/tree: `a6d751e3f157fca63a93931d62b9f7a9318c6cb5` / `fa1aaf635518e6d7a1f292f410185d220ccacc99`.
- Run ID: `rd-external-final-20261125-01`.
- causalAssembly 1.2.1, pinned commit `8da3729e6383f0e1cbe7740bb6ab7ac4977ac7f9`; sample/reference hashes는 [public execution manifest](../external_validation/semisynthetic_final/final_public_execution_manifest.json)에 기록되어 있다.
- 최종 수량: 고정 training frame 512행, 신규 G0 200개, recommendation 17,000건, action 5개×2,500 response rows = 12,500행.
- 저장된 recommendation lock·execution manifest·evaluation manifest·response vector 및 analysis hash를 감사기가 재검증했다.

## 재감사 실행

명령 형식:

```powershell
& <Research-C-readonly-Python> research/external_validation/semisynthetic_final/audit_final_artifacts.py `
  --external-root <local-evaluator-only-final-run> `
  --repo-root <Research-D-repository> `
  --output <external-local-audit-output.json>
```

완료된 출력은 `status=PASS`, 27/27 checks, 실패 0, Primary 재계산 `0.03422489689372574`였다. 이 read-only 재감사 JSON의 SHA-256은 `6fa458199ea814a61248a1088bbe5a3b96a586916516c02a1dd6b54c0331292b`이다. 원시 response values와 개인 로컬 경로는 저장소에 복사하지 않았다.

검증 범위에는 17,000개 unique recommendation key, 85개 정책×예산 집계, 다섯 response vector의 2,500 finite float64 값과 file hash, bias-corrected action loss, Primary/Secondary, edit cost, saved interval binding, source code·contract·manifest 및 표본 수가 포함된다.

## 재검증 결과 및 제한

Primary B=2 `L(S0)−L(Full Greedy)=+0.0342248969`. 95% 구간은 G0-only `[0.02664478, 0.04180501]`, Action-MC-only `[0.00650999, 0.06284998]`, two-source `[0.00617347, 0.06535080]`. MC-only 반폭 목표 0.020 및 combined 반폭 목표 0.025는 충족하지 못했다. 후속 표본 확장은 승인되지 않았고 수행하지 않았다.

M4−Full Greedy 평균 손실 대비는 `+0.00122956`; 두-source 구간 `[0.00000000, 0.00391596]`. 평균 수정 횟수는 M4 `0.335`, Full Greedy `1.160`; 동일 행동 198/200. Graph-free association baseline의 loss `0.789362`는 Full Greedy와 같았다. 이 baseline은 관측 연관성 추천이지 인과효과 추정기가 아니다.

이 결과는 하나의 고정 DRF DGP와 고정 학습자료에 조건부인 reference-relative semisynthetic robustness evidence다. 물리 제조 개입, 완전한 physical GT, 200개 독립 SCM, 제조 모집단 일반화를 뜻하지 않는다. 외부 DGP 재적합·원자료·training-frame 변동은 추론에 포함되지 않았고 resource monitor는 2초 간격 process-tree RSS 표본 감시였다.

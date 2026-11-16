# Step 4B-4 statistical calibration v2

**판정: IN_PROGRESS. 주 평균 추론법을 채택하지 않는다.** 기존 v1 JSON은 보존했다. v1의 `alt_ci_coverage_at_mean_0_10`는 CI에 0이 포함되는지 검사해 참평균 0.10의 coverage가 아니었다. 수정 runner는 null CI를 true mean 0과 비교하고 shifted alternative CI를 true mean 0.10과 비교하며, 0 기각 비율을 별도 저장한다.

설정 SHA-256 `956c4dbc2b0fa2eef177358f05bfdca6859c949636d8bb32548e13f788100a63`. 2 seeds × 20,000 replicates × scenario/n, n=[34, 64, 100, 200], alpha=.05 two-sided, shift=.10. Abstract SCM-level paired differences only; no SCM, data, effects or regret.

## 계산 오류와 퇴화 표본

- Coverage는 각 분포의 참평균과 CI를 비교한다. 검정력은 대안에서 H0 mean=0을 기각하는 비율이다.
- Exact constant 표본은 point CI와 `degenerate_zero_variance`로 표시한다. 이를 일반적인 유효 추론으로 보지 않는다. 0 상수는 기각하지 않으며, 비영 상수는 기계적으로 기각하더라도 표본만으로 모집단 퇴화를 입증하지 못한다.
- Exact elementwise equality로 상수 행을 탐지해 1e-14 동일값의 NumPy 표준편차 반올림(약 1e-30)을 0으로 분류한다. 작은 양의 분산은 그대로 계산하고 near-zero 상태로 따로 표시한다.
- df=199 t critical은 1.9719565이며 테스트에서 확인한다.

## n=200 결과 (seed 4042026)

| 분포 | Type I | H0 CI coverage | power (delta=.10) | H1 CI coverage | null CI 폭 평균 |
|---|---:|---:|---:|---:|---:|
| normal | 0.0503 | 0.9496 | 0.2944 | 0.9496 | 0.27841 |
| zero_heavy_symmetric | 0.0493 | 0.9507 | 0.2939 | 0.9507 | 0.27814 |
| zero_heavy_skewed | 0.1363 | 0.8637 | 0.4097 | 0.8637 | 0.26159 |
| rare_symmetric_extremes | 0.0145 | 0.9855 | 0.3947 | 0.9855 | 0.25023 |
| cancellation | 0.0479 | 0.9521 | 0.2871 | 0.9521 | 0.27883 |
| rare_large_loss | 0.0563 | 0.9437 | 0.3674 | 0.9437 | 0.44536 |
| near_degenerate | 0.0518 | 0.9482 | 1.0000 | 0.9482 | 0.00000 |
| degenerate_zero | 0.0000 | 1.0000 | 1.0000 | 1.0000 | 0.00000 |

zero-heavy skew의 이론 평균 0, 분산 1, 왜도 약 -8.43. 독립 seed 4042026 / 918273645에서 Type I 0.13635 / 0.13415, 참평균 CI coverage 0.86365 / 0.86585, 표본평균 평균 0.000237 / -0.000212, median SD 0.9969였다. Type I Monte Carlo SE는 각각 약 0.00242이다. 따라서 이 결과는 .05 주변의 Monte Carlo 흔들림이 아니다. 임계값 구현 오류가 아니라 심한 왜도·희소 tail에 대한 finite-sample t 보정 실패다.

n=200 studentized/bootstrap-t CI coverage는 skew .855, rare-large-loss .745였으며 rare-loss 재표본의 50.2%에서 bootstrap t 구간이 unbounded였다. Percentile bootstrap coverage는 각각 .867과 .946. 대칭·정규 조건에서의 양호한 수치만으로 실제 대상의 분포 가정을 정당화할 수 없다.

Chebyshev(알려진 시나리오 분산)와 Hoeffding(알려진 시나리오 범위) 구간은 시뮬레이션에서 보수적으로 덮었지만 zero-heavy skew n=200 반폭이 각각 .316 및 1.012였다. 실제 regret 차이의 알려진 분산 상한이나 유한 범위는 아직 없다. 따라서 둘 다 현재 확인 분석용으로 쓸 수 없다. Sign/Wilcoxon 검정으로 평균 추정량을 대체하지 않는다.

**판정:** paired t, percentile bootstrap, bootstrap-t, sign-flip, sign, Wilcoxon 어느 것도 주 평균 추론법으로 선정하지 않는다. 추정 대상은 유지하되, 과학적으로 정당한 tail 가정/범위 없이 추론법을 확정하지 못했다. .10은 표준화 제곱손실 척도의 연구자 정의값이지 산업 절감률이 아니다.

# Wind Tunnel block 및 action support 감사

## 출처 및 검사 경계

재사용 파일 `work/data/wt_bernoulli_v1.zip`은 14,047,460 bytes, SHA-256 `e5d58a67f6307b9099177425e91c449b9e62e7c712f8c6f34d1dc80ce4db01e3`로 Step 0 manifest와 일치하며 CC-BY-4.0 공개 물리 측정 자료다. 재다운로드하지 않았다. 파일 검사는 allowlist 열 `timestamp, config, counter, flag, intervention, load_in, load_out, hatch`로만 수행했다. Y 또는 다른 반응 컬럼의 값/평균/요약은 열람하지 않았다.

## 프로토콜 대비 실제 기록

공식 [random_loads_intake.py](https://github.com/juangamella/causal-chamber/blob/c2b307036446b8d3ca173e9f41ff465b7111819a/datasets/wt_bernoulli_v1/generators/random_loads_intake.py)는 RNG seed 42, `load_in ~ Uniform(0,1)`의 두 자리 반올림, 각 block `flag=i`, `WAIT,8000`, `MSR,100,0`, N=2,000을 정의한다. 19개 고정 설정을 먼저 쓰며 여기에는 `load_out=0.1`, `hatch=0`이 포함된다. 프로토콜상 8초 대기는 stabilise 의도이나 실제 정상상태 증거가 아니다.

| 검사 | 직접 파일 결과 |
|---|---:|
| CSV 크기 | 200,000 행 × 37 열 (기존 스키마 검사) |
| flag 그룹 | 2,000개, 순서대로 0–1,999 |
| 각 배정 block 행수 | 정확히 100, 전부 |
| block 내부 load_in 일관성 | 2,000/2,000 |
| NumPy default_rng(42) 재현 | 두 자리 값이 모든 2,000 block에서 일치 |
| config / 배경값 | `standard` 200,000; `load_out=0.1`, `hatch=0` 유지 |
| intervention 표식 | 1인 행 2,000개, 각 block 첫 행; 나머지 198,000은 0 |
| timestamp | 기존 검사에서 유일·증가; 연속 간격 중앙값 0.1515초, 99분위 1.2257초, 최댓값 9.3220초 |
| block 경계 시간차 | 8.2521–9.3220초; wait 프로토콜과 일치하는 정황이나 reset/settling 입증 아님 |
| counter | 중복/비단조 특성 있음; 유일 독립 단위 식별자로 사용할 수 없음 |

아카이브의 배정열은 공식 RNG와 일치한다. `intervention=1` 표식이 각 block 첫 행과 일치하는 점은 SET이 block 시작에 대응한다는 강한 파일 내부 정황이다. 그러나 row-level firmware actuation timestamp, MSR의 개별 시점, 계측이 명령 전/후 어떤 물리 상태를 포착하는지는 공개되지 않았다. 100개 연속 센서 행은 100개 독립 배정이 아니다.

## 제안 행동 지원(결과 열람 없이)

공식 grid는 0.00–1.00, 0.01 간격이다. 예시 5-arm `{0.10,0.30,0.50,0.70,0.90}`는 block 수가 각각 24, 23, 20, 12, 18이다. 이 수는 전체 파일에서의 배정 횟수이며 독립 세션 수나 train/evaluation 분할 후 support가 아니다. 행 단위 분할은 금지다. 시간/flag 경계를 보존한 block 분할 후에는 arm별 block 수가 더 작아진다. 난수실험이라 arm-mean 학습 baseline에 적합할 가능성은 있지만, 특정 5-arm은 개발·평가 분할, 정밀도 요구 및 최소 독립 block 기준을 사전 설정한 뒤에만 확정할 수 있다.

2,000 block은 한 실험 archive 내 순차 배정이며 2,000 장치 또는 독립 세션이 아니다. 장치, 날짜, session ID, reset 및 중단/재시작 정보는 파일에서 확인되지 않는다. 결과에 따른 임의 arm 선택은 없었다.

## 후속 요구

평가 전에 split 경계와 temporal buffer 규칙, 허용 행동 grid, 각 split의 block support를 결과-blind 검사로 동결해야 한다. 보수적인 buffer 크기 및 의존성 추론 모델은 반응값/개발 진단의 별도 승인 뒤 정한다. archive가 공개 논문 benchmark 자료이므로 새로 수집한 미열람 외부 held-out이라고 부를 수 없다.

# 연구 주장–근거–반례 매트릭스

| 주장 | 검증 질문/실험 | 근거 수치 | 재현·반례 | 증거 수준 및 허용 해석 | 금지되는 해석 | 근거 파일 |
|---|---|---|---|---|---|---|
| A. 전체 구조 점수가 같아도 결정 손실이 다를 수 있다 | 초기 synthetic controlled-error에서 구조 점수 동점 graph 쌍의 추천·손실 비교 | 과제 핵심–주변 162쌍: 핵심 오류 쪽 손실 큼 93, 작음 4, 동률 65. 경로 유지 114쌍 중 48/3/63 | 반대 방향 사례와 동률 다수 존재; 162쌍은 독립 공정 아님 | 존재 증거: 같은 점수만으로 같은 손실을 보장할 수 없음 | 구조 점수는 무의미하거나 항상 결정 성능을 설명 못 한다 | `docs/research_design/SYNTHETIC_FINAL_RESULTS_AND_CLAIMS.md` |
| B. 그래프 수정 결과가 달라도 조작 결정이 같을 수 있다 | Step 5/6 paired 정책 출력 비교 | Step 6 그래프 다름 FN/FP/REV 76/109/93; Action 일치 200/200, k 차이 14/3/25 | Step 5도 Action 64/64 일치; k 차이는 FN3, FP0, REV5 | 두 출력 단계가 다름을 직접 관찰 | 그래프 차이가 반드시 결정 또는 regret 차이를 만든다 | Step 5/6 regret analysis |
| C. 일부 SCM에서 수정 우선순위가 regret을 바꾼다 | 같은 SCM의 같은 유형에서 정책 순서 대응 | Step 6 SCM 차이 양수 25, 음수 8, 0 167; Step 5 양수 6, 음수 1, 0 57 | 대부분 동률; Global이 유리한 음수 사례 존재 | 이 합성 조건에서 일부 SCM의 선택 차이가 regret 차이를 만들 수 있음 | Task-Focused가 보편적으로 이긴다 | Step 5/6 SCM summaries |
| D. 두 코호트에서 평균 차이 양수 방향이 재현됐다 | 분리된 development/confirmation namespace 기술 평균 | Step 5 0.0146605 (n64), Step 6 0.0200725 (n200) | 둘 다 median 0; Step 6 음수 8개; 극단값 민감성 | 방향 유사한 기술적 재현 | 확인적 복제, 통계적으로 유의한 우월성, N=264 합산 | cross-cohort report; frozen Option B |
| E. Task-Focused 이점은 대다수 SCM의 보편적 개선이 아니다 | SCM 차이의 부호와 동률 분포 | 동률 57/64 및 167/200; Step 6 양수 25, 음수 8 | 평균 양수는 일부 양의 차이로 생성; top two가 합의 29.4% | 분포의 희소성과 이질성 | 모든/대부분 공정에서 개선 | Step 5/6 regret analysis |
| F. 오류 유형 상대 중요성은 코호트마다 달라졌다 | 유형별 평균 D 기술 비교 | 개발 REV .03816 > FN .00583 > FP 0; 재현 FN .03077 > REV .02727 > FP .00218 | 반복 측정이고 표본 내 구조/변동; 순위는 기술적 | 관측된 유형별 기술 패턴이 동일하지 않음 | FN 또는 REV가 일반적으로 가장 중요 | cross-cohort comparison |
| G. 최우수 구조 지표는 확정되지 않았다 | 기존 metric prediction 연구의 독립/후속 비교 | 확인 당시 경로 대 연결 ΔMAE .014264, 95% 구조 bootstrap [.002912,.025278]; 이후 이론 민감도 .006317 [−.004227,.017585], 개발 incremental 경로 ΔMAE .005200 [−.005155,.014421] | 정의·자료·검증 버전이 다름; 후속은 안정적 추가 예측력 미확립 | 초기 증거는 경로의 제한적 대체 예측력 지지, 증분 우월성은 미확립 | 현재 Step 5/6 정책 결과가 경로 지표 우월성을 입증 | `SYNTHETIC_FINAL_RESULTS_AND_CLAIMS.md`; `PATH_METRIC_INCREMENTAL_VALIDATION_REPORT.md` |
| H. 실제 제조공정 효과는 검증되지 않았다 | TEP 구조 자산과 합성 SCM 실험의 범위 감사 | 실제 공정 intervention/recovery/safety/economic outcome 실험 0 | TEP 자료 구조 채점은 합성 SCM의 hard-do 결과와 동일 생성환경을 보장하지 않음 | 범위 제한에 관한 직접 사실 | 실제 DAT 개선·안전·수율 향상 | `RESEARCH_DESIGN.md`; `RESEARCH_COMPASS.md`; `STEP4_FROZEN_PROTOCOL.md` |

## 공통 해석 규칙

- 양수 `D`는 정의된 손실·부호에서 Task-Focused regret이 낮다는 뜻이며, 산업적 이득의 크기와 같지 않다.
- 동일 Action은 task가 고정된 대응 설계의 결과다. 같은 Action과 같은 `k`이면 공통 GT 평가에서 손실이 같다.
- Step 5/6는 서로 다른 코호트다. 합쳐 독립 n=264로 만들지 않는다.
- Option B는 확인적 우월성·동등성 주장을 보류한다. 참고용 가정 기반 CI도 확증으로 사용하지 않는다.
- Oracle 기반 오류 후보가 주어졌으므로 정책은 오류 발견기를 평가하지 않는다.

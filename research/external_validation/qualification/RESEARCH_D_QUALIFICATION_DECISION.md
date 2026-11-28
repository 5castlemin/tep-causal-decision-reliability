# Research D Step 1 적격성 판정

일자: 2026-11-25. 기준: Step 0 audit branch commit `89a49224a997f33aee5a5075842144df48e39d45`; Step 1은 그 commit을 부모로 한 별도 작업 branch에서 진행.

## 요약 판정

**ELIGIBLE_CONDITIONAL_PHYSICAL_CASE**, 단 조건부 물리 사례 후보로만 적격하다. Light Tunnel Mk2 `lt_spice_v1`는 실제 물리 장치에서 생성된 공개 자료이며, 생성기의 배정 명령과 CSV 열 순서는 재현·대조됐다. 하지만 완전한 GT DAG/strict indirect-only 비간선, 명령 적용과 센서 측정의 행별 시간 정렬, 독립 세션/장치 복제는 확인되지 않았다. 이 세 조건은 기존 Research C의 정확한 외부 확증을 막는다. reference-relative/제한 부분참조와 새 평가 계약을 선택한다면 특정 configuration 내 기술 사례 또는 제한된 정책 비교 가능성은 남아 있다.

| Gate | 판정 | 요지 |
|---|---|---|
| A 출처/권리 | PASS (Step 0 evidence unchanged) | 공식 v1 ZIP, CC-BY-4.0, 실제 파일 hash는 Step0 manifest에 기록 |
| B 참조구조 | CONDITIONAL | Step 0 기존 90/142 DAG는 acyclic; Step 1은 독립 전체 재전사/diff 미완료. 비간선·strict task의 GT 근거 부족 |
| C task/action | CONDITIONAL | green 배정은 실행 가능; 경로는 도식에 존재; direct-edge 부재 미검증 |
| D 실측 평가 | CONDITIONAL→현재 정책 효과 추론 차단 | 기록된 action assignment는 있으나 response와 actuation의 행별 시점/고정행동 평가 지지 부족. 자료는 observational cohort가 아니라 rowwise SET experiment이고 `intervention` 컬럼은 0 고정 |
| E 독립성 | FAIL for confirmatory population claim; CONDITIONAL for case | 장치/session ID 미확인; 20 blocks는 단일 submit 내 순차 기록 |

## 권고와 제한

현 단계의 후보 estimand는 무작위 **배정 green command regime**에 대한 조건부 ITT뿐이며, 이마저 carryover·serial dependence, 입력/기록 정렬, 평가 분할이 확인되어야 한다. 자료는 무개입 관측 cohort가 아니라 각 행에서 여러 입력을 SET하는 순차 randomized-command experiment다. 따라서 Research C의 observational SCM fit/discovery 단계와 동일한 데이터 역할을 가정할 수 없으며, G0 discovery/learner adapter가 필요하다. 이는 원 SPICE paper의 `ir_1` treatment→`ir_2` outcome 과제와 다르다. 원 논문은 `green`을 confounder, `current_ls_raw`를 proxy로 취급하고 low/noisy 차이를 ADC data rate (`sps_current_ls` 4/7)로 정의했다. 이번 후보의 `green→current_led_2_uv`는 새 연구과제다. 물리 광출력 효과 및 고정 설정 정상상태 효과는 지지되지 않는다. 기존 C의 S0 vs Full Greedy, B=2, M1–M4 strict complete-DAG contract는 그대로 적용 승인되지 않는다. M4는 secondary status를 유지한다. Graph-free action baseline은 그래프 수리의 추가 가치 분리 목적의 별도 comparator로 제안한다.

조건부 사례는 단일 설정의 관찰된 자료에 한정되며 독립 SCM 모집단 확증도, 일반 제조공정 효능도, 배포 안전성도 의미하지 않는다. 공개 논문의 outcome 결과표 일부가 web 검색 추출에 노출되었으나 task 선택에는 사용하지 않았다. 원자료 response를 요약하거나 정책별 성능을 계산하지 않았지만, 본 데이터는 공개 논문과 benchmark 자료로 완전히 미열람 외부 holdout이 아니다.

## 진입 전 blocker / 결정 요청

1. 공식 참조를 완전 GT로 요구할지, pair별 partial reference 또는 reference-relative benchmark로 재계약할지 결정.
2. 장치 운영자에게 experiment/session/device ID, firmware 로그, SET–MSR semantics, acquisition timing/settling/reset 증거를 요청할지 결정(현재 발송하지 않음).
3. 이 archive가 주는 목표가 순간 명령 regime인지, 고정행동 효과인지 승인. 후자면 신규 실험 자료 없이는 중단.
4. 변수 projection/상수 처리와 오류 pair denominator/예산을 사전 지정하는 별도 설계 검토.
5. 결과를 보기 전 평가 분할과 최소 action support/독립성·정밀도 산정 절차 정의.

**본실험/최종 데이터셋 채택/장치 제어/실측 정책 regret 평가 승인 아님.** unresolved blocker가 답변 없이 남으면 이 단계 결과는 qualification case로 닫고 평가값을 열람하지 않는다.

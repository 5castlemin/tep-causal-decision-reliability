# 재개 기록

- 브랜치: feature/decision-reliability-next. 시작 commit e769ef58b015d31f3b3eef27e83c52ccd3017175. main e960fa8.
- 질문: 같은 전체 정확도의 오류 위치/유형이 실제 조작·개선/악화를 어떻게 바꾸는가? 지표 순위 최적화가 목적 아님.
- 단계1: AGENTS/CONTRIBUTING/원설계/현재 상태/PR15 보고서 확인. 기존 나침반 문서 없음. RESEARCH_COMPASS 작성. PR15 OPEN, head e769ef5, CI40158875287 success. 자동 병합 안 함.
- 근거: 기존 통제 오류 S1/S7 120행, C01~C12 1104행 및 저장 모형·공통 정책·do 기록 확인. 이 자료를 재사용하며 새 독립 결과로 부르지 않음.
- 단계2 완료: PR15 raw/이론/구조CV 검증 통과. PLAN_v1/SHA 고정 후 기존 통제1224행 추천 재계산,432명목 F1/오류수 일치쌍. 명칭 중복108 제거 후324실제쌍,현재 과제 핵심–주변162쌍,양쪽 경로유지114쌍. 원래 기록은 그대로 보존.
- 단계3 완료: 발견 기본정책720행(가용716),기준 악화20/큰 악화4. C07 같은6개 관측자료에서 정답구조 Ridge6개를 새 적합하고 기울기/절편 oracle 대조. 실제 발견 graph와 분리. C07 경로 유지 F1동일 누락쌍의 손실14.542543 대.36, C03 반대 사례. 새 인과발견 학습/do 생성은0.
- 단계4 완료: 고정9후보의 중첩 구조CV. 내부선택 기본19/경로1,외부MAE .323129. 경로 추가의 부호가 기준 모형에 따라 달라지고 정밀도 거친 추정132구조/1188학습으로30/288 초과. 새 독립 확인 NOT_RUN. 개별5검사 통과(저장자료/중첩CV/6적합 replay 포함).
- 단계5: 기존 제조 상태/코드 보고서만 확인. 동일 관측–참조–do 계약 미확인으로 제조 준비NO-GO 유지; 새 제조실험 없음. 우선순위는 환경 정합성 계약,오류–효과–선택의 독립 대조 설계,정밀도/예산이다.
- 미수행: 새 독립구조/발견학습/do/제조운전. 전체65개 검사·동결39해시·Step6·상태/manifest 검사 통과. push·새PR·아카이브는 최종 확인 단계에서 기록한다. 기존 원본 변경 없음.
- 핵심 파일: RESEARCH_COMPASS.md; DECISION_RELIABILITY_NEXT_REPORT.md; src/decision_reliability_next.py; scripts/run_decision_reliability_next.py / summarize_decision_reliability_next.py / validate_decision_reliability_next.py.
- 재현: python -X utf8 scripts/run_decision_reliability_next.py --output <fresh>; python -X utf8 scripts/summarize_decision_reliability_next.py --input <fresh> --output <fresh-audit>; python -X utf8 scripts/validate_decision_reliability_next.py. 결과는 run_v1/audit_supplement_v1.
- 다음 한 가지: 검증된 변경을 커밋/push하고 PR15 위 stacked PR로 제출한다(자동 병합 없음).
- 위험: 정답으로 만든 인위적 graph를 실제 발견 출력으로 혼합하거나, 재분석을 독립 확인으로 재분류하지 않는다.

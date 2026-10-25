# 오류가 의사결정을 바꾸는 과정: 기존 개발 자료의 실행 대조

나침반: `docs/research_design/RESEARCH_COMPASS.md`.
한국어 결과: `docs/research_design/DECISION_RELIABILITY_NEXT_REPORT.md`.
재개: `CHECKPOINT.md`. 원 설계/기존 연구 파일은 수정하지 않는다.

PR15 head e769ef5 위 stacked 작업. main 병합/새 독립 구조·인과발견 학습·do 생성·제조 운전 없음.

1. `PLAN_v1.json/.sha256`: 실행 전에 고정한 오류쌍/큰 악화/모형9개/규제·선택/예산 조건.
2. `run_v1/`: 기존 통제 오류1224행 추천 재계산·실제 수식/저장 do 비교, 전체 F1/오류수 일치432명목쌍, 발견 기본정책720행 진단, 새C07 정답구조6개 Ridge 적합(oracle), 20구조의 중첩 구조 검증 및 정밀도.
3. `audit_supplement_v1/`: 실제 graph가 같은108개 명칭 중복 표시;324실제쌍. 과제별 핵심–주변 재판정. 원래 결과 보존.
4. `PR15_REVIEW.json/PR15_LOCAL_VALIDATION.txt`: 이번 선행 검토. 사용자 병합 승인 및 별도 팀원 검토 없음.
5. `MANUFACTURING_TRANSFER.json`: 기존 상태에 근거한 이전 가능/불가 계약. 새 simulator 실행 증거 아님.

```powershell
python -X utf8 scripts/validate_path_metric_incremental.py
python -X utf8 scripts/run_decision_reliability_next.py --output <fresh-run-directory>
python -X utf8 scripts/summarize_decision_reliability_next.py --input <fresh-run-directory> --output <fresh-audit-directory>
python -X utf8 scripts/validate_decision_reliability_next.py
python -X utf8 -m unittest discover -s tests -v
```

실제 실행은 기존 고정 Python3.11.15/NumPy1.26.4/Pandas2.2.3 환경을 재사용했다. 새 causal-learn/lingam 학습은 필요하지 않다. CI 기본 requirements 환경은 저장 원시 기록과 방정식 계산·6개 적합·중첩 검증을 재실행한다. 소스/hash·입력 원본은 기존 저장소의 버전 고정 산출물에 연결한다. 원본 대량 CSV·외부 라이브러리를 다시 복사하지 않는다.

손실 개선과 추가 손실은 반대 정의가 아니다(기준과 최선이 다름). 방향 반전과0효과 누락, 실제 계산 기준 조작과 경로부재 대체를 분리한다. 큰 악화 문턱은 연구 진단용이며 Safety 기준이 아니다. 모든20구조는 개발 자료다. 인위적 오류와 oracle 응답 교체를 실제 발견 graph로 합치지 않는다.

# 합성 최종 주장·근거 통합

한국어 Results·Discussion: `docs/research_design/SYNTHETIC_FINAL_RESULTS_AND_CLAIMS.md`.

- `CLAIM_EVIDENCE_MATRIX.json`: A/B1/B2/C/D/E/F의 가설·실험·단위·실제값·지지·반례·허용/금지 해석·원시 위치·판정.
- `RESULT_SUMMARY.json`: 기존 예측행/오류쌍/추천정책의 재집계. 새 관측·학습·do 결과가 아님.
- `INPUT_SHA256.json`: 실제 읽은 기존 입력의 정확한 바이트 SHA. 과거 manifest나 원자료를 수정하지 않음.
- `validation/`: 이번 실제 검사. CI와 단위검사는 과거 수치 검증이며 신규 연구 실험이 아님.

검사: `python -X utf8 scripts/summarize_synthetic_final_claims.py --check`.
요약 코드는 stdlib만 사용하고 simulator/학습/적합 모듈을 import하지 않는다. 기존 구간을 복사·대조하며 새 bootstrap도 하지 않는다. `--check`는 원시 예측행의 구조 동일가중 MAE,동점 오류쌍/중복,정책 손실·실패 상태와 저장 요약을 비교한다. 생성 모드는 기존 결과 파일을 덮어쓰지 않는다.

당시 C12의 M1-M2 사전 지지는 보존하되,이론평균 민감도와 M1-M4/M5-M6 추가 정보의 불확실성을 분리한다. C12는 이제 개발 자료이며 새 독립 확인에 재사용할 수 없다. TEP는 동결 유지,제조 복구·안전 검증 없음. 다음 자원 우선순위는 제한 독립 합성 오류대조의 계약·예산 확정이며,이번에 새 실험을 실행하지 않는다.

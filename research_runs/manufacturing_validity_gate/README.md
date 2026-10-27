# 제조 연구 타당성 Gate — 2026-10-27

보고서: `docs/research_design/MANUFACTURING_VALIDITY_GATE_REVIEW.md`.

- `review_v4/`: 최종 성공 감사. 기존7 graph/84과제/198조작–목표 쌍 재계산, 원본 평가기 실행, 원래10000개 무작위 draw의21조건 재집계, 수치/시간 계약 및 기존 join guard의 한계. 새로운 draw·학습·시뮬레이터 실행 없음.
- `review_v1/`: 실패한 CSV index 읽기. 원본 파일/행을 바꾸지 않고 index_col=0 규약으로 수정.
- `review_v2/`: 손실된 소수 CSV의 F1 동률을 그대로 비교하여 실패.
- `review_v3/`: 저장 CSV를 거의 완전 정밀도로 가정하여 실패. 실제 반올림값은 정답 간선 수의 .001 미만 오차이며 .5 간격보다 작아 TP를 유일하게 복원 가능. 그 검사를 추가해 v4에서 원래 표와 일치 확인. 실패 출력은 원본으로 보존.
- `NEXT_ENVIRONMENT_CONTRACT_SPEC.json`: 다음 구현할 작은 검사 계약. 현재 구현/과학적 승인 아님.

```powershell
python -X utf8 graphs/final/verify_and_load.py
python -X utf8 scripts/audit_manufacturing_validity.py --output <fresh-folder> --step6-zip <hash-verified TEP_step6_results_slack.zip>
python -X utf8 scripts/validate_ref_b_minimal_records.py
python -X utf8 scripts/validate_decision_mvp.py
python -X utf8 scripts/validate_manufacturing_validity.py
python -X utf8 -m unittest discover -s tests -v
```

원본 ZIP SHA28824bc2…와 data/local의 고정 CSV/GT가 첫 감사의 외부 입력이다. 경로는 실행 인수로 전달하고 개인 절대 경로를 Git에 넣지 않는다. 원 ZIP/코드는 재배포하지 않는다. CI는 저장 histogram·정의·계산 및 기존 증거/guard를 재검산하며, 외부ZIP/원시 정상CSV를 다시 취득하거나 인과발견 학습을 수행하지 않는다. 설치환경은 기존Python3.11.15/NumPy1.26.4/Pandas2.2.3을 재사용했다.

새로운 관측 노드 GT, 물리 효과 정답, Recovery/Safety 또는 신규 환경 채택은 없다. 현행 gate는 서로 다른 id를 차단하지만 같은 이름/수동Boolean으로 metadata 검증을 대신할 수 없다는 한계를 새로 확인했다. 연구 상태 문서에서 이 제한을 보존한다.

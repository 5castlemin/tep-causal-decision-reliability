# 제한 내부 동적 연구계약 검토

PR19 `5d3d627` 위 설계 검토. **PROPOSED_FOR_REVIEW / 판정2 / 실행NO-GO**.

- `PROTOCOL.json`: 단 하나의 수동 냉각수–에너지 후보. u/v/W/E·1초12미채점쌍,부모폐쇄/경계,알고리즘 추정대상,온도목표·선택,독립평가·중단 규약. 공식GT 아님.
- `DECISION.json`: 현재정당화안됨의근거와다음한결정. B본실험확대중단,C별도효과중심설계검토여부는사용자선택. 자동연구변경없음.
- `EVIDENCE.json`: 과거근거의정적LF-normalized문서hash와이번정적source읽기버전,확인한공식문서/원논문 링크. 과거rawSHA를바꾸지않음.
- `validation/`: schema·상태·전체기존검사 기록. 과거저장숫자의재검산을새simulator실행으로세지않음.

검사:
```text
python -X utf8 scripts/validate_bounded_dynamic_protocol.py
python -X utf8 -m unittest tests.test_bounded_dynamic_protocol -v
python -X utf8 scripts/check_research_state.py
```
검사통과는문서내부일관성만뜻한다. simulator import/물리식 source실행/학습/새do/GT/F1은모두0. 한국어계약은 `docs/research_design/BOUNDED_DYNAMIC_RESEARCH_PROTOCOL.md`.

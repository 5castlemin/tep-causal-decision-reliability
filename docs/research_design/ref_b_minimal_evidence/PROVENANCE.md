# REF-B 최소 검산 기록

local_checks.json은 사전 계획 뒤 고정 Python source에서 실행한 17회 단일 평가·제어기 복사본 검산·수동2객체 각6step의 선택 원시값이다. 내부 상태 변화는 단위 검산이며 물리적 조작 API가 아니다. 결과는 CANDIDATE_NOT_OFFICIAL_GT이다.

decision.json은 국소 구현 확인과 관측 수준 참조 차단을 분리한다. teprob.f hash는 동일 source 계보의 정적 식 대조만 뜻하며 Fortran 실행은 NOT_RUN이다. SHA256.json과 .gitattributes는 기록 바이트 보존에 사용한다.

source 실행은 scripts/validate_ref_b_subsystem_source.py와 외부 고정 checkout이 필요하다. CI는 scripts/validate_ref_b_minimal_records.py로 저장된 차분·해석식/오차·조건·hash를 재대조한다. source를 CI에 복사하지 않으며 CI가 공식 GT나 물리적 정확도를 승인하지 않는다.

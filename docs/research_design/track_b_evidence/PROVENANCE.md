# 출처와 검증 범위

- source_probe.json: 2026-10-24 사전 계획의 4객체×30step API/RNG 관찰 기록. scripts/audit_track_b_source.py와 기존 고정 source SHA로 재실행 가능. 새 GT·효과 성능 자료 아님.
- source_inventory.json: 공식 DOI/Dataverse API의 최소 공개 필드, source/LICENSE hash. provider MD5는 원본 다운로드 검증이 아니며 원시 데이터 SHA는 null.
- decision.json: Q1~Q5와 의존 PR6·미채택 판단. 관측 상태와 연구 설계 판단을 구분.
- SHA256.json: 생성 JSON의 바이트 SHA-256. Windows checkout의 줄바꿈 변환은 .gitattributes에서 막음.
- 원본 API 응답·접근 기록·실패 요약·최종 ZIP은 사용자가 지정한 날짜별 아카이브에 보관. 개인 경로·서명 URL·외부 데이터 본체는 Git에 반입하지 않음.

이 패키지의 validator/CI 통과는 기록 정합성 검사이지 참조 인과구조의 과학적 증명이나 Track B 채택 승인이 아니다.

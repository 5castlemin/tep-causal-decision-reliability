# 의사결정 이력

| 시점 | 결정 또는 제안 | 근거 | 채택하지 않은 대안·재검토 조건 |
|---|---|---|---|
| 2026-08-23 보고 | 시뮬레이터 연동과 반사실 추천을 지향 | 방학 스터디 보고서 | 현재 실행 자료가 없어 완료 상태로 승격하지 않음. 소스·로그 확보 시 재검토 |
| 2026-10-05~06 | 7개 최종 그래프와 Step 6 엄격 평가 보존 | Final ZIP, Step 6 CSV·FREEZE | GT 성능으로 그래프를 사후 수정하지 않음 |
| 2026-10-06 | 198→65→12 구조 평가 후보 기록 | GT·변수 대응·사람이 고른 대표 목록·자동 유효성 검사 | 12개를 실제 복구 과제로 간주하지 않음. 시뮬레이터 확인 시 별도 과제 확정 |
| 2026-10-06 | 정적 4개는 확정 방향만, VarLiNGAM·DYNOTEARS는 원래 시차 구조, PCMCI+는 보류 | 순환/시차 감사 | 미확정 간선 자동 방향화·순환 간선 임의 삭제를 기각. 인과적 식별 근거가 생기면 재검토 |
| 2026-10-06 | 선형 가산 SCM·공통 Ridge 격자·동일 목표 행·시간순 분할 설계 | 최종 학습 전 freeze | 비선형 모델은 파일럿 성공 뒤 민감도 분석. 실제 적합과 별개 |
| 2026-10월 중순 이후 | 전체 정확도 대 경로 정확도에서 여러 구조 지표의 유용성 비교로 **질문 확대 제안** | 구조 지표 순위 불일치와 팀 연구방향 문서 | 후속 성능 미측정이므로 설명력 결론 없음. 파일럿 실행 가능성에 따라 범위 축소 |
| 2026-10-23 | 실제 개입 전 1과제·정적 3그래프 파일럿 우선, 현 단계에서는 정상상태 수치 적합만 기록 | 시뮬레이터 소스/API 미확보, 기존 결과 감사 | 12과제 일괄 실험·알고리즘 확장을 보류. Gate A 재현 후 갱신 |
| 2026-10-23 | 공개 Python simulator 후보를 기존 8월 구현과 별도로 smoke 검증 | `docs/audit/SIMULATOR_FEASIBILITY_REPORT.md` | 30분 실행 성공을 장기 안정성·기존 GT 개입 정답으로 승격하지 않음. 수치·reset·controller 호환 관문 필요 |

| 2026-10-23 | 공개 후보의 반복 단위는 동일 source/backend/seed/mode의 새 객체 | `docs/audit/SIMULATOR_RELIABILITY_REPORT.md` 및 reset 10경우 | fresh twin 경로 exact, 같은 객체 운전 후 reset 관측 약 1e-12 차이. 관측값 강제 복원·원본 패치 기각 |
| 2026-10-23 | 관측 시계와 Euler 상태 시계를 별도 기록 | `experiments/simulator/diagnostics/run_20261023_aligned` | 추가 evaluate 호출 없이 공통 시각 비교. 기존 CSV에 누락된 상태를 소급 생성하지 않음 |
| 2026-10-23 | 후보 내부 탐색 CONDITIONAL / benchmark 개입 정답 직접 사용 NO-GO | 3 dt 수렴 경향, 압력 종료 및 2시간 정상 분포 차이 | 수치 수렴을 실제 모델/제어기 동등성으로 승격하지 않음. 독립 기준·생성 계보 확보 전 Recovery/Safety 주장 보류 |

| 2026-10-23 | Benchmark 호환성 Gate는 현재 증거 부족, 다음 최소 복원 경로는 A 권고 | `docs/research_design/BENCHMARK_COMPATIBILITY_DECISION.md` | 공식 수정 모델 source·setpoint 배선은 확보했으나 원시 timestamp/seed/export·실행 동등성 미확인. RESEARCH_DESIGN은 유지하며 B Primary 전환·C Secondary 도입은 승인 전 실행하지 않음 |
| 2026-10-23 | PR #4 raw·중간 결과의 중복은 보존 | `docs/research_design/evidence/local_20261023_v2/pr4_asset_review.json` | 동일 바이트 24그룹/88경로는 반복·빈 기록·파생 통계를 포함. 보존정책을 임의 변경하거나 원시 manifest를 깨는 삭제를 하지 않음 |

| 2026-10-23 | 사용자 승인으로 PR4→PR5 순서 통합 | PR4 merge 1e4fcc7, PR5 base main | 최초 decision의 dependency는 당시 기록으로 보존하고 현재 병합 상태를 github_current에 분리. 연구 질문·Track B/C 채택 변경 없음 |
# 2026-10-23 Track A 복원 접근·실행 Gate

정상 원시 ZIP의 공식 목록과 공개 기술보고서를 확보한 사실을 원시 바이트 회수와 구분한다. 문서상 Tests의 시간/seed 파일 구조를 정상 ZIP 또는 benchmark 선택 run에 전이하지 않는다. MATLAB 검색 범위 미발견을 전역 설치/라이선스 부재로 단정하지 않는다.
현재 A1/A2 BLOCKED이므로 A3는 NOT_RUN, 직접 효과 참조 NO-GO와 가설 INSUFFICIENT_EVIDENCE를 유지한다. 새로운 자료가 없는 반복 검색은 종료한다. 요청의 C(차단 명시 및 Track B 참조 구조 검증 설계 검토 제안)를 권고하되 연구 방향을 변경하거나 Track B/C를 채택하지 않는다. 새로운 실행환경/원본이 제공되면 Track A 재개 가능하다. 전환은 사용자 승인 대상이다.
근거: docs/research_design/TRACK_A_RECOVERY_GATE.md 및 track_a_evidence/gate_evidence.json.

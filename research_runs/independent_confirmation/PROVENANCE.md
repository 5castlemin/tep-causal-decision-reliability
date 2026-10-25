# 출처·버전·보존 계약

2026-10-25(KST). 시작 기준은 미병합 PR #13의 `a4ae7694aff24e8a40dce516cf44007d52676907`이며 그 base는 미병합 PR #12다. 기존 Git 이력과 TEP/동결/Step 6/기존 적합·원시·첫 통합·반복·다양 구조 결과 및 RESEARCH_DESIGN.md를 수정하지 않는다. 새 산출물의 범위는 합성 재현성·방법론 진단·독립 확인이다.

## 외부 생성 도구

- 공식 repository: https://github.com/boschresearch/causalAssembly
- 고정 commit: `8da3729e6383f0e1cbe7740bb6ab7ac4977ac7f9`
- 사용 파일: `causalAssembly/models_fcm.py`
- SHA-256: `c1f1b7f6b62c8916ebd23cb0002cdad1e9fcfb995b81cfae9558271987c4290e`
- 원본의 AGPL-3.0-or-later 헤더를 보존하며 소스를 변경하거나 이 저장소에 복사하지 않는다. 기존에 확보한 고정 파일을 바이트 검증 후 사용했다.
- 임의 수식 예제의 FCM 기능만 검증했다. 제조 generator 전체 또는 기존 TEP와의 동등성을 검증한 것이 아니다.

## 원래 재실행과 새로운 확인 자료

원래144회는 변경하지 않은 기존 runner, 원래 PLAN·seed·의존성으로 별도 프로세스·디렉터리에서 실행했다. `REPLAY_COMPARISON.json`은 핵심 수치/이산값 비교, `replay_evidence/`는 실제 시간 ledger·버전·원시 manifest와 그래프 기록이다. 동일한 데이터 바이트를 Git에 다시 복제하지 않는다. 원시 재실행의 전체 파일은 지정 로컬 아카이브에 보존했다. 시간 정보가 다르므로 전체 실행 폴더의 모든 파일이 바이트 일치한다고 주장하지 않는다. 같은 host/설치 환경의 재현이며 다른 OS의 외부 학습 이식성 검증과 다르다.

새 구조·계수·과제·관측/noise/do는 이 프로젝트에서 명시한 수식과 사전 고정 seed로 실제 생성한 합성 자료다. 외부 TEP 데이터의 재배포가 아니다. `generation_acceptance_records.json`에 기각 후보까지 기록했다. 기존 결과를 보며 구조나 비용·seed를 사후 변경하지 않는다.

## 실행 소프트웨어와 공개 범위

실제 외부 학습은 기존 별도 venv의 Python3.11.15, NumPy1.26.4, causal-learn0.1.4.8, lingam1.13.0 등 동일 lock을 재사용했다. 정확한 전체 버전은 각 environment.json/requirements.lock.txt, 수치 backend는 NUMERICAL_BACKEND.txt/RUNTIME_POLICY.json을 확인한다. thread 수를 실행 중 바꾸지 않았다. 라이브러리 절대 경로는 정리하고 원래 경로 정보는 로컬 아카이브에만 둔다.

CI의 requirements.txt는 NumPy/Pandas/NetworkX 기반의 **저장 기록 검사** 환경이다. 해당 환경에서216회 외부 알고리즘을 학습했다고 주장하지 않는다. 개인 경로를 포함할 수 있는 worker 원본 console은 로컬 아카이브에, 정리된 사본과 원본 SHA는 Git에 보존한다. 가상환경·설치 파일·자격 증명·대형 ZIP은 Git에 올리지 않는다.

## 해시와 압축

사전 계획·분석 코드·옛 자료로 적합한 손실 예측모형의 해시는 FREEZE.json/PLAN_v1에 있다. 해시 동결 이후 실제 데이터 생성이 시작됐는지는 execution_ledger의 UTC 순서로 확인한다. 실제 추천은 개입 평가 전에 별도 SHA로 고정했다.

새 대형 JSON 및 do/noise CSV는 무손실 gzip으로 저장한다. COMPRESSION.json의 원본 SHA와 압축 SHA, 원래 run/SHA256.json의 해시를 모두 검증한다. 원시 수치나 행은 압축 과정에서 반올림·삭제하지 않는다. 최종 전체 파일 목록은 FINAL_SHA256.json이며 자기 자신은 제외한다. 원래 소스·과거 실험의 manifest는 갱신하지 않는다.

재현 실행의 데이터는 독립 학습 데이터 증가로 세지 않고, 새 구조에서도 여러 알고리즘·과제·정책·do 표본을 독립 구조 수로 더하지 않는다. 독립 확인의 실제 분석 범위·판정·실패·NOT_RUN은 한국어 보고서와 analysis_v1 결과를 우선한다.

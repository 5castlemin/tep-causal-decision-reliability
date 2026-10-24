# 승인된 예제 FCM acceptance

PLAN_v1은 실행 전 고정했고 사용자는 소규모 예제 실행만 별도 승인했다. 원본 단일 models_fcm.py를 격리 venv에서 실제 실행한 기록은 run_20261024_v1이다. 외부 source는 SHA로 검증하며 vendoring하지 않는다.

직접 선언한4노드 IID fixture의 reference/관측/do/반복·분할·Action/Target 확인은 통과했다. 제조 generator·물리 시계·Track B 채택·새 discovery/SCM 학습은 하지 않았다. reference CSV는 이 fixture의 선언 그래프이며 TEP GT가 아니다.

18batch×64행 data/noise와 hook 없는 API9회 통제(총 sampler27회)를 기록했다. 동일 seed라도 관측/do 잡음은 정렬되지 않아 분포수준 do만 허용한다. sample_id는 시간·동일 개체 식별자가 아니다. train 역할의 do배치도 acceptance 기록일 뿐 미래 learner 입력이 아니다.

재현: 새 Python3.11 venv에 run_20261024_v1/requirements.lock.txt 설치, 고정 module 확보 후 별도 승인 아래 scripts/run_env_acceptance.py의 --module/--output/--execution-approved 사용. 기존 output 덮어쓰기 금지. negative_no_approval_v1은 승인flag 누락의 예상 거부 기록이다.

CI의 scripts/validate_env_acceptance.py는 외부 source를 실행하지 않고 raw식·hash·split·범위·실패guard를 검사한다. 설치/실행 원시 console과 venv는 지정 archive에 보존하며 venv는 Git/배포ZIP에서 제외한다.

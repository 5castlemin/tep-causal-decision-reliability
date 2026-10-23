# 설치 실패 원시 로그 요약

TEP Studio 0.2.0 최초 pip 설치: UnicodeEncodeError cp949 (U+00DC).
재시도: PYTHONUTF8=1, python -X utf8 -m pip install . --log install_attempt.log
인코딩 실패는 해결됨. 최종 실패: Microsoft Visual C++ 14.0 or greater is required.
전체 원시 설치 로그는 저장소 밖 tep-studio-candidate/install_attempt.log 및 install_console.txt에 보존했다. 개인 경로를 포함하여 Git에는 반입하지 않았다.

최초 Python smoke 실행은 shutdown으로 reference/intervention 기록 길이가 달라져 ValueError: operands could not be broadcast together with shapes (60,) (61,) 발생. CSV는 run_20261023에 보존. v2/v3는 동일 개입을 유지하고 공통 시점으로 비교했다.

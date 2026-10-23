# 최종 그래프

`final/`은 검증된 `TEP_final_graphs_v1.zip`에서 꺼낸 원본 정적 행렬·시차 그래프·설정·검증기다. `A_dir[i,j]=1`은 Xi→Xj이며 `A_unres`는 방향 미확정 연결이다. `python -X utf8 graphs/final/verify_and_load.py`로 39개 파일 해시와 3종 시차 변환을 다시 확인한다. SCM 파일럿에서는 정적 그래프의 확정 방향만 부모로 사용했다. 원본 파일은 편집하지 말고 별도 파생 산출물로 변경을 기록한다.

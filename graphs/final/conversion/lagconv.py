"""시차 그래프 → 정적 그래프 변환 (지시서 5절) 및 정적 그래프 형식 변환.

내부 시차 그래프 표준 형식 (tigramite 규약):
    lag_graph: np.ndarray[str], shape (d, d, tau_max+1)
    lag_graph[i, j, tau] = '-->'  ⟺  X_i(t-tau) → X_j(t)
    tau=0 은 대칭 표기: lag_graph[i,j,0]='-->' 이면 lag_graph[j,i,0]='<--'
    그 밖의 표기: 'o-o','x-x','<->','o->','<-o','x->','<-x' 등, 빈 문자열 = 연결 없음

출력 (정적):
    A_dir   : int (d, d), A_dir[i,j]=1 ⟺ X_i → X_j 확정 방향 (row = parent)
    A_unres : int (d, d), 대칭, 연결은 있으나 방향 미확정
    두 행렬의 지지(support)는 서로소이며 대각은 0.

사전 등록 규칙 (GT를 보기 전 고정):
  R1 tau>=1 의 '-->' 는 X_i → X_j.
  R2 tau=0 은 알고리즘 방향을 따름 ('-->' 또는 '<--').
  R3 모든 시차를 OR 결합, 자기 자신으로 가는 시차 연결 제외.
  R4 결합 후 i→j 와 j→i 가 모두 있으면 방향 충돌 → 미확정.
  R5 방향 미정/잠재교란 표기(o-o, x-x, o->, <-o, <-> 등, tau 무관)는 미확정 표기.
  [엄격(primary)] 한 쌍에 미확정 표기가 하나라도 있으면 그 쌍은 미확정.
  [관대(sensitivity)] 미확정 표기가 있어도 반대 방향 없이 한 방향 확정 표기가 있으면 확정.
"""
import numpy as np

DIRECTED = {"-->"}
REVERSED = {"<--"}


def lag_to_static(lag_graph, mode="strict"):
    """lag_graph (d,d,T+1) -> (A_dir (d,d), A_unres (d,d), info dict)"""
    d = lag_graph.shape[0]
    fwd = np.zeros((d, d), bool)    # 확정 방향 표기 존재 i→j
    und = np.zeros((d, d), bool)    # 미확정 표기 존재 (대칭)
    for tau in range(lag_graph.shape[2]):
        for i in range(d):
            for j in range(d):
                m = lag_graph[i, j, tau]
                if m == "" or i == j:
                    continue                      # R3: 자기 연결 제외
                if tau >= 1:
                    if m in DIRECTED:
                        fwd[i, j] = True          # R1
                    else:
                        und[i, j] = und[j, i] = True   # R5
                else:
                    if m in DIRECTED:
                        fwd[i, j] = True          # R2
                    elif m in REVERSED:
                        fwd[j, i] = True
                    else:
                        und[i, j] = und[j, i] = True
    conflict = fwd & fwd.T                        # R4
    A_dir = np.zeros((d, d), int)
    A_unres = np.zeros((d, d), int)
    n_conf = n_mixed = 0
    for i in range(d):
        for j in range(i + 1, d):
            has = fwd[i, j] or fwd[j, i] or und[i, j]
            if not has:
                continue
            if conflict[i, j]:
                A_unres[i, j] = A_unres[j, i] = 1; n_conf += 1
            elif und[i, j] and (fwd[i, j] or fwd[j, i]):
                n_mixed += 1
                if mode == "strict":
                    A_unres[i, j] = A_unres[j, i] = 1
                else:
                    if fwd[i, j]: A_dir[i, j] = 1
                    else: A_dir[j, i] = 1
            elif und[i, j]:
                A_unres[i, j] = A_unres[j, i] = 1
            elif fwd[i, j]:
                A_dir[i, j] = 1
            else:
                A_dir[j, i] = 1
    check_static(A_dir, A_unres)
    return A_dir, A_unres, dict(n_conflict=n_conf, n_mixed_marks=n_mixed, mode=mode)


def check_static(A_dir, A_unres):
    assert A_dir.shape == A_unres.shape and A_dir.shape[0] == A_dir.shape[1]
    assert np.all(np.diag(A_dir) == 0) and np.all(np.diag(A_unres) == 0)
    assert np.all(A_unres == A_unres.T), "A_unres 비대칭"
    assert not np.any(A_dir & A_dir.T), "A_dir 에 양방향 쌍"
    assert not np.any((A_dir | A_dir.T) & A_unres), "확정/미확정 지지가 겹침"


def dag_to_static(A):
    """DAG 이진행렬 (row=parent) -> (A_dir, A_unres=0)"""
    A = (np.asarray(A) != 0).astype(int); np.fill_diagonal(A, 0)
    Z = np.zeros_like(A); check_static(A, Z); return A, Z


def causallearn_to_static(G):
    """causal-learn GeneralGraph.graph (d,d) -> (A_dir, A_unres)
    causal-learn 규약: G[j,i]=1 & G[i,j]=-1 ⟺ i→j ; G[i,j]=G[j,i]=-1 ⟺ i—j ; 둘 다 1 ⟺ i↔j"""
    d = G.shape[0]; A = np.zeros((d, d), int); U = np.zeros((d, d), int)
    for i in range(d):
        for j in range(i + 1, d):
            a, b = G[i, j], G[j, i]
            if a == 0 and b == 0: continue
            if a == -1 and b == 1: A[i, j] = 1
            elif a == 1 and b == -1: A[j, i] = 1
            else: U[i, j] = U[j, i] = 1
    check_static(A, U); return A, U


def is_acyclic(A_dir):
    """확정 방향 부분그래프의 방향 순환 여부 (True = 순환 없음)"""
    import networkx as nx
    return nx.is_directed_acyclic_graph(nx.DiGraph(np.asarray(A_dir)))


def edgelist(A_dir, A_unres, names):
    rows = []
    d = len(names)
    for i in range(d):
        for j in range(d):
            if A_dir[i, j]: rows.append((names[i], names[j], "-->"))
            if i < j and A_unres[i, j]: rows.append((names[i], names[j], "---(unresolved)"))
    return rows

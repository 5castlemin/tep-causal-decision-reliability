"""TEP Final Graphs v1 검증·로딩.
verify(): MANIFEST 해시 재계산, 변수 순서, 정적 그래프 성질, 시계열 lag→static 엄격 재변환 일치 확인. 실패 시 예외.
load_graphs(): {algo: {"A_dir": (31,31) int, "A_unres": (31,31) int, "lag_graph": (31,31,T+1) str|None, "config": dict}}
규약: A_dir[i,j]=1 ⟺ X_i→X_j (row=parent), 순서 = variables.csv"""
import hashlib, json, os, sys
import numpy as np, pandas as pd
ROOT = os.path.dirname(os.path.abspath(__file__))
ALGOS = ["pc", "boss", "directlingam", "dagma", "pcmciplus", "varlingam", "dynotears"]
TS = {"pcmciplus", "varlingam", "dynotears"}


def _sha(p):
    h = hashlib.sha256(); h.update(open(p, "rb").read()); return h.hexdigest()


def load_graphs(check=True):
    if check: verify()
    V = pd.read_csv(os.path.join(ROOT, "variables.csv")).variable.tolist(); out = {}
    for a in ALGOS:
        d = os.path.join(ROOT, "graphs", a)
        A = pd.read_csv(f"{d}/A_dir.csv", index_col=0); U = pd.read_csv(f"{d}/A_unres.csv", index_col=0)
        assert list(A.index) == list(A.columns) == list(U.index) == list(U.columns) == V
        L = np.load(f"{d}/lag_graph.npy") if a in TS else None
        out[a] = dict(A_dir=A.values.astype(int), A_unres=U.values.astype(int), lag_graph=L,
                      config=json.load(open(f"{d}/config.json")), variables=V)
    return out


def verify():
    m = pd.read_csv(os.path.join(ROOT, "MANIFEST.csv"))
    bad = [f for f, h in zip(m.file, m.sha256) if _sha(os.path.join(ROOT, f)) != h]
    if bad: raise RuntimeError(f"해시 불일치: {bad}")
    sys.path.insert(0, os.path.join(ROOT, "conversion")); from lagconv import lag_to_static, check_static
    G = load_graphs(check=False)
    for a, g in G.items():
        check_static(g["A_dir"], g["A_unres"])
        if g["lag_graph"] is not None:
            A2, U2, _ = lag_to_static(g["lag_graph"], "strict")
            if not (np.array_equal(A2, g["A_dir"]) and np.array_equal(U2, g["A_unres"])):
                raise RuntimeError(f"{a}: lag→static 엄격 재변환 불일치")
    print(f"OK: {len(m)}개 파일 해시 일치, 변수 순서 일치, 시계열 {len(TS)}개 엄격 재변환 일치")


if __name__ == "__main__":
    verify()

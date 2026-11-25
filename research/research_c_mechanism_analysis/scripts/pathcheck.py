import sqlite3, json, sys
from collections import Counter
db=sqlite3.connect(f"file:{sys.argv[1]}?mode=ro",uri=True); c=Counter()
def haspath(edges,a,t):
    ch={}; [ch.setdefault(u,[]).append(v) for u,v in edges]
    st=[a]; seen={a}
    while st:
        u=st.pop()
        if u==t: return True
        for v in ch.get(u,[]):
            if v not in seen: seen.add(v); st.append(v)
    return False
for (rj,) in db.execute("select result_json from scms where status='COMPLETED'"):
    p=json.loads(rj)["payload"]; e=p["e2e_result"]; a,t=e["input"]["action"],e["input"]["target"]
    for b in e["budgets"]:
        for pol in b["policies"]:
            L=pol["unresolved_abstention"]["learner_dag_edges"]; pr=pol["evaluation"]["predicted_losses"].values()
            flat=max(pr)-min(pr)<1e-9; hp=haspath(L,a,t)
            c[(("path" if hp else "nopath"),("flat" if flat else "effect"))]+=1
print(dict(c))

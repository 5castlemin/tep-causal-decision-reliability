import json, sys, statistics as st, math
d = json.load(open(sys.argv[1])); R = d["recs"]
def get(pol,B): return {r["scm"]: r for r in R if r["pol"]==pol and r["B"]==B}
s0, fg, m4 = get("S0",2), get("M1+M2+M3+M4",2), get("M4",2)
ids = sorted(s0)
dl = [s0[i]["regret"]-fg[i]["regret"] for i in ids]
n=len(dl); m=st.mean(dl); sd=st.stdev(dl); se=sd/math.sqrt(n)
print("n",n,"S0",round(st.mean(s0[i]["regret"] for i in ids),8),"FG",round(st.mean(fg[i]["regret"] for i in ids),8),"M4",round(st.mean(m4[i]["regret"] for i in ids),8))
print("delta",round(m,8),"sd",round(sd,8),"se",round(se,8))
print("imp/wor/tie", sum(x>1e-12 for x in dl), sum(x<-1e-12 for x in dl), sum(abs(x)<=1e-12 for x in dl))
print("zero-error G0", sum(d["scm"][i]["init_err"]==0 for i in ids))
print("FG mean cost", st.mean(fg[i]["cost"] for i in ids), "M4 cost", st.mean(m4[i]["cost"] for i in ids))
dm=[fg[i]["regret"]-m4[i]["regret"] for i in ids]
print("FG-M4", round(st.mean(dm),8), sum(x>1e-12 for x in dm), sum(x<-1e-12 for x in dm))
pols = sorted({r["pol"] for r in R})
for p in pols:
    print(f"{p:14s}", " ".join(f"{st.mean(r['regret'] for r in R if r['pol']==p and r['B']==B):.5f}" for B in range(5)))

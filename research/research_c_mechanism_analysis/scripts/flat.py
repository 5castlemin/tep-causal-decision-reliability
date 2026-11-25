import json, sys
from collections import Counter
F=json.load(open(sys.argv[1])); EPS=1e-12
def kind(r):
    pr=r["pred"]; vals=list(pr.values())
    if max(vals)-min(vals)<1e-9: return "flat_no_predicted_effect"
    # predicted best sign vs true opt sign
    kbest=float(min(pr,key=pr.get))
    return "pred_effect"
out={}
for pol in ["S0","M4","M1+M2+M3+M4","M2","CANONICAL_ORACLE"]:
  for B in (0,2,4):
    if pol=="S0" and B: continue
    rows=[r for r in F["recs"] if r["pol"]==pol and r["B"]==B]
    c=Counter()
    for r in rows:
        k=kind(r); pos=r["regret"]>EPS
        if k=="flat_no_predicted_effect": c["flat"]+=1; c["flat_k0"]+= (r["k"]==0.0)
        c[f"{'flat' if k.startswith('flat') else 'eff'}_{'pos' if pos else 'zero'}"]+=1
        if pos and not k.startswith('flat'):
            c["eff_pos_wrong_sign"]+= (r["k"]*r["opt"]<0); c["eff_pos_same_sign"]+=(r["k"]*r["opt"]>0)
        if pos: c["sum_regret"]+=r["regret"]; 
        if pos and k.startswith('flat'): c["sum_regret_flat"]+=r["regret"]
    c["opt0"]=sum(r["opt"]==0.0 for r in rows)
    out[f"{pol}@B{B}"]=dict(c); print(pol,B,dict(c))
json.dump(out,open(sys.argv[2],"w"),indent=1)

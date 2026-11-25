import json, sys, statistics as st
from collections import Counter, defaultdict
d = json.load(open(sys.argv[1])); R = d["recs"]; SC = d["scm"]
FG="M1+M2+M3+M4"; EPS=1e-12
idx = {(r["scm"],r["pol"],r["B"]): r for r in R}
ids = sorted(SC, key=lambda i: SC[i]["ord"])
pols = ["S0","M1","M2","M3","M4","M1+M2","M1+M3","M1+M4","M2+M3","M2+M4","M3+M4","M1+M2+M3","M1+M2+M4","M1+M3+M4","M2+M3+M4",FG,"CANONICAL_ORACLE"]
out = {}
# A. policy x budget table
tab=[]
for p in pols:
  for B in range(5):
    rows=[idx[(i,p,B)] for i in ids]; s0=[idx[(i,"S0",B)] for i in ids]
    c=Counter()
    for r in rows:
      for e in r["edits"]: c[(e["t"], "task" if e["tz"] else "off")]+=1
    tab.append(dict(pol=p,B=B,regret=st.mean(r["regret"] for r in rows), cost=st.mean(r["cost"] for r in rows),
      unused=st.mean(B-r["cost"] for r in rows),
      graph_changed=sum(r["graph"]!=a["graph"] for r,a in zip(rows,s0)),
      learner_changed=sum(r["learner"]!=a["learner"] for r,a in zip(rows,s0)),
      action_changed=sum(r["k"]!=a["k"] for r,a in zip(rows,s0)),
      better=sum(a["regret"]-r["regret"]>EPS for r,a in zip(rows,s0)), worse=sum(r["regret"]-a["regret"]>EPS for r,a in zip(rows,s0)),
      edits={f"{t}_{z}":v for (t,z),v in sorted(c.items())},
      task_edits=sum(v for (t,z),v in c.items() if z=="task"), off_edits=sum(v for (t,z),v in c.items() if z=="off"),
      resid_task=st.mean(sum(r["final"]["M4"].values()) for r in rows),
      resid_off=st.mean(sum(sum(r["final"][m].values()) for m in ("M1","M2","M3")) for r in rows)))
out["policy_table"]=tab
# initial G0 error composition
ic=Counter()
for i in ids:
  for m,kk in SC[i]["init_counts"].items():
    for k,v in kk.items(): ic[(m,k)]+=v
out["g0_errors"]={f"{m}_{k}":v for (m,k),v in sorted(ic.items())}
out["g0_scm_with_task_err"]=sum(sum(SC[i]["init_counts"]["M4"].values())>0 for i in ids)
out["g0_scm_with_off_err_only"]=sum(sum(SC[i]["init_counts"]["M4"].values())==0 and SC[i]["init_err"]>0 for i in ids)
out["g0_zero"]=sum(SC[i]["init_err"]==0 for i in ids)
# S0 regret by whether task-zone errors exist
out["s0_regret_task_err"]=st.mean(idx[(i,"S0",0)]["regret"] for i in ids if sum(SC[i]["init_counts"]["M4"].values())>0)
out["s0_regret_no_task_err"]=st.mean([idx[(i,"S0",0)]["regret"] for i in ids if sum(SC[i]["init_counts"]["M4"].values())==0] or [0])
out["s0_pos_regret_no_task_err"]=sum(idx[(i,"S0",0)]["regret"]>EPS for i in ids if sum(SC[i]["init_counts"]["M4"].values())==0)
out["s0_pos_regret_task_err"]=sum(idx[(i,"S0",0)]["regret"]>EPS for i in ids if sum(SC[i]["init_counts"]["M4"].values())>0)
# B. FG vs M4 at each budget
cmp={}
for B in range(1,5):
  cats=Counter(); cases=[]
  for i in ids:
    f,m,s=idx[(i,FG,B)],idx[(i,"M4",B)],idx[(i,"S0",B)]
    sg=f["graph"]==m["graph"]; sl=f["learner"]==m["learner"]; sa=f["k"]==m["k"]
    dr=f["regret"]-m["regret"]
    cat=("same_graph" if sg else "same_learner_dag" if sl else "diff_graph_same_action" if sa else "diff_action")
    cats[cat]+=1
    if not sa:
      fm=sum(f["final"]["M4"].values()); mm=sum(m["final"]["M4"].values())
      cases.append(dict(scm=i, ord=SC[i]["ord"], template=SC[i]["template"], n=SC[i]["n"], action=SC[i]["action"], target=SC[i]["target"],
        g0=SC[i]["init_counts"], regret_S0=s["regret"], regret_FG=f["regret"], regret_M4=m["regret"], k_S0=s["k"], k_FG=f["k"], k_M4=m["k"], opt=f["opt"],
        FG_edits=f["edits"], M4_edits=m["edits"], FG_resid_task=fm, M4_resid_task=mm, FG_cost=f["cost"], M4_cost=m["cost"],
        FG_margin=f["margin"], M4_margin=m["margin"], truth=f["truth"], FG_pred=f["pred"], M4_pred=m["pred"]))
  # mechanism classification among diff-action
  mech=Counter()
  for c in cases:
    better = "M4_better" if c["regret_FG"]-c["regret_M4"]>EPS else "FG_better" if c["regret_M4"]-c["regret_FG"]>EPS else "tie"
    if c["FG_resid_task"]>c["M4_resid_task"]: why="FG_left_task_error_unfixed"
    elif c["FG_resid_task"]==c["M4_resid_task"]: why="same_task_residual_FG_extra_offtask"
    else: why="M4_left_more_task_error"
    mech[(better,why)]+=1
  cmp[B]=dict(categories=dict(cats), diff_action_cases=cases, mechanism={f"{a}|{b}":v for (a,b),v in mech.items()},
     mean_FG_minus_M4=st.mean(idx[(i,FG,B)]["regret"]-idx[(i,"M4",B)]["regret"] for i in ids),
     FG_resid_task_gt_M4=sum(sum(idx[(i,FG,B)]["final"]["M4"].values())>sum(idx[(i,"M4",B)]["final"]["M4"].values()) for i in ids))
out["fg_vs_m4"]=cmp
# C. FG edit order at B=2: first-edit metric, and position of off-task edits before task edits
first=Counter(); off_before_task=0; scm_with_both=0
for i in ids:
  ed=idx[(i,FG,2)]["edits"]
  if ed: first["task" if ed[0]["tz"] else "off"]+=1
  init_task=sum(SC[i]["init_counts"]["M4"].values())
  if ed and init_task>0 and any(not e["tz"] for e in ed):
    scm_with_both+=1
    tz=[e["tz"] for e in ed]
    if (False in tz) and (True in tz and tz.index(False)<len(tz)-1-tz[::-1].index(True)) or (True not in tz): off_before_task+=1
out["fg_B2_first_edit_zone"]=dict(first); out["fg_B2_offtask_spent_while_task_err_pending"]=off_before_task; out["fg_B2_scm_with_task_err_and_off_edit"]=scm_with_both
# D. off-task-only policies: effect on regret
offonly={}
for p in ["M1","M2","M3","M1+M2","M1+M3","M2+M3","M1+M2+M3"]:
  for B in (2,4):
    diffs=[(i,idx[(i,p,B)]["regret"]-idx[(i,"S0",B)]["regret"]) for i in ids]
    offonly[f"{p}@B{B}"]=dict(worse=[(i,round(x,5)) for i,x in diffs if x>EPS], better=[(i,round(x,5)) for i,x in diffs if x<-EPS],
       learner_changed=sum(idx[(i,p,B)]["learner"]!=idx[(i,"S0",B)]["learner"] for i in ids),
       action_changed=sum(idx[(i,p,B)]["k"]!=idx[(i,"S0",B)]["k"] for i in ids))
out["offtask_only"]=offonly
# E. structure vs regret decoupling
dec=Counter()
for p in [FG,"M4"]:
  for i in ids:
    s,f=idx[(i,"S0",2)],idx[(i,p,2)]
    dec[(p, "Pall_down" if f["P_all"]<s["P_all"] else "Pall_same", "reg_down" if s["regret"]-f["regret"]>EPS else "reg_up" if f["regret"]-s["regret"]>EPS else "reg_tie")]+=1
out["structure_vs_regret_B2"]={"|".join(k):v for k,v in sorted(dec.items())}
# F. worse-than-S0 cases for FG and M4 at any budget
w=[]
for p in [FG,"M4"]:
  for B in range(1,5):
    for i in ids:
      s,f=idx[(i,"S0",B)],idx[(i,p,B)]
      if f["regret"]-s["regret"]>EPS: w.append(dict(pol=p,B=B,scm=i,regret_S0=s["regret"],regret=f["regret"],edits=f["edits"],k_S0=s["k"],k=f["k"],opt=f["opt"],g0=SC[i]["init_counts"],resid=f["final"]))
out["worse_than_S0"]=w
json.dump(out, open(sys.argv[2],"w"), indent=1, default=str)
# print summary
for t in tab:
  if t["B"] in (1,2,4): print(f'{t["pol"]:16s} B{t["B"]} reg={t["regret"]:.5f} cost={t["cost"]:.3f} task={t["task_edits"]:3d} off={t["off_edits"]:3d} learnerΔ={t["learner_changed"]:3d} actΔ={t["action_changed"]:3d} +{t["better"]}/-{t["worse"]} residT={t["resid_task"]:.3f}')
for k in ["g0_errors","g0_scm_with_task_err","g0_scm_with_off_err_only","g0_zero","s0_regret_task_err","s0_regret_no_task_err","s0_pos_regret_no_task_err","s0_pos_regret_task_err","fg_B2_first_edit_zone","fg_B2_offtask_spent_while_task_err_pending","fg_B2_scm_with_task_err_and_off_edit","structure_vs_regret_B2"]: print(k, out[k])
for B,v in cmp.items(): print("B",B,v["categories"],v["mechanism"],round(v["mean_FG_minus_M4"],5),"FGresid>M4",v["FG_resid_task_gt_M4"])
for k,v in offonly.items(): print(k, "lΔ",v["learner_changed"],"aΔ",v["action_changed"],"worse",v["worse"][:6],"better",v["better"][:6])
print("worse_than_S0:", [(x["pol"],x["B"],x["scm"],round(x["regret"]-x["regret_S0"],4)) for x in w])

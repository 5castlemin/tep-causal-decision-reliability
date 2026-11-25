import json, csv, sys
S, OUT = sys.argv[1], sys.argv[2]
for coh in ("dev","ho"):
    A=json.load(open(f"{S}/runs/{coh}_analysis.json"))
    with open(f"{OUT}/tables/{coh}_policy_budget_mechanism.csv","w",newline="") as f:
        w=csv.writer(f); w.writerow(["policy","B","mean_regret","mean_cost","mean_unused_budget","edits_task","edits_offtask","FN_task","FP_task","REV_task","UNRES_task","FN_off","FP_off","REV_off","UNRES_off","learner_dag_changed_vs_S0","action_changed_vs_S0","better_vs_S0","worse_vs_S0","mean_residual_task_errors","mean_residual_offtask_errors"])
        for t in A["policy_table"]:
            e=t["edits"]; w.writerow([t["pol"],t["B"],f'{t["regret"]:.8f}',f'{t["cost"]:.3f}',f'{t["unused"]:.3f}',t["task_edits"],t["off_edits"],*[e.get(f"{k}_task",0) for k in ("FN","FP","REV","UNRES")],*[e.get(f"{k}_off",0) for k in ("FN","FP","REV","UNRES")],t["learner_changed"],t["action_changed"],t["better"],t["worse"],f'{t["resid_task"]:.3f}',f'{t["resid_off"]:.3f}'])
    with open(f"{OUT}/tables/{coh}_fg_vs_m4_diff_action_cases.csv","w",newline="") as f:
        w=csv.writer(f); w.writerow(["B","scm_id","template","nodes","action","target","opt_k","k_S0","k_FG","k_M4","regret_S0","regret_FG","regret_M4","FG_edits","M4_edits","FG_resid_task","M4_resid_task"])
        fmt=lambda es:" > ".join(f'{x["m"]}:{x["t"]}({"/".join(x["pair"])})' for x in es)
        for B,v in A["fg_vs_m4"].items():
            for c in v["diff_action_cases"]:
                w.writerow([B,c["scm"],c["template"],c["n"],c["action"],c["target"],c["opt"],c["k_S0"],c["k_FG"],c["k_M4"],f'{c["regret_S0"]:.5f}',f'{c["regret_FG"]:.5f}',f'{c["regret_M4"]:.5f}',fmt(c["FG_edits"]),fmt(c["M4_edits"]),c["FG_resid_task"],c["M4_resid_task"]])
# ---------- figures (held-out) ----------
A=json.load(open(f"{S}/runs/ho_analysis.json")); FL=json.load(open(f"{S}/runs/ho_flat_summary.json"))
reg={(t["pol"],t["B"]):t["regret"] for t in A["policy_table"]}
css="""<style>.t{font:13px system-ui,-apple-system,'Noto Sans KR',sans-serif;fill:#191919}.s{font:12px system-ui,sans-serif;fill:#666}.g{stroke:#e5e5e5;stroke-width:1}.ax{stroke:#999;stroke-width:1}
@media (prefers-color-scheme:dark){.t{fill:#efefef}.s{fill:#9c9c9c}.g{stroke:#333}.bg{fill:#191919}}</style>"""
# Fig1 line
W,H,L,R,T,Bm=760,380,64,210,46,52
pw,ph=W-L-R,H-T-Bm; ymax=0.10
X=lambda b:L+pw*b/4; Y=lambda v:T+ph*(1-v/ymax)
ser=[("S0","S0 (무수정)","#257de0"),("CANONICAL_ORACLE","Canonical Oracle","#f2a600"),("M1+M2+M3+M4","Full Greedy","#f47230"),("M4","M4 단독","#00b894")]
o=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">{css}<rect class="bg" width="{W}" height="{H}" fill="#fff"/>',
   f'<text class="t" x="{L}" y="22" font-weight="600">그림 1. 예산별 평균 Decision Regret (Held-out 200 SCM)</text>']
for v in (0,0.02,0.04,0.06,0.08,0.10):
    o.append(f'<line class="g" x1="{L}" x2="{L+pw}" y1="{Y(v):.1f}" y2="{Y(v):.1f}"/><text class="s" x="{L-8}" y="{Y(v)+4:.1f}" text-anchor="end">{v:.2f}</text>')
for b in range(5): o.append(f'<text class="s" x="{X(b):.1f}" y="{T+ph+20}" text-anchor="middle">B={b}</text>')
o.append(f'<text class="s" x="{L+pw/2}" y="{H-10}" text-anchor="middle">수정 예산 B (원자 수정 횟수)</text>')
lab_y={}
for pid,name,col in ser:
    pts=" ".join(f"{X(b):.1f},{Y(reg[(pid,b)]):.1f}" for b in range(5))
    o.append(f'<polyline points="{pts}" fill="none" stroke="{col}" stroke-width="2"/>')
    for b in range(5): o.append(f'<circle cx="{X(b):.1f}" cy="{Y(reg[(pid,b)]):.1f}" r="4" fill="{col}" stroke="#fff" stroke-width="2"><title>{name} B={b}: {reg[(pid,b)]:.5f}</title></circle>')
    lab_y[name]=Y(reg[(pid,4)])
# direct labels with simple collision avoidance
items=sorted(((y,n,c) for (p,n,c) in ser for y in [lab_y[n]]))
last=-99
for y,n,c in items:
    y=max(y,last+16); last=y
    col=[cc for (_,nn,cc) in ser if nn==n][0]
    o.append(f'<rect x="{L+pw+12}" y="{y-8}" width="10" height="10" rx="2" fill="{col}"/><text class="t" x="{L+pw+28}" y="{y+1}">{n} {reg[([p for p,nn,_ in ser if nn==n][0],4)]:.4f}</text>')
o.append('</svg>'); open(f"{OUT}/figures/fig1_regret_by_budget_heldout.svg","w").write("\n".join(o))
# Fig2 stacked horizontal bars: positive-regret SCMs at B=2 by cause
rows=[("S0@B0","S0 (무수정)"),("M2@B2","M2 단독 B=2"),("CANONICAL_ORACLE@B2","Canonical Oracle B=2"),("M1+M2+M3+M4@B2","Full Greedy B=2"),("M4@B2","M4 단독 B=2")]
W,H,L=760,300,170; pw=W-L-110; bh=26; T=70; xmax=60
o=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">{css}<rect class="bg" width="{W}" height="{H}" fill="#fff"/>',
   f'<text class="t" x="16" y="22" font-weight="600">그림 2. Regret&gt;0 인 SCM 수와 원인 (Held-out, 200 SCM 중)</text>',
   f'<rect x="16" y="36" width="10" height="10" rx="2" fill="#257de0"/><text class="t" x="32" y="45">수정 그래프에 X→Y 유향 경로 없음 → 예측 효과 0 → k=0 선택</text>',
   f'<rect x="16" y="52" width="10" height="10" rx="2" fill="#f47230"/><text class="t" x="32" y="61">경로는 있으나 예측 효과 부호가 반대</text>']
for i,(key,name) in enumerate(rows):
    d=FL[key]; flat=d.get("flat_pos",0); wrong=d.get("eff_pos_wrong_sign",0); y=T+12+i*(bh+16)
    o.append(f'<text class="t" x="{L-10}" y="{y+bh/2+4}" text-anchor="end">{name}</text>')
    x0=L; wf=pw*flat/xmax; ww=pw*wrong/xmax
    if flat: o.append(f'<rect x="{x0}" y="{y}" width="{max(wf-1,1):.1f}" height="{bh}" rx="3" fill="#257de0"><title>{name}: 경로 없음 {flat}</title></rect>')
    if wrong: o.append(f'<rect x="{x0+wf+1:.1f}" y="{y}" width="{max(ww-1,1):.1f}" height="{bh}" rx="3" fill="#f47230"><title>{name}: 부호 반대 {wrong}</title></rect>')
    o.append(f'<text class="t" x="{x0+wf+ww+8:.1f}" y="{y+bh/2+4}">{flat} + {wrong} = {flat+wrong}</text>')
o.append('</svg>'); open(f"{OUT}/figures/fig2_regret_cause_heldout.svg","w").write("\n".join(o))
print("ok")

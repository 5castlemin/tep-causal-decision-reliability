"""Render reproducible lightweight SVG figures from public F-Lite aggregates."""
import csv, json
from pathlib import Path

ROOT=Path(__file__).resolve().parent; OUT=ROOT/"figures"; DATA=ROOT/"outputs"; OUT.mkdir(exist_ok=True)
POLICIES=["S0","RANDOM_VERIFICATION","FIT_BASED_VERIFICATION","SUSPICION_ONLY","DECISION_IMPACT_ONLY","DECISION_WEIGHTED_VERIFICATION","ORACLE_ASSISTED_M4_DIAGNOSTIC","GRAPH_FREE_ASSOCIATION_DIAGNOSTIC"]
LABEL={"S0":"S0","RANDOM_VERIFICATION":"Random","FIT_BASED_VERIFICATION":"Fit","SUSPICION_ONLY":"Suspicion","DECISION_IMPACT_ONLY":"Impact","DECISION_WEIGHTED_VERIFICATION":"Decision-weighted","ORACLE_ASSISTED_M4_DIAGNOSTIC":"Oracle M4","GRAPH_FREE_ASSOCIATION_DIAGNOSTIC":"Graph-free"}
COLORS={"S0":"#555555","RANDOM_VERIFICATION":"#8c8c8c","FIT_BASED_VERIFICATION":"#377eb8","SUSPICION_ONLY":"#4daf4a","DECISION_IMPACT_ONLY":"#984ea3","DECISION_WEIGHTED_VERIFICATION":"#e41a1c","ORACLE_ASSISTED_M4_DIAGNOSTIC":"#ff7f00","GRAPH_FREE_ASSOCIATION_DIAGNOSTIC":"#a65628"}
def rows(path):
    with path.open(encoding="utf-8",newline="") as f:return list(csv.DictReader(f))
def svg(path,body,w=1000,h=620,title=""):
    text=f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}"><rect width="100%" height="100%" fill="white"/><text x="{w/2}" y="32" text-anchor="middle" font-family="Arial" font-size="20">{title}</text>{body}</svg>'
    path.write_text(text,encoding="utf-8")
def txt(x,y,s,size=12,anchor="middle",fill="#222"):
    return f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}" font-family="Arial" font-size="{size}" fill="{fill}">{s}</text>'
def line(x1,y1,x2,y2,color="#777",width=1):return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{width}"/>'
def axes(w,h,left=80,right=25,top=65,bottom=75):
    return left,top,w-left-right,h-top-bottom
def main():
    datasets={"Development":rows(DATA/"c_development_aggregate.csv"),"Held-out":rows(DATA/"c_heldout_aggregate.csv")}
    # F1: budget x policy heatmaps; separate panels by cohort.
    body=""
    for ci,(cohort,rs) in enumerate(datasets.items()):
        x0=70+ci*485;y0=110;cw=50;ch=54
        vals={(r["policy"],int(r["budget"])):float(r["mean_regret"]) for r in rs}
        maxv=max(vals.values())
        body+=txt(x0+cw*2.5,y0-24,cohort,16)
        for j,p in enumerate(POLICIES):
            body+=txt(x0-8,y0+j*ch+31,LABEL[p],11,"end")
            for b in range(5):
                v=vals[(p,b)];q=min(v/maxv,1);red=int(255*q);blue=int(245*(1-q));color=f"#{red:02x}{210:02x}{blue:02x}"
                body+=f'<rect x="{x0+b*cw}" y="{y0+j*ch}" width="{cw-2}" height="{ch-2}" fill="{color}" stroke="white"/>'+txt(x0+b*cw+cw/2,y0+j*ch+31,f"{v:.3f}",10)
        for b in range(5):body+=txt(x0+b*cw+cw/2,y0+len(POLICIES)*ch+14,str(b),11)
    svg(OUT/"F1_budget_performance_heatmaps.svg",body,title="F1 — Mean regret by verification policy and query budget (cohorts separate)")
    # F2: key policy curves, separate panels.
    body="";keys=["S0","RANDOM_VERIFICATION","FIT_BASED_VERIFICATION","SUSPICION_ONLY","DECISION_IMPACT_ONLY","DECISION_WEIGHTED_VERIFICATION","ORACLE_ASSISTED_M4_DIAGNOSTIC","GRAPH_FREE_ASSOCIATION_DIAGNOSTIC"]
    for ci,(cohort,rs) in enumerate(datasets.items()):
        x0=85+ci*480;y0=75;pw=400;ph=390
        body+=txt(x0+pw/2,45,cohort,16)
        lookup={(r["policy"],int(r["budget"])):float(r["mean_regret"]) for r in rs};mx=max(lookup.values())*1.05
        for t in range(5):body+=line(x0,y0+ph*t/4,x0+pw,y0+ph*t/4,"#ddd")+txt(x0-8,y0+ph*t/4+4,f"{mx*(1-t/4):.2f}",10,"end")
        for p in keys:
            pts=[]
            for b in range(5):pts.append((x0+pw*b/4,y0+ph*(1-lookup[(p,b)]/mx)))
            body+='<polyline fill="none" stroke="'+COLORS[p]+'" stroke-width="2" points="'+' '.join(f'{x:.1f},{y:.1f}' for x,y in pts)+'"/>'
            for x,y in pts:body+=f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="{COLORS[p]}"/>'
        for b in range(5):body+=txt(x0+pw*b/4,y0+ph+20,str(b),11)
    legend="";x=85
    for p in keys:
        legend+=line(x,520,x+22,520,COLORS[p],3)+txt(x+26,524,LABEL[p],11,"start");x+=115
    svg(OUT/"F2_budget_curves.svg",body+legend,title="F2 — Mean regret curves; lower is better")
    # F3: paired contrasts from stored audit.
    audit=json.loads((ROOT/"saved_output_audit.json").read_text(encoding="utf-8")); cs=[c for c in audit["paired_contrasts"] if c["cohort"]=="C_HELDOUT" and c["comparator"]!="DECISION_WEIGHTED_VERIFICATION"]
    body="";x0=350;y0=110;scale=850
    body+=line(x0,80,x0,480,"#333")
    for i,c in enumerate(cs):
        y=y0+i*70;lo=c["ci95_low"];hi=c["ci95_high"];mu=c["mean_comparator_minus_proposed"]
        body+=txt(315,y+5, c["comparator"].replace("_"," "),12,"end")+line(x0+lo*scale,y,x0+hi*scale,y,"#31688e",4)+f'<circle cx="{x0+mu*scale:.1f}" cy="{y}" r="6" fill="#d73027"/>'
    body+=line(x0-240,480,x0+130,480,"#555")+txt(x0,515,"Comparator regret − decision-weighted regret (positive favors proposal)",13)
    svg(OUT/"F3_heldout_paired_contrasts.svg",body,title="F3 — Held-out B=4 paired SCM bootstrap contrasts")
    # F4: discovery vs regret, B4.
    body="";x0,y0,pw,ph=90,80,800,420; keys=[]
    for cohort,rs in datasets.items():
        for r in rs:
            if int(r["budget"])==4 and r["policy"] not in ("S0","GRAPH_FREE_ASSOCIATION_DIAGNOSTIC"):
                xx=x0+float(r["mean_discovered_error_pairs"])/2.2*pw; yy=y0+ph*(1-float(r["mean_regret"])/.11)
                body+=f'<circle cx="{xx:.1f}" cy="{yy:.1f}" r="4" fill="{COLORS[r["policy"]]}" opacity=".7"/>'
    body+=txt(x0+pw/2,y0+ph+38,"Mean incorrect relations discovered (descriptive)",13)+txt(25,y0+ph/2,"Mean regret",13)
    svg(OUT/"F4_discovery_vs_regret.svg",body,title="F4 — Error discovery and decision regret at B=4")
    # F5: query count / edit count / regret across all policies B4.
    body="";cohort="Held-out";rs=datasets[cohort]
    for r in rs:
        if int(r["budget"])!=4:continue
        x=100+float(r["mean_query_count"] or 0)*115;y=470-float(r["mean_regret"])/.11*380
        body+=f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="{COLORS[r["policy"]]}"/>'+txt(x,y-9,LABEL[r["policy"]],10)
    body+=txt(480,530,"Mean number of expert queries (horizontal); y = mean regret",13)
    svg(OUT/"F5_queries_and_regret.svg",body,title="F5 — Verification effort and B=4 Held-out regret")
    # F6: blind policies and benchmarks B4.
    body="";rs=datasets["Held-out"];selected=[r for r in rs if int(r["budget"])==4]
    for i,r in enumerate(selected):
        y=90+i*48;v=float(r["mean_regret"]);body+=txt(255,y+4,LABEL[r["policy"]],12,"end")+f'<rect x="280" y="{y-12}" width="{v/.1*600:.1f}" height="22" fill="{COLORS[r["policy"]]}"/>'+txt(290+v/.1*600,y+4,f"{v:.4f}",11,"start")
    svg(OUT/"F6_blind_oracle_graphfree_comparison.svg",body,title="F6 — B=4 Held-out regret; Oracle uses reference information")
    # F7: toy fixture only; never presented as a cohort case or measured result.
    body=""
    nodes={"X":(120,220),"M":(390,220),"Y":(660,220),"Z":(390,400)}
    for a,b in [("X","M"),("M","Y"),("Z","M")]:
        x1,y1=nodes[a];x2,y2=nodes[b];body+=line(x1+34,y1,x2-38,y2,"#31688e",3)+txt((x1+x2)/2,(y1+y2)/2-10,"→",16)
    for n,(x,y) in nodes.items():body+=f'<circle cx="{x}" cy="{y}" r="34" fill="#eef4f8" stroke="#31688e" stroke-width="2"/>'+txt(x,y+5,n,18)
    body+=f'<rect x="735" y="160" width="220" height="100" rx="8" fill="#fff4e6" stroke="#e68613" stroke-width="2"/>'+txt(845,195,"Expert answers only queried pair",13)+txt(845,220,"(toy illustration, not study data)",11)
    svg(OUT/"F7_reference_blind_query_fixture.svg",body,title="F7 — Query/update interface illustration (deterministic toy fixture)")
    # F9: conceptual framework.
    boxes=[(40,170,200,110,"Initial graph +\nobservational data"),(290,170,200,110,"Reference-blind\nquery policy"),(540,170,180,110,"Pair query"),(770,170,190,110,"Expert returns only\nqueried relation"),(540,370,200,110,"Update graph; enforce DAG"),(290,370,200,110,"Existing learner\nrecommends action"),(40,370,200,110,"Evaluator scores\nlocked recommendation")]
    body=""
    for x,y,w,h,label in boxes:
        body+=f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="#eef4f8" stroke="#31688e" stroke-width="2"/>'
        for j,line0 in enumerate(label.split("\n")):body+=txt(x+w/2,y+45+j*20,line0,14)
    for a,b in [((240,225),(290,225)),((490,225),(540,225)),((720,225),(770,225)),((865,280),(650,370)),((540,425),(490,425)),((290,425),(240,425)),((140,370),(140,280))]:body+=line(*a,*b,"#555",2)
    svg(OUT/"F9_research_framework.svg",body,title="F9 — Research F-Lite information flow (interface separation)")
    # F8 is emitted only when both cohort sensitivity aggregates are present.
    noise_paths=[DATA/"c_development_noise_sensitivity.csv",DATA/"c_heldout_noise_sensitivity.csv"]
    if all(p.exists() for p in noise_paths):
        nd={"Development":rows(noise_paths[0]),"Held-out":rows(noise_paths[1])};body=""
        ps=["RANDOM_VERIFICATION","SUSPICION_ONLY","DECISION_IMPACT_ONLY","DECISION_WEIGHTED_VERIFICATION"]
        for ci,(cohort,rs) in enumerate(nd.items()):
            x0=100+ci*480;y0=85;pw=380;ph=360;body+=txt(x0+pw/2,52,cohort,16)
            lookup={(float(r["accuracy"]),r["policy"]):float(r["mean_regret"]) for r in rs};mx=max(lookup.values())*1.05
            for t in range(5):body+=line(x0,y0+ph*t/4,x0+pw,y0+ph*t/4,"#ddd")+txt(x0-6,y0+ph*t/4+4,f"{mx*(1-t/4):.2f}",10,"end")
            for p in ps:
                pts=[]
                for j,a in enumerate((0.8,0.9)):
                    pts.append((x0+pw*j,y0+ph*(1-lookup[(a,p)]/mx)))
                body+='<polyline fill="none" stroke="'+COLORS[p]+'" stroke-width="3" points="'+' '.join(f'{x:.1f},{y:.1f}' for x,y in pts)+'"/>'
                for x,y in pts:body+=f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="{COLORS[p]}"/>'
            body+=txt(x0,y0+ph+22,"0.8",11)+txt(x0+pw,y0+ph+22,"0.9",11)
        x=140
        for p in ps:body+=line(x,505,x+20,505,COLORS[p],3)+txt(x+25,509,LABEL[p],11,"start");x+=180
        svg(OUT/"F8_expert_noise_sensitivity.svg",body,title="F8 — Hypothetical expert response accuracy sensitivity; B=4")
if __name__=="__main__":main()

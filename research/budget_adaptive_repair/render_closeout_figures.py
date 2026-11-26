from __future__ import annotations
import csv, html
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
D=ROOT/'research/final_integration/research_e_audit'; F=D/'figures'; F.mkdir(parents=True,exist_ok=True)
def csvrows(p):return list(csv.DictReader(p.open(newline='',encoding='utf-8-sig')))
def save(name,text):
 p=F/name
 with p.open('x',encoding='utf-8',newline='\n') as f:f.write(text)
# Pareto scatter and frontier.
pts=csvrows(D/'expanded_pareto_frontiers.csv')
allagg=csvrows(ROOT/'research/budget_adaptive_repair/outputs/e2_extended_budget_aggregate.csv')
adap=csvrows(ROOT/'research/budget_adaptive_repair/outputs/adaptive_m4_aggregate.csv')
colors={'C_DEVELOPMENT':'#1565c0','C_HELDOUT':'#c62828'}
W,H=1180,660
parts=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}"><rect width="100%" height="100%" fill="white"/><text x="590" y="34" text-anchor="middle" font-family="Arial" font-size="24" font-weight="bold">Research E — expanded C cost–performance frontier</text><text x="590" y="58" text-anchor="middle" font-family="Arial" font-size="13">Original 17 policies + Adaptive M4 · post-hoc unit-cost analysis · regret is C analytic Decision Regret</text>']
for panel,(co,title) in enumerate([('C_DEVELOPMENT','Development · n=64 · Bmax=7'),('C_HELDOUT','Held-out · n=200 · Bmax=9')]):
 x0=90+panel*570;y0=105;pw=480;ph=440
 data=[r for r in allagg if r['cohort']==co]
 data += [{'cohort':r['cohort'],'policy':'ADAPTIVE_M4_BLOCKER_AWARE','budget':r['budget'],'mean_cost':r['mean_cost'],'mean_regret':r['mean_regret']} for r in adap if r['cohort']==co]
 maxx=max(float(r['mean_cost']) for r in data)*1.08; maxy=max(float(r['mean_regret']) for r in data)*1.08
 def X(v):return x0+float(v)/maxx*pw
 def Y(v):return y0+ph-float(v)/maxy*ph
 parts.append(f'<text x="{x0+pw/2}" y="86" text-anchor="middle" font-family="Arial" font-size="17" font-weight="bold">{title}</text>')
 parts.append(f'<line x1="{x0}" y1="{y0+ph}" x2="{x0+pw}" y2="{y0+ph}" stroke="#333"/><line x1="{x0}" y1="{y0}" x2="{x0}" y2="{y0+ph}" stroke="#333"/>')
 for i in range(6):
  xx=maxx*i/5; yy=maxy*i/5
  parts.append(f'<line x1="{X(xx)}" y1="{y0}" x2="{X(xx)}" y2="{y0+ph}" stroke="#e5e7eb"/><text x="{X(xx)}" y="{y0+ph+20}" text-anchor="middle" font-family="Arial" font-size="11">{xx:.2f}</text>')
  parts.append(f'<line x1="{x0}" y1="{Y(yy)}" x2="{x0+pw}" y2="{Y(yy)}" stroke="#e5e7eb"/><text x="{x0-8}" y="{Y(yy)+4}" text-anchor="end" font-family="Arial" font-size="11">{yy:.3f}</text>')
 front=[r for r in pts if r['cohort']==co and r['frontier']=='CROSS_BUDGET']
 flabel={(r['policy'],int(r['budget'])) for r in front}
 for r in data:
  x=float(r['mean_cost']); y=float(r['mean_regret']); isf=(r['policy'],int(r['budget'])) in flabel
  color=colors[co] if isf else '#9ca3af'; rad=5 if isf else 2.6
  parts.append(f'<circle cx="{X(x):.2f}" cy="{Y(y):.2f}" r="{rad}" fill="{color}" opacity="{0.9 if isf else 0.45}"><title>{html.escape(r["policy"])} B={r["budget"]}; edit count={x:.4f}; regret={y:.7f}; frontier={isf}</title></circle>')
 # label selected frontier with at most key policy points
 for r in front:
  if r['policy'] not in {'S0','M3','M4','ADAPTIVE_M4_BLOCKER_AWARE'}:continue
  x=float(r['cost']);y=float(r['loss']);lab=f'{r["policy"]} B{r["budget"]}'
  parts.append(f'<text x="{X(x)+7:.2f}" y="{Y(y)-7:.2f}" font-family="Arial" font-size="10" fill="{colors[co]}">{html.escape(lab)}</text>')
 parts.append(f'<text x="{x0+pw/2}" y="{y0+ph+48}" text-anchor="middle" font-family="Arial" font-size="13">Mean atomic edit count (cost proxy)</text>')
 parts.append(f'<text transform="translate({x0-55},{y0+ph/2}) rotate(-90)" text-anchor="middle" font-family="Arial" font-size="13">Mean C Regret</text>')
parts.append('<text x="590" y="640" text-anchor="middle" font-family="Arial" font-size="12">Frontier membership is descriptive; ties are retained. Costs are edit counts, not labor or money.</text></svg>')
save('E9_expanded_pareto.svg','\n'.join(parts))
# Lower envelope displayed in ordered, equally sized bands; exact numeric ranges remain in the CSV.
rows=csvrows(D/'expanded_lambda_lower_envelope.csv'); W,H=1120,390
parts=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}"><rect width="100%" height="100%" fill="white"/><text x="560" y="32" text-anchor="middle" font-family="Arial" font-size="23" font-weight="bold">Research E — observed C lower envelope for Jλ</text><text x="560" y="55" text-anchor="middle" font-family="Arial" font-size="13">Jλ = mean regret + λ × mean edit count · post-hoc; bands are ordered, not proportional in width</text>']
cohort_names={'C_DEVELOPMENT':'Development','C_HELDOUT':'Held-out'}
colors2=['#0d47a1','#1565c0','#42a5f5','#ef6c00','#b71c1c']
for iy,co in enumerate(['C_DEVELOPMENT','C_HELDOUT']):
 y=132+iy*100; z=[r for r in rows if r['cohort']==co]; x0=195;pw=850;step=pw/len(z)
 parts.append(f'<text x="95" y="{y+16}" text-anchor="middle" font-family="Arial" font-size="14" font-weight="bold">{cohort_names[co]}</text>')
 for i,r in enumerate(z):
  xa=x0+i*step;hi=r['lambda_hi_exclusive'];lo=float(r['lambda_lo_inclusive'])
  raw=r['optimal_candidates'].split(';')
  short=[]
  for label in raw:
   if '@' in label:
    pol,b=label.rsplit('@B',1);pol=pol.replace('ADAPTIVE_M4_BLOCKER_AWARE','Adaptive M4').replace('CANONICAL_ORACLE','Oracle')
    text=f'{pol} B{b}'
   else:text=label
   if text not in short:short.append(text)
  # Collapse repeated budgets when candidates share an identical policy/loss-cost line.
  compact=[]
  for pol in dict.fromkeys(x.rsplit(' B',1)[0] if ' B' in x else x for x in short):compact.append(pol)
  label=' / '.join(compact)
  parts.append(f'<rect x="{xa:.2f}" y="{y-13}" width="{step:.2f}" height="28" fill="{colors2[min(i,len(colors2)-1)]}" stroke="white"><title>λ∈[{lo:.9g}, {hi}): {html.escape(r["optimal_candidates"])}</title></rect>')
  parts.append(f'<text x="{xa+step/2:.1f}" y="{y+5}" text-anchor="middle" font-family="Arial" font-size="10" fill="white">{html.escape(label[:35])}</text>')
  parts.append(f'<text x="{xa+step/2:.1f}" y="{y+34}" text-anchor="middle" font-family="Arial" font-size="9">λ {lo:.4g}–{hi if hi!="inf" else "∞"}</text>')
parts.append('<text x="560" y="365" text-anchor="middle" font-family="Arial" font-size="12">At boundaries, tied candidates are listed in expanded_lambda_breakpoints.csv; λ is not a monetary cost.</text></svg>')
save('E10_lambda_lower_envelope.svg','\n'.join(parts))
print('wrote E9/E10 SVG; no data generated')

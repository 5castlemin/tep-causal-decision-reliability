"""Render compact, dependency-free public SVG figures from aggregate-only tables."""
import csv
from pathlib import Path

ROOT=Path(__file__).resolve().parent
TABLES=ROOT/'tables'; FIG=ROOT/'figures'; FIG.mkdir(exist_ok=True)
rows=list(csv.DictReader((TABLES/'s3_policy_aggregates.csv').open(encoding='utf-8')))
policies=sorted({r['policy'] for r in rows if r['policy'] not in {'M4_ORIGINAL','M4_RANDOM_EXPECTATION'} and not r['policy'].endswith(('LOOKAHEAD2','GREEDY2'))})
def val(c,p,b): return float(next(r['mean_regret'] for r in rows if r['cohort']==c and r['policy']==p and int(r['budget'])==b))
policies.sort(key=lambda p:val('C_HELDOUT',p,2))
W=1080; left=260; top=100; rh=18; cw=160; height=top+len(policies)*rh+40
def color(x,lo,hi):
 t=0 if hi<=lo else max(0,min(1,(x-lo)/(hi-lo)))
 a=(235,245,238); b=(28,108,70); rgb=tuple(round(a[i]*(1-t)+b[i]*t) for i in range(3)); return '#%02x%02x%02x'%rgb
cells=[(c,b) for c in ('C_DEVELOPMENT','C_HELDOUT') for b in (1,2)]
values=[val(c,p,b) for p in policies for c,b in cells]; lo=min(values); hi=max(values)
svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{height}" viewBox="0 0 {W} {height}">','<rect width="100%" height="100%" fill="white"/>','<style>text{font-family:Arial,sans-serif;fill:#203128}.title{font-size:20px;font-weight:bold}.sub{font-size:12px}.lab{font-size:10px}.head{font-size:11px;font-weight:bold}</style>',f'<text x="20" y="28" class="title">S3: all 63 metric subsets — regret by cohort and budget</text>','<text x="20" y="48" class="sub">Exploratory original Research C cohorts; lower is better. Rows ordered by Held-out B=2. Not confirmatory.</text>']
for j,(c,b) in enumerate(cells):
 x=left+j*cw
 title=('Development' if c=='C_DEVELOPMENT' else 'Held-out')+f' B={b}'
 svg.append(f'<text x="{x+cw/2}" y="76" text-anchor="middle" class="head">{title}</text>')
for i,p in enumerate(policies):
 y=top+i*rh
 svg.append(f'<text x="{left-8}" y="{y+13}" text-anchor="end" class="lab">{p}</text>')
 for j,(c,b) in enumerate(cells):
  x=left+j*cw; z=val(c,p,b)
  svg.append(f'<rect x="{x}" y="{y}" width="{cw-3}" height="{rh-2}" fill="{color(z,lo,hi)}" stroke="#ffffff"/>')
  svg.append(f'<text x="{x+cw/2}" y="{y+12}" text-anchor="middle" class="lab">{z:.4f}</text>')
svg.append(f'<text x="{left}" y="{height-10}" class="sub">Color scale: {lo:.4f} to {hi:.4f}; policy evaluation reuses the same original SCMs.</text>')
(FIG/'S3_POLICY_HEATMAP.svg').write_text(''.join(svg)+'</svg>',encoding='utf-8')

ints=list(csv.DictReader((TABLES/'s3_primary_paired_intervals.csv').open(encoding='utf-8')))
items=[r for r in ints if r['budget']=='2' and 'LOOKAHEAD2' in r['contrast']]
W=1080; left=330; right=1020; top=80; rh=30; zero=left+(right-left)/2; scale=(right-left)/2
maxabs=max(abs(float(r[k])) for r in items for k in ('ci95_low','ci95_high')) or 1
height=top+len(items)*rh+50
svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{height}" viewBox="0 0 {W} {height}">','<rect width="100%" height="100%" fill="white"/>','<style>text{font-family:Arial,sans-serif;fill:#203128}.title{font-size:19px;font-weight:bold}.sub{font-size:12px}.lab{font-size:10px}</style>','<text x="20" y="28" class="title">S3: two-step lookahead minus one-step greedy (B=2)</text>','<text x="20" y="48" class="sub">Paired SCM-level difference in Regret; negative favors lookahead. 95% pointwise percentile intervals.</text>',f'<line x1="{zero}" y1="60" x2="{zero}" y2="{height-25}" stroke="#666" stroke-dasharray="4 3"/>']
for i,r in enumerate(items):
 y=top+i*rh; lo1=float(r['ci95_low']); hi1=float(r['ci95_high']); m=float(r['mean_difference']); c='#245f9c' if r['cohort']=='C_DEVELOPMENT' else '#b15b28'
 x1=zero+scale*lo1/maxabs; x2=zero+scale*hi1/maxabs; xm=zero+scale*m/maxabs
 svg += [f'<text x="{left-8}" y="{y+12}" text-anchor="end" class="lab">{r["cohort"]} {r["contrast"].replace("_LOOKAHEAD2 - "," − ").replace("_GREEDY2","")}</text>',f'<line x1="{x1}" y1="{y+8}" x2="{x2}" y2="{y+8}" stroke="{c}" stroke-width="2"/>',f'<circle cx="{xm}" cy="{y+8}" r="4" fill="{c}"/>']
svg.append(f'<text x="{left}" y="{height-8}" class="sub">Shared zero reference; interval span scaled to observed maximum ±{maxabs:.4f}. Cohort-color: blue Development, orange Held-out.</text>')
(FIG/'S3_LOOKAHEAD_PAIRED.svg').write_text(''.join(svg)+'</svg>',encoding='utf-8')
print('Rendered 2 SVG figures from aggregate tables.')

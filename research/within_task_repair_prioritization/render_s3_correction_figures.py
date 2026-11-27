from __future__ import annotations
import csv, html
from pathlib import Path
HERE=Path(__file__).resolve().parent
OUT=HERE/'outputs_v12'
DEST=HERE/'figures'/'correction_v1'
DEST.mkdir(parents=True,exist_ok=True)
rows=list(csv.DictReader((OUT/'s3_policy_aggregates.csv').open(encoding='utf-8')))
ints=list(csv.DictReader((OUT/'s3_primary_paired_intervals.csv').open(encoding='utf-8')))
sets=sorted({r['policy'] for r in rows if r['budget']=='1' and not r['policy'].endswith(('LOOKAHEAD2','GREEDY2')) and r['policy'] not in {'M4_ORIGINAL','M4_RANDOM_EXPECTATION'}})
def color(v,lo,hi):
 x=0 if hi==lo else (v-lo)/(hi-lo)
 # pale blue to dark blue, no external plotting dependency
 r=int(239-190*x); g=int(246-135*x); b=int(255-35*x)
 return f'#{r:02x}{g:02x}{b:02x}'
# Corrected 63-subset greedy heatmap, panels separated by cohort.
w,h=1220,2750; left=290; top=105; rowh=22; colw=82
svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">','<rect width="100%" height="100%" fill="white"/>','<style>text{font-family:Arial,sans-serif;font-size:12px}.title{font-size:20px;font-weight:bold}.head{font-weight:bold}</style>','<text x="30" y="34" class="title">Corrected S3: one-step structural-score Greedy</text>','<text x="30" y="58">Mean Research C regret; original cohorts; exploratory post-hoc; lower is better. Cohorts use separate color scales.</text>']
for panel,cohort in enumerate(('C_DEVELOPMENT','C_HELDOUT')):
 y0=top+panel*1320
 svg.append(f'<text x="30" y="{y0-24}" class="head">{cohort}</text>')
 for j,b in enumerate((1,2,3,4)):
  x=left+j*colw; svg.append(f'<text x="{x+20}" y="{y0-7}" class="head">B={b}</text>')
 data={(r['policy'],int(r['budget'])):float(r['mean_regret']) for r in rows if r['cohort']==cohort and not r['policy'].endswith(('LOOKAHEAD2','GREEDY2')) and r['policy'] not in {'M4_ORIGINAL','M4_RANDOM_EXPECTATION'}}
 vals=[v for v in data.values()]; lo=min(vals); hi=max(vals)
 for i,p in enumerate(sets):
  y=y0+i*rowh
  svg.append(f'<text x="30" y="{y+15}">{html.escape(p)}</text>')
  for j,b in enumerate((1,2,3,4)):
   x=left+j*colw; v=data[(p,b)]; svg.append(f'<rect x="{x}" y="{y}" width="74" height="19" fill="{color(v,lo,hi)}" stroke="#ddd"/>'); svg.append(f'<text x="{x+5}" y="{y+14}" fill="{"white" if (v-lo)/(hi-lo or 1)>.55 else "#111"}">{v:.4f}</text>')
svg.append('</svg>')
(DEST/'S3_CORRECTED_GREEDY_HEATMAP.svg').write_text('\n'.join(svg),encoding='utf-8')
# Corrected 63-set paired lookahead contrasts, only effect estimates and pointwise intervals.
w,h=1200,920; svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">','<rect width="100%" height="100%" fill="white"/>','<style>text{font-family:Arial,sans-serif;font-size:11px}.title{font-size:20px;font-weight:bold}.head{font-size:14px;font-weight:bold}</style>','<text x="25" y="32" class="title">Corrected S3: 2-step lookahead − one-step Greedy at B=2</text>','<text x="25" y="53">All 63 metric subsets; paired SCM regret differences; pointwise 95% bootstrap intervals; post-hoc.</text>']
for panel,cohort in enumerate(('C_DEVELOPMENT','C_HELDOUT')):
 rs=[r for r in ints if r['cohort']==cohort and 'LOOKAHEAD2' in r['contrast']]
 rs.sort(key=lambda r:(float(r['mean_difference']),r['contrast']))
 x0=280; width=850; y0=95+panel*400; rowh=5.2
 vals=[float(r['mean_difference']) for r in rs]; lows=[float(r['ci95_low']) for r in rs]; highs=[float(r['ci95_high']) for r in rs]; lim=max(abs(min(lows)),abs(max(highs)),1e-9)
 def xpos(v):return x0+(v+lim)/(2*lim)*width
 svg.append(f'<text x="25" y="{y0-15}" class="head">{cohort}</text>')
 svg.append(f'<line x1="{xpos(0)}" y1="{y0-5}" x2="{xpos(0)}" y2="{y0+len(rs)*rowh}" stroke="#333"/>')
 for i,r in enumerate(rs):
  y=y0+i*rowh; lo=float(r['ci95_low']); hi=float(r['ci95_high']); mean=float(r['mean_difference']); label=r['contrast'].replace('_LOOKAHEAD2','').replace(' - ',' − ')
  if i%3==0:svg.append(f'<text x="25" y="{y+4}">{html.escape(label[:42])}</text>')
  svg.append(f'<line x1="{xpos(lo)}" y1="{y}" x2="{xpos(hi)}" y2="{y}" stroke="#3973ac" stroke-width="1.4"/><circle cx="{xpos(mean)}" cy="{y}" r="2.3" fill="#d04a35"/>')
svg.append('</svg>')
(DEST/'S3_CORRECTED_LOOKAHEAD_PAIRED.svg').write_text('\n'.join(svg),encoding='utf-8')
print('rendered two corrected SVG figures')

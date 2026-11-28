"""Render simple, source-linked SVG curves from final saved E aggregates."""
import csv
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
DATA=ROOT/'research/budget_adaptive_repair/outputs/final_extension_v1/budget_policy_aggregate.csv'
OUT=ROOT/'research/budget_adaptive_repair/figures'
POLICIES=['S0','M4','FULL_GREEDY','T5_GUIDED_M4','M2+M4','FULL_T1_T6','GRAPH_FREE_ASSOCIATION']
COLORS={'S0':'#555555','M4':'#1769aa','FULL_GREEDY':'#c23b22','T5_GUIDED_M4':'#008f72','M2+M4':'#8e44ad','FULL_T1_T6':'#d18b00','GRAPH_FREE_ASSOCIATION':'#222222'}
LABELS={'S0':'No repair','M4':'Frozen M4','FULL_GREEDY':'Full Greedy','T5_GUIDED_M4':'T5-guided M4','M2+M4':'M2+M4','FULL_T1_T6':'Full T1-T6','GRAPH_FREE_ASSOCIATION':'Graph-free'}
def esc(s): return s.replace('&','&amp;').replace('<','&lt;')
def main():
    rows=list(csv.DictReader(DATA.open(encoding='utf-8'))); OUT.mkdir(parents=True,exist_ok=True)
    for cohort,title,ykey,filename,ylabel in [
      ('S4_DEVELOPMENT_80','S4 Development (80 SCMs)','mean_loss','E_extension_S4_development_budget_regret.svg','Mean analytic regret'),
      ('S4_INDEPENDENT_REPLICATION_160','S4 Independent replication (160 SCMs)','mean_loss','E_extension_S4_replication_budget_regret.svg','Mean analytic regret'),
      ('S5_EXTERNAL_G0','S5 conditional external (200 G0 draws)','mean_loss','E_extension_S5_budget_tracking_loss.svg','Mean standardized tracking loss')]:
        rr=[r for r in rows if r['cohort']==cohort and r['policy'] in POLICIES and r['budget'] in ['0','1','2','3','4']]
        vals=[float(r[ykey]) for r in rr]; lo=min(vals); hi=max(vals); span=max(hi-lo,1e-12)
        W,H=900,520; left,right,top,bottom=90,260,70,90; pw=W-left-right; ph=H-top-bottom
        def x(b): return left+int(b/4*pw)
        def y(v): return top+int((hi-v)/span*ph)
        out=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">','<rect width="100%" height="100%" fill="white"/>',f'<text x="{left}" y="35" font-family="Arial" font-size="21" font-weight="bold">{esc(title)}</text>',f'<text x="{left}" y="57" font-family="Arial" font-size="13">Budget B=0–4; {esc(ylabel)}; saved results; exploratory/descriptive</text>']
        for i in range(5):
            xx=x(i); out.append(f'<line x1="{xx}" y1="{top}" x2="{xx}" y2="{H-bottom}" stroke="#dddddd"/>'); out.append(f'<text x="{xx}" y="{H-bottom+24}" text-anchor="middle" font-family="Arial" font-size="13">{i}</text>')
        for j in range(5):
            v=lo+(hi-lo)*j/4; yy=y(v); out.append(f'<line x1="{left}" y1="{yy}" x2="{W-right}" y2="{yy}" stroke="#e7e7e7"/>'); out.append(f'<text x="{left-10}" y="{yy+4}" text-anchor="end" font-family="Arial" font-size="11">{v:.4f}</text>')
        out.append(f'<text x="{left+pw/2}" y="{H-24}" text-anchor="middle" font-family="Arial" font-size="14">Maximum allowed atomic edits (B)</text>')
        out.append(f'<text x="20" y="{top+ph/2}" transform="rotate(-90 20 {top+ph/2})" text-anchor="middle" font-family="Arial" font-size="14">{esc(ylabel)}</text>')
        for pi,p in enumerate(POLICIES):
            data=sorted([r for r in rr if r['policy']==p],key=lambda r:int(r['budget']))
            if not data: continue
            pts=' '.join(f'{x(int(r["budget"]))},{y(float(r[ykey]))}' for r in data)
            out.append(f'<polyline points="{pts}" fill="none" stroke="{COLORS[p]}" stroke-width="2.5"/>')
            for r in data: out.append(f'<circle cx="{x(int(r["budget"]))}" cy="{y(float(r[ykey]))}" r="3.5" fill="{COLORS[p]}"/>')
            ly=top+pi*24; out.append(f'<line x1="{W-right+18}" y1="{ly}" x2="{W-right+42}" y2="{ly}" stroke="{COLORS[p]}" stroke-width="3"/><text x="{W-right+50}" y="{ly+4}" font-family="Arial" font-size="12">{esc(LABELS[p])}</text>')
        out.append('</svg>'); (OUT/filename).write_text('\n'.join(out)+'\n',encoding='utf-8')
if __name__=='__main__': main()

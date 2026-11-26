"""Postprocess locked E2/E3 unit results into public aggregates and SVG figures."""
import csv, json, math
from pathlib import Path
from collections import defaultdict
import numpy as np
HERE=Path(__file__).resolve().parent; OUT=HERE/'outputs'; FIG=HERE/'figures'; FIG.mkdir(exist_ok=True)
BOOT=10_000; SEED=2026112604
def read(name): return list(csv.DictReader((OUT/name).open(encoding='utf-8')))
def write(name,rows):
 if not rows:return
 with (OUT/name).open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=list(dict.fromkeys(k for r in rows for k in r)));w.writeheader();w.writerows(rows)
def pareto(points):
 result=[]
 for p in points:
  dom=any(q['cost']<=p['cost']+1e-12 and q['loss']<=p['loss']+1e-12 and (q['cost']<p['cost']-1e-12 or q['loss']<p['loss']-1e-12) for q in points if q is not p)
  if not dom:result.append(p)
 return result
def svg_start(title,w=1000,h=650):
 return [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">','<rect width="100%" height="100%" fill="white"/>',f'<text x="{w/2}" y="28" text-anchor="middle" font-family="Arial" font-size="18" font-weight="bold">{title}</text>']
def svg_end(lines,path):
 lines.append('</svg>');Path(path).write_text('\n'.join(lines),encoding='utf-8')
def plot_lines(rows,path,title,cohort,policies,metric='mean_regret',ylabel='Mean regret'):
 W,H=1000,620;L=100;R=30;T=60;B=70; x0,x1=L,W-R;y0,y1=T,H-B
 vals=[float(r[metric]) for r in rows if r['cohort']==cohort and r['policy'] in policies]; ymin=min(vals);ymax=max(vals);pad=max((ymax-ymin)*.08,1e-5);ymin-=pad;ymax+=pad
 ls=svg_start(title,W,H);ls += [f'<line x1="{x0}" y1="{y1}" x2="{x1}" y2="{y1}" stroke="#333"/>',f'<line x1="{x0}" y1="{y0}" x2="{x0}" y2="{y1}" stroke="#333"/>']
 budgets=sorted({int(r['budget']) for r in rows if r['cohort']==cohort})
 for b in budgets:
  x=x0+(x1-x0)*(b-min(budgets))/max(1,max(budgets)-min(budgets));ls.append(f'<line x1="{x:.1f}" y1="{y1}" x2="{x:.1f}" y2="{y1+5}" stroke="#333"/><text x="{x:.1f}" y="{y1+23}" text-anchor="middle" font-family="Arial" font-size="12">{b}</text>')
 for t in range(5):
  v=ymin+(ymax-ymin)*t/4;y=y1-(y1-y0)*t/4;ls.append(f'<line x1="{x0}" y1="{y:.1f}" x2="{x1}" y2="{y:.1f}" stroke="#ddd"/><text x="{x0-10}" y="{y+4:.1f}" text-anchor="end" font-family="Arial" font-size="11">{v:.3g}</text>')
 palette=['#1f77b4','#d62728','#2ca02c','#9467bd','#ff7f0e','#17becf']
 for j,p in enumerate(policies):
  xs=sorted([r for r in rows if r['cohort']==cohort and r['policy']==p],key=lambda r:int(r['budget']))
  coords=[]
  for r in xs:
   b=int(r['budget']);x=x0+(x1-x0)*b/max(1,max(budgets));v=float(r[metric]);y=y1-(v-ymin)/(ymax-ymin)*(y1-y0);coords.append(f'{x:.1f},{y:.1f}')
  color=palette[j%len(palette)];ls.append(f'<polyline points="{" ".join(coords)}" fill="none" stroke="{color}" stroke-width="2"/>')
  for c in coords:
   x,y=c.split(',');ls.append(f'<circle cx="{x}" cy="{y}" r="3" fill="{color}"/>')
  ly=50+j*18;ls.append(f'<text x="{x1-160}" y="{ly}" font-family="Arial" font-size="12" fill="{color}">{p}</text>')
 ls.append(f'<text x="{(x0+x1)/2}" y="{H-20}" text-anchor="middle" font-family="Arial" font-size="13">Maximum edit budget B (atomic edits)</text>')
 ls.append(f'<text transform="translate(22 {(y0+y1)/2}) rotate(-90)" text-anchor="middle" font-family="Arial" font-size="13">{ylabel}</text>')
 svg_end(ls,path)
def main():
 e2=read('c_extended_budget_results.csv');agg=[];groups=defaultdict(list)
 for r in e2: 
  for k in ('budget','loss','cost','unused','task_edits','offtask_edits','remaining_errors','action','initial_errors','terminal_policy_candidate_count','terminal_policy_feasible_count','terminal_all_candidate_count','terminal_all_feasible_count'):r[k]=float(r[k]) if k not in ('budget',) else int(r[k])
  for k in ('constraint_saturated','policy_candidate_saturated','structurally_saturated','same_as_s0'):r[k]=r[k].lower()=='true'
  groups[(r['cohort'],r['policy'],r['budget'])].append(r)
 for (co,p,b),rs in sorted(groups.items()):
  agg.append({'cohort':co,'policy':p,'budget':b,'n':len(rs),'mean_regret':np.mean([r['loss'] for r in rs]),'mean_cost':np.mean([r['cost'] for r in rs]),
    'mean_remaining_errors':np.mean([r['remaining_errors'] for r in rs]),'mean_task_edits':np.mean([r['task_edits'] for r in rs]),'mean_offtask_edits':np.mean([r['offtask_edits'] for r in rs]),
    'action_change_rate':np.mean([not r['same_as_s0'] for r in rs]),'no_op_rate':np.mean([r['cost']==0 for r in rs]),
    'terminal_policy_candidate_mean':np.mean([r['terminal_policy_candidate_count'] for r in rs]),'terminal_policy_feasible_mean':np.mean([r['terminal_policy_feasible_count'] for r in rs])})
 # D is deliberately aggregate-only: use the saved 85-row independent audit curve.
 for x in read('d_final_aggregate_results.csv'):
  agg.append({'cohort':'D_FINAL','policy':x['policy'],'budget':int(x['budget']),'n':200,
   'mean_regret':float(x['loss']),'mean_cost':float(x['cost']),'mean_remaining_errors':None,
   'mean_task_edits':float(x['task_edits']),'mean_offtask_edits':float(x['offtask_edits']),
   'action_change_rate':None,'no_op_rate':float(x['no_op_rate']),
   'terminal_policy_candidate_mean':None,'terminal_policy_feasible_mean':None})
 # Only the documented B=2 graph-free loss is available in the independent-audit summary.
 agg.append({'cohort':'D_FINAL','policy':'GRAPH_FREE_ASSOCIATION','budget':2,'n':200,
  'mean_regret':0.7893621879206892,'mean_cost':0.0,'mean_remaining_errors':None,'mean_task_edits':0.0,
  'mean_offtask_edits':0.0,'action_change_rate':None,'no_op_rate':1.0,'terminal_policy_candidate_mean':None,'terminal_policy_feasible_mean':None})
 write('e2_extended_budget_aggregate.csv',agg)
 # paired marginal increments with SCM bootstrap; same sampled units for all adjacent budgets.
 rng=np.random.default_rng(SEED);marg=[]
 for co in ('C_DEVELOPMENT','C_HELDOUT'):
  policies=sorted({r['policy'] for r in e2 if r['cohort']==co});maxb=max(r['budget'] for r in e2 if r['cohort']==co);ids=sorted({r['scm_id'] for r in e2 if r['cohort']==co});N=len(ids);idx={x:i for i,x in enumerate(ids)}
  for pol in policies:
   for b in range(1,maxb+1):
    a=sorted([r for r in e2 if r['cohort']==co and r['policy']==pol and r['budget']==b-1],key=lambda r:r['scm_id']);z=sorted([r for r in e2 if r['cohort']==co and r['policy']==pol and r['budget']==b],key=lambda r:r['scm_id']);
    if len(a)!=N or len(z)!=N: raise RuntimeError('missing paired budget rows')
    benefit=np.array([x['loss']-y['loss'] for x,y in zip(a,z)]);dcost=np.array([y['cost']-x['cost'] for x,y in zip(a,z)]);samples= rng.integers(0,N,size=(BOOT,N));boot=benefit[samples].mean(axis=1)
    md=float(dcost.mean());mb=float(benefit.mean())
    marg.append({'cohort':co,'policy':pol,'from_budget':b-1,'to_budget':b,'mean_marginal_benefit':mb,'paired_bootstrap95_lo':np.quantile(boot,.025),'paired_bootstrap95_hi':np.quantile(boot,.975),
     'mean_added_edit_count':md,'benefit_per_added_edit':mb/md if md>1e-15 else None,'zero_added_edit_fraction':np.mean(dcost==0),'improved_fraction':np.mean(benefit>1e-12),'worsened_fraction':np.mean(benefit< -1e-12),'unchanged_fraction':np.mean(np.abs(benefit)<=1e-12),
     'edit_added_but_loss_unchanged_fraction':np.mean((dcost>0)&(np.abs(benefit)<=1e-12))})
 write('e2_extended_marginal_benefit.csv',marg)
 # Saturation: terminal graph vs policy-eligible candidates vs decision sequence.
 sat=[]
 for co in ('C_DEVELOPMENT','C_HELDOUT'):
  maxb=max(r['budget'] for r in e2 if r['cohort']==co); last=[r for r in e2 if r['cohort']==co and r['budget']==maxb]
  for pol in sorted({r['policy'] for r in last}):
   xs=[r for r in last if r['policy']==pol]; sat.append({'cohort':co,'policy':pol,'B_max':maxb,'n':len(xs),'structurally_saturated_fraction':np.mean([r['structurally_saturated'] for r in xs]),
      'policy_candidate_saturated_fraction':np.mean([r['policy_candidate_saturated'] for r in xs]),'constraint_saturated_fraction':np.mean([r['constraint_saturated'] for r in xs]),
      'any_policy_feasible_candidates_fraction':np.mean([r['terminal_policy_feasible_count']>0 for r in xs]),'mean_residual_error_count':np.mean([r['remaining_errors'] for r in xs])})
 write('e2_saturation_diagnostics.csv',sat)
 # Cost/performance frontiers at maximum allowed B, all cross-budget options, and D graph-free.
 front=[]
 d=read('d_final_aggregate_results.csv')
 for co in ('C_DEVELOPMENT','C_HELDOUT','D_FINAL'):
  rs=[x for x in agg if x['cohort']==co];maxb=max(x['budget'] for x in rs)
  for cap in range(maxb+1):
   pts=[{'cohort':co,'policy':x['policy'],'budget':x['budget'],'cost':float(x['mean_cost']),'loss':float(x['mean_regret'])} for x in rs if x['budget']<=cap]
   if co=='D_FINAL':
    pts.append({'cohort':co,'policy':'GRAPH_FREE_ASSOCIATION','budget':0,'cost':0.,'loss':0.7893621879206892})
   for x in pareto(pts):front.append({'frontier':'FIXED_MAX_BUDGET','max_budget':cap,**x})
  pts=[{'cohort':co,'policy':x['policy'],'budget':x['budget'],'cost':float(x['mean_cost']),'loss':float(x['mean_regret'])} for x in rs]
  if co=='D_FINAL':pts.append({'cohort':co,'policy':'GRAPH_FREE_ASSOCIATION','budget':0,'cost':0.,'loss':0.7893621879206892})
  for x in pareto(pts):front.append({'frontier':'CROSS_BUDGET','max_budget':maxb,**x})
 write('e2_extended_pareto_frontiers.csv',front)
 # Adaptive comparisons, paired on same original SCMs.
 adapt=read('adaptive_m4_unit_results.csv')
 for r in adapt:r['budget']=int(r['budget'])
 lookup={(r['cohort'],r['scm_id'],r['budget']):r for r in adapt};compare=[]
 for co in ('C_DEVELOPMENT','C_HELDOUT'):
  maxb=max(r['budget'] for r in adapt if r['cohort']==co);ids=sorted({r['scm_id'] for r in adapt if r['cohort']==co});N=len(ids)
  for b in range(maxb+1):
   for other in ('M4','M2+M4','M1+M2+M3+M4'):
    pairs=[]
    for sid in ids:
     a=lookup[(co,sid,b)];q=next(x for x in e2 if x['cohort']==co and x['scm_id']==sid and x['policy']==other and int(x['budget'])==b)
     pairs.append((float(a['regret'])-float(q['loss']),float(a['cost'])-float(q['cost'])))
    dl=np.array([x[0] for x in pairs]);dc=np.array([x[1] for x in pairs]);ix=rng.integers(0,N,size=(BOOT,N));boot=dl[ix].mean(axis=1)
    compare.append({'cohort':co,'budget':b,'adaptive_vs':other,'n':N,'mean_regret_difference_adaptive_minus_comparator':dl.mean(),'paired_bootstrap95_lo':np.quantile(boot,.025),'paired_bootstrap95_hi':np.quantile(boot,.975),
      'mean_edit_count_difference':dc.mean(),'adaptive_better_fraction':np.mean(dl< -1e-12),'adaptive_worse_fraction':np.mean(dl>1e-12),'tie_fraction':np.mean(np.abs(dl)<=1e-12)})
 write('e3_adaptive_paired_comparisons.csv',compare)
 # Adaptive point on the same observed C cost frontier (exploratory, SCM-level).
 e3front=[]
 for co in ('C_DEVELOPMENT','C_HELDOUT'):
  candidates=[{'cohort':co,'policy':x['policy'],'budget':int(x['budget']),'cost':float(x['mean_cost']),'loss':float(x['mean_regret'])} for x in agg if x['cohort']==co and x['policy']!='GRAPH_FREE_ASSOCIATION']
  candidates += [{'cohort':co,'policy':'ADAPTIVE_M4_BLOCKER_AWARE','budget':int(x['budget']),'cost':float(x['mean_cost']),'loss':float(x['mean_regret'])} for x in read('adaptive_m4_aggregate.csv') if x['cohort']==co]
  for x in pareto(candidates):e3front.append({'cohort':co,'frontier':'cross-budget exploratory','policy':x['policy'],'budget':x['budget'],'cost':x['cost'],'loss':x['loss']})
 write('e3_adaptive_pareto.csv',e3front)
 # Decision saturation is the first B whose later action and loss stay unchanged.
 decision=[]
 for co in ('C_DEVELOPMENT','C_HELDOUT'):
  for pol in sorted({r['policy'] for r in e2 if r['cohort']==co}):
   ids=sorted({r['scm_id'] for r in e2 if r['cohort']==co and r['policy']==pol})
   for sid in ids:
    xs=sorted([r for r in e2 if r['cohort']==co and r['policy']==pol and r['scm_id']==sid],key=lambda r:int(r['budget']))
    first=None
    for i,x in enumerate(xs):
     if all(y['action']==x['action'] and abs(float(y['loss'])-float(x['loss']))<=1e-12 for y in xs[i:]):first=x['budget'];break
    decision.append({'cohort':co,'policy':pol,'scm_id':sid,'decision_saturation_budget':first})
 # compact distributions by policy
 decisions=[]
 for co in ('C_DEVELOPMENT','C_HELDOUT'):
  for pol in sorted({x['policy'] for x in decision if x['cohort']==co}):
   xs=[x['decision_saturation_budget'] for x in decision if x['cohort']==co and x['policy']==pol and x['decision_saturation_budget'] is not None]
   decisions.append({'cohort':co,'policy':pol,'n_saturated':len(xs),'fraction_saturated':len(xs)/len([x for x in decision if x['cohort']==co and x['policy']==pol]),'median_first_stable_budget':float(np.median(xs)) if xs else None})
 write('e2_decision_saturation.csv',decisions)
 # E3 target sensitivity summaries already exist; report internal grid optimum support.
 # Figures use labeled SVG, all exploratory and cohort-specific.
 summary_rows=[{**x,'cohort':x['cohort']} for x in agg]
 for co in ('C_DEVELOPMENT','C_HELDOUT'):
  plot_lines(summary_rows,FIG/f'E2_curves_{co}.svg',f'Research E budget-performance ({co}; SCM-level)',co,['S0','M4','M2+M4','M1+M2+M3+M4'])
 # Heatmap, all 17 policies (3 panels; B0-4 only for common display).
 policies=sorted({r['policy'] for r in agg if r['budget']<=4}); colors=['#2166ac','#67a9cf','#f7f7f7','#ef8a62','#b2182b']
 lines=svg_start('Research E: mean loss/regret by policy and budget (exploratory)',1200,770); maxv=max(float(x['mean_regret']) for x in agg if int(x['budget'])<=4)
 for pi,co in enumerate(('C_DEVELOPMENT','C_HELDOUT','D_FINAL')):
  ox=20+pi*395; lines.append(f'<text x="{ox+180}" y="60" text-anchor="middle" font-family="Arial" font-size="14" font-weight="bold">{co}</text>')
  for yi,p in enumerate(policies):
   y=85+yi*35
   if pi==0:lines.append(f'<text x="{ox+80}" y="{y+20}" text-anchor="end" font-family="Arial" font-size="10">{p}</text>')
   for b in range(5):
    r=next((x for x in agg if x['cohort']==co and x['policy']==p and int(x['budget'])==b),None)
    if r is None:continue
    v=float(r['mean_regret']); t=min(.999,max(0,v/maxv)); col=colors[min(4,int(t*5))];x=ox+90+b*52
    lines.append(f'<rect x="{x}" y="{y}" width="48" height="28" fill="{col}" stroke="white"/><title>{p}; B={b}; mean={v:.6g}</title>')
    lines.append(f'<text x="{x+24}" y="{y+19}" text-anchor="middle" font-family="Arial" font-size="9">{v:.3f}</text>')
 svg_end(lines,FIG/'E1_policy_budget_heatmap.svg')
 # Primary comparison curve / fixed subset heatmap covers means, marginal chart key policies.
 margrows=marg
 for co in ('C_DEVELOPMENT','C_HELDOUT'):
  plot_lines(agg,FIG/f'E2_key_policy_curves_{co}.svg',f'Budget and decision performance: {co}',co,['S0','M4','M2+M4','M1+M2+M3+M4'])
 # Pareto at largest cap, cross-budget, D graph-free.
 for co in ('C_DEVELOPMENT','C_HELDOUT','D_FINAL'):
  pts=[x for x in front if x['cohort']==co and x['frontier']=='CROSS_BUDGET']
  maxcap=max(int(x['max_budget']) for x in pts)
  fixed2=[x for x in front if x['cohort']==co and x['frontier']=='FIXED_MAX_BUDGET' and int(x['max_budget'])==min(2,maxcap)]
  fixedmax=[x for x in front if x['cohort']==co and x['frontier']=='FIXED_MAX_BUDGET' and int(x['max_budget'])==maxcap]
  W,H=900,560;ls=svg_start(f'Cost-performance Pareto frontiers — {co}',W,H);x0,y0=80,70;x1,y1=780,440
  maxc=max(float(x['cost']) for x in pts);minl=min(float(x['loss']) for x in pts);maxl=max(float(x['loss']) for x in pts)
  for group,color,shape in ((fixed2,'#d62728','circle'),(fixedmax,'#2ca02c','rect'),(pts,'#2166ac','circle')):
   for x in group:
    cx=x0+float(x['cost'])/max(maxc,1e-9)*(x1-x0);cy=y1-(float(x['loss'])-minl)/max(maxl-minl,1e-9)*(y1-y0)
    mark=(f'<circle cx="{cx}" cy="{cy}" r="6" fill="{color}"/>' if shape=='circle' else f'<rect x="{cx-5}" y="{cy-5}" width="10" height="10" fill="{color}"/>')
    ls.append(mark+f'<title>{x["policy"]}@B{x["budget"]}, cost={float(x["cost"]):.5g}, loss={float(x["loss"]):.6g}</title>')
  for y,col,label in ((490,'#d62728','fixed max B=2'),(510,'#2ca02c',f'fixed max B={maxcap}'),(530,'#2166ac','cross-budget')):ls.append(f'<circle cx="120" cy="{y-4}" r="5" fill="{col}"/><text x="135" y="{y}" font-family="Arial" font-size="11">{label}</text>')
  ls.append(f'<text x="{(x0+x1)/2}" y="475" text-anchor="middle" font-family="Arial" font-size="12">Mean atomic edge edits (C regret vs D tracking loss; never pooled)</text>');ls.append(f'<text transform="translate(20 260) rotate(-90)" text-anchor="middle" font-family="Arial" font-size="12">Mean loss / regret</text>');svg_end(ls,FIG/f'E4_pareto_{co}.svg')
 # Adaptive curve and target sensitivity B=2 M4.
 adapagg=[{**x,'policy':'ADAPTIVE_M4_BLOCKER_AWARE'} for x in read('adaptive_m4_aggregate.csv')]
 for co in ('C_DEVELOPMENT','C_HELDOUT'):
  combined=[x for x in summary_rows if x['cohort']==co and x['policy'] in ('M4','M2+M4','M1+M2+M3+M4')]+[x for x in adapagg if x['cohort']==co]
  plot_lines(combined,FIG/f'E7_adaptive_M4_{co}.svg',f'Adaptive M4 vs existing policies (exploratory): {co}',co,['M4','M2+M4','M1+M2+M3+M4','ADAPTIVE_M4_BLOCKER_AWARE'])
 sens=read('target_sensitivity_aggregate.csv')
 for co in ('C_DEVELOPMENT','C_HELDOUT'):
  xs=[x for x in sens if x['cohort']==co and x['budget']=='2' and x['policy']=='M4'];W,H=760,500;ls=svg_start(f'Target sensitivity, M4 B=2 — {co}',W,H);x0,y0=80,70;x1,y1=710,420;v=[float(x['mean_regret']) for x in xs];lo=min(v);hi=max(v);pts=[]
  for i,r in enumerate(sorted(xs,key=lambda x:float(x['target_delta']))):
   x=x0+i*(x1-x0)/max(1,len(xs)-1);y=y1-(float(r['mean_regret'])-lo)/max(hi-lo,1e-8)*(y1-y0);pts.append(f'{x:.1f},{y:.1f}');ls.append(f'<text x="{x:.1f}" y="{y1+20}" text-anchor="middle" font-family="Arial" font-size="11">δ={r["target_delta"]}</text>')
  ls.append(f'<polyline points="{" ".join(pts)}" fill="none" stroke="#d62728" stroke-width="2"/>');ls.append('<text x="380" y="470" text-anchor="middle" font-family="Arial" font-size="12">Target = train mean + δ × train SD; same five actions</text>');svg_end(ls,FIG/f'E8_target_sensitivity_{co}.svg')
 # E3: paired marginal benefit, retaining harmful budget increments below zero.
 em=read('e2_extended_marginal_benefit.csv')
 for co in ('C_DEVELOPMENT','C_HELDOUT'):
  xs=[r for r in em if r['cohort']==co and r['policy'] in ('M2','M4','M2+M4','M1+M2+M3+M4')];W,H=1000,620;L,R,T,B=90,30,60,75;x0,x1=L,W-R;y0,y1=T,H-B
  vals=[float(r['mean_marginal_benefit']) for r in xs];lo=min(min(vals),0);hi=max(max(vals),0);pad=max((hi-lo)*.08,1e-5);lo-=pad;hi+=pad;ls=svg_start(f'Paired marginal benefit by added budget — {co}',W,H)
  zero=y1-(0-lo)/(hi-lo)*(y1-y0);ls.append(f'<line x1="{x0}" y1="{zero:.1f}" x2="{x1}" y2="{zero:.1f}" stroke="#222" stroke-dasharray="5 3"/>')
  palette=['#1f77b4','#d62728','#2ca02c','#9467bd']
  for j,p in enumerate(('M2','M4','M2+M4','M1+M2+M3+M4')):
   pr=sorted([r for r in xs if r['policy']==p],key=lambda r:int(r['to_budget']));coords=[]
   for r in pr:
    b=int(r['to_budget']);x=x0+(x1-x0)*b/max(1,max(int(x['to_budget']) for x in pr));v=float(r['mean_marginal_benefit']);y=y1-(v-lo)/(hi-lo)*(y1-y0);coords.append(f'{x:.1f},{y:.1f}')
   ls.append(f'<polyline points="{" ".join(coords)}" fill="none" stroke="{palette[j]}" stroke-width="2"/>')
   ls.append(f'<text x="{x1-165}" y="{65+j*17}" font-family="Arial" font-size="12" fill="{palette[j]}">{p}</text>')
  ls.append('<text x="500" y="585" text-anchor="middle" font-family="Arial" font-size="12">B increment; SCM-paired bootstrap interval in companion CSV; positive = improvement</text>');svg_end(ls,FIG/f'E3_marginal_benefit_{co}.svg')
 # E5: cost-weighted policy choices on the supplied lambda grid (ties retained in table).
 lam=read('lambda_optima.csv')
 for co in ('C_DEVELOPMENT','C_HELDOUT','D_FINAL'):
  xs=[r for r in lam if r['cohort']==co];W,H=1100,600;ls=svg_start(f'Lambda-grid optimal observed candidates — {co}',W,H)
  grid=sorted({float(r['lambda']) for r in xs});opts=[]
  for x,lmb in enumerate(grid):
   winners=sorted({f"{r['policy']}@{r['budget']}" for r in xs if float(r['lambda'])==lmb});
   ls.append(f'<text x="{90+x*105}" y="95" text-anchor="middle" font-family="Arial" font-size="11">λ={lmb:g}</text>')
   ls.append(f'<rect x="{45+x*105}" y="115" width="95" height="370" fill="#f4f6f8" stroke="#ccc"/>')
   for j,name in enumerate(winners[:18]):ls.append(f'<text x="{92+x*105}" y="{140+j*18}" text-anchor="middle" font-family="Arial" font-size="10">{name}</text>')
  ls.append('<text x="550" y="540" text-anchor="middle" font-family="Arial" font-size="12">λ is hypothetical loss-units per atomic edge edit; exact intervals in lambda_exact_intervals.csv</text>');svg_end(ls,FIG/f'E5_lambda_choices_{co}.svg')
 # E6: keep structural, policy and decision saturation distinct.
 satrows=read('e2_saturation_diagnostics.csv');decs=read('e2_decision_saturation.csv')
 for co in ('C_DEVELOPMENT','C_HELDOUT'):
  W,H=1100,620;ls=svg_start(f'Saturation types at cohort Bmax — {co}',W,H);pols=['M4','M2+M4','M1+M2+M3+M4'];colors=['#2166ac','#f28e2b','#2ca02c'];ybase=130
  for j,p in enumerate(pols):
   s=next(x for x in satrows if x['cohort']==co and x['policy']==p);d=next(x for x in decs if x['cohort']==co and x['policy']==p)
   vals=[float(s['structurally_saturated_fraction']),float(s['policy_candidate_saturated_fraction']),float(s['constraint_saturated_fraction']),float(d['fraction_saturated'])]
   for k,v in enumerate(vals):
    x=180+k*210;y=ybase+j*115;ls.append(f'<text x="{x}" y="{y-14}" text-anchor="middle" font-family="Arial" font-size="11">{v:.2f}</text>');ls.append(f'<rect x="{x-55}" y="{y}" width="110" height="{v*65:.1f}" fill="{colors[j]}"/>')
   ls.append(f'<text x="65" y="{ybase+j*115+25}" font-family="Arial" font-size="12">{p}</text>')
  for k,label in enumerate(('structural\nsaturated','no policy\ncandidate','DAG constraint\nblocked','decision\nsaturated')):
   x=180+k*210;ls.append(f'<text x="{x}" y="540" text-anchor="middle" font-family="Arial" font-size="11">{label.replace(chr(10)," ")}</text>')
  ls.append('<text x="550" y="580" text-anchor="middle" font-family="Arial" font-size="11">Fractions at the precomputed maximum budget; the four definitions are not interchangeable</text>');svg_end(ls,FIG/f'E6_saturation_{co}.svg')
 result={'status':'POSTPROCESS_COMPLETE','figures':[p.name for p in FIG.glob('*.svg')],'aggregate_rows':len(agg),'marginal_rows':len(marg),'saturation_rows':len(sat),'frontier_rows':len(front),'adaptive_comparison_rows':len(compare),'decision_saturation_rows':len(decisions),'bootstrap':{'replicates':BOOT,'seed':SEED,'unit':'paired original SCM'}}
 (OUT/'e2_e3_summary.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2))
if __name__=='__main__':main()

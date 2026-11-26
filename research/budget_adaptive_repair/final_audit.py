from __future__ import annotations
import csv, hashlib, json, math, statistics
from pathlib import Path
from collections import Counter
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'research/final_integration/research_e_audit'
SRC=ROOT/'research/budget_adaptive_repair/outputs'
BOOT=2000
BOOT_SEED=2026112699
TOL=1e-12

def read_csv(p):
 with p.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def write_csv(p, rows):
 if p.exists(): raise FileExistsError(f'refusing to overwrite {p}')
 with p.open('x',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def frontier(points):
 # Keep all exact/near coordinate ties; reject only strict Pareto domination.
 ans=[]
 for x in points:
  dominated=any(y['cost']<=x['cost']+TOL and y['loss']<=x['loss']+TOL and
    (y['cost']<x['cost']-TOL or y['loss']<x['loss']-TOL) for y in points)
  if not dominated:ans.append(x)
 return ans
def lower_envelope(points):
 # Finite exact pair crossings induce all candidate intervals for lambda >= 0.
 crossings={0.0}
 for i,a in enumerate(points):
  for b in points[i+1:]:
   den=a['cost']-b['cost']
   if abs(den)>TOL:
    x=(b['loss']-a['loss'])/den
    if x>0 and math.isfinite(x):crossings.add(x)
 xs=sorted(crossings); bounds=xs+[float('inf')]; rows=[]; winners=set(); exact=[]
 for i,lo in enumerate(xs):
  hi=bounds[i+1]; probe=lo+1 if math.isinf(hi) else (lo+hi)/2
  scores=[(p['loss']+probe*p['cost'],p['label']) for p in points]; mn=min(v for v,_ in scores)
  tie=sorted(k for v,k in scores if abs(v-mn)<=1e-10)
  winners.update(tie)
  if not rows or rows[-1]['optimal_candidates']!=';'.join(tie):
   rows.append({'lambda_lo_inclusive':lo,'lambda_hi_exclusive':hi,'probe_lambda':probe,'optimal_candidates':';'.join(tie)})
  else:
   rows[-1]['lambda_hi_exclusive']=hi
 # Include exact transition ties only; crossings between non-optimal candidates are irrelevant.
 for i in range(1,len(rows)):
  x=rows[i]['lambda_lo_inclusive']
  scores=[(p['loss']+x*p['cost'],p['label']) for p in points]; mn=min(v for v,_ in scores)
  tie=sorted(k for v,k in scores if abs(v-mn)<=1e-10)
  if len(tie)>1:
   winners.update(tie);exact.append({'lambda_value':x,'tied_optimal_candidates':';'.join(tie)})
 return rows,winners,exact

def main():
 OUT.mkdir(parents=True,exist_ok=True)
 agg=read_csv(SRC/'e2_extended_budget_aggregate.csv'); adap=read_csv(SRC/'adaptive_m4_aggregate.csv')
 unit=read_csv(SRC/'c_extended_budget_results.csv'); au=read_csv(SRC/'adaptive_m4_unit_results.csv')
 refs=read_csv(SRC/'reference_graph_learner_diagnostic.csv'); sens=read_csv(SRC/'target_sensitivity_unit_results.csv')
 sat=read_csv(SRC/'e2_saturation_diagnostics.csv'); paired=read_csv(SRC/'e3_adaptive_paired_comparisons.csv')
 # Required complete key space and no duplicate keys.
 key=lambda r:(r['cohort'],r['scm_id'],r['policy'],r['budget'])
 assert len(unit)==42704 and len({key(r) for r in unit})==len(unit)
 akey=lambda r:(r['cohort'],r['scm_id'],r['budget'])
 assert len(au)==2512 and len({akey(r) for r in au})==len(au)
 assert len(refs)==264 and len({(r['cohort'],r['scm_id']) for r in refs})==264
 counts={co:Counter(int(r['budget']) for r in unit if r['cohort']==co) for co in ('C_DEVELOPMENT','C_HELDOUT')}
 assert counts['C_DEVELOPMENT']==Counter({b:64*17 for b in range(8)})
 assert counts['C_HELDOUT']==Counter({b:200*17 for b in range(10)})
 assert sum(int(r['budget'])<=4 for r in unit)==22440
 # Reference learner diagnostic.
 refsummary=[]
 for co in ('C_DEVELOPMENT','C_HELDOUT'):
  z=[r for r in refs if r['cohort']==co];rr=[float(r['regret']) for r in z]
  refsummary.append({'cohort':co,'n':len(z),'mean_regret':statistics.mean(rr),'median_regret':statistics.median(rr),'regret_gt_1e-12_n':sum(x>1e-12 for x in rr),'selected_k_equals_grid_optimum_n':sum(abs(float(r['k'])-float(r['optimal_k']))<=TOL for r in z),'reference_learner_action_counts':json.dumps(dict(Counter(r['k'] for r in z)),sort_keys=True)})
 # Sensitivity: fixed target task delta 0, M4 B2.
 sens_rows=[]
 for co in ('C_DEVELOPMENT','C_HELDOUT'):
  z=[r for r in sens if r['cohort']==co and r['policy']=='M4' and int(r['budget'])==2 and float(r['target_delta'])==0]
  assert len(z)==(64 if co=='C_DEVELOPMENT' else 200)
  sens_rows.append({'cohort':co,'n':len(z),'selected_k_counts':json.dumps(dict(Counter(r['k'] for r in z)),sort_keys=True),'selected_equals_optimum_n':sum(abs(float(r['k'])-float(r['optimal_k']))<=TOL for r in z),'interior_optimum_n':sum(r['internal_optimum'].lower()=='true' for r in z),'mean_regret':statistics.mean(float(r['regret']) for r in z)})
 # Saturation rates are read directly from the terminal diagnostic table.
 constraint=[{'cohort':r['cohort'],'policy':r['policy'],'B_max':int(r['B_max']),'n':int(r['n']),'structurally_saturated_fraction':float(r['structurally_saturated_fraction']),'policy_candidate_saturated_fraction':float(r['policy_candidate_saturated_fraction']),'constraint_saturated_fraction':float(r['constraint_saturated_fraction']),'mean_residual_error_count':float(r['mean_residual_error_count'])} for r in sat]
 # Aggregate extended points and Adaptive M4 together (C only).
 by={(r['cohort'],r['policy'],int(r['budget'])):{'cohort':r['cohort'],'policy':r['policy'],'budget':int(r['budget']),'n':int(r['n']),'loss':float(r['mean_regret']),'cost':float(r['mean_cost'])} for r in agg if r['cohort'].startswith('C_')}
 for r in adap:
  co=r['cohort'];b=int(r['budget']);by[(co,'ADAPTIVE_M4_BLOCKER_AWARE',b)]={'cohort':co,'policy':'ADAPTIVE_M4_BLOCKER_AWARE','budget':b,'n':int(r['n']),'loss':float(r['mean_regret']),'cost':float(r['mean_cost'])}
 all_front=[];lambda_rows=[];lambda_break_rows=[];lambda_winners={};bootstrap_rows=[]
 rng=np.random.default_rng(BOOT_SEED)
 for co,n in [('C_DEVELOPMENT',64),('C_HELDOUT',200)]:
  cap=7 if co=='C_DEVELOPMENT' else 9
  points=[dict(v,label=f"{v['policy']}@B{v['budget']}") for k,v in by.items() if k[0]==co]
  assert len(points)==18*(cap+1)
  cross=frontier(points);fixed=frontier([x for x in points if x['budget']==cap])
  env,wins,breaks=lower_envelope(points);lambda_winners[co]=sorted(wins)
  lambda_break_rows.extend({'cohort':co,**x} for x in breaks)
  for x in cross:all_front.append({'frontier':'CROSS_BUDGET','max_budget':cap,'cohort':co,'policy':x['policy'],'budget':x['budget'],'cost':x['cost'],'loss':x['loss'],'label':x['label'],'supported_by_nonnegative_lambda':x['label'] in wins})
  for x in fixed:all_front.append({'frontier':'FIXED_MAX_BUDGET','max_budget':cap,'cohort':co,'policy':x['policy'],'budget':x['budget'],'cost':x['cost'],'loss':x['loss'],'label':x['label'],'supported_by_nonnegative_lambda':x['label'] in wins})
  for i,row in enumerate(env):
   item={'cohort':co,**row,'supported_candidates':row['optimal_candidates']}
   lambda_rows.append(item)
  # Joint unit bootstrap across all policy/budget candidates, preserving pairing.
  original=[r for r in unit if r['cohort']==co]
  ids=sorted({r['scm_id'] for r in original});assert len(ids)==n
  labels=sorted(f"{p}@B{b}" for p in ({r['policy'] for r in original}|{'ADAPTIVE_M4_BLOCKER_AWARE'}) for b in range(cap+1))
  idx={s:i for i,s in enumerate(ids)}; lidx={s:i for i,s in enumerate(labels)}
  cm=np.full((n,len(labels)),np.nan);lm=np.full_like(cm,np.nan)
  for r in original:
   i=idx[r['scm_id']];j=lidx[f"{r['policy']}@B{int(r['budget'])}"];cm[i,j]=float(r['cost']);lm[i,j]=float(r['loss'])
  for r in au:
   if r['cohort']==co:
    i=idx[r['scm_id']];j=lidx[f"ADAPTIVE_M4_BLOCKER_AWARE@B{int(r['budget'])}"];cm[i,j]=float(r['cost']);lm[i,j]=float(r['regret'])
  assert np.isfinite(cm).all() and np.isfinite(lm).all()
  inc=np.zeros(len(labels),dtype=np.int64); total=0
  for start in range(BOOT):
   sample=rng.integers(0,n,size=n);cost=cm[sample].mean(axis=0);loss=lm[sample].mean(axis=0)
   # unique points; identical coordinates are retained as a tie group on frontier
   on=np.ones(len(labels),dtype=bool)
   for j in range(len(labels)):
    dominates=(cost<=cost[j]+TOL)&(loss<=loss[j]+TOL)&((cost<cost[j]-TOL)|(loss<loss[j]-TOL))
    if dominates.any():on[j]=False
   inc+=on;total+=int(on.sum())
  for j,label in enumerate(labels):bootstrap_rows.append({'cohort':co,'candidate':label,'bootstrap_replicates':BOOT,'seed':BOOT_SEED,'frontier_inclusion_fraction':inc[j]/BOOT})
 # Unit-level Adaptive paired B3 Held-out count and contrasts.
 held=[r for r in paired if r['cohort']=='C_HELDOUT' and int(r['budget'])==3 and r['adaptive_vs']=='M4'][0]
 # Cross-check B3 cost/regret from independent aggregates.
 def get(co,p,b):return by[(co,p,b)]
 assert abs(get('C_HELDOUT','M4',3)['cost']-.760)<1e-12
 assert abs(get('C_HELDOUT','M1+M2+M3+M4',3)['cost']-1.790)<1e-12
 assert abs(get('C_HELDOUT','M2+M4',3)['cost']-1.350)<1e-12
 assert abs(get('C_HELDOUT','ADAPTIVE_M4_BLOCKER_AWARE',3)['cost']-.780)<1e-12
 # Existing unit-level blocker occurrences.
 blockers=[]
 for co in ('C_DEVELOPMENT','C_HELDOUT'):
  for b in range(0,8 if co=='C_DEVELOPMENT' else 10):
   z=[r for r in au if r['cohort']==co and int(r['budget'])==b]
   blockers.append({'cohort':co,'budget':b,'units':len(z),'blocker_edits_total':sum(int(r['blocker_edits']) for r in z),'units_with_blocker_edit':sum(int(r['blocker_edits'])>0 for r in z)})
 # Audit all declared source/input hashes in the existing manifest without altering it.
 manifest=json.loads((ROOT/'research/budget_adaptive_repair/research_e_integrity_manifest.json').read_text(encoding='utf-8-sig'))
 source_hash_check={p:sha(ROOT/p)==h for p,h in manifest['source_sha256'].items()}
 aggregate_hash_check={p:sha(SRC/p)==h for p,h in manifest['public_aggregate_sha256'].items()}
 figures_hash_check={p:sha(ROOT/'research/budget_adaptive_repair/figures'/p)==h for p,h in manifest['public_figure_sha256'].items()}
 assert all(source_hash_check.values()) and all(aggregate_hash_check.values()) and all(figures_hash_check.values())
 summary={'status':'FINAL_AUDIT_PARTIAL_D_ARTIFACTS_UNAVAILABLE','research_e_gate':'RESEARCH_E_CORE_COMPLETED_WITH_LIMITATIONS','original_c_units':{'development':64,'heldout':200},'extended_unit_rows':len(unit),'adaptive_unit_rows':len(au),'reference_learner':refsummary,'target_delta0_m4_b2':sens_rows,'heldout_b3_adaptive_vs_m4':held,'constraint_saturation_nonzero':constraint,'blocker_edits_by_budget':blockers,'pareto':{'candidate_count_per_cohort':{'C_DEVELOPMENT':144,'C_HELDOUT':180},'bootstrap_replicates':BOOT,'bootstrap_seed':BOOT_SEED,'note':'joint paired unit resampling; frequency of empirical non-dominated status; post-hoc descriptive, not a superiority probability'},'lambda_lower_envelope_winners':lambda_winners,'source_sha256_checks':source_hash_check,'public_aggregate_sha256_checks':aggregate_hash_check,'public_figure_sha256_checks':figures_hash_check,'unit_level_artifact_sha256':{n:sha(SRC/n) for n in ['c_extended_budget_results.csv','adaptive_m4_unit_results.csv','reference_graph_learner_diagnostic.csv','target_sensitivity_unit_results.csv']},'input_sha256_actual':{ 'c_development_cohort':sha(Path(r'C:/DAT_RESEARCH/research-c/development/development-20261123-seed-2026112301-v1/research_c_cohort.sqlite')), 'c_development_proposal':sha(Path(r'C:/DAT_RESEARCH/research-c/development/development-20261123-seed-2026112301-v1/research_c_proposal_stage.sqlite')), 'c_heldout_cohort':sha(Path(r'C:/DAT_RESEARCH/research-c/heldout/independent-evaluation-20261123-seed-2026112303-v1/research_c_cohort.sqlite')), 'c_heldout_proposal':sha(Path(r'C:/DAT_RESEARCH/research-c/heldout/independent-evaluation-20261123-seed-2026112303-v1/research_c_proposal_stage.sqlite')), 'd_local_audit':sha(Path(r'C:/DAT_RESEARCH/research-d/final-reaudit-20261126.json'))},'input_sha256_match':{'c_development_cohort':manifest['input_sha256']['c_development_cohort']==sha(Path(r'C:/DAT_RESEARCH/research-c/development/development-20261123-seed-2026112301-v1/research_c_cohort.sqlite')),'c_development_proposal':manifest['input_sha256']['c_development_proposal']==sha(Path(r'C:/DAT_RESEARCH/research-c/development/development-20261123-seed-2026112301-v1/research_c_proposal_stage.sqlite')),'c_heldout_cohort':manifest['input_sha256']['c_heldout_cohort']==sha(Path(r'C:/DAT_RESEARCH/research-c/heldout/independent-evaluation-20261123-seed-2026112303-v1/research_c_cohort.sqlite')),'c_heldout_proposal':manifest['input_sha256']['c_heldout_proposal']==sha(Path(r'C:/DAT_RESEARCH/research-c/heldout/independent-evaluation-20261123-seed-2026112303-v1/research_c_proposal_stage.sqlite')),'d_local_audit':manifest['input_sha256']['d_local_audit']==sha(Path(r'C:/DAT_RESEARCH/research-d/final-reaudit-20261126.json'))},'d_artifact_search':{'current_designated_external_root':'C:/DAT_RESEARCH/research-d','found':'final-reaudit-20261126.json only at the root; no raw response vectors/recommendations/training frame in designated directory','prior_audit_record':'27 checks passed, but this closeout could only re-read the stored 31,584-byte audit summary'},'rows_generated_in_this_audit':0,'new_scm_or_g0_or_response_samples':0}
 write_csv(OUT/'expanded_pareto_frontiers.csv',all_front)
 write_csv(OUT/'expanded_lambda_lower_envelope.csv',lambda_rows)
 write_csv(OUT/'expanded_lambda_breakpoints.csv',lambda_break_rows or [{'cohort':'none','lambda_value':'none','tied_optimal_candidates':'none'}])
 write_csv(OUT/'expanded_pareto_bootstrap_stability.csv',bootstrap_rows)
 write_csv(OUT/'reference_learner_summary.csv',refsummary)
 write_csv(OUT/'corrected_saturation_rates.csv',constraint)
 write_csv(OUT/'adaptive_blocker_counts.csv',blockers)
 (OUT/'final_audit_summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True),encoding='utf-8')
 print(json.dumps(summary,indent=2,sort_keys=True))
if __name__=='__main__':main()

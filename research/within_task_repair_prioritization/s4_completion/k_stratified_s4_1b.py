"""Aggregate saved B1 results by structural opportunity K; no fits/evaluation."""
import csv,hashlib,json,os
from pathlib import Path
HERE=Path(__file__).resolve().parent
CONTRACT=HERE/'s4_1b_retrospective'/'k_stratified_contract.json'
C=json.loads(CONTRACT.read_text(encoding='utf-8-sig'))
PILOT=Path(os.environ['S4_PILOT_INPUT']); PRIVATE=Path(os.environ['S4_RETROSPECTIVE_PRIVATE_OUT'])
OUT=HERE/'s4_1b_retrospective'/'k_stratified_outputs'
EXPECTED=C['inputs']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(path,expected):
 if sha(path)!=expected:raise ValueError(f'hash mismatch: {path.name}')
 return json.loads(path.read_text(encoding='utf-8-sig'))
def csvrows(path,expected):
 if sha(path)!=expected:raise ValueError(f'hash mismatch: {path.name}')
 with path.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def main():
 policies=read(PILOT/'policy_results_private.json',EXPECTED['policy_results_private_sha256'])
 b1=csvrows(PRIVATE/'b1_all_63_unit_recommendations.csv',EXPECTED['b1_recommendations_sha256'])
 ks=csvrows(PRIVATE/'opportunity_budget_unit_diagnostics.csv',EXPECTED['k_diagnostics_sha256'])
 kmap={(r['cohort'],r['scm_id']):int(r['K_initial']) for r in ks}
 m4={(r['cohort'],r['scm_id']):r for r in policies if r['policy']=='M4' and int(r['budget'])==1}
 groups={}
 for r in b1:groups.setdefault((r['cohort'],kmap[(r['cohort'],r['scm_id'])],r['policy']),[]).append(r)
 out=[]
 for (cohort,k,policy),rows in sorted(groups.items()):
  ds=[];sameg=[];samea=[]
  for r in rows:
   m=m4[(cohort,r['scm_id'])]; ds.append(float(r['regret'])-float(m['regret']))
   sameg.append(r['graph_hash']==m['graph_hash']);samea.append(float(r['selected_k'])==float(m['selected_k']))
  n=len(ds);out.append({'cohort':cohort,'K_initial':k,'policy':policy,'n_scm':n,'mean_T_minus_M4':sum(ds)/n,'median_T_minus_M4':sorted(ds)[n//2] if n%2 else (sorted(ds)[n//2-1]+sorted(ds)[n//2])/2,
    'T_better':sum(d < -1e-12 for d in ds),'T_worse':sum(d > 1e-12 for d in ds),'tie':sum(abs(d)<=1e-12 for d in ds),'same_graph_fraction':sum(sameg)/n,'same_action_fraction':sum(samea)/n})
 OUT.mkdir(exist_ok=False)
 with (OUT/'b1_policy_differences_by_initial_K.csv').open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=list(out[0]));w.writeheader();w.writerows(out)
 summary={'analysis_id':C['analysis_id'],'classification':C['classification'],'rows':len(out),'generated_counts':C['method']['new_samples'],'input_sha256':{'policy_results_private.json':sha(PILOT/'policy_results_private.json'),'b1_all_63_unit_recommendations.csv':sha(PRIVATE/'b1_all_63_unit_recommendations.csv'),'opportunity_budget_unit_diagnostics.csv':sha(PRIVATE/'opportunity_budget_unit_diagnostics.csv')}}
 (OUT/'summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n',encoding='utf-8')
if __name__=='__main__':main()

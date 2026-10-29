"""Summarize isolated traces and local benchmark; no causal or equivalence claim."""
import sys,json,pathlib,hashlib
import numpy as np,pandas as pd
p=pathlib.Path(sys.argv[1]);out=pathlib.Path('research_runs/tep_operating_condition');base=pd.read_csv('data/local/datasetTE.csv',index_col=0);run=json.loads((p/'results.json').read_text());allframes={};rows=[]
for cond in ('A','B'):
 z=np.load(p/f'{cond}_2h.npz');t=z['time'];measure=z['measurements'];a=z['actions'];df=pd.DataFrame({col:(measure[:,int(col[1:])-1] if int(col[1:])<=22 else a[:,int(col[1:])-23]) for col in base.columns});allframes[cond]=(t,df,z)
for col in base.columns:
 x=base[col];row={'variable':col,'benchmark_mean':x.mean(),'benchmark_sd':x.std(),'benchmark_median':x.median(),'benchmark_q05':x.quantile(.05),'benchmark_q95':x.quantile(.95),'benchmark_autocorrelation_lag1':x.autocorr()}
 for c,(t,df,z) in allframes.items():
  x=df[col];delta=x.mean()-row['benchmark_mean'];den=row['benchmark_sd'];mean=row['benchmark_mean'];row.update({f'{c}_observed_h':t[-1],f'{c}_mean':x.mean(),f'{c}_sd':x.std(),f'{c}_median':x.median(),f'{c}_q05':x.quantile(.05),f'{c}_q95':x.quantile(.95),f'{c}_first':x.iloc[0],f'{c}_last':x.iloc[-1],f'{c}_lag1_autocorrelation':x.autocorr(),f'{c}_relative_mean_difference':delta/abs(mean) if abs(mean)>1e-12 else np.nan,f'{c}_standardized_mean_difference':delta/den if den>1e-12 else np.nan})
  for window in (.5,1.,2.):
   if t[-1]+1e-8>=window:
    mask=t>t[-1]-window;row[f'{c}_last_{window}h_mean']=x[mask].mean();row[f'{c}_last_{window}h_slope_per_h']=np.polyfit(t[mask],x[mask],1)[0]
 rows.append(row)
pd.DataFrame(rows).to_csv(out/'COMPARISON_31.csv',index=False)
extra={}
for c,(t,df,z) in allframes.items():
 extra[c]={'duration_h':float(t[-1]),'correlation':json.loads(df.corr().to_json()),'pressure_purge_command_final':float(z['actions'][-1,5]),'pressure_purge_ratio_final':float(z['r5'][-1]),'stripper_level_final':float(z['measurements'][-1,14])}
info={'runs':run,'derived':extra,'raw_zip_sha256':hashlib.sha256((p/'artifact.zip').read_bytes()).hexdigest(),'expected_unrun':['B full 2h stopped','A/B 6h','A/B 24h','C/D','integrator convergence','intervention'],'evidence':'measurements downsampled every 6 steps; not equivalent clocks or preprocessing; reference correlations use 1499 rows','prior_PR28_B_same_crossing':{'hours':1.519,'stripper_level_percent':100.62355412209789,'reported_shutdown':False,'interpretation':'prior probe lacked per-step schema constraint gate'}}
(out/'RUN_RESULTS.json').write_text(json.dumps(info,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf8')
print('zip SHA256',info['raw_zip_sha256']);print('final purge',[(c,x['pressure_purge_command_final']) for c,x in extra.items()]);print('standardized extreme',sorted([(r['variable'],r['A_standardized_mean_difference']) for r in rows if np.isfinite(r['A_standardized_mean_difference'])], key=lambda x:abs(x[1]),reverse=True)[:5])

import importlib.util, sys, json, hashlib, pathlib, os
import numpy as np, pandas as pd
s=importlib.util.spec_from_file_location('standalone_schema',sys.argv[1]); mod=importlib.util.module_from_spec(s);sys.modules[s.name]=mod;s.loader.exec_module(mod)
root=pathlib.Path('research_runs/tep_studio_execution'); raw=pathlib.Path(sys.argv[2])
data=pd.read_csv('data/local/datasetTE.csv',index_col=0)
mapping=[]; comparison=[]; series={}
for cond in ('A','B'):
 z=np.load(raw/f'{cond}_2.0.npz'); arr=np.concatenate((z['measurements'],z['actions']),axis=1); columns={}
 for name in data.columns:
  i=int(name[1:]); role='measurements' if i<=22 else 'manipulated_variables'; idx=i-1 if i<=22 else i-23; v=mod.TEP_SCHEMA._variables_for_role(role)[idx]
  vals=arr[:,idx if i<=22 else 41+idx]; columns[name]=vals
  if cond=='A':mapping.append({'dataset':name,'candidate_studio_name':v.name,'candidate_legacy_symbol':v.legacy_symbol,'role':role,'unit_studio':v.unit,'mapping_status':'PROVISIONAL: benchmark export and time not verified','source':'TEP Studio schema; PR27 tentative mapping'})
 df=pd.DataFrame(columns); series[cond]=df
for name in data.columns:
 row={'variable':name}
 for label,vals in [('benchmark',data[name]),('A_raw',series['A'][name]),('B_raw',series['B'][name])]:
  x=pd.Series(vals); row.update({label+'_mean':x.mean(),label+'_sd':x.std(),label+'_median':x.median(),label+'_q05':x.quantile(.05),label+'_q95':x.quantile(.95),label+'_first':x.iloc[0],label+'_last':x.iloc[-1],label+'_lag1_autocorrelation':x.autocorr()})
 for cond in ('A','B'):
  source=series[cond][name].to_numpy(); indices=np.rint((np.arange(10,7201,10)/3600)/.0005).astype(int)-1; indices=np.clip(indices,0,len(source)-1); filtered=pd.Series(source[indices]).rolling(18,min_periods=18).median().dropna(); row[cond+'_approx_10s_3min_median_mean']=filtered.mean(); row[cond+'_approx_10s_3min_median_sd']=filtered.std()
  x=series[cond][name]; sd=data[name].std();row[cond+'_difference_mean']=x.mean()-data[name].mean();row[cond+'_difference_over_benchmark_sd']=(x.mean()-data[name].mean())/sd if sd>1e-12 else np.nan
 comparison.append(row)
pd.DataFrame(mapping).to_csv(root/'VARIABLE_MAPPING.csv',index=False);pd.DataFrame(comparison).to_csv(root/'COMPARISON_31.csv',index=False)
summary={'data_sha256':hashlib.sha256(pathlib.Path('data/local/datasetTE.csv').read_bytes()).hexdigest(),'raw_artifact_sha256':hashlib.sha256((raw/'artifact.zip').read_bytes()).hexdigest(),'source':'GitHub Actions run 40873474299 artifact','rows':json.loads((raw/'results.json').read_text()),'biggest_absolute_mean_gap':[{'condition':c, 'values':sorted([{'variable':x['variable'],'difference':x[c+'_difference_mean']} for x in comparison],key=lambda x:abs(x['difference']),reverse=True)[:5]} for c in ('A','B')], 'correlation_matrices':{k:json.loads(v.corr().to_json()) for k,v in [('benchmark',data),('A_raw',series['A']),('B_raw',series['B'])]},'warning':'Raw data at 1.8 s and processed benchmark ~75h are not equivalence tests; missing uncertain preprocessing and units; correlations may be undefined for constants.'}
(root/'RUN_SUMMARY.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf8')
print(json.dumps(summary['biggest_absolute_mean_gap'],indent=2));print('zip sha',summary['raw_artifact_sha256'])

import numpy as np,pandas as pd,json,hashlib,pathlib
out=pathlib.Path('research_runs/tep_official_validation');raw=pathlib.Path('data/local/tep_official_validation/run_v1');b=pd.read_csv('data/local/datasetTE.csv',index_col=0);runs={};df=None
for name in ('guard_injection','A0','A1','A2','A3'):
 a=np.loadtxt(raw/(name+'.csv'),delimiter=','); _,idx=np.unique(a[:,0],return_index=True);a=a[idx];t=np.arange(0,a[-1,0]+1e-9,10/3600);s=np.array([np.interp(t,a[:,0],a[:,i]) for i in range(1,104)]).T
 runs[name]={'time_h':float(a[-1,0]),'logged_rows':len(a),'stop_reason':int(a[-1,-1]),'sha256':hashlib.sha256((raw/(name+'.csv')).read_bytes()).hexdigest(),'mean_X7_X8_X9':s[:,[6,7,8]].mean(0).tolist(),'final_X7_X8_X9':a[-1,[7,8,9]].tolist(),'last_hour_mean':s[t>=max(0,t[-1]-1)][:,[6,7,8]].mean(0).tolist(),'MV5_MV9_MV12':a[-1,[46,50,53]].tolist()}
 if name=='A3':df=pd.DataFrame({c:s[:,int(c[1:])-1 if int(c[1:])<=22 else 41+int(c[1:])-23] for c in b})
rows=[]
for c in b:
 row={'variable':c}
 for label,x in [('benchmark',b[c]),('official_6h_10s_interpolated',df[c])]:
  row.update({label+'_mean':x.mean(),label+'_sd':x.std(),label+'_median':x.median(),label+'_q05':x.quantile(.05),label+'_q95':x.quantile(.95),label+'_lag1':x.autocorr()})
 row['standardized_mean_gap']=(df[c].mean()-b[c].mean())/b[c].std();rows.append(row)
pd.DataFrame(rows).to_csv(out/'NORMAL_COMPARISON_31.csv',index=False);df.corr().to_csv(out/'OFFICIAL_CORRELATION.csv');b.corr().to_csv(out/'BENCHMARK_CORRELATION.csv')
(out/'NORMAL_RUN_RESULTS.json').write_text(json.dumps({'runs':runs,'sampling':'linear interpolation of major-output logs to 10s; not original filtering or measurement replication','phase_B':'NOT_RUN'},indent=2),encoding='utf8')
(out/'SAFETY_MONITOR_VALIDATION.json').write_text(json.dumps({'injected_stop':'PASS at 0.0005h reason99 vs requested0.001h','normal_runs':'A0,A1,A2,A3 complete reason0','scope':'mdlOutputs sensors, cached commands, all-state finite, native shutdown. physical-state limits NOT verified beyond finite; minor derivative evaluation not monitored','fault_type_coverage':'only injected stop branch tested; each numerical rejection branch not separately tested'},indent=2),encoding='utf8')
(out/'ENVIRONMENT_MATCH_DECISION.json').write_text(json.dumps({'phase_A':'CLOSE_CANDIDATE_BUT_UNVERIFIED','final':'OFFICIAL_SIMULATOR_RUN_VERIFIED_ENVIRONMENT_UNVERIFIED','phase_B':'NOT_RUN','reasons':['model default now has documented 0/0/100 commands and near target means','original preprocessing, noise flags, seed policy and exact 1499 provenance unverified','6h single trajectory not 75h comparable independent stationary sample; no predeclared numeric equivalence margins','31-variable mapping is provisional'],'next':'recover original Manca normal data timestamps and generation/filter metadata for independently specified comparable validation'},indent=2),encoding='utf8')
print(json.dumps(runs['A3'],indent=2));print(pd.DataFrame(rows).sort_values('standardized_mean_gap').iloc[[0,-1]][['variable','standardized_mean_gap']].to_string(index=False))

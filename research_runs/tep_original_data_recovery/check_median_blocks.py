import numpy as np,pandas as pd,json,pathlib
b=pd.read_csv('data/local/datasetTE.csv',index_col=0).to_numpy();records=[]
for r in (1,2,3):
 z=np.load(f'data/local/tep_original_data_recovery/normal_{r}.npz');raw=np.column_stack([z['SIMOUT'][:,:22],z['XMV'][:,:11]])[:,[i for i in range(33) if i not in (26,30)]]
 for start in (0,1):
  m=np.median(raw[start:start+27000].reshape(1500,18,31),axis=1)
  for skip in (0,1):
   d=m[skip:skip+1499]-b;record={'run':r,'block_start_row':start,'skip_first_block':skip,'max_abs':float(np.abs(d).max()),'mae':float(np.abs(d).mean())};records.append(record)
print(sorted(records,key=lambda x:x['mae'])[:4]);pathlib.Path('research_runs/tep_original_data_recovery/MEDIAN_EXPLORATION.json').write_text(json.dumps({'status':'EXPLORATORY_NOT_CONFIRMED_ORIGINAL_CODE','rules':'18 observations per nonoverlapping3min block; start0/1 and drop0/1 block; each of three originals. No parameter tuning beyond this named finite check','results':records},indent=2),encoding='utf8')

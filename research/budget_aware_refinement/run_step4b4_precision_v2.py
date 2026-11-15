"""Normal paired-mean precision/power planning; no study outcomes."""
from __future__ import annotations
import json,math,platform,sys
from hashlib import sha256
from pathlib import Path
from scipy.stats import nct,t
HERE=Path(__file__).parent;OUT=HERE/'step4b4_precision_v2.json'
NS=(34,64,100,200);SDS=(.2,.3,.5,.7,1.);DELTA=.1;ALPHA=.05
SET={'protocol':'STEP4B4_NORMAL_PAIRED_DIFFERENCE_PRECISION_V2','n_grid':NS,'sd_scenarios':SDS,'delta':DELTA,'alpha':ALPHA,'method':'exact noncentral t power under iid Normal SCM-level differences; nominal t CI half width using known scenario SD'}
SHA=sha256(json.dumps(SET,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def run():
 rows=[]
 for n in NS:
  crit=float(t.ppf(1-ALPHA/2,n-1))
  for sd in SDS:
   nc=DELTA*math.sqrt(n)/sd;power=float(nct.sf(crit,n-1,nc)+nct.cdf(-crit,n-1,nc));half=crit*sd/math.sqrt(n)
   rows.append({'n':n,'sd':sd,'mean_shift':DELTA,'two_sided_power_normal_assumption':power,'nominal_95_ci_half_width':half,'nominal_95_ci_full_width':2*half,'would_ci_halfwidth_be_at_most_0_10':half<=.1})
 return {'settings':SET,'settings_sha256':SHA,'software':{'python':sys.version.split()[0],'platform':platform.platform()},'results':rows,'limits':['Power uses the normal paired-difference model; it does not apply to the skewed zero-heavy distribution that invalidated small-sample t calibration.','CI width is nominal with known scenario SD; realized width varies.','This is design arithmetic, not evidence of actual SCM variance.']}
def main():
 r=run();OUT.write_text(json.dumps(r,sort_keys=True,indent=2)+'\n',encoding='utf-8');print(json.dumps({'settings_sha256':SHA,'n200':[x for x in r['results'] if x['n']==200]},indent=2))
if __name__=='__main__':main()

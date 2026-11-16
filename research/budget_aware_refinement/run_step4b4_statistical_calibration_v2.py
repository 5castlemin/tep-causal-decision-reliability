"""Corrected, outcome-free paired-mean inference calibration (v2)."""
from __future__ import annotations
from hashlib import sha256
import json
from pathlib import Path
import numpy as np
from .step4b4_design import student_t_critical
HERE=Path(__file__).parent; OUTPUT=HERE/'step4b4_statistical_calibration_v2.json'
SEEDS=(4042026,918273645); N_GRID=(34,64,100,200); REPS=20000; ALPHA=.05; SHIFT=.10
BOOT_N=200; BOOT_OUTER=1000; BOOT_INNER=499
SCENARIOS=('normal','zero_heavy_symmetric','zero_heavy_skewed','rare_symmetric_extremes','cancellation','rare_large_loss','near_degenerate','degenerate_zero')
SETTINGS={'protocol':'STEP4B4_ABSTRACT_PAIRED_MEAN_CALIBRATION_V2','seeds':SEEDS,'n_grid':N_GRID,'reps_per_scenario_n_seed':REPS,'alpha_two_sided':ALPHA,'mean_shift':SHIFT,'bootstrap_n':BOOT_N,'bootstrap_outer':BOOT_OUTER,'bootstrap_inner':BOOT_INNER,'scenarios':SCENARIOS,'confidence_interval_coverage_truth_specific':True,'no_scm_or_regret_draws':True}
SETTINGS_SHA=sha256(json.dumps(SETTINGS,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def _draw(name,rng,shape):
 u=rng.random(shape);z=np.zeros(shape,dtype=float)
 if name=='normal':return rng.normal(size=shape)
 if name=='zero_heavy_symmetric':z[u<.10]=-np.sqrt(5);z[(u>=.10)&(u<.20)]=np.sqrt(5);return z
 if name=='zero_heavy_skewed':
  pos=np.sqrt(1/.9);z[u<.01]=-9*pos;z[(u>=.90)&(u<.99)]=pos;return z
 if name=='rare_symmetric_extremes':z[u<.005]=-10;z[(u>=.005)&(u<.010)]=10;return z
 if name=='cancellation':z[u<.45]=-np.sqrt(1/.9);z[(u>=.45)&(u<.90)]=np.sqrt(1/.9);return z
 if name=='rare_large_loss':z[u<.01]=10;z[(u>=.01)&(u<.015)]=-20;return z
 if name=='near_degenerate':return (u-.5)*2e-10
 if name=='degenerate_zero':return z
 raise ValueError(name)

THEORY={'normal':{'mean':0.,'variance':1.,'skewness':0.},'zero_heavy_symmetric':{'mean':0.,'variance':1.,'skewness':0.},'zero_heavy_skewed':{'mean':0.,'variance':1.,'skewness':-8.4327404},'rare_symmetric_extremes':{'mean':0.,'variance':1.,'skewness':0.},'cancellation':{'mean':0.,'variance':1.,'skewness':0.},'rare_large_loss':{'mean':0.,'variance':3.,'skewness':-5.7735027},'near_degenerate':{'mean':0.,'variance':(1e-10)**2/3,'skewness':0.},'degenerate_zero':{'mean':0.,'variance':0.,'skewness':None}}
RANGES={'normal':None,'zero_heavy_symmetric':[-float(np.sqrt(5)),float(np.sqrt(5))],'zero_heavy_skewed':[-9*float(np.sqrt(1/.9)),float(np.sqrt(1/.9))],'rare_symmetric_extremes':[-10.,10.],'cancellation':[-float(np.sqrt(1/.9)),float(np.sqrt(1/.9))],'rare_large_loss':[-20.,10.],'near_degenerate':[-1e-10,1e-10],'degenerate_zero':[0.,0.]}

def _summarize(samples,true_mean,critical):
 n=samples.shape[1];means=samples.mean(axis=1);sd=samples.std(axis=1,ddof=1);constant=np.all(samples==samples[:,:1],axis=1);sd[constant]=0.;means[constant]=samples[constant,0];zero=sd==0;se=sd/np.sqrt(n);low=means-critical*se;high=means+critical*se
 zero=se==0;stat=np.empty_like(means);stat[~zero]=means[~zero]/se[~zero];stat[zero]=0.;nz=zero&(means!=0);stat[nz]=np.sign(means[nz])*np.inf
 reject=np.abs(stat)>critical;cover=(low<=true_mean)&(true_mean<=high);width=high-low
 bad=~(np.isfinite(means)&np.isfinite(sd)&np.isfinite(se)&np.isfinite(low)&np.isfinite(high))
 return {'type1_or_power_rejects_zero':float(reject.mean()),'true_mean_ci_coverage':float(cover.mean()),'mcse_rejection':float(np.sqrt(reject.mean()*(1-reject.mean())/len(reject))),'mcse_coverage':float(np.sqrt(cover.mean()*(1-cover.mean())/len(cover))),'mean_ci_width':float(width.mean()),'median_ci_width':float(np.median(width)),'zero_sample_sd_rate':float(zero.mean()),'near_zero_sd_rate_1e-12':float(((sd>0)&(sd<=1e-12)).mean()),'numeric_failure_rate':float(bad.mean()),'sample_mean_average':float(means.mean()),'sample_sd_min':float(sd.min()),'sample_sd_median':float(np.median(sd))}

def _studentized_bootstrap_once(x,rng):
 n=len(x);mean=float(x.mean());sd=float(x.std(ddof=1));se=sd/np.sqrt(n);idx=rng.integers(0,n,size=(BOOT_INNER,n));b=x[idx];bm=b.mean(axis=1);bs=b.std(axis=1,ddof=1);bse=bs/np.sqrt(n)
 tstar=np.empty(BOOT_INNER);ok=bse>0;tstar[ok]=(bm[ok]-mean)/bse[ok]
 same=(~ok)&(bm==mean);tstar[same]=0.;tstar[(~ok)&(bm>mean)]=np.inf;tstar[(~ok)&(bm<mean)]=-np.inf
 qlo,qhi=np.quantile(tstar,[ALPHA/2,1-ALPHA/2],method='inverted_cdf');return mean-qhi*se,mean-qlo*se,int((~ok).sum())
def _bootstrap_check(name,seed):
 rng=np.random.default_rng(seed);n=BOOT_N;crit=student_t_critical(ALPHA,n-1);count={'t':0,'percentile':0,'studentized':0};deg=0;unstable=0;width={'t':[],'percentile':[],'studentized':[]};unbounded=0
 for _ in range(BOOT_OUTER):
  x=_draw(name,rng,(n,));m=float(x.mean());sd=float(x.std(ddof=1));se=sd/np.sqrt(n);tlo,thi=m-crit*se,m+crit*se;count['t']+=tlo<=0<=thi;width['t'].append(thi-tlo)
  idx=rng.integers(0,n,size=(BOOT_INNER,n));means=x[idx].mean(axis=1);plo,phi=np.quantile(means,[ALPHA/2,1-ALPHA/2]);count['percentile']+=plo<=0<=phi;width['percentile'].append(phi-plo);deg+=(plo==phi)
  slo,shi,fail=_studentized_bootstrap_once(x,rng);unstable+=fail>0;count['studentized']+=slo<=0<=shi;w=shi-slo
  if np.isfinite(w):width['studentized'].append(w)
  else:unbounded+=1
 return {'n':n,'outer':BOOT_OUTER,'inner':BOOT_INNER,'coverage':{k:v/BOOT_OUTER for k,v in count.items()},'mean_width':{k:(float(np.mean(v)) if v else None) for k,v in width.items()},'studentized_unbounded_interval_rate':unbounded/BOOT_OUTER,'percentile_degenerate_rate':deg/BOOT_OUTER,'studentized_resamples_with_zero_se_rate':unstable/BOOT_OUTER,'mcse_worst_case':float(np.sqrt(.25/BOOT_OUTER))}

def run():
 all_results={}; replicate_checks=[]
 for seed in SEEDS:
  rng=np.random.default_rng(seed);by_s={}
  for name in SCENARIOS:
   by_n={}
   for n in N_GRID:
    crit=student_t_critical(ALPHA,n-1);null=_draw(name,rng,(REPS,n));alt=null+SHIFT
    h0=_summarize(null,THEORY[name]['mean'],crit);ha=_summarize(alt,THEORY[name]['mean']+SHIFT,crit)
    range_=RANGES[name];var=THEORY[name]['variance'];cheb=(float(np.sqrt(var/(ALPHA*n))) if var else 0.0);hoeff=(None if range_ is None else float((range_[1]-range_[0])*np.sqrt(np.log(2/ALPHA)/(2*n))))
    bounded={'chebyshev_known_variance':{'half_width':cheb,'null_coverage_mc':float(np.mean(np.abs(null.mean(axis=1)-THEORY[name]['mean'])<=cheb)),'validity_requires_known_true_variance':True},'hoeffding_known_range':{'half_width':hoeff,'null_coverage_mc':(None if hoeff is None else float(np.mean(np.abs(null.mean(axis=1)-THEORY[name]['mean'])<=hoeff))),'support_range':range_,'validity_requires_prejustified_finite_range':True}}
    by_n[str(n)]={'critical_value':crit,'null':h0,'alternative':ha,'conservative_bounds':bounded}
   by_s[name]=by_n
  all_results[str(seed)]=by_s
  replicate_checks.append({'seed':seed,'skew_null_n200':by_s['zero_heavy_skewed']['200']['null'],'skew_power_n200':by_s['zero_heavy_skewed']['200']['alternative']['type1_or_power_rejects_zero']})
 boot={name:_bootstrap_check(name,SEEDS[0]+i+1000) for i,name in enumerate(('normal','zero_heavy_symmetric','zero_heavy_skewed','rare_large_loss','near_degenerate'))}
 constants={}
 for c in (0.,SHIFT,1e-14):
  sample=np.full(200,c);row=_summarize(sample.reshape(1,-1),0.,student_t_critical(ALPHA,199));alt=_summarize((sample+SHIFT).reshape(1,-1),SHIFT,student_t_critical(ALPHA,199));constants[str(c)]={'constant_sample':_summarize(sample.reshape(1,-1),c,student_t_critical(ALPHA,199)),'shifted_constant_sample':_summarize((sample+SHIFT).reshape(1,-1),c+SHIFT,student_t_critical(ALPHA,199))}
 return {'settings':SETTINGS,'settings_sha256':SETTINGS_SHA,'theoretical_moments':THEORY,'results_by_seed':all_results,'independent_seed_skew_check':replicate_checks,'bootstrap_n200':boot,'constant_sample_cases':constants,'interpretation':['Chebyshev/Hoeffding intervals are diagnostics only; their validity in this simulation uses known variance/support, neither justified for actual regret yet.','CI coverage is evaluated against the corresponding true mean: 0 under H0, 0.10 under shifted alternative.','Power is rejection of mean zero, separately recorded.','For exactly constant samples, t inference is marked degenerate with point CI; rejection is deterministic and not treated as calibrated inferential evidence.','Near-degenerate finite-variance behavior is numerically fragile and not treated as proof of calibrated inference.','No method is selected as universally valid.']}
def main():
 r=run();OUTPUT.write_text(json.dumps(r,sort_keys=True,indent=2,allow_nan=False)+'\n',encoding='utf-8');print(json.dumps({'output':OUTPUT.name,'settings_sha256':SETTINGS_SHA,'n200_skew_type1':{s:r['results_by_seed'][str(s)]['zero_heavy_skewed']['200']['null']['type1_or_power_rejects_zero'] for s in SEEDS},'n200_skew_coverage':{s:r['results_by_seed'][str(s)]['zero_heavy_skewed']['200']['null']['true_mean_ci_coverage'] for s in SEEDS}},indent=2))
if __name__=='__main__':main()

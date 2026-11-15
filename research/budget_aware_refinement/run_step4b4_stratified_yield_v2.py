"""Stratified yield review from preserved topology-only v1 attempts."""
from __future__ import annotations
from hashlib import sha256
import gzip,json
from pathlib import Path
from .step4b4_design import (clopper_pearson,minimum_attempt_cap,
                            stratified_yield_interval,stratified_yield_variance)
HERE=Path(__file__).parent;SOURCE=HERE/'step4b4_q_yield_v1.json.gz';OUTPUT=HERE/'step4b4_stratified_yield_v2.json'
ALPHA=.05;CAP_ALPHA=.025;TARGET_ATTAIN=.975
SETTINGS={'protocol':'STEP4B4_STRATIFIED_Q_YIELD_REVIEW_V2','source':'step4b4_q_yield_v1.json.gz','stratum_weights':'1/20 each; future stratum independently drawn uniformly per candidate','point_estimator':'weighted mean of per-stratum acceptance proportions','simultaneous_interval':'Bonferroni-adjusted exact Clopper-Pearson per stratum, weighted endpoints','interval_alpha':ALPHA,'cap_confidence_alpha':CAP_ALPHA,'cap_conditional_attainment':TARGET_ATTAIN,'targets':[64,200]}
SETTINGS_SHA=sha256(json.dumps(SETTINGS,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def run():
 raw=SOURCE.read_bytes();data=json.loads(gzip.decompress(raw));ss=data['strata'];k=[int(x['q_common_accepted']) for x in ss];n=[int(x['candidate_attempts']) for x in ss];w=[1/len(ss)]*len(ss)
 point=sum(wi*ki/ni for wi,ki,ni in zip(w,k,n));var=stratified_yield_variance(k,n,w);lo,hi=stratified_yield_interval(k,n,alpha=ALPHA,weights=w);caplo,_=stratified_yield_interval(k,n,alpha=CAP_ALPHA,weights=w)
 table=[]
 for row,ki,ni in zip(ss,k,n):
  a,b=clopper_pearson(ki,ni,ALPHA);table.append({'template':row['template'],'node_count':row['node_count'],'successes':ki,'attempts':ni,'rate':ki/ni,'individual_cp95':[a,b]})
 caps={}
 for target in SETTINGS['targets']:
  cap,prob=minimum_attempt_cap(target,caplo,TARGET_ATTAIN);caps[str(target)]={'candidate_cap':cap,'yield_lower_assumption':caplo,'conditional_probability_at_least_target':prob}
 return {'settings':SETTINGS,'settings_sha256':SETTINGS_SHA,'source_sha256':sha256(raw).hexdigest(),'strata_count':len(ss),'total_attempts':sum(n),'total_successes':sum(k),'unstratified_pooled_rate_descriptive':sum(k)/sum(n),'weighted_stratified_point_estimate':point,'plug_in_design_standard_error':var**.5,'weighted_simultaneous_cp95_conservative_interval':[lo,hi],'yield_lower_for_two_layer_cap':caplo,'two_layer_caps':caps,'strata':table,'zero_success_strata':sum(x==0 for x in k),'all_success_strata':sum(x==ni for x,ni in zip(k,n)),'future_sampling_contract':'For each candidate attempt, select stratum uniformly using the predeclared RNG stream, then accept by Q eligibility; under fixed stratum yields the unconditional acceptance indicators are iid Bernoulli with p equal to the 1/20 weighted yield. This differs from the fixed-quota audit design.','cap_interpretation':'Bonferroni 97.5% simultaneous lower confidence bound plus 97.5% conditional binomial attainment; union-bound planning confidence is at least approximately 95% under the independent future candidate model. Not a resource-approved operational cap.','no_outcome_selection':True}
def main():
 r=run();OUTPUT.write_text(json.dumps(r,sort_keys=True,indent=2,allow_nan=False)+'\n',encoding='utf-8');print(json.dumps({'output':OUTPUT.name,'settings_sha256':SETTINGS_SHA,'yield':r['weighted_stratified_point_estimate'],'interval':r['weighted_simultaneous_cp95_conservative_interval'],'cap_lower':r['yield_lower_for_two_layer_cap'],'caps':r['two_layer_caps']}))
if __name__=='__main__':main()

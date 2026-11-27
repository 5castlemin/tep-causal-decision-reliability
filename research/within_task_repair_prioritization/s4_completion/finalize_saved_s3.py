"""Independent aggregate-only analyzer for completed ignored S3 replay rows."""
import ast,csv,json
from collections import defaultdict
import math
from pathlib import Path
import numpy as np

HERE=Path(__file__).resolve().parent
SRC=HERE/'outputs_v13'
DEST=HERE/'tables'/'completion_v1'
GAMMAS=(0.0,0.2,0.5); METRICS=tuple(f'T{i}' for i in range(1,7)); TOL=1e-12; NBOOT=10000; SEED=2026112703

def read(name):
    with (SRC/name).open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
def write(name,rows):
    if not rows:return
    keys=sorted({k for r in rows for k in r})
    with (DEST/name).open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(rows)
def num(x):return float(x) if x not in ('',None) else np.nan
def holm(pvalues):
    order=np.argsort(pvalues); m=len(pvalues); adj=np.ones(m); running=0.0
    for rank,idx in enumerate(order):
        running=max(running,(m-rank)*pvalues[idx]);adj[idx]=min(1.0,running)
    return adj
def _betacf(a,b,x):
    qab=a+b; qap=a+1.0; qam=a-1.0; c=1.0; d=1.0-qab*x/qap
    if abs(d)<1e-300:d=1e-300
    d=1.0/d; h=d
    for m in range(1,301):
        m2=2*m; aa=m*(b-m)*x/((qam+m2)*(a+m2));d=1.0+aa*d
        if abs(d)<1e-300:d=1e-300
        c=1.0+aa/c
        if abs(c)<1e-300:c=1e-300
        d=1.0/d;h*=d*c;aa=-(a+m)*(qab+m)*x/((a+m2)*(qap+m2));d=1.0+aa*d
        if abs(d)<1e-300:d=1e-300
        c=1.0+aa/c
        if abs(c)<1e-300:c=1e-300
        d=1.0/d;delta=d*c;h*=delta
        if abs(delta-1.0)<3e-14:break
    return h
def _ibeta(a,b,x):
    if x<=0:return 0.0
    if x>=1:return 1.0
    bt=math.exp(math.lgamma(a+b)-math.lgamma(a)-math.lgamma(b)+a*math.log(x)+b*math.log1p(-x))
    return bt*_betacf(a,b,x)/a if x<(a+1)/(a+b+2) else 1-bt*_betacf(b,a,1-x)/b
def paired_t_pvalue(d):
    d=np.asarray(d,dtype=float);n=len(d);sd=float(d.std(ddof=1))
    if sd==0:return 1.0 if abs(float(d.mean()))<1e-15 else 0.0
    t=abs(float(d.mean()))/(sd/math.sqrt(n));x=(n-1)/((n-1)+t*t)
    return float(_ibeta((n-1)/2.0,0.5,x))

def main():
    if DEST.exists() and any(DEST.iterdir()):raise FileExistsError(DEST)
    DEST.mkdir(parents=True,exist_ok=True)
    units=read('unit_results_private.csv'); candidates=read('single_edit_candidates_aggregate.csv'); pairs=read('two_edit_interactions_private.csv')
    ex=[r for r in units if r['gamma'] not in ('','all') and r['base_regret']!='']
    # Fail closed on cohort size and unique unit keys.
    expected={'C_DEVELOPMENT':64,'C_HELDOUT':200}
    for cohort,n in expected.items():
        for g in GAMMAS:
            sub=[r for r in ex if r['cohort']==cohort and float(r['gamma'])==g]
            assert len(sub)==n and len({r['scm'] for r in sub})==n
    # Paired, common-index SCM bootstrap for ex-post benchmarks; same indices reused across gamma and contrasts.
    paired=[]; rng_by_cohort={c:np.random.default_rng(SEED+i) for i,c in enumerate(expected)}
    for c,n in expected.items():
        ids=sorted(r['scm'] for r in ex if r['cohort']==c and float(r['gamma'])==0.0)
        index=rng_by_cohort[c].integers(0,n,size=(NBOOT,n))
        for g in GAMMAS:
            rows=sorted((r for r in ex if r['cohort']==c and float(r['gamma'])==g),key=lambda r:r['scm'])
            assert [r['scm'] for r in rows]==ids
            for label,left,right in [('S0_minus_expost_opt','base_regret','best_two_or_fewer_regret'),('S0_minus_best_single','base_regret','best_single_regret')]:
                d=np.array([num(r[left])-num(r[right]) for r in rows]); b=d[index].mean(axis=1)
                paired.append({'cohort':c,'gamma':g,'contrast':label,'mean_difference':float(d.mean()),'ci95_low':float(np.quantile(b,.025)),'ci95_high':float(np.quantile(b,.975)),'better':int((d>TOL).sum()),'worse':int((d< -TOL).sum()),'tie':int((np.abs(d)<=TOL).sum()),'n_scm':n,'bootstrap_seed':SEED+list(expected).index(c),'replicates':NBOOT,'interval':'pointwise_percentile'})
    write('expost_paired_bootstrap.csv',paired)
    # Aggregate all structure policies by cohort, target objective, set and budget; preserve paired unit denominator.
    pol=[r for r in units if r['gamma']=='all' and r['policy'] not in ('','')]
    polagg=[]
    groups=defaultdict(list)
    for r in pol:
        for g,losscol,actioncol in [(0.0,'regret_g0','action_g0'),(.2,'regret_g0.2','action_g0.2'),(.5,'regret_g0.5','action_g0.5')]:
            key=(r['cohort'],r['policy'],r['metric_set'],int(r['budget']),g)
            groups[key].append((r,num(r[losscol]),num(r['cost']),num(r[actioncol])))
    s0={(r['cohort'],int(r['budget']),g,r['scm']):a for r in pol for g,a_col in [(0.0,'action_g0'),(.2,'action_g0.2'),(.5,'action_g0.5')] for a in [num(r[a_col])] if r['policy']=='S0'}
    for (c,p,metricset,b,g),vals in sorted(groups.items()):
        losses=np.array([x[1] for x in vals]);cost=np.array([x[2] for x in vals]);actions=np.array([x[3] for x in vals]); change=[]
        for r,_,_,a in vals:
            base=s0[(c,b,g,r['scm'])];change.append(bool(a!=base))
        polagg.append({'cohort':c,'policy':p,'metric_set':metricset,'budget':b,'gamma':g,'n_scm':len(vals),'mean_regret':float(losses.mean()),'median_regret':float(np.median(losses)),'sd_regret':float(losses.std(ddof=1)),'p25_regret':float(np.quantile(losses,.25)),'p75_regret':float(np.quantile(losses,.75)),'mean_edit_cost':float(cost.mean()),'mean_unused_budget':float(b-cost.mean()),'action_change_rate_vs_S0':float(np.mean(change)),'unique_final_graphs':len({x[0]['graph_hash'] for x in vals})})
    write('policy_objective_budget_aggregates.csv',polagg)
    # Within-SCM ranking of single-edit T gains against realized regret benefit. Candidates are clustered by SCM.
    candgroups=defaultdict(list)
    for r in candidates:candgroups[(r['cohort'],r['scm'])].append(r)
    ranking=[]
    for metric in METRICS+('M4',)+('+'.join(METRICS),):
        for g in GAMMAS:
            for cohort in expected:
                sg=[]
                for (c,sid),rs in candgroups.items():
                    if c!=cohort or len(rs)<2:continue
                    u=np.array([num(r[f'regret_gain_g{g}']) for r in rs])
                    if metric=='M4':score=np.array([num(r['M4_structural_gain']) for r in rs])
                    elif metric=='T1+T2+T3+T4+T5+T6':score=np.mean([[num(r[f'{m}_gain']) for m in METRICS] for r in rs],axis=1)
                    else:score=np.array([num(r[f'{metric}_gain']) for r in rs])
                    if metric=='M4':eligible=(score>TOL)
                    else:eligible=(score>TOL)
                    if eligible.any(): candidates_idx=np.where(eligible)[0]; order=sorted(candidates_idx,key=lambda i:(-score[i],ast.literal_eval(rs[i]['pair']),rs[i]['operation']))
                    else:
                        m4=np.array([num(r['M4_structural_gain']) for r in rs]); candidates_idx=np.where(m4>TOL)[0]
                        if not len(candidates_idx):
                            sg.append({'utility':0.0,'hit':float(np.max(u)<=TOL),'gap':float(np.max(u)),'random_utility':float(np.mean(u)),'rank_acc':np.nan});continue
                        order=sorted(candidates_idx,key=lambda i:(-m4[i],ast.literal_eval(rs[i]['pair']),rs[i]['operation']))
                    chosen=order[0]; best=np.max(u); hit=float(any(abs(u[i]-best)<=TOL for i in order if abs(score[i]-score[chosen])<=TOL))
                    # Pairwise ranking accuracy with ties in score credited 1/2.
                    wins=tot=0
                    for i in range(len(rs)):
                        for j in range(i+1,len(rs)):
                            if abs(u[i]-u[j])<=TOL:continue
                            tot+=1;prod=(score[i]-score[j])*(u[i]-u[j]);wins+=1 if prod>TOL else (.5 if abs(score[i]-score[j])<=TOL else 0)
                    sg.append({'utility':float(u[chosen]),'hit':hit,'gap':float(best-u[chosen]),'random_utility':float(np.mean(u)),'rank_acc':wins/tot if tot else np.nan})
                if sg:
                    ranking.append({'cohort':cohort,'gamma':g,'candidate_score':metric,'scm_with_2plus_candidates':len(sg),'mean_selected_regret_gain':float(np.mean([x['utility'] for x in sg])),'tied_best_hit_rate':float(np.mean([x['hit'] for x in sg])),'mean_optimality_gap':float(np.mean([x['gap'] for x in sg])),'mean_uniform_random_regret_gain':float(np.mean([x['random_utility'] for x in sg])),'mean_pairwise_rank_accuracy':float(np.nanmean([x['rank_acc'] for x in sg])) if np.isfinite([x['rank_acc'] for x in sg]).any() else None})
    write('single_edit_ranking_aggregate.csv',ranking)
    # Pair interactions first average ordered pairs within SCM; SCM, not candidate pair, is the inferential unit.
    pairagg=[]
    for c in expected:
        for g in GAMMAS:
            byscm=defaultdict(list)
            for r in pairs:
                if r['cohort']==c:byscm[r['scm']].append(num(r[f'interaction_g{g}']))
            scmmeans=np.array([np.mean(v) for v in byscm.values() if v]); n=len(scmmeans)
            if n:
                rrng=np.random.default_rng(SEED+100+list(expected).index(c)*10+GAMMAS.index(g));ix=rrng.integers(0,n,size=(NBOOT,n));boots=scmmeans[ix].mean(axis=1)
                pairagg.append({'cohort':c,'gamma':g,'scm_with_legal_pairs':n,'ordered_sequences':sum(map(len,byscm.values())),'mean_scm_mean_interaction':float(scmmeans.mean()),'ci95_low_scm_bootstrap':float(np.quantile(boots,.025)),'ci95_high_scm_bootstrap':float(np.quantile(boots,.975)),'scm_mean_synergy_positive':int((scmmeans>TOL).sum()),'scm_mean_additive_tie':int((np.abs(scmmeans)<=TOL).sum()),'scm_mean_substitution_negative':int((scmmeans< -TOL).sum())})
    write('two_edit_interaction_cluster_aggregate.csv',pairagg)
    # Holm correction for a transparently bounded family of post-hoc B=2 gamma-zero contrasts.
    family=[]
    chosen=[('S0','M4_ORIGINAL'),('S0','FULL_GREEDY'),('M4_ORIGINAL','FULL_GREEDY')]
    for c in expected:
        rows={(r['cohort'],r['scm'],r['policy'],int(r['budget'])):num(r['regret_g0']) for r in pol if r['cohort']==c and r['gamma']=='all'}
        for a,b in chosen:
            d=np.array([rows[(c,s,a,2)]-rows[(c,s,b,2)] for s in sorted({r['scm'] for r in pol if r['cohort']==c})])
            p=paired_t_pvalue(d) if len(d)>1 else 1.0
            family.append({'cohort':c,'gamma':0,'budget':2,'contrast':f'{a} - {b}','mean_difference':float(d.mean()),'paired_t_p_raw':p,'n_scm':len(d),'test':'two-sided paired t test; SCM differences assumed iid within named C cohort'})
        pv=np.array([r['paired_t_p_raw'] for r in family if r['cohort']==c]);adj=holm(pv);k=0
        for r in family:
            if r['cohort']==c:r['holm_p_within_cohort_3_contrasts']=float(adj[k]);k+=1
    write('holm_posthoc_primary_baselines.csv',family)
    summ={'status':'S3_COMPLETION_RECOMPUTED_WITH_LIMITATIONS','classification':'post-hoc exploratory','input_rows':{'S3_policy_unit_rows':len(pol),'single_edit_candidate_rows':len(candidates),'ordered_interaction_rows':len(pairs)},'cohort_n':expected,'gamma':list(GAMMAS),'bootstrap':{'replicates':NBOOT,'seed_by_cohort':{'C_DEVELOPMENT':SEED,'C_HELDOUT':SEED+1},'common_indices_reused_across_objectives_and_contrasts':True,'unit':'SCM','interval':'pointwise percentile'},'new_scm':0,'new_g0':0,'new_observations':0,'new_interventions':0,'public_aggregate_only':True,'limitations':['existing cohort reuse and post-hoc selection remain','candidate/rank data are summarized within SCM; no causal error-type effect','only B<=2 ex-post feasible edit universe was enumerated','no Research D unit-level data','no independent S4 cohort run']}
    (DEST/'summary.json').write_text(json.dumps(summ,indent=2),encoding='utf-8')
    print(json.dumps(summ,indent=2))

if __name__=='__main__':main()

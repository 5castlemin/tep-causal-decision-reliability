"""Hash-bound post-hoc S3 completion replay; aggregate outputs only."""
from __future__ import annotations
import csv, hashlib, itertools, json, os, time
from pathlib import Path
import numpy as np

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
import sys
sys.path[:0]=[str(ROOT),str(ROOT/'src')]
from research.within_task_repair_prioritization import s3_analysis as s3
from research.budget_aware_refinement.step3_adapter import prepare
from research.budget_aware_refinement.step4c1_gt import analytic_response
from research.original_objective import policy_engine as pe
from integrated_pilot import fit_model
from decision_mvp import static_mean_response

GAMMAS=(0.0,0.2,0.5); T=s3.T; SETS=s3.SETS; BOOT=10_000; BOOT_SEED=2026112703; TOL=1e-12
OUT=HERE/'outputs_completion_v1'

def csvout(name,rows):
    if not rows:return
    with (OUT/name).open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def main():
    if OUT.exists() and any(OUT.iterdir()): raise FileExistsError(f'refusing overwrite: {OUT}')
    OUT.mkdir(parents=True,exist_ok=True); started=time.perf_counter()
    all_units=[]; candidates_public=[]; interactions_public=[]; cohort_meta={}
    for cohort,cp,pp in s3.SOURCES:
        before={'cohort':s3.sha(cp),'proposals':s3.sha(pp)}
        assert before['cohort']==s3.EXPECTED[f'{cohort}:cohort'] and before['proposals']==s3.EXPECTED[f'{cohort}:proposals']
        _, rows=s3.load_cohort(cohort,cp,pp)
        units=[]; two_plus_count=0
        for sid,proposal,payload,scm,obs,truth,g0,cfg in rows:
            action,target=proposal['action'],proposal['target']; delta=payload['input_binding']['delta']
            data=np.asarray(obs['rows'],dtype=np.float64)
            request={'node_ids':proposal['nodes'],'action':action,'target':target}
            graph_cache={}
            def outcomes(g):
                h=pe.graph_hash(g)
                if h in graph_cache:return graph_cache[h]
                graph_result={'final_graph':[list(e) for e in sorted(e for e in g.values() if e!=pe.UNRES)]}
                _,sel=prepare(request,data,proposal['nodes'],proposal['nodes'],delta,fit_model,static_mean_response,graph_result=graph_result)
                target_value=sel['target']; scale=sel['sd_y']
                predicted={float(x['k']):float(x['predicted_loss']) for x in sel['candidates']}
                truth_spec=scm['truth_spec']
                truth_loss={float(x['k']):((float(analytic_response(truth_spec,action,float(x['action']))[proposal['target']])-target_value)/scale)**2 for x in sel['candidates']}
                out={}
                for gamma in GAMMAS:
                    pred_obj={k:v+gamma*k*k for k,v in predicted.items()}
                    chosen=min(pred_obj,key=lambda k:(pred_obj[k],abs(k),k))
                    gt_obj={k:v+gamma*k*k for k,v in truth_loss.items()}
                    best=min(gt_obj,key=lambda k:(gt_obj[k],abs(k),k))
                    out[gamma]={'regret':gt_obj[chosen]-gt_obj[best],'action_k':chosen,'optimum_k':best,'target':target_value,'scale':scale}
                graph_cache[h]=out;return out
            base=outcomes(g0)
            initial=pe.metrics(truth,g0,action,target,cfg)
            pool=[e for e in pe.candidates(truth,g0,action,target,cfg) if e.metric=='M4']
            feasible=[]
            q0=s3.q_metrics(g0,(truth,action,target,*s3.structural_sets(truth,action,target,cfg)))
            for e in pool:
                g1=pe.apply(g0,e)
                if not pe.dag(g1) or not s3.direct_task_edit(e,truth,g0,action,target,cfg):continue
                q1=s3.q_metrics(g1,(truth,action,target,*s3.structural_sets(truth,action,target,cfg)))
                y=outcomes(g1)
                row={'cohort':cohort,'scm':sid,'pair':list(e.pair),'operation':e.operation,'error_type':e.kind,'metric':e.metric,'graph_hash':pe.graph_hash(g1),
                     'T1_gain':q1['T1']-q0['T1'],'T2_gain':q1['T2']-q0['T2'],'T3_gain':q1['T3']-q0['T3'],'T4_gain':q1['T4']-q0['T4'],'T5_gain':q1['T5']-q0['T5'],'T6_gain':q1['T6']-q0['T6'],
                     'M4_structural_gain':s3.m4_gain(e,truth,g0,initial,action,target,cfg)}
                for ga in GAMMAS:
                    row[f'regret_gain_g{ga}']=base[ga]['regret']-y[ga]['regret'];row[f'action_changed_g{ga}']=y[ga]['action_k']!=base[ga]['action_k']
                candidates_public.append(row);feasible.append((e,g1,row))
            two_plus_count += int(len(feasible)>=2)
            # Every legal ordered sequence through depth 2, including no-op and one-edit choices.
            states=[('NO_EDIT',g0,())]
            states += [(e.key,g,((e.key,e.kind),)) for e,g,_ in feasible]
            second_legal=[]
            for e1,g1,r1 in feasible:
                for e2 in pool:
                    if e2.key==e1.key or not s3.direct_task_edit(e2,truth,g1,action,target,cfg):continue
                    g2=pe.apply(g1,e2)
                    if not pe.dag(g2):continue
                    second_legal.append((e1,g1,r1,e2,g2))
                    states.append((f'{e1.key}>{e2.key}',g2,((e1.key,e1.kind),(e2.key,e2.kind))))
            state_rows=[]
            for sidstate,g,seq in states:
                o=outcomes(g);state_rows.append({'id':sidstate,'hash':pe.graph_hash(g),'seq':seq,'cost':len(seq),'out':o})
            optimal={ga:min(state_rows,key=lambda z:(z['out'][ga]['regret'],z['cost'],z['hash'])) for ga in GAMMAS}
            # SCM-level ex-post single/two-edit summaries and pair interactions.
            best_single={ga:min([z for z in state_rows if z['cost']<=1],key=lambda z:(z['out'][ga]['regret'],z['cost'],z['hash'])) for ga in GAMMAS}
            for ga in GAMMAS:
                vals=[z['out'][ga]['regret'] for z in state_rows]; base_r=base[ga]['regret']
                unit={'cohort':cohort,'scm':sid,'gamma':ga,'initial_feasible_edits':len(feasible),'ordered_two_edit_sequences':len(second_legal),
                      'unique_final_graphs':len({z['hash'] for z in state_rows}),'base_regret':base_r,'best_single_regret':best_single[ga]['out'][ga]['regret'],
                      'best_two_or_fewer_regret':optimal[ga]['out'][ga]['regret'],'single_gap':best_single[ga]['out'][ga]['regret']-optimal[ga]['out'][ga]['regret'],
                      'two_or_fewer_gap':0.0,'optimal_cost':optimal[ga]['cost'],'best_single_cost':best_single[ga]['cost'],
                      'base_action_k':base[ga]['action_k'],'optimal_action_k':optimal[ga]['out'][ga]['action_k'],'optimal_graph_hash':optimal[ga]['hash'],
                      'best_single_graph_hash':best_single[ga]['hash'],'best_single_sequence':json.dumps(best_single[ga]['seq']),
                      'n_state_evaluations':len(state_rows),'n_unique_graph_evaluations':len(graph_cache)}
                units.append(unit)
            # Interaction only for edit pairs individually feasible at G0 and a legal ordered joint result.
            for e1,g1,r1,e2,g2 in second_legal:
                if not any(x.key==e2.key and gg==pe.apply(g0,e2) for x,gg,_ in feasible):continue
                r2row=next(rr for x,gg,rr in feasible if x.key==e2.key)
                joint=outcomes(g2)
                it={'cohort':cohort,'scm':sid,'edit1':json.dumps([list(e1.pair),e1.operation]),'edit2':json.dumps([list(e2.pair),e2.operation]),'error_type1':e1.kind,'error_type2':e2.kind,'joint_graph_hash':pe.graph_hash(g2),'reversed_order_feasible':False}
                for ga in GAMMAS:
                    v1=r1[f'regret_gain_g{ga}'];v2=r2row[f'regret_gain_g{ga}'];v12=base[ga]['regret']-joint[ga]['regret']
                    it[f'V1_g{ga}']=v1;it[f'V2_g{ga}']=v2;it[f'V12_g{ga}']=v12;it[f'interaction_g{ga}']=v12-v1-v2
                interactions_public.append(it)
            # Existing structure-guided 63 subset Greedy and 2-step Lookahead at B2.
            for combo in SETS:
                for b in (1,2,3,4):
                    g,log=s3.greedy(truth,g0,action,target,cfg,combo,b)
                    o=outcomes(g)
                    units.append({'cohort':cohort,'scm':sid,'gamma':'all','metric_set':'+'.join(combo),'policy':'T_GREEDY','budget':b,'regret_g0':o[0.0]['regret'],'regret_g0.2':o[0.2]['regret'],'regret_g0.5':o[0.5]['regret'],'cost':len(log),'graph_hash':pe.graph_hash(g),'action_g0':o[0.0]['action_k'],'action_g0.2':o[0.2]['action_k'],'action_g0.5':o[0.5]['action_k']})
                choice=s3.sequence2(truth,g0,action,target,cfg,combo)
                if choice is None:g2=g0;log2=[]
                else: _,e1,e2,g1,g2,fb=choice;log2=[e1]+([e2] if e2 is not None else [])
                o=outcomes(g2)
                units.append({'cohort':cohort,'scm':sid,'gamma':'all','metric_set':'+'.join(combo),'policy':'T_LOOKAHEAD2','budget':2,'regret_g0':o[0.0]['regret'],'regret_g0.2':o[0.2]['regret'],'regret_g0.5':o[0.5]['regret'],'cost':len(log2),'graph_hash':pe.graph_hash(g2),'action_g0':o[0.0]['action_k'],'action_g0.2':o[0.2]['action_k'],'action_g0.5':o[0.5]['action_k'],'fallback':bool(choice and choice[-1])})
            # S0, existing frozen baselines and regret-greedy / exact depth-2 optimum are separate diagnostics.
            for b in (0,1,2,3,4):
                for pid,subset,canon in [('S0',(),False),('FULL_GREEDY',pe.METRICS,False),('CANONICAL_ORACLE',pe.METRICS,True),('M4_ORIGINAL',('M4',),False)]:
                    res=pe.run(truth,g0,action,target,b,subset,cfg,canonical=canon);g=pe.state(res['final_edges'],unresolved=res['final_unresolved']);o=outcomes(g)
                    units.append({'cohort':cohort,'scm':sid,'gamma':'all','policy':pid,'budget':b,'regret_g0':o[0.0]['regret'],'regret_g0.2':o[0.2]['regret'],'regret_g0.5':o[0.5]['regret'],'cost':res['total_cost'],'graph_hash':res['final_hash'],'action_g0':o[0.0]['action_k'],'action_g0.2':o[0.2]['action_k'],'action_g0.5':o[0.5]['action_k']})
        cohort_meta[cohort]={'n':len(rows),'source_before':before,'feasibility_two_or_more':two_plus_count}
        all_units.extend(units)
        after={'cohort':s3.sha(cp),'proposals':s3.sha(pp)}
        assert before==after
        cohort_meta[cohort]['source_after']=after
    # Aggregate only; row-level unit table stays in ignored local output.
    private_path=OUT/'unit_results_private.csv';csvout('unit_results_private.csv',all_units)
    # Aggregate ex-post optimality and policy outcomes by cohort/gamma.
    summaries=[]
    for (c,gamma),grp in itertools.groupby(sorted((r for r in all_units if r.get('gamma') in GAMMAS),key=lambda x:(x['cohort'],x['gamma'])),key=lambda x:(x['cohort'],x['gamma'])):
        rows=list(grp); summaries.append({'cohort':c,'gamma':gamma,'n_scm':len(rows),'mean_base_regret':float(np.mean([r['base_regret'] for r in rows])),'mean_best_single_regret':float(np.mean([r['best_single_regret'] for r in rows])),'mean_expost_optimal_regret':float(np.mean([r['best_two_or_fewer_regret'] for r in rows])),'mean_single_gap':float(np.mean([r['single_gap'] for r in rows])),'mean_optimal_edits':float(np.mean([r['optimal_cost'] for r in rows])),'mean_initial_candidates':float(np.mean([r['initial_feasible_edits'] for r in rows])),'scm_with_two_or_more':sum(r['initial_feasible_edits']>=2 for r in rows),'positive_single_edit_fraction':float(np.mean([r['base_regret']-r['best_single_regret']>TOL for r in rows]))})
    csvout('expost_optimality_aggregate.csv',summaries)
    csvout('single_edit_candidates_aggregate.csv',candidates_public)
    csvout('two_edit_interactions_private.csv',interactions_public)
    public_inter=[]
    for c in sorted({r['cohort'] for r in interactions_public}):
        rr=[r for r in interactions_public if r['cohort']==c]
        for ga in GAMMAS:
            vv=[r[f'interaction_g{ga}'] for r in rr]
            public_inter.append({'cohort':c,'gamma':ga,'ordered_pair_rows':len(rr),'mean_interaction':float(np.mean(vv)) if vv else None,'median_interaction':float(np.median(vv)) if vv else None,'positive_complementarity_fraction':float(np.mean(np.array(vv)>TOL)) if vv else None,'negative_substitution_fraction':float(np.mean(np.array(vv)<-TOL)) if vv else None})
    csvout('two_edit_interactions_aggregate.csv',public_inter)
    # Common-index paired bootstrap for selected ex-post contrasts (all paired per SCM).
    paired=[]; rng=np.random.default_rng(BOOT_SEED)
    for c in ('C_DEVELOPMENT','C_HELDOUT'):
        base_rows=[r for r in all_units if r.get('gamma') in GAMMAS and r['cohort']==c]
        for ga in GAMMAS:
            vals=[r for r in base_rows if r['gamma']==ga]; n=len(vals); ix=rng.integers(0,n,size=(BOOT,n))
            for label,col in [('base_minus_expost','base_regret','best_two_or_fewer_regret'),('base_minus_single','base_regret','best_single_regret')]:
                d=np.array([r[col[0]]-r[col[1]] for r in vals])
                boot=d[ix].mean(axis=1)
                paired.append({'cohort':c,'gamma':ga,'contrast':label,'mean':float(d.mean()),'ci95_low':float(np.quantile(boot,.025)),'ci95_high':float(np.quantile(boot,.975)),'better':int(np.sum(d>TOL)),'worse':int(np.sum(d< -TOL)),'tie':int(np.sum(np.abs(d)<=TOL)),'n':n,'bootstrap_seed':BOOT_SEED,'replicates':BOOT})
    csvout('expost_paired_bootstrap.csv',paired)
    summary={'gate':'S3_COMPLETION_RECOMPUTED_WITH_LIMITATIONS','classification':'post-hoc exploratory','source_commit':os.environ.get('S3_SOURCE_COMMIT','unknown'),'cohorts':cohort_meta,'gamma':list(GAMMAS),'subsets':len(SETS),'policy_unit_rows':sum(r.get('gamma')=='all' for r in all_units),'single_candidate_rows':len(candidates_public),'two_edit_ordered_sequences':len(interactions_public),'bootstrap':{'replicates':BOOT,'seed':BOOT_SEED,'unit':'SCM','paired_common_indices_per_cohort':True},'new_scm':0,'new_g0':0,'new_observation_draws':0,'new_intervention_rows':0,'observation_reconstruction':'deterministic original-seed restoration; exact original observation digest asserted by s3.load_cohort','private_unit_file':private_path.name,'public_rows_include_scm_keys':False,'elapsed_seconds':time.perf_counter()-started,'limits':['candidate and sequence records remain in ignored private local output; public output is aggregate-only','two-edit interactions only defined for initially feasible individual edits and legal ordered pairs','no Research D unit-level data used']}
    (OUT/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps(summary,indent=2))

if __name__=='__main__':main()

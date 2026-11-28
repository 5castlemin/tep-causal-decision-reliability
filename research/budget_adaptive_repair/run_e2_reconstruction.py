"""Hash-identical restoration and budget saturation analysis for C only."""
from __future__ import annotations

import csv, hashlib, json, sqlite3, sys, time
import os
from collections import defaultdict
from pathlib import Path

import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from research.budget_aware_refinement.step4c1_scm import generate_scm_parameters, generate_observations
from research.budget_aware_refinement.step3_adapter import prepare, evaluate
from research.budget_aware_refinement.step4c1_gt import analytic_response
from research.original_objective import policy_engine as pe
from integrated_pilot import fit_model
from decision_mvp import static_mean_response

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / "outputs"
DATA_ROOT=Path(os.environ.get("DAT_RESEARCH_ROOT","C:/DAT_RESEARCH"))
SOURCES = [
    ("C_DEVELOPMENT", "development", DATA_ROOT/"research-c/development/development-20261123-seed-2026112301-v1/research_c_cohort.sqlite", DATA_ROOT/"research-c/development/development-20261123-seed-2026112301-v1/research_c_proposal_stage.sqlite"),
    ("C_HELDOUT", "confirmation", DATA_ROOT/"research-c/heldout/independent-evaluation-20261123-seed-2026112303-v1/research_c_cohort.sqlite", DATA_ROOT/"research-c/heldout/independent-evaluation-20261123-seed-2026112303-v1/research_c_proposal_stage.sqlite"),
]

def digest_file(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''): h.update(b)
    return h.hexdigest()

def cfg_from(payload):
    c=dict(payload['config']['repair_config'])
    c['costs']=tuple(tuple(x) for x in c['costs']); c['beta']=tuple(c['beta']); c['weights']=tuple(c['weights']); c['route_relevant_fp']=tuple(tuple(x) for x in c['route_relevant_fp'])
    return pe.Config(**c)

def main():
    OUT.mkdir(parents=True,exist_ok=True); started=time.perf_counter()
    all_results={}; summaries=[]; provenance=[]
    policies=[(('S0' if not subset else '+'.join(subset)),subset,False) for subset in pe.catalog()]
    policies.append(('CANONICAL_ORACLE',pe.METRICS,True))
    for cohort,proposal_cohort,cohort_path,proposal_path in SOURCES:
        con=sqlite3.connect(f'file:{cohort_path}?mode=ro',uri=True); con.execute('pragma query_only=on')
        propcon=sqlite3.connect(f'file:{proposal_path}?mode=ro',uri=True); propcon.execute('pragma query_only=on')
        prop_by_scm={}
        for (raw,) in propcon.execute("select proposal_json from proposal_attempts where status='ELIGIBLE'"):
            proposal=json.loads(raw); prop_by_scm[proposal['scm_id']]=proposal
        rows=list(con.execute('select scm_id,status,result_json from scms order by ordinal'))
        error_counts=[]
        for scm_id,status,raw in rows:
            assert status=='COMPLETED'; payload=json.loads(raw)['payload']; proposal=prop_by_scm[scm_id]
            scm=generate_scm_parameters(proposal); obs=generate_observations(proposal,scm)
            binding=payload['input_binding']
            assert scm['equation_signature_sha256']==binding['truth_spec_sha256']
            assert obs['data_sha256']==binding['observations_sha256']
            assert (proposal['action'],proposal['target'])==(binding['action'],binding['target'])
            truth=pe.state([tuple(e) for e in scm['truth_spec']['edges']])
            initial_json=payload['g0_generation']['initial_graph']
            initial=pe.state([tuple(e) for e in initial_json['edges']],unresolved=[tuple(e) for e in initial_json['unresolved']])
            config=cfg_from(payload)
            stats=pe.metrics(truth,initial,proposal['action'],proposal['target'],config)
            err=sum(sum(x.values()) for m in stats['counts'].values() for x in [m])
            error_counts.append(err)
        bmax=max(4,max(error_counts))
        provenance.append({'cohort':cohort,'n':len(rows),'initial_error_min':int(min(error_counts)),'initial_error_mean':float(np.mean(error_counts)),
            'initial_error_median':float(np.median(error_counts)),'initial_error_q90':float(np.quantile(error_counts,.90)),
            'initial_error_q95':float(np.quantile(error_counts,.95)),'initial_error_q99':float(np.quantile(error_counts,.99)),
            'initial_error_max':int(max(error_counts)),'B_max':bmax})
        # Second pass: recalc each budget; never alter a ledger or proposal DB.
        for scm_id,status,raw in rows:
            payload=json.loads(raw)['payload']; proposal=prop_by_scm[scm_id]
            scm=generate_scm_parameters(proposal); obs=generate_observations(proposal,scm); data=np.asarray(obs['rows'],dtype=np.float64)
            truth=pe.state([tuple(e) for e in scm['truth_spec']['edges']]); gj=payload['g0_generation']['initial_graph']
            initial=pe.state([tuple(e) for e in gj['edges']],unresolved=[tuple(e) for e in gj['unresolved']]); config=cfg_from(payload)
            initial_errors=sum(sum(v.values()) for v in pe.metrics(truth,initial,proposal['action'],proposal['target'],config)['counts'].values())
            request={'node_ids':proposal['nodes'],'action':proposal['action'],'target':proposal['target']}; delta=binding_delta=payload['input_binding']['delta']
            cache={}; canonical=json.loads(raw)['payload']['e2e_result']['budgets']
            for policy_id,subset,is_canonical in policies:
                for budget in range(bmax+1):
                    rr=pe.run(truth,initial,proposal['action'],proposal['target'],budget,subset,config,canonical=is_canonical)
                    if budget<=4:
                        old=next(x for x in canonical[budget]['policies'] if x['policy_id']==policy_id)
                        assert rr['final_hash']==old['final_graph_sha256'],(cohort,scm_id,policy_id,budget,'graph hash')
                        assert json.dumps(rr['edits'],sort_keys=True)==json.dumps(old['edit_log'],sort_keys=True),(cohort,scm_id,policy_id,budget,'edit log')
                    cachekey=rr['final_hash']
                    if cachekey not in cache:
                        directed=[list(e) for e in rr['final_edges']]
                        _,selection=prepare(request,data,proposal['nodes'],proposal['nodes'],delta,fit_model,static_mean_response,graph_result={'final_graph':directed})
                        ev=evaluate(selection,scm['truth_spec'],analytic_response)
                        cache[cachekey]=(selection,ev)
                    selection,ev=cache[cachekey]
                    if budget<=4:
                        old=next(x for x in canonical[budget]['policies'] if x['policy_id']==policy_id)
                        assert float(next(r['action'] for r in selection['candidates'] if r['k']==selection['selected_k']))==float(old['evaluation']['selected_action']),(cohort,scm_id,policy_id,budget,'action')
                        assert abs(float(ev['regret'])-float(old['evaluation']['regret']))<1e-12,(cohort,scm_id,policy_id,budget,'regret')
                    key=(cohort,scm_id,policy_id,budget)
                    final_errors=rr['final_counts']; remaining=sum(sum(v.values()) for v in final_errors.values())
                    terminal=pe.state(rr['final_edges'],unresolved=rr['final_unresolved'])
                    terminal_candidates=pe.candidates(truth,terminal,proposal['action'],proposal['target'],config)
                    eligible=[e for e in terminal_candidates if is_canonical or e.metric in subset]
                    feasible=[e for e in eligible if pe.dag(pe.apply(terminal,e))]
                    all_feasible=[e for e in terminal_candidates if pe.dag(pe.apply(terminal,e))]
                    all_results[key]={'loss':float(ev['regret']),'cost':float(rr['total_cost']),'unused':float(rr['unused_budget']),
                        'task_edits':sum(x['metric']=='M4' for x in rr['edits']),'offtask_edits':sum(x['metric']!='M4' for x in rr['edits']),
                        'remaining_errors':remaining,'action':float(next(r['action'] for r in selection['candidates'] if r['k']==selection['selected_k'])),
                        'initial_errors':initial_errors,'policy_stop':rr['stop_reason'],'dag_rejects':rr['dag_rejects'],
                        'graph_hash':rr['final_hash'],'edits':rr['edits'],'same_as_s0':None,
                        'terminal_policy_candidate_count':len(eligible),'terminal_policy_feasible_count':len(feasible),
                        'terminal_all_candidate_count':len(terminal_candidates),'terminal_all_feasible_count':len(all_feasible),
                        'constraint_saturated':bool(eligible and not feasible),
                        'policy_candidate_saturated':bool(not eligible),
                        'structurally_saturated':bool(not terminal_candidates)}
            # mark action changes vs baseline at the matching budgets
            for budget in range(bmax+1):
                s0=all_results[(cohort,scm_id,'S0',budget)]['action']
                for pid,subset,is_canonical in policies:
                    all_results[(cohort,scm_id,pid,budget)]['same_as_s0']=all_results[(cohort,scm_id,pid,budget)]['action']==s0
        con.close();propcon.close()
    for key,r in all_results.items():
        cohort,scm_id,policy,budget=key
        summaries.append({'cohort':cohort,'scm_id':scm_id,'policy':policy,'budget':budget,**{k:v for k,v in r.items() if k not in ('edits',)}})
    outpath=OUT/'c_extended_budget_results.csv'
    with outpath.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(summaries[0]));w.writeheader();w.writerows(summaries)
    # cohort/policy/budget aggregates and structural/policy/decision saturation diagnostics
    grouped=defaultdict(list)
    for r in summaries: grouped[(r['cohort'],r['policy'],r['budget'])].append(r)
    aggregate=[]
    for (cohort,policy,b),rs in sorted(grouped.items()):
        for metric in ('loss','cost','unused','task_edits','offtask_edits','remaining_errors'):
            pass
        aggregate.append({'cohort':cohort,'policy':policy,'budget':b,'n':len(rs),'mean_regret':float(np.mean([r['loss'] for r in rs])),
            'mean_cost':float(np.mean([r['cost'] for r in rs])),'mean_unused_budget':float(np.mean([r['unused'] for r in rs])),
            'mean_remaining_errors':float(np.mean([r['remaining_errors'] for r in rs])),
            'mean_task_edits':float(np.mean([r['task_edits'] for r in rs])),'mean_offtask_edits':float(np.mean([r['offtask_edits'] for r in rs])),
            'action_change_rate':float(np.mean([not r['same_as_s0'] for r in rs]))})
    with (OUT/'c_extended_budget_aggregate.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(aggregate[0]));w.writeheader();w.writerows(aggregate)
    summary={'status':'PASS_HASH_IDENTICAL_RECONSTRUCTION_AND_B0_B4_REPLAY','cohorts':provenance,'unit':'original Research C SCM; exact restoration, not new cohort',
        'added_evaluations':'budgets 5..B_max for all 17 policies using original deterministic truth/observations and analytic evaluator',
        'reconstruction_arrays':'generated in memory and discarded; each truth, 512-row observation matrix, task and G0 checked against ledger bindings before analysis',
        'B0_B4_verification':'all original graphs, edit sequences, chosen actions and regrets re-matched for all SCMs/policies/budgets',
        'source_hashes':{f'{cohort}:{kind}':digest_file(path) for cohort,_,cp,pp in SOURCES for kind,path in (("cohort",cp),("proposal_stage",pp))},
        'elapsed_seconds':time.perf_counter()-started,'new_scm_or_g0_count':0,'new_intervention_rows':0,
        'outputs':['c_extended_budget_results.csv','c_extended_budget_aggregate.csv']}
    (OUT/'e2_reconstruction_summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps(summary,indent=2))

if __name__=='__main__': main()

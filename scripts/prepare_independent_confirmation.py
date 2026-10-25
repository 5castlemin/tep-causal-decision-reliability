"""Freeze rule-generated DAGs and all analysis inputs BEFORE confirmation sampling."""
import copy,hashlib,json,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'));sys.path.insert(0,str(ROOT/'scripts'))
from independent_confirmation import select_controls
from diverse_structure_pilot import all_paths
from run_diverse_structure_pilot import save

def near_same(g,h):
    """Up to one edge removed from each, under any node relabeling; exact check."""
    import networkx as nx
    if len(g)!=len(h) or abs(g.number_of_edges()-h.number_of_edges())>1:return False
    left=[g]+[g.copy() for _ in g.edges];right=[h]+[h.copy() for _ in h.edges]
    for v,e in zip(left[1:],g.edges):v.remove_edge(*e)
    for v,e in zip(right[1:],h.edges):v.remove_edge(*e)
    return any(a.number_of_edges()==b.number_of_edges() and nx.is_isomorphic(a,b) for a in left for b in right)

def generate(old):
    import numpy as np
    import networkx as nx
    specs=[];records=[]
    old_graphs=[nx.DiGraph([(e['source'],e['target']) for e in s['edges']]) for s in old['structures']]
    for g,s in zip(old_graphs,old['structures']):g.add_nodes_from(s['nodes'])
    for group in ['A','B','C']:
        accepted=0;attempt=0
        while accepted<4:
            if attempt>=1000:raise RuntimeError('STRUCTURAL_RULE_EXHAUSTED_NO_SILENT_RELAXATION')
            seed=925200+1000*ord(group)+attempt;attempt+=1;rng=np.random.default_rng(seed)
            n=int(rng.integers(6,11));core=['V'+str(i) for i in range(n-2)];nodes=core+['P','Q'];last=len(core)-1
            pairs={(core[i],core[i+1]) for i in range(last)}|{('P','Q')}
            prob={'A':.07,'B':.5,'C':.32}[group]
            for i in range(len(core)):
                for j in range(i+2,len(core)):
                    if rng.random()<prob:pairs.add((core[i],core[j]))
            if group=='C':pairs.add((core[0],core[-1]))
            g=nx.DiGraph();g.add_nodes_from(nodes);g.add_edges_from(pairs)
            reason=None
            if group=='B' and len(all_paths(pairs,core[0],core[-1]))<2:reason='DENSE_GROUP_REQUIRES_MULTIPLE_PATHS'
            if any(near_same(g,h) for h in old_graphs):reason='ISOMORPHIC_OR_ONE_EDGE_NEIGHBOR_OF_OLD_S1_S8'
            if any(near_same(g,nx.DiGraph([(e['source'],e['target']) for e in s['edges']])) for s in specs):reason='ISOMORPHIC_OR_ONE_EDGE_NEIGHBOR_OF_ACCEPTED_CONFIRMATION'
            if reason:records.append(dict(seed=seed,group=group,accepted=False,reason=reason,n_nodes=n,n_edges=len(pairs)));continue
            accepted+=1;sid='C'+str(len(specs)+1).zfill(2);edges=[]
            for a,b in sorted(pairs):
                magnitude=round(float(rng.uniform(.35,1.2)),4)
                sign=-1 if group=='C' and ((a,b)==(core[0],core[-1]) or (a not in core[:-1] or b!=core[core.index(a)+1]) and rng.random()<.5) else 1
                edges.append(dict(source=a,target=b,coefficient=sign*magnitude))
            tasks=[]
            for tid,action,target,goal,kind in [('direct',core[-2],core[-1],.65,'direct'),('path',core[0],core[-1],.6,'indirect')]:
                for setting,grid,cost in [('primary',[-1,-.5,0,.5,1],.2),('fine',[-1,-.75,-.5,-.25,0,.25,.5,.75,1],.2),('low_cost',[-1,-.5,0,.5,1],.1),('high_cost',[-1,-.5,0,.5,1],.4)]:
                    tasks.append(dict(task_id=tid if setting=='primary' else tid+'__'+setting,action=action,target=target,
                        target_value=goal,task_kind=kind,setting=setting,action_values=grid,reference_action=0.,cost_weight=cost,loss_scale=1.,
                        measurement='independent do target mean; empirical and analytic losses separate'))
            index=len(specs);spec=dict(structure_id=sid,label='Rule-generated family '+group,group=group,generation_seed=seed,nodes=nodes,
                algorithm_column_order=rng.permutation(nodes).tolist(),edges=edges,noise_sd={v:1. for v in nodes},tasks=tasks,
                tags=[group,'all_observed','independent_uniform','peripheral_branch'],acceptance_seed=930000+index*10000,
                evaluation_seed_base=2000000+index*10000,datasets=[dict(dataset_id=sid+'_n'+str(n)+'_r'+str(r),train_n=n,replicate=r,
                    train_seed=10000000+index*100000+n*100+r*10,validation_seed=10000000+index*100000+n*100+r*10+1,
                    validation_n=256,algorithm_seed=10000000+index*100000+n*100+r*10+2) for n in [256,512] for r in [1,2,3]])
            variants,notes=select_controls(spec);spec['controlled_variants']=variants;spec['controlled_selection']=notes
            specs.append(spec);records.append(dict(seed=seed,group=group,accepted=True,structure_id=sid,n_nodes=n,n_edges=len(pairs),
                longest_path=len(core)-1,path_count=len(all_paths(pairs,core[0],core[-1])),reason='predefined structural criteria only, not learned/observed effects'))
    return specs,records

def main():
    base=ROOT/'research_runs/independent_confirmation';replay=json.loads((base/'REPLAY_COMPARISON.json').read_text(encoding='utf-8'));assert replay['status']=='PASS'
    assert not (base/'PLAN_v1.json').exists(),'DO_NOT_REFREEZE_AFTER_DATA'
    old=json.loads((ROOT/'research_runs/diverse_structure_pilot/PLAN_v1.json').read_text(encoding='utf-8'))
    plan=copy.deepcopy(old);plan.update(protocol='INDEPENDENT-CONFIRMATION-v1',date='2026-10-25',scope='authorized synthetic confirmation only, no manufacturing adoption',base_commit='a4ae7694aff24e8a40dce516cf44007d52676907',base_branch='feature/diverse-causal-structures',base_pr=13)
    plan['structures'],rejections=generate(old)
    plan['generation_rules']=dict(program='scripts/prepare_independent_confirmation.py',families=dict(A='chain+skip probability .07',B='chain+skip probability .5, at least2paths',C='chain+skip probability .32, negative direct shortcut and signed extra edges'),
        seed_formula='925200+1000*ord(group)+attempt',n_nodes='uniform integer6..10',coefficients='uniform magnitude .35..1.2 rounded4; positive chains; family C direct shortcut negative and extra edges randomly signed',
        peripheral='P->Q independent of core',reject='same node count and isomorphic after removing at most1edge from each (old or already accepted); B requires multiple paths; no quality/outcome input',
        task_rule='last core edge direct and first core->last core path, fixed goals .65/.6 independent of coefficients')
    ids=[s['structure_id'] for s in plan['structures']];plan['acceptance']['first_stage']=ids[:2];plan['acceptance']['all_stage']=ids
    plan['evaluation']['candidate_union']=[-1,-.75,-.5,-.25,0,.25,.5,.75,1]
    plan['evaluation']['condition_index']='0..8 union grid,9 independent reference; map each scenario grid by value'
    plan['execution']=dict(worker='unchanged scripts/learn_diverse_graph.py, independent child per graph',parallelism='3 child processes per dataset, isolated RNG, fixed result collection order',replay='original serial runner unchanged')
    plan['controlled_errors']=dict(enabled=True,structures=ids,scope='separate artificial errors; lexical rules fixed before confirmation, NOT real discovery',use_in_primary_analysis=False)
    plan['confirmation_analysis']=dict(models=['M0','M1','M2','M3'],supplementary='M4_incremental',trained_on='old S1..S8 only',alpha=.01,
        frozen_models='exploratory_diagnostics_v1/frozen_prediction_models.json',primary='confirmed_only, direct/path task IDs only',
        outcome='scale_normalized_regret',metric='structure-equal macro MAE',delta='MAE(M1)-MAE(M2)',minimum_improvement=.01,
        uncertainty=dict(method='whole-structure percentile bootstrap',repeats=10000,seed=925104,interval=[.025,.975],leave_one_structure_out=True),
        uncertainty_limit='fixed4-per-family quotas and uniqueness rejection constrain exchangeability; structure bootstrap is conditional descriptive precision, not random manufacturing-population sampling or uncertainty in old fitted models',
        decision=dict(support='delta>=.01 and bootstrap lower>0',counter='delta<=-.01 and bootstrap upper<0',otherwise='INCONCLUSIVE',invalid='not all12 structures evaluated; any structure has fewer than4datasets with at least2algorithms; pooled skeleton or path metric constant'),
        no_posthoc_clipping=True,all_sensitivity_settings='primary5/.2, fine9/.2, low5/.1, high5/.4 all12 structures/both tasks/3policies; assess separately',
        fixed_effect='all graphs predict do(.5)-do(0) without optimizing, compare empirical independent do means and analytic mean',
        inference_limit='rule-generated synthetic families; old metric candidates already selected after exploratory findings; no causal effect of metric, no manufacturing claim')
    plan['analysis']=dict(active='confirmation_analysis replaces previous exploratory LOSO protocol',metric_definitions='reuse inherited metrics unchanged',old_training_structures=8,new_confirmation_structures=12)
    source_paths=['src/independent_confirmation.py','scripts/prepare_independent_confirmation.py','scripts/run_independent_confirmation.py','scripts/analyze_independent_confirmation.py','tests/test_independent_confirmation.py']
    plan['frozen_code_sha256']={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in source_paths}
    plan['frozen_models_sha256']=hashlib.sha256((base/plan['confirmation_analysis']['frozen_models']).read_bytes()).hexdigest()
    save(base/'generation_acceptance_records.json',rejections);save(base/'PLAN_v1.json',plan)
    save(base/'FREEZE.json',dict(utc=datetime.now(timezone.utc).isoformat(),plan_sha256=hashlib.sha256((base/'PLAN_v1.json').read_bytes()).hexdigest(),confirmation_data_started=False,structures=12,code=plan['frozen_code_sha256'],models_sha256=plan['frozen_models_sha256']))
    print('12 structures + all code/models/seeds/sensitivity/bootstrap frozen before sampling')
if __name__=='__main__':main()

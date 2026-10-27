"""Static proposal consistency only. No simulator, equations, GT, fit or do run."""
from hashlib import sha256
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'research_runs/bounded_dynamic_protocol'


def load(path):return json.loads(path.read_text(encoding='utf-8-sig'))


def validate_proposal(p,d):
    """Reject accidental promotion of this unresolved proposal to executable GT."""
    assert p['status']==d['status']=='PROPOSED_FOR_REVIEW'
    assert p['protocol_id']==d['protocol_id']
    assert p['authorization']==dict(design_review_only=True,execution_allowed=False,
        official_gt_allowed=False,environment_adopted=False,research_design_changed=False,merge_allowed=False)
    assert [n['id'] for n in p['nodes']]==['u','v','W','E']
    f=p['finite_comparison_design']
    expected={(s,t,1) for s in ['u','v','W','E'] for t in ['v','W','E']}
    actual={(x['source'],x['target'],x['lag']) for x in f['universe']}
    assert len(f['universe'])==12 and actual==expected
    assert f['lag_steps']==[1] and f['targets']==['v','W','E']
    assert all(x['scoring_status']=='NOT_ADJUDICATED' for x in f['universe'])
    assert f['justified_negative_pairs_for_discovery']==[]
    closure={x['target']:x['status'] for x in p['parent_closure']}
    assert closure==dict(v_next='CONDITIONALLY_CLOSED_ONLY',W_next='NOT_CLOSED',
                         E_next='NOT_CLOSED',T_R_H='NOT_CLOSED')
    boundaries={x['id']:x for x in p['boundaries']}
    for key in ['reactor_inventory','surrounding_flux_and_reaction','UA_and_agitator']:
        b=boundaries[key]
        assert b['exogenous'] is False and b['directly_actuatable'] is False
        assert b['fixed_under_candidate_actions'] is False
    gate=p['scoring_gate']
    assert gate['finite_universe_fixed_as_proposal'] is True
    assert all(gate[k] is False for k in gate if k!='finite_universe_fixed_as_proposal')
    task=p['decision_task']
    for key in ['action_values_pp','physical_admissible_range','horizon_seconds','target_temperature_degC','cost_weight']:
        assert task[key] is None
    assert task['minimum_distinct_choices']==2 and len(set(task['choices']))>=2
    assert task['status']=='BLOCKED_NOT_A_READY_TASK'
    assert p['learning_contract']['new_dataset_allowed'] is False
    assert all(a['eligible'] is False for a in p['learning_contract']['algorithms'])
    assert all(v==0 for v in p['new_activity'].values())
    assert d['requested_judgment']==2 and d['conclusion']=='LIMITED_DYNAMIC_CONTRACT_CURRENTLY_NOT_JUSTIFIED'
    assert d['execution_gate']=='NO-GO'
    for key in ['scope_changed','environment_adopted','official_gt_created','research_hypothesis_confirmed','code_alone_resolves_primary_blocker']:
        assert d[key] is False
    assert d['c_is_not_original_hypothesis_test'] is True
    assert set(d['reason_codes'])=={'ENDOGENOUS_BOUNDARY_NOT_CLOSED','DISCOVERY_REFERENCE_ESTIMAND_MISMATCH',
        'OBSERVATION_EXCITATION_UNJUSTIFIED','NONTRIVIAL_TEMPERATURE_DECISION_NOT_READY'}
    return dict(status='PASS_STATIC_CONSISTENCY_ONLY',nodes=4,proposed_pairs=12,
                scientific_judgment=2,execution_allowed=False,source_executed=False)


def main():
    p=load(BASE/'PROTOCOL.json');d=load(BASE/'DECISION.json')
    result=validate_proposal(p,d)
    for record in load(BASE/'EVIDENCE.json')['files']:
        path=ROOT/record['path']
        assert sha256(path.read_bytes().replace(b'\r\n',b'\n')).hexdigest()==record['sha256_lf'],record['path']
    state=load(ROOT/'docs/research_state.json')
    current=state['bounded_dynamic_protocol']
    assert current['review_status']=='PROPOSED_FOR_REVIEW' and current['judgment']==2
    assert current['new_simulator_runs']==current['new_discovery_fits']==current['new_do_samples']==0
    assert current['research_design_changed'] is False
    report=(ROOT/'docs/research_design/BOUNDED_DYNAMIC_RESEARCH_PROTOCOL.md').read_text(encoding='utf-8')
    assert '판정 2' in report and 'PROPOSED_FOR_REVIEW' in report
    print('[PASS_STATIC_ONLY] proposed4nodes/12unadjudicated pairs; endogenous boundaries retained; judgment2/NO-GO; evidence/document/state consistency. No model execution or new GT.')
    return result


if __name__=='__main__':main()

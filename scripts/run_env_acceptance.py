"""Execute the explicitly approved, isolated, source-pinned FCM fixture acceptance."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from fcm_acceptance_adapter import load_pinned_module,build_fixture,sample,reconstruction
from decision_mvp import static_mean_response,require_research_environment


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')


def execute(args):
    if not args.execution_approved:raise PermissionError('SEPARATE_EXECUTION_APPROVAL_REQUIRED')
    if sys.prefix==sys.base_prefix:raise RuntimeError('ISOLATED_VENV_REQUIRED')
    os.environ['MPLBACKEND']='Agg'
    os.environ['MPLCONFIGDIR']=str(Path(sys.prefix)/'.mplcache')
    import numpy as np
    import pandas as pd
    plan_path=ROOT/'research_runs/env_acceptance/PLAN_v1.json';plan=read(plan_path)
    module=load_pinned_module(args.module)
    out=args.output;raw=out/'raw';raw.mkdir()
    write(out/'plan.json',plan)
    freeze=subprocess.check_output([sys.executable,'-m','pip','freeze','--all'],text=True)
    (out/'requirements.lock.txt').write_text(freeze,encoding='utf-8',newline='\n')
    expected={tuple(e) for e in plan['expected_direct_edges']}
    fcm,symbols=build_fixture(module,3101)
    gt=fcm.ground_truth
    gt.index=[str(x) for x in gt.index];gt.columns=[str(x) for x in gt.columns]
    gt=gt.loc[plan['nodes'],plan['nodes']]
    returned={(a,b) for a in gt.index for b in gt.columns if gt.loc[a,b]!=0}
    assert returned==expected and list(gt.index)==list(gt.columns)==plan['nodes']
    gt.to_csv(out/'declared_fixture_reference.csv',lineterminator='\n')
    assert set(plan['train_seeds']).isdisjoint(plan['holdout_seeds'])
    records=[];common_noise_checks=[];repeat_checks=[];hook_controls=[]
    total_calls=0
    for split,seeds in [('train',plan['train_seeds']),('holdout',plan['holdout_seeds'])]:
        for seed in seeds:
            first_frames={};first_noise={}
            for condition,action in [('observational',None),('do_A_minus0.1',-0.1),('do_A_plus0.1',0.1)]:
                condition_records=[]
                for repeat in range(plan['repeats']):
                    frame,noise,metadata=sample(module,seed,plan['sample_count'],action);total_calls+=1
                    errors=reconstruction(frame,noise,action)
                    assert all(value<=1e-10 for value in errors.values()),errors
                    assert {tuple(e) for e in metadata['original_edges']}==expected
                    if action is not None:
                        cut=metadata['mutilated']
                        assert not cut['action_parents'] and float(cut['action_term'])==action
                        assert {tuple(e) for e in cut['edges']}==expected-{('R','A')}
                        assert cut['nonaction_terms_unchanged']
                        assert np.array_equal(frame['A'].to_numpy(),np.full(plan['sample_count'],action))
                    tag=f'{split}__seed{seed}__{condition}__repeat{repeat}'
                    data_path=raw/(tag+'.csv');noise_path=raw/(tag+'__noise.csv')
                    frame.rename_axis('sample_id').to_csv(data_path,lineterminator='\n')
                    pd.DataFrame(noise).rename_axis('sample_id').to_csv(noise_path,lineterminator='\n')
                    record=dict(batch=tag,split=split,seed=seed,condition=condition,action=action,repeat=repeat,
                        count=len(frame),axis=plan['sample_axis'],data_file='raw/'+data_path.name,noise_file='raw/'+noise_path.name,
                        data_sha256=sha(data_path),noise_sha256=sha(noise_path),mechanism_max_abs_error=errors,metadata=metadata)
                    records.append(record);condition_records.append(record)
                    if repeat==0:first_frames[condition]=frame;first_noise[condition]=noise
                repeat_checks.append(dict(seed=seed,condition=condition,
                    data_exact=condition_records[0]['data_sha256']==condition_records[1]['data_sha256'],
                    noise_exact=condition_records[0]['noise_sha256']==condition_records[1]['noise_sha256']))
                original,syms=build_fixture(module,seed)
                if action is None:unhooked=original.sample(size=plan['sample_count'],additive_gaussian_noise=False,snr=None)
                else:
                    original.intervene_on({syms['A']:float(action)})
                    unhooked=original.interventional_sample(size=plan['sample_count'],which_intervention=0,additive_gaussian_noise=False,snr=None)
                total_calls+=1
                unhooked=unhooked.loc[:,plan['nodes']].astype(float)
                hook_controls.append(dict(seed=seed,condition=condition,exact=unhooked.equals(first_frames[condition])))
            for condition in ['do_A_minus0.1','do_A_plus0.1']:
                obs=first_noise['observational'];do=first_noise[condition]
                common_noise_checks.append(dict(seed=seed,condition=condition,
                    per_noise_equal={key:bool(np.array_equal(obs[key],do[key])) for key in sorted(set(obs)&set(do))},
                    removed_noise=sorted(set(obs)-set(do)),
                    interpretation='동일 seed가 행별 동일 외생 잡음을 보장하는지 관찰. 불일치하면 분포수준 do만 허용'))
    assert all(x['data_exact'] and x['noise_exact'] for x in repeat_checks)
    assert all(x['exact'] for x in hook_controls)
    first_observations=[r for r in records if r['condition']=='observational' and r['repeat']==0]
    new_seed_distinct=len({r['data_sha256'] for r in first_observations})==3
    assert new_seed_distinct
    # Reuse PR9 evaluation machinery with declared oracle coefficients: no fitting.
    oracle=dict(scaler_mean={n:0.0 for n in plan['nodes']},scaler_std={n:1.0 for n in plan['nodes']},equations=[
        dict(target='R',intercept_standardized=0.0,parents=[]),
        dict(target='A',intercept_standardized=0.0,parents=[dict(source='R',lag=0,coefficient_standardized=2.0)]),
        dict(target='M',intercept_standardized=0.0,parents=[dict(source='A',lag=0,coefficient_standardized=3.0)]),
        dict(target='Y',intercept_standardized=0.0,parents=[dict(source='M',lag=0,coefficient_standardized=1.0),dict(source='R',lag=0,coefficient_standardized=1.0)])])
    oracle_check={str(a):static_mean_response(oracle,'A',a)['Y'] for a in plan['action_values']}
    assert all(abs(value-3*float(a))<1e-12 for a,value in oracle_check.items())
    environment_id='CAUSALASSEMBLY_EXAMPLE_IID_'+sha(plan_path)[:12]
    approvals={k:True for k in ['model_controller_identity','variable_intervention_alignment','reference_structure_valid','independent_evaluation_contract']}
    require_research_environment(environment_id,environment_id,approvals)
    try:require_research_environment('CPCAD_PIN_72b0f5e',environment_id,approvals)
    except ValueError:cross_environment_rejected=True
    else:raise AssertionError('CROSS_ENVIRONMENT_JOIN_WAS_ALLOWED')
    result=dict(protocol=plan['protocol'],status='PASS_EXAMPLE_IID_FCM_ONLY',environment_id=environment_id,
        approval='사용자의 소규모 acceptance 별도 실행 승인',isolated_venv=True,
        python=platform.python_version(),numpy=np.__version__,pandas=pd.__version__,
        plan_sha256=sha(plan_path),source_commit=plan['source_commit'],source_sha256=sha(args.module),
        source_loading_scope='고정 원본 models_fcm.py 직접 import; 전체 package/R/DRF 제조 generator 설치·실행 아님',
        source_modified=False,source_hash_after=sha(args.module),
        checks={'declared_direct_graph':'PASS','observation_same_fcm':'PASS','do_replaces_equation':'PASS',
                'same_variables_axis':'PASS_IID_SCHEMA_PHYSICAL_TIME_NOT_APPLICABLE',
                'new_seed_reproducibility_and_split':'PASS','action_target_api':'PASS_EXAMPLE_ONLY'},
        records=records,repeat_checks=repeat_checks,hook_controls=hook_controls,common_noise_checks=common_noise_checks,
        raw_batches=18,sampler_calls_including_unhooked_controls=total_calls,
        new_seed_observations_distinct=new_seed_distinct,
        pr9_reuse=dict(oracle_mean_response=oracle_check,same_fixture_guard_accepted=True,
                      cross_environment_rejected=cross_environment_rejected,learned_coefficients=False),
        permitted_estimand='IID 분포의 do(A=a)에서 Y 반응. 행별 동일 잡음 반사실과 구분',
        strict_counterfactual_ready=False,manufacturing_generator_validated=False,track_b_adopted=False,
        discovery_trained=False,scm_fitted=False,recovery_safety_computed=False)
    write(out/'result.json',result)
    write(out/'SHA256.json',{str(p.relative_to(out)).replace('\\','/'):sha(p) for p in out.rglob('*') if p.is_file()})
    print(json.dumps(dict(status=result['status'],checks=result['checks'],raw_batches=len(records),
                         sampler_calls=total_calls,noise_alignment=common_noise_checks[0]),ensure_ascii=False))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--module',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True);parser.add_argument('--execution-approved',action='store_true')
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=False)
    try:execute(args)
    except Exception as exc:
        write(args.output/'FAILURE.json',dict(status='FAILED',error_type=type(exc).__name__,
            source_sha256=sha(args.module) if args.module.is_file() else None,
            plan_sha256=sha(ROOT/'research_runs/env_acceptance/PLAN_v1.json'),
            message='실행 중단. 격리 환경 console과 source/plan hash 확인; 미실행 항목을 PASS로 기록하지 않음'))
        raise

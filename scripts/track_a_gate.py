"""Evidence gate; document access and static settings cannot stand in for runs."""


def evaluate(evidence):
    raw=evidence['raw_data']
    engine=evidence['execution_environment']
    a1='VERIFIED' if all(raw[k] for k in ('acquired','timestamp_acquired','seed_acquired','export_reproduced','configuration_matched')) else ('PARTIAL' if raw['acquired'] else 'BLOCKED')
    a2='VERIFIED' if all(engine[k] for k in ('matlab_invocable','simulink_available','license_available','model_load_verified','mex_compatible')) else 'BLOCKED'
    runs=evidence['normal_runs']
    if runs and a2!='VERIFIED':
        raise ValueError('A2 미통과 상태의 정상 실행 주장은 허용하지 않음')
    a3='VERIFIED' if len(runs)>=2 and evidence['repeatability_verified'] else ('PARTIAL' if runs else 'NOT_RUN')
    direct=(a1==a2==a3=='VERIFIED' and evidence['intervention_interface_verified'])
    return dict(A1=a1,A2=a2,A3=a3,A4='GO' if direct else 'NO-GO',
                hypothesis_gate='READY_FOR_EFFECT_PROTOCOL' if direct else 'INSUFFICIENT_EVIDENCE',
                recommendation='A' if direct else ('B' if a2=='VERIFIED' else 'C'),
                track_b_or_c_adopted=False)

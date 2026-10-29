"""Narrow manual/no-fault valve-step check; never an observed-variable GT.

The normal regime is deliberately smaller than the source equation's domain.
Invalid/fault/controller records are rejected, not repaired using v_next.
"""
import math


def validate_transition(row, *, tolerance=1e-12):
    reasons=[]
    def fail(code):
        if code not in reasons:reasons.append(code)
    values={}
    fields=('requested_u_pp','evaluated_u_pp','cache_before_pp','applied_c_pp',
            'v_before_pp','v_after_pp','derivative_pp_per_hour','dt_hours','tau_hours',
            'evaluation_hours','state_after_hours','stiction_threshold_pp','ivst14')
    for field in fields:
        x=row.get(field)
        if type(x) not in (int,float) or not math.isfinite(x):
            fail('CACHE_UNKNOWN' if field in ('cache_before_pp','applied_c_pp') else 'MISSING_OR_NONFINITE')
        else:values[field]=x
    if row.get('source_verified') is not True:fail('SOURCE_UNVERIFIED')
    if row.get('mode')!='MANUAL':fail('CONTROLLER_MODE_UNSUPPORTED')
    if row.get('controller_overwrite') is not False:fail('CONTROLLER_OVERWRITE_OR_UNKNOWN')
    if row.get('clipping_active') is not False:fail('CLIPPING_OR_BOUNDARY_UNKNOWN')
    idv=row.get('idv')
    if not isinstance(idv,list) or len(idv)!=20 or any(type(x) not in (int,float) or x!=0 for x in idv):
        fail('FAULT_OR_STICTION_UNVERIFIED')
    if values.get('ivst14')!=0:fail('STICTION_OR_UNKNOWN')
    if row.get('shutdown_before') is not False or row.get('shutdown_after') is not False:
        fail('SHUTDOWN_OR_UNKNOWN')
    if row.get('step_running') is not True or row.get('finite_state') is not True:
        fail('STOPPED_OR_NONFINITE')
    if row.get('dt_unit')!='hour' or row.get('tau_unit')!='hour':fail('TIME_UNIT_MISMATCH')
    if values.get('dt_hours',0)<=0 or values.get('tau_hours',0)<=0:fail('INVALID_TIME_SCALE')
    for key in ('requested_u_pp','evaluated_u_pp','applied_c_pp','v_before_pp','v_after_pp'):
        if key in values and not 0<values[key]<100:fail('CLIPPING_OR_BOUNDARY_UNKNOWN')
    if len(values)==len(fields):
        if abs(values['requested_u_pp']-values['evaluated_u_pp'])>tolerance:
            fail('CONTROLLER_OVERWRITE_OR_UNKNOWN')
        if values['stiction_threshold_pp']<0:fail('STICTION_OR_UNKNOWN')
        refresh=(values['evaluation_hours']==0 or
                 abs(values['cache_before_pp']-values['evaluated_u_pp'])>
                 values['stiction_threshold_pp']*values['ivst14'])
        expected_cache=values['evaluated_u_pp'] if refresh else values['cache_before_pp']
        if abs(expected_cache-values['applied_c_pp'])>tolerance:fail('CACHE_RULE_MISMATCH')
        if abs(values['applied_c_pp']-values['evaluated_u_pp'])>tolerance:fail('CACHE_COMMAND_MISMATCH')
        if abs(values['state_after_hours']-values['evaluation_hours']-values['dt_hours'])>tolerance:
            fail('STATE_CLOCK_MISMATCH')
    else:refresh=None
    derivative=expected_next=derivative_error=step_error=None
    if not reasons:
        derivative=(values['applied_c_pp']-values['v_before_pp'])/values['tau_hours']
        expected_next=values['v_before_pp']+values['dt_hours']*derivative
        derivative_error=abs(values['derivative_pp_per_hour']-derivative)
        step_error=abs(values['v_after_pp']-expected_next)
        if derivative_error>tolerance:fail('DERIVATIVE_MISMATCH')
        if step_error>tolerance:fail('EULER_MISMATCH')
    return dict(status='VERIFIED_NARROW_TRANSITION' if not reasons else 'REJECTED',
                reasons=reasons,cache_refresh=refresh,expected_derivative_pp_per_hour=derivative,
                expected_next_v_pp=expected_next,derivative_absolute_error=derivative_error,
                step_absolute_error_pp=step_error,tolerance=tolerance,
                official_gt=False,global_f1_allowed=False)

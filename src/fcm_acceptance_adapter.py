"""Minimal adapter around one unmodified upstream module, not its manufacturing generator."""
import contextlib
import hashlib
import importlib.util
from pathlib import Path

PIN_SHA='c1f1b7f6b62c8916ebd23cb0002cdad1e9fcfb995b81cfae9558271987c4290e'


def load_pinned_module(path):
    path=Path(path)
    if hashlib.sha256(path.read_bytes()).hexdigest()!=PIN_SHA:
        raise ValueError('UPSTREAM_SOURCE_HASH_MISMATCH')
    spec=importlib.util.spec_from_file_location('causalassembly_fcm_pinned',path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def build_fixture(module,seed):
    from sympy import Eq,symbols
    from sympy.stats import Normal
    R,A,M,Y=symbols('R A M Y')
    equations=[Eq(R,Normal('u_R',0,1)),Eq(A,2*R+Normal('u_A',0,0.5)),
               Eq(M,3*A+Normal('u_M',0,1)),Eq(Y,M+R+Normal('u_Y',0,0.25))]
    fcm=module.FCM(name='ENV-MVP-EXAMPLE-FCM-v1',seed=seed)
    fcm.input_fcm(equations)
    return fcm,dict(R=R,A=A,M=M,Y=Y)


@contextlib.contextmanager
def capture_noise(module):
    """Observation hook only; forward every upstream call and return its original value."""
    import numpy as np
    original=module.sympy_sample
    draws={}
    def tap(distribution,*args,**kwargs):
        value=original(distribution,*args,**kwargs)
        name=str(distribution)
        if name in draws:raise ValueError('DUPLICATE_NOISE_CALL_IN_FIXTURE')
        draws[name]=np.asarray(value,dtype=float).copy()
        return value
    module.sympy_sample=tap
    try:yield draws
    finally:module.sympy_sample=original


def sample(module,seed,count,action=None):
    fcm,symbols=build_fixture(module,seed)
    original_edges={(str(a),str(b)) for a,b in fcm.edges}
    original_terms={str(n):str(fcm.graph.nodes[n]['term']) for n in fcm.nodes}
    if action is not None:fcm.intervene_on({symbols['A']:float(action)})
    with capture_noise(module) as draws:
        frame=(fcm.sample(size=count,additive_gaussian_noise=False,snr=None) if action is None
               else fcm.interventional_sample(size=count,which_intervention=0,additive_gaussian_noise=False,snr=None))
    if set(frame.columns)!={'R','A','M','Y'}:raise ValueError('UNEXPECTED_NODE_SCHEMA')
    source_column_order=list(frame.columns)
    frame=frame.loc[:,['R','A','M','Y']].astype(float)
    if len(frame)!=count or list(frame.index)!=list(range(count)):raise ValueError('UNEXPECTED_SAMPLE_INDEX')
    assert original_edges=={(str(a),str(b)) for a,b in fcm.edges}
    assert original_terms=={str(n):str(fcm.graph.nodes[n]['term']) for n in fcm.nodes}
    mutilated=None
    if action is not None:
        graph=fcm.mutilated_dags[fcm.interventions[0]]
        mutilated=dict(edges=sorted((str(a),str(b)) for a,b in graph.edges),
                       action_term=str(graph.nodes[symbols['A']]['term']),
                       action_parents=[str(n) for n in graph.predecessors(symbols['A'])],
                       nonaction_terms_unchanged=all(str(graph.nodes[symbols[n]]['term'])==original_terms[n] for n in ['R','M','Y']))
    return frame,draws,dict(original_edges=sorted(original_edges),original_terms=original_terms,
                            source_column_order=source_column_order,mutilated=mutilated)


def reconstruction(frame,noise,action=None):
    import numpy as np
    expected={'R':noise['u_R'],
              'A':(2*frame['R'].to_numpy()+noise['u_A']) if action is None else np.full(len(frame),action),
              'M':3*frame['A'].to_numpy()+noise['u_M'],
              'Y':frame['M'].to_numpy()+frame['R'].to_numpy()+noise['u_Y']}
    return {n:float(np.max(np.abs(frame[n].to_numpy()-values))) for n,values in expected.items()}

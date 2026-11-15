"""Strict graph-stage adapter. Evaluation must be a separate caller-held stage."""
try:
    from .policy_engine import refine
except ImportError:
    from policy_engine import refine

REQUIRED=frozenset(('node_ids','initial_edges','reference_edges','allowed_types',
                    'policy_id','budget','gamma','action','target','seed'))
OPTIONAL=frozenset(('prior_edges','display_names','graph_id'))

def run_graph_stage(request):
    if type(request) is not dict or not REQUIRED.issubset(request) or set(request)-REQUIRED-OPTIONAL:
        raise ValueError('graph-only request: missing or forbidden fields')
    return refine(**request)

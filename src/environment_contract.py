"""Fail-closed metadata/evidence compatibility, NOT causal or physical certification.

Every section cites local evidence bytes. Matching contracts only make a join
eligible for scientific review; neither this module nor an environment label
can establish the validity of the cited scientific claims.
"""
from hashlib import sha256
import json
import math
from pathlib import Path
import re

FIELDS = {
    'model': ('source_url', 'commit', 'source_sha256', 'configuration'),
    'controller': ('source_sha256', 'configuration', 'mode'),
    'observation': ('nodes', 'representation'),
    'clock': ('state_clock', 'sensor_clock', 'integration_seconds',
              'sampling_seconds', 'aggregation', 'window_seconds', 'stride_seconds'),
    'reference': ('nodes', 'representation', 'edge_semantics', 'lag_definition',
                  'positive_pairs', 'negative_pairs', 'uncertain_pairs', 'coverage'),
    'intervention': ('action', 'target', 'kind', 'mechanism', 'controller_policy'),
    'execution': ('initialization', 'noise', 'train_holdout', 'horizon_seconds'),
}


def canonical_hash(value):
    return sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                             ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def _meaningful(value):
    if value is None or value == '' or value == 'UNKNOWN':
        return False
    if isinstance(value, float) and not math.isfinite(value):
        return False
    if isinstance(value, dict):
        return bool(value) and all(_meaningful(v) for v in value.values())
    if isinstance(value, list):
        return all(_meaningful(v) for v in value)  # empty pair sets are legitimate
    return True


def compare_environment_contracts(structure, outcome, *, evidence_root,
                                  purpose='structure_effect_research'):
    """Return stable, structured rejection reasons; never authorize execution.

    purpose=interface_only skips full reference coverage, but still checks node,
    clock, intervention and all cited evidence. reference must explicitly be
    partial/unavailable rather than being silently omitted. Evidence paths are
    relative to evidence_root; traversal/absolute paths and changed bytes fail.
    """
    reasons = []

    def reject(code, path, side='both'):
        reasons.append(dict(code=code, path=path, side=side))

    if purpose not in {'structure_effect_research', 'interface_only'}:
        reject('INVALID_PURPOSE', 'purpose')
    root = Path(evidence_root).resolve()
    for side, contract in [('structure', structure), ('outcome', outcome)]:
        if not isinstance(contract, dict):
            reject('INVALID_CONTRACT', '$', side)
            continue
        if contract.get('schema_version') != 1:
            reject('SCHEMA_VERSION', 'schema_version', side)
        if not contract.get('environment_id'):
            reject('MISSING_FIELD', 'environment_id', side)
        evidence = contract.get('evidence', {})
        for section, fields in FIELDS.items():
            item = contract.get(section)
            if not isinstance(item, dict):
                reject('MISSING_SECTION', section, side)
                continue
            for key in fields:
                if key not in item or not _meaningful(item[key]):
                    reject('MISSING_OR_UNKNOWN_FIELD', f'{section}.{key}', side)
            refs = item.get('evidence_refs')
            if not isinstance(refs, list) or not refs:
                reject('MISSING_EVIDENCE', section, side)
                continue
            for ref in refs:
                ev = evidence.get(ref) if isinstance(evidence, dict) and isinstance(ref, str) else None
                if not isinstance(ev, dict):
                    reject('MISSING_EVIDENCE', f'{section}.{ref}', side)
                    continue
                if ev.get('level') != 'VERIFIED':
                    reject('EVIDENCE_NOT_VERIFIED', f'evidence.{ref}.level', side)
                p, digest = ev.get('path'), ev.get('sha256')
                if not isinstance(p, str) or not p or Path(p).is_absolute() or '\\' in p or ':' in p:
                    reject('INVALID_EVIDENCE_PATH', f'evidence.{ref}.path', side)
                    continue
                path = (root / p).resolve()
                if not path.is_relative_to(root):
                    reject('EVIDENCE_OUTSIDE_ROOT', f'evidence.{ref}.path', side)
                elif not path.is_file():
                    reject('EVIDENCE_FILE_MISSING', f'evidence.{ref}.path', side)
                elif not isinstance(digest, str) or not re.fullmatch('[0-9a-f]{64}', digest):
                    reject('INVALID_EVIDENCE_HASH', f'evidence.{ref}.sha256', side)
                elif sha256(path.read_bytes()).hexdigest() != digest:
                    reject('EVIDENCE_HASH_MISMATCH', f'evidence.{ref}.sha256', side)

        # Types and node meaning must be explicit, not merely equal strings.
        for section in ('model', 'controller'):
            data = contract.get(section, {})
            if not isinstance(data, dict):
                continue
            hashes = data.get('source_sha256')
            if not isinstance(hashes, dict) or not hashes or not all(
                    isinstance(k, str) and isinstance(v, str) and re.fullmatch('[0-9a-f]{64}', v)
                    for k, v in hashes.items()):
                reject('INVALID_SOURCE_HASH', f'{section}.source_sha256', side)
        model = contract.get('model', {})
        if isinstance(model, dict) and not re.fullmatch('[0-9a-f]{40}', str(model.get('commit'))):
            reject('INVALID_SOURCE_COMMIT', 'model.commit', side)
        execution = contract.get('execution', {})
        if isinstance(execution, dict):
            horizon = execution.get('horizon_seconds')
            if type(horizon) not in (int, float) or not math.isfinite(horizon) or horizon <= 0:
                reject('INVALID_TIME', 'execution.horizon_seconds', side)
        obs = contract.get('observation', {})
        obs = obs if isinstance(obs, dict) else {}
        nodes = obs.get('nodes', []) if isinstance(obs, dict) else []
        names = []
        if not isinstance(nodes, list) or not nodes:
            reject('INVALID_NODE_SCHEMA', 'observation.nodes', side)
        else:
            for node in nodes:
                if not isinstance(node, dict) or not all(isinstance(node.get(k), str) and node[k]
                                                        for k in ('name', 'unit', 'kind')):
                    reject('INVALID_NODE_SCHEMA', 'observation.nodes', side)
                else:
                    names.append(node['name'])
            if len(names) != len(set(names)):
                reject('DUPLICATE_NODE', 'observation.nodes', side)
        clock = contract.get('clock', {})
        if isinstance(clock, dict):
            for key in ('integration_seconds', 'sampling_seconds', 'stride_seconds'):
                value = clock.get(key)
                if type(value) not in (int, float) or not math.isfinite(value) or value <= 0:
                    reject('INVALID_TIME', f'clock.{key}', side)
            value = clock.get('window_seconds')
            if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
                reject('INVALID_TIME', 'clock.window_seconds', side)
        action = contract.get('intervention', {})
        if isinstance(action, dict):
            if action.get('kind') not in {'command', 'actuator_state', 'setpoint', 'structural_do'}:
                reject('INVALID_INTERVENTION_KIND', 'intervention.kind', side)
            if action.get('action') not in names or action.get('target') not in names:
                reject('ACTION_TARGET_NOT_OBSERVED', 'intervention', side)
        ref = contract.get('reference', {})
        if not isinstance(ref, dict):
            continue
        if purpose == 'structure_effect_research':
            if ref.get('nodes') != names or ref.get('representation') != obs.get('representation'):
                reject('REFERENCE_OBSERVATION_MISMATCH', 'reference', side)
            if ref.get('edge_semantics') != 'direct_same_step':
                # A lagged contract needs a separately specified finite lag universe.
                reject('UNSUPPORTED_EDGE_SEMANTICS', 'reference.edge_semantics', side)
            if ref.get('coverage') != 'complete_directed_pair_universe':
                reject('INCOMPLETE_NEGATIVE_COVERAGE', 'reference.coverage', side)
            universe = {(a, b) for a in names for b in names if a != b}
            sets = []
            for key in ('positive_pairs', 'negative_pairs', 'uncertain_pairs'):
                rows = ref.get(key)
                valid = isinstance(rows, list) and all(isinstance(p, list) and len(p) == 2
                      and all(isinstance(v, str) for v in p) for p in rows)
                pairs = {tuple(p) for p in rows} if valid else set()
                if not valid or len(pairs) != len(rows) or not pairs <= universe:
                    reject('INVALID_REFERENCE_PAIRS', f'reference.{key}', side)
                sets.append(pairs)
            positive, negative, uncertain = sets
            if uncertain or positive & negative or positive | negative != universe:
                reject('INCOMPLETE_NEGATIVE_COVERAGE', 'reference.pairs', side)

    if isinstance(structure, dict) and isinstance(outcome, dict):
        if structure.get('environment_id') != outcome.get('environment_id'):
            reject('ENVIRONMENT_ID_MISMATCH', 'environment_id')
        for section, fields in FIELDS.items():
            for key in fields:
                left, right = structure.get(section, {}), outcome.get(section, {})
                if isinstance(left, dict) and isinstance(right, dict) and left.get(key) != right.get(key):
                    reject('METADATA_MISMATCH', f'{section}.{key}')
    ok = not reasons
    return dict(schema_version=1, purpose=purpose, metadata_consistent=ok,
                research_join_eligible_for_review=ok and purpose == 'structure_effect_research',
                scientific_equivalence_proven=False, manufacturing_adopted=False,
                execution_authorized=False, reasons=reasons)


def require_environment_contract(structure, outcome, *, evidence_root):
    """Strict successor to the legacy ID/Boolean guard; no physical approval."""
    result = compare_environment_contracts(structure, outcome, evidence_root=evidence_root)
    if not result['research_join_eligible_for_review']:
        raise ValueError('ENVIRONMENT_CONTRACT_REJECTED: ' + json.dumps(result['reasons']))
    return result

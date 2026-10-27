"""Adversarial contract checks. Fixtures certify software behavior only."""
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import tempfile
import unittest

from src.environment_contract import compare_environment_contracts, require_environment_contract
from src.decision_mvp import require_research_environment


def software_fixture(path):
    """Two-node schema fixture, NOT generated data or a manufacturing GT."""
    path.write_text('software fixture only: A -> Y; no physical validity claim\n', encoding='utf-8')
    h = sha256(path.read_bytes()).hexdigest()
    c = dict(schema_version=1, environment_id='SYNTHETIC_SCHEMA_FIXTURE_ONLY',
        model=dict(source_url='urn:software-test-fixture', commit='1'*40,
                   source_sha256={'fixture.txt': h}, configuration={'equations': 'A=epsA;Y=A+epsY'}),
        controller=dict(source_sha256={'fixture.txt': h}, configuration={'enabled': False}, mode='none'),
        observation=dict(nodes=[dict(name='A', unit='arbitrary', kind='generated_variable'),
                                dict(name='Y', unit='arbitrary', kind='generated_variable')],
                         representation='declared_fcm_variables'),
        clock=dict(state_clock='sample_index', sensor_clock='sample_index', integration_seconds=1,
                   sampling_seconds=1, aggregation='none', window_seconds=0, stride_seconds=1),
        reference=dict(nodes=['A','Y'], representation='declared_fcm_variables',
                       edge_semantics='direct_same_step', lag_definition='zero_lag_only',
                       positive_pairs=[['A','Y']], negative_pairs=[['Y','A']], uncertain_pairs=[],
                       coverage='complete_directed_pair_universe'),
        intervention=dict(action='A', target='Y', kind='structural_do', mechanism='replace_equation',
                          controller_policy='none'),
        execution=dict(initialization='new_fcm', noise='independent_per_arm_samples',
                       train_holdout='disjoint_seed_namespaces', horizon_seconds=1),
        evidence={'fixture': dict(path=path.name, sha256=h, level='VERIFIED')})
    for name in ('model','controller','observation','clock','reference','intervention','execution'):
        c[name]['evidence_refs']=['fixture']
    return c


class EnvironmentContractTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.c=software_fixture(self.root/'fixture.txt')

    def compare(self, other=None, **kwargs):
        return compare_environment_contracts(self.c, self.c if other is None else other,
                                              evidence_root=self.root, **kwargs)

    def test_fixture_only_metadata_acceptance(self):
        result=require_environment_contract(self.c, deepcopy(self.c), evidence_root=self.root)
        self.assertTrue(result['metadata_consistent'])
        self.assertFalse(result['scientific_equivalence_proven'])
        self.assertFalse(result['execution_authorized'])
        self.assertFalse(result['manufacturing_adopted'])

    def test_same_label_mismatches(self):
        changes=[('controller','configuration',{'enabled':True}), ('controller','mode','manual'),
                 ('model','commit','2'*40), ('clock','sampling_seconds',3),
                 ('clock','sensor_clock','previous_evaluation'), ('clock','aggregation','median'),
                 ('clock','window_seconds',180), ('intervention','kind','setpoint'),
                 ('intervention','controller_policy','automatic_override'),
                 ('execution','noise','paired_unproven'), ('execution','initialization','same_object_reset')]
        for section,key,value in changes:
            with self.subTest(field=f'{section}.{key}'):
                other=deepcopy(self.c);other[section][key]=value
                result=self.compare(other)
                self.assertFalse(result['metadata_consistent'])
                self.assertIn(dict(code='METADATA_MISMATCH',path=f'{section}.{key}',side='both'),result['reasons'])

    def test_node_order_units_kind_and_set_mismatch(self):
        for field,value in [('name','W'),('unit','degC'),('kind','internal_state')]:
            other=deepcopy(self.c);other['observation']['nodes'][0][field]=value
            self.assertFalse(self.compare(other)['metadata_consistent'])
        other=deepcopy(self.c);other['observation']['nodes'].reverse()
        self.assertFalse(self.compare(other)['metadata_consistent'])

    def test_internal_state_reference_rejected(self):
        other=deepcopy(self.c);other['reference']['representation']='internal_derivative_dependencies'
        self.assertIn('REFERENCE_OBSERVATION_MISMATCH', {r['code'] for r in self.compare(other)['reasons']})

    def test_unknown_non_edges_and_lagged_reference_rejected(self):
        for field,value in [('negative_pairs',[]),('uncertain_pairs',[['Y','A']]),
                            ('coverage','positive_only'),('edge_semantics','lagged_update')]:
            other=deepcopy(self.c);other['reference'][field]=value
            self.assertFalse(self.compare(other)['research_join_eligible_for_review'])

    def test_missing_or_unverified_evidence(self):
        for level in ['REPORTED','UNKNOWN',None]:
            other=deepcopy(self.c);other['evidence']['fixture']['level']=level
            self.assertFalse(self.compare(other)['metadata_consistent'])
        other=deepcopy(self.c);other['controller']['evidence_refs']=[]
        self.assertFalse(self.compare(other)['metadata_consistent'])

    def test_actual_hash_and_missing_bytes(self):
        (self.root/'fixture.txt').write_text('changed', encoding='utf-8')
        self.assertIn('EVIDENCE_HASH_MISMATCH', {r['code'] for r in self.compare()['reasons']})
        (self.root/'fixture.txt').unlink()
        self.assertIn('EVIDENCE_FILE_MISSING', {r['code'] for r in self.compare()['reasons']})

    def test_evidence_path_escape(self):
        for p in ['../outside.txt','/outside.txt','C:/outside.txt','..\\outside.txt']:
            other=deepcopy(self.c);other['evidence']['fixture']['path']=p
            self.assertFalse(self.compare(other)['metadata_consistent'])

    def test_invalid_types_fail_closed(self):
        for key,value in [('observation',None),('reference',[]),('clock',None),('evidence',[]),
                          ('schema_version',2),('model',{})]:
            other=deepcopy(self.c);other[key]=value
            self.assertFalse(self.compare(other)['metadata_consistent'])
        for value in [None, [], 'label']:
            self.assertFalse(self.compare(value if value is not None else [])['metadata_consistent'])

    def test_different_id_legacy_and_strict(self):
        approvals={k:True for k in ('model_controller_identity','variable_intervention_alignment',
                                   'reference_structure_valid','independent_evaluation_contract')}
        with self.assertRaises(ValueError):require_research_environment('CPCAD','PYTHON_TEP',approvals)
        other=deepcopy(self.c);other['environment_id']='OTHER'
        with self.assertRaises(ValueError):require_environment_contract(self.c,other,evidence_root=self.root)

    def test_invalid_times_and_pair_partition(self):
        for value in [0,-1,float('nan'),True]:
            other=deepcopy(self.c);other['clock']['sampling_seconds']=value
            self.assertFalse(self.compare(other)['metadata_consistent'])
        for pairs in [[['Y','A'],['Y','A']],[['A','Y']],[['Y','Z']]]:
            other=deepcopy(self.c);other['reference']['negative_pairs']=pairs
            self.assertFalse(self.compare(other)['metadata_consistent'])

    def test_interface_cannot_authorize_research(self):
        result=self.compare(purpose='interface_only')
        self.assertTrue(result['metadata_consistent'])
        self.assertFalse(result['research_join_eligible_for_review'])
        self.assertFalse(self.compare(purpose='arbitrary')['metadata_consistent'])

    def test_saved_technical_and_contract_records(self):
        from scripts.validate_environment_contract import validate
        self.assertEqual(len(validate()),15)


if __name__=='__main__':unittest.main()

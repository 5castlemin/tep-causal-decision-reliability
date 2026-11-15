import ast,itertools,json,random,sys,unittest
from collections import Counter
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"research/budget_aware_refinement"))
from policy_engine import refine,path_f1,compare_edits,schema_mapping
from graph_adapter import run_graph_stage
from step1_fixture import run as fixture

class EngineTests(unittest.TestCase):
 def setUp(self):
  self.base=dict(node_ids=['a','b','c','d'],reference_edges=[('a','b'),('b','c')],initial_edges=[('b','a'),('c','d')],allowed_types=('FN','FP','REV'),policy_id='G-FN-FP-REV',budget=4,gamma=1,action='a',target='c',seed=0)
 def call(self,**kw):x=dict(self.base);x.update(kw);return refine(**x)
 def test_all_14_against_step1(self):
  for n in (1,2,3):
   for types in itertools.combinations(('FN','FP','REV'),n):
    for focus in (False,True):
     policy=('T' if focus else 'G')+'-'+'-'.join(types);r=self.call(allowed_types=types,policy_id=policy,budget=2)
     f=fixture(tuple(self.base['node_ids']),set(self.base['reference_edges']),set(self.base['initial_edges']),types,2,'a','c',focus)
     self.assertEqual(r['edit_sequence'],f['edit_sequence'])
 def test_errors_and_atomic_reverse(self):
  r=self.call(node_ids=['a','b'],reference_edges=[('a','b')],initial_edges=[('b','a')],allowed_types=['REV'],policy_id='G-REV',action='a',target='b')
  self.assertEqual(r['edit_sequence'],[('REV','b','a')]);self.assertEqual(r['spent_budget'],1);self.assertEqual(r['type_edit_counts']['REV'],1)
 def test_budget_gamma(self):
  for gamma in (1,2,3):
   r=self.call(node_ids=['a','b'],reference_edges=[('a','b')],initial_edges=[('b','a')],allowed_types=['REV'],policy_id='G-REV',budget=gamma,gamma=gamma,action='a',target='b')
   self.assertEqual(r['spent_budget'],gamma);self.assertEqual(r['spent_budget']+r['unused_budget'],gamma)
  r=self.call(node_ids=['a','b'],reference_edges=[('a','b')],initial_edges=[('b','a')],allowed_types=['REV'],policy_id='G-REV',budget=1,gamma=3,action='a',target='b');self.assertEqual(r['spent_budget'],0);self.assertEqual(r['termination_reason'],'no_affordable_candidate')
 def test_cycle_then_valid(self):
  r=self.call(node_ids=['a','b','c'],reference_edges=[('a','b'),('b','c')],initial_edges=[('b','c'),('c','a')],allowed_types=('FN','FP'),policy_id='G-FN-FP',budget=2,action='a',target='c')
  self.assertTrue(any(x['reason']=='cycle' for x in r['rejected_operations']));self.assertEqual(r['spent_budget'],2);self.assertEqual(set(map(tuple,r['final_graph'])),{('a','b'),('b','c')});self.assertEqual(len(r['ledger']),2)
 def test_zero_empty_noedit(self):
  r=self.call(budget=0);self.assertEqual(r['spent_budget'],0);self.assertEqual(r['termination_reason'],'budget_exhausted')
  r=self.call(initial_edges=self.base['reference_edges']);self.assertEqual(r['termination_reason'],'candidates_exhausted')
  r=self.call(policy_id='NO-EDIT');self.assertEqual(r['termination_reason'],'no_edit');self.assertEqual(r['initial_hash'],r['final_hash'])
 def test_json_and_no_double_cost(self):
  r=self.call();json.dumps(r);self.assertEqual(sum(x['cost'] for x in r['ledger']),r['spent_budget']);self.assertEqual(len(set(r['edit_sequence'])),len(r['edit_sequence']))
 def test_rename_and_input_order(self):
  a=self.call(display_names={'a':'A','b':'B','c':'C','d':'D'});b=self.call(node_ids=['d','b','a','c'],display_names={'a':'aa','b':'bb','c':'cc','d':'dd'});self.assertEqual(a['edit_sequence'],b['edit_sequence']);self.assertEqual(a['initial_hash'],b['initial_hash'])
 def test_invalid_inputs(self):
  cases=[{'node_ids':['a','a']},{'initial_edges':[('a','a')]},{'initial_edges':[('a','z')]},{'initial_edges':[('a','b'),('a','b')]},{'initial_edges':[('a','b'),('b','a')]},{'initial_edges':[('a','b'),('b','c'),('c','a')]},{'action':'z'},{'gamma':4},{'budget':-1},{'display_names':{'a':'A'}}]
  for case in cases:
   with self.subTest(case=case),self.assertRaises(ValueError):self.call(**case)
 def test_schema_mapping(self):
  self.assertEqual(schema_mapping(['a','b'],['a','b'],[3,4]),{'a':3,'b':4})
  with self.assertRaises(ValueError):schema_mapping(['b','a'],['a','b'],[4,3])
 def test_schedule_and_focus(self):
  common=dict(reference_edges=[('a','b'),('c','d')],initial_edges=[],allowed_types=['FN'],budget=1,action='c',target='d')
  g=self.call(policy_id='G-FN',**common);t=self.call(policy_id='T-FN',**common);self.assertNotEqual(g['edit_sequence'],t['edit_sequence']);self.assertEqual(g['type_opportunities'],t['type_opportunities'])
 def test_random_reproducible_and_varies(self):
  common=dict(reference_edges=[('a','b'),('c','d')],initial_edges=[],allowed_types=['FN'],policy_id='RANDOM',budget=1,action='a',target='b')
  self.assertEqual(self.call(seed=1,**common),self.call(seed=1,**common));counts=Counter(tuple(self.call(seed=i,**common)['edit_sequence'][0]) for i in range(400));self.assertEqual(len(counts),2);self.assertTrue(all(150<v<250 for v in counts.values()))
 def test_path_f1_false_extra_and_empty(self):
  n=['a','b','c','d'];truth={('a','b'),('b','d')};extra=truth|{('a','c'),('c','d')}
  self.assertEqual(path_f1(n,truth,truth,'a','d'),1);self.assertLess(path_f1(n,truth,extra,'a','d'),1);self.assertIsNone(path_f1(n,set(),set(),'a','d'))
  with self.assertRaises(ValueError):path_f1(n,truth,[('a','b'),('b','a')],'a','d')
 def test_path_baseline_skip_and_improve(self):
  r=self.call(node_ids=['a','b','c'],reference_edges=[('a','b'),('b','c')],initial_edges=[],allowed_types=['FN'],policy_id='PATH-F1',budget=3,action='a',target='c');self.assertEqual(r['spent_budget'],0);self.assertEqual(r['termination_reason'],'path_no_positive_gain')
  r=self.call(node_ids=['a','b','c'],reference_edges=[('a','b'),('b','c')],initial_edges=[('a','b')],allowed_types=['FN'],policy_id='PATH-F1',budget=3,action='a',target='c');self.assertEqual(r['edit_sequence'],[('FN','b','c')])
 def test_path_zero_denominator_and_tie(self):
  r=self.call(node_ids=['a','b','c'],reference_edges=[],initial_edges=[('a','b')],allowed_types=['FP'],policy_id='PATH-F1',budget=2,action='a',target='c');self.assertEqual(r['termination_reason'],'path_undefined')
  r=self.call(reference_edges=[('a','b'),('b','d'),('a','c'),('c','d')],initial_edges=[('a','b'),('a','c')],allowed_types=['FN'],policy_id='PATH-F1',budget=1,action='a',target='d');self.assertEqual(r['edit_sequence'],[('FN','b','d')])
 def test_compare(self):
  self.assertEqual(compare_edits([],[])['jaccard'],1);self.assertEqual(compare_edits([('FN','a','b')],[('FN','a','b'),('FP','b','c')])['common_prefix_length'],1)
 def test_information_boundary_with_evaluator(self):
  class Forbidden:
   def __getattribute__(self,name):raise AssertionError('evaluation accessed')
  with self.assertRaises(TypeError):self.call(evaluator=Forbidden())
  with self.assertRaises(ValueError):run_graph_stage(dict(self.base,evaluator=Forbidden()))
  with self.assertRaises(ValueError):run_graph_stage(dict(self.base,training_data=[1],evaluation_data=[2]))
  with self.assertRaises(ValueError):self.call(reference_edges=Forbidden())
  for coefficient in (1,-100):
   def adapter(effect):
    def evaluate():return effect
    result=run_graph_stage(dict(self.base));return result,evaluate
   result,evaluate=adapter(coefficient)
   self.assertEqual(evaluate(),coefficient)
   if coefficient==1:first=result['edit_sequence']
   else:self.assertEqual(first,result['edit_sequence'])
  tree=ast.parse((Path(__file__).resolve().parents[1]/'research/budget_aware_refinement/policy_engine.py').read_text());imports=[n.module for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)];self.assertFalse(any(x and ('evaluation' in x or 'scm' in x) for x in imports))
 def test_mock_graph_train_recommend_evaluate_boundary(self):
  class Evaluator:
   def __init__(self,coefficient):self.coefficient=coefficient
   def assess(self,chosen):return self.coefficient*chosen
  def pipeline(evaluator):
   request=dict(self.base);selection=run_graph_stage(request)
   # Mock model receives training values and final graph only, never the evaluator.
   def mock_fit(training,edges):return (sum(training),len(edges))
   model=mock_fit([1,2],selection['final_graph']);choice=1 if model[0]>0 else -1
   return selection,evaluator.assess(choice)
  left,lval=pipeline(Evaluator(1));right,rval=pipeline(Evaluator(-7))
  self.assertEqual(left['edit_sequence'],right['edit_sequence']);self.assertNotEqual(lval,rval)
  with self.assertRaises(ValueError):run_graph_stage(dict(self.base,evaluator=Evaluator(1)))
 def test_random_dag_fixture_parity(self):
  rng=random.Random(163);nodes=('a','b','c','d');pairs=list(itertools.combinations(nodes,2))
  for _ in range(120):
   order=list(nodes);rng.shuffle(order);rank={v:i for i,v in enumerate(order)}
   truth=[(a,b) for a,b in pairs if rng.random()<.4]
   initial=[(a,b) if rank[a]<rank[b] else (b,a) for a,b in pairs if rng.random()<.4]
   seed=rng.randrange(3);focus=bool(rng.randrange(2));policy=('T' if focus else 'G')+'-FN-FP-REV'
   r=self.call(node_ids=list(reversed(nodes)),reference_edges=truth,initial_edges=initial,policy_id=policy,budget=3,seed=seed)
   f=fixture(nodes,set(truth),set(initial),('FN','FP','REV'),3,'a','c',focus,seed=seed)
   self.assertEqual(r['edit_sequence'],f['edit_sequence']);self.assertEqual(r['spent_budget'],f['spent_budget'])
 def test_small_random_graphs(self):
  rng=random.Random(7)
  for _ in range(100):
   nodes=['a','b','c','d'];edges=[(a,b) for a,b in itertools.combinations(nodes,2) if rng.random()<.4]
   r=self.call(node_ids=nodes,reference_edges=edges,initial_edges=[],allowed_types=['FN'],policy_id='G-FN',budget=6,action='a',target='d');self.assertEqual(set(map(tuple,r['final_graph'])),set(edges));self.assertEqual(r['spent_budget'],len(edges))
if __name__=='__main__':unittest.main()

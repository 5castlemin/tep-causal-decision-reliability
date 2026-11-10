import itertools,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"research/budget_aware_refinement"))
from step1_fixture import candidates,apply,dag,distances,score,run,enumerate_valid

class Step1Fixtures(unittest.TestCase):
 def setUp(self):self.n=("a","b","c","d")
 def test_fn_fp_rev_disjoint_and_unit_cost(self):
  cases=[({("a","b")},set(),("FN","a","b")),(set(),{("a","b")},("FP","a","b")),({("a","b")},{("b","a")},("REV","b","a"))]
  for truth,g,op in cases:
   self.assertEqual(candidates(self.n,truth,g,("FN","FP","REV")),[op]);r=run(self.n,truth,g,(op[0],),1,"a","b");self.assertEqual(r["spent_budget"],1);self.assertEqual(set(r["final_graph"]),truth)
 def test_three_types(self):
  t={("a","b"),("b","c")};g={("b","a"),("c","d")};self.assertEqual({o[0] for o in candidates(self.n,t,g,("FN","FP","REV"))},{"FN","FP","REV"})
 def test_add_cycle_and_later_valid(self):
  t={("a","b"),("b","c")};g={("b","c"),("c","a")};r=run(self.n,t,g,("FN","FP"),2,"a","c");self.assertIn((("FN","a","b"),"cycle"),r["rejected_operations"]);self.assertEqual(set(r["final_graph"]),t);self.assertEqual(r["edit_sequence"][0][0],"FP")
 def test_reverse_cycle(self):
  t={("a","b"),("c","a")};g={("b","a"),("b","c"),("c","a")};self.assertFalse(dag(self.n,apply(g,("REV","b","a"))));self.assertIn((("FP","b","c"),("REV","b","a")),enumerate_valid(self.n,t,g,("FP","REV"),2))
 def test_type_restriction_and_budget(self):
  t={("a","b"),("b","c")};g={("b","c"),("c","a")};self.assertEqual(enumerate_valid(self.n,t,g,("FN",),6),[()]);self.assertEqual(enumerate_valid(self.n,t,g,("FN","FP"),1),[(),(("FP","c","a"),)])
 def test_equal_type_opportunities_and_different_position(self):
  t={("a","b"),("c","d")};g=set();a=run(self.n,t,g,("FN",),1,"c","d");b=run(self.n,t,g,("FN",),1,"c","d",True);self.assertNotEqual(a["edit_sequence"],b["edit_sequence"]);self.assertEqual(a["type_opportunities"],b["type_opportunities"])
 def test_score_missing_disconnected_and_h(self):
  d=distances(self.n,set(),(),"a","b");self.assertEqual(score(("FN","c","d"),d),0);self.assertGreater(score(("FN","a","c"),d),0);self.assertGreater(score(("FN","a","c"),distances(self.n,set(),(("a","c"),),"a","b")),1)
 def test_wrong_task_region_and_ties(self):
  t={("a","b"),("c","d")};r=run(self.n,t,set(),("FN",),1,"c","d",True);self.assertEqual(r["edit_sequence"],[('FN','c','d')]);self.assertNotIn(('a','b'),r['final_graph'])
 def test_stable_ids_under_rename(self):
  t={("a","b"),("c","d")};m={'a':'z','b':'y','c':'x','d':'w'};nn=tuple(m[x] for x in self.n);tt={(m[a],m[b]) for a,b in t}
  for focused in (False,True):
   r=run(self.n,t,set(),("FN",),1,"a","d",focused);s=run(nn,tt,set(),("FN",),1,m['a'],m['d'],focused)
   self.assertEqual([(k,m[a],m[b]) for k,a,b in r['edit_sequence']],s['edit_sequence'])
 def test_shared_round_robin_and_seed_rotation(self):
  t={('a','b'),('b','c')};g={('b','a'),('c','d')};types=('FN','FP','REV')
  for seed in (0,1,2):
   a=run(self.n,t,g,types,3,'a','c',False,seed=seed);b=run(self.n,t,g,types,3,'a','c',True,seed=seed)
   self.assertEqual(a['type_opportunities'][:3],b['type_opportunities'][:3]);self.assertEqual(a['type_opportunities'][0],types[seed])
 def test_budget_zero_and_duplicate_policies(self):
  t={("a","b")};g=set()
  for subset in itertools.chain.from_iterable(itertools.combinations(("FN","FP","REV"),k) for k in (1,2,3)):
   for focused in (False,True):self.assertEqual(run(self.n,t,g,subset,0,'a','b',focused)['final_graph'],[])
  self.assertEqual(run(self.n,t,g,("FN",),2,'a','b')['edit_sequence'],run(self.n,t,g,("FN","FP"),2,'a','b',True)['edit_sequence'])
 def test_unused_and_weighted(self):
  r=run(self.n,{('a','b')},{('b','a')},('REV',),1,'a','b',gamma=2);self.assertEqual((r['spent_budget'],r['unused_budget']),(0,1));self.assertIn((("REV","b","a"),"budget"),r['rejected_operations'])
 def test_reject_effect_coefficients(self):
  with self.assertRaises(TypeError):run(self.n,{('a','b')},set(),('FN',),1,'a','b',gt_effect=1.0)
 def test_coefficients_are_outside_selection_interface(self):
  def pipeline(coefficient):
   del coefficient  # evaluator input is never forwarded to graph selection
   return run(self.n,{('a','b'),('c','d')},set(),('FN',),1,'a','b',True)
  self.assertEqual(pipeline(1)['edit_sequence'],pipeline(-100)['edit_sequence'])
 def test_fourteen_policies_cover_seven_combinations(self):
  types=('FN','FP','REV');ids=[]
  for size in (1,2,3):
   for subset in itertools.combinations(types,size):
    for focus in (False,True):
     r=run(self.n,{('a','b'),('b','c')},{('b','a'),('c','d')},subset,2,'a','c',focus)
     ids.append(r['policy_id']);self.assertTrue(dag(self.n,r['final_graph']));self.assertLessEqual(r['spent_budget'],2)
  self.assertEqual(len(set(ids)),14)
 def test_independent_transitive_closure_oracle(self):
  def independent_dag(edges):
   reach=set(edges)
   for k in self.n:
    reach |= {(a,b) for a,c in list(reach) for d,b in list(reach) if c==k and d==k}
   return not any(a==b for a,b in reach)
  pairs=list(itertools.permutations(self.n,2))
  for n in range(4):
   for subset in itertools.combinations(pairs,n):self.assertEqual(dag(self.n,subset),independent_dag(subset))
 def test_exhaustive_reference_order(self):
  t={('a','b'),('b','c')};g={('b','c'),('c','a')};ops=[('FN','a','b'),('FP','c','a')];expected={()}
  for k in (1,2):
   for order in itertools.permutations(ops,k):
    h=set(g);valid=True
    for op in order:
     h=apply(h,op)
     if not dag(self.n,h):valid=False;break
    if valid:expected.add(order)
  self.assertEqual(set(enumerate_valid(self.n,t,g,('FN','FP'),2)),expected)
if __name__=='__main__':unittest.main()

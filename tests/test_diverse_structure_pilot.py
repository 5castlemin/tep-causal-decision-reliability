import json
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from diverse_structure_pilot import reference_edges,all_paths,analytic_response,score_graph,controlled_graphs
from repeated_metric_pilot import acyclic


class DiverseStructureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.plan=json.loads((ROOT/'research_runs/diverse_structure_pilot/PLAN_v1.json').read_text(encoding='utf-8'))

    def test_eight_distinct_dags_and_144_attempts(self):
        specs=self.plan['structures'];self.assertEqual(len(specs),8)
        self.assertEqual(len({tuple(sorted(reference_edges(s))) for s in specs}),8)
        self.assertEqual(sum(len(s['datasets'])*3 for s in specs),144)
        for s in specs:
            self.assertTrue(5<=len(s['nodes'])<=8)
            self.assertTrue(acyclic(s['nodes'],reference_edges(s)))
            self.assertEqual(set(s['algorithm_column_order']),set(s['nodes']))
            self.assertGreaterEqual(len([t for t in s['tasks'] if t['task_kind']!='negative_control']),2)

    def test_task_kinds_and_indirect_paths_are_predefined(self):
        for s in self.plan['structures']:
            for task in s['tasks']:
                paths=all_paths(reference_edges(s),task['action'],task['target'])
                if task['task_kind']=='negative_control':self.assertEqual(paths,[])
                elif task['task_kind']=='direct':self.assertIn((task['action'],task['target']),reference_edges(s))
                else:self.assertTrue(any(len(p)>=3 for p in paths))

    def test_negative_control_has_no_fake_path_accuracy(self):
        s=self.plan['structures'][0];task=s['tasks'][2]
        result=score_graph(reference_edges(s),set(),s,task)
        self.assertEqual(result['skeleton_f1'],1)
        self.assertEqual(result['strict_directed_f1'],1)
        self.assertIsNone(result['key_path_edge_recall'])
        self.assertFalse(result['action_target_reachable'])

    def test_direct_and_total_effect_differ(self):
        s=self.plan['structures'][3]
        # Direct A->Y=-.4, indirect A->M->Y=+1.1, total=.7.
        self.assertAlmostEqual(analytic_response(s,'A',1)['Y'],.7)

    def test_one_error_same_f1_different_location(self):
        for s in self.plan['structures']:
            if s['structure_id'] not in self.plan['controlled_errors']['structures']:continue
            graphs=controlled_graphs(s,self.plan);task=next(t for t in s['tasks'] if t['task_id']=='path')
            key=score_graph(graphs['remove_key'],set(),s,task)
            peripheral=score_graph(graphs['remove_peripheral'],set(),s,task)
            self.assertEqual(key['skeleton_f1'],peripheral['skeleton_f1'])
            self.assertEqual(key['strict_directed_f1'],peripheral['strict_directed_f1'])
            self.assertFalse(key['action_target_reachable'])
            self.assertTrue(peripheral['action_target_reachable'])

    def test_actual_saved_experiment(self):
        sys.path.insert(0,str(ROOT/'scripts'))
        from validate_diverse_structure_pilot import validate
        validate()


if __name__=='__main__':unittest.main()

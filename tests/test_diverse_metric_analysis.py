import json
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from diverse_metric_analysis import weighted_predict,loso,primary_rows


class DiverseAnalysisTests(unittest.TestCase):
    def test_heldout_outcomes_cannot_change_predictions(self):
        train=[dict(structure_id='S1',skeleton_f1=.2,scale_normalized_regret=.8),dict(structure_id='S2',skeleton_f1=.8,scale_normalized_regret=.1)]
        test=[dict(structure_id='S3',skeleton_f1=None,scale_normalized_regret=1000.)]
        pred,model=weighted_predict(train,test,['skeleton_f1'])
        test[0]['scale_normalized_regret']=-1000
        repeated,other=weighted_predict(train,test,['skeleton_f1'])
        self.assertEqual(pred,repeated)
        self.assertEqual(model,other)
        self.assertEqual(model['training_structures'],['S1','S2'])
        self.assertAlmostEqual(model['feature_imputations'][0],.5)

    def test_equal_structure_weights_not_row_weights(self):
        train=[dict(structure_id='S1',scale_normalized_regret=0.)]*10+[dict(structure_id='S2',scale_normalized_regret=2.)]
        pred,model=weighted_predict(train,[dict(structure_id='S3')],[])
        self.assertAlmostEqual(pred[0],1.)
        self.assertTrue(model['structure_equal_weights'])

    def test_negative_controls_and_controlled_graphs_excluded(self):
        valid=dict(source_type='discovery',row_status='EVALUATED',task_kind='indirect',policy='confirmed_only')
        self.assertEqual(primary_rows([valid,dict(valid,source_type='controlled_error'),dict(valid,task_kind='negative_control'),dict(valid,policy='mec_minimax')]),[valid])

    def test_all_rows_of_structure_are_held_out_together(self):
        plan=json.loads((ROOT/'research_runs/diverse_structure_pilot/PLAN_v1.json').read_text(encoding='utf-8'))
        rows=[]
        for i in range(8):
            for alg in ['pc','boss','directlingam']:
                for task in ['direct','path']:
                    rows.append(dict(source_type='discovery',row_status='EVALUATED',task_kind='indirect',policy='confirmed_only',structure_id=f'S{i+1}',dataset_id=f'S{i+1}_toy',graph_id=f'S{i+1}_{alg}',task_id=task,algorithm=alg,train_n=256,n_nodes=5+i%4,predicted_density=.3,unresolved_ratio=.1,skeleton_f1=.2+.08*i,strict_directed_f1=.1+.06*i,key_path_edge_recall=float(i%2),direct_xy_correct=True,normalized_shd=1-.05*i,scale_normalized_regret=1-.08*i))
        result=loso(rows,plan)
        self.assertEqual(len(result['macro_scores']),14)
        for artifact in result['artifacts']:
            self.assertEqual(len(artifact['training_structures']),7)
            self.assertNotIn(artifact['held_out_structure'],artifact['training_structures'])
        self.assertFalse(result['test_outcomes_used_for_selection'])


if __name__=='__main__':unittest.main()

"""Diagnostics on old exploratory data only. Confirmation samples not accessed."""
import argparse,json,sys,hashlib,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from decision_mvp import static_mean_response
from independent_confirmation import descriptive_diagnostics,freeze_models
from diverse_metric_analysis import weighted_predict,primary_rows
sys.path.insert(0,str(ROOT/'scripts'))
from run_diverse_structure_pilot import save
def main():
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);a=p.parse_args();out=Path(a.output);out.mkdir(parents=True,exist_ok=False)
    run=ROOT/'research_runs/diverse_structure_pilot/run_v1';rows=json.loads((run/'comparison.json').read_text(encoding='utf-8'))
    evaluation=json.loads((run/'intervention_evaluation.json').read_text(encoding='utf-8'));fixed=[]
    for r in primary_rows(rows):
        model=json.loads((run/'datasets'/r['dataset_id']/(r['algorithm']+'_models.json')).read_text(encoding='utf-8'))['primary']
        pred=static_mean_response(model,r['action'],.5)[r['target']]-static_mean_response(model,r['action'],0)[r['target']]
        prefix=r['structure_id']+'__'+r['action']+'__'
        actual=evaluation[prefix+'3']['statistics'][r['target']]['mean']-evaluation[prefix+'reference']['statistics'][r['target']]['mean']
        fixed.append(dict(r,fixed_action=.5,fixed_predicted_effect=pred,fixed_actual_effect=actual,fixed_effect_absolute_error=abs(pred-actual)))
    save(out/'fixed_action_effects.json',fixed)
    diagnostics=descriptive_diagnostics(rows,fixed)
    models=freeze_models(rows);save(out/'frozen_prediction_models.json',models)
    cov=models['M0']['features'];specs={'M0':cov,'M1':cov+['skeleton_f1'],'M2':cov+['key_path_edge_recall'],'M3':cov+['strict_directed_f1'],'M4_incremental':cov+['skeleton_f1','key_path_edge_recall']}
    data=primary_rows(rows);loso=[]
    for sid in sorted({r['structure_id'] for r in data}):
        train=[r for r in data if r['structure_id']!=sid];test=[r for r in data if r['structure_id']==sid]
        for name,features in specs.items():
            pred,artifact=weighted_predict(train,test,features,.01)
            loso.append(dict(structure_id=sid,model=name,mae=statistics.mean(abs(p-r['scale_normalized_regret']) for p,r in zip(pred,test)),rank=artifact['rank_status']))
    diagnostics['incremental_loso']=loso
    diagnostics['frozen_model_training_only']='S1..S8, outcomes and metrics previously explored; no new confirmation outcomes used'
    diagnostics['diagnostic_conclusions']=['conditional associations cannot remove selection bias','path-fallback mechanically related; fixed-action error separates selection but still model-path dependent',
        'DirectLiNGAM favored by linear non-Gaussian sufficient fixture; BOSS BIC is quasi-score','no inference from invariant within-algorithm metric','no new Gaussian sampling performed']
    save(out/'diagnostics.json',diagnostics)
    save(out/'SHA256.json',{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in out.glob('*.json')})
    print('Exploratory diagnostics and 5 prediction models frozen; confirmation outcomes not accessed')
if __name__=='__main__':main()

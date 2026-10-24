"""Compare a replay to preserved measurements; replay is not an independent sample."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from fcm_acceptance_adapter import load_pinned_module
from integrated_pilot import build_family


def main():
    p=argparse.ArgumentParser();p.add_argument('--module',required=True);p.add_argument('--replay',required=True);p.add_argument('--record',required=True)
    args=p.parse_args();run=ROOT/'research_runs/first_integrated_pilot/run_v1';replay=Path(args.replay)
    record=Path(args.record)
    if record.exists():raise ValueError('PRESERVE_EXISTING_REPLAY_RECORD')
    read=lambda f:json.loads(f.read_text(encoding='utf-8-sig'))
    module=load_pinned_module(args.module);plan=read(run/'plan.json');gts={}
    for family in plan['families']:
        fcm,_=build_family(module,81011,family,plan);gt=fcm.ground_truth
        edges=sorted((str(a),str(b)) for a in gt.index for b in gt.columns if gt.loc[a,b]!=0)
        assert edges==sorted(tuple(e) for e in plan['reference_edges'])
        gts[family]=edges
    identical=[];semantic=[]
    for file in run.rglob('*'):
        if not file.is_file():continue
        relative=file.relative_to(run);other=replay/relative
        assert other.is_file(),str(relative)
        if file.name in ['SHA256.json','execution_ledger.json']:continue
        if file.name.endswith('_graph.json'):
            a=read(file);b=read(other);a.pop('seconds');b.pop('seconds');assert a==b
            semantic.append(relative.as_posix())
        else:
            assert file.read_bytes()==other.read_bytes(),relative.as_posix()
            identical.append(relative.as_posix())
    result=dict(status='PASS',exact_files=len(identical),exact_file_names=identical,
        semantic_graphs_excluding_runtime=semantic,independent_experiment_count_added=0,
        returned_ground_truth_post_run_check=gts,
        source_sha256=hashlib.sha256(Path(args.module).read_bytes()).hexdigest(),
        summary_sha256=hashlib.sha256((run/'summary.json').read_bytes()).hexdigest())
    record.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('PASS: replay identical measurements/models/recommendations/summary; graph equality excluding runtime; returned GT both families')


if __name__=='__main__':main()

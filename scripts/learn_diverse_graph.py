"""Isolated learner worker: config contains no reference graph, equations or tasks."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from integrated_pilot import learn_graph


def main():
    p=argparse.ArgumentParser();p.add_argument('--train',required=True);p.add_argument('--config',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();cfg=json.loads(Path(a.config).read_text(encoding='utf-8'));out=Path(a.output)
    if out.exists():raise ValueError('WORKER_OUTPUT_EXISTS')
    assert set(cfg)=={'algorithm','seed','names','algorithms','families','train_sha256'}
    assert hashlib.sha256(Path(a.train).read_bytes()).hexdigest()==cfg['train_sha256']
    import pandas as pd
    x=pd.read_csv(a.train)[cfg['names']].to_numpy();z=(x-x.mean(axis=0))/x.std(axis=0,ddof=0)
    started=time.monotonic();edges,unknown,native=learn_graph(z,cfg['names'],cfg['algorithm'],cfg['seed'],'uniform',cfg)
    result=dict(status='LEARNED',confirmed_edges=sorted(edges),unresolved_pairs=sorted(sorted(e) for e in unknown),
        native=native,seconds=time.monotonic()-started,seed=cfg['seed'],column_order=cfg['names'],train_sha256=cfg['train_sha256'])
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print('LEARNED',cfg['algorithm'],len(edges),len(unknown),flush=True)
if __name__=='__main__':main()

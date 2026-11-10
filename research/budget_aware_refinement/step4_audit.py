"""Read saved Step 3 records and calculate illustrative normal-theory precision.

No SCM is generated, fitted or evaluated by this script.
"""
import hashlib,json,math
from collections import Counter
from pathlib import Path
from statistics import NormalDist

ROOT=Path(__file__).resolve().parent

def audit():
    path=ROOT/'step3_supplement_results/raw.jsonl'
    manifest=json.loads((path.parent/'manifest.json').read_text(encoding='utf8'))
    data=path.read_bytes(); windows=data.replace(b'\r\n',b'\n').replace(b'\n',b'\r\n')
    actual=hashlib.sha256(data).hexdigest(); restored=hashlib.sha256(windows).hexdigest()
    if manifest['raw_sha256'] not in (actual,restored):raise ValueError('source hash mismatch')
    rows=[json.loads(line) for line in data.splitlines()]
    if len(rows)!=456 or any(x['status']!='OK' for x in rows):raise ValueError('unexpected record status')
    counts=Counter((r['has_path'],r['evaluation']['regret']>1e-12,r['recommendation_changed'],r['prediction_changed']) for r in rows)
    cells=[dict(path=k[0],positive_regret=k[1],recommendation_changed=k[2],prediction_changed=k[3],n=v) for k,v in sorted(counts.items())]
    nop=[r for r in rows if not r['has_path']]
    flat=sum(max(x['predicted_y'] for x in r['selection']['candidates'])-min(x['predicted_y'] for x in r['selection']['candidates'])<1e-12 for r in nop)
    k0=sum(r['selection']['selected_k']==0 for r in nop)
    z=NormalDist().inv_cdf(1-0.025/2); tab=[]
    for sd in (0.2,0.3,0.5,0.7,1.0):
        se=sd/math.sqrt(200); mu=0.1/se
        power=1-NormalDist().cdf(z-mu)+NormalDist().cdf(-z-mu)
        tab.append(dict(sd=sd,ci95_half_width=1.95996398454*se,bonferroni_two_sided_alpha_025_power=power))
    return dict(source_sha256_recorded=manifest['raw_sha256'],n=len(rows),cells=cells,no_path_constant=flat,no_path_k0=k0,normal_approximation=tab)

if __name__=='__main__': print(json.dumps(audit(),indent=2,sort_keys=True))

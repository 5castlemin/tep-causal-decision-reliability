"""Lossless deterministic per-file compression of new raw records only."""
import argparse,gzip,hashlib,json
from pathlib import Path
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
    p=argparse.ArgumentParser();p.add_argument('--run',required=True);a=p.parse_args();root=Path(a.run).resolve()
    assert root.name=='run_v1' and root.parent.name=='independent_confirmation'
    records=[]
    files=list((root/'do_evaluation').glob('*.csv'))+list(root.glob('*comparison*.json'))+list(root.glob('*recommendations_frozen.json'))
    files+= [f for f in root.rglob('*.json') if f.name not in {'SHA256.json','plan.json','COMPRESSION.json'} and f.stat().st_size>65536]
    files=list(dict.fromkeys(files))
    # Comparison CSV is retained as a human table; no per-graph duplicate do samples.
    for f in files:
        b=f.read_bytes();target=Path(str(f)+'.gz');assert not target.exists()
        compressed=gzip.compress(b,mtime=0);assert gzip.decompress(compressed)==b
        target.write_bytes(compressed)
        records.append(dict(original=f.relative_to(root).as_posix(),original_bytes=len(b),original_sha256=sha(b),compressed=target.relative_to(root).as_posix(),compressed_bytes=len(compressed),compressed_sha256=sha(compressed)))
        f.unlink()  # This newly generated file has a verified lossless copy; older runs are never touched.
    (root/'COMPRESSION.json').write_text(json.dumps(records,indent=2)+'\n',encoding='utf-8')
    print('lossless new-file compression',len(records))
if __name__=='__main__':main()

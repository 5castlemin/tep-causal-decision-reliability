"""Prepare a fresh local workspace using previously verified local files only."""
import argparse,hashlib,re,shutil
from pathlib import Path

def prepare(official,guarded,destination):
    official,guarded,destination=map(Path,(official,guarded,destination))
    original=(official/'temexd_mod.c').read_bytes()
    assert hashlib.sha256(original).hexdigest()=='eff57b75700e7472005785150c21f82b0c3d178ebceebe37e532794f23785aba'
    assert hashlib.sha256((guarded/'temexd_mod.c').read_bytes()).hexdigest()=='16f0fea120781a0e22fc6c113ccca3db017fdafe599b5a20866df50acc30b45e'
    destination.mkdir(parents=True,exist_ok=False)
    for name in ['MultiLoop_mode1.mdl','TElib.mdl','Mode_1_Init.m','Mode1xInitial.mat','teprob_mod.h','temexd_mod.c','temexd_mod.mexw64']:
        shutil.copy2(guarded/name,destination/name)
    ref,n=re.subn(r'(#define\s+S_FUNCTION_NAME\s+)temexd_mod',r'\1temexd_ref',original.decode('latin1'))
    assert n==1
    (destination/'temexd_ref.c').write_bytes(ref.encode('latin1'))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('official');p.add_argument('guarded');p.add_argument('destination')
    a=p.parse_args();prepare(a.official,a.guarded,a.destination)

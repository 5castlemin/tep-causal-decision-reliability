import json, hashlib, zipfile
from pathlib import Path
base=Path(__import__('sys').argv[1])
zips=list(base.rglob('temexd_mod.zip'))
src=Path('../tep-studio-candidate/temexd_mod')
res={}
for z in zips:
 with zipfile.ZipFile(z) as f:
  for name in ('temexd_mod.c','teprob_mod.h','Mode1xInitial.mat'):
   matches=[s for s in f.namelist() if s.lower().endswith('/'+name.lower()) or s.lower()==name.lower()]
   loc=list(src.rglob(name))
   if matches and loc:
    a=hashlib.sha256(f.read(matches[0])).hexdigest(); b=hashlib.sha256(loc[0].read_bytes()).hexdigest()
    res[name]={'official':a,'studio':b,'equal':a==b,'archive_member':matches[0]}
 if len(res)==3: break
print(json.dumps({'archive':str(z),'archive_sha256':hashlib.sha256(z.read_bytes()).hexdigest(),'files':res},ensure_ascii=False,indent=2))
